import os
import json
import time
import sys
from pathlib import Path
from dotenv import load_dotenv
import chromadb

sys.path.append(str(Path(__file__).parent.parent))
from llm.embedding_client import EmbeddingClient

load_dotenv()

embedder = EmbeddingClient()

chroma_client = chromadb.PersistentClient(path="./long_term_memory/vector_store")
collection_name = "karpaty_knowledge"

try:
    chroma_client.delete_collection(name=collection_name)
    print(f"Колекцію '{collection_name}' видалено для оновлення розмірності.")
except:
    pass

collection = chroma_client.create_collection(name=collection_name)

def read_json_chunks(path: str):
    p = Path(path)
    if not p.exists():
        print(f" Файл не знайдено: {path}")
        return []
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def ingest_data(file_path: str):
    chunks = read_json_chunks(file_path)
    if not chunks:
        return

    print(f"Починаємо обробку {len(chunks)} чанків з {file_path} через Azure OpenAI...")

    for i, chunk in enumerate(chunks):
        text_content = chunk["text"]
        metadata = chunk["metadata"]

        try:
            vector = embedder.embed(text_content)

            collection.add(
                ids=[f"{metadata.get('source', 'unknown')}_{i}_{int(time.time())}"],
                embeddings=[vector],
                metadatas=[metadata],
                documents=[text_content]
            )

            if i % 10 == 0:
                print(f"Оброблено {i}/{len(chunks)}...")
            
        except Exception as e:
            print(f"Помилка на чанку {i}: {e}")
            continue

if __name__ == "__main__":
    ingest_data("./long_term_memory/semantic/data/chunks.json")
    
    ingest_data("./long_term_memory/semantic/data/safety_chunks.json")

    print("\n Індексацію завершено. Векторна пам'ять готова.")