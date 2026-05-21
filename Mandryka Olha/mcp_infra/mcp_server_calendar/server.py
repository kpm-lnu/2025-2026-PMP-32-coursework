import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4

from pydantic import ValidationError
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from schema import CalendarDayEventRequest


app = Server("mcp-server-calendar")

def build_ical_event(
    title: str,
    date: str,
    description: str | None,
    location: str | None
) -> str:
    uid = f"{uuid4()}@pathguard"
    dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    dtstart = date_obj.strftime("%Y%m%d")
    dtend = (date_obj + timedelta(days=1)).strftime("%Y%m%d")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//PathGuard//Calendar MCP//UA",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART;VALUE=DATE:{dtstart}",
        f"DTEND;VALUE=DATE:{dtend}",
        f"SUMMARY:{title}",
    ]

    if description:
        lines.append(f"DESCRIPTION:{description}")

    if location:
        lines.append(f"LOCATION:{location}")

    lines.extend([
        "END:VEVENT",
        "END:VCALENDAR"
    ])

    return "\n".join(lines)


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="create_ical_event",
            description=(
                "Створює .ics файл з днем походу (all-day подія). "
                "Файл можна імпортувати в Google Calendar, Apple Calendar або Outlook."
            ),
            inputSchema=CalendarDayEventRequest.model_json_schema()
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name != "create_ical_event":
        return [TextContent(type="text", text="Невідомий tool")]

    try:
        req = CalendarDayEventRequest(**arguments)
    except ValidationError as e:
        return [TextContent(type="text", text=f"Помилка валідації:\n{e}")]

    ical_text = build_ical_event(
        title=req.title,
        date=req.date,
        description=req.description,
        location=req.location
    )

    filename = req.filename or f"hike_{req.date}.ics"
    filepath = Path.cwd() / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(ical_text)

    response_text = f"""#iCal файл створено 

**Файл:** `{filename}`

### Що далі
— відкрий файл або імпортуй його в календар  
— Google Calendar / Apple Calendar / Outlook підтримуються  
— подія створена як **all-day event**

### Дані події
```text
{ical_text}
```
"""

    return [TextContent(type="text", text=response_text)]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
