from app.analyzers.base import Analyzer
from app.analyzers.complexity import ComplexityAnalyzer
from app.analyzers.security import SecurityAnalyzer
from app.analyzers.style import StyleAnalyzer


def build_analyzers(include_llm:bool = True) -> list[Analyzer]:

    analyzers: list[Analyzer] = [
        ComplexityAnalyzer(),
        SecurityAnalyzer(),
        StyleAnalyzer()
    ]

    if include_llm:
        from app.analyzers.llm_reviewer import LLMReviewAnalyzer
        analyzers.append(LLMReviewAnalyzer())
    return analyzers