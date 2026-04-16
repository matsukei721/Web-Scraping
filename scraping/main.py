import os
import sys
import logging
import logging.handlers
import yaml
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

from modules.login import login, click_menu
from modules.search import search_by_id
from modules.csv_handler import load_csv, save_csv


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


def main() -> None:
    # .envを読み込む（LOGIN_URL / LOGIN_ID / LOGIN_PASSWORD）
    load_dotenv()

    # config.yaml を読み込む
    config = load_config()

    # ロガーをセットアップ
    logger = setup_logging(config)
    logger.info("スクレイピング処理を開始します")

    id_column = config["csv"]["id_column"]
    result_column = config["csv"]["result_column"]

    # CSVを読み込む
    df = load_csv(config, logger)

    if df.empty:
        logger.warning("CSVにデータがありません。処理を終了します。")
        sys.exit(0)

    # ChromeDriverを起動
    driver = build_driver(config)

    try:
        # ログイン → メニュークリック
        login(driver, config, logger)
        click_menu(driver, config, logger)

        # ID列を1行ずつ処理
        for index, row in df.iterrows():
            target_id = str(row[id_column]).strip()

            # 既に結果が書き込まれている行はスキップ
            if pd.notna(row[result_column]) and str(row[result_column]).strip() != "":
                logger.debug(f"行 {index + 1}: ID={target_id} → スキップ（処理済み）")
                continue

            logger.info(f"行 {index + 1}: ID={target_id} を処理中...")
            result = search_by_id(driver, target_id, config, logger)
            df.at[index, result_column] = result

        # 全行処理後にCSVを上書き保存
        save_csv(df, config, logger)
        logger.info("全行の処理が完了しました。正常終了します。")

    except Exception as e:
        # 予期しない例外が発生した場合もCSVを保存して終了
        logger.exception(f"予期しないエラーが発生しました: {e}")
        save_csv(df, config, logger)
        sys.exit(1)

    finally:
        driver.quit()
        logger.info("ブラウザを終了しました")


if __name__ == "__main__":
    main()
