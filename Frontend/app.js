const qs = new URLSearchParams(location.search);
const $ = (sel, root=document) => root.querySelector(sel);
const API_BASE = (localStorage.getItem('API_BASE') || 'http://72.60.189.114:8010').replace(/\/$/, '');



// modal API
function openSettings(){ $('#settingsModal')?.classList.remove('hidden'); $('#apiBaseInput').value = API_BASE; }
function closeSettings(){ $('#settingsModal')?.classList.add('hidden'); }
function saveSettings(){ const val = $('#apiBaseInput').value.trim(); if(val){ localStorage.setItem('API_BASE', val); closeSettings(); location.reload(); } }
$('#btnSettings')?.addEventListener('click', openSettings);
$('#btnCloseSettings')?.addEventListener('click', closeSettings);
$('#btnSaveSettings')?.addEventListener('click', saveSettings);

async function apiPost(path, body){
  const resp = await fetch(`${API_BASE}${path}`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
  if(!resp.ok){ const txt = await resp.text(); throw new Error(`POST ${path} -> ${resp.status} ${txt}`); }
  return resp.json();
}

// état global
const state = {
  provider: qs.get('provider') || 'openai',
  model: null,
  messages: [],
  sending: false
};

// modèles disponibles
const MODELS = {
  openai: [
    { id: 'openai:gpt-4o-mini', label: 'GPT-4o-Mini' },
    { id: 'openai:gpt-4o', label: 'GPT-4o' },
    { id: 'openai:gpt-4-turbo', label: 'GPT-4-Turbo' },
    { id: 'openai:gpt-3.5-turbo', label: 'GPT-3.5-Turbo' },
    { id: 'openai:gpt-5', label: 'GPT-5 (bientôt disponible)', disabled: true },
  ],
    mistral: [
        { id: 'mistral:open-mixtral-8x7b', label: 'Mixtral 8×7B' },
        { id: 'mistral:open-mistral-7b', label: 'Mistral 7B' },
    ],
};



// initialise dropdown selon le provider
function initModelSelect() {
  const select = $('#modelSelect');
  if (!select) return;
  const providerModels = MODELS[state.provider] || [];
  select.innerHTML = '';
  providerModels.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m.id;
    opt.textContent = m.label;
    select.appendChild(opt);
  });
  state.model = providerModels[0]?.id || null;
  $('#currentModelLabel').textContent = providerModels[0]?.label || 'Modèle';
  select.addEventListener('change', e => {
    state.model = e.target.value;
    const selectedText = e.target.options[e.target.selectedIndex].text;
    $('#currentModelLabel').textContent = selectedText;
  });
}

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
  if(state.sending || !state.model) return;
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
  initModelSelect();
}

// boot
initChat();
