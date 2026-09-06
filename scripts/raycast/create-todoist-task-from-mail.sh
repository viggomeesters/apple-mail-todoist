#!/bin/sh

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Create Todoist Task from Mail
# @raycast.mode silent

# Optional parameters:
# @raycast.icon ✅
# @raycast.packageName Apple Mail to Todoist

# Documentation:
# @raycast.description Create an idempotent Todoist task from one selected Apple Mail message.
# @raycast.author Viggo Meesters

cli="${APPLE_MAIL_TODOIST_CLI:-}"
if [ -z "$cli" ]; then
  for candidate in "$HOME/.local/bin/apple-mail-todoist" /opt/homebrew/bin/apple-mail-todoist; do
    if [ -x "$candidate" ]; then
      cli="$candidate"
      break
    fi
  done
fi

if [ -z "$cli" ] || [ ! -x "$cli" ]; then
  printf '%s\n' "Apple Mail to Todoist is not installed"
  exit 2
fi

nohup "$cli" capture-notify </dev/null >/dev/null 2>&1 &
printf '%s\n' "Creating Todoist task"
