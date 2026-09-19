# Setup Guide for Claude Code

This file is a step-by-step guide for Claude Code (or any LLM agent) to install and configure the TradingView MCP server. If a user asks you to install or set up this project, follow these steps exactly.

## Step 1: Clone and Install

```bash
git clone https://github.com/tradesdontlie/tradingview-mcp.git ~/tradingview-mcp
cd ~/tradingview-mcp
npm install
```

If the user specifies a different install path, use that instead of `~/tradingview-mcp`.

## Step 2: Add to MCP Config

Add the server to the user's Claude Code MCP configuration. The config file is at `~/.claude/.mcp.json` (global) or `.mcp.json` (project-level).

```json
{
  "mcpServers": {
    "tradingview": {
      "command": "node",
      "args": ["<INSTALL_PATH>/src/server.js"]
    }
  }
}
```

Replace `<INSTALL_PATH>` with the actual path where the repo was cloned (e.g., `/Users/username/tradingview-mcp`).

If the config file already exists and has other servers, merge the `tradingview` entry into the existing `mcpServers` object. Do not overwrite other servers.

## Step 3: Launch TradingView Desktop

TradingView Desktop must be running with Chrome DevTools Protocol enabled.

**Auto-detect and launch (recommended):**
After the MCP server is connected, use the `tv_launch` tool — it auto-detects TradingView on Mac, Windows, and Linux.

**Manual launch by platform:**

Mac:
```bash
/Applications/TradingView.app/Contents/MacOS/TradingView --remote-debugging-port=9222
```

Windows:

TradingView for Windows now ships **only as an MSIX package** (Microsoft Store and tvd-packages.tradingview.com both install under `C:\Program Files\WindowsApps\`). Use the launch script — it resolves the install via `Get-AppxPackage`, which works without admin rights:

```bat
scripts\launch_tv_debug.bat
```

Or, preferred: let the `tv_launch` MCP tool do it — it auto-detects MSIX installs and, on Windows builds where launching from `WindowsApps` is blocked with **"Access is denied"**, automatically copies the package to `%LOCALAPPDATA%\tradingview-mcp\` (one-time, ~330MB) and launches from the copy. The copy keeps your login, layout, and chart state. If the fallback was used, the result includes `msix_local_copy: true`.

Manual equivalent of that fallback, if you need it:

```powershell
$pkg = (Get-AppxPackage TradingView.Desktop).InstallLocation
Copy-Item "$pkg\*" "$env:LOCALAPPDATA\tradingview-mcp\TradingView" -Recurse -Force
& "$env:LOCALAPPDATA\tradingview-mcp\TradingView\TradingView.exe" --remote-debugging-port=9222
```

Reading files out of `WindowsApps` by exact path is allowed even where executing them isn't. Do **not** try to change ACLs on `WindowsApps` with `icacls` — it fails and can break app servicing.

Legacy (pre-MSIX) installs:
```bash
%LOCALAPPDATA%\TradingView\TradingView.exe --remote-debugging-port=9222
```

Linux:
```bash
/opt/TradingView/tradingview --remote-debugging-port=9222
# or: tradingview --remote-debugging-port=9222
```

## Step 4: Restart Claude Code

The MCP server only loads when Claude Code starts. After adding the config:

1. Exit Claude Code (Ctrl+C)
2. Relaunch Claude Code
3. The tradingview MCP server should connect automatically

## Step 5: Verify Connection

Use the `tv_health_check` tool. Expected response:

```json
{
  "success": true,
  "cdp_connected": true,
  "chart_symbol": "...",
  "api_available": true
}
```

If `cdp_connected: false`, TradingView is not running with `--remote-debugging-port=9222`.

## Step 6: Install CLI (Optional)

To use the `tv` CLI command globally:

```bash
cd ~/tradingview-mcp
npm link
```

Then `tv status`, `tv quote`, `tv pine compile`, etc. work from anywhere.

## Step 7: Apple Design MCP Servers (Optional)

`apple-design.mcp.json` registers the MCP servers found by the GitHub repository search **"apple design mcp"** (17 results when this was written, 16 today; 13 of them are runnable MCP servers). Together they give the agent Apple Human Interface Guidelines lookups, design tokens, Liquid Glass and motion guidance, SwiftUI HIG checks, and a few Apple-app integrations.

| Server | Source | Runs via | What the agent gets |
|--------|--------|----------|---------------------|
| `hig` | [aka-kika/hig-mcp](https://github.com/aka-kika/hig-mcp) | `uvx hig-mcp` (PyPI) | HIG design tokens (color, typography, materials, layout), Liquid Glass checklist, SwiftUI mappings |
| `apple-design` | [rncrosby/apple-design-mcp](https://github.com/rncrosby/apple-design-mcp) | local clone, Node 20 | Full-text search and Markdown pages of the live HIG for every Apple platform |
| `orchard-hig` | [sophiacave/orchard-hig](https://github.com/sophiacave/orchard-hig) | local clone, Python 3.10 (stdlib only) | Checks SwiftUI code against 22 HIG rules |
| `better-design` | [marvkr/better-design](https://github.com/marvkr/better-design) | `npx -y better-design mcp` | 31 design systems incl. Apple, UI principles, review rules, icon search. Needs `BETTER_DESIGN_API_KEY` |
| `detent` | [TomAs-1226/Detent](https://github.com/TomAs-1226/Detent) | local clone, Node 20 | Apple-like motion: springs, gesture physics, ~110 presets, Liquid Glass "Bezel" tokens |
| `vishwakarma` | [yogvidwankhede/vishwakarma](https://github.com/yogvidwankhede/vishwakarma) | local clone, pnpm 10 build | 32 design/engineering skills served as tools, platform-correct constants for Apple |
| `clarity-beta` | [rutika196/clarity-beta](https://github.com/rutika196/clarity-beta) | local clone, uv + Playwright | Markdown to diagrams rendered in Apple HIG style |
| `keynote` | [superdwayne/keynoteMP](https://github.com/superdwayne/keynoteMP) | local clone, Node | 67 tools driving Apple Keynote (macOS only) |
| `seis` | [emirhankudun-ux/SEIS](https://github.com/emirhankudun-ux/SEIS) | local clone, Node | MCP server of the SEIS Apple-first engineering ecosystem |
| `logomcp` | [gofastercloud/logoMCP](https://github.com/gofastercloud/logoMCP) | local clone, uv | Brand and logo design-system generation with local models (Apple Silicon only) |
| `smart-photo-journal` | [Siddhant-K-code/memory-journal-mcp-server](https://github.com/Siddhant-K-code/memory-journal-mcp-server) | local clone, uv | Searches your Apple Photos library (macOS only) |
| `apple-mail` | [BastianZim/apple-mail-mcp](https://github.com/BastianZim/apple-mail-mcp) | `uvx` from git | Read-only Apple Mail search (macOS only) |
| `harlo` | [JosephOIbrahim/Harlo](https://github.com/JosephOIbrahim/Harlo) | local clone, uv + Rust toolchain | Decision coach over Apple Watch health data (macOS only) |

From the same search but not registered: [palmier-pro](https://github.com/Genuscambarustangerinetree105/palmier-pro) (a Windows video editor, no MCP server), [kpa](https://github.com/alvelda/kpa) (its `kpa-mcp` server is still on the upstream roadmap) and [emasoft-complete-ios-app-authoring](https://github.com/Emasoft/emasoft-complete-ios-app-authoring) (a Claude Code plugin, not a server; `--with-plugins` installs it together with the Detent plugin).

### Install and test

```bash
bash scripts/install_apple_design_mcp.sh            # all 13; add --design-only for the 7 HIG/design servers
node scripts/check_apple_design_mcp.mjs        # handshake test: prints the tool count of every server
```

The installer clones into `vendor/apple-design/` (git-ignored) and builds there. It needs `git`, Node 20+, `uv` (`brew install uv`) and, for `vishwakarma`, pnpm 10 (falls back to `npx pnpm@10`). What it cannot do for you, printed again at the end of each run:

- `better-design`: set `BETTER_DESIGN_API_KEY` (`npx better-design -y` mints a free key, or https://better-design.com/mcp)
- `logomcp`: Apple Silicon with 24 GB+ RAM, `hf auth login`, about 12 GB of models on first use
- `harlo`: Python 3.12 and a Rust toolchain (maturin build)
- macOS permissions: Automation for `keynote`, Full Disk Access and Photos access for `smart-photo-journal`, Mail database access for `apple-mail`

### Activate

Claude Code only auto-loads a file named `.mcp.json`, so nothing runs until you activate it:

```bash
bash scripts/install_apple_design_mcp.sh --design-only --activate   # writes the servers that installed OK into .mcp.json (merges if it exists)
# alternatives:
cp apple-design.mcp.json .mcp.json                             # all 13, project scope
claude --mcp-config apple-design.mcp.json                      # one session only
```

Claude Code asks you to approve project servers the first time it sees them (`claude mcp reset-project-choices` asks again). The paths use `${CLAUDE_PROJECT_DIR}`, which Claude Code expands to this directory; if you move entries into `~/.claude/.mcp.json`, replace it with the absolute path of the clone.

**Read before activating everything.** `apple-mail`, `smart-photo-journal` and `harlo` give the agent read access to your email, photo library and health data; keep them only if that is what you want. Most of these projects are small (0 to 35 GitHub stars) and run with your user permissions, so treat them like any other dependency you add. The upstream tradingview-mcp project keeps `.mcp.json` files out of its repository (see CONTRIBUTING.md), which is why this fork ships the config under a separate name.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `cdp_connected: false` | Launch TradingView with `--remote-debugging-port=9222` |
| Windows: "Access is denied" launching from `WindowsApps` | Use `tv_launch` (auto copy-fallback) or the manual copy snippet in Step 3 — never `icacls` on WindowsApps |
| `ECONNREFUSED` | TradingView isn't running or port 9222 is blocked |
| MCP server not showing in Claude Code | Check `~/.claude/.mcp.json` syntax, restart Claude Code |
| `tv` command not found | Run `npm link` from the project directory |
| Tools return stale data | TradingView may still be loading — wait a few seconds |
| Pine Editor tools fail | Open the Pine Editor panel first (`ui_open_panel pine-editor open`) |
| Apple design server shows "failed" in `/mcp` | Run `bash scripts/install_apple_design_mcp.sh`, then `node scripts/check_apple_design_mcp.mjs` and follow the manual steps it prints |

## What to Read Next

- `CLAUDE.md` — Decision tree for which tool to use when (auto-loaded by Claude Code)
- `README.md` — Full tool reference (78 MCP tools, 30 CLI commands)
- `RESEARCH.md` — Research context and open questions
