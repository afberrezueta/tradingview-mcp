#!/usr/bin/env bash
#
# Install the Apple design MCP servers declared in apple-design.mcp.json.
#
# The servers come from the GitHub repository search "apple design mcp". This script:
#   - clones the servers that need a local checkout into vendor/apple-design/ (git-ignored)
#   - builds them (npm install / pnpm build / uv sync)
#   - pre-downloads the package-based servers (uvx / npx) so the first Claude Code start is fast
#   - prints a per-server status and the manual steps that cannot be automated
#     (API keys, macOS permissions, model downloads)
#
# Usage:
#   bash scripts/install_apple_design_mcp.sh                 install everything
#   bash scripts/install_apple_design_mcp.sh --design-only   only the HIG / design-language servers
#   bash scripts/install_apple_design_mcp.sh --only hig --only detent
#   bash scripts/install_apple_design_mcp.sh --skip logomcp --skip harlo
#   bash scripts/install_apple_design_mcp.sh --with-plugins  also install the Claude Code plugins
#   bash scripts/install_apple_design_mcp.sh --activate      also write the installed servers into .mcp.json
#   bash scripts/install_apple_design_mcp.sh --dry-run       show the plan, change nothing
#
# Afterwards: node scripts/check_apple_design_mcp.mjs   (handshake test of every server)
#
# Claude Code only auto-loads a file named .mcp.json, so nothing is active until you pass
# --activate (or copy apple-design.mcp.json to .mcp.json yourself).
#
# Works with the bash 3.2 that ships with macOS (no associative arrays). On Windows run it
# from Git Bash or WSL; the JSON config itself is cross-platform.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDOR="$ROOT/vendor/apple-design"
LOGS="$VENDOR/.logs"

# name|kind|source|clone dir|build command (runs inside the clone)|file that must exist afterwards
# kind: git = clone + build, uvx = Python package resolved by uvx at launch, npx = npm package resolved by npx at launch
SERVERS='
hig|uvx|hig-mcp|||
apple-design|git|https://github.com/rncrosby/apple-design-mcp.git|apple-design-mcp|npm install|dist/cli.js
orchard-hig|git|https://github.com/sophiacave/orchard-hig.git|orchard-hig||src/mcp_server.py
better-design|npx|better-design|||
detent|git|https://github.com/TomAs-1226/Detent.git|Detent||mcp/server.mjs
vishwakarma|git|https://github.com/yogvidwankhede/vishwakarma.git|vishwakarma|$PNPM install && $PNPM build|packages/mcp/dist/server.js
clarity-beta|git|https://github.com/rutika196/clarity-beta.git|clarity-beta|uv sync && uv run playwright install chromium|pyproject.toml
keynote|git|https://github.com/superdwayne/keynoteMP.git|keynoteMP|npm install && npm run build|dist/index.js
seis|git|https://github.com/emirhankudun-ux/SEIS.git|SEIS|npm install --prefix packages/seis-ai|packages/seis-ai/bin/seis-mcp.mjs
logomcp|git|https://github.com/gofastercloud/logoMCP.git|logoMCP|cd backend && uv sync|backend/pyproject.toml
smart-photo-journal|git|https://github.com/Siddhant-K-code/memory-journal-mcp-server.git|memory-journal-mcp-server|uv sync|server.py
apple-mail|uvx|git+https://github.com/BastianZim/apple-mail-mcp|||
harlo|git|https://github.com/JosephOIbrahim/Harlo.git|Harlo|uv sync|pyproject.toml
'

# Servers that are about Apple design itself (HIG, Liquid Glass, motion, design tokens).
DESIGN_SET=" hig apple-design orchard-hig better-design detent vishwakarma clarity-beta "

ONLY=" "
SKIP=" "
DRY_RUN=0
WITH_PLUGINS=0
ACTIVATE=0

usage() { sed -n '2,27p' "$0" | sed 's/^# \{0,1\}//'; }

while [ $# -gt 0 ]; do
  case "$1" in
    --only) ONLY="$ONLY$2 "; shift 2 ;;
    --skip) SKIP="$SKIP$2 "; shift 2 ;;
    --design-only)
      while IFS='|' read -r name _rest; do
        [ -z "$name" ] && continue
        case "$DESIGN_SET" in *" $name "*) ;; *) SKIP="$SKIP$name " ;; esac
      done <<< "$SERVERS"
      shift ;;
    --with-plugins) WITH_PLUGINS=1; shift ;;
    --activate) ACTIVATE=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

selected() {
  case "$SKIP" in *" $1 "*) return 1 ;; esac
  [ "$ONLY" = " " ] && return 0
  case "$ONLY" in *" $1 "*) return 0 ;; *) return 1 ;; esac
}

have() { command -v "$1" >/dev/null 2>&1; }
say() { printf '%s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }

RESULTS=""
record() { RESULTS="$RESULTS$1|$2|$3"$'\n'; }

# --- prerequisites -------------------------------------------------------------------------
for tool in git node npm; do
  have "$tool" || { echo "error: '$tool' is required" >&2; exit 1; }
done
NODE_MAJOR="$(node -p 'Number(process.versions.node.split(".")[0])')"
[ "$NODE_MAJOR" -ge 20 ] || warn "Node $NODE_MAJOR detected; apple-design, detent and vishwakarma need Node 20+"
HAVE_UV=0; have uv && HAVE_UV=1
[ "$HAVE_UV" = 1 ] || warn "'uv' not found: the Python servers will be skipped. Install it with 'brew install uv' or 'curl -LsSf https://astral.sh/uv/install.sh | sh'"
if have pnpm; then PNPM=pnpm; else PNPM="npx -y pnpm@10"; fi
export PNPM

needs_uv() {
  case "$1" in
    uvx) return 0 ;;
    git) case "$2" in *"uv "*|*"uv sync"*) return 0 ;; esac ;;
  esac
  return 1
}

# --- install -------------------------------------------------------------------------------
say "Apple design MCP servers -> $VENDOR"
[ "$DRY_RUN" = 1 ] && say "(dry run: nothing will be changed)"
say ""
[ "$DRY_RUN" = 1 ] || mkdir -p "$LOGS"

while IFS='|' read -r name kind source dir build entry; do
  [ -z "$name" ] && continue
  if ! selected "$name"; then
    record "$name" "skipped" "excluded by --only/--skip/--design-only"
    continue
  fi
  if needs_uv "$kind" "$build" && [ "$HAVE_UV" != 1 ]; then
    record "$name" "skipped" "needs uv"
    continue
  fi

  case "$kind" in
    uvx)
      say "==> $name: resolving Python package '$source' with uvx"
      if [ "$DRY_RUN" = 1 ]; then record "$name" "planned" "uvx --from $source"; continue; fi
      if uvx --from "$source" python -c 'import sys' >"$LOGS/$name.log" 2>&1; then
        record "$name" "ok" "uvx cache warmed"
      else
        record "$name" "failed" "see $LOGS/$name.log"
      fi
      ;;
    npx)
      say "==> $name: resolving npm package '$source' with npx"
      if [ "$DRY_RUN" = 1 ]; then record "$name" "planned" "npx -y $source"; continue; fi
      if npx -y "$source" --help >"$LOGS/$name.log" 2>&1; then
        record "$name" "ok" "npx cache warmed"
      else
        record "$name" "failed" "see $LOGS/$name.log"
      fi
      ;;
    git)
      target="$VENDOR/$dir"
      say "==> $name: $source -> vendor/apple-design/$dir"
      if [ "$DRY_RUN" = 1 ]; then record "$name" "planned" "clone${build:+ + '$build'}"; continue; fi
      mkdir -p "$VENDOR"
      if [ -d "$target/.git" ]; then
        git -C "$target" pull --ff-only --quiet >"$LOGS/$name.log" 2>&1 || warn "$name: could not fast-forward existing clone (kept as is)"
      elif ! git clone --depth 1 --quiet "$source" "$target" >"$LOGS/$name.log" 2>&1; then
        record "$name" "failed" "git clone failed, see $LOGS/$name.log"
        continue
      fi
      if [ -n "$build" ]; then
        say "    building: $build"
        if ! (cd "$target" && eval "$build") >>"$LOGS/$name.log" 2>&1; then
          record "$name" "failed" "build failed, see $LOGS/$name.log"
          continue
        fi
      fi
      if [ -e "$target/$entry" ]; then
        record "$name" "ok" "vendor/apple-design/$dir/$entry"
      else
        record "$name" "failed" "expected file missing: $entry"
      fi
      ;;
  esac
done <<< "$SERVERS"

# --- optional Claude Code plugins (repositories from the same search that are plugins, not servers)
if [ "$WITH_PLUGINS" = 1 ]; then
  say ""
  if ! have claude; then
    warn "'claude' CLI not found, plugins not installed"
  elif [ "$DRY_RUN" = 1 ]; then
    say "==> plugins: would run 'claude plugin marketplace add' + 'claude plugin install' for Emasoft/emasoft-complete-ios-app-authoring and TomAs-1226/Detent"
  else
    say "==> plugins: Emasoft/emasoft-complete-ios-app-authoring (27 skills, 15 agents, XcodeBuildMCP + ios-simulator-mcp)"
    claude plugin marketplace add Emasoft/emasoft-complete-ios-app-authoring \
      && claude plugin install emasoft-complete-ios-app-authoring@emasoft-complete-ios-app-authoring \
      || warn "emasoft-complete-ios-app-authoring plugin install failed"
    say "==> plugins: TomAs-1226/Detent (skills + the detent MCP server as a plugin)"
    claude plugin marketplace add TomAs-1226/Detent \
      && claude plugin install detent@detent \
      || warn "detent plugin install failed"
  fi
fi

# --- optional activation: merge the servers that installed OK into the project .mcp.json ---
if [ "$ACTIVATE" = 1 ]; then
  say ""
  OK_NAMES="$(printf '%s' "$RESULTS" | awk -F'|' '$2 == "ok" { print $1 }' | tr '\n' ' ')"
  if [ "$DRY_RUN" = 1 ]; then
    say "==> activate: would merge the installed servers into $ROOT/.mcp.json"
  elif [ -z "${OK_NAMES// /}" ]; then
    warn "nothing installed successfully, .mcp.json left untouched"
  else
    ACTIVATE_NAMES="$OK_NAMES" node - "$ROOT" <<'NODE'
const fs = require('node:fs');
const path = require('node:path');
const root = process.argv[2];
const names = process.env.ACTIVATE_NAMES.trim().split(/\s+/);
const source = JSON.parse(fs.readFileSync(path.join(root, 'apple-design.mcp.json'), 'utf8')).mcpServers;
const target = path.join(root, '.mcp.json');
const current = fs.existsSync(target) ? JSON.parse(fs.readFileSync(target, 'utf8')) : {};
current.mcpServers = current.mcpServers || {};
for (const name of names) if (source[name]) current.mcpServers[name] = source[name];
fs.writeFileSync(target, `${JSON.stringify(current, null, 2)}\n`);
console.log(`==> activate: ${names.length} server(s) written to ${target}: ${names.join(', ')}`);
NODE
  fi
fi

# --- summary -------------------------------------------------------------------------------
say ""
say "Summary"
printf '  %-22s %-9s %s\n' "server" "status" "detail"
printf '%s' "$RESULTS" | while IFS='|' read -r name status detail; do
  [ -z "$name" ] && continue
  printf '  %-22s %-9s %s\n' "$name" "$status" "$detail"
done

say ""
say "Manual steps (only for the servers you keep):"
say "  better-design        set BETTER_DESIGN_API_KEY (free key: 'npx better-design -y', or https://better-design.com/mcp)"
say "  clarity-beta         Chromium for Playwright was installed into the uv environment (about 150 MB)"
say "  vishwakarma          built with pnpm 10 + turbo; rebuild after 'git pull' with '\$PNPM build'"
say "  keynote              macOS + Keynote; grant Automation permission to your terminal the first time"
say "  logomcp              Apple Silicon, 24 GB+ RAM, 'hf auth login', downloads about 12 GB of models on first use"
say "  smart-photo-journal  macOS Photos library; grant Full Disk Access + Photos access (reads your photos)"
say "  apple-mail           macOS Mail; read-only access to Mail's local database (reads your email)"
say "  harlo                Python 3.12 + Rust toolchain (maturin build); reads Apple Watch health data"
say ""
say "Next:"
say "  1. node scripts/check_apple_design_mcp.mjs      # handshake test, lists tool counts"
if [ "$ACTIVATE" = 1 ]; then
  say "  2. restart Claude Code in this directory and approve the project servers when prompted"
  say "     (reset those choices later with 'claude mcp reset-project-choices')"
else
  say "  2. activate: re-run with --activate (merges the installed servers into .mcp.json),"
  say "     or 'cp apple-design.mcp.json .mcp.json', or 'claude --mcp-config apple-design.mcp.json'"
  say "  3. restart Claude Code in this directory and approve the project servers when prompted"
fi

printf '%s' "$RESULTS" | grep -q '|failed|' && exit 1
exit 0
