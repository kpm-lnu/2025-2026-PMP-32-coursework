import json


def chunk_routes(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    raw_routes = content.split("=" * 80)
    final_chunks = []

    for raw in raw_routes:
        if not raw.strip():
            continue
            
        parts = raw.split("Опис маршруту:")
        title = parts[0].replace("Назва маршруту:", "").strip()
        description = parts[1].strip() if len(parts) > 1 else ""

        
        chunk_title = {
            "text": f"МАРШРУТ: {title}\nОПИС: {description[:600]}",
            "metadata": {
                "source": "karpaty.rocks",
                "title": title,
                "type": "header_and_start"
            }
        }
        final_chunks.append(chunk_title)

        if len(description) > 600:
            remaining_text = description[600:]
            words = remaining_text.split()
            for i in range(0, len(words), 100): 
                sub_text = " ".join(words[i:i+120]) 
                final_chunks.append({
                    "text": f"МАРШРУТ (продовження): {title}\nДЕТАЛІ: {sub_text}",
                    "metadata": {
                        "source": "karpaty.rocks",
                        "title": title,
                        "type": "detail"
                    }
                })

    return final_chunks

chunks = chunk_routes("./long_term_memory/semantic/data/karpaty_routes.txt")
with open("./long_term_memory/semantic/data/chunks.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=4)

print(f"Створено {len(chunks)} чанків для RAG.")