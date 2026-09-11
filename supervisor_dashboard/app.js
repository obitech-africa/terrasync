const API="/api/v1",TOKEN_KEY="terrasync_supervisor_token";
let user=null;
const q=s=>document.querySelector(s),qa=s=>[...document.querySelectorAll(s)];
function headers(){return{"Authorization":`Bearer ${localStorage.getItem(TOKEN_KEY)||""}`,"Content-Type":"application/json"}}
async function api(path,opts={}){const r=await fetch(API+path,{...opts,headers:{...headers(),...(opts.headers||{})}});if(!r.ok){const b=await r.json().catch(()=>({detail:r.statusText}));throw new Error(typeof b.detail==="string"?b.detail:JSON.stringify(b.detail))}return r.json()}
function initials(n){return(n||"SV").split(/\s+/).map(x=>x[0]).join("").slice(0,2).toUpperCase()}
function show(id){qa(".view").forEach(v=>v.classList.toggle("active",v.id===id));qa(".nav button").forEach(b=>b.classList.toggle("active",b.dataset.view===id));q("#title").textContent={home:"Executive Operations",portfolio:"Portfolio",quality:"Quality & Risk",teams:"Teams",devices:"Device Governance",profile:"Profile"}[id]}
function row(title,sub,right=""){return`<div class="row"><div><h4>${title}</h4><p>${sub}</p></div><div>${right}</div></div>`}
function metric(label,value){return`<article class="metric"><span>${label}</span><strong>${value}</strong></article>`}
function riskClass(score){return score>=70?"high":score>=30?"med":"low"}
async function load(){
  user=await api("/auth/me");if(!["SUPERVISOR","ADMIN"].includes(user.role))throw new Error("Supervisor access required");
  q("#name").textContent=user.full_name;q("#role").textContent="Supervisor";q("#avatar").textContent=initials(user.full_name);
  q("#profileData").innerHTML=row("Staff number",user.staff_no||"—")+row("Company",user.company||"—")+row("Email",user.email||"—")+row("Access","Portfolio oversight & escalation");
  const [d,assignments,devices,techs,queue]=await Promise.all([api("/dashboard/supervisor"),api("/assignments"),api("/devices"),api("/users/technicians"),api("/review-queue")]);
  q("#metrics").innerHTML=metric("Assignments",d.total_assignments)+metric("Pending review",d.pending_review)+metric("Critical reports",d.critical_reports)+metric("Overdue",d.overdue);
  q("#health").innerHTML=`<div class="mini-grid"><div class="mini-card"><span>Completed</span><strong>${d.completed}</strong></div><div class="mini-card"><span>Field technicians</span><strong>${d.field_technicians}</strong></div><div class="mini-card"><span>Coordinators</span><strong>${d.coordinators}</strong></div><div class="mini-card"><span>Sync health</span><strong>${d.sync_health}%</strong></div></div>`;
  const critical=queue.filter(r=>(r.ai_risk_score||0)>=70);
  q("#escalations").innerHTML=critical.map(r=>row(r.report_no,r.ai_summary||r.status,`<span class="risk high">${r.ai_risk_score}/100</span>`)).join("")||row("No critical report escalation","Current AI-screened review queue has no report ≥70 risk.","<span class='risk low'>Clear</span>");
  q("#assignmentList").innerHTML=assignments.map(x=>row(x.work_order_no,`${x.report_type} · ${x.assigned_to||"Unassigned"} · ${x.status}`,`<span class="status">${x.priority}</span>`)).join("")||"<p class='muted'>No assignments.</p>";
  q("#qualityList").innerHTML=queue.map(r=>row(`${r.report_no} · ${r.status}`,r.ai_summary||r.report_type,`<span class="risk ${riskClass(r.ai_risk_score||0)}">${r.ai_risk_score||0}/100</span>`)).join("")||row("Review queue","No open reports require human review.");
  q("#teamList").innerHTML=techs.map(x=>row(x.full_name,`${x.staff_no||x.username} · ${x.company||"—"}`,`<span class="status">${x.active?"Active":"Inactive"}</span>`)).join("");
  q("#deviceList").innerHTML=devices.map(x=>row(x.device_name,`${x.platform||"Device"} · last seen ${new Date(x.last_seen_at).toLocaleString()}`,x.active?`<button data-revoke="${x.id}">Revoke</button>`:`<span class="status">Revoked</span>`)).join("")||"<p class='muted'>No registered devices.</p>";
}
q("#loginForm").addEventListener("submit",async e=>{e.preventDefault();q("#loginMessage").textContent="Signing in…";try{const data=await api("/auth/staff-login",{method:"POST",headers:{"Content-Type":"application/json","Authorization":""},body:JSON.stringify({username:q("#username").value,password:q("#password").value})});localStorage.setItem(TOKEN_KEY,data.access_token);q("#login").classList.add("hidden");q("#shell").classList.remove("hidden");await load()}catch(err){q("#loginMessage").textContent=err.message}});
document.body.addEventListener("click",async e=>{const b=e.target.closest("[data-revoke]");if(!b)return;if(!confirm("Revoke this registered field device? It will be blocked on its next online validation."))return;try{await api(`/devices/${b.dataset.revoke}/revoke`,{method:"POST"});await load()}catch(err){alert(err.message)}});
qa(".nav button").forEach(b=>b.addEventListener("click",()=>show(b.dataset.view)));
q("#logout").addEventListener("click",()=>{localStorage.removeItem(TOKEN_KEY);location.reload()});
if(localStorage.getItem(TOKEN_KEY)){q("#login").classList.add("hidden");q("#shell").classList.remove("hidden");load().catch(()=>{localStorage.removeItem(TOKEN_KEY);location.reload()})}