const API="/api/v1",TOKEN_KEY="terrasync_coordinator_token";
let user=null;
const q=s=>document.querySelector(s),qa=s=>[...document.querySelectorAll(s)];
function headers(){return{"Authorization":`Bearer ${localStorage.getItem(TOKEN_KEY)||""}`,"Content-Type":"application/json"}}
async function api(path,opts={}){const r=await fetch(API+path,{...opts,headers:{...headers(),...(opts.headers||{})}});if(!r.ok){const b=await r.json().catch(()=>({detail:r.statusText}));throw new Error(typeof b.detail==="string"?b.detail:JSON.stringify(b.detail))}return r.json()}
function initials(n){return(n||"CO").split(/\s+/).map(x=>x[0]).join("").slice(0,2).toUpperCase()}
function show(id){qa(".view").forEach(v=>v.classList.toggle("active",v.id===id));qa(".nav button").forEach(b=>b.classList.toggle("active",b.dataset.view===id));q("#title").textContent={home:"Dashboard",assignments:"Assignments",review:"AI Review Queue",templates:"Templates",clients:"Clients & Projects",assetschemas:"Asset Schemas",airules:"AI Rules",layouts:"Report Layouts",devices:"Field Devices",profile:"Profile"}[id]}
function metric(label,value){return`<article class="metric"><span>${label}</span><strong>${value}</strong></article>`}
function row(title,sub,right=""){return`<div class="row"><div><h4>${title}</h4><p>${sub}</p></div><div>${right}</div></div>`}
function riskClass(score){return score>=70?"high":score>=30?"med":"low"}
async function loadDashboard(){
  const [dashboard,queue]=await Promise.all([api("/dashboard/coordinator"),api("/review-queue")]);
  q("#metrics").innerHTML=metric("Assigned",dashboard.assigned)+metric("In field",dashboard.in_field)+metric("Awaiting review",dashboard.awaiting_review)+metric("Critical",dashboard.critical);
  q("#recent").innerHTML=(dashboard.recent_reports||[]).map(r=>row(r.report_no,r.summary||r.status,`<span class="risk ${riskClass(r.risk||0)}">${r.risk||0}/100</span>`)).join("")||"<p class='muted'>No reports yet.</p>";
  q("#fieldStatus").innerHTML=`<div class="mini-grid"><div class="mini-card"><span>Active technicians</span><strong>${dashboard.active_technicians}</strong></div><div class="mini-card"><span>Registered devices</span><strong>${dashboard.registered_devices}</strong></div><div class="mini-card"><span>Review queue</span><strong>${queue.length}</strong></div><div class="mini-card"><span>Critical queue</span><strong>${queue.filter(r=>(r.ai_risk_score||0)>=70).length}</strong></div></div>`;
  renderReview(queue);
}
function renderReview(queue){
  q("#reviewList").innerHTML=queue.map(r=>`<div class="row">
    <div><h4>${r.report_no} · ${r.report_type}</h4><p>${r.ai_summary||"AI screening complete."}</p><p>Inspector: ${r.inspector_name} · Status: ${r.status}</p></div>
    <div class="review-actions">
      <span class="risk ${riskClass(r.ai_risk_score||0)}">${r.ai_risk_score||0}/100</span>
      <a href="${API}/reports/${r.id}/pdf" target="_blank"><button>PDF</button></a>
      <button class="approve" data-review="${r.id}" data-decision="approve">Approve</button>
      <button class="return" data-review="${r.id}" data-decision="return">Return</button>
    </div>
  </div>`).join("")||"<p class='muted'>No reports currently require coordinator review.</p>";
}

let templateCatalog=[];
function renderTemplates(){
  const sector=q("#templateSector")?.value||"";
  const list=sector?templateCatalog.filter(t=>t.sector===sector):templateCatalog;
  q("#templateList").innerHTML=list.map(t=>`<div class="row"><div><h4>${t.name}</h4><p>${t.sector} · ${t.category} · v${t.version}</p><p>${t.description}</p></div><div><span class="status">${t.section_count} sections</span><br><small class="muted">${t.minimum_evidence} min. photos</small></div></div>`).join("")||"<p class='muted'>No templates.</p>";
}
async function loadTemplates(){
  templateCatalog=await api("/inspection-templates");
  q("#reportType").innerHTML=templateCatalog.map(t=>`<option value="${t.name}">${t.name} · ${t.sector}</option>`).join("");
  const sectors=[...new Set(templateCatalog.map(t=>t.sector))].sort();
  q("#templateSector").innerHTML='<option value="">All sectors</option>'+sectors.map(s=>`<option>${s}</option>`).join("");
  renderTemplates();
}

async function loadOperations(){
  const [assignments,devices,techs,sites]=await Promise.all([api("/assignments"),api("/devices"),api("/users/technicians"),api("/sites")]);
  q("#assignmentList").innerHTML=assignments.map(x=>row(x.work_order_no,`${x.report_type} · ${x.assigned_to||"Unassigned"} · ${x.status}`,`<span class="status">${x.priority}</span>`)).join("")||"<p class='muted'>No assignments.</p>";
  q("#deviceList").innerHTML=devices.map(x=>row(x.device_name,`${x.platform||"Device"} · last seen ${new Date(x.last_seen_at).toLocaleString()}`,`<span class="status">${x.active?"Active":"Revoked"}</span>`)).join("")||"<p class='muted'>No registered devices.</p>";
  const options=techs.map(x=>`<option value="${x.id}">${x.full_name} · ${x.staff_no||x.username}</option>`).join("");
  q("#technicianId").innerHTML=options;q("#otpTech").innerHTML=options;
  q("#siteId").innerHTML=sites.map(x=>`<option value="${x.id}">${x.code} · ${x.name}</option>`).join("");
}

let configState={clients:[],projects:[],assetSchemas:[],aiRules:[],layouts:[]};
function renderConfig(){
  q("#clientList").innerHTML=configState.clients.map(c=>row(c.name,`${c.code} · ${c.sector||"Multi-sector"}`,`<span class="status">${c.active?"Active":"Inactive"}</span>`)).join("")||"<p class='muted'>No clients.</p>";
  q("#projectList").innerHTML=configState.projects.map(p=>row(p.name,`${p.code} · ${p.sector||"Inherited sector"}`,`<span class="status">${p.status}</span>`)).join("")||"<p class='muted'>No projects.</p>";
  q("#projectClient").innerHTML=configState.clients.map(c=>`<option value="${c.id}">${c.name}</option>`).join("");
  q("#assetSchemaList").innerHTML=configState.assetSchemas.map(a=>row(a.asset_type,`${a.name} · ${a.fields.length} fields`,a.evidence_rules?.live_camera_required?'<span class="status">Camera required</span>':"")).join("")||"<p class='muted'>No asset schemas.</p>";
  q("#aiRuleList").innerHTML=configState.aiRules.map(a=>row(a.name,`${a.rules.length} rules · ${Object.entries(a.thresholds||{}).map(([k,v])=>`${k}: ${v}`).join(" · ")}`,`<span class="status">${a.active?"Active":"Inactive"}</span>`)).join("")||"<p class='muted'>No AI rule sets.</p>";
  q("#layoutList").innerHTML=configState.layouts.map(l=>row(l.name,`${l.compression_profile} · target ${l.layout?.target_pdf_mb||"—"} MB · ${l.layout?.photo_grid_columns||"—"} photo columns`,`<span class="status">${l.active?"Active":"Inactive"}</span>`)).join("")||"<p class='muted'>No report layouts.</p>";
}
async function loadConfiguration(){
  const [clients,projects,assetSchemas,aiRules,layouts]=await Promise.all([
    api("/configuration/clients"),
    api("/configuration/projects"),
    api("/configuration/asset-schemas"),
    api("/configuration/ai-rules"),
    api("/configuration/report-layouts")
  ]);
  configState={clients,projects,assetSchemas,aiRules,layouts};renderConfig();
}

async function boot(){
  user=await api("/auth/me");
  if(!["COORDINATOR","ADMIN"].includes(user.role))throw new Error("Coordinator access required");
  q("#name").textContent=user.full_name;q("#role").textContent="Coordinator";q("#avatar").textContent=initials(user.full_name);
  q("#profileData").innerHTML=row("Staff number",user.staff_no||"—")+row("Company",user.company||"—")+row("Email",user.email||"—")+row("Role","Coordinator — assignment & human review");
  await Promise.all([loadDashboard(),loadOperations(),loadTemplates(),loadConfiguration()]);
}
q("#loginForm").addEventListener("submit",async e=>{e.preventDefault();q("#loginMessage").textContent="Signing in…";try{const data=await api("/auth/staff-login",{method:"POST",headers:{"Content-Type":"application/json","Authorization":""},body:JSON.stringify({username:q("#username").value,password:q("#password").value})});localStorage.setItem(TOKEN_KEY,data.access_token);q("#login").classList.add("hidden");q("#shell").classList.remove("hidden");await boot()}catch(err){q("#loginMessage").textContent=err.message}});
q("#assignmentForm").addEventListener("submit",async e=>{e.preventDefault();q("#assignmentMessage").textContent="Publishing…";try{await api("/assignments",{method:"POST",body:JSON.stringify({work_order_no:q("#woNo").value.trim(),site_id:q("#siteId").value,report_type:q("#reportType").value,priority:q("#priority").value,technician_id:q("#technicianId").value})});q("#assignmentMessage").textContent="Assignment published to the technician.";q("#assignmentMessage").className="success wide";e.target.reset();await Promise.all([loadDashboard(),loadOperations()])}catch(err){q("#assignmentMessage").textContent=err.message;q("#assignmentMessage").className="error wide"}});
q("#otpForm").addEventListener("submit",async e=>{e.preventDefault();try{const data=await api("/auth/activation-codes",{method:"POST",body:JSON.stringify({user_id:q("#otpTech").value,expires_minutes:Number(q("#otpMinutes").value)})});q("#otpResult").innerHTML=`<div class="callout"><span class="muted">One-time activation code</span><h2>${data.code}</h2><p class="muted">Expires ${new Date(data.expires_at).toLocaleString()}. It can be used once only.</p></div>`}catch(err){q("#otpResult").innerHTML=`<p class="error">${err.message}</p>`}});
document.body.addEventListener("click",async e=>{const b=e.target.closest("[data-review]");if(!b)return;const decision=b.dataset.decision;let note=null;if(decision==="return"){note=prompt("What should the field technician correct or recapture?","Please review the flagged item and resubmit verified evidence.");if(note===null)return}if(decision==="approve"&&!confirm("Approve this inspection report?"))return;try{await api(`/reports/${b.dataset.review}/review`,{method:"POST",body:JSON.stringify({decision,note})});await Promise.all([loadDashboard(),loadOperations()])}catch(err){alert(err.message)}});
qa(".nav button").forEach(b=>b.addEventListener("click",()=>show(b.dataset.view)));
q("#logout").addEventListener("click",()=>{localStorage.removeItem(TOKEN_KEY);location.reload()});
if(localStorage.getItem(TOKEN_KEY)){q("#login").classList.add("hidden");q("#shell").classList.remove("hidden");boot().catch(()=>{localStorage.removeItem(TOKEN_KEY);location.reload()})}


q("#clientForm").addEventListener("submit",async e=>{e.preventDefault();await api("/configuration/clients",{method:"POST",body:JSON.stringify({name:q("#clientName").value,code:q("#clientCode").value,sector:q("#clientSector").value||null,branding:{}})});e.target.reset();await loadConfiguration()});
q("#projectForm").addEventListener("submit",async e=>{e.preventDefault();await api("/configuration/projects",{method:"POST",body:JSON.stringify({client_id:q("#projectClient").value,name:q("#projectName").value,code:q("#projectCode").value,sector:q("#projectSector").value||null,settings:{}})});e.target.reset();await loadConfiguration()});


let selectedTemplate=null;
let templateDraft={sections:[]};

function slugify(value){
  return value.toLowerCase().trim().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"");
}

function emptyField(){
  return {key:"field_"+Date.now(),label:"New field",type:"text",required:false,evidence:"none",options:[]};
}
function emptySection(){
  return {id:"section-"+Date.now(),title:"New section",evidence_min:0,fields:[emptyField()]};
}
function resetTemplateBuilder(){
  selectedTemplate=null;
  templateDraft={sections:[emptySection()]};
  q("#templateDbId").value="";
  q("#templateName").value="";
  q("#templateSlug").value="";
  q("#templateEditorSector").value="";
  q("#templateEditorCategory").value="inspection";
  q("#templateDescription").value="";
  q("#templateEditorTitle").textContent="New Template";
  q("#templateDraftStatus").textContent="Draft";
  renderSectionBuilder();
}
function renderSectionBuilder(){
  q("#sectionBuilder").innerHTML=templateDraft.sections.map((section,sIndex)=>`
    <div class="section-card" data-section-index="${sIndex}">
      <div class="section-header">
        <div><span class="drag-handle">☰</span> <strong>${section.title||"Untitled section"}</strong></div>
        <div class="small-actions">
          <button type="button" data-section-up="${sIndex}">↑</button>
          <button type="button" data-section-down="${sIndex}">↓</button>
          <button type="button" data-section-delete="${sIndex}" class="danger">Remove</button>
        </div>
      </div>
      <div class="form-grid">
        <label>Section title<input data-section-title="${sIndex}" value="${section.title||""}"></label>
        <label>Section ID<input data-section-id="${sIndex}" value="${section.id||""}"></label>
        <label>Minimum photos<input data-section-evidence="${sIndex}" type="number" min="0" value="${section.evidence_min||0}"></label>
      </div>
      <div class="panel-head"><h4>Fields</h4><button type="button" data-field-add="${sIndex}">Add field</button></div>
      <div class="section-fields">
        ${(section.fields||[]).map((field,fIndex)=>`
          <div class="field-row">
            <label>Label<input data-field-label="${sIndex}:${fIndex}" value="${field.label||""}"></label>
            <label>Key<input data-field-key="${sIndex}:${fIndex}" value="${field.key||""}"></label>
            <label>Type<select data-field-type="${sIndex}:${fIndex}">
              ${["text","textarea","number","select"].map(t=>`<option ${field.type===t?"selected":""}>${t}</option>`).join("")}
            </select></label>
            <label>Evidence<select data-field-evidence="${sIndex}:${fIndex}">
              ${["none","required","required_if_failed","optional"].map(v=>`<option value="${v}" ${field.evidence===v?"selected":""}>${v.replaceAll("_"," ")}</option>`).join("")}
            </select></label>
            <div class="small-actions">
              <label class="form-check"><input type="checkbox" data-field-required="${sIndex}:${fIndex}" ${field.required?"checked":""}> Required</label>
              <button type="button" data-field-delete="${sIndex}:${fIndex}" class="danger">×</button>
            </div>
          </div>`).join("")}
      </div>
    </div>`).join("");
}
function syncTemplateDraftFromDOM(){
  templateDraft.sections.forEach((section,sIndex)=>{
    section.title=q(`[data-section-title="${sIndex}"]`)?.value||section.title;
    section.id=q(`[data-section-id="${sIndex}"]`)?.value||slugify(section.title);
    section.evidence_min=Number(q(`[data-section-evidence="${sIndex}"]`)?.value||0);
    section.fields.forEach((field,fIndex)=>{
      const key=`${sIndex}:${fIndex}`;
      field.label=q(`[data-field-label="${key}"]`)?.value||field.label;
      field.key=q(`[data-field-key="${key}"]`)?.value||slugify(field.label).replaceAll("-","_");
      field.type=q(`[data-field-type="${key}"]`)?.value||field.type;
      field.evidence=q(`[data-field-evidence="${key}"]`)?.value||"none";
      field.required=!!q(`[data-field-required="${key}"]`)?.checked;
    });
  });
}
async function editTemplate(id){
  const data=await api(`/configuration/templates/${id}`);
  selectedTemplate=data;
  const def=data.active_version?.definition||{};
  templateDraft={sections:JSON.parse(JSON.stringify(def.sections||[]))};
  q("#templateDbId").value=id;
  q("#templateName").value=data.name||def.name||"";
  q("#templateSlug").value=data.slug||def.id||"";
  q("#templateEditorSector").value=data.sector||def.sector||"";
  q("#templateEditorCategory").value=data.category||def.category||"inspection";
  q("#templateDescription").value=data.description||def.description||"";
  q("#templateEditorTitle").textContent=data.name;
  q("#templateDraftStatus").textContent=data.active_version?.status||"Draft";
  renderSectionBuilder();
}
function renderTemplates(){
  const sector=q("#templateSector")?.value||"";
  const category=q("#templateCategory")?.value||"";
  let list=templateCatalog;
  if(sector)list=list.filter(t=>t.sector===sector);
  if(category)list=list.filter(t=>t.category===category);
  q("#templateList").innerHTML=list.map(t=>`
    <div class="row">
      <div><h4>${t.name}</h4><p>${t.sector} · ${t.category} · v${t.active_version||t.version||1}</p><p>${t.description||""}</p></div>
      <button data-edit-template="${t.id||t.database_id}">Edit</button>
    </div>`).join("")||"<p class='muted'>No templates.</p>";
}

function renderAssetFieldBuilder(fields=[]){
  q("#assetFieldBuilder").innerHTML=fields.map((f,i)=>`
    <div class="asset-field-row">
      <label>Label<input data-asset-field-label="${i}" value="${f.label||""}"></label>
      <label>Key<input data-asset-field-key="${i}" value="${f.key||""}"></label>
      <label>Type<select data-asset-field-type="${i}">
        ${["text","number","select","textarea"].map(t=>`<option ${f.type===t?"selected":""}>${t}</option>`).join("")}
      </select></label>
      <label class="form-check"><input data-asset-field-required="${i}" type="checkbox" ${f.required?"checked":""}> Required</label>
      <button type="button" data-asset-field-delete="${i}" class="danger">×</button>
    </div>`).join("");
}
function assetFieldsFromDOM(){
  return [...qa("[data-asset-field-label]")].map((el,i)=>({
    label:el.value,
    key:q(`[data-asset-field-key="${i}"]`).value,
    type:q(`[data-asset-field-type="${i}"]`).value,
    required:q(`[data-asset-field-required="${i}"]`).checked,
  }));
}
function resetAssetSchema(){
  q("#assetSchemaId").value="";
  q("#assetSchemaName").value="";
  q("#assetSchemaType").value="";
  q("#assetSchemaCamera").checked=true;
  renderAssetFieldBuilder([
    {key:"manufacturer",label:"Manufacturer",type:"text"},
    {key:"model",label:"Model",type:"text"},
    {key:"serial_number",label:"Serial number",type:"text"},
    {key:"quantity",label:"Quantity",type:"number"},
    {key:"condition",label:"Condition",type:"select"},
  ]);
}
function editAssetSchema(id){
  const row=configurationState.assetSchemas.find(x=>x.id===id);if(!row)return;
  q("#assetSchemaId").value=row.id;q("#assetSchemaName").value=row.name;q("#assetSchemaType").value=row.asset_type;
  q("#assetSchemaClient").value=row.client_id||"";q("#assetSchemaProject").value=row.project_id||"";
  q("#assetSchemaCamera").checked=!!row.evidence_rules?.live_camera_required;
  renderAssetFieldBuilder(row.fields||[]);
}

function resetAIRules(){
  q("#aiRuleId").value="";q("#aiRuleName").value="";q("#aiHighRisk").value=60;q("#aiEarthMax").value=5;q("#aiCriticalGrade").value="Grade D";
  q("#aiRequiredEvidence").checked=true;q("#aiGradeConsistency").checked=true;q("#aiAbnormalReadings").checked=true;
}
function editAIRules(id){
  const row=configurationState.aiRules.find(x=>x.id===id);if(!row)return;
  q("#aiRuleId").value=row.id;q("#aiRuleName").value=row.name;q("#aiHighRisk").value=row.thresholds?.high_risk_score??60;
  q("#aiEarthMax").value=row.thresholds?.earth_resistance_ohm_max??5;q("#aiCriticalGrade").value=row.thresholds?.critical_grade||"Grade D";
  q("#aiRequiredEvidence").checked=row.rules.some(r=>r.type==="required_evidence");
  q("#aiGradeConsistency").checked=row.rules.some(r=>r.type==="grade_comment_consistency");
  q("#aiAbnormalReadings").checked=row.rules.some(r=>r.type==="numeric_threshold");
}

function renderLayoutPreview(){
  const cols=Number(q("#layoutPhotoCols").value||2);
  const showCover=q("#layoutCover").checked;
  const showAI=q("#layoutAISummary").checked;
  q("#layoutPreview").innerHTML=`
    ${showCover?'<div class="preview-cover"><strong>CLIENT INSPECTION REPORT</strong><div>Site / Project / Report No.</div></div>':""}
    ${showAI?'<p><strong>AI Pre-Screen</strong><br>Completeness 96% · 1 abnormal reading · 0 critical defects</p>':""}
    <p><strong>Inspection Findings</strong><br>Dynamic sections expand only where evidence or defects require detail.</p>
    <div class="preview-grid" style="grid-template-columns:repeat(${cols},1fr)">
      ${Array.from({length:Math.max(2,cols*2)},(_,i)=>`<div class="preview-photo">Photo ${i+1}</div>`).join("")}
    </div>`;
}
function resetLayout(){
  q("#layoutId").value="";q("#layoutName").value="";q("#layoutCompression").value="compact";q("#layoutTargetMb").value=5;q("#layoutPhotoCols").value=2;
  ["layoutCover","layoutAISummary","layoutInspector","layoutCollapsePass","layoutExpandCritical"].forEach(id=>q("#"+id).checked=true);
  renderLayoutPreview();
}
function editLayout(id){
  const row=configurationState.layouts.find(x=>x.id===id);if(!row)return;
  q("#layoutId").value=row.id;q("#layoutName").value=row.name;q("#layoutCompression").value=row.compression_profile||"standard";
  q("#layoutTargetMb").value=row.layout?.target_pdf_mb||5;q("#layoutPhotoCols").value=row.layout?.photo_grid_columns||2;
  q("#layoutCover").checked=row.layout?.cover!==false;q("#layoutAISummary").checked=row.layout?.show_ai_summary!==false;
  q("#layoutInspector").checked=row.layout?.show_inspector_credentials!==false;q("#layoutCollapsePass").checked=!!row.layout?.collapse_passed_sections;
  q("#layoutExpandCritical").checked=!!row.layout?.expand_grade_c_d;renderLayoutPreview();
}

q("#newTemplateButton").addEventListener("click",resetTemplateBuilder);
q("#addSectionButton").addEventListener("click",()=>{syncTemplateDraftFromDOM();templateDraft.sections.push(emptySection());renderSectionBuilder()});
q("#templateSector").addEventListener("change",renderTemplates);
q("#templateCategory").addEventListener("change",renderTemplates);
q("#templateName").addEventListener("input",()=>{if(!q("#templateDbId").value)q("#templateSlug").value=slugify(q("#templateName").value)});

q("#sectionBuilder").addEventListener("click",e=>{
  syncTemplateDraftFromDOM();
  const add=e.target.closest("[data-field-add]");if(add){templateDraft.sections[+add.dataset.fieldAdd].fields.push(emptyField());renderSectionBuilder();return}
  const del=e.target.closest("[data-section-delete]");if(del){templateDraft.sections.splice(+del.dataset.sectionDelete,1);renderSectionBuilder();return}
  const fdel=e.target.closest("[data-field-delete]");if(fdel){const [s,f]=fdel.dataset.fieldDelete.split(":").map(Number);templateDraft.sections[s].fields.splice(f,1);renderSectionBuilder();return}
  const up=e.target.closest("[data-section-up]");if(up){const i=+up.dataset.sectionUp;if(i>0)[templateDraft.sections[i-1],templateDraft.sections[i]]=[templateDraft.sections[i],templateDraft.sections[i-1]];renderSectionBuilder();return}
  const down=e.target.closest("[data-section-down]");if(down){const i=+down.dataset.sectionDown;if(i<templateDraft.sections.length-1)[templateDraft.sections[i+1],templateDraft.sections[i]]=[templateDraft.sections[i],templateDraft.sections[i+1]];renderSectionBuilder()}
});
q("#templateList").addEventListener("click",e=>{const b=e.target.closest("[data-edit-template]");if(b)editTemplate(b.dataset.editTemplate)});

q("#templateBuilderForm").addEventListener("submit",async e=>{
  e.preventDefault();syncTemplateDraftFromDOM();
  const payload={name:q("#templateName").value,slug:q("#templateSlug").value,sector:q("#templateEditorSector").value,category:q("#templateEditorCategory").value,description:q("#templateDescription").value||null,client_id:null,definition:{id:q("#templateSlug").value,name:q("#templateName").value,sector:q("#templateEditorSector").value,category:q("#templateEditorCategory").value,version:1,description:q("#templateDescription").value||"",asset_types:[],sections:templateDraft.sections}};
  const id=q("#templateDbId").value;
  await api(id?`/configuration/templates/${id}`:"/configuration/templates",{method:id?"PUT":"POST",body:JSON.stringify(payload)});
  await loadTemplates();resetTemplateBuilder();
});
q("#publishTemplateButton").addEventListener("click",async()=>{
  const id=q("#templateDbId").value;if(!id)return alert("Save the template first.");
  const data=await api(`/configuration/templates/${id}`);
  const version=data.active_version;if(!version)return;
  await api(`/configuration/templates/${id}/versions/${version.id}/publish`,{method:"POST",body:"{}"});
  await loadTemplates();await editTemplate(id);
});
q("#deleteTemplateButton").addEventListener("click",async()=>{
  const id=q("#templateDbId").value;if(!id)return;
  if(!confirm("Delete this template and its versions?"))return;
  await api(`/configuration/templates/${id}`,{method:"DELETE"});await loadTemplates();resetTemplateBuilder();
});

q("#newAssetSchemaButton").addEventListener("click",resetAssetSchema);
q("#assetSchemaList").addEventListener("click",e=>{const b=e.target.closest("[data-edit-asset-schema]");if(b)editAssetSchema(b.dataset.editAssetSchema)});
q("#addAssetFieldButton").addEventListener("click",()=>{const fields=assetFieldsFromDOM();fields.push({key:"new_field",label:"New field",type:"text",required:false});renderAssetFieldBuilder(fields)});
q("#assetFieldBuilder").addEventListener("click",e=>{const b=e.target.closest("[data-asset-field-delete]");if(!b)return;const fields=assetFieldsFromDOM();fields.splice(+b.dataset.assetFieldDelete,1);renderAssetFieldBuilder(fields)});
q("#assetSchemaForm").addEventListener("submit",async e=>{
  e.preventDefault();const id=q("#assetSchemaId").value;
  const payload={client_id:q("#assetSchemaClient").value||null,project_id:q("#assetSchemaProject").value||null,name:q("#assetSchemaName").value,asset_type:q("#assetSchemaType").value,fields:assetFieldsFromDOM(),evidence_rules:{live_camera_required:q("#assetSchemaCamera").checked}};
  await api(id?`/configuration/asset-schemas/${id}`:"/configuration/asset-schemas",{method:id?"PUT":"POST",body:JSON.stringify(payload)});await loadConfiguration();resetAssetSchema();
});
q("#deleteAssetSchemaButton").addEventListener("click",async()=>{const id=q("#assetSchemaId").value;if(!id)return;if(confirm("Delete asset schema?")){await api(`/configuration/asset-schemas/${id}`,{method:"DELETE"});await loadConfiguration();resetAssetSchema()}});

q("#newAIRuleButton").addEventListener("click",resetAIRules);
q("#aiRuleList").addEventListener("click",e=>{const b=e.target.closest("[data-edit-ai-rule]");if(b)editAIRules(b.dataset.editAiRule)});
q("#aiRuleForm").addEventListener("submit",async e=>{
  e.preventDefault();const id=q("#aiRuleId").value;const rules=[];
  if(q("#aiRequiredEvidence").checked)rules.push({type:"required_evidence",severity:"high"});
  if(q("#aiGradeConsistency").checked)rules.push({type:"grade_comment_consistency",severity:"medium"});
  if(q("#aiAbnormalReadings").checked)rules.push({type:"numeric_threshold",field:"earth_resistance_ohm",operator:">",value:Number(q("#aiEarthMax").value),severity:"high"});
  const payload={client_id:null,project_id:null,template_id:null,name:q("#aiRuleName").value,rules,thresholds:{high_risk_score:Number(q("#aiHighRisk").value),earth_resistance_ohm_max:Number(q("#aiEarthMax").value),critical_grade:q("#aiCriticalGrade").value}};
  await api(id?`/configuration/ai-rules/${id}`:"/configuration/ai-rules",{method:id?"PUT":"POST",body:JSON.stringify(payload)});await loadConfiguration();resetAIRules();
});
q("#deleteAIRuleButton").addEventListener("click",async()=>{const id=q("#aiRuleId").value;if(!id)return;if(confirm("Delete AI rule set?")){await api(`/configuration/ai-rules/${id}`,{method:"DELETE"});await loadConfiguration();resetAIRules()}});

q("#newLayoutButton").addEventListener("click",resetLayout);
q("#layoutList").addEventListener("click",e=>{const b=e.target.closest("[data-edit-layout]");if(b)editLayout(b.dataset.editLayout)});
["layoutCompression","layoutTargetMb","layoutPhotoCols","layoutCover","layoutAISummary","layoutInspector","layoutCollapsePass","layoutExpandCritical"].forEach(id=>q("#"+id).addEventListener("change",renderLayoutPreview));
q("#layoutForm").addEventListener("submit",async e=>{
  e.preventDefault();const id=q("#layoutId").value;
  const payload={client_id:null,project_id:null,template_id:null,name:q("#layoutName").value,compression_profile:q("#layoutCompression").value,layout:{target_pdf_mb:Number(q("#layoutTargetMb").value),photo_grid_columns:Number(q("#layoutPhotoCols").value),cover:q("#layoutCover").checked,show_ai_summary:q("#layoutAISummary").checked,show_inspector_credentials:q("#layoutInspector").checked,collapse_passed_sections:q("#layoutCollapsePass").checked,expand_grade_c_d:q("#layoutExpandCritical").checked}};
  await api(id?`/configuration/report-layouts/${id}`:"/configuration/report-layouts",{method:id?"PUT":"POST",body:JSON.stringify(payload)});await loadConfiguration();resetLayout();
});
q("#deleteLayoutButton").addEventListener("click",async()=>{const id=q("#layoutId").value;if(!id)return;if(confirm("Delete report layout?")){await api(`/configuration/report-layouts/${id}`,{method:"DELETE"});await loadConfiguration();resetLayout()}});

const oldRenderConfiguration=renderConfiguration;
renderConfiguration=function(){
  oldRenderConfiguration();
  q("#assetSchemaClient").innerHTML='<option value="">Global</option>'+configurationState.clients.map(c=>`<option value="${c.id}">${c.name}</option>`).join("");
  q("#assetSchemaProject").innerHTML='<option value="">All projects</option>'+configurationState.projects.map(p=>`<option value="${p.id}">${p.name}</option>`).join("");
  q("#assetSchemaList").innerHTML=configurationState.assetSchemas.map(a=>`<div class="row"><div><h4>${a.asset_type}</h4><p>${a.name} · ${(a.fields||[]).length} fields</p></div><button data-edit-asset-schema="${a.id}">Edit</button></div>`).join("")||"<p class='muted'>No asset schemas.</p>";
  q("#aiRuleList").innerHTML=configurationState.aiRules.map(a=>`<div class="row"><div><h4>${a.name}</h4><p>${(a.rules||[]).length} rules · high risk ${a.thresholds?.high_risk_score??"—"}</p></div><button data-edit-ai-rule="${a.id}">Edit</button></div>`).join("")||"<p class='muted'>No AI rule sets.</p>";
  q("#layoutList").innerHTML=configurationState.layouts.map(l=>`<div class="row"><div><h4>${l.name}</h4><p>${l.compression_profile} · ${l.layout?.target_pdf_mb||"—"} MB target</p></div><button data-edit-layout="${l.id}">Edit</button></div>`).join("")||"<p class='muted'>No layouts.</p>";
};

resetTemplateBuilder();resetAssetSchema();resetAIRules();resetLayout();
