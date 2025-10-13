const qs = new URLSearchParams(location.search);
const $ = (sel, root=document) => root.querySelector(sel);
const API_BASE = (localStorage.getItem('API_BASE') || 'http://localhost:8000').replace(/\/$/, '');

// Settings modal
function openSettings(){ $('#settingsModal')?.classList.remove('hidden'); $('#apiBaseInput').value = API_BASE; }
function closeSettings(){ $('#settingsModal')?.classList.add('hidden'); }
function saveSettings(){ const val = $('#apiBaseInput').value.trim(); if(val){ localStorage.setItem('API_BASE', val); closeSettings(); location.reload(); } }
$('#btnSettings')?.addEventListener('click', openSettings);
$('#btnCloseSettings')?.addEventListener('click', closeSettings);
$('#btnSaveSettings')?.addEventListener('click', saveSettings);

async function apiGet(path){ const resp = await fetch(`${API_BASE}${path}`); if(!resp.ok) throw new Error(`GET ${path} -> ${resp.status}`); return resp.json(); }
async function apiPost(path, body){
  const resp = await fetch(`${API_BASE}${path}`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
  if(!resp.ok){ const txt = await resp.text(); throw new Error(`POST ${path} -> ${resp.status} ${txt}`); }
  return resp.json();
}

// index.html
async function initIndex(){
  const grid = $('#modelsGrid');
  if(!grid) return;
  try{
    const models = await apiGet('/models');
    grid.innerHTML = '';
    // Ne garder que ChatGPT & Mistral
    const allowed = ['openai', 'mistral'];
    const filtered = models.filter(m => allowed.includes(m.provider));
    for(const m of filtered){
      const card = document.createElement('a');
      card.className = 'card';
      card.href = `./chat.html?model=${encodeURIComponent(m.model)}&label=${encodeURIComponent(m.label)}`;
      card.innerHTML = `
        <div class="row">
          <div class="badge">${m.provider === 'openai' ? 'ChatGPT' : 'Mistral'}</div>
          <strong>${m.label}</strong>
        </div>
        <p class="muted small">Modèle ID: <code>${m.model}</code></p>
      `;
      grid.appendChild(card);
    }
  }catch(e){
    grid.innerHTML = `<div class="card"><p>Erreur : <code>${e}</code></p></div>`;
  }
}

// chat.html
const state = {model: qs.get('model')||null, modelLabel: qs.get('label')||null, messages: [], sending: false};

function renderUsage(resp){
  const u = resp?.usage || {};
  const parts = [];
  if(u.input_tokens || u.output_tokens) parts.push(`tokens ${u.input_tokens||0}/${u.output_tokens||0}`);
  if(resp?.cost_eur) parts.push(`${resp.cost_eur.toFixed(6)} €`);
  if(resp?.est_co2e_g) parts.push(`${resp.est_co2e_g.toFixed(2)} gCO₂e`);
  $('#usageStats').textContent = parts.join(' • ');
}
function renderMessages(){
  const log = $('#chatLog');
  if(!log) return;
  log.innerHTML = '';
  for(const msg of state.messages){
    const icon = msg.role==='assistant'?'🤖':(msg.role==='system'?'⚙️':'🙂');
    log.innerHTML += `<div class="msg ${msg.role}"><div class="avatar">${icon}</div><div class="bubble">${msg.content}</div></div>`;
  }
  log.scrollTop = log.scrollHeight;
}
async function sendMessage(){
  if(state.sending) return;
  const input = $('#chatInput');
  const text = (input.value||'').trim();
  if(!text) return;
  state.messages.push({role:'user', content:text});
  input.value=''; renderMessages();
  state.sending=true; $('#btnSend').disabled=true;
  try{
    const body = {user_id:'webclient', model:state.model, messages:state.messages, stream:false};
    const resp = await apiPost('/chat', body);
    state.messages.push({role:'assistant', content:resp?.content||''});
    renderMessages(); renderUsage(resp);
  }catch(e){
    state.messages.push({role:'assistant', content:`⚠️ Erreur: ${e.message}`});
    renderMessages();
  }finally{ state.sending=false; $('#btnSend').disabled=false; }
}
function initChat(){
  if(!$('.chat-layout')) return;
  $('#btnClear')?.addEventListener('click', ()=>{ state.messages=[]; renderMessages(); $('#usageStats').textContent=''; });
  $('#chatForm')?.addEventListener('submit', e=>{ e.preventDefault(); sendMessage(); });
  $('#chatInput')?.addEventListener('keydown', e=>{ if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); sendMessage(); }});
  $('#currentModelLabel').textContent = state.modelLabel || state.model || 'Modèle';
}

// boot
initIndex();
initChat();
