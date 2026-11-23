import fs from "node:fs";
import { spawnSync } from "node:child_process";
import { bootstrapPlan } from "./bootstrap-plan.mjs";
const key = process.env.RELAYDESK_INTERNAL_KEY;
if (!key || key.length < 32)
  throw new Error("A generated RELAYDESK_INTERNAL_KEY is required.");
function run(args) {
  const result = spawnSync("n8n", args, { stdio: "inherit", env: process.env });
  if (result.status !== 0)
    throw new Error("n8n initialization failed: " + args[0]);
}
const credentials = [
  {
    id: "relaydesk-ingress-jwt",
    name: "RelayDesk short-lived ingress",
    type: "jwtAuth",
    data: { keyType: "passphrase", secret: key, algorithm: "HS256" },
  },
  {
    id: "relaydesk-internal",
    name: "RelayDesk internal service",
    type: "httpHeaderAuth",
    data: { name: "X-Relay-Key", value: key },
  },
  {
    id: "relaydesk-ollama",
    name: "RelayDesk local Ollama",
    type: "ollamaApi",
    data: {
      baseUrl:
        process.env.RELAYDESK_OLLAMA_URL || "http://host.docker.internal:11434",
    },
  },
];
const temporary = "/tmp/relaydesk-initial-credentials.json";
try {
  fs.writeFileSync(temporary, JSON.stringify(credentials), { mode: 0o600 });
  run(["import:credentials", "--input=" + temporary]);
} finally {
  if (fs.existsSync(temporary)) fs.unlinkSync(temporary);
}
const listing = spawnSync("n8n", ["list:workflow", "--onlyId"], {
  encoding: "utf8",
  env: process.env,
});
if (listing.status !== 0)
  throw new Error(
    "Could not inspect existing workflows; refusing to overwrite configuration.",
  );
const marker='/home/node/.n8n/relaydesk-initialization.json';
const pending=new Set(fs.existsSync(marker)?JSON.parse(fs.readFileSync(marker,'utf8')):[]);
function savePending(){fs.writeFileSync(marker+'.tmp',JSON.stringify([...pending]),{mode:0o600});fs.renameSync(marker+'.tmp',marker);}
const plan = bootstrapPlan(
  listing.stdout.split(/\r?\n/).map((line) => line.trim()),
  process.argv.includes("--refresh-core"),
  [...pending],
);
for (const flow of plan) {
  if(flow.core){pending.add(flow.id);savePending();}
  run(["import:workflow", "--input=/opt/relaydesk/workflows/" + flow.file]);
  if (flow.core) {run(["publish:workflow", "--id=" + flow.id]);pending.delete(flow.id);savePending();}
}
console.log(
  `RelayDesk: initialized ${plan.length} workflows. Existing configuration was preserved unless --refresh-core was explicitly requested. Optional email is never auto-published.`,
);
