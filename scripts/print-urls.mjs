import fs from "node:fs";
const config = Object.fromEntries(
  fs
    .readFileSync(".env", "utf8")
    .split(/\r?\n/)
    .filter((line) => line.includes("=") && !line.startsWith("#"))
    .map((line) => {
      const i = line.indexOf("=");
      return [line.slice(0, i).trim(), line.slice(i + 1).trim()];
    }),
);
const port = (name, fallback) =>
  /^\d+$/.test(config[name] || "") ? config[name] : fallback;
console.log(
  `RelayDesk portal: http://localhost:${port("RELAYDESK_PORT", "18080")}`,
);
console.log(
  `n8n editor: http://localhost:${port("RELAYDESK_N8N_PORT", "15678")} — create your owner account on first visit.`,
);
