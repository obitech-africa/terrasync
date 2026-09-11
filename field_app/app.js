const API="/api/v1";
const TOKEN_KEY="terrasync_device_token";
const PROFILE_KEY="terrasync_profile";
const TASKS_KEY="terrasync_assignments";
const DEVICE_KEY="terrasync_device_key";
const ASSET_CACHE_KEY="terrasync_asset_cache_v2";
const DB_NAME="terrasync-field-v2";
const DB_VERSION=1;

let profile=null;
let activeAssignment=null;
let cameraStream=null;
let assetCameraStream=null;
let capturedEvidence=[];
let activeTemplate=null;
let capturedAssetEvidence=null;

const q=s=>document.querySelector(s);
const qa=s=>[...document.querySelectorAll(s)];

function openDB(){
  return new Promise((resolve,reject)=>{
    const request=indexedDB.open(DB_NAME,DB_VERSION);
    request.onupgradeneeded=()=>{
      const db=request.result;
      if(!db.objectStoreNames.contains("outbox"))db.createObjectStore("outbox",{keyPath:"id"});
      if(!db.objectStoreNames.contains("drafts"))db.createObjectStore("drafts",{keyPath:"work_order_id"});
    };
    request.onsuccess=()=>resolve(request.result);
    request.onerror=()=>reject(request.error);
  });
}
async function dbPut(store,value){const db=await openDB();return new Promise((resolve,reject)=>{const tx=db.transaction(store,"readwrite");tx.objectStore(store).put(value);tx.oncomplete=()=>resolve(value);tx.onerror=()=>reject(tx.error)})}
async function dbDelete(store,key){const db=await openDB();return new Promise((resolve,reject)=>{const tx=db.transaction(store,"readwrite");tx.objectStore(store).delete(key);tx.oncomplete=()=>resolve();tx.onerror=()=>reject(tx.error)})}
async function dbGet(store,key){const db=await openDB();return new Promise((resolve,reject)=>{const r=db.transaction(store).objectStore(store).get(key);r.onsuccess=()=>resolve(r.result||null);r.onerror=()=>reject(r.error)})}
async function dbAll(store){const db=await openDB();return new Promise((resolve,reject)=>{const r=db.transaction(store).objectStore(store).getAll();r.onsuccess=()=>resolve(r.result||[]);r.onerror=()=>reject(r.error)})}

function deviceKey(){let k=localStorage.getItem(DEVICE_KEY);if(!k){k=crypto.randomUUID();localStorage.setItem(DEVICE_KEY,k)}return k}
function authHeaders(){const token=localStorage.getItem(TOKEN_KEY);return token?{"Authorization":`Bearer ${token}`}:{}} 
function initials(name){return(name||"FT").split(/\s+/).map(x=>x[0]).join("").slice(0,2).toUpperCase()}
function uid(){return crypto.randomUUID?crypto.randomUUID():`${Date.now()}-${Math.random()}`}
function cachedTasks(){return JSON.parse(localStorage.getItem(TASKS_KEY)||"[]")}
function assetCache(){return JSON.parse(localStorage.getItem(ASSET_CACHE_KEY)||"{}")}
function saveAssetCache(cache){localStorage.setItem(ASSET_CACHE_KEY,JSON.stringify(cache))}
const TEMPLATE_CACHE_KEY="terrasync_templates_v3";

function templateCache(){return JSON.parse(localStorage.getItem(TEMPLATE_CACHE_KEY)||"{}")}
function saveTemplateCache(cache){localStorage.setItem(TEMPLATE_CACHE_KEY,JSON.stringify(cache))}

async function resolveTemplate(reportType){
  const cache=templateCache();
  const summaries=cache.__summaries||[];
  let summary=summaries.find(t=>t.name===reportType||t.id===reportType);
  if(!summary&&navigator.onLine){
    const fresh=await api("/inspection-templates");
    cache.__summaries=fresh;
    localStorage.setItem(TEMPLATE_CACHE_KEY,JSON.stringify(cache));
    summary=fresh.find(t=>t.name===reportType||t.id===reportType);
  }
  if(!summary){
    summary=(cache.__summaries||[]).find(t=>reportType?.toLowerCase().includes(t.name.toLowerCase().replace(" inspection","")));
  }
  if(!summary)return null;
  if(cache[summary.id])return cache[summary.id];
  if(!navigator.onLine)return null;
  const definition=await api(`/inspection-templates/${summary.id}`);
  cache[summary.id]=definition;
  saveTemplateCache(cache);
  return definition;
}

function fieldId(key){return `tpl_${key.replace(/[^a-zA-Z0-9_-]/g,"_")}`}

function renderTemplate(template){
  activeTemplate=template;
  q("#inspectionTemplate").value=template?`${template.name} · v${template.version}`:activeAssignment.report_type;
  if(!template){
    q("#templateSummary").textContent="Template definition is not cached on this device. Connect once to download it.";
    q("#templateSections").innerHTML="";
    q("#evidenceSection").innerHTML='<option value="general">General evidence</option>';
    return;
  }
  const minimum=template.sections.reduce((sum,s)=>sum+(s.evidence_min||0),0);
  q("#templateSummary").innerHTML=`<strong>${template.sector} · ${template.category}</strong><br>${template.description}<br><span class="muted">${template.sections.length} sections · minimum ${minimum} evidence photo${minimum===1?"":"s"}</span>`;
  q("#evidenceSection").innerHTML=template.sections.map(s=>`<option value="${s.id}">${s.title}</option>`).join("");
  q("#templateSections").innerHTML=template.sections.map(section=>`
    <section class="template-section" data-section="${section.id}">
      <div class="template-section-head">
        <div><h4>${section.title}</h4><span class="muted">${section.fields.length} fields</span></div>
        <span class="pill">${section.evidence_min||0} photo min.</span>
      </div>
      <div class="template-fields">
        ${section.fields.map(item=>{
          const required=item.required?'<span class="req">*</span>':"";
          const evidence=item.evidence&&item.evidence!=="none"?`<span class="evidence-rule"> · evidence: ${item.evidence.replaceAll("_"," ")}</span>`:"";
          const id=fieldId(item.key);
          let control="";
          if(item.type==="select"){
            control=`<select id="${id}" data-template-key="${item.key}" ${item.required?"required":""}><option value="">Select…</option>${(item.options||[]).map(o=>`<option>${o}</option>`).join("")}</select>`;
          }else if(item.type==="textarea"){
            control=`<textarea id="${id}" data-template-key="${item.key}" rows="3" ${item.required?"required":""}></textarea>`;
          }else{
            control=`<input id="${id}" data-template-key="${item.key}" type="${item.type==="number"?"number":"text"}" ${item.type==="number"?'step="any"':""} ${item.required?"required":""}>`;
          }
          return `<label class="${item.type==="textarea"?"full":""}">${item.label}${item.unit?` (${item.unit})`:""} ${required}${evidence}${control}</label>`;
        }).join("")}
      </div>
    </section>`).join("");
  renderEvidenceGallery();
}

function templateAnswers(){
  const result={};
  qa("[data-template-key]").forEach(el=>{result[el.dataset.templateKey]=el.value===""?null:el.value});
  return result;
}
function restoreTemplateAnswers(answers={}){
  qa("[data-template-key]").forEach(el=>{const value=answers[el.dataset.templateKey];if(value!==undefined&&value!==null)el.value=value});
}
function renderEvidenceGallery(){
  const evidence=Array.isArray(capturedEvidence)?capturedEvidence:[];
  q("#evidenceGallery").innerHTML=evidence.map((item,index)=>`<div class="evidence-thumb"><img src="data:${item.mime_type};base64,${item.content_base64}" alt="Inspection evidence ${index+1}"><small>${item.section_title||item.section_id||"Evidence"} · ${index+1}</small></div>`).join("");
  if(!activeTemplate){q("#evidenceProgress").textContent=`${evidence.length} photos captured`;return}
  const parts=activeTemplate.sections.map(section=>{
    const count=evidence.filter(item=>item.section_id===section.id).length;
    return `${section.title}: ${count}/${section.evidence_min||0}`;
  });
  q("#evidenceProgress").textContent=parts.join(" · ");
  const minimum=activeTemplate.sections.reduce((sum,s)=>sum+(s.evidence_min||0),0);
  q("#evidenceStatus").textContent=`${evidence.length}/${minimum}`;
  q("#evidenceStatus").className=`state ${evidence.length>=minimum?"good":"bad"}`;
}

function localTemplateValidation(){
  if(!activeTemplate)return {valid:false,message:"Inspection template is unavailable."};
  const answers=templateAnswers();
  const missing=[];
  const missingEvidence=[];
  for(const section of activeTemplate.sections){
    for(const item of section.fields){
      if(item.required&&(answers[item.key]===null||answers[item.key]===""))missing.push(item.label);
    }
    const count=capturedEvidence.filter(photo=>photo.section_id===section.id).length;
    if(count<(section.evidence_min||0))missingEvidence.push(`${section.title} (${count}/${section.evidence_min})`);
  }
  if(missing.length)return {valid:false,message:`Complete required fields: ${missing.slice(0,4).join(", ")}${missing.length>4?"…":""}`};
  if(missingEvidence.length)return {valid:false,message:`Capture required section evidence: ${missingEvidence.slice(0,3).join("; ")}${missingEvidence.length>3?"…":""}`};
  return {valid:true,message:"Ready"};
}

async function api(path,opts={}){
  const response=await fetch(API+path,{...opts,headers:{"Content-Type":"application/json",...authHeaders(),...(opts.headers||{})}});
  if(!response.ok){const body=await response.json().catch(()=>({detail:response.statusText}));throw new Error(typeof body.detail==="string"?body.detail:JSON.stringify(body.detail))}
  return response.json();
}
function network(){
  const online=navigator.onLine;
  q("#network").textContent=online?"● Online":"● Offline";
  q("#network").className=`network ${online?"online":"offline"}`;
  q("#syncStatus").textContent=online?"Online — ready to synchronize queued field work.":"Offline — work stays on this device until connectivity returns.";
}
function show(id){
  qa(".view").forEach(v=>v.classList.toggle("active",v.id===id));
  qa(".rail nav button,.bottom-nav button").forEach(b=>b.classList.toggle("active",b.dataset.view===id));
  q("#title").textContent={home:"Dashboard",tasks:"Assignments",inventory:"Equipment inventory",inspection:"Inspection",sync:"Synchronization",profile:"Profile"}[id]||"TerraSync";
  if(id!=="inspection")stopCamera();
  if(id!=="inventory")stopAssetCamera();
}
function renderProfile(){
  if(!profile)return;
  const first=profile.full_name.split(" ")[0];
  q("#userName").textContent=profile.full_name;
  q("#userRole").textContent=profile.role.replaceAll("_"," ");
  q("#avatar").textContent=initials(profile.full_name);
  q("#headerInitials").textContent=initials(profile.full_name);
  q("#profileAvatar").textContent=initials(profile.full_name);
  q("#profileName").textContent=profile.full_name;
  q("#profileStaff").textContent=`${profile.staff_no||"—"} · ${profile.company||"—"}`;
  q("#welcome").textContent=`Good field work, ${first}.`;
  q("#profileDetails").innerHTML=[
    ["Staff / inspector no.",profile.staff_no||"—"],
    ["Company",profile.company||"—"],
    ["Phone",profile.phone||"—"],
    ["Email",profile.email||"—"]
  ].map(([k,v])=>`<div><span>${k}</span><strong>${v}</strong></div>`).join("");
  q("#credentials").innerHTML=(profile.certifications||[]).map(c=>`<div class="credential"><span>${c.id||"Credential"}</span><strong>${c.name}</strong><span>Valid to ${c.expires||"—"}</span></div>`).join("")||"<p class='muted'>No certifications recorded.</p>";
}
function taskRow(task){
  const due=task.due_at?new Date(task.due_at).toLocaleDateString():"No due date";
  const action=["Completed","Submitted","Closed"].includes(task.status)?"View":task.status==="Assigned"?"Start":"Continue";
  return `<div class="row">
    <div><h4>${task.work_order_no}</h4><p>${task.site_name||task.site_id} · ${task.report_type}</p><p>Due ${due} · <span class="priority-${String(task.priority).toLowerCase()}">${task.priority}</span></p></div>
    <div><span class="state ${task.status==="Assigned"?"warn":task.status==="In Progress"?"good":"good"}">${task.status}</span> <button data-task="${task.id}">${action}</button></div>
  </div>`;
}
async function renderTasks(data={}){
  const tasks=data.assignments||cachedTasks();
  const html=tasks.map(taskRow).join("")||"<p class='muted'>No assignments downloaded to this device.</p>";
  q("#taskList").innerHTML=html;
  q("#homeTasks").innerHTML=tasks.slice(0,4).map(taskRow).join("")||html;
  q("#taskCount").textContent=`${tasks.length} task${tasks.length===1?"":"s"}`;
  q("#assigned").textContent=data.assigned??tasks.filter(x=>x.status==="Assigned").length;
  q("#progress").textContent=data.in_progress??tasks.filter(x=>x.status==="In Progress").length;
  q("#completed").textContent=data.completed??tasks.filter(x=>["Completed","Submitted","Closed"].includes(x.status)).length;
  q("#inventoryAssignment").innerHTML=tasks.map(x=>`<option value="${x.id}">${x.work_order_no} · ${x.site_name||x.site_id}</option>`).join("");
  const queue=await dbAll("outbox");
  q("#pending").textContent=queue.length;
  renderQueue(queue);
}
function renderQueue(queue){
  const assets=queue.filter(x=>x.kind==="asset").length;
  const reports=queue.filter(x=>x.kind==="report").length;
  q("#queueBreakdown").innerHTML=`<div class="sync-item"><span>Asset records</span><strong>${assets}</strong></div><div class="sync-item"><span>Inspection reports</span><strong>${reports}</strong></div>`;
  q("#homeSync").innerHTML=`<div class="sync-item"><span>Network</span><strong>${navigator.onLine?"Online":"Offline"}</strong></div><div class="sync-item"><span>Queued changes</span><strong>${queue.length}</strong></div><div class="sync-item"><span>Last confirmed sync</span><strong>${localStorage.getItem("terrasync_last_sync")||"Never"}</strong></div>`;
}
function stopCamera(){if(cameraStream){cameraStream.getTracks().forEach(t=>t.stop());cameraStream=null}}
function stopAssetCamera(){if(assetCameraStream){assetCameraStream.getTracks().forEach(t=>t.stop());assetCameraStream=null}}
async function openCamera(video,kind){
  if(!navigator.mediaDevices?.getUserMedia)throw new Error("Live camera capture requires a supported browser over HTTPS or localhost.");
  if(kind==="inspection")stopCamera();else stopAssetCamera();
  const stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:"environment"},width:{ideal:1920},height:{ideal:1080}},audio:false});
  if(kind==="inspection")cameraStream=stream;else assetCameraStream=stream;
  video.srcObject=stream;video.hidden=false;await video.play();
}
function geolocate(){return new Promise((resolve,reject)=>{if(!navigator.geolocation)return reject(new Error("Phone location is unavailable."));navigator.geolocation.getCurrentPosition(resolve,e=>reject(new Error(e.message||"Location permission is required.")),{enableHighAccuracy:true,timeout:15000,maximumAge:0})})}
function toBlob(canvas,quality=.56){return new Promise((resolve,reject)=>canvas.toBlob(blob=>blob?resolve(blob):reject(new Error("Could not compress evidence image.")),"image/jpeg",quality))}
function toBase64(blob){return new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(String(r.result).split(",")[1]);r.onerror=()=>reject(r.error);r.readAsDataURL(blob)})}
async function sha256(blob){const h=await crypto.subtle.digest("SHA-256",await blob.arrayBuffer());return [...new Uint8Array(h)].map(b=>b.toString(16).padStart(2,"0")).join("")}
function watermark(ctx,w,h,time,lat,lon,accuracy){
  const scale=Math.max(1,w/1200),pad=14*scale,line=27*scale,font=18*scale;
  const rows=[new Date(time).toLocaleString(),`${lat.toFixed(6)}, ${lon.toFixed(6)}  ±${Math.round(accuracy)} m`];
  const box=pad*2+rows.length*line;
  ctx.save();ctx.fillStyle="rgba(0,0,0,.62)";ctx.fillRect(0,h-box,w,box);ctx.fillStyle="#fff";ctx.font=`600 ${font}px system-ui`;ctx.textBaseline="top";
  rows.forEach((text,i)=>ctx.fillText(text,pad,h-box+pad+i*line,w-pad*2));ctx.restore();
}
async function makeEvidence(video,canvas,workOrderNo){
  const position=await geolocate();
  const capturedAt=new Date().toISOString();
  const maxWidth=1280,scale=Math.min(1,maxWidth/video.videoWidth);
  canvas.width=Math.max(1,Math.round(video.videoWidth*scale));canvas.height=Math.max(1,Math.round(video.videoHeight*scale));
  const ctx=canvas.getContext("2d");ctx.drawImage(video,0,0,canvas.width,canvas.height);
  watermark(ctx,canvas.width,canvas.height,capturedAt,position.coords.latitude,position.coords.longitude,position.coords.accuracy);
  const blob=await toBlob(canvas,.55);
  const evidenceId=uid();
  return {
    kind:"photo",source:"live_camera",name:`terrasync-${evidenceId}.jpg`,evidence_id:evidenceId,
    sha256:await sha256(blob),mime_type:"image/jpeg",content_base64:await toBase64(blob),
    captured_at:capturedAt,latitude:position.coords.latitude,longitude:position.coords.longitude,
    accuracy_m:position.coords.accuracy,device_id:deviceKey(),inspector_name:profile.full_name,
    work_order_no:workOrderNo
  };
}
async function loadAssets(workOrderId){
  if(!workOrderId){q("#assetList").innerHTML="<p class='muted'>Select an assignment.</p>";return}
  let cache=assetCache(),assets=cache[workOrderId]||[];
  if(navigator.onLine){
    try{assets=await api(`/assets?work_order_id=${encodeURIComponent(workOrderId)}`);cache[workOrderId]=assets;saveAssetCache(cache)}catch(e){}
  }
  const queued=(await dbAll("outbox")).filter(x=>x.kind==="asset"&&x.payload.work_order_id===workOrderId).map(x=>({...x.payload,id:x.id,queued:true}));
  const all=[...queued,...assets.filter(a=>!queued.some(qi=>qi.client_id===a.client_id))];
  q("#assetList").innerHTML=all.map(a=>`<article class="asset-card">
    <div class="panel-head"><div><h4>${a.asset_type}</h4><p>${a.manufacturer||"—"} · ${a.model||"—"}</p></div><span class="state ${a.condition==="Critical"?"bad":a.condition==="Poor"?"warn":"good"}">${a.condition}</span></div>
    <div class="asset-meta"><div><span>Serial</span><br><strong>${a.serial_number||"—"}</strong></div><div><span>Quantity</span><br><strong>${a.quantity||1}</strong></div><div><span>Height</span><br><strong>${a.height_or_elevation||"—"}</strong></div><div><span>Position</span><br><strong>${a.position||"—"}</strong></div></div>
    <p><span class="pill">${a.source==="client_supplied"?"Client supplied":a.queued?"Queued on device":"Created on-site"}</span></p>
    ${a.evidence?.[0]?.content_base64?`<img src="data:${a.evidence[0].mime_type};base64,${a.evidence[0].content_base64}" alt="${a.asset_type} evidence">`:""}
  </article>`).join("")||"<p class='muted'>No inventory for this assignment. Create assets on-site when required.</p>";
}
async function startAssignment(id){
  const task=cachedTasks().find(x=>x.id===id);if(!task)return;
  activeAssignment={...task};
  if(navigator.onLine&&task.status==="Assigned"){
    try{const updated=await api(`/assignments/${id}/start`,{method:"POST"});activeAssignment={...task,...updated};const tasks=cachedTasks().map(x=>x.id===id?{...x,...updated}:x);localStorage.setItem(TASKS_KEY,JSON.stringify(tasks));await renderTasks({assignments:tasks})}catch(e){}
  }else if(task.status==="Assigned"){
    activeAssignment.status="In Progress";const tasks=cachedTasks().map(x=>x.id===id?{...x,status:"In Progress"}:x);localStorage.setItem(TASKS_KEY,JSON.stringify(tasks));await renderTasks({assignments:tasks});
  }
  localStorage.setItem("terrasync_active_assignment",id);
  q("#inspectionEmpty").classList.add("hidden");q("#inspectionForm").classList.remove("hidden");
  q("#inspectionTitle").textContent=activeAssignment.work_order_no;
  q("#inspectionSite").textContent=`${activeAssignment.site_name||activeAssignment.site_id} · ${activeAssignment.site_code||""}`;
  q("#inspectionPriority").textContent=activeAssignment.priority;
  q("#inspectionTemplate").value=activeAssignment.report_type;
  q("#inventoryAssignment").value=id;
  await loadAssets(id);
  activeTemplate=await resolveTemplate(activeAssignment.report_type);
  renderTemplate(activeTemplate);
  const draft=await dbGet("drafts",id);if(draft)loadDraft(draft);
  show("inspection");
}
function loadDraft(d){
  capturedEvidence=Array.isArray(d.evidence)?d.evidence:(d.evidence?[d.evidence]:[]);
  restoreTemplateAnswers(d.template_answers||{});
  renderEvidenceGallery();
  if(capturedEvidence.length){
    const latest=capturedEvidence[capturedEvidence.length-1];
    const img=q("#capturedPreview");img.src=`data:${latest.mime_type};base64,${latest.content_base64}`;img.hidden=false;
    q("#submitInspectionButton").disabled=false;
    q("#captureMetadata").textContent=`Draft restored · ${capturedEvidence.length} evidence photo${capturedEvidence.length===1?"":"s"}`;
  }
}
function draftData(){
  return {
    work_order_id:activeAssignment.id,
    template_id:activeTemplate?.id||null,
    template_version:activeTemplate?.version||null,
    template_answers:templateAnswers(),
    evidence:capturedEvidence,
    updated_at:new Date().toISOString()
  };
}
function showInspectionEvidence(e){
  const section=activeTemplate?.sections.find(s=>s.id===q("#evidenceSection").value);
  e.section_id=section?.id||"general";
  e.section_title=section?.title||"General evidence";
  capturedEvidence.push(e);
  const img=q("#capturedPreview");img.src=`data:${e.mime_type};base64,${e.content_base64}`;img.hidden=false;
  q("#cameraPreview").hidden=true;q("#retakeButton").hidden=false;q("#submitInspectionButton").disabled=false;
  q("#captureMetadata").textContent=`${new Date(e.captured_at).toLocaleString()} · ${e.latitude.toFixed(6)}, ${e.longitude.toFixed(6)} · ±${Math.round(e.accuracy_m)} m · ${(e.content_base64.length*0.75/1024).toFixed(0)} KB`;
  renderEvidenceGallery();
}
async function saveDraft(){if(!activeAssignment)return;q("#formMessage").textContent="Saving on device…";await dbPut("drafts",draftData());q("#formMessage").textContent=`Draft saved locally at ${new Date().toLocaleTimeString()}.`}
async function submitInspection(e){
  e.preventDefault();if(!activeAssignment||!capturedEvidence.length){q("#formMessage").textContent="Verified live-camera evidence is required.";return}
  const validation=localTemplateValidation();if(!validation.valid){q("#formMessage").textContent=validation.message;return}
  const cache=assetCache(),serverAssets=cache[activeAssignment.id]||[];
  const queuedAssets=(await dbAll("outbox")).filter(x=>x.kind==="asset"&&x.payload.work_order_id===activeAssignment.id).map(x=>x.payload);
  const payload={
    client_id:uid(),work_order_id:activeAssignment.id,site_id:activeAssignment.site_id,inspector_name:profile.full_name,
    report_type:activeTemplate?.name||activeAssignment.report_type,
    summary:templateAnswers().final_comments||templateAnswers().comments||templateAnswers().recommendation||"",
    answers:{template_id:activeTemplate?.id,template_version:activeTemplate?.version,template_answers:templateAnswers(),asset_inventory:[...serverAssets,...queuedAssets].map(a=>({asset_type:a.asset_type,manufacturer:a.manufacturer,model:a.model,serial_number:a.serial_number,quantity:a.quantity,height_or_elevation:a.height_or_elevation,condition:a.condition,position:a.position}))},
    evidence:capturedEvidence,latitude:capturedEvidence[0].latitude,longitude:capturedEvidence[0].longitude,captured_at:capturedEvidence[0].captured_at,submit:true
  };
  await dbPut("outbox",{id:uid(),kind:"report",payload,created_at:new Date().toISOString()});
  await dbDelete("drafts",activeAssignment.id);
  q("#formMessage").textContent="Inspection submitted to the local queue.";
  capturedEvidence=[];q("#submitInspectionButton").disabled=true;renderEvidenceGallery();
  const tasks=cachedTasks().map(x=>x.id===activeAssignment.id?{...x,status:"Submitted"}:x);localStorage.setItem(TASKS_KEY,JSON.stringify(tasks));await renderTasks({assignments:tasks});
  if(navigator.onLine)await sync();show("sync");
}
async function sync(){
  network();
  const queue=await dbAll("outbox");renderQueue(queue);q("#pending").textContent=queue.length;
  if(!navigator.onLine)return;
  q("#syncStatus").textContent=`Synchronizing ${queue.length} queued change${queue.length===1?"":"s"}…`;
  for(const item of queue.filter(x=>x.kind==="asset")){
    try{await api("/assets",{method:"POST",body:JSON.stringify(item.payload)});await dbDelete("outbox",item.id)}catch(e){q("#syncStatus").textContent=`Asset sync paused: ${e.message}`;return}
  }
  const reportItems=(await dbAll("outbox")).filter(x=>x.kind==="report");
  if(reportItems.length){
    try{
      const body={mutations:reportItems.map(x=>({mutation_id:x.id,entity:"report",operation:"upsert",payload:x.payload}))};
      const result=await api("/sync/push",{method:"POST",body:JSON.stringify(body)});
      for(const r of result.results.filter(x=>["applied","duplicate"].includes(x.status)))await dbDelete("outbox",r.mutation_id);
      const errors=result.results.filter(x=>x.status==="error");if(errors.length)throw new Error(errors[0].message||"Report sync failed");
    }catch(e){q("#syncStatus").textContent=`Report sync paused: ${e.message}`;return}
  }
  localStorage.setItem("terrasync_last_sync",new Date().toLocaleString());q("#lastSync").textContent=`Synced ${new Date().toLocaleTimeString()}`;
  await refreshFromServer();const remaining=await dbAll("outbox");renderQueue(remaining);q("#pending").textContent=remaining.length;q("#syncStatus").textContent="Synchronization complete.";
  if(q("#inventoryAssignment").value)await loadAssets(q("#inventoryAssignment").value);
}
async function refreshFromServer(){
  const data=await api("/dashboard/technician");localStorage.setItem(TASKS_KEY,JSON.stringify(data.assignments));await renderTasks(data);
}
async function primeTemplates(){
  if(!navigator.onLine)return;
  try{
    const summaries=await api("/inspection-templates");
    const cache=templateCache();cache.__summaries=summaries;saveTemplateCache(cache);
  }catch(e){}
}
async function boot(){
  await new Promise(r=>setTimeout(r,650));
  const token=localStorage.getItem(TOKEN_KEY);profile=JSON.parse(localStorage.getItem(PROFILE_KEY)||"null");
  q("#splash").classList.add("hidden");
  if(!token||!profile){q("#activation").classList.remove("hidden");return}
  q("#fieldShell").classList.remove("hidden");renderProfile();network();await renderTasks();
  const activeId=localStorage.getItem("terrasync_active_assignment");if(activeId&&cachedTasks().some(x=>x.id===activeId))activeAssignment=cachedTasks().find(x=>x.id===activeId);
  if(activeAssignment){q("#inspectionEmpty").classList.add("hidden");q("#inspectionForm").classList.remove("hidden");q("#inspectionTitle").textContent=activeAssignment.work_order_no;q("#inspectionSite").textContent=activeAssignment.site_name||activeAssignment.site_id;q("#inspectionPriority").textContent=activeAssignment.priority;q("#inspectionTemplate").value=activeAssignment.report_type;const draft=await dbGet("drafts",activeAssignment.id);if(draft)loadDraft(draft)}
  if(navigator.onLine){try{await refreshFromServer();localStorage.setItem("terrasync_last_sync",new Date().toLocaleString())}catch(e){if(String(e.message).includes("401")||String(e.message).includes("Invalid")){localStorage.removeItem(TOKEN_KEY);localStorage.removeItem(PROFILE_KEY);location.reload()}}}
  const queue=await dbAll("outbox");renderQueue(queue);q("#deviceInfo").innerHTML=`<div class="sync-item"><span>Device key</span><strong>${deviceKey().slice(0,12)}…</strong></div><div class="sync-item"><span>Session</span><strong>Activated</strong></div>`;
}
q("#activationForm").addEventListener("submit",async e=>{e.preventDefault();q("#activationMessage").textContent="Activating this phone…";try{const data=await api("/auth/activate-device",{method:"POST",body:JSON.stringify({username:q("#username").value.trim(),code:q("#otp").value.trim(),device_key:deviceKey(),device_name:(navigator.userAgent||"TerraSync phone").slice(0,120),platform:navigator.platform||"Web"})});localStorage.setItem(TOKEN_KEY,data.access_token);localStorage.setItem(PROFILE_KEY,JSON.stringify(data.user));location.reload()}catch(err){q("#activationMessage").textContent=err.message}});
document.body.addEventListener("click",async e=>{const task=e.target.closest("[data-task]");if(task){await startAssignment(task.dataset.task);return}const view=e.target.closest("[data-view-button]");if(view){show(view.dataset.viewButton)}});
qa(".rail nav button,.bottom-nav button").forEach(b=>b.addEventListener("click",()=>show(b.dataset.view)));
q("#profileButton").addEventListener("click",()=>show("profile"));
q("#syncNow").addEventListener("click",sync);q("#syncPageButton").addEventListener("click",sync);
q("#inventoryAssignment").addEventListener("change",e=>loadAssets(e.target.value));
q("#startCameraButton").addEventListener("click",async()=>{if(!activeAssignment)return;try{q("#capturedPreview").hidden=true;await openCamera(q("#cameraPreview"),"inspection");q("#captureButton").disabled=false;q("#captureMetadata").textContent="Camera ready. Capture will bind current GPS and time."}catch(e){q("#captureMetadata").textContent=e.message}});
q("#captureButton").addEventListener("click",async()=>{try{q("#captureMetadata").textContent="Capturing and compressing verified evidence…";const evidence=await makeEvidence(q("#cameraPreview"),q("#captureCanvas"),activeAssignment.work_order_no);stopCamera();showInspectionEvidence(evidence);await saveDraft()}catch(e){q("#captureMetadata").textContent=`Capture failed: ${e.message}`}});
q("#retakeButton").addEventListener("click",()=>q("#startCameraButton").click());
q("#saveDraftButton").addEventListener("click",saveDraft);q("#inspectionForm").addEventListener("submit",submitInspection);
q("#openAssetCamera").addEventListener("click",async()=>{try{capturedAssetEvidence=null;q("#assetPreview").hidden=true;await openCamera(q("#assetCamera"),"asset");q("#captureAssetPhoto").disabled=false;q("#assetCaptureStatus").textContent="Camera ready. GPS and time will be captured automatically."}catch(e){q("#assetCaptureStatus").textContent=e.message}});
q("#captureAssetPhoto").addEventListener("click",async()=>{const assignment=cachedTasks().find(x=>x.id===q("#inventoryAssignment").value);if(!assignment)return;try{q("#assetCaptureStatus").textContent="Capturing verified asset evidence…";capturedAssetEvidence=await makeEvidence(q("#assetCamera"),q("#assetCanvas"),assignment.work_order_no);stopAssetCamera();const img=q("#assetPreview");img.src=`data:${capturedAssetEvidence.mime_type};base64,${capturedAssetEvidence.content_base64}`;img.hidden=false;q("#assetCamera").hidden=true;q("#retakeAssetPhoto").hidden=false;q("#assetEvidenceState").textContent="Verified";q("#assetEvidenceState").className="state good";q("#assetCaptureStatus").textContent=`${new Date(capturedAssetEvidence.captured_at).toLocaleString()} · ${capturedAssetEvidence.latitude.toFixed(6)}, ${capturedAssetEvidence.longitude.toFixed(6)}`}catch(e){q("#assetCaptureStatus").textContent=e.message}});
q("#retakeAssetPhoto").addEventListener("click",()=>q("#openAssetCamera").click());
q("#assetForm").addEventListener("submit",async e=>{e.preventDefault();const assignment=cachedTasks().find(x=>x.id===q("#inventoryAssignment").value);if(!assignment){q("#assetCaptureStatus").textContent="Select an assignment.";return}if(!capturedAssetEvidence){q("#assetCaptureStatus").textContent="A live full-picture camera capture is required.";return}const payload={client_id:uid(),work_order_id:assignment.id,site_id:assignment.site_id,asset_type:q("#assetType").value,manufacturer:q("#assetManufacturer").value||null,model:q("#assetModel").value||null,serial_number:q("#assetSerial").value||null,quantity:Number(q("#assetQuantity").value)||1,height_or_elevation:q("#assetHeight").value||null,dimensions:q("#assetDimensions").value||null,position:q("#assetPosition").value||null,condition:q("#assetCondition").value,notes:q("#assetNotes").value||null,source:"on_site",evidence:[capturedAssetEvidence]};await dbPut("outbox",{id:uid(),kind:"asset",payload,created_at:new Date().toISOString()});capturedAssetEvidence=null;e.target.reset();q("#assetQuantity").value=1;q("#assetPreview").hidden=true;q("#assetEvidenceState").textContent="Required";q("#assetEvidenceState").className="state bad";q("#assetCaptureStatus").textContent="Asset saved locally and queued for sync.";await loadAssets(assignment.id);const queue=await dbAll("outbox");renderQueue(queue);q("#pending").textContent=queue.length;if(navigator.onLine)await sync()});
window.addEventListener("online",()=>{network();sync()});window.addEventListener("offline",network);window.addEventListener("beforeunload",()=>{stopCamera();stopAssetCamera()});
if("serviceWorker" in navigator)navigator.serviceWorker.register("/app/service-worker.js");
boot();