import fs from "node:fs";
import crypto from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const target = path.join(root, ".env");
if (fs.existsSync(target)) {
  if (process.argv.includes("--rotate-internal")) {
    let content = fs.readFileSync(target, "utf8");
    const line =
      "RELAYDESK_INTERNAL_KEY=" + crypto.randomBytes(32).toString("hex");
    content = /^RELAYDESK_INTERNAL_KEY=/m.test(content)
      ? content.replace(/^RELAYDESK_INTERNAL_KEY=.*$/m, line)
      : content + "\n" + line + "\n";
    fs.writeFileSync(target, content, { mode: 0o600 });
    console.log(
      "Rotated the internal service key. Re-import credentials and recreate services to apply it.",
    );
  } else console.log("Using existing .env; keys preserved.");
} else {
  fs.writeFileSync(
    target,
    [
      `RELAYDESK_INTERNAL_KEY=${crypto.randomBytes(32).toString("hex")}`,
      `N8N_ENCRYPTION_KEY=${crypto.randomBytes(32).toString("hex")}`,
      "RELAYDESK_PORT=18080",
      "RELAYDESK_N8N_PORT=15678",
      "RELAYDESK_OLLAMA_URL=http://host.docker.internal:11434",
      "RELAYDESK_OLLAMA_MODEL=llama3.2:3b",
      "RELAYDESK_PORTAL_KEY=",
      "",
    ].join("\n"),
    { mode: 0o600, flag: "wx" },
  );
  console.log(
    "Created .env with independent random service and encryption keys.",
  );
}
