/* Pure functions shared by the exported n8n Code nodes and executable tests.
   The generator embeds this source; n8n needs no community/custom node. */
export const CATEGORIES = ['network','vpn','account','software','device','other'];
export const DEPARTMENTS = {network:'Network Support',vpn:'Network Support',account:'Identity Support',software:'Application Support',device:'Device Support',other:'Service Desk'};

export function decode(raw) {
  if (raw && typeof raw === 'object') return raw;
  const text=String(raw ?? '').replace(/```(?:json)?|```/g,'').trim();
  return JSON.parse(text.slice(text.indexOf('{'),text.lastIndexOf('}')+1));
}

export function normalize(raw) {
  let text=String(raw.text ?? '').trim();
  if (text.length<8 || text.length>4000) throw new Error('Describe the issue in 8–4000 characters.');
  const flags=[];
  const redacted=text.replace(/\b(password|passcode|recovery code|access token|token)\s*(?:is|=|:)\s*[^\s,;.]+/gi,'$1=[REDACTED]');
  if(redacted!==text) flags.push('sensitive_content_redacted');
  text=redacted;
  if(/ignore.{0,30}(previous|instructions)|system prompt|auto.?approve|bypass.{0,20}(review|approval)/i.test(text)) flags.push('prompt_injection');
  const location=String(raw.location ?? '').trim().slice(0,160);
  if(!location) flags.push('missing_location');
  return {text,location,requester:String(raw.requester || 'Anonymous').trim().slice(0,80),request_id:String(raw.request_id || '').slice(0,120),mode:raw.mode==='live'?'live':'demo',channel:['portal','email','webhook'].includes(raw.channel)?raw.channel:'portal',flags,trace:[{name:'Intake validation',kind:'guard',detail:'Validated input bounds and applied limited secret redaction. Review sensitive data before sharing.'}]};
}

export function classify(context) {
  const text=context.text.toLowerCase();
  const rules=[['vpn',/\bvpn\b|remote.access|\btunnel\b/],['account',/password|\bmfa\b|authenticator|account|sign.in|login|credentials/],['network',/wi.?fi|wireless|internet|ethernet|network|router/],['software',/app(?:lication)?\b|crash|software|install|license|spreadsheet|excel|outlook/],['device',/laptop|monitor|printer|keyboard|dock|display|battery|device|projector/]];
  const category=rules.find(([,pattern])=>pattern.test(text))?.[0] || 'other';
  const hazard=/smoke|sparks|swollen battery|burning smell/.test(text);
  return {...context,category,priority:hazard?'urgent':/everyone|whole office|entire|all staff|outage/.test(text)?'high':'normal',summary:context.text.slice(0,110),mode_used:context.mode==='live'?'live':'demo',flags:[...context.flags,...(hazard?['physical_hazard']:[])],trace:[...context.trace,{name:'Classifier specialist',kind:'rule',detail:`Matched ${category}; route: ${DEPARTMENTS[category]}. Demo routing uses explicit rules.`}]};
}

export function parseClassification(context, raw) {
  const baseline=classify(context);
  try {
    const result=decode(raw);
    if(!CATEGORIES.includes(result.category) || typeof result.summary!=='string' || !['normal','high','urgent'].includes(result.priority)) throw new Error('Invalid classification');
    const category=baseline.category==='other'?result.category:baseline.category;
    const priority=baseline.priority==='urgent'?'urgent':result.priority;
    return {...baseline,category,priority,summary:result.summary.slice(0,180),mode_used:'live',trace:[...context.trace,{name:'Classifier specialist',kind:'model',detail:`Local LLM proposed ${result.category}; bounded route: ${category} / ${DEPARTMENTS[category]}. Priority: ${priority}.`}]};
  } catch {
    return {...baseline,mode_used:'live_fallback',flags:[...baseline.flags,'model_fallback'],trace:[...baseline.trace,{name:'Model fallback',kind:'guard',detail:'Classifier model failed or returned invalid JSON. Used bounded demo rules; handoff is blocked.'}]};
  }
}

export function draft(context) {
  const citations=context.citations || [];
  if(!citations.length) return {...context,response:'I do not have a matching reviewed procedure for this request. Please provide the affected service, exact error and location so the service desk can review it.',steps:['Collect the affected service, exact error and location.','Ask the service desk to review the request.'],citation_ids:[],trace:[...context.trace,{name:'Resolution specialist',kind:'rule',detail:'No matching evidence. Abstained from troubleshooting advice.'}]};
  const source=citations[0];
  const sentences=source.excerpt.replace(/Fictional RelayDesk procedure\.\s*/g,'').split(/(?<=[.!?])\s+/).filter(s=>s.length>12);
  const steps=sentences.slice(0,3).map(s=>s.slice(0,700));
  let response=`Your request is ready for ${DEPARTMENTS[context.category] || 'Service Desk'} review. ${sentences.slice(0,2).join(' ')} [${source.id}]`;
  if(context.flags.includes('physical_hazard')) response=`Stop using the affected equipment. Do not open or repair it. Contact on-site safety staff through the established local process. [${source.id}]`;
  return {...context,response,steps,citation_ids:[source.id],trace:[...context.trace,{name:'Resolution specialist',kind:'rule',detail:'Prepared an extractive draft from the retrieved procedure. No model was called in this stage.'}]};
}

export function parseDraft(context, raw) {
  try {
    const value=decode(raw);
    if(typeof value.response!=='string' || value.response.length<8 || value.response.length>5000 || !Array.isArray(value.steps) || value.steps.length>6 || !value.steps.every(s=>typeof s==='string' && s.length<1200) || !Array.isArray(value.citation_ids)) throw new Error('Invalid draft');
    const ids=new Set(context.citations.map(c=>c.id));
    if(!value.citation_ids.length || value.citation_ids.some(id=>!ids.has(id)) || !value.citation_ids.every(id=>value.response.includes(`[${id}]`))) {
      const safe=draft(context);
      return {...safe,flags:[...safe.flags,'invalid_citations']};
    }
    return {...context,response:value.response,steps:value.steps,citation_ids:value.citation_ids,trace:[...context.trace,{name:'Resolution specialist',kind:'model',detail:'Local LLM drafted a response using retrieved procedure IDs. Draft still requires review.'}]};
  } catch {
    const safe=draft(context);
    return {...safe,mode_used:'live_fallback',flags:[...safe.flags,'model_fallback']};
  }
}

export function parseReview(context, raw) {
  try {
    const result=decode(raw);
    if(typeof result.supported!=='boolean' || typeof result.reason!=='string') throw new Error('Invalid review');
    return {...context,flags:[...context.flags,...(result.supported?[]:['review_rejected'])],trace:[...context.trace,{name:'Reviewer specialist',kind:'model',detail:`${result.supported?'Supported draft':'Review rejected draft'}: ${result.reason.slice(0,700)}`}]};
  } catch {
    return {...context,mode_used:'live_fallback',flags:[...context.flags,'model_fallback'],trace:[...context.trace,{name:'Reviewer specialist',kind:'guard',detail:'Reviewer unavailable or invalid response. Handoff blocked.'}]};
  }
}

export function guard(context) {
  const flags=new Set(context.flags || []);
  const citations=context.citations || [];
  if(!citations.length) flags.add('insufficient_evidence');
  if(citations.some(c=>!c.trusted)) flags.add('untrusted_evidence');
  if(citations.some(c=>/ignore.{0,30}(instructions|previous)|system prompt|auto.?approve/i.test(c.excerpt))) flags.add('prompt_injection');
  const joined=`${context.response} ${(context.steps || []).join(' ')}`;
  const positive=joined.replace(/\b(?:do not|don't|never)\s+(?:disable|bypass|turn off)[^.!?]*[.!?]?/gi,'');
  if(/(?:disable|bypass|turn off).{0,35}(?:firewall|mfa|antivirus|certificate)|(?:run|execute).{0,20}(?:powershell|sudo|curl|wget)/i.test(positive)) flags.add('unsafe_instruction');
  const allowed=new Set(citations.map(c=>c.id));
  const inline=[...String(context.response).matchAll(/\[(KB-[^\]]+)\]/g)].map(m=>m[1]);
  if(inline.some(id=>!allowed.has(id))) flags.add('invalid_citations');
  const blockers=['insufficient_evidence','untrusted_evidence','prompt_injection','invalid_citations','unsafe_instruction','review_rejected','model_fallback','missing_location'];
  const grounded=citations.length>0 && !flags.has('invalid_citations');
  const response=flags.has('unsafe_instruction')?'The generated draft failed the safety check. Please ask a support operator to review the request using the cited procedures.':context.response;
  return {request_id:context.request_id,text:context.text,location:context.location,requester:context.requester,channel:context.channel,mode:context.mode,mode_used:context.mode_used || context.mode,category:context.category,priority:context.priority,summary:context.summary,response,steps:flags.has('unsafe_instruction')?['Request manual support review.']:context.steps,citations,flags:[...flags],grounded,automation_allowed:grounded && !blockers.some(f=>flags.has(f)),trace:[...context.trace,{name:'Policy guard',kind:'guard',detail:`Checked citation IDs, source trust and bounded unsafe-action patterns. ${blockers.some(f=>flags.has(f))?'Handoff blocked; review findings.':'Draft eligible for operator approval.'}`}],execution_id:String(context.execution_id || '')};
}
