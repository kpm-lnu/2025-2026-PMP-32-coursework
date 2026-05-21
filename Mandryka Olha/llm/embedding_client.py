import os
import httpx
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

_HTTP_TIMEOUT = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)

class EmbeddingClient:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT").rstrip('/') + '/'
        self.model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.deployment = os.getenv("EMBEDDING_DEPLOYMENT", self.model_name)
        self.api_version = os.getenv("EMBEDDING_API_VERSION", "2024-12-01-preview")

        api_key = os.getenv("EMBEDDING_API_KEY")
        if not api_key:
            raise ValueError("EMBEDDING_API_KEY не знайдено в .env файлі")

        self.client = AzureOpenAI(
            api_version=self.api_version,
            azure_endpoint=self.endpoint,
            api_key=api_key,
            http_client=httpx.Client(timeout=_HTTP_TIMEOUT),
            max_retries=0,
        )

    def embed(self, text: str) -> list[float]:
        try:
            response = self.client.embeddings.create(
                model=self.deployment,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise RuntimeError(f"Помилка embedding: {str(e)}")
