"""プロジェクト関連性評価機能.

マークダウンファイルで定義されたプロジェクト概要を基に、
論文がそのプロジェクトにどのように活用・応用できるかを評価する。
"""

import logging
from pathlib import Path
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from .config import settings
from .models import Paper

logger = logging.getLogger(__name__)


class ProjectRelevanceEvaluator:
    """プロジェクト関連性評価クラス."""

    def __init__(self) -> None:
        """初期化."""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required for relevance evaluation")
        
        self._project_overview: Optional[str] = None
        self._load_project_overview()

    def _load_project_overview(self) -> None:
        """プロジェクト概要を読み込む."""
        if not settings.project_overview_file or not settings.project_overview_file.exists():
            logger.warning("Project overview file not found or not specified")
            return

        try:
            with open(settings.project_overview_file, "r", encoding="utf-8") as f:
                self._project_overview = f.read()
            logger.info(f"Loaded project overview from {settings.project_overview_file}")
        except Exception as e:
            logger.error(f"Failed to load project overview: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def evaluate_relevance(self, paper: Paper) -> Optional[str]:
        """論文のプロジェクト関連性を評価し、活用方法のコメントを生成する.
        
        Args:
            paper: 評価対象の論文
            
        Returns:
            プロジェクトへの活用方法を示すコメント（関連性が低い場合はNone）
        """
        if not self._project_overview:
            logger.warning("Project overview not loaded, skipping relevance evaluation")
            return None

        # プロンプトを構築
        prompt = self._build_prompt(paper)
        
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "あなたは研究開発プロジェクトの技術アドバイザーです。"
                        "論文の内容を分析し、特定のプロジェクトへの具体的な活用方法を簡潔に提案してください。"
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=200,
                temperature=0.3,
            )
            
            comment = response.choices[0].message.content.strip()
            
            # 関連性が低い場合の判定
            if self._is_low_relevance(comment):
                return None
                
            return comment
            
        except Exception as e:
            logger.error(f"Failed to evaluate relevance for paper {paper.id}: {e}")
            raise

    def _build_prompt(self, paper: Paper) -> str:
        """プロンプトを構築する.
        
        Args:
            paper: 論文情報
            
        Returns:
            構築されたプロンプト
        """
        return f"""
以下のプロジェクト概要と論文情報を参考に、この論文がプロジェクトにどのように活用・応用できるかを日本語で一言コメントしてください。

【プロジェクト概要】
{self._project_overview}

【論文情報】
タイトル: {paper.title}
著者: {paper.get_formatted_authors()}
カテゴリ: {', '.join(paper.categories)}
要約: {paper.abstract}

【出力形式】
- 関連性が高い場合: 具体的な活用方法を50文字以内で提案
- 関連性が低い場合: "関連性低" とのみ回答

活用方法のコメント:
"""

    def _is_low_relevance(self, comment: str) -> bool:
        """関連性が低いかどうかを判定する.
        
        Args:
            comment: 生成されたコメント
            
        Returns:
            関連性が低い場合True
        """
        low_relevance_indicators = [
            "関連性低",
            "関連性が低い",
            "直接的な関連性はない",
            "プロジェクトには適用困難",
            "活用は困難",
        ]
        
        return any(indicator in comment for indicator in low_relevance_indicators)

    def is_enabled(self) -> bool:
        """プロジェクト関連性評価が有効かどうか."""
        return settings.is_project_relevance_enabled()


# グローバルインスタンス
_evaluator: Optional[ProjectRelevanceEvaluator] = None


def get_evaluator() -> Optional[ProjectRelevanceEvaluator]:
    """プロジェクト関連性評価器を取得する.
    
    Returns:
        評価器インスタンス（無効な場合はNone）
    """
    global _evaluator
    
    if not settings.is_project_relevance_enabled():
        return None
        
    if _evaluator is None:
        try:
            _evaluator = ProjectRelevanceEvaluator()
        except Exception as e:
            logger.error(f"Failed to initialize project relevance evaluator: {e}")
            return None
            
    return _evaluator