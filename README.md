# Mimi Leads Bot

> Telegram bot for agency managers to capture and triage client leads — add them through a guided dialog and change their status with inline buttons.

## Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![asyncio](https://img.shields.io/badge/asyncio-3776AB?style=for-the-badge&logo=python&logoColor=white)

## Features

- **Guided lead creation** — `/new` runs a `ConversationHandler`: name → contact → message → confirm.
- **Inline status management** — change a lead between `new` / `in_progress` / `done` with buttons, right in the chat.
- **Recent leads & stats** — `/leads` lists the latest entries; `/stats` shows counts by status.
- **Self-contained storage** — async SQLite (`aiosqlite`); no external services needed to run.
- **API-ready** — can instead read leads from [`mimi-leads-api`](https://github.com/alyoshagafurov/mimi-leads-api) (see below).
- **Robust** — central error handler, structured logging, HTML-escaped user input.

## Screenshots / Demo

<!-- TODO: screenshot of the /new dialog and inline status buttons -->

## Installation & Run

Requires Python 3.11+ and a bot token from [@BotFather](https://t.me/BotFather).

### Quick start

```bash
git clone https://github.com/alyoshagafurov/mimi-leads-bot.git
cd mimi-leads-bot
./run.sh                 # sets everything up, then asks for your token
# edit .env -> TELEGRAM_BOT_TOKEN=<token from @BotFather>
./run.sh                 # run again to start the bot
```

`run.sh` creates the virtualenv, installs dependencies and generates `.env`. The
only manual step is pasting your bot token. On Windows, use the manual steps below.

### Manual setup

```bash
# 1. Clone and enter the project
git clone https://github.com/alyoshagafurov/mimi-leads-bot.git
cd mimi-leads-bot

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your token
cp .env.example .env             # Windows: copy .env.example .env
#    then edit .env and set TELEGRAM_BOT_TOKEN=...

# 5. Run the bot (long polling)
python -m bot.main
```

## Commands

| Command   | Description                                              |
| --------- | -------------------------------------------------------- |
| `/start`  | Welcome message and quick overview                       |
| `/help`   | Full list of commands                                    |
| `/new`    | Add a lead via a step-by-step dialog with confirmation   |
| `/leads`  | Show the latest leads, each with inline status buttons   |
| `/stats`  | Show counts of leads by status                           |
| `/cancel` | Abort the current `/new` dialog                          |

## How it works together

This bot is one half of a small lead-intake system. The companion project is
[`mimi-leads-api`](https://github.com/alyoshagafurov/mimi-leads-api) — a FastAPI backend.

```
  ┌────────────────────┐    POST /leads (JSON)    ┌─────────────────────┐
  │   Next.js sites    │ ───────────────────────▶ │   mimi-leads-api    │
  │  (kha.tj, mimi…)   │     form submission      │      (FastAPI)      │
  └────────────────────┘                          └──────────┬──────────┘
                                                             │ on new lead:
                                                             │ Telegram Bot API
                                                             ▼
                                                  ┌─────────────────────┐
   manager reviews & updates status in chat  ◀──  │   mimi-leads-bot    │
   /leads · /stats · inline status buttons        │ (python-telegram-bot)│
                                                  └─────────────────────┘
```

- **Inbound:** when a website form hits `POST /leads`, the API notifies this bot
  through the Telegram Bot API, so the manager sees new leads instantly.
- **Outbound / standalone:** the bot can also create leads itself via `/new`,
  storing them in its own SQLite database — useful for phone or walk-in enquiries.

Each project runs independently; together they cover both website and manual intake.

### Connecting the bot to the API

By default the bot uses its own SQLite database. To make it read the **same**
leads the API stores, point it at `mimi-leads-api` instead:

1. Set the following in `.env`:
   ```
   API_ENABLED=true
   API_BASE_URL=http://localhost:8000
   ```
2. Add a tiny API client (`bot/api_client.py`) and call it from the handlers:
   ```python
   import httpx
   from .config import get_settings

   settings = get_settings()

   async def list_leads(limit: int = 10) -> list[dict]:
       async with httpx.AsyncClient(base_url=settings.api_base_url, timeout=10) as client:
           resp = await client.get("/leads", params={"limit": limit})
           resp.raise_for_status()
           return resp.json()["items"]

   async def update_status(lead_id: int, status: str) -> None:
       async with httpx.AsyncClient(base_url=settings.api_base_url, timeout=10) as client:
           resp = await client.patch(f"/leads/{lead_id}", json={"status": status})
           resp.raise_for_status()
   ```
3. In `handlers.py`, swap `from . import database as db` for `from . import api_client as db`
   when `settings.api_enabled` is true. The handler code stays the same because the
   function signatures match.

This turns the two projects into a single system with one shared source of truth.

## Project structure

```
mimi-leads-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py         # entrypoint: builds the Application and handlers
│   ├── config.py       # pydantic-settings configuration
│   ├── database.py     # async SQLite storage
│   ├── keyboards.py    # inline keyboards
│   └── handlers.py     # commands, /new conversation, callbacks
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```
