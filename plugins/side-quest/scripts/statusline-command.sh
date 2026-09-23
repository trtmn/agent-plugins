#!/usr/bin/env bash
# Claude Code statusline — mirrors the zsh prompt style (user@host:dir)
# Adds git branch, session name, model name, context usage percentage,
# and the active VS Code document (when available via AppleScript).

input=$(cat)

user=$(whoami)
host=$(hostname -s)
dir=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""')
# Show ~ for home directory, like the shell prompt does
dir="${dir/#$HOME/\~}"

model=$(echo "$input" | jq -r '.model.display_name // ""')
used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
session_name=$(echo "$input" | jq -r '.session_name // ""')

# Build context indicator
if [ -n "$used" ]; then
  used_int=${used%.*}
  ctx_str="ctx:${used_int}%"
else
  ctx_str=""
fi

# Build cache indicator (cache_read and cache_creation tokens from last API call)
cache_read=$(echo "$input" | jq -r '.context_window.current_usage.cache_read_input_tokens // empty')
cache_write=$(echo "$input" | jq -r '.context_window.current_usage.cache_creation_input_tokens // empty')
uncached=$(echo "$input" | jq -r '.context_window.current_usage.input_tokens // empty')
cache_str=""
if [ -n "$cache_read" ] || [ -n "$cache_write" ]; then
  read_k=$(awk "BEGIN {printf \"%.1f\", ${cache_read:-0}/1000}")
  write_k=$(awk "BEGIN {printf \"%.1f\", ${cache_write:-0}/1000}")
  total_input=$(( ${cache_read:-0} + ${cache_write:-0} + ${uncached:-0} ))
  if [ "$total_input" -gt 0 ]; then
    cache_pct=$(awk "BEGIN {printf \"%.0f\", ${cache_read:-0}/$total_input*100}")
  else
    cache_pct="0"
  fi
  cache_str="cache: ${cache_pct}% hit  ${read_k}k read / ${write_k}k write"
fi

# Build rate limit indicators
five_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
five_resets=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
seven_pct=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
seven_resets=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')

five_str=""
if [ -n "$five_pct" ]; then
  five_int=$(printf '%.0f' "$five_pct")
  if [ -n "$five_resets" ]; then
    five_reset_fmt=$(date -r "$five_resets" "+%l:%M%p" 2>/dev/null | tr -s ' ' | sed 's/^ //')
    five_str="5h:${five_int}% (resets ${five_reset_fmt})"
  else
    five_str="5h:${five_int}%"
  fi
fi

seven_str=""
if [ -n "$seven_pct" ]; then
  seven_int=$(printf '%.0f' "$seven_pct")
  if [ -n "$seven_resets" ]; then
    reset_fmt=$(date -r "$seven_resets" "+%a %l:%M%p" 2>/dev/null | tr -s ' ' | sed 's/^ //')
    seven_str="7d:${seven_int}% (resets ${reset_fmt})"
  else
    seven_str="7d:${seven_int}%"
  fi
fi

# Resolve actual cwd for git branch lookup (expand ~ back to full path)
actual_dir=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""')
git_branch=""
if [ -n "$actual_dir" ] && [ -d "$actual_dir" ]; then
  git_branch=$(GIT_OPTIONAL_LOCKS=0 git -C "$actual_dir" symbolic-ref --short HEAD 2>/dev/null)
fi

# Detect active VS Code document via AppleScript (macOS only, silent on failure)
# TEMPORARILY DISABLED: this was being invoked on every statusline refresh across
# multiple Claude CLI sessions, causing launchservicesd/WindowServer/trustd thrashing
# and extremely high system CPU. Re-enable once refresh-rate/caching is added.
vscode_file=""
# if command -v osascript >/dev/null 2>&1; then
#   vscode_file=$(osascript 2>/dev/null <<'APPLESCRIPT'
# tell application "System Events"
#   set vsRunning to (name of processes) contains "Code"
# end tell
# if not vsRunning then return ""
# tell application "Code"
#   if (count of windows) > 0 then
#     set docName to name of front window
#     -- Strip common VS Code window title suffixes (e.g. " - Visual Studio Code", " - workspace name")
#     set AppleScript's text item delimiters to " - "
#     set parts to text items of docName
#     if (count of parts) > 1 then
#       set docName to item 1 of parts
#     end if
#     return docName
#   end if
# end tell
# return ""
# APPLESCRIPT
#   )
# fi

# Build statusline with ANSI colors matching the zsh prompt palette
# blue for user@host, green for directory, dim for metadata

# Line 1: user@host:dir [git branch] [vscode file] [session name] [model]
printf "\033[34m%s@%s\033[0m:\033[32m%s\033[0m" "$user" "$host" "$dir"

if [ -n "$git_branch" ]; then
  printf "  \033[35m\xef\x9c\xb0 %s\033[0m" "$git_branch"
fi

if [ -n "$vscode_file" ]; then
  printf "  \033[36m\xef\x80\x9f %s\033[0m" "$vscode_file"
fi

if [ -n "$session_name" ]; then
  printf "  \033[2m[%s]\033[0m" "$session_name"
fi

if [ -n "$model" ]; then
  printf "  \033[2m%s\033[0m" "$model"
fi

printf "\n"

# Line 2: context usage + cache info
ctx_cache_line=""
if [ -n "$ctx_str" ]; then
  ctx_cache_line="$ctx_str"
fi
if [ -n "$cache_str" ]; then
  if [ -n "$ctx_cache_line" ]; then
    ctx_cache_line="$ctx_cache_line  $cache_str"
  else
    ctx_cache_line="$cache_str"
  fi
fi
if [ -n "$ctx_cache_line" ]; then
  printf "\033[2m%s\033[0m\n" "$ctx_cache_line"
fi

# Line 3: rate limit info (only printed when data is present)
rate_line=""
if [ -n "$five_str" ]; then
  rate_line="$five_str"
fi
if [ -n "$seven_str" ]; then
  if [ -n "$rate_line" ]; then
    rate_line="$rate_line  $seven_str"
  else
    rate_line="$seven_str"
  fi
fi
if [ -n "$rate_line" ]; then
  printf "\033[2m%s\033[0m\n" "$rate_line"
fi
