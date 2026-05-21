import asyncio
import sys
import logging
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from typing import List
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from llm.embedding_client import EmbeddingClient

logger = logging.getLogger(__name__)

class SemanticRetriever:
    def __init__(
        self,
        persist_dir="./long_term_memory/vector_store",
        collection_name="karpaty_knowledge"  
    ):
        load_dotenv()
        
        self.embedding_client = EmbeddingClient()
        logger.debug("Azure OpenAI embedding client initialized")

        self.chroma_client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        collection_count = self.collection.count()
        logger.debug(f"Collection loaded with {collection_count} documents")

    def _get_query_embedding(self, query: str) -> List[float]:
     
        try:
            return self.embedding_client.embed(query)
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            raise

    async def _get_query_embedding_async(self, query: str) -> List[float]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.embedding_client.embed, query)

    async def retrieve_async(
        self,
        query: str,
        k: int = 5,
        where: dict | None = None,
    ) -> List[str]:
        try:
            query_vector = await self._get_query_embedding_async(query)
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self.collection.query(
                    query_embeddings=[query_vector],
                    n_results=k,
                    where=where,
                )
            )
            documents = results.get("documents", [])
            return documents[0] if documents and len(documents) > 0 else []
        except Exception as e:
            logger.error(f"Помилка семантичного пошуку: {e}")
            logger.info("Fallback: keyword пошук по JSON файлах,,,")
            return self._keyword_fallback(query, k, where)

    def retrieve(
        self,
        query: str,
        k: int = 5,
        where: dict | None = None
    ) -> List[str]:
        try:
            query_vector = self._get_query_embedding(query)

            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=k,
                where=where
            )

            documents = results.get("documents", [])

            return documents[0] if documents and len(documents) > 0 else []

        except Exception as e:
            logger.error(f"Помилка семантичного пошуку: {e}")
            logger.info("Fallback: keyword пошук по JSON файлах...")
            return self._keyword_fallback(query, k, where)

    def _keyword_fallback(self, query: str, k: int = 5, where: dict | None = None) -> List[str]:
        """Fallback: пошук за ключовими словами напряму з JSON файлів коли Embedding API недоступний."""
        import json as _json
        data_dir = Path(__file__).parent / "data"
        files = ["chunks.json", "safety_chunks.json"]

        keywords = [w.lower() for w in query.split() if len(w) > 2]
        if not keywords:
            return []

        scored: List[tuple] = []  

        for fname in files:
            fpath = data_dir / fname
            if not fpath.exists():
                continue
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    chunks = _json.load(f)
                for chunk in chunks:
                    text = chunk.get("text", "")
                    meta = chunk.get("metadata", {})

                    if where:
                        match = all(meta.get(wk) == wv for wk, wv in where.items())
                        if not match:
                            continue

                    text_lower = text.lower()
                    score = sum(1 for kw in keywords if kw in text_lower)
                    if score > 0:
                        scored.append((score, text))
            except Exception as err:
                logger.warning(f"Keyword fallback: помилка читання {fname}: {err}")

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [text for _, text in scored[:k]]
        logger.info(f"Keyword fallback: знайдено {len(results)} результатів для '{query[:50]}'")
        return results

#if __name__ == "__main__":
#    retriever = SemanticRetriever()
#    question = "Звідки йти на Піп Іван?" 
#    context_chunks = retriever.retrieve(question, k=2)
    
#    print(f"\n Питання: {question}")
#    print("=" * 50)
    
#    if not context_chunks:
#        print("Нічого не знайдено. запусти інгест")
#    else:
#        for i, chunk in enumerate(context_chunks, 1):
#            print(f" ЗНАЙДЕНИЙ КОНТЕКСТ {i}:")
#            print(f"{chunk[:300]}...") 
#            print("-" * 50)