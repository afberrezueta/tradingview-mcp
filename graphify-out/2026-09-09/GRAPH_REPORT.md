# Graph Report - tradingview-mcp  (2026-09-09)

## Corpus Check
- 80 files · ~52,955 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 470 nodes · 920 edges · 28 communities (23 shown, 3 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 4 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c05b8f57`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- evaluate
- Decision Tree — Which Tool When
- server.js
- safeString
- TradingView MCP Bridge
- connection.js
- package.json
- router.js
- e2e.test.js
- core/health.js
- core/stream.js
- core/replay.js
- core/index.js
- Setup Guide for Claude Code
- Multi-Symbol Scanner
- Strategy Performance Report
- Chart Analysis Workflow
- Pine Script Development Loop
- core/indicators.js
- Contributing
- Replay Practice Trading
- Security Policy
- cli.test.js
- performance-analyst.md
- launch_tv_debug_linux.sh
- launch_tv_debug_mac.sh

## God Nodes (most connected - your core abstractions)
1. `evaluate()` - 94 edges
2. `jsonResult()` - 29 edges
3. `safeString()` - 26 edges
4. `getClient()` - 25 edges
5. `evaluateAsync()` - 21 edges
6. `TradingView MCP Bridge` - 19 edges
7. `register()` - 16 edges
8. `Decision Tree — Which Tool When` - 13 edges
9. `scripts` - 11 edges
10. `ensurePineEditorOpen()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `deleteAlerts()` --calls--> `evaluate()`  [EXTRACTED]
  src/core/alerts.js → src/connection.js
- `discover()` --calls--> `evaluate()`  [EXTRACTED]
  src/core/health.js → src/connection.js
- `uiState()` --calls--> `evaluate()`  [EXTRACTED]
  src/core/health.js → src/connection.js
- `list()` --calls--> `evaluateAsync()`  [EXTRACTED]
  src/core/alerts.js → src/connection.js
- `batchRun()` --calls--> `safeString()`  [EXTRACTED]
  src/core/batch.js → src/connection.js

## Import Cycles
- None detected.

## Communities (28 total, 3 thin omitted)

### Community 0 - "evaluate"
Cohesion: 0.08
Nodes (55): evaluate(), evaluateAsync(), getClient(), KNOWN_PATHS, buildGraphicsJS(), ensureStrategyTesterReady(), getDepth(), getEquity() (+47 more)

### Community 1 - "Decision Tree — Which Tool When"
Cohesion: 0.05
Nodes (36): "Analyze my chart" (full report workflow), Architecture, "Change the chart", Context Management Rules, Decision Tree — Which Tool When, "Draw on the chart", "Give me price data", graphify (+28 more)

### Community 2 - "server.js"
Cohesion: 0.13
Nodes (20): REPO_ROOT, _resolve(), update(), server, transport, registerAlertTools(), registerBatchTools(), registerCaptureTools() (+12 more)

### Community 3 - "safeString"
Cohesion: 0.12
Nodes (23): requireFinite(), safeString(), CONDITION_TYPE_MAP, create(), deleteAlerts(), list(), getState(), getVisibleRange() (+15 more)

### Community 4 - "TradingView MCP Bridge"
Cohesion: 0.06
Nodes (33): 1. Install, 2. Launch TradingView with CDP, 3. Add to Claude Code, 4. Verify, All Commands, Architecture, Attributions, Chart Control (+25 more)

### Community 5 - "connection.js"
Cohesion: 0.12
Nodes (25): CDP_HOST, CDP_PORT, connect(), findChartTarget(), findTargetById(), getBottomBar(), getChartApi(), getChartCollection() (+17 more)

### Community 6 - "package.json"
Cohesion: 0.07
Nodes (27): bin, tv, dependencies, chrome-remote-interface, @modelcontextprotocol/sdk, description, devDependencies, eslint (+19 more)

### Community 7 - "router.js"
Cohesion: 0.20
Nodes (7): commands, execute(), handleError(), printCommandHelp(), printHelp(), register(), run()

### Community 8 - "e2e.test.js"
Cohesion: 0.12
Nodes (13): chrome-remote-interface, outPath, t, targets, escaped, src, srcPath, t (+5 more)

### Community 9 - "core/health.js"
Cohesion: 0.16
Nodes (14): getTargetInfo(), checkForUpdate(), _copyMsixPackageLocal(), discover(), healthCheck(), launch(), _resolveLaunchDeps(), _spawnDetached() (+6 more)

### Community 10 - "core/stream.js"
Cohesion: 0.23
Nodes (16): fetchAllPanes(), fetchLabels(), fetchLastBar(), fetchLines(), fetchQuote(), fetchTables(), fetchValues(), pollLoop() (+8 more)

### Community 11 - "core/replay.js"
Cohesion: 0.39
Nodes (13): getReplayApi(), autoplay(), _resolve(), start(), status(), step(), stop(), trade() (+5 more)

### Community 12 - "core/index.js"
Cohesion: 0.15
Nodes (12): alerts, batch, capture, chart, data, drawing, health, indicators (+4 more)

### Community 13 - "Setup Guide for Claude Code"
Cohesion: 0.20
Nodes (9): Setup Guide for Claude Code, Step 1: Clone and Install, Step 2: Add to MCP Config, Step 3: Launch TradingView Desktop, Step 4: Restart Claude Code, Step 5: Verify Connection, Step 6: Install CLI (Optional), Troubleshooting (+1 more)

### Community 14 - "Multi-Symbol Scanner"
Cohesion: 0.20
Nodes (9): For Custom Analysis (per-symbol), For Screenshot Comparison, For Strategy Performance Comparison, Multi-Symbol Scanner, Step 1: Define the Scan, Step 2: Run the Scan, Step 3: Compile Results, Step 4: Report (+1 more)

### Community 15 - "Strategy Performance Report"
Cohesion: 0.20
Nodes (9): Equity Curve Assessment, Key Metrics, Step 1: Gather Data, Step 2: Capture Visuals, Step 3: Analyze, Step 4: Generate Report, Step 5: Suggest Improvements, Strategy Performance Report (+1 more)

### Community 16 - "Chart Analysis Workflow"
Cohesion: 0.22
Nodes (8): Chart Analysis Workflow, Cleanup, Step 1: Set Up the Chart, Step 2: Add Indicators, Step 3: Navigate to Key Areas, Step 4: Annotate, Step 5: Capture and Analyze, Step 6: Report

### Community 17 - "Pine Script Development Loop"
Cohesion: 0.22
Nodes (8): Pine Script Development Loop, Step 1: Understand the Goal, Step 2: Pull Current Source (if modifying), Step 3: Write the Pine Script, Step 4: Push and Compile, Step 5: Fix Errors, Step 6: Verify on Chart, Step 7: Iterate

### Community 18 - "core/indicators.js"
Cohesion: 0.50
Nodes (8): addStudyFromSearch(), closeDialog(), delay(), openDialog(), searchStudies(), setInputs(), toggleVisibility(), typeQuery()

### Community 19 - "Contributing"
Cohesion: 0.25
Nodes (7): Bug Reports, Contributing, Development, Pull Requests, Scope, What's in scope, What's out of scope

### Community 20 - "Replay Practice Trading"
Cohesion: 0.25
Nodes (7): Replay Practice Trading, Step 1: Setup, Step 2: Pre-Trade Analysis, Step 3: Step Through Bars, Step 4: Execute Trades, Step 5: Review, Tips

### Community 21 - "Security Policy"
Cohesion: 0.33
Nodes (5): Best Practices for Users, Out of Scope, Reporting a Vulnerability, Scope, Security Policy

### Community 23 - "performance-analyst.md"
Cohesion: 0.50
Nodes (3): Analysis Framework, Data Gathering, Output

## Knowledge Gaps
- **171 isolated node(s):** `name`, `version`, `description`, `type`, `main` (+166 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 203 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `evaluate()` connect `evaluate` to `safeString`, `connection.js`, `core/health.js`, `core/stream.js`, `core/replay.js`, `core/indicators.js`?**
  _High betweenness centrality (0.138) - this node is a cross-community bridge._
- **Why does `chrome-remote-interface` connect `e2e.test.js` to `connection.js`, `package.json`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **What connects `name`, `version`, `description` to the rest of the system?**
  _171 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `evaluate` be split into smaller, more focused modules?**
  _Cohesion score 0.08038075092543628 - nodes in this community are weakly interconnected._
- **Should `Decision Tree — Which Tool When` be split into smaller, more focused modules?**
  _Cohesion score 0.05128205128205128 - nodes in this community are weakly interconnected._
- **Should `server.js` be split into smaller, more focused modules?**
  _Cohesion score 0.13090418353576247 - nodes in this community are weakly interconnected._
- **Should `safeString` be split into smaller, more focused modules?**
  _Cohesion score 0.12299465240641712 - nodes in this community are weakly interconnected._