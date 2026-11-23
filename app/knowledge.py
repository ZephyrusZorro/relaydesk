import re
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from rank_bm25 import BM25Okapi

STOP = set("the a an i my is are was has have with for to of on in and or it this that can how do does not please help me issue problem support fictional relaydesk procedure".split())


def tokens(text):
    return [t for t in re.findall(r"[\w]+", text.lower()) if t not in STOP and len(t) > 1]


class ProcedureRetriever(BaseRetriever):
    """Actual LangChain retriever; BM25 lexical relevance, not semantic embeddings."""
    documents: list[Document]
    category: str | None = None

    def _get_relevant_documents(self, query, *, run_manager):
        query_tokens = tokens(query)
        if not query_tokens or not self.documents:
            return []
        corpus_tokens = [tokens(d.page_content + " " + d.metadata["title"]) for d in self.documents]
        model = BM25Okapi(corpus_tokens)
        scores = model.get_scores(query_tokens)
        ranked = sorted(enumerate(scores), key=lambda pair: pair[1], reverse=True)
        found = []
        for i, score in ranked:
            if self.category and self.documents[i].metadata["category"] != self.category:
                continue
            overlap = set(query_tokens) & set(corpus_tokens[i])
            if score > 0.1 and overlap:
                doc = self.documents[i]
                found.append(Document(page_content=doc.page_content, metadata={**doc.metadata, "score": round(float(score), 3)}))
        return found[:3]


def retrieve(documents, query, category=None):
    # Rank against the full corpus so single-category IDF remains meaningful.
    chunks = []
    for source in documents:
        content = source["content"]
        for index, start in enumerate(range(0, len(content), 1600)):
            part = content[max(0, start - 160):start + 1600]
            chunks.append(Document(page_content=part, metadata={k: v for k, v in source.items() if k != "content"} | {"chunk_id": source["id"] if index == 0 else f"{source['id']}:{index + 1}"}))
    # Fetch all matching documents before category filtering, avoiding top-k starvation.
    retriever = ProcedureRetriever(documents=chunks, category=category)
    matches = retriever.invoke(query)
    if category == "other":
        matches = []
    return [{"id": d.metadata["chunk_id"], "title": d.metadata["title"], "excerpt": d.page_content,
             "category": d.metadata["category"], "trusted": d.metadata.get("trusted", False),
             "synthetic": d.metadata.get("synthetic", False), "score": d.metadata["score"]} for d in matches[:3]]
