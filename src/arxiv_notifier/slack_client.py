"""Slack通知クライアント.

Slack Webhook APIを使用して論文情報を投稿する機能を提供する。
"""

import time
from typing import Any

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import settings
from .models import Paper


class SlackClient:
    """Slack通知クライアント."""

    def __init__(self, webhook_url: str | None = None) -> None:
        """初期化.

        Args:
            webhook_url: Slack Webhook URL（省略時は設定から取得）

        """
        self.webhook_url = webhook_url or settings.slack_webhook_url
        if not self.webhook_url:
            raise ValueError("Slack webhook URL is not configured")

        self.client = httpx.Client(timeout=settings.api_timeout)

    def __enter__(self) -> "SlackClient":
        """コンテキストマネージャー開始."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """コンテキストマネージャー終了."""
        self.client.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def _send_message(self, payload: dict[str, Any]) -> bool:
        """Slackにメッセージを送信.

        Args:
            payload: 送信するペイロード

        Returns:
            送信成功の場合True

        """
        try:
            response = self.client.post(self.webhook_url, json=payload)
            response.raise_for_status()
            logger.debug("Successfully sent message to Slack")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to send message to Slack: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise

    def post_paper(
        self, 
        paper: Paper, 
        japanese_summary: str | None = None,
        project_relevance_comment: str | None = None
    ) -> bool:
        """論文情報をSlackに投稿.

        Args:
            paper: 論文情報
            japanese_summary: 日本語要約（オプション）
            project_relevance_comment: プロジェクト関連性コメント（オプション）

        Returns:
            投稿成功の場合True

        """
        try:
            # Slack Block Kit形式のメッセージを取得（日本語要約・プロジェクト関連性付き）
            message = paper.to_slack_message(japanese_summary, project_relevance_comment)

            # 追加の設定を適用
            payload = {
                **message,
                "username": settings.slack_username,
                "icon_emoji": settings.slack_icon_emoji,
            }

            # チャンネル指定がある場合
            if settings.slack_channel:
                payload["channel"] = settings.slack_channel

            # メッセージ送信
            success = self._send_message(payload)

            # レート制限対応（1秒待機）
            time.sleep(1)

            if success:
                logger.info(f"Posted paper to Slack: {paper.id} - {paper.title}")

            return success

        except Exception as e:
            logger.error(f"Error posting paper {paper.id} to Slack: {e}")
            return False

    def post_papers_batch(self, papers: list[Paper], max_papers: int = 10) -> dict:
        """複数の論文をバッチで投稿.

        Args:
            papers: 論文リスト
            max_papers: 最大投稿数

        Returns:
            投稿結果の辞書 {"success": [成功したPaper], "failed": [失敗したPaper]}

        """
        results = {"success": [], "failed": []}

        # 投稿数を制限
        papers_to_post = papers[:max_papers]

        if len(papers) > max_papers:
            logger.warning(
                f"Limiting posts to {max_papers} papers out of {len(papers)}"
            )

        for paper in papers_to_post:
            if self.post_paper(paper):
                results["success"].append(paper)
            else:
                results["failed"].append(paper)

        logger.info(
            f"Batch posting completed: "
            f"{len(results['success'])} success, {len(results['failed'])} failed"
        )

        return results

    def post_summary(self, papers: list[Paper]) -> bool:
        """論文のサマリーを投稿.

        Args:
            papers: 論文リスト

        Returns:
            投稿成功の場合True

        """
        if not papers:
            logger.debug("No papers to summarize")
            return True

        try:
            # カテゴリ別に集計
            category_counts = {}
            for paper in papers:
                category = paper.get_primary_category()
                category_counts[category] = category_counts.get(category, 0) + 1

            # サマリーメッセージ作成
            summary_text = "📊 *Today's arXiv Summary*\n"
            summary_text += f"Found *{len(papers)}* new papers\n\n"
            summary_text += "*By Category:*\n"

            for category, count in sorted(
                category_counts.items(), key=lambda x: x[1], reverse=True
            ):
                summary_text += f"• {category}: {count} papers\n"

            payload = {
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": summary_text,
                        },
                    },
                    {"type": "divider"},
                ],
                "username": settings.slack_username,
                "icon_emoji": settings.slack_icon_emoji,
            }

            if settings.slack_channel:
                payload["channel"] = settings.slack_channel

            success = self._send_message(payload)

            if success:
                logger.info("Posted summary to Slack")

            return success

        except Exception as e:
            logger.error(f"Error posting summary to Slack: {e}")
            return False

    def test_connection(self) -> bool:
        """Slack接続をテスト.

        Returns:
            接続成功の場合True

        """
        try:
            test_payload = {
                "text": "🔧 arXiv Notifier connection test successful!",
                "username": settings.slack_username,
                "icon_emoji": settings.slack_icon_emoji,
            }

            if settings.slack_channel:
                test_payload["channel"] = settings.slack_channel

            return self._send_message(test_payload)

        except Exception as e:
            logger.error(f"Slack connection test failed: {e}")
            return False
