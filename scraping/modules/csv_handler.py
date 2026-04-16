import logging
import pandas as pd


def load_csv(config: dict, logger: logging.Logger) -> pd.DataFrame:
    """CSVファイルを読み込んでDataFrameとして返す"""
    file_path = config["csv"]["input_file"]
    encoding = config["csv"]["encoding"]

    df = pd.read_csv(file_path, encoding=encoding, dtype=str)
    logger.info(f"CSVを読み込みました: {file_path}（{len(df)}行）")

    # 結果列が存在しない場合は空列を追加
    result_column = config["csv"]["result_column"]
    if result_column not in df.columns:
        df[result_column] = ""
        logger.debug(f"結果列 '{result_column}' を新規追加しました")

    return df


def save_csv(df: pd.DataFrame, config: dict, logger: logging.Logger) -> None:
    """DataFrameを元のCSVファイルに上書き保存する"""
    file_path = config["csv"]["input_file"]
    encoding = config["csv"]["encoding"]

    df.to_csv(file_path, index=False, encoding=encoding)
    logger.info(f"CSVを上書き保存しました: {file_path}")
