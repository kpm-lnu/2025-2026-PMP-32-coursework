from llama_parse import LlamaParse
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()
llama_key = os.getenv("LLAMA_CLOUD_API_KEY")

if not llama_key:
    raise ValueError("LLAMA_CLOUD_API_KEY не знайдено у файлі .env або в оточеннях")

os.environ["LLAMA_CLOUD_API_KEY"] = llama_key
print("Ключ LlamaParse завантажено")

def parse_with_llamaparse(pdf_path: str, output_md: str = "./long_term_memory/semantic/data/safety.md"):
    parser = LlamaParse(
        result_type="markdown",          
        language="uk",                   
        system_prompt=(
            "Extract main content only. Skip headers, footers, page numbers. "
            "Preserve sections, lists, tables as markdown. "
            "Handle Ukrainian text accurately. Ignore artifacts like  or ."
        ),
        num_workers=4,                   
        verbose=True
    )

    documents = parser.load_data(pdf_path)
    
    full_md = "\n\n".join([doc.text for doc in documents])
    
    documents = [doc for i, doc in enumerate(documents) if 3 <= i < len(documents)-1]
    
    with open(output_md, "w", encoding="utf-8") as f:
        f.write(full_md)
    
    print(f"Збережено у {output_md} ({len(full_md):,} символів)")
    print("Початок:", full_md[:300])

pdf_file = "./long_term_memory/semantic/sources/porady_ryatuvalnikiv_v_karpatah.pdf"
parse_with_llamaparse(pdf_file)