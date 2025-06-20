# arXiv Notifier

arXivから指定したキーワードに関する最新の論文を定期的に取得し、SlackとNotionに自動投稿するシステムです。

## 機能

- 🔍 **論文検索**: arXiv APIを使用して、指定したキーワードやカテゴリの論文を自動取得
- 💬 **Slack通知**: 新着論文をSlackチャンネルに自動投稿
- 📝 **Notion連携**: 論文情報をNotionデータベースに自動保存
- 🎯 **プロジェクト関連性評価**: AIが論文のプロジェクトへの活用方法を自動評価・コメント生成
- 🔄 **重複管理**: 処理済み論文を記録し、重複投稿を防止
- ⏰ **スケジュール実行**: 定期的な自動実行（時刻指定または間隔指定）
- 📊 **ログ管理**: 詳細なログ出力とローテーション機能

## インストール

### 前提条件

- Python 3.11以上
- uv (Pythonパッケージマネージャー)

### セットアップ

1. リポジトリをクローン
```bash
git clone https://github.com/yourusername/arxiv-notifier.git
cd arxiv-notifier
```

2. 依存関係をインストール
```bash
uv sync
```

3. 環境変数を設定
```bash
# サンプルファイルを生成
uv run arxiv-notifier generate-env

# .envファイルを作成して編集
cp .env.example .env
```

## 設定

### 環境変数

`.env`ファイルで以下の設定を行います：

#### arXiv設定
- `ARXIV_KEYWORDS`: 検索キーワード（カンマ区切り）
- `ARXIV_CATEGORIES`: 検索カテゴリ（カンマ区切り）
- `ARXIV_MAX_RESULTS`: 一度に取得する最大論文数
- `ARXIV_DAYS_BACK`: 何日前までの論文を取得するか

#### Slack設定（オプション）
- `SLACK_WEBHOOK_URL`: Slack Webhook URL
- `SLACK_CHANNEL`: 投稿先チャンネル（Webhookで指定済みの場合は不要）
- `SLACK_USERNAME`: Bot表示名
- `SLACK_ICON_EMOJI`: Botアイコン絵文字

#### Notion設定（オプション）
- `NOTION_API_KEY`: Notion Integration Token
- `NOTION_DATABASE_ID`: 論文を保存するデータベースID

#### OpenAI設定（オプション）
- `OPENAI_API_KEY`: OpenAI APIキー（日本語要約生成・プロジェクト関連性評価用）
- `OPENAI_MODEL`: 使用するGPTモデル（デフォルト: gpt-3.5-turbo）

#### プロジェクト関連性評価設定（オプション）
- `PROJECT_OVERVIEW_FILE`: プロジェクト概要マークダウンファイルのパス
- `ENABLE_PROJECT_RELEVANCE`: プロジェクト関連性評価機能を有効にするか（true/false）

#### スケジュール設定
- `SCHEDULE_TIME`: 実行時刻（HH:MM形式）または
- `SCHEDULE_INTERVAL_HOURS`: 実行間隔（時間）

### Slack Webhookの取得方法

1. [Slack App Directory](https://api.slack.com/apps)にアクセス
2. 「Create New App」→「From scratch」を選択
3. App名とワークスペースを設定
4. 「Incoming Webhooks」を有効化
5. 「Add New Webhook to Workspace」でチャンネルを選択
6. 生成されたWebhook URLをコピー

### Notion Integrationの設定方法

1. [Notion Integrations](https://www.notion.so/my-integrations)にアクセス
2. 「New integration」をクリック
3. 名前を設定して作成
4. 「Internal Integration Token」をコピー
5. Notionで論文保存用のデータベースを作成
6. データベースページで「...」→「Add connections」からIntegrationを追加
7. データベースIDをURLから取得（`https://www.notion.so/xxxxx?v=yyyyy`のxxxxxの部分）

### プロジェクト関連性評価機能の設定方法

この機能により、論文がプロジェクトにどのように活用できるかをAIが自動評価し、具体的なコメントを生成します。

#### 1. プロジェクト概要ファイルの作成

プロジェクトの目的・技術領域を記載したマークダウンファイルを作成します：

```markdown
# プロジェクト概要

## プロジェクト名
機械学習を活用したスマート農業システム

## 目的・目標
IoTセンサーとAI技術を組み合わせて、農作物の生育環境を最適化し、
収穫量の向上と労働コストの削減を実現するシステムを開発する。

## 技術領域
- 機械学習: 作物の生育予測、病害虫検出
- コンピュータビジョン: ドローン画像解析
- IoT: 土壌センサー、気象センサー
- データ分析: 収穫データの統計分析

## 応用可能な研究分野
- 深層学習・ニューラルネットワーク
- 時系列データ解析
- 画像処理・コンピュータビジョン
- センサーネットワーク
```

#### 2. 環境変数の設定

`.env`ファイルに以下を追加：

```bash
# プロジェクト関連性評価設定
PROJECT_OVERVIEW_FILE=project_overview.md
ENABLE_PROJECT_RELEVANCE=true
OPENAI_API_KEY=your_openai_api_key
```

#### 3. 機能の動作

- 関連性の高い論文に対してプロジェクトへの具体的な活用方法をコメント生成
- Slack通知とNotion保存の両方にコメントが表示
- 関連性が低い論文はコメントなしで通常通り処理
- OpenAI APIの使用料金が発生するため、必要に応じて有効化

## 使用方法

### コマンド一覧

```bash
# ヘルプを表示
uv run arxiv-notifier --help

# 設定を確認
uv run arxiv-notifier config

# 接続テスト
uv run arxiv-notifier test

# 一度だけ実行
uv run arxiv-notifier once

# スケジューラーを起動（定期実行）
uv run arxiv-notifier run

# スケジューラーを起動（起動時に即実行）
uv run arxiv-notifier run --immediately
```

### Docker での実行

```bash
# イメージをビルド
docker build -t arxiv-notifier .

# コンテナを実行
docker run -d \
  --name arxiv-notifier \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/arxiv_papers.db:/app/arxiv_papers.db \
  arxiv-notifier
```

### Docker Compose での実行

```bash
# 起動
docker-compose up -d

# ログを確認
docker-compose logs -f

# 停止
docker-compose down
```

## 外部スケジューラーとの連携

内蔵のスケジューラーの代わりに、crontabやGitHub Actionsなどの外部スケジューリングシステムを使用することも可能です。

### crontab での定期実行

crontabを使用して定期実行する場合は、`arxiv-notifier once`コマンドまたは提供されているスクリプトを使用します。

#### 方法1: 直接コマンドを実行

```bash
# crontabを編集
crontab -e

# 毎日午前9時に実行する例
0 9 * * * cd /path/to/arxiv-notifier && /path/to/uv run arxiv-notifier once >> /var/log/arxiv-notifier.log 2>&1

# 6時間ごとに実行する例
0 */6 * * * cd /path/to/arxiv-notifier && /path/to/uv run arxiv-notifier once >> /var/log/arxiv-notifier.log 2>&1
```

#### 方法2: 提供されているスクリプトを使用（推奨）

```bash
# スクリプトに実行権限を付与
chmod +x /path/to/arxiv-notifier/scripts/run-once.sh

# crontabを編集
crontab -e

# 毎日午前9時に実行する例
0 9 * * * /path/to/arxiv-notifier/scripts/run-once.sh

# 6時間ごとに実行する例
0 */6 * * * /path/to/arxiv-notifier/scripts/run-once.sh
```

**スクリプトの利点:**
- エラーハンドリングが組み込まれている
- 自動的にプロジェクトディレクトリに移動
- 専用のログファイル（`logs/crontab.log`）に出力
- 環境変数ファイルの存在確認

**注意点:**
- 絶対パスを使用してください
- 環境変数が正しく読み込まれることを確認してください
- ログファイルの権限を確認してください

### GitHub Actions での定期実行

GitHub Actionsを使用してクラウドで定期実行することも可能です。

`.github/workflows/arxiv-notifier.yml`を作成：

```yaml
name: arXiv Notifier

on:
  schedule:
    # 毎日UTC 0:00（日本時間 9:00）に実行
    - cron: '0 0 * * *'
  workflow_dispatch: # 手動実行も可能

jobs:
  notify:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install uv
      run: |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        echo "$HOME/.cargo/bin" >> $GITHUB_PATH
        
    - name: Install dependencies
      run: uv sync
      
    - name: Run arXiv Notifier
      env:
        ARXIV_KEYWORDS: ${{ secrets.ARXIV_KEYWORDS }}
        ARXIV_CATEGORIES: ${{ secrets.ARXIV_CATEGORIES }}
        ARXIV_MAX_RESULTS: ${{ secrets.ARXIV_MAX_RESULTS }}
        ARXIV_DAYS_BACK: ${{ secrets.ARXIV_DAYS_BACK }}
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
        SLACK_CHANNEL: ${{ secrets.SLACK_CHANNEL }}
        SLACK_USERNAME: ${{ secrets.SLACK_USERNAME }}
        SLACK_ICON_EMOJI: ${{ secrets.SLACK_ICON_EMOJI }}
        NOTION_API_KEY: ${{ secrets.NOTION_API_KEY }}
        NOTION_DATABASE_ID: ${{ secrets.NOTION_DATABASE_ID }}
        DATABASE_URL: "sqlite:///./arxiv_papers.db"
        LOG_LEVEL: "INFO"
      run: uv run arxiv-notifier once
```

**GitHub Secretsの設定:**

1. GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」
2. 「New repository secret」で以下の環境変数を設定：
   - `ARXIV_KEYWORDS`
   - `ARXIV_CATEGORIES`
   - `SLACK_WEBHOOK_URL`
   - `NOTION_API_KEY`
   - `NOTION_DATABASE_ID`
   - その他必要な設定値

### 実行方法の比較

| 方法 | メリット | デメリット | 適用場面 |
|------|----------|------------|----------|
| 内蔵スケジューラー | 設定が簡単、ログ管理が統合 | サーバーの常時稼働が必要 | 専用サーバーがある場合 |
| crontab | システムレベルの信頼性、リソース効率 | 設定が複雑、ログ管理が分散 | Linuxサーバーでの運用 |
| GitHub Actions | インフラ不要、無料枠あり | 実行時間制限、ログ保持期間制限 | 個人利用、軽量な処理 |

## 開発

### テストの実行

```bash
# 全テストを実行
uv run pytest

# カバレッジ付きで実行
uv run pytest --cov=src/arxiv_notifier --cov-report=html

# 特定のテストを実行
uv run pytest tests/arxiv_notifier/test_models.py
```

### コードフォーマット

```bash
# フォーマットチェック
uv run ruff check .

# 自動修正
uv run ruff check --fix .

# 型チェック
uv run mypy src/
```

## トラブルシューティング

### よくある問題

1. **Slack通知が届かない**
   - Webhook URLが正しいか確認
   - ネットワーク接続を確認
   - ログファイルでエラーを確認

2. **Notion連携が動作しない**
   - Integration TokenとDatabase IDが正しいか確認
   - IntegrationがデータベースにアクセスできるかNotionで確認
   - APIレート制限に達していないか確認

3. **論文が取得できない**
   - arXiv APIのステータスを確認
   - キーワードやカテゴリの指定が正しいか確認
   - ログファイルでエラーを確認

### ログの確認

```bash
# 最新のログを確認
tail -f logs/arxiv_notifier.log

# エラーログのみ表示
grep ERROR logs/arxiv_notifier.log
```

## ライセンス

MIT License

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを作成して変更内容を議論してください。

## 作者

ryok
