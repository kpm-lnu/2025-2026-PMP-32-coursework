import json
import re

def chunk_markdown_manual(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    chunks = []
    current_h1 = ""
    current_h2 = ""
    current_h3 = ""
    current_content = []

    def save_current_chunk():
        if current_content:
            full_context = f"РОЗДІЛ: {current_h1}\nТЕМА: {current_h2}\nПІДТЕМА: {current_h3}\n\n"
            text = full_context + "".join(current_content).strip()
            
            chunks.append({
                "text": text,
                "metadata": {
                    "h1": current_h1,
                    "h2": current_h2,
                    "h3": current_h3,
                    "source": "Безпека туристів в Українських Карпатах"
                }
            })

    for line in lines:

        if line.startswith("## "):
            save_current_chunk()
            current_h1 = line.strip("# ").strip()
            current_h2, current_h3 = "", ""
            current_content = []
        elif line.startswith("### "):
            save_current_chunk()
            current_h2 = line.strip("# ").strip()
            current_h3 = ""
            current_content = []
        elif line.startswith("#### "):
            save_current_chunk()
            current_h3 = line.strip("# ").strip()
            current_content = []
        else:
            if line.strip():
                current_content.append(line)

    save_current_chunk() 
    return chunks

import os
safety_md_path = "./long_term_memory/semantic/data/safety.md"
if os.path.exists(safety_md_path):
    manual_data = chunk_markdown_manual(safety_md_path)
else:
    print(f"Файл не знайдено: {safety_md_path}")
    manual_data = []

with open("./long_term_memory/semantic/data/safety_chunks.json", "w", encoding="utf-8") as f:
    json.dump(manual_data, f, ensure_ascii=False, indent=4)

print(f"Створено {len(manual_data)} чанків з посібника з безпеки.")