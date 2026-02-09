#!/usr/bin/env node
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import dotenv from "dotenv";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.resolve(__dirname, "..", ".env") });

const baseUrl = (process.env.N8N_BASE_URL || "http://localhost:5678").replace(/\/$/, "");
const apiBase = (process.env.N8N_API_BASE || "/api").replace(/\/$/, "");
const apiVersion = process.env.N8N_API_VERSION || "1";
const apiKey = process.env.N8N_API_KEY || "";
const timeoutSeconds = Number(process.env.N8N_TIMEOUT_SECONDS || "30");

function makeUrl(p) {
  const pathPart = p.startsWith("/") ? p : `/${p}`;
  return `${baseUrl}${apiBase}/v${apiVersion}${pathPart}`;
}

async function requestJson(method, url, payload) {
  const headers = { Accept: "application/json" };
  if (apiKey) headers["X-N8N-API-KEY"] = apiKey;
  if (payload !== undefined) headers["Content-Type"] = "application/json";

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutSeconds * 1000);

  try {
    const res = await fetch(url, {
      method,
      headers,
      body: payload !== undefined ? JSON.stringify(payload) : undefined,
      signal: controller.signal,
    });
    const text = await res.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = null;
    }

    if (!res.ok) {
      const msg = data ?? text;
      throw new Error(`HTTP ${res.status}: ${typeof msg === "string" ? msg : JSON.stringify(msg)}`);
    }

    return data ?? text;
  } finally {
    clearTimeout(timeout);
  }
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}

function writeJson(filePath, data) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), "utf-8");
}

function printUsage() {
  console.log(`n8n management CLI

Commands:
  ping [--path /healthz]
  list-workflows
  get-workflow <id>
  export-workflow <id> --out <file>
  import-workflow <file>
  activate <id>
  deactivate <id>
  execute <id> [--payload <file>]
  list-executions
  get-execution <id>
  request <METHOD> <path> [--payload <file>]
`);
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    printUsage();
    process.exit(1);
  }

  const cmd = args[0];

  if (cmd === "ping") {
    const pathArg = args[1] === "--path" ? args[2] : "/healthz";
    const url = `${baseUrl}${pathArg}`;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutSeconds * 1000);
    try {
      const res = await fetch(url, { signal: controller.signal });
      const text = await res.text();
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${text}`);
      console.log(text.trim() || "ok");
    } finally {
      clearTimeout(timeout);
    }
    return;
  }

  if (cmd === "list-workflows") {
    const data = await requestJson("GET", makeUrl("/workflows"));
    console.log(JSON.stringify(data, null, 2));
    return;
  }

  if (cmd === "get-workflow") {
    const id = args[1];
    const data = await requestJson("GET", makeUrl(`/workflows/${id}`));
    console.log(JSON.stringify(data, null, 2));
    return;
  }

  if (cmd === "export-workflow") {
    const id = args[1];
    const outIndex = args.indexOf("--out");
    if (!id || outIndex === -1 || !args[outIndex + 1]) throw new Error("Missing --out <file>");
    const outFile = args[outIndex + 1];
    const data = await requestJson("GET", makeUrl(`/workflows/${id}`));
    writeJson(outFile, data);
    console.log(outFile);
    return;
  }

  if (cmd === "import-workflow") {
    const file = args[1];
    const payload = readJson(file);
    const data = await requestJson("POST", makeUrl("/workflows"), payload);
    console.log(JSON.stringify(data, null, 2));
    return;
  }

  if (cmd === "activate") {
    const id = args[1];
    const data = await requestJson("POST", makeUrl(`/workflows/${id}/activate`));
    console.log(JSON.stringify(data, null, 2));
    return;
  }

  if (cmd === "deactivate") {
    const id = args[1];
    const data = await requestJson("POST", makeUrl(`/workflows/${id}/deactivate`));
    console.log(JSON.stringify(data, null, 2));
    return;
  }

  if (cmd === "execute") {
    const id = args[1];
    const payloadIndex = args.indexOf("--payload");
    const payload = payloadIndex !== -1 ? readJson(args[payloadIndex + 1]) : undefined;
    const data = await requestJson("POST", makeUrl(`/workflows/${id}/execute`), payload);
    console.log(JSON.stringify(data, null, 2));
    return;
  }

  if (cmd === "list-executions") {
    const data = await requestJson("GET", makeUrl("/executions"));
    console.log(JSON.stringify(data, null, 2));
    return;
  }

  if (cmd === "get-execution") {
    const id = args[1];
    const data = await requestJson("GET", makeUrl(`/executions/${id}`));
    console.log(JSON.stringify(data, null, 2));
    return;
  }

  if (cmd === "request") {
    const method = args[1];
    const p = args[2];
    const payloadIndex = args.indexOf("--payload");
    const payload = payloadIndex !== -1 ? readJson(args[payloadIndex + 1]) : undefined;
    const url = p.startsWith("/api/") ? `${baseUrl}${p}` : makeUrl(p);
    const data = await requestJson(method.toUpperCase(), url, payload);
    console.log(JSON.stringify(data, null, 2));
    return;
  }

  printUsage();
  process.exit(1);
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
