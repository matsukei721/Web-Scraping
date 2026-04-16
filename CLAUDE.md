# CLAUDE.md

このプロジェクトについてClaudeが把握しておくべき情報をまとめています。

## プロジェクト概要

SeleniumベースのWebスクレイピング骨組み。
CSVのID列を1行ずつ処理し、検索結果を同じCSVに書き戻す。

## フォルダ構成

```
Web-Scraping/
├── Makefile
├── README.md
├── CLAUDE.md
└── scraping/
    ├── .env                  # ログイン情報（Git管理外）
    ├── .gitignore
    ├── .venv/                # 仮想環境（Git管理外）
    ├── config.yaml           # セレクタ・列名・タイムアウト・ログ設定
    ├── main.py               # エントリーポイント
    ├── requirements.txt
    └── modules/
        ├── __init__.py
        ├── login.py          # ログイン・メニュークリック
        ├── search.py         # 検索・結果取得
        └── csv_handler.py    # CSV読み込み・保存
```

## 開発方針

- 仮想環境は `venv + pip` で構築（標準ライブラリのみ、追加ツール不要）
- uvやruffは使用しない（他の人が使いやすいようにレガシー寄りで統一）

## 設計ルール

- セレクタ・列名・タイムアウト・ログ設定はすべて `config.yaml` で管理し、コードにハードコードしない
- ログイン情報・URLは `.env` で管理（`python-dotenv` で読み込み）
- ロガー（`logging.Logger`）は `main.py` で生成し、各モジュールの関数に引数として渡す
- 各モジュールは機能単位で分割する（login / search / csv_handler）

## コーディング規約

- コメントは日本語で記載
- 関数の引数順は `(driver, config, logger)` を基本とする
- セレクタは `config["selectors"]` から取得する

## 実行方法

```bash
make setup   # 初回のみ（仮想環境作成 + パッケージインストール）
make run     # 実行
```

## 注意事項

- `.env` は `.gitignore` で除外済み。絶対にコミットしない
- `.venv/` は `.gitignore` で除外済み
- `logs/` ディレクトリも `.gitignore` で除外済み
- ChromeDriverは `webdriver-manager` が自動管理するため手動インストール不要
