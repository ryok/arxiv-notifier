#!/bin/bash

# arXiv Notifier - Crontab用実行スクリプト
# このスクリプトはcrontabから呼び出すために作成されています

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# プロジェクトディレクトリに移動
cd "$PROJECT_DIR" || exit 1

# ログディレクトリを作成
mkdir -p logs

# 環境変数ファイルの存在確認
if [ ! -f ".env" ]; then
    echo "Error: .env file not found in $PROJECT_DIR" >&2
    exit 1
fi

# uvコマンドの存在確認
if ! command -v uv &> /dev/null; then
    echo "Error: uv command not found. Please install uv first." >&2
    exit 1
fi

# タイムスタンプ付きでログ出力
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting arXiv Notifier (crontab execution)" >> logs/crontab.log

# arXiv Notifierを実行（quietモードで実行）
uv run arxiv-notifier once --quiet >> logs/crontab.log 2>&1
EXIT_CODE=$?

# 実行結果をログに記録
if [ $EXIT_CODE -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - arXiv Notifier completed successfully" >> logs/crontab.log
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - arXiv Notifier failed with exit code $EXIT_CODE" >> logs/crontab.log
fi

exit $EXIT_CODE
