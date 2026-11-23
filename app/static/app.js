const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const paths = {
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  inbox: '<path d="M4 4h16l2 11v5H2v-5L4 4Z"/><path d="M2 15h6l2 3h4l2-3h6"/>',
  book: '<path d="M12 5v16M3 3c4-1 7 0 9 2 2-2 5-3 9-2v16c-4-1-7 0-9 2-2-2-5-3-9-2V3Z"/>',
  workflow:
    '<rect x="3" y="2" width="6" height="6" rx="2"/><rect x="15" y="16" width="6" height="6" rx="2"/><rect x="3" y="16" width="6" height="6" rx="2"/><path d="M6 8v8M9 5h5a4 4 0 0 1 4 4v7"/>',
  external:
    '<path d="M14 3h7v7M21 3l-10 10M10 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-5"/>',
  help: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 0 1 5 0c0 2-2.5 2-2.5 4M12 16v.1"/>',
  refresh: '<path d="M20 8a8 8 0 1 0 0 8M20 3v5h-5"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  chevron: '<path d="m9 5 7 7-7 7"/>',
  shield:
    '<path d="m12 2 9 4v6c0 5-9 10-9 10S3 17 3 12V6l9-4Z"/><path d="m8 12 3 3 5-6"/>',
  chart: '<path d="M4 3v18h18M9 16V9M14 16V5M19 16v-5"/>',
  download: '<path d="M12 3v12m-5-5 5 5 5-5M4 15v6h16v-6"/>',
  search: '<circle cx="10.5" cy="10.5" r="7.5"/><path d="m16 16 5 5"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7v.1"/>',
  play: '<path d="m8 4 13 8-13 8V4Z"/>',
  mail: '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m2 5 10 8L22 5"/>',
  close: '<path d="m6 6 12 12M6 18 18 6"/>',
  mic: '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8"/>',
  vpn: '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3"/>',
  network:
    '<path d="M2 8a16 16 0 0 1 20 0M5 12a11 11 0 0 1 14 0M8.5 16a6 6 0 0 1 7 0M12 20v.1"/>',
  account:
    '<circle cx="12" cy="7" r="4"/><path d="M4 22v-2a8 8 0 0 1 16 0v2"/>',
  device:
    '<rect x="3" y="3" width="18" height="13" rx="2"/><path d="M12 16v5M8 21h8"/>',
  software:
    '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="m9 9-3 3 3 3m6-6 3 3-3 3"/>',
  other:
    '<circle cx="12" cy="12" r="9"/><path d="M8 12h.1M12 12h.1M16 12h.1"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  copy: '<rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 8V3H3v13h5"/>',
  speaker:
    '<path d="m11 3-6 5H2v8h3l6 5V3ZM15 8a6 6 0 0 1 0 8M18 5a10 10 0 0 1 0 14"/>',
};
function icon(name) {
  return `<svg viewBox="0 0 24 24" aria-hidden="true">${paths[name] || paths.other}</svg>`;
}
function icons(root = document) {
  $$("[data-icon]", root).forEach(
    (el) => (el.innerHTML = icon(el.dataset.icon)),
  );
}
function e(value) {
  return String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
}
const labels = {
  network: "Network",
  vpn: "VPN",
  account: "Account",
  software: "Software",
  device: "Device",
  other: "Other",
  needs_review: "Needs review",
  approved: "Approved",
  resolved: "Resolved",
  normal: "Normal",
  high: "High",
  urgent: "Urgent",
  sample: "Sample fixture",
  demo: "Demo rules",
  live: "Local LLM",
  live_fallback: "Model fallback",
};
const state = {
  tickets: [],
  documents: [],
  events: [],
  pendingCount: 0,
  health: {},
  view: "overview",
  detail: null,
  tab: "response",
  draft: "",
  requestId: crypto.randomUUID(),
  busy: false,
};
let toastTimer;
function toast(message, error = false) {
  clearTimeout(toastTimer);
  const t = $("#toast");
  ($$('dialog[open]').at(-1) || document.body).append(t);
  t.textContent = message;
  t.className = "toast" + (error ? " error" : "");
  t.hidden = false;
  toastTimer = setTimeout(() => (t.hidden = true), error ? 10000 : 5000);
}
async function api(url, options = {}) {
  let response;
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        "X-Portal-Key": sessionStorage.getItem("relaydesk-key") || "",
        ...options.headers,
      },
    });
  } catch {
    throw new Error(
      "The local service is unreachable. Check Docker and try again.",
    );
  }
  const value = await response
    .json()
    .catch(() => ({ detail: "Unexpected service response" }));
  if (!response.ok) {
    const error = new Error(
      typeof value.detail === "string"
        ? value.detail
        : "Check the request fields and try again.",
    );
    error.status = response.status;
    throw error;
  }
  return value;
}
const post = (url, body) =>
  api(url, { method: "POST", body: JSON.stringify(body) });
const patch = (url, body) =>
  api(url, { method: "PATCH", body: JSON.stringify(body) });
const del = (url) => api(url, { method: "DELETE" });
function tag(text, color = "neutral") {
  return `<span class="tag ${color}">${e(text)}</span>`;
}
function statusTag(status) {
  return tag(
    labels[status] || status,
    status === "approved"
      ? "mint"
      : status === "resolved"
        ? "neutral"
        : "violet",
  );
}
function relative(date) {
  const mins = Math.max(0, Math.floor((Date.now() - new Date(date)) / 60000));
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  if (mins < 1440) return `${Math.floor(mins / 60)}h ago`;
  return `${Math.floor(mins / 1440)}d ago`;
}
function time(date) {
  return new Date(date).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}
function empty(title, detail, which = "inbox") {
  return `<div class="empty"><span data-icon="${which}">${icon(which)}</span><strong>${e(title)}</strong>${e(detail)}</div>`;
}
function row(t) {
  return `<button class="request-row" data-ticket="${e(t.id)}"><span class="category-icon ${e(t.category)}">${icon(t.category)}</span><span class="request-info"><span class="request-title">${e(t.summary)}</span><span class="request-meta"><span>${e(t.id)}</span><span>·</span><span>${e(t.requester)}</span><span>·</span><span>${e(t.location || "Location needed")}</span></span></span><span class="request-side">${statusTag(t.status)}<small>${relative(t.updated_at)}</small></span></button>`;
}
function renderOverview() {
 const pending=state.tickets.filter(t=>t.status==='needs_review'),resolved=state.tickets.filter(t=>t.status==='resolved'),grounded=state.tickets.filter(t=>t.grounded);
 $('#stats').innerHTML=[['Active requests',state.tickets.length-resolved.length,'Across all support services','inbox',''],['Awaiting approval',pending.length,'Your next decisions','shield','violet'],['Resolved requests',resolved.length,'Confirmed by an operator','check','mint'],['Evidence attached',`${grounded.length}/${state.tickets.length}`,'With traceable source citations','book','']].map(([label,value,note,ic,color])=>`<article class="stat ${color}"><div class="stat-top"><span>${label}</span>${icon(ic)}</div><div class="stat-value">${value}</div><div class="stat-note">${note}</div></article>`).join('');
 $('#review-count').textContent=pending.length;
 $('#attention-list').innerHTML=pending.slice(0,5).map(row).join('')||empty('You’re all caught up.','New drafts will appear here when they are ready for review.');
 const activeJob=state.jobs.find(j=>j.state==='running');
 const liveStageMap={classifying:'01',retrieving:'02',drafting:'03',reviewing:'04'};
 const activeNum=activeJob?liveStageMap[activeJob.stage]:null;
 $('#pipeline').innerHTML=[['inbox','Classifier specialist','Identify the service and its support team.','01'],['book','Evidence retrieval','Search a cached, versioned knowledge index.','02'],['workflow','Resolution specialist','Draft a response grounded in the sources.','03'],['shield','Independent reviewer','Validate the draft before operator approval.','04']].map(([ic,title,detail,num])=>`<div class="pipeline-step${activeNum===num?' live-stage':''}"><span class="step-icon">${icon(ic)}</span><div><strong>${title}</strong><p>${detail}</p></div><span class="step-index">${activeNum===num?'ACTIVE':num}</span></div>`).join('');
 const max=Math.max(1,...['network','vpn','account','software','device'].map(c=>state.tickets.filter(t=>t.category===c).length));
 $('#service-mix').innerHTML=['network','vpn','account','software','device'].map(c=>{const n=state.tickets.filter(t=>t.category===c).length;return `<div class="mix-row"><span>${labels[c]}</span><div class="mix-bar"><div style="width:${n/max*100}%"></div></div><span>${n}</span></div>`;}).join('');
 $('#nav-count').textContent=pending.length;
 $('#worker-badge').textContent=state.health.jobs?.worker_online?'Worker online':'Worker offline';
 $('#worker-badge').className='tag '+(state.health.jobs?.worker_online?'mint':'amber');
 $('#recent-jobs').innerHTML=state.jobs.length?state.jobs.slice(0,4).map(j=>`<button class="job-compact" data-job="${e(j.id)}"><span class="job-marker ${e(j.state)}"></span><div><strong>${e(j.summary)}</strong><small>${e(j.id)} · ${e(stageLabels[j.stage]||j.stage)}</small></div>${tag(jobLabels[j.state]||j.state,j.state==='completed'?'mint':j.state==='failed'?'rose':'violet')}</button>`).join(''):empty('Your next request starts here.','Submit a request to see the worker and n8n execute it.','workflow');
}
function renderQueue() {
  const q = $("#queue-search").value.toLowerCase(),
    status = $("#status-filter").value,
    category = $("#category-filter").value;
  const counts = {
    "": state.tickets.length,
    needs_review: state.tickets.filter((t) => t.status === "needs_review").length,
    approved: state.tickets.filter((t) => t.status === "approved").length,
    resolved: state.tickets.filter((t) => t.status === "resolved").length,
  };
  const pillBox = $("#status-pills");
  if (pillBox) {
    pillBox.innerHTML = [
      ["", "All requests"],
      ["needs_review", "Needs review"],
      ["approved", "Approved"],
      ["resolved", "Resolved"],
    ]
      .map(
        ([key, label]) =>
          `<button type="button" role="tab" aria-selected="${status === key}" class="status-pill${status === key ? " active" : ""}" data-status-pill="${key}">${label} <span>${counts[key]}</span></button>`,
      )
      .join("");
  }
  const list = state.tickets.filter(
    (t) =>
      (!status || t.status === status) &&
      (!category || t.category === category) &&
      `${t.id} ${t.summary} ${t.text} ${t.requester} ${t.location}`
        .toLowerCase()
        .includes(q),
  );
  $("#queue-table").innerHTML = list.length
    ? `<div class="table-wrap"><table><thead><tr><th>Request</th><th>Service</th><th>Priority</th><th>Status</th><th>Updated</th></tr></thead><tbody>${list.map((t) => `<tr><td><button data-ticket="${e(t.id)}">${e(t.summary)}</button><span class="table-id">${e(t.id)} · ${e(t.requester)}</span></td><td><span class="category-icon ${e(t.category)}">${icon(t.category)}</span>${e(labels[t.category])}</td><td>${tag(labels[t.priority], t.priority === "urgent" ? "rose" : t.priority === "high" ? "amber" : "neutral")}</td><td>${statusTag(t.status)}</td><td>${relative(t.updated_at)}</td></tr>`).join("")}</tbody></table></div>`
    : empty(
        "No matching requests.",
        "Try another search or clear the filters.",
      );
}
function renderKnowledge() {
  $("#document-count").textContent = `${state.documents.length} procedures`;
  $("#knowledge-grid").innerHTML = state.documents
    .map(
      (d) =>
        `<article class="panel knowledge-card"><div class="card-top"><span class="category-icon ${e(d.category)}">${icon(d.category)}</span>${tag(d.trusted ? "Reviewed" : "Unreviewed", d.trusted ? "mint" : "amber")}</div><h3>${e(d.title)}</h3><span class="source-id">${e(d.id)}</span><p>${e(d.content.slice(0, 170))}…</p><div class="card-tags">${tag(labels[d.category])} ${d.synthetic ? tag("Fictional demo") : tag("Custom procedure", "violet")}</div><details><summary>Read full procedure</summary><p>${e(d.content)}</p></details>${d.synthetic ? "" : `<div class="card-actions"><button type="button" class="card-btn" data-toggle-trust="${e(d.id)}" data-next-trust="${d.trusted ? "false" : "true"}">${d.trusted ? "Mark unreviewed" : "Mark reviewed"}</button><button type="button" class="card-btn danger" data-delete-doc="${e(d.id)}">Remove</button></div>`}</article>`,
    )
    .join("");
}
function renderAutomations(){
 const h=state.health,metrics=h.jobs||{},index=h.retrieval_stats||{};
 const cards=[['workflow','n8n orchestration',h.n8n?'Connected':'Not verified',h.n8n, h.n8n?`Authenticated handshake · execution ${h.handshake?.execution_id||''}`:'Test the published connection workflow.'],['clock','Durable worker',metrics.worker_online?'Online':'Offline',metrics.worker_online,`${(metrics.counts?.queued||0)+(metrics.counts?.retrying||0)} queued · ${metrics.counts?.running||0} running`],['other','Local model',h.model_ready?'Available':h.ollama?'Not installed':'Offline',h.model_ready,h.model||'Ollama'],['book','Knowledge index',`${index.chunks||0} chunks`,true,`Revision ${index.revision||0} · ${index.cache_hits||0} query cache hits`]];
 $('#connection-grid').innerHTML=cards.map(([ic,title,status,up,detail])=>`<article class="connection-card"><div class="connection-head"><h3>${title}</h3>${icon(ic)}</div><div class="connection-status ${up?'healthy':'offline'}">${e(status)}</div><p>${e(detail)}</p></article>`).join('');
 const descriptions={RelayDeskIntake01:'Three native specialist agents, cached RAG, policy validation and durable stage callbacks. Requests become review tickets.',RelayDeskHandoff1:'Read approved outbox events and record idempotent support receipts. Approval remains an operator decision.',RelayDeskEmail01:'Optional mailbox intake using the same support workflow. Mailbox credentials and publication are required.',RelayDeskStatus01:'An authenticated website-to-n8n handshake. This verifies this endpoint; it does not imply other workflows are published.'};
 const formatFlowTitle=name=>{const clean=name.replace('RelayDesk · ','');return clean?clean[0].toUpperCase()+clean.slice(1):name;};
 $('#workflow-library').innerHTML=(h.workflows||[]).map(flow=>`<article class="panel automation-card"><span class="automation-icon ${flow.optional?'amber':'violet'}">${icon(flow.optional?'mail':'workflow')}</span><h2>${e(formatFlowTitle(flow.name))}</h2><p>${e(descriptions[flow.id]||'Configured n8n workflow template.')}</p>${tag(flow.id===h.handshake?.workflow_id&&h.n8n?'Handshake verified':flow.optional?'Optional · setup required':'Configured core template',flow.id===h.handshake?.workflow_id&&h.n8n?'mint':'neutral')}<div class="workflow-meta"><span>${flow.nodes} nodes</span><span>${flow.agents} agents</span><span>rev ${e(flow.revision)}</span></div><a class="workflow-link" href="${e(flow.editor_url)}" target="_blank" rel="noopener">Open in n8n ${icon('external')}</a></article>`).join('')||empty('Workflow templates are unavailable.','Check the service deployment and try refreshing.','workflow');
 $('#jobs-count').textContent=`${state.jobs.length} recent jobs`;
 $('#jobs-list').innerHTML=state.jobs.length?state.jobs.map(j=>`<div class="job-row"><span class="job-marker ${e(j.state)}"></span><div><strong>${e(j.summary)}</strong><small>${e(j.id)} · ${e(stageLabels[j.stage]||j.stage)} · attempt ${j.attempts}/${j.max_attempts}${j.execution_id?' · n8n '+e(j.execution_id):''}</small>${j.error?`<small class="job-error">${e(j.error)}</small>`:''}</div>${tag(jobLabels[j.state]||j.state,j.state==='completed'?'mint':j.state==='failed'?'rose':'violet')}<div class="job-actions">${j.ticket_id?`<button class="text-button" data-ticket="${e(j.ticket_id)}">View request</button>`:''}${j.state==='failed'?`<button class="text-button" data-retry-job="${e(j.id)}">Retry</button>`:''}<button class="text-button" data-job="${e(j.id)}">Timeline</button></div></div>`).join(''):empty('No background jobs yet.','Submit a new request to start the durable pipeline.','workflow');
 $('#outbox-count').textContent=`${state.pendingCount} pending · ${state.events.length} recent`;
 $('#run-handoff').disabled=!state.pendingCount||!h.n8n;
 $('#outbox-list').innerHTML=state.events.length?state.events.map(ev=>`<div class="outbox-row"><span class="category-icon">${icon(ev.status==='delivered'?'check':'workflow')}</span><div><button class="text-button" data-ticket="${e(ev.ticket_id)}">${e(ev.ticket_id)}</button><small>${e(ev.id)} · ${time(ev.created_at)}</small>${ev.execution_id?`<small>n8n execution ${e(ev.execution_id)}</small>`:''}</div>${tag(ev.status==='delivered'?'Delivered internally':'Pending',ev.status==='delivered'?'mint':'amber')}</div>`).join(''):empty('No approved handoffs.','Approve a supported draft to queue its first handoff.','shield');
}
function renderHealth(){
 const h=state.health;$('#engine-status').textContent=h.n8n?'n8n connected':'Connection unverified';$('#engine-status').classList.toggle('online',!!h.n8n);
 $('#side-engine-label').textContent=h.n8n?'CONNECTED':'OFFLINE';$('#side-engine-label').className='tag '+(h.n8n?'mint':'amber');
 const banner=$('#connection-banner');banner.hidden=!!h.n8n;banner.textContent='The authenticated n8n connection check is unavailable. Requests can remain safely queued. Check the Workflows view and the published n8n endpoints.';
 if(h.editor_url)$('#canvas-link').href=h.editor_url;
 const liveNote=$('#live-mode-note');
 if(liveNote){liveNote.textContent=h.model_ready?`${h.model||'Ollama'} · ready (3 agent stages)`:h.ollama?`${h.model||'Model'} not pulled in Ollama`:'Ollama offline · uses fallback if unreachable';}
 const index=h.retrieval_stats||{};$('#knowledge-summary').innerHTML=`<div><strong>${state.documents.length}</strong> procedures</div><div><strong>${state.documents.filter(d=>d.trusted).length}</strong> reviewed sources</div><div><strong>${index.cache_hits||0}</strong> query cache hits</div><div>Index revision <strong>${index.revision||0}</strong></div>`;
}
async function refresh(showNotice = false, allowChallenge = true) {
  try {
    const [tickets, knowledge, outbox, health, jobs] = await Promise.all([
      api("/api/tickets"),
      api("/api/knowledge"),
      api("/api/outbox"),
      api("/api/health"),
      api("/api/jobs"),
    ]);
    state.tickets = tickets.tickets;
    state.documents = knowledge.documents;
    state.events = outbox.events;
    state.pendingCount = outbox.pending_count;
    state.health = health;
    state.jobs = jobs.jobs;
    renderOverview();
    renderQueue();
    renderKnowledge();
    renderAutomations();
    renderHealth();
    if (showNotice) toast("Workspace refreshed.");
    return true;
  } catch (err) {
    toast(err.message, true);
    if (err.status === 401 && allowChallenge) await accessKey();
    return false;
  }
}
function navigate(view) {
  if (!["overview", "queue", "knowledge", "automations"].includes(view))
    view = "overview";
  state.view = view;
  $$(".view").forEach((el) => (el.hidden = el.id !== `${view}-view`));
  $$("[data-view]").forEach((el) => {
    el.classList.toggle("active", el.dataset.view === view);
    if (el.dataset.view === view) el.setAttribute("aria-current", "page");
    else el.removeAttribute("aria-current");
  });
  $("#breadcrumb").textContent = {
    overview: "Overview",
    queue: "Requests",
    knowledge: "Knowledge",
    automations: "Workflows",
  }[view];
  if (location.hash !== `#${view}`) history.replaceState(null, "", `#${view}`);
}
function openRequest(prefill) {
  if (state.busy) {
    toast("A request is still running in n8n.");
    return;
  }
  if (prefill) {
    $("#report-text").value = prefill.text;
    $("#location").value = prefill.location;
    $("#requester").value = prefill.requester;
    state.requestId = crypto.randomUUID();
  }
  $("#request-progress").hidden=true;
  if(!$("#request-dialog").open)$("#request-dialog").showModal();
}
async function openTicket(id) {
  try {
    state.detail = await api(`/api/tickets/${encodeURIComponent(id)}`);
    state.tab = "response";
    state.draft = state.detail.approved_response || state.detail.response;
    renderDetail();
    if (!$("#detail-dialog").open) $("#detail-dialog").showModal();
  } catch (err) {
    toast(err.message, true);
  }
}
function renderDetail() {
  const t = state.detail;
  if (!t) return;
  const flags = t.flags
    .map((f) =>
      tag(
        f.replaceAll("_", " "),
        ["physical_hazard", "sensitive_content_redacted"].includes(f)
          ? "amber"
          : "rose",
      ),
    )
    .join("");
  const tabButtons = [
    ["response", "Response"],
    ["evidence", "Evidence", t.citations.length],
    ["agents", "Agent trail", t.trace.length],
    ["audit", "History", t.audit.length],
  ]
    .map(
      ([key, label, n]) =>
        `<button role="tab" aria-selected="${state.tab === key}" class="${state.tab === key ? "active" : ""}" data-tab="${key}">${label}${n !== undefined ? ` (${n})` : ""}</button>`,
    )
    .join("");
  let body = "";
  if (state.tab === "response")
    body = `${t.mode_used === "sample" ? '<div class="notice"><p>This is a seeded example. Submit a new request to execute the n8n workflow.</p></div>' : ""}<label for="response-draft">${t.status === "needs_review" ? "Review and edit the proposed response" : "Approved response"}</label><textarea id="response-draft" class="response-draft" maxlength="6000" ${t.status !== "needs_review" ? "readonly" : ""}>${e(state.draft)}</textarea><div class="response-tools"><button class="button secondary small" id="read-response">${icon("speaker")}Read aloud</button><button class="button secondary small" id="copy-response">${icon("copy")}Copy response</button></div><h3>Suggested support steps</h3><ol class="steps">${t.steps.map((s) => `<li>${e(s)}</li>`).join("")}</ol>${flags ? `<div class="flags">${flags}</div>` : ""}<div class="detail-actions">${t.status === "needs_review" ? `<p>${t.automation_allowed ? "Review the answer and evidence before approving. Approval queues an internal handoff." : "Handoff is blocked by the findings above. Review the procedure or submit a corrected request."}</p><button class="button primary" id="approve-ticket" ${t.automation_allowed ? "" : "disabled"}>${icon("shield")}Approve response</button>` : t.status === "approved" ? '<p>Approval is recorded. Mark resolved after support confirms the issue is fixed.</p><button class="button primary" id="resolve-ticket">Mark resolved</button>' : "<p>This request is resolved. Its evidence and decision history remain available.</p>"}</div>${!t.automation_allowed ? '<button class="text-button" id="resubmit-ticket" style="margin-top:20px">Create a corrected request</button>' : ""}`;
  if (state.tab === "evidence")
    body = t.citations.length
      ? t.citations
          .map(
            (c) =>
              `<article class="evidence-result"><h3>${e(c.title)} ${tag(c.trusted ? "Reviewed" : "Unreviewed", c.trusted ? "mint" : "amber")}</h3><p class="microcopy">${e(c.id)}${c.synthetic ? " · Fictional demo procedure" : ""} · Rank score ${Number(c.score || 0).toFixed(2)}</p><p>${e(c.excerpt)}</p></article>`,
          )
          .join("")
      : empty(
          "No matching evidence.",
          "The workflow abstained from giving unsupported troubleshooting advice.",
          "book",
        );
  if (state.tab === "agents")
    body =
      `<p class="muted">${t.execution_id ? `n8n execution ${e(t.execution_id)} · ` : ""}${e(labels[t.mode_used] || t.mode_used)}. Model traces show summaries, not hidden reasoning.</p>` +
      t.trace
        .map(
          (a, i) =>
            `<article class="trace-row"><span class="trace-icon">${i + 1}</span><h3>${e(a.name)} ${tag(a.kind, a.kind === "model" ? "violet" : a.kind === "retrieval" ? "mint" : "neutral")}</h3><p>${e(a.detail)}</p></article>`,
        )
        .join("");
  if (state.tab === "audit")
    body = t.audit
      .map(
        (a) =>
          `<article class="audit-row"><strong>${e(a.action.replaceAll("_", " "))}</strong><p>${e(a.detail)}</p><small>${time(a.created_at)}</small></article>`,
      )
      .join("");
  $("#detail-content").innerHTML =
    `<div class="detail-top"><span class="detail-id">${e(t.id)}</span><button class="icon-button" data-close="detail-dialog" aria-label="Close request details">${icon("close")}</button></div><h2 class="detail-title">${e(t.summary)}</h2><div class="detail-tags">${statusTag(t.status)}${tag(labels[t.category])}${tag(labels[t.priority], t.priority === "urgent" ? "rose" : t.priority === "high" ? "amber" : "neutral")}${tag(labels[t.mode_used] || t.mode_used, t.mode_used === "live" ? "violet" : "neutral")}</div><div class="detail-report"><span class="tiny-kicker">ORIGINAL REQUEST</span><p>${e(t.text)}</p><small>${e(t.requester)} · ${e(t.location || "Location needed")} · ${time(t.created_at)}</small></div><div class="detail-tabs" role="tablist" aria-label="Request information">${tabButtons}</div><div class="detail-body" role="tabpanel">${body}</div>`;
  if (t.status === "approved" && state.tab === "response")
    $(".detail-actions").insertAdjacentHTML(
      "beforebegin",
      '<label for="resolution-note">Resolution note</label><textarea id="resolution-note" maxlength="1000" rows="2" placeholder="What confirmed the issue was fixed?" style="width:100%;min-height:80px"></textarea>',
    );
  $("#response-draft")?.addEventListener(
    "input",
    (ev) => (state.draft = ev.target.value),
  );
  $("#read-response")?.addEventListener("click", () => speak(state.draft));
  $("#copy-response")?.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(state.draft);
      toast("Response copied.");
    } catch {
      toast("Clipboard unavailable. Select and copy the response text.", true);
    }
  });
  $("#approve-ticket")?.addEventListener("click", async (ev) => {
    ev.currentTarget.disabled = true;
    try {
      const updated = await post(`/api/tickets/${t.id}/approve`, {
        version: t.version,
        response: state.draft,
      });
      state.detail = updated;
      state.draft = updated.approved_response;
      renderDetail();
      await refresh();
      toast("Response approved. One handoff is queued in Workflows.");
    } catch (err) {
      toast(err.message, true);
      await openTicket(t.id);
    }
  });
  $("#resolve-ticket")?.addEventListener("click", async () => {
    const note = $("#resolution-note")?.value.trim();
    if (!note) return;
    if (note.trim().length < 3) {
      toast("Add a resolution note of at least three characters.", true);
      return;
    }
    try {
      state.detail = await post(`/api/tickets/${t.id}/resolve`, {
        version: t.version,
        note,
      });
      renderDetail();
      await refresh();
      toast("Request marked resolved.");
    } catch (err) {
      toast(err.message, true);
    }
  });
  $("#resubmit-ticket")?.addEventListener("click", () => {
    $("#detail-dialog").close();
    openRequest(t);
  });
}
function speak(text) {
  if (!("speechSynthesis" in window)) {
    toast("Speech synthesis is unavailable in this browser.", true);
    return;
  }
  if (speechSynthesis.speaking) {
    speechSynthesis.cancel();
    toast("Read-aloud stopped.");
    return;
  }
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-IN";
  utterance.rate = 0.95;
  utterance.onerror = event => {
    if(!['canceled','interrupted'].includes(event.error))
      toast("The browser could not play speech. Text remains available.", true);
  };
  speechSynthesis.speak(utterance);
  toast("Reading the response. Select Read aloud again to stop.");
}
function accessKey() {
  if (!$("#access-dialog").open) {
    $("#access-error").hidden = true;
    $("#access-dialog").showModal();
    $("#portal-access-key").focus();
  }
}
$("#access-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const key = $("#portal-access-key").value.trim();
  if (!key) {
    $("#access-error").textContent =
      "Enter a key, or choose Clear session key.";
    $("#access-error").hidden = false;
    return;
  }
  const button = $('button[type="submit"]', ev.currentTarget);
  button.disabled = true;
  sessionStorage.setItem("relaydesk-key", key);
  try {
    if (await refresh(false, false)) {
      $("#access-dialog").close();
      $("#portal-access-key").value = "";
    } else {
      $("#access-error").textContent =
        "The workspace could not be opened. Check the key and service status.";
      $("#access-error").hidden = false;
    }
  } finally {
    button.disabled = false;
  }
});
$("#clear-access-key").addEventListener("click", () => {
  sessionStorage.removeItem("relaydesk-key");
  $("#portal-access-key").value = "";
  $("#access-dialog").close();
  toast("Portal key cleared for this browser session.");
});

document.addEventListener("click", (ev) => {
  const view = ev.target.closest("[data-view]");
  if (view) navigate(view.dataset.view);
  const goto = ev.target.closest("[data-goto]");
  if (goto) navigate(goto.dataset.goto);
  const close = ev.target.closest("[data-close]");
  if (close) $("#" + close.dataset.close).close();
  const ticket = ev.target.closest("[data-ticket]");
  if (ticket) openTicket(ticket.dataset.ticket);
  const tab = ev.target.closest("[data-tab]");
  if (tab) {
    state.tab = tab.dataset.tab;
    renderDetail();
    $(`[data-tab="${state.tab}"]`)?.focus();
  }
  const example = ev.target.closest("[data-example]");
  if (example) {
    $("#report-text").value = {
      vpn: "My VPN keeps disconnecting during video calls. The tunnel drops after about five minutes.",
      network:
        "The office Wi-Fi has no internet for everyone on the second floor.",
      account:
        "My account is locked after changing my phone and I cannot complete MFA.",
    }[example.dataset.example];
    if (!$("#location").value) $("#location").value = "Studio · Floor 2";
    $("#report-text").focus();
  }
});
$("#new-button").addEventListener("click", () => openRequest());
$("#refresh-button").addEventListener("click", () => refresh(true));
$("#about-button").addEventListener("click", () =>
  $("#about-dialog").showModal(),
);
$("#access-key-button").addEventListener("click", accessKey);
$("#add-knowledge-button").addEventListener("click", () =>
  $("#knowledge-dialog").showModal(),
);
for (const id of ["queue-search", "status-filter", "category-filter"])
  $("#" + id).addEventListener(
    id === "queue-search" ? "input" : "change",
    renderQueue,
  );
$("#today-label").textContent = new Date().toLocaleDateString(undefined, {
  weekday: "short",
  day: "numeric",
  month: "short",
  year: "numeric",
});
const stageLabels={queued:'Queued',dispatching:'Dispatching',classifying:'Classifying',retrieving:'Retrieving evidence',drafting:'Drafting response',reviewing:'Reviewing',persisting:'Saving ticket',completed:'Completed',retrying:'Retry scheduled',failed:'Needs attention'};
const jobLabels={queued:'Queued',running:'Processing',retrying:'Retry scheduled',failed:'Failed',completed:'Completed'};
let watchedJob=null;
let inspectedJob=null;
function stageTrackHtml(job){
 const phases=['queued','classifying','retrieving','drafting','reviewing','persisting'];
 let current=phases.indexOf(job.stage);
 if(job.stage==='dispatching')current=0;
 if(job.state==='completed')current=phases.length;
 return `<div class="stage-track">${phases.map((phase,i)=>`<span class="stage-pill ${i<current?'done':i===current?'current':''}">${e(stageLabels[phase])}</span>`).join('')}</div>`;
}
function paintJob(job){
 const box=$('#request-progress');box.hidden=false;
 box.innerHTML=`${job.state==='failed'?'':`<span class="spinner"></span>`}<div><strong>${e(stageLabels[job.stage]||job.stage)} · ${e(job.id)}</strong>${job.summary?`<p class="job-watch-summary">${e(job.summary)}</p>`:''}<p>${job.state==='queued'?(state.health.jobs?.worker_online?'Your request is safely queued for the dispatcher.':'The worker is offline. Your request remains safely queued.'):job.state==='failed'?'The bounded retry cycle ended. You can retry from Workflows.':`Attempt ${job.attempts}/${job.max_attempts}. Stages are reported by n8n; processing continues if you close this dialog.`}</p>${stageTrackHtml(job)}</div>`;
}
async function watchJob(id){
 watchedJob=id;
 try{const job=await api('/api/jobs/'+encodeURIComponent(id));if(watchedJob!==id)return;paintJob(job);
 if(job.state==='completed'){watchedJob=null;$('#request-dialog').close();await refresh();await openTicket(job.ticket_id);toast('n8n completed the request. Review the response and its findings.');return;}
 if(job.state==='failed'){watchedJob=null;await refresh();toast('Processing needs attention. Inspect the job and retry in Workflows.',true);return;}
 setTimeout(()=>{if(watchedJob===id)watchJob(id);},1200);
 }catch(err){watchedJob=null;toast(err.message,true);}
}
function renderJobDialog(job){
 const events=(job.events||[]).map((ev,i)=>`<article class="trace-row"><span class="trace-icon">${i+1}</span><h3>${e(stageLabels[ev.stage]||ev.stage)}</h3><p>${e(ev.detail)}</p><small class="muted">${time(ev.created_at)}</small></article>`).join('');
 $('#job-dialog-content').innerHTML=`<div class="modal-header"><div><p class="eyebrow">DURABLE JOB TIMELINE</p><h2>${e(job.id)}</h2></div><button type="button" class="icon-button" data-close="job-dialog" aria-label="Close job timeline">${icon('close')}</button></div><div class="detail-tags" style="margin-bottom:14px">${tag(jobLabels[job.state]||job.state,job.state==='completed'?'mint':job.state==='failed'?'rose':'violet')}${tag(labels[job.mode]||job.mode,'neutral')}${tag(`Attempt ${job.attempts}/${job.max_attempts}`,'neutral')}${job.execution_id?tag(`n8n #${job.execution_id}`,'violet'):''}</div><p class="job-watch-summary">${e(job.summary)}</p><p class="muted" style="margin:4px 0 14px">${e(job.requester)} · Updated ${time(job.updated_at)}</p>${stageTrackHtml(job)}${job.error?`<p class="error-note">${e(job.error)}</p>`:''}<div class="job-events">${events||empty('No stage events recorded yet.','Worker heartbeats and n8n callbacks will appear here.','clock')}</div><div class="modal-footer"><span class="microcopy">Leased worker execution with bounded retries.</span><div style="display:flex;gap:8px">${job.state==='failed'?`<button type="button" class="button secondary" data-retry-job="${e(job.id)}">Retry job</button>`:''}${job.ticket_id?`<button type="button" class="button primary" data-open-from-job="${e(job.ticket_id)}">Open ticket</button>`:''}</div></div>`;
}
async function openJob(id){
 inspectedJob=id;
 try{
  const job=await api('/api/jobs/'+encodeURIComponent(id));
  if(inspectedJob!==id)return;
  renderJobDialog(job);
  if(!$('#job-dialog').open)$('#job-dialog').showModal();
  if(!['completed','failed'].includes(job.state)){
   setTimeout(()=>{if(inspectedJob===id&&$('#job-dialog').open)openJob(id);},1500);
  }
 }catch(err){inspectedJob=null;toast(err.message,true);}
}
$('#job-dialog').addEventListener('close',()=>{inspectedJob=null;});
$('#request-form').addEventListener('submit',async ev=>{
 ev.preventDefault();if(state.busy)return;state.busy=true;$('#submit-request').disabled=true;
 const values=Object.fromEntries(new FormData(ev.currentTarget));
 try{const job=await post('/api/jobs',{...values,request_id:state.requestId,channel:'portal'});state.requestId=crypto.randomUUID();$('#report-text').value='';paintJob(job);watchJob(job.id);await refresh();}catch(err){toast(err.message,true);}finally{state.busy=false;$('#submit-request').disabled=false;}
});
$('#request-dialog').addEventListener('close',()=>{watchedJob=null;});
$('#check-connection').addEventListener('click',async ev=>{const button=ev.currentTarget;button.disabled=true;try{state.health=await post('/api/integrations/check',{});renderHealth();renderAutomations();renderOverview();toast(state.health.n8n?'Authenticated website-to-n8n handshake verified.':'Connection could not be verified. Check the published connection workflow.',!state.health.n8n);}catch(err){toast(err.message,true);}finally{button.disabled=false;}});
$('#global-search').addEventListener('click',()=>{navigate('queue');$('#queue-search').focus();});
if($('#search-kbd'))$('#search-kbd').textContent=/Mac|iPhone|iPad/i.test(navigator.platform||'')?'⌘ K':'Ctrl K';
document.addEventListener('keydown',ev=>{if((ev.ctrlKey||ev.metaKey)&&ev.key.toLowerCase()==='k'){ev.preventDefault();navigate('queue');$('#queue-search').focus();}});
document.addEventListener('click',async ev=>{
 if(ev.target.closest('[data-new-request]'))openRequest();
 const pill=ev.target.closest('[data-status-pill]');
 if(pill){$('#status-filter').value=pill.dataset.statusPill;renderQueue();return;}
 const openFromJob=ev.target.closest('[data-open-from-job]');
 if(openFromJob){$('#job-dialog').close();openTicket(openFromJob.dataset.openFromJob);return;}
 const retry=ev.target.closest('[data-retry-job]');
 if(retry){try{await post('/api/jobs/'+retry.dataset.retryJob+'/retry',{});await refresh();if($('#job-dialog').open&&inspectedJob===retry.dataset.retryJob)openJob(inspectedJob);toast('The job is queued for another bounded retry cycle.');}catch(err){toast(err.message,true);}return;}
 const job=ev.target.closest('[data-job]');
 if(job){openJob(job.dataset.job);return;}
 const toggleTrust=ev.target.closest('[data-toggle-trust]');
 if(toggleTrust){
  toggleTrust.disabled=true;
  const nextTrust=toggleTrust.dataset.nextTrust==='true';
  try{
   await patch('/api/knowledge/'+encodeURIComponent(toggleTrust.dataset.toggleTrust),{trusted:nextTrust});
   await refresh();
   toast(nextTrust?'Procedure marked reviewed. Retrieval cache invalidated.':'Procedure marked unreviewed. Automated handoff will block when cited.');
  }catch(err){toast(err.message,true);toggleTrust.disabled=false;}
  return;
 }
 const delDoc=ev.target.closest('[data-delete-doc]');
 if(delDoc){
  if(!delDoc.dataset.armed){
   delDoc.dataset.armed='1';
   delDoc.textContent='Confirm remove?';
   setTimeout(()=>{if(delDoc.isConnected&&delDoc.dataset.armed){delete delDoc.dataset.armed;delDoc.textContent='Remove';}},4000);
   return;
  }
  delDoc.disabled=true;
  try{
   await del('/api/knowledge/'+encodeURIComponent(delDoc.dataset.deleteDoc));
   await refresh();
   toast('Custom procedure removed. Retrieval index will rebuild on next query.');
  }catch(err){toast(err.message,true);delDoc.disabled=false;}
 }
});
setInterval(async()=>{if(document.hidden)return;try{const [jobs,health,outbox]=await Promise.all([api('/api/jobs'),api('/api/health'),api('/api/outbox')]);state.jobs=jobs.jobs;state.health=health;state.events=outbox.events;state.pendingCount=outbox.pending_count;if(state.jobs.some(job=>job.ticket_id&&!state.tickets.some(ticket=>ticket.id===job.ticket_id))){await refresh();return;}renderOverview();renderAutomations();renderHealth();}catch{/* Explicit refresh surfaces errors; passive polling stays quiet. */}},7000);
$("#knowledge-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const button = $('button[type="submit"]', ev.currentTarget);
  button.disabled = true;
  const form = new FormData(ev.currentTarget);
  try {
    await post("/api/knowledge", {
      title: form.get("title"),
      category: form.get("category"),
      content: form.get("content"),
      trusted: form.has("trusted"),
    });
    $("#knowledge-dialog").close();
    ev.target.reset();
    await refresh();
    toast("Procedure added. The retrieval index will rebuild on its next query.");
  } catch (err) {
    toast(err.message, true);
  } finally {
    button.disabled = false;
  }
});
$("#knowledge-search-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const button = $("button", ev.currentTarget);
  button.disabled = true;
  try {
    const category = $("#knowledge-category")?.value || null;
    const result = await post("/api/knowledge/search", {
      query: $("#knowledge-query").value,
      ...(category ? { category } : {}),
    });
    const d = result.diagnostics || {};
    const diagBar = `<div class="retrieval-diagnostics"><span>${tag(d.cache_hit ? "Cache hit" : "Fresh query", d.cache_hit ? "mint" : "violet")}</span><span><strong>${Number(d.search_ms ?? 0).toFixed(2)} ms</strong></span><span>Index rev <strong>${e(d.index_revision ?? 0)}</strong></span><span><strong>${e(d.indexed_chunks ?? 0)}</strong> chunks</span><span>${e(result.retrieval || "Hybrid lexical")}</span></div>`;
    $("#retrieval-results").innerHTML =
      diagBar +
      (result.citations.length
        ? result.citations
            .map(
              (c) =>
                `<article class="evidence-result"><h3>${e(c.title)} ${tag(c.id, "mint")} ${tag(c.trusted ? "Reviewed" : "Unreviewed", c.trusted ? "mint" : "amber")}</h3><p>${e(c.excerpt)}</p><p class="microcopy">Hybrid lexical rank score: ${Number(c.score).toFixed(2)} · ${c.synthetic ? "Fictional demo source" : "Custom procedure"}</p></article>`,
            )
            .join("")
        : empty(
            "No relevant source found.",
            "Add a reviewed procedure or try a question within the supported services.",
            "book",
          ));
    const health = await api("/api/health").catch(() => null);
    if (health) {
      state.health = health;
      renderHealth();
      renderAutomations();
    }
  } catch (err) {
    toast(err.message, true);
  } finally {
    button.disabled = false;
  }
});
$("#run-handoff").addEventListener("click", async (ev) => {
  ev.currentTarget.disabled = true;
  try {
    const result = await post("/api/automations/run", {});
    await refresh();
    toast(
      `${result.delivered} internal handoff${result.delivered === 1 ? "" : "s"} recorded by n8n.`,
    );
  } catch (err) {
    toast(err.message, true);
    renderAutomations();
  }
});
$("#export-button").addEventListener("click", async () => {
  try {
    const result = await api("/api/export"),
      url = URL.createObjectURL(
        new Blob([JSON.stringify(result, null, 2)], {
          type: "application/json",
        }),
      ),
      a = document.createElement("a");
    a.href = url;
    a.download = `relaydesk-workspace-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast(
      "Workspace export downloaded. It includes request text; store it privately.",
    );
  } catch (err) {
    toast(err.message, true);
  }
});
const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null,
  listening = false;
if (!Recognition) {
  $("#dictate-button").disabled = true;
  $("#speech-status").textContent =
    "Dictation unavailable in this browser. Type your request.";
} else
  $("#dictate-button").addEventListener("click", () => {
    if (listening) {
      recognition.stop();
      return;
    }
    recognition = new Recognition();
    recognition.lang = $("#speech-language").value;
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.onstart = () => {
      listening = true;
      $("#speech-status").textContent =
        "Listening… select Dictate request to stop.";
    };
    recognition.onresult = (ev) => {
      const text = ev.results[0][0].transcript;
      $("#report-text").value = ($("#report-text").value + " " + text)
        .trim()
        .slice(0, 4000);
      $("#speech-status").textContent =
        "Transcript added. Review it before submitting.";
    };
    recognition.onerror = (ev) => {
      $("#speech-status").textContent =
        `Dictation ${ev.error}. You can type your request.`;
    };
    recognition.onend = () => {
      listening = false;
    };
    try {
      recognition.start();
    } catch {
      toast("Could not start dictation. Check microphone permission.", true);
    }
  });
$("#request-dialog").addEventListener("close", () => {
  if (listening) recognition?.stop();
});
$("#detail-dialog").addEventListener("close", () => {
  if ("speechSynthesis" in window) speechSynthesis.cancel();
});
window.addEventListener("hashchange", () => navigate(location.hash.slice(1)));
state.jobs=[];
icons();
navigate(location.hash.slice(1) || "overview");
refresh();
