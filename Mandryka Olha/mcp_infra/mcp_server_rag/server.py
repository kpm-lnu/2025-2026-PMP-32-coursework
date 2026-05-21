import asyncio
import json
import sys
import logging
import os
from pathlib import Path
from pydantic import ValidationError
from typing import Dict, List, Any

src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

try:
    from .schema import RAGSearchRequest, RAGSearchResponse, RAGAnalysisRequest, RAGAnalysisResponse, RAGSafetySearchRequest
except ImportError:
    from schema import RAGSearchRequest, RAGSearchResponse, RAGAnalysisRequest, RAGAnalysisResponse, RAGSafetySearchRequest

from long_term_memory.semantic.retriever import SemanticRetriever
from llm.groq_client import GroqClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Server("mcp-server-rag")

rag_retriever = None
llm_client = None

def _initialize_components():
    global rag_retriever, llm_client
    
    try:
        cwd = os.getcwd()
        logger.info(f"[RAG] Initializing from directory: {cwd}")
        
        vector_store_path = "./long_term_memory/vector_store"
        if not os.path.exists(vector_store_path):
            alt_path = src_path / "long_term_memory" / "vector_store"
            if os.path.exists(alt_path):
                vector_store_path = str(alt_path)
            else:
                logger.error(f"[RAG] Vector store not found at {vector_store_path} or {alt_path}")
                return False
        
        logger.info(f"[RAG] Creating SemanticRetriever with {vector_store_path}...")
        rag_retriever = SemanticRetriever(persist_dir=vector_store_path)
        logger.info("[RAG] SemanticRetriever initialized")
        
        logger.info("[RAG] Creating GroqClient...")
        llm_client = GroqClient()
        logger.info("[RAG] GroqClient initialized")
        
        logger.info("[RAG] All components initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"[RAG] Initialization error: {e}", exc_info=True)
        return False

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="rag_search",
            description="Семантичний пошук в RAG системі з існуючою базою знань про Карпати",
            inputSchema=RAGSearchRequest.model_json_schema()
        ),
        Tool(
            name="rag_analyze",
            description="Аналіз та структурування результатів RAG пошуку через LLM",
            inputSchema=RAGAnalysisRequest.model_json_schema()
        ),
        Tool(
            name="rag_safety_search",
            description="Пошук рекомендацій безпеки для туристів у Карпатах (лавини, перша допомога, спорядження, погодні небезпеки)",
            inputSchema=RAGSafetySearchRequest.model_json_schema()
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Виконання RAG інструментів"""
    global rag_retriever, llm_client
    
    logger.info(f"[RAG] Calling tool: {name}")
    
    if rag_retriever is None or llm_client is None:
        logger.error("[RAG] Components not initialized")
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "RAG components not initialized",
                "status": "not_ready"
            }, ensure_ascii=False)
        )]
    
    if name == "rag_search":
        try:
            request = RAGSearchRequest(**arguments)
            
            chunks = await rag_retriever.retrieve_async(
                query=request.query,
                k=request.k,
                where=request.where
            )
            
            response = RAGSearchResponse(
                query=request.query,
                chunks=chunks,
                count=len(chunks),
                metadata={
                    "collection_name": request.collection_name,
                    "search_params": {
                        "k": request.k,
                        "where": request.where
                    }
                }
            )
            
            logger.info(f"[RAG] Search: '{request.query}' -> {len(chunks)} results")
            
            return [TextContent(
                type="text",
                text=response.model_dump_json(ensure_ascii=False)
            )]
            
        except ValidationError as e:
            logger.error(f"[RAG] Validation error: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Validation error",
                    "details": str(e)
                }, ensure_ascii=False)
            )]
        except Exception as e:
            logger.error(f"[RAG] Search error: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Search failed",
                    "details": str(e)
                }, ensure_ascii=False)
            )]
    
    elif name == "rag_analyze":
        try:
            request = RAGAnalysisRequest(**arguments)
            
            analysis_result = await analyze_rag_results(
                query=request.query,
                chunks=request.chunks,
                analysis_type=request.analysis_type,
                preferences=request.preferences
            )
            
            logger.info(f"[RAG] Analysis: type '{request.analysis_type}' for {len(request.chunks)} chunks")
            
            return [TextContent(
                type="text",
                text=analysis_result.model_dump_json(ensure_ascii=False)
            )]
            
        except ValidationError as e:
            logger.error(f"[RAG] Validation error in analysis: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Validation error",
                    "details": str(e)
                }, ensure_ascii=False)
            )]
        except Exception as e:
            logger.error(f"[RAG] Analysis error: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Analysis failed",
                    "details": str(e)
                }, ensure_ascii=False)
            )]
    
    elif name == "rag_safety_search":
        try:
            request = RAGSafetySearchRequest(**arguments)

            safety_chunks = await rag_retriever.retrieve_async(
                query=request.query,
                k=request.k,
                where={"source": "Безпека туристів в Українських Карпатах (посібник)"}
            )

            logger.info(f"[RAG] Safety search: '{request.query}' -> {len(safety_chunks)} results")

            return [TextContent(
                type="text",
                text=json.dumps({
                    "query": request.query,
                    "safety_chunks": safety_chunks,
                    "count": len(safety_chunks)
                }, ensure_ascii=False)
            )]

        except Exception as e:
            logger.error(f"[RAG] Safety search error: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Safety search failed",
                    "details": str(e)
                }, ensure_ascii=False)
            )]

    else:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": f"Unknown tool: {name}"
            }, ensure_ascii=False)
        )]

async def analyze_rag_results(query: str, chunks: List[str], analysis_type: str, preferences: List[str]) -> RAGAnalysisResponse:
    global llm_client
    
    if analysis_type == "routes":
        system_prompt = """Ти експерт з аналізу маршрутів у Карпатах.
        Проаналізуй знайдені текстові фрагменти та витягни структуровану інформацію про маршрути.
        
        Поверни JSON з такою структурою:
        {
            "routes": [
                {
                    "name": "назва маршруту",
                    "difficulty": "легкий/середній/важкий",
                    "duration": "тривалість",
                    "distance": "відстань",
                    "description": "опис маршруту",
                    "key_points": ["ключові точки"]
                }
            ],
            "summary": "загальний підсумок",
            "recommendations": ["рекомендації"]
        }"""
    
    elif analysis_type == "safety":
        system_prompt = """Ти експерт з безпеки в горах.
        Проаналізуй фрагменти та витягни інформацію про безпеку та попередження.
        
        Поверни JSON з такою структурою:
        {
            "safety_recommendations": [
                {
                    "category": "категорія безпеки",
                    "recommendation": "текст рекомендації",
                    "priority": "висока/середня/низька"
                }
            ],
            "warnings": ["попередження"],
            "equipment": ["необхідне спорядження"],
            "emergency_info": ["контакти служб порятунку"]
        }"""
    
    else:  
        system_prompt = """Проаналізуй текстові фрагменти та витягни ключову інформацію.
        
        Поверни JSON з такою структурою:
        {
            "key_information": ["ключові факти"],
            "topics": ["основні теми"],
            "entities": ["згадані місця, об'єкти"],
            "summary": "загальний підсумок"
        }"""
    
    chunks_text = "\n\n".join([f"Фрагмент {i+1}: {chunk}" for i, chunk in enumerate(chunks[:10])])
    preferences_text = ", ".join(preferences) if preferences else "немає"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user", 
            "content": f"""Запит користувача: {query}
Вподобання: {preferences_text}

Текстові фрагменти для аналізу:
{chunks_text}

Проаналізуй та поверни структуровані дані у JSON форматі."""
        }
    ]
    
    try:
        response = await llm_client.generate(messages, json_mode=True)
        structured_data = json.loads(response.content)
        
        confidence = min(0.9, len(chunks) * 0.15 + 0.3)
        
        if analysis_type == "routes":
            summary = f"Знайдено {len(structured_data.get('routes', []))} маршрутів"
        elif analysis_type == "safety":
            summary = f"Виявлено {len(structured_data.get('safety_recommendations', []))} рекомендацій безпеки"
        else:
            summary = f"Проаналізовано {len(chunks)} фрагментів загальної інформації"
        
        return RAGAnalysisResponse(
            analysis_type=analysis_type,
            structured_data=structured_data,
            summary=summary,
            confidence=confidence,
            metadata={
                "chunks_processed": len(chunks),
                "preferences_considered": preferences,
                "llm_model": "groq/llama"
            }
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"[RAG] JSON parse error from LLM: {e}")
        fallback_data = {
            "error": "Failed to parse LLM response",
            "raw_response": response.content[:500] if 'response' in locals() else "No response"
        }
        
        return RAGAnalysisResponse(
            analysis_type=analysis_type,
            structured_data=fallback_data,
            summary="Analysis failed",
            confidence=0.1,
            metadata={"error": str(e)}
        )
    
    except Exception as e:
        logger.error(f"[RAG] LLM analysis error: {e}", exc_info=True)
        raise


async def main():
    """Запуск MCP RAG сервера з ініціалізацією компонентів"""
    logger.info("[RAG] Starting RAG MCP server...")
    
    if _initialize_components():
        logger.info("[RAG] Components initialized, server ready")
    else:
        logger.error("[RAG] Failed to initialize components - exiting")
        return
    
    logger.info("[RAG] Starting MCP server on stdio")
    async with stdio_server() as streams:
        await app.run(
            streams[0], streams[1], app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())