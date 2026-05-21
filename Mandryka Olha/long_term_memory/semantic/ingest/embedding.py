import chromadb
import json
import time
import hashlib 
import sys
from dotenv import load_dotenv
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from llm.embedding_client import EmbeddingClient

load_dotenv()

embedding_client = EmbeddingClient()
print("embedding клієнт ініціалізовано")

chroma_client = chromadb.PersistentClient(path="./long_term_memory/vector_store")

collection = chroma_client.get_or_create_collection(
    name="karpaty_knowledge_base",
    metadata={"hnsw:space": "cosine"}
)

def get_text_hash(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def is_embedding_cached(text_hash: str) -> bool:
    try:
        existing = collection.get(ids=[text_hash])
        return len(existing['ids']) > 0
    except:
        return False

def process_and_upload(chunks_file):
    if not Path(chunks_file).exists():
        print(f"  Файл {chunks_file} не знайдено, пропускаємо")
        return
    
    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f" Починаємо індексацію {len(chunks)} чанків з файлу {chunks_file}")
    
    processed = 0
    skipped = 0
    batch_size = 10
    
    for i, chunk in enumerate(chunks):
        text_to_embed = chunk['text']
        text_hash = get_text_hash(text_to_embed)
        
        if is_embedding_cached(text_hash):
            skipped += 1
            if i % batch_size == 0:
                print(f"Пропущено дублікат {i}/{len(chunks)} (кешовано: {skipped})")
            continue
        
        try:
            embedding = embedding_client.embed(text_to_embed)

            collection.add(
                ids=[text_hash],
                embeddings=[embedding],
                metadatas=[{
                    **chunk['metadata'],
                    'source_file': chunks_file,
                    'processed_at': time.time()
                }],
                documents=[text_to_embed]
            )
            
            processed += 1
            
            if i % batch_size == 0:
                print(f" Оброблено {processed}/{len(chunks)} чанків (пропущено: {skipped})")
            
            if processed % 5 == 0:
                time.sleep(0.2)  

        except Exception as e:
            print(f" Помилка на чанку {i}: {e}")
            time.sleep(1.0)

    print(f" Завершено: оброблено {processed}, пропущено {skipped} з {len(chunks)} чанків")

def main():
    print("індексація з embeddings")
    
    files_to_process = [
        "./long_term_memory/semantic/data/chunks.json",
        "./long_term_memory/semantic/data/safety_chunks.json"
    ]
    
    total_start = time.time()
    
    for file_path in files_to_process:
        file_start = time.time()
        process_and_upload(file_path)
        file_time = time.time() - file_start
        print(f" Файл {Path(file_path).name} оброблено за {file_time:.1f}с")
    
    total_time = time.time() - total_start
    
    collection_count = collection.count()
    print(f"\n Векторна база створена")
    print(f" Загальна кількість записів: {collection_count}")
    print(f" Загальний час: {total_time:.1f}с")

if __name__ == "__main__":
    main()