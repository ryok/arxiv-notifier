# arXiv Notifier

arXivから指定したキーワードに関する最新の論文を定期的に取得し、SlackとNotionに自動投稿するシステムです。

## 機能

- 🔍 **論文検索**: arXiv APIを使用して、指定したキーワードやカテゴリの論文を自動取得
- 💬 **Slack通知**: 新着論文をSlackチャンネルに自動投稿
- 📝 **Notion連携**: 論文情報をNotionデータベースに自動保存
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
