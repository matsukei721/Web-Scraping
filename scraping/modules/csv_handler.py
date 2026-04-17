import os
import re
import logging
from datetime import datetime
import pandas as pd


# 対応する日付フォーマット（ファイル名に含まれる日付パターン）
DATE_PATTERNS = [
    (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),   # 2024-01-01
    (r"\d{4}_\d{2}_\d{2}", "%Y_%m_%d"),   # 2024_01_01
    (r"\d{8}",             "%Y%m%d"),      # 20240101
    (r"\d{2}-\d{2}-\d{4}", "%d-%m-%Y"),   # 01-01-2024
]


def _parse_date_from_filename(filename: str) -> datetime | None:
    """ファイル名から日付を抽出してdatetimeを返す。マッチしなければNoneを返す"""
    for pattern, fmt in DATE_PATTERNS:
        match = re.search(pattern, filename)
        if match:
            try:
                return datetime.strptime(match.group(), fmt)
            except ValueError:
                continue
    return None


def find_csv_file(config: dict, logger: logging.Logger, target_date: str | None = None) -> str:
    """
    input_dirから対象CSVファイルを特定して返す。
    target_dateが指定されていればその日付のファイルを探す。
    指定がなければ最新日付のファイルを返す。
    """
    input_dir = config["csv"]["input_dir"]
    file_prefix = config["csv"].get("file_prefix", "")

    # CSVファイルを列挙
    candidates = [
        f for f in os.listdir(input_dir)
        if f.endswith(".csv") and f.startswith(file_prefix)
    ]

    if not candidates:
        raise FileNotFoundError(f"CSVファイルが見つかりません: {input_dir}/{file_prefix}*.csv")

    # 各ファイルから日付を抽出
    dated_files = []
    for filename in candidates:
        dt = _parse_date_from_filename(filename)
        if dt:
            dated_files.append((dt, filename))

    if not dated_files:
        raise ValueError(f"日付を含むCSVファイルが見つかりません: {candidates}")

    if target_date:
        # 指定日付に一致するファイルを探す
        target_dt = _parse_target_date(target_date)
        matched = [f for dt, f in dated_files if dt.date() == target_dt.date()]
        if not matched:
            raise FileNotFoundError(f"指定日付 '{target_date}' に一致するCSVファイルが見つかりません")
        selected = matched[0]
        logger.info(f"指定日付のCSVを選択しました: {selected}")
    else:
        # 最新日付のファイルを自動選択
        dated_files.sort(key=lambda x: x[0], reverse=True)
        selected = dated_files[0][1]
        logger.info(f"最新日付のCSVを自動選択しました: {selected}")

    return os.path.join(input_dir, selected)


def _parse_target_date(target_date: str) -> datetime:
    """コマンドライン引数で渡された日付文字列をdatetimeに変換する"""
    for _, fmt in DATE_PATTERNS:
        try:
            return datetime.strptime(target_date, fmt)
        except ValueError:
            continue
    raise ValueError(
        f"日付フォーマットが認識できません: '{target_date}'\n"
        f"対応フォーマット: YYYY-MM-DD / YYYY_MM_DD / YYYYMMDD / DD-MM-YYYY"
    )


def load_csv(config: dict, logger: logging.Logger, file_path: str) -> pd.DataFrame:
    """CSVファイルを読み込んでDataFrameとして返す"""
    encoding = config["csv"]["encoding"]

    df = pd.read_csv(file_path, encoding=encoding, dtype=str)
    logger.info(f"CSVを読み込みました: {file_path}（{len(df)}行）")

    # ID列に重複がある場合は警告
    id_column = config["csv"]["id_column"]
    if id_column in df.columns and df[id_column].duplicated().any():
        dupes = df[id_column][df[id_column].duplicated()].tolist()
        logger.warning(f"ID列に重複があります: {dupes}")

    # 結果列が存在しない場合は空列を追加
    result_column = config["csv"]["result_column"]
    if result_column not in df.columns:
        df[result_column] = ""
        logger.debug(f"結果列 '{result_column}' を新規追加しました")

    return df


def save_csv(df: pd.DataFrame, config: dict, logger: logging.Logger, file_path: str) -> None:
    """DataFrameを元のCSVファイルに上書き保存する"""
    encoding = config["csv"]["encoding"]

    df.to_csv(file_path, index=False, encoding=encoding)
    logger.info(f"CSVを上書き保存しました: {file_path}")
