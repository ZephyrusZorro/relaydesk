export function bootstrapPlan(existingIds, refreshCore = false, pendingIds = []) {
  const existing = new Set(existingIds);
  const pending = new Set(pendingIds);
  return [
    { id: "RelayDeskIntake01", file: "01-intake.json", core: true },
    { id: "RelayDeskHandoff1", file: "02-handoff.json", core: true },
    { id: "RelayDeskEmail01", file: "03-email-optional.json", core: false },
  ].filter((flow) => !existing.has(flow.id) || (refreshCore && flow.core) || (flow.core && pending.has(flow.id)));
}
