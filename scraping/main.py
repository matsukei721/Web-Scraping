import argparse
import os
import sys
import time
import logging
import logging.handlers
import yaml
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

# リトライ対象の例外（一時的な問題のみ）
RETRYABLE_EXCEPTIONS = (TimeoutException, StaleElementReferenceException)

from modules.login import login, click_menu
from modules.search import search_by_id
from modules.csv_handler import find_csv_file, load_csv, save_csv
from modules.notifier import send_slack


def load_config(path: str = "config.yaml") -> dict:
    """config.yamlを読み込んで設定辞書を返す"""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup_logging(config: dict) -> logging.Logger:
    """ロガーを設定して返す（コンソール出力 + ファイルローテーション）"""
    log_cfg = config["logging"]
    level = getattr(logging, log_cfg["level"].upper(), logging.INFO)
    formatter = logging.Formatter(log_cfg["format"], datefmt=log_cfg["date_format"])

    logger = logging.getLogger("scraping")
    logger.setLevel(level)

    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイルハンドラ（ログファイルパスが設定されている場合のみ）
    log_file = log_cfg.get("file", "")
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=log_cfg["max_bytes"],
            backupCount=log_cfg["backup_count"],
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def build_driver(config: dict) -> webdriver.Chrome:
    """ChromeDriverを自動更新して起動する"""
    options = Options()
    options.add_argument("--headless")           # ブラウザ非表示（バックグラウンド実行）
    options.add_argument("--start-maximized")    # フルスクリーン起動
    options.add_argument("--no-sandbox")         # Linux環境で必要な場合あり
    options.add_argument("--disable-gpu")        # headless時にセットで指定
    options.add_argument("--window-size=1920,1080")  # 解像度指定

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(config["timeout"]["implicit_wait"])
    return driver


def search_with_retry(driver, target_id: str, config: dict, logger: logging.Logger) -> str:
    """リトライ処理付きで検索を実行する（一時的なエラーのみリトライ）"""
    max_attempts = config["retry"]["max_attempts"]
    wait_seconds = config["retry"]["wait_seconds"]

    for attempt in range(1, max_attempts + 1):
        try:
            return search_by_id(driver, target_id, config, logger)
        except RETRYABLE_EXCEPTIONS as e:
            # タイムアウト・要素再描画など一時的な問題はリトライ
            if attempt < max_attempts:
                logger.warning(f"ID={target_id} → リトライ {attempt}/{max_attempts}回目: {e}")
                time.sleep(wait_seconds)
            else:
                logger.error(f"ID={target_id} → {max_attempts}回試行しましたが失敗しました: {e}")
                raise
        except Exception as e:
            # セレクタ不一致・権限エラーなど即時失敗すべきエラーはリトライしない
            logger.error(f"ID={target_id} → リトライ不可のエラーが発生しました: {type(e).__name__}: {e}")
            raise


def parse_args() -> argparse.Namespace:
    """コマンドライン引数を解析する"""
    parser = argparse.ArgumentParser(description="Seleniumスクレイピング")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="処理対象の日付（例: 20240101 / 2024-01-01 / 2024_01_01 / 01-01-2024）省略時は最新日付のCSVを自動選択",
    )
    return parser.parse_args()


def main() -> None:
    # コマンドライン引数を解析
    args = parse_args()

    # .envを読み込む（LOGIN_URL / LOGIN_ID / LOGIN_PASSWORD / SLACK_WEBHOOK_URL）
    load_dotenv()

    # config.yaml を読み込む
    config = load_config()

    # ロガーをセットアップ
    logger = setup_logging(config)
    logger.info("スクレイピング処理を開始します")

    id_column = config["csv"]["id_column"]
    result_column = config["csv"]["result_column"]

    # 対象CSVファイルを特定して読み込む
    csv_file = find_csv_file(config, logger, target_date=args.date)
    df = load_csv(config, logger, csv_file)

    if df.empty:
        logger.warning("CSVにデータがありません。処理を終了します。")
        sys.exit(0)

    # 実行レポート用カウンター
    count_success = 0
    count_not_found = 0
    count_error = 0
    count_skip = 0

    # ChromeDriverを起動
    driver = build_driver(config)

    try:
        # ログイン → メニュークリック
        login(driver, config, logger)
        click_menu(driver, config, logger)

        # ID列を1行ずつ処理（チェックポイント：処理済み行はスキップ）
        for index, row in df.iterrows():
            target_id = str(row[id_column]).strip()

            # 処理済み行はスキップ
            if pd.notna(row[result_column]) and str(row[result_column]).strip() != "":
                logger.debug(f"行 {index + 1}: ID={target_id} → スキップ（処理済み）")
                count_skip += 1
                continue

            logger.info(f"行 {index + 1}: ID={target_id} を処理中...")

            try:
                result = search_with_retry(driver, target_id, config, logger)
                df.at[index, result_column] = result

                if result == config["csv"]["not_found_text"]:
                    count_not_found += 1
                else:
                    count_success += 1

            except Exception:
                # リトライ全滅時はエラーとして記録しCSVに書き込み処理を継続
                df.at[index, result_column] = "エラー"
                count_error += 1

            # 1行処理するたびにCSVを中間保存（クラッシュ対策）
            save_csv(df, config, logger, csv_file)

        # 実行レポートをログに出力
        total = count_success + count_not_found + count_error
        report = (
            f"\n========== 実行レポート ==========\n"
            f"  処理件数  : {total}件\n"
            f"  成功      : {count_success}件\n"
            f"  結果なし  : {count_not_found}件\n"
            f"  エラー    : {count_error}件\n"
            f"  スキップ  : {count_skip}件\n"
            f"=================================="
        )
        logger.info(report)

        # Slack通知（完了）
        if config["slack"].get("notify_on_complete", False):
            send_slack(
                f":white_check_mark: スクレイピング完了\n"
                f"成功: {count_success}件 / 結果なし: {count_not_found}件 / エラー: {count_error}件",
                config,
                logger,
            )

        logger.info("全行の処理が完了しました。正常終了します。")

    except Exception as e:
        logger.exception(f"予期しないエラーが発生しました: {e}")
        save_csv(df, config, logger, csv_file)

        # Slack通知（エラー）
        if config["slack"].get("notify_on_error", False):
            send_slack(f":x: スクレイピング中に予期しないエラーが発生しました\n{e}", config, logger)

        sys.exit(1)

    finally:
        driver.quit()
        logger.info("ブラウザを終了しました")


if __name__ == "__main__":
    main()
