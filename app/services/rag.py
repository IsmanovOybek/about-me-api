from __future__ import annotations

from functools import lru_cache

from app.config import Settings, get_settings
from app.services.embeddings import EmbeddingProvider, get_embedding_provider
from app.services.ingest import ChromaVectorStore, VectorStore
from app.services.llm import LLMProvider, get_llm_provider

LOCALE_NAMES = {
    "en": "English",
    "ko": "Korean",
    "ru": "Russian",
    "uz": "Uzbek",
}

UNKNOWN_REPLY = {
    "en": (
        "There is no clear information about this in Oybek's About Me knowledge base. "
        "Please ask about his profile, education, skills, experience, projects, or this portfolio site."
    ),
    "ko": (
        "Oybek의 About Me 지식 베이스에 이에 대한 명확한 정보가 없습니다. "
        "프로필, 학력, 기술, 경력, 프로젝트 또는 이 포트폴리오 사이트에 대해 질문해 주세요."
    ),
    "ru": (
        "В базе знаний About Me об Oybek нет точной информации об этом. "
        "Спросите о профиле, образовании, навыках, опыте, проектах или этом портфолио-сайте."
    ),
    "uz": (
        "Oybekning About Me bilim bazasida bu haqida aniq ma’lumot yo‘q. "
        "Profili, ta’limi, skilllari, tajribasi, loyihalari yoki shu portfolio sayti haqida so‘rang."
    ),
}


def build_system_prompt(locale: str) -> str:
    language = LOCALE_NAMES.get(locale, "English")
    return f"""You are the AI Assistant on Oybek Ismanov's (Bek / 베크) personal About Me / portfolio website.

Identity:
- His English/common nickname is Bek. In Korean, call him 베크.
- This site is Oybek's (Bek) personal About Me portfolio platform with an AI assistant.
- When the user asks what this platform/site is, explain it as his personal portfolio / About Me site.
- In Korean replies, prefer 베크 for his name.

Answer style:
- Reply in {language}.
- Use ONLY the provided context. Do not invent facts.
- If the context does not contain the answer, say clearly that this information is not in the knowledge base.
- Do NOT give overly short one-line answers.
- Write natural, clear, well-structured replies (usually 2–6 sentences; more for broad questions).
- For broad questions, combine related context into one complete answer.
- For projects: explain what it is, main features, tech stack, year, and link when available.
- When the user asks about projects in general, list the featured ones with links if present in context (especially AutoCare AI, Mashaqqat, Static Engine).
- Be professional, friendly, and helpful — like a portfolio guide.
- Only mention projects that appear in the context.
"""


class RagService:
    def __init__(
        self,
        settings: Settings | None = None,
        embeddings: EmbeddingProvider | None = None,
        llm: LLMProvider | None = None,
        store: VectorStore | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.embeddings = embeddings or get_embedding_provider()
        self.llm = llm or get_llm_provider()
        self.store = store or ChromaVectorStore(
            self.settings.chroma_path,
            self.settings.chroma_collection,
        )

    def answer(self, message: str, locale: str = "en") -> str:
        query_vector = self.embeddings.embed_query(message)
        chunks = self.store.query(query_vector, top_k=self.settings.top_k)

        if not chunks:
            return UNKNOWN_REPLY.get(locale, UNKNOWN_REPLY["en"])

        context = self._format_context(chunks)
        system_prompt = build_system_prompt(locale)
        user_prompt = (
            f"Context:\n{context}\n\n"
            f"User question:\n{message}\n\n"
            "Answer using only the context above. "
            "Give a complete, natural answer — not a tiny one-liner."
        )
        reply = self.llm.generate(system_prompt=system_prompt, user_prompt=user_prompt)
        return reply or UNKNOWN_REPLY.get(locale, UNKNOWN_REPLY["en"])

    @staticmethod
    def _format_context(chunks: list[dict]) -> str:
        parts: list[str] = []
        for i, chunk in enumerate(chunks, start=1):
            meta = chunk.get("metadata") or {}
            title = meta.get("title") or chunk.get("id") or f"chunk-{i}"
            parts.append(f"[{i}] {title}\n{chunk.get('document', '')}")
        return "\n\n".join(parts)


@lru_cache
def get_rag_service() -> RagService:
    return RagService()
