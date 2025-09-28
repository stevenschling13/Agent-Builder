// app.js
// Single-file glue for the 3-part flow: OpenAI (GPT Actions) → n8n → Notion.
// - Serves OpenAPI schema at /openapi.json for GPT Actions.
// - Exposes /actions/* endpoints that forward to n8n webhooks.
// - Falls back to Notion direct (create/update) if n8n is down.
// Refs: GPT Actions + OpenAPI, n8n Webhook node behavior, Notion Pages/Databases APIs. 
// (Docs cited after code.)

import 'dotenv/config';
import express from 'express';
import fetch from 'node-fetch';
import crypto from 'crypto';
import { Client as Notion } from '@notionhq/client';

const {
  PORT = 3000,
  // Security
  API_KEY,                   // optional shared secret for X-BB-Key
  HMAC_SECRET,               // optional HMAC for X-BB-Signature (hex sha256 of raw body)

  // n8n
  N8N_BASE,                  // e.g. https://bloombuddy13.app.n8n.cloud
  N8N_CREATE_TASK = '/webhook/create-task',
  N8N_GET_CONTEXT = '/webhook/get-context',
  N8N_UPSERT = '/webhook/upsert-analysis',

  // Notion fallback
  NOTION_TOKEN,
  PLANTS_DB_ID,              // Notion DB: Plants
  LOGS_DB_ID,                // Notion DB: Logs
} = process.env;

const app = express();

// capture raw for HMAC
app.use(express.json({
  verify: (req, _res, buf) => { req.rawBody = buf; }
}));

// ---------- helpers ----------
const okKey = req => !API_KEY || req.header('X-BB-Key') === API_KEY;
const okHmac = req => {
  if (!HMAC_SECRET) return true;
  const sent = req.header('X-BB-Signature') || '';
  const mac = crypto.createHmac('sha256', HMAC_SECRET).update(req.rawBody || '').digest('hex');
  return sent && crypto.timingSafeEqual(Buffer.from(sent), Buffer.from(mac));
};

const guard = handler => async (req, res) => {
  try {
    if (!okKey(req)) return res.status(401).json({ error: 'bad key' });
    if (!okHmac(req)) return res.status(401).json({ error: 'bad signature' });
    await handler(req, res);
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: e.message });
  }
};

// DLI = PPFD * 3600 * hours / 1e6
const dli = (ppfd, hours) =>
  (ppfd == null || hours == null) ? null : +(ppfd * 3600 * hours / 1e6).toFixed(2);

// Notion helpers (fallback path)
const notion = NOTION_TOKEN ? new Notion({ auth: NOTION_TOKEN }) : null;
const titleProp = s => ({ title: [{ type: 'text', text: { content: String(s ?? '') } }] });
const rtProp    = s => ({ rich_text: [{ type: 'text', text: { content: String(s ?? '') } }] });
const numProp   = n => (n == null || isNaN(n) ? { number: null } : { number: +n });
const dateProp  = iso => ({ date: iso ? { start: iso } : null });
const selProp   = s => (s ? { select: { name: s } } : { select: null });
const relProp   = id => ({ relation: id ? [{ id }] : [] });

// Find plant page by "Plant ID" (Title) in Plants DB
async function findPlantPage(plantId) {
  const r = await notion.databases.query({
    database_id: PLANTS_DB_ID,
    filter: { property: 'Plant ID', title: { equals: String(plantId) } },
    page_size: 1
  });
  return r.results[0]?.id || null;
}

// Find log page by "Run ID" (rich text) in Logs DB
async function findLogByRun(runId) {
  const r = await notion.databases.query({
    database_id: LOGS_DB_ID,
    filter: { property: 'Run ID', rich_text: { equals: String(runId) } },
    page_size: 1
  });
  return r.results[0] || null;
}

async function upsertLog({
  run_id, plant_id, timestamp, stage, scores = {}, metrics = {}, image_urls = [], version = 'v1', title
}) {
  const plantPage = await findPlantPage(plant_id);
  if (!plantPage) throw new Error('plant not found (Notion fallback)');

  const computedDLI = metrics.DLI ?? dli(metrics.PPFD, metrics['Photoperiod h']);
  const props = {
    Title: titleProp(title || `${plant_id} — ${timestamp || new Date().toISOString()}`),
    Plant: relProp(plantPage),
    'Run ID': rtProp(run_id || ''),
    Timestamp: dateProp(timestamp),
    Stage: selProp(stage),

    Vigor: numProp(scores.Vigor),
    Color: numProp(scores.Color),
    Turgor: numProp(scores.Turgor),
    'Leaf Morph': numProp(scores['Leaf Morph']),
    Internode: numProp(scores.Internode),
    Canopy: numProp(scores.Canopy),
    Training: numProp(scores.Training),
    'Flower Maturity': numProp(scores['Flower Maturity']),
    'Pest Pressure': numProp(scores['Pest Pressure']),
    'Abiotic Stress': numProp(scores['Abiotic Stress']),

    PPFD: numProp(metrics.PPFD),
    'Photoperiod h': numProp(metrics['Photoperiod h']),
    DLI: numProp(computedDLI),
    'Temp C': numProp(metrics['Temp C']),
    'RH %': numProp(metrics['RH %']),
    'VPD kPa': numProp(metrics['VPD kPa']),
    'CO2 ppm': numProp(metrics['CO2 ppm']),
    'EC in': numProp(metrics['EC in']),
    'EC out': numProp(metrics['EC out']),
    'pH in': numProp(metrics['pH in']),
    'pH out': numProp(metrics['pH out']),
    'Images (URLs)': rtProp((image_urls || []).join('\n')),
    Version: rtProp(version),
  };

  const existing = run_id ? await findLogByRun(run_id) : null;
  if (existing?.id) {
    await notion.pages.update({ page_id: existing.id, properties: props });
    return { id: existing.id, updated: true, dli: computedDLI };
  } else {
    const created = await notion.pages.create({ parent: { database_id: LOGS_DB_ID }, properties: props });
    return { id: created.id, created: true, dli: computedDLI };
  }
}

// ---------- OpenAPI for GPT Actions ----------
app.get('/openapi.json', (_req, res) => {
  const serverUrl = process.env.PUBLIC_BASE_URL || 'http://localhost:' + PORT;
  res.json({
    openapi: '3.1.0',
    info: { title: 'BloomBuddy Actions', version: '1.0.0' },
    servers: [{ url: serverUrl }],
    components: {
      securitySchemes: { ApiKeyAuth: { type: 'apiKey', in: 'header', name: 'X-BB-Key' } }
    },
    security: API_KEY ? [{ ApiKeyAuth: [] }] : [],
    paths: {
      '/actions/create-task': {
        post: {
          operationId: 'createTask',
          description: 'Test task creation via n8n webhook.',
          requestBody: { required: true, content: { 'application/json': { schema: {
            type: 'object', properties: { title: { type: 'string' } }, required: ['title']
          }}}},
          responses: { '200': { description: 'OK' } }
        }
      },
      '/actions/get-context': {
        post: {
          operationId: 'getContext',
          description: 'Fetch plant context by plant_id (proxied to n8n, with Notion fallback).',
          requestBody: { required: true, content: { 'application/json': { schema: {
            type: 'object', properties: { plant_id: { type: 'string' } }, required: ['plant_id']
          }}}},
          responses: { '200': { description: 'OK' } }
        }
      },
      '/actions/upsert-analysis': {
        post: {
          operationId: 'upsertAnalysis',
          description: 'Upsert a Logs row (scores/metrics/images). Computes DLI if missing.',
          requestBody: { required: true, content: { 'application/json': { schema: {
            type: 'object',
            properties: {
              run_id: { type: 'string' },
              plant_id: { type: 'string' },
              timestamp: { type: 'string' },
              stage: { type: 'string' },
              scores: { type: 'object' },
              metrics: { type: 'object' },
              image_urls: { type: 'array', items: { type: 'string' } },
              version: { type: 'string' },
              title: { type: 'string' }
            },
            required: ['plant_id']
          }}}},
          responses: { '200': { description: 'OK' } }
        }
      }
    }
  });
});

// ---------- Action endpoints (proxy → n8n; fallback → Notion) ----------
async function proxyOr(res, path, body, fallback) {
  const base = N8N_BASE;
  if (base) {
    try {
      const r = await fetch(new URL(path, base).toString(), {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(body)
      });
      if (r.ok) return res.status(r.status).json(await r.json());
      // if n8n returns non-200, try fallback if provided
    } catch (e) {
      // fall through to fallback
    }
  }
  if (!fallback) return res.status(502).json({ error: 'n8n not reachable' });
  try {
    const out = await fallback();
    return res.json(out);
  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
}

app.post('/actions/create-task', guard(async (req, res) => {
  await proxyOr(res, N8N_CREATE_TASK, req.body, async () => {
    const { title } = req.body || {};
    return { title, status: 'created (fallback)' };
  });
}));

app.post('/actions/get-context', guard(async (req, res) => {
  const { plant_id } = req.body || {};
  if (!plant_id) return res.status(400).json({ error: 'plant_id required' });
  await proxyOr(res, N8N_GET_CONTEXT, req.body, async () => {
    if (!notion) throw new Error('Notion not configured');
    const plantPage = await findPlantPage(plant_id);
    if (!plantPage) return { error: 'plant not found (fallback)' };
    const page = await notion.pages.retrieve({ page_id: plantPage });
    return { plant_page_id: plantPage, properties: page.properties };
  });
}));

app.post('/actions/upsert-analysis', guard(async (req, res) => {
  await proxyOr(res, N8N_UPSERT, req.body, async () => {
    if (!notion) throw new Error('Notion not configured');
    return await upsertLog(req.body || {});
  });
}));

// ---------- boot ----------
app.listen(PORT, () => {
  console.log(`BloomBuddy Actions listening on :${PORT}  (OpenAPI at /openapi.json)`);
});

// Docs
// - OpenAI GPT Actions: https://platform.openai.com/docs/actions
// - OpenAPI 3.1.0: https://spec.openapis.org/oas/latest.html
// - n8n Webhook node: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/
// - Notion API: https://developers.notion.com/reference
