"""論文要約生成モジュール.

OpenAI GPT APIを使用して論文の英語要約を日本語で200文字程度に要約する機能を提供する。
"""

import openai
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import settings
from .models import Paper


class PaperSummarizer:
    """論文要約生成クラス."""

    def __init__(self, api_key: str | None = None) -> None:
        """初期化.

        Args:
            api_key: OpenAI APIキー（省略時は環境変数から取得）

        """
        self.api_key = api_key or settings.openai_api_key
        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            logger.warning("OpenAI API key not configured. Summarization disabled.")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def _call_openai_api(self, system_prompt: str, user_prompt: str) -> str:
        """OpenAI APIを呼び出し.

        Args:
            system_prompt: システムプロンプト
            user_prompt: ユーザープロンプト

        Returns:
            生成されたテキスト

        """
        if not self.client:
            raise ValueError("OpenAI client not initialized")

        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,  # 要約なので低めの温度設定
                max_tokens=400,  # 日本語200文字程度を考慮
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

    def generate_summary(self, paper: Paper) -> str | None:
        """論文の日本語要約を生成.

        Args:
            paper: 論文情報

        Returns:
            日本語要約（200文字程度）、生成できない場合はNone

        """
        if not self.enabled:
            return None

        try:
            # システムプロンプト
            system_prompt = """あなたは機械学習・AI分野の専門家です。
英語の論文要約（Abstract）を読んで、日本語で簡潔にまとめてください。
以下の点に注意してください：
1. 200文字程度で要約する
2. 研究の目的、手法、主な結果を含める
3. 専門用語は適切に日本語化する
4. 読みやすく、理解しやすい文章にする
5. 重要な数値結果があれば含める"""

            # ユーザープロンプト
            user_prompt = f"""以下の論文を日本語で200文字程度に要約してください。

タイトル: {paper.title}
カテゴリ: {paper.get_primary_category()}
要約: {paper.abstract}

日本語要約:"""

            # API呼び出し
            summary = self._call_openai_api(system_prompt, user_prompt)

            # 200文字を大幅に超える場合は切り詰め
            if len(summary) > 250:
                summary = summary[:197] + "..."

            logger.debug(
                f"Generated summary for paper {paper.id}: {len(summary)} chars"
            )
            return summary

        except Exception as e:
            logger.error(f"Error generating summary for paper {paper.id}: {e}")
            return None

    def is_enabled(self) -> bool:
        """要約機能が有効かどうか.

        Returns:
            有効な場合True

        """
        return self.enabled


# シングルトンインスタンス
_summarizer_instance: PaperSummarizer | None = None


def get_summarizer() -> PaperSummarizer:
    """要約生成器のシングルトンインスタンスを取得.

    Returns:
        PaperSummarizerインスタンス

    """
    global _summarizer_instance
    if _summarizer_instance is None:
        _summarizer_instance = PaperSummarizer()
    return _summarizer_instance
