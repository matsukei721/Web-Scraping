# Web-Scraping

SeleniumベースのWebスクレイピング骨組みです。
CSVのID列を1行ずつ処理し、検索結果を同じCSVに書き戻します。

## 必要環境

- Python 3.9 以上
- Google Chrome（ChromeDriverは自動インストール）

## セットアップ

### 1. リポジトリをクローン

```bash
git clone https://github.com/matsukei721/Web-Scraping.git
cd Web-Scraping
```

### 2. 仮想環境を作成してパッケージをインストール

```bash
make setup
```

### 3. `.env` を編集

`scraping/.env` にログイン情報を設定します。

```env
LOGIN_URL=https://example.com/login
LOGIN_ID=your_login_id
LOGIN_PASSWORD=your_password
BASE_URL=https://example.com
```

### 4. `config.yaml` を必要に応じて編集

`scraping/config.yaml` でセレクタや列名を対象サイトに合わせて変更します。

```yaml
selectors:
  login:
    id_field: "input[name='username']"
    password_field: "input[name='password']"
    submit_button: "button[type='submit']"
  ...
```

### 5. 入力CSVを配置

`scraping/input.csv` を用意します。ID列が必須です（列名は `config.yaml` の `csv.id_column` で変更可）。

```csv
ID,結果
A001,
A002,
A003,
```

## 実行

```bash
make run
```

## フォルダ構成

```
Web-Scraping/
├── Makefile
├── README.md
└── scraping/
    ├── .env                  # ログイン情報（Git管理外）
    ├── .gitignore
    ├── .venv/                # 仮想環境（Git管理外）
    ├── config.yaml           # セレクタ・列名・タイムアウト設定
    ├── main.py               # エントリーポイント
    ├── requirements.txt
    └── modules/
        ├── __init__.py
        ├── login.py          # ログイン・メニュークリック
        ├── search.py         # 検索・結果取得
        └── csv_handler.py    # CSV読み込み・保存
```

## ログ

実行ログは `scraping/logs/scraping.log` に出力されます（5MB × 3世代でローテーション）。
ログレベルは `config.yaml` の `logging.level` で変更できます（`DEBUG` / `INFO` / `WARNING` / `ERROR`）。

## カスタマイズ

| 変更したい内容 | 編集ファイル |
|---|---|
| ログイン情報・URL | `scraping/.env` |
| セレクタ・列名・タイムアウト | `scraping/config.yaml` |
| 処理ロジック | `scraping/modules/` 以下の各ファイル |
