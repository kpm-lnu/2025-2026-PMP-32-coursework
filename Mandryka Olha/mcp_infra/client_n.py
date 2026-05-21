# mcp_infra/client.py
import asyncio
from typing import Dict, List, Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import logging
import sys
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class MCPClient:

    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.available_tools: Dict[str, List] = {}
        self._stdio_tasks: Dict[str, asyncio.Task] = {}
        self._stdio_shutdown: Dict[str, asyncio.Event] = {}

        python_exe = sys.executable
        base_dir = Path(__file__).parent.parent

        self.server_configs = {
            "mcp-server-calendar": {
                "command": python_exe,
                "args": [str(base_dir / "mcp_infra/mcp_server_calendar/server.py")]
            },
            "mcp-server-weather": {
                "command": python_exe,
                "args": [str(base_dir / "mcp_infra/mcp_server_weather/server.py")]
            },
            "mcp-server-navigation": {
                "command": python_exe,
                "args": [str(base_dir / "mcp_infra/mcp_server_navigation/server.py")]
            },
            "mcp-server-map": {
                "command": python_exe,
                "args": [str(base_dir / "mcp_infra/mcp_server_map_geo/server.py")]
            },
            "mcp-server-rag": {
                "command": python_exe,
                "args": [str(base_dir / "mcp_infra/mcp_server_rag/server.py")]
            }
        }

    async def connect_all(self):

        for server_name, config in self.server_configs.items():
            if server_name not in self.sessions:
                await self._connect_to_server(server_name, config)

    async def _connect_to_server(self, server_name: str, config: Dict[str, Any]):
        try:
            logger.info(f"[*] Connecting to {server_name}...")
            server_params = StdioServerParameters(
                command=config["command"],
                args=config.get("args", []),
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
                cwd=str(Path(__file__).parent.parent)
            )

            shutdown_event = asyncio.Event()
            ready = asyncio.get_running_loop().create_future()
            self._stdio_shutdown[server_name] = shutdown_event
            self._stdio_tasks[server_name] = asyncio.create_task(
                self._run_stdio_context(server_name, server_params, ready, shutdown_event)
            )
            async with asyncio.timeout(15.0):
                read, write = await ready
            
            session = ClientSession(read, write)
            await session.__aenter__()
            
            logger.info(f"[*] Initializing session for {server_name}...")
            async with asyncio.timeout(60.0):
                await session.initialize()
            
            async with asyncio.timeout(30.0):
                tools_res = await session.list_tools()
            self.available_tools[server_name] = tools_res.tools
            self.sessions[server_name] = session
            logger.info(f"[+] Connected to {server_name}")
            
        except Exception as e:
            logger.error(f"[-] Failed to connect to {server_name}: {e}")
            await self._shutdown_stdio(server_name)

    async def _run_stdio_context(
        self,
        server_name: str,
        server_params: StdioServerParameters,
        ready: asyncio.Future,
        shutdown_event: asyncio.Event,
    ) -> None:
        try:
            async with stdio_client(server_params) as (read, write):
                if not ready.done():
                    ready.set_result((read, write))
                await shutdown_event.wait()
        except Exception as e:
            if not ready.done():
                ready.set_exception(e)
            logger.error(f"[-] Stdio context error for {server_name}: {e}")

    async def _shutdown_stdio(self, server_name: str) -> None:
        shutdown_event = self._stdio_shutdown.pop(server_name, None)
        if shutdown_event:
            shutdown_event.set()

        task = self._stdio_tasks.pop(server_name, None)
        if task:
            try:
                await task
            except Exception:
                pass

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: float = 60.0,
    ) -> Any:
        if server_name not in self.sessions:
            raise ValueError(f"Сервер {server_name} не підключений")
        session = self.sessions[server_name]
        try:
            async with asyncio.timeout(timeout):
                return await session.call_tool(tool_name, arguments)
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Інструмент '{tool_name}' на '{server_name}' не відповів за {timeout}s"
            )

    def get_tools_for_prompt(self) -> str:
        tools_description = []
        for server_name, tools in self.available_tools.items():
            tools_description.append(f"\n## {server_name.upper()} Server Tools:")
            for tool in tools:
                tools_description.append(f"- {tool.name}: {tool.description}")
        return "\n".join(tools_description)

    async def disconnect_all(self):
        for name, session in list(self.sessions.items()):
            try:
                await session.__aexit__(None, None, None)
            except: pass
        for name in list(self._stdio_tasks.keys()):
            await self._shutdown_stdio(name)
        self.sessions.clear()
        self._stdio_tasks.clear()
        self._stdio_shutdown.clear()

_mcp_client_instance: Optional[MCPClient] = None

async def get_mcp_client() -> MCPClient:
    global _mcp_client_instance
    if _mcp_client_instance is None:
        _mcp_client_instance = MCPClient()
        await _mcp_client_instance.connect_all()
    return _mcp_client_instance

if __name__ == "__main__":
    async def main():
        client = await get_mcp_client()
        print("Доступні інструменти:")
        print(client.get_tools_for_prompt())
        await client.disconnect_all()

    asyncio.run(main())