/**
 * Tests for TV_MCP_READONLY mode: write tools are not registered, read tools are.
 */
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { WRITE_TOOLS, isReadOnly, isWriteTool, installReadOnlyGuard } from '../src/readonly.js';

function fakeServer() {
  const registered = [];
  return { registered, tool(name) { registered.push(name); return name; } };
}

function allDeclaredTools() {
  const dir = join(import.meta.dirname, '..', 'src', 'tools');
  const names = new Set();
  for (const f of readdirSync(dir)) {
    if (!f.endsWith('.js')) continue;
    const src = readFileSync(join(dir, f), 'utf8');
    for (const m of src.matchAll(/server\.tool\(\s*'([a-z_]+)'/g)) names.add(m[1]);
  }
  return names;
}

describe('isReadOnly()', () => {
  it('is off by default', () => {
    assert.equal(isReadOnly({}), false);
  });
  it('accepts 1/true/yes/on (case-insensitive)', () => {
    for (const v of ['1', 'true', 'YES', ' on ']) assert.equal(isReadOnly({ TV_MCP_READONLY: v }), true, v);
  });
  it('rejects 0/false/empty', () => {
    for (const v of ['0', 'false', '']) assert.equal(isReadOnly({ TV_MCP_READONLY: v }), false, v);
  });
});

describe('WRITE_TOOLS list', () => {
  it('only names tools that actually exist (catches renames)', () => {
    const declared = allDeclaredTools();
    for (const name of WRITE_TOOLS) assert.ok(declared.has(name), `${name} is not a registered tool`);
  });
  it('covers every tool that trades, persists, or executes arbitrary UI/JS', () => {
    const mustBlock = ['replay_trade', 'ui_evaluate', 'ui_click', 'alert_create', 'pine_save', 'watchlist_add', 'tv_update'];
    for (const name of mustBlock) assert.ok(isWriteTool(name), `${name} must be a write tool`);
  });
  it('keeps read/navigation tools available', () => {
    for (const name of ['quote_get', 'data_get_ohlcv', 'chart_set_symbol', 'capture_screenshot', 'replay_step', 'draw_list']) {
      assert.equal(isWriteTool(name), false, `${name} must stay available`);
    }
  });
});

describe('installReadOnlyGuard()', () => {
  it('skips write tools and registers the rest', () => {
    const server = fakeServer();
    const skipped = installReadOnlyGuard(server);
    server.tool('quote_get');
    server.tool('replay_trade');
    server.tool('ui_evaluate');
    server.tool('chart_get_state');
    assert.deepEqual(server.registered, ['quote_get', 'chart_get_state']);
    assert.deepEqual(skipped, ['replay_trade', 'ui_evaluate']);
  });
  it('passes remaining arguments through to the original tool()', () => {
    const calls = [];
    const server = { tool: (...args) => { calls.push(args); } };
    installReadOnlyGuard(server);
    server.tool('quote_get', 'desc', { a: 1 }, 'handler');
    assert.deepEqual(calls, [['quote_get', 'desc', { a: 1 }, 'handler']]);
  });
});
