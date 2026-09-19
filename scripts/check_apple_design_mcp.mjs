#!/usr/bin/env node
/**
 * Handshake test for the MCP servers declared in apple-design.mcp.json (or --config FILE).
 *
 * For every stdio server it spawns the configured command, sends `initialize`,
 * `notifications/initialized` and `tools/list`, and reports the tool count or the failure
 * reason (command missing, early exit, no reply). It does not call any tool.
 *
 * Usage:
 *   node scripts/check_apple_design_mcp.mjs                    check every server
 *   node scripts/check_apple_design_mcp.mjs hig detent         check only these servers
 *   node scripts/check_apple_design_mcp.mjs --timeout 120      seconds to wait per server (default 60)
 *   node scripts/check_apple_design_mcp.mjs --config .mcp.json check the active project config instead
 *
 * Exit code 1 if any checked server failed.
 */
import { spawn } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const CONCURRENCY = 3;

let timeoutMs = 60_000;
let configPath = 'apple-design.mcp.json';
const only = [];
const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i++) {
  const arg = argv[i];
  if (arg === '--timeout') {
    timeoutMs = Number(argv[++i]) * 1000;
  } else if (arg === '--config') {
    configPath = argv[++i];
  } else if (arg === '-h' || arg === '--help') {
    console.log(readFileSync(fileURLToPath(import.meta.url), 'utf8').split('\n').slice(1, 15).join('\n'));
    process.exit(0);
  } else {
    only.push(arg);
  }
}
if (!configPath || Number.isNaN(timeoutMs)) {
  console.error('usage: check_apple_design_mcp.mjs [--config FILE] [--timeout SECONDS] [server...]');
  process.exit(2);
}

// Same expansion rules Claude Code applies to .mcp.json: ${VAR} and ${VAR:-default}.
const baseEnv = { ...process.env, CLAUDE_PROJECT_DIR: process.env.CLAUDE_PROJECT_DIR || ROOT };
const expand = (value, env) =>
  value.replace(/\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}/g, (match, name, fallback) => env[name] ?? fallback ?? match);

const config = JSON.parse(readFileSync(resolve(ROOT, configPath), 'utf8'));
const servers = Object.entries(config.mcpServers ?? {}).filter(([name]) => only.length === 0 || only.includes(name));
const unknown = only.filter((name) => !config.mcpServers?.[name]);
if (unknown.length) {
  console.error(`unknown server(s): ${unknown.join(', ')}`);
  process.exit(2);
}

const stderrTail = (text) => {
  const lines = text.trim().split('\n').filter(Boolean).slice(-3).join(' | ');
  return lines ? ` -- stderr: ${lines.slice(0, 300)}` : '';
};

function probe(name, spec) {
  return new Promise((done) => {
    if (spec.type && spec.type !== 'stdio') {
      done({ name, status: 'skipped', detail: `${spec.type} transport, not a local process` });
      return;
    }
    const env = { ...baseEnv };
    for (const [key, value] of Object.entries(spec.env ?? {})) env[key] = expand(String(value), env);
    const command = expand(spec.command, env);
    const args = (spec.args ?? []).map((arg) => expand(String(arg), env));
    const started = Date.now();

    let child;
    try {
      child = spawn(command, args, { env, stdio: ['pipe', 'pipe', 'pipe'], shell: process.platform === 'win32' });
    } catch (err) {
      done({ name, status: 'failed', detail: err.message });
      return;
    }

    let stdout = '';
    let stderr = '';
    let finished = false;
    const finish = (result) => {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      child.stdin.end(); // well-behaved servers exit on stdin EOF, including the children of npx/uv wrappers
      child.kill();
      done({ name, ms: Date.now() - started, ...result });
    };
    const timer = setTimeout(
      () => finish({ status: 'failed', detail: `no tools/list reply within ${timeoutMs / 1000}s${stderrTail(stderr)}` }),
      timeoutMs,
    );
    const send = (message) => {
      try {
        child.stdin.write(`${JSON.stringify(message)}\n`);
      } catch {
        // a dead pipe is reported through the 'error' / 'exit' handlers
      }
    };

    child.on('error', (err) =>
      finish({ status: 'failed', detail: err.code === 'ENOENT' ? `command not found: ${command}` : err.message }),
    );
    child.on('exit', (code, signal) =>
      finish({ status: 'failed', detail: `exited before replying (${signal ?? `code ${code}`})${stderrTail(stderr)}` }),
    );
    child.stdin.on('error', () => {});
    child.stderr.on('data', (chunk) => {
      stderr += chunk;
    });
    child.stdout.on('data', (chunk) => {
      stdout += chunk;
      let newline;
      while ((newline = stdout.indexOf('\n')) >= 0) {
        const line = stdout.slice(0, newline).trim();
        stdout = stdout.slice(newline + 1);
        if (!line) continue;
        let message;
        try {
          message = JSON.parse(line);
        } catch {
          continue; // servers occasionally log plain text on stdout
        }
        if (message.id === 1) {
          if (message.error) {
            finish({ status: 'failed', detail: `initialize error: ${message.error.message}` });
            return;
          }
          send({ jsonrpc: '2.0', method: 'notifications/initialized' });
          send({ jsonrpc: '2.0', id: 2, method: 'tools/list', params: {} });
        } else if (message.id === 2) {
          if (message.error) {
            finish({ status: 'failed', detail: `tools/list error: ${message.error.message}` });
            return;
          }
          const tools = message.result?.tools ?? [];
          const names = tools.slice(0, 5).map((tool) => tool.name).join(', ');
          finish({ status: 'ok', tools: tools.length, detail: names + (tools.length > 5 ? ', ...' : '') });
        }
      }
    });

    send({
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: {
        protocolVersion: '2025-06-18',
        capabilities: {},
        clientInfo: { name: 'tradingview-mcp-apple-design-check', version: '1.0.0' },
      },
    });
  });
}

const results = [];
const queue = [...servers];
async function worker() {
  while (queue.length) {
    const [name, spec] = queue.shift();
    const result = await probe(name, spec);
    results.push(result);
    const seconds = result.ms ? ` (${(result.ms / 1000).toFixed(1)}s)` : '';
    const tools = result.tools === undefined ? '' : ` ${result.tools} tools:`;
    console.log(`${result.status.padEnd(7)} ${name.padEnd(20)}${tools} ${result.detail}${seconds}`);
  }
}
await Promise.all(Array.from({ length: Math.min(CONCURRENCY, servers.length) }, worker));

const failed = results.filter((result) => result.status === 'failed');
console.log(`\n${results.length - failed.length}/${results.length} servers answered tools/list`);
if (failed.length) {
  console.log('Failed servers: run bash scripts/install_apple_design_mcp.sh, then check the manual steps it prints.');
  process.exit(1);
}
