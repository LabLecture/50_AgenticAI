"""
_judges.py — Ragas / DeepEval 의 심판 LLM 을 OpenRouter free 모델로 wrap

Ragas:   LangchainLLMWrapper(ChatOpenAI(OpenRouter)) — 그대로 동작.
DeepEval: DeepEvalBaseLLM 서브클래스 필요 (OpenAI 키 없이 OpenRouter 사용).
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from _common import get_llm


def ragas_judge():
    """Ragas 메트릭에 주입할 심판 LLM (LangChain wrapper)."""
    from ragas.llms import LangchainLLMWrapper
    llm = get_llm()
    if llm is None:
        return None
    return LangchainLLMWrapper(llm)


def ragas_embeddings():
    """Ragas 의 TestsetGenerator / 일부 메트릭이 요구하는 임베딩."""
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from _common import get_embeddings
    return LangchainEmbeddingsWrapper(get_embeddings())


# ─────────────────────────────────────────────────────────────────────
# DeepEval — DeepEvalBaseLLM 서브클래스로 OpenRouter free 모델 사용
# ─────────────────────────────────────────────────────────────────────
def deepeval_judge():
    from deepeval.models.base_model import DeepEvalBaseLLM
    from pydantic import BaseModel
    import instructor
    import json

    class OpenRouterJudge(DeepEvalBaseLLM):
        """OpenRouter free 모델 (gpt-oss-20b 등) 을 DeepEval 의 심판 LLM 으로."""

        def __init__(self):
            self._llm = get_llm()

        def load_model(self):
            return self._llm

        def generate(self, prompt: str, schema: type[BaseModel] | None = None):
            text = self._llm.invoke(prompt).content
            if schema is None:
                return text
            # schema 가 주어지면 JSON 파싱 시도 (free 모델 호환을 위해 관대하게)
            try:
                from json_repair import repair_json
                fixed = repair_json(text, return_objects=True)
                return schema.model_validate(fixed)
            except Exception:
                return schema()  # 빈 인스턴스 — 실패 시 graceful fallback

        async def a_generate(self, prompt: str, schema: type[BaseModel] | None = None):
            return self.generate(prompt, schema)

        def get_model_name(self) -> str:
            try:
                return self._llm.model_name
            except Exception:
                return "openrouter-free"

    judge = OpenRouterJudge()
    return judge
