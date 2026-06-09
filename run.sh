#!/usr/bin/env bash
#
# One-command launcher for mimi-leads-bot.
# Creates a virtual environment, installs dependencies, prepares .env,
# and starts the bot. Safe to run repeatedly.
#
# The ONLY thing you must provide is a bot token from @BotFather.
#
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"

# 1. Virtual environment
if [ ! -d ".venv" ]; then
  echo "==> Creating virtual environment (.venv)"
  "$PYTHON" -m venv .venv
fi

# 2. Dependencies (only the first time)
if [ ! -f ".venv/.deps-installed" ]; then
  echo "==> Installing dependencies"
  ./.venv/bin/python -m pip install -q --upgrade pip
  ./.venv/bin/pip install -q -r requirements.txt
  touch ".venv/.deps-installed"
fi

# 3. Local config
if [ ! -f ".env" ]; then
  echo "==> Creating .env from .env.example"
  cp .env.example .env
fi

# 4. Require a token before starting
if ! grep -qE '^TELEGRAM_BOT_TOKEN=.+' .env; then
  echo ""
  echo "------------------------------------------------------------------"
  echo "  Almost there! Your bot token is not set yet."
  echo ""
  echo "  1) In Telegram, open @BotFather and send:  /newbot"
  echo "  2) Copy the token it gives you (looks like 123456:ABC-DEF...)"
  echo "  3) Open the file  .env  and set:"
  echo "         TELEGRAM_BOT_TOKEN=123456:ABC-DEF..."
  echo "  4) Run  ./run.sh  again"
  echo "------------------------------------------------------------------"
  exit 1
fi

# 5. Run
echo "==> Starting bot (long polling). Press Ctrl+C to stop."
exec ./.venv/bin/python -m bot.main
