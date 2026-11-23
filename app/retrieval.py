"""Versioned hybrid lexical RAG index with a bounded query cache."""
from collections import Counter, OrderedDict
from copy import deepcopy
from math import sqrt
from threading import RLock
from time import perf_counter
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from rank_bm25 import BM25Okapi
from .knowledge import tokens

EXPANSIONS = {"wifi": ["wireless", "wi-fi"], "screen": ["monitor", "display"], "login": ["account", "sign-in"], "authentication": ["mfa", "authenticator"], "tunnel": ["vpn"], "app": ["application", "software"]}


def grams(text):
    value = " ".join(tokens(text))
    return Counter(value[i:i+3] for i in range(max(0, len(value)-2)))


class HybridRetriever(BaseRetriever):
    documents: list[Document]
    model: object
    token_sets: list[set]
    vectors: list[Counter]
    norms: list[float]
    category: str | None = None

    def _get_relevant_documents(self, query, *, run_manager):
        words = tokens(query)
        expanded = words + [word for token in words for word in EXPANSIONS.get(token, [])]
        if not expanded or self.category == "other":
            return []
        scores = self.model.get_scores(expanded)
        vector = grams(" ".join(expanded))
        norm = sqrt(sum(v*v for v in vector.values())) or 1
        candidates = [i for i,d in enumerate(self.documents) if (not self.category or d.metadata["category"] == self.category) and scores[i] > 0.1 and set(expanded) & self.token_sets[i]]
        bm = sorted(candidates, key=lambda i: scores[i], reverse=True)
        similarity = {i: sum(v*self.vectors[i].get(k, 0) for k,v in vector.items())/(norm*self.norms[i]) for i in candidates}
        char = sorted(candidates, key=lambda i: similarity[i], reverse=True)
        bm_rank = {ident: rank for rank,ident in enumerate(bm)}
        char_rank = {ident: rank for rank,ident in enumerate(char)}
        fused = {i: 1/(61+bm_rank[i]) + 1/(61+char_rank[i]) for i in candidates}
        return [Document(page_content=self.documents[i].page_content, metadata={**self.documents[i].metadata, "score": round(fused[i]*1000, 3)}) for i in sorted(candidates, key=lambda i: fused[i], reverse=True)[:3]]


class KnowledgeIndex:
    def __init__(self, store):
        self.store = store
        self.lock = RLock()
        self.revision = -1
        self.builds = 0
        self.queries = 0
        self.hits = 0
        self.cache = OrderedDict()
        self.retriever = None
        self.build_ms = 0

    def _ensure(self):
        if self.revision == self.store.knowledge_revision():
            return
        start = perf_counter()
        revision, sources = self.store.knowledge_snapshot()
        docs = []
        for source in sources:
            for index, offset in enumerate(range(0, len(source["content"]), 1600)):
                text = source["content"][max(0, offset-160):offset+1600]
                meta = {k:v for k,v in source.items() if k not in {"content", "steps"}}
                docs.append(Document(page_content=text, metadata={**meta, "chunk_id": source["id"] if not index else f"{source['id']}:{index+1}"}))
        if docs:
            terms = [tokens(d.page_content + " " + d.metadata["title"]) for d in docs]
            vectors = [grams(d.page_content) for d in docs]
            self.retriever = HybridRetriever(documents=docs, model=BM25Okapi(terms), token_sets=[set(t) for t in terms], vectors=vectors, norms=[sqrt(sum(v*v for v in vec.values())) or 1 for vec in vectors])
        else:
            self.retriever = None
        self.revision = revision
        self.builds += 1
        self.cache.clear()
        self.build_ms = round((perf_counter()-start)*1000, 3)

    def search(self, query, category=None):
        start = perf_counter()
        with self.lock:
            self._ensure()
            self.queries += 1
            key = (self.revision, query.strip().lower(), category)
            hit = key in self.cache
            if hit:
                self.hits += 1
                citations = deepcopy(self.cache[key])
                self.cache.move_to_end(key)
            else:
                retriever = self.retriever.model_copy(update={"category": category}) if self.retriever else None
                found = retriever.invoke(query) if retriever else []
                citations = [{"id": d.metadata["chunk_id"], "title": d.metadata["title"], "excerpt": d.page_content, "category": d.metadata["category"], "trusted": d.metadata.get("trusted", False), "synthetic": d.metadata.get("synthetic", False), "score": d.metadata["score"]} for d in found]
                self.cache[key] = deepcopy(citations)
                if len(self.cache)>128:
                    self.cache.popitem(last=False)
            return {"citations": citations, "retrieval": "Hybrid lexical · BM25 + character similarity", "diagnostics": {"cache_hit": hit, "index_revision": self.revision, "indexed_chunks": len(self.retriever.documents) if self.retriever else 0, "search_ms": round((perf_counter()-start)*1000, 3)}}

    def stats(self):
        with self.lock:
            self._ensure()
            return {"revision": self.revision, "builds": self.builds, "queries": self.queries, "cache_hits": self.hits, "cache_entries": len(self.cache), "build_ms": self.build_ms, "chunks": len(self.retriever.documents) if self.retriever else 0}
