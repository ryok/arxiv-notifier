# Python ボイラープレート

再利用可能なPythonプロジェクトの基本構造を提供するボイラープレートです。

## 機能

- 基本的なパッケージ構造
- ロギング機能
- コマンドライン引数の処理
- 設定ファイル読み込み（YAML/JSON）
- 単体テスト環境

## 要件

- Python 3.8以上
- PyYAML 6.0以上

## インストール

### 開発環境のセットアップ（uvを使用）

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/python-boilerplate.git
cd python-boilerplate

# uvのインストール（まだインストールしていない場合）
pip install uv

# uvを使用して仮想環境の作成と依存パッケージのインストール
uv venv
source .venv/bin/activate  # Linuxの場合
# または
.venv\Scripts\activate  # Windowsの場合

# 開発用依存パッケージのインストール
uv pip install -e ".[dev]"
```

### 従来の方法（pipを使用）

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/python-boilerplate.git
cd python-boilerplate

# 仮想環境の作成と有効化
python -m venv venv
source venv/bin/activate  # Linuxの場合
# または
venv\Scripts\activate  # Windowsの場合

# 開発用依存パッケージのインストール
pip install -e ".[dev]"
```

## 使い方

### コマンドラインからの実行

```bash
# ヘルプの表示
python-boilerplate --help

# バージョン情報の表示
python-boilerplate --version

# アプリケーションの実行
python-boilerplate run

# 設定ファイルを指定して実行
python-boilerplate -c config.yaml run

# ログレベルを指定して実行
python-boilerplate -l DEBUG run

# アプリケーションの初期化
python-boilerplate init
```

### ライブラリとしての使用

```python
from src.core.config import ConfigManager
from src.core.logger import Logger
from src.core.main import Application

# 設定の読み込み
config = ConfigManager("config.yaml")

# ロガーの初期化
logger = Logger("my-app", level="INFO", log_file="app.log")

# アプリケーションの実行
app = Application(config_path="config.yaml")
app.run()
```

## プロジェクト構造

```
python-boilerplate/
├── docs/               # ドキュメント
│   └── design.md       # 設計書
├── src/                # ソースコード
│   ├── __init__.py     # パッケージ定義
│   ├── core/           # コア機能
│   │   ├── __init__.py # パッケージ定義
│   │   ├── config.py   # 設定管理
│   │   ├── logger.py   # ロギング
│   │   └── main.py     # メイン機能
│   └── cli.py          # コマンドラインインターフェース
├── tests/              # テストコード
│   ├── __init__.py     # パッケージ定義
│   ├── core/           # コア機能のテスト
│   │   ├── __init__.py # パッケージ定義
│   │   ├── test_config.py  # 設定管理のテスト
│   │   ├── test_logger.py  # ロギングのテスト
│   │   └── test_main.py    # メイン機能のテスト
│   └── test_cli.py     # CLIのテスト
├── .gitignore          # Git除外設定
├── pyproject.toml      # プロジェクト設定
└── README.md           # プロジェクト説明
```

## テスト

```bash
# すべてのテストを実行
pytest

# カバレッジレポートを生成
pytest --cov=src

# 特定のテストを実行
pytest tests/core/test_config.py
```

## ライセンス

MITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。
