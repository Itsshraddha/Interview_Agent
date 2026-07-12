/* ══════════════════════════════════════════════════════════════════════
   Interview Trainer Agent — app.js
   Handles: form submit, loading states, results rendering, dark mode,
            copy-to-clipboard, TTS, accordion, tabs, checklist progress,
            drag-drop upload, markdown download.
══════════════════════════════════════════════════════════════════════ */

'use strict';

// ── Dark mode ──────────────────────────────────────────────────────────────
(function initTheme() {
  const saved = localStorage.getItem('ia-theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
})();

document.getElementById('themeToggle').addEventListener('click', () => {
  const html = document.documentElement;
  const next = html.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
  html.setAttribute('data-theme', next);
  localStorage.setItem('ia-theme', next);
});

// ── Role dropdown — show custom input ─────────────────────────────────────
const roleSelect  = document.getElementById('target_role');
const customInput = document.getElementById('custom_role');
if (roleSelect) {
  roleSelect.addEventListener('change', () => {
    customInput.style.display = roleSelect.value === 'Other' ? 'block' : 'none';
    if (roleSelect.value !== 'Other') customInput.value = '';
  });
}

// ── Slider label ───────────────────────────────────────────────────────────
const slider   = document.getElementById('top_k');
const topKLabel = document.getElementById('topKLabel');
if (slider && topKLabel) {
  slider.addEventListener('input', () => { topKLabel.textContent = slider.value; });
}

// ── Drag & drop upload zone ────────────────────────────────────────────────
const uploadZone    = document.getElementById('uploadZone');
const uploadInput   = document.getElementById('resume');
const uploadContent = document.getElementById('uploadContent');

function showFileSelected(filename) {
  uploadContent.innerHTML = `
    <div class="upload-success">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
      ${filename}
      <button type="button" onclick="clearUpload()" style="background:none;border:none;cursor:pointer;color:var(--danger);font-size:1rem;padding:0;margin-left:4px">×</button>
    </div>`;
}

window.clearUpload = function () {
  uploadInput.value = '';
  uploadContent.innerHTML = `
    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="upload-icon"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
    <p class="upload-label">Drop PDF or TXT here, or <span class="upload-link">browse</span></p>
    <p class="upload-sub">Personalises questions to your skills</p>`;
};

if (uploadInput) {
  uploadInput.addEventListener('change', () => {
    if (uploadInput.files[0]) showFileSelected(uploadInput.files[0].name);
  });
}
if (uploadZone) {
  uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('drag-over'); });
  uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
  uploadZone.addEventListener('drop', e => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file && (file.type === 'application/pdf' || file.name.endsWith('.txt'))) {
      const dt = new DataTransfer();
      dt.items.add(file);
      uploadInput.files = dt.files;
      showFileSelected(file.name);
    }
  });
}

// ── Loading step sequencer ─────────────────────────────────────────────────
let loadingTimer = null;
const LOADING_STEPS = ['lstep1','lstep2','lstep3','lstep4','lstep5'];

function startLoadingSteps() {
  let current = 0;
  const stepEl = id => document.getElementById(id);
  LOADING_STEPS.forEach(id => {
    const el = stepEl(id);
    if (el) { el.classList.remove('active','done'); }
  });
  function activate() {
    if (current > 0) {
      const prev = stepEl(LOADING_STEPS[current - 1]);
      if (prev) { prev.classList.remove('active'); prev.classList.add('done'); }
    }
    if (current < LOADING_STEPS.length) {
      const cur = stepEl(LOADING_STEPS[current]);
      if (cur) cur.classList.add('active');
      current++;
      loadingTimer = setTimeout(activate, 5500);
    }
  }
  activate();
}

function stopLoadingSteps() {
  if (loadingTimer) clearTimeout(loadingTimer);
  LOADING_STEPS.forEach(id => {
    const el = document.getElementById(id);
    if (el) { el.classList.remove('active'); el.classList.add('done'); }
  });
}

// ── Show / hide panels ─────────────────────────────────────────────────────
function showPanel(name) {
  ['featureShowcase','loadingPanel','errorPanel','resultsPanel'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = id === name ? 'block' : 'none';
  });
}

window.resetToForm = function () {
  showPanel('featureShowcase');
  const btn = document.getElementById('generateBtn');
  if (btn) { btn.disabled = false; btn.textContent = ''; btn.innerHTML = svgBolt() + ' Generate Prep Kit'; }
};

function svgBolt() {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`;
}

// ── Form submit ────────────────────────────────────────────────────────────
const form = document.getElementById('prepForm');
if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const name    = document.getElementById('candidate_name').value.trim();
    const roleRaw = roleSelect ? roleSelect.value : '';
    const role    = roleRaw === 'Other' ? customInput.value.trim() : roleRaw;
    const note    = document.getElementById('formNote');

    if (!name || !role) {
      if (note) { note.textContent = 'Please fill in your name and target role.'; note.style.display = 'block'; }
      return;
    }
    if (note) note.style.display = 'none';

    // Disable button & show loading
    const btn = document.getElementById('generateBtn');
    btn.disabled = true;
    btn.innerHTML = `<span style="display:inline-flex;gap:4px">
      <span style="animation:bounce 1.2s -.32s infinite ease-in-out both;display:inline-block;width:6px;height:6px;border-radius:50%;background:#fff"></span>
      <span style="animation:bounce 1.2s -.16s infinite ease-in-out both;display:inline-block;width:6px;height:6px;border-radius:50%;background:#fff"></span>
      <span style="animation:bounce 1.2s 0s infinite ease-in-out both;display:inline-block;width:6px;height:6px;border-radius:50%;background:#fff"></span>
    </span> Generating…`;

    showPanel('loadingPanel');
    startLoadingSteps();

    // Build form data (inject resolved role)
    const fd = new FormData(form);
    fd.set('target_role', role);

    try {
      const resp = await fetch('/generate', { method: 'POST', body: fd });
      const data = await resp.json();
      stopLoadingSteps();

      if (data.status === 'ok') {
        renderKit(data.kit, data.profile);
      } else {
        showError(data.type, data.message);
      }
    } catch (err) {
      stopLoadingSteps();
      showError('unknown', 'Network error — could not reach the server.\n' + err.message);
    } finally {
      btn.disabled = false;
      btn.innerHTML = svgBolt() + ' Generate Prep Kit';
    }
  });
}

// ── Error display ──────────────────────────────────────────────────────────
function showError(type, message) {
  showPanel('errorPanel');
  const titles = {
    credentials: 'Credentials Not Configured',
    no_kb:       'Knowledge Base Not Built',
    generation:  'Generation Failed',
    unknown:     'Unexpected Error',
  };
  const hints = {
    credentials: 'Copy .env.example → .env and fill in WATSONX_APIKEY, WATSONX_URL, WATSONX_PROJECT_ID.',
    no_kb:       'Run: python src/ingest.py  to build the knowledge base first.',
    generation:  'Check that your IBM Cloud instance is active and within quota.',
    unknown:     'Check the terminal for the full traceback.',
  };
  document.getElementById('errorTitle').textContent = titles[type] || 'Error';
  document.getElementById('errorMsg').textContent   = (message || '') + '\n\n' + (hints[type] || '');
}

// ── Tabs ───────────────────────────────────────────────────────────────────
function initTabs(container) {
  container.querySelectorAll('.kit-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      container.querySelectorAll('.kit-tab').forEach(t => t.classList.remove('active'));
      container.querySelectorAll('.kit-tab-panel').forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      const panel = container.querySelector(`[data-panel="${tab.dataset.tab}"]`);
      if (panel) panel.classList.add('active');
    });
  });
}

// ── Accordion ──────────────────────────────────────────────────────────────
function initAccordions(container) {
  container.querySelectorAll('.q-header').forEach(header => {
    header.addEventListener('click', () => {
      const card = header.closest('.q-card');
      card.classList.toggle('open');
    });
  });
}

// ── Checklist progress ─────────────────────────────────────────────────────
function initChecklist(container) {
  const items   = container.querySelectorAll('.checklist-item');
  const fill    = container.querySelector('.cp-bar-fill');
  const counter = container.querySelector('.cp-counter');

  function update() {
    const done = container.querySelectorAll('.checklist-item.checked').length;
    const pct  = items.length ? Math.round((done / items.length) * 100) : 0;
    if (fill)    fill.style.width = pct + '%';
    if (counter) counter.textContent = `${done} / ${items.length}`;
  }

  items.forEach(item => {
    item.addEventListener('click', () => {
      item.classList.toggle('checked');
      update();
    });
  });
  update();
}

// ── Copy to clipboard ──────────────────────────────────────────────────────
window.copyText = function (text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
  }).catch(() => { btn.textContent = 'Failed'; setTimeout(() => btn.textContent = 'Copy', 2000); });
};

// ── Text-to-speech ─────────────────────────────────────────────────────────
window.readAloud = function (text, btn) {
  if (!window.speechSynthesis) return;
  if (speechSynthesis.speaking) {
    speechSynthesis.cancel();
    btn.textContent = '🔊 Read';
    btn.classList.remove('speaking');
    return;
  }
  const utt = new SpeechSynthesisUtterance(text);
  utt.rate = 0.92;
  btn.textContent = '⏹ Stop';
  btn.classList.add('speaking');
  utt.onend = () => { btn.textContent = '🔊 Read'; btn.classList.remove('speaking'); };
  speechSynthesis.speak(utt);
};

// ── HTML escape ────────────────────────────────────────────────────────────
function esc(s) {
  return (s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── Difficulty badge ───────────────────────────────────────────────────────
function diffBadge(d) {
  const map = { foundational: 'tag-foundational', intermediate: 'tag-intermediate', advanced: 'tag-advanced' };
  const cls = map[(d||'').toLowerCase()] || 'tag-intermediate';
  return `<span class="q-tag ${cls}">${esc(d || 'intermediate')}</span>`;
}

// ── Build tips HTML ────────────────────────────────────────────────────────
function tipsHtml(tips) {
  if (!tips || !tips.length) return '';
  return `<div class="q-section-label label-amber">💡 Improvement Tips</div>
    <div class="tips-list">${tips.map((t,i) => `
      <div class="tip-pill">
        <span class="tip-num">${i+1}</span>
        <span>${esc(t)}</span>
      </div>`).join('')}
    </div>`;
}

// ── Build one technical question card ─────────────────────────────────────
function techCardHtml(q, i) {
  const ans = esc(q.model_answer || '');
  const codeHtml = q.code_example
    ? `<div class="q-section-label label-blue">Code Example</div>
       <div class="code-box">${esc(q.code_example)}</div>` : '';
  const whyHtml  = q.why_asked
    ? `<div class="why-box">
         <span style="flex-shrink:0">🎯</span>
         <em>${esc(q.why_asked)}</em>
       </div>` : '';
  const fuHtml   = q.follow_up_question
    ? `<div class="q-section-label label-blue" style="margin-top:.9rem">Likely Follow-up</div>
       <div class="followup-box">
         <span class="followup-icon">↩</span>
         <span>${esc(q.follow_up_question)}</span>
       </div>` : '';

  return `
    <div class="q-card">
      <div class="q-header">
        <span class="q-num">${i}</span>
        <div class="q-title-area">
          <div class="q-text">${esc(q.question)}</div>
          <div class="q-tags">${diffBadge(q.difficulty)}</div>
        </div>
        <svg class="q-chevron" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
      </div>
      <div class="q-body">
        ${whyHtml}
        <div class="q-section-label label-blue" style="margin-top:.9rem">📘 Model Answer</div>
        <div class="answer-box">
          ${ans}
          <button class="copy-btn" onclick="copyText(${JSON.stringify(q.model_answer||'')}, this)">Copy</button>
        </div>
        <button class="tts-btn" onclick="readAloud(${JSON.stringify((q.question||'') + '. ' + (q.model_answer||''))}, this)">🔊 Read aloud</button>
        ${codeHtml}
        ${tipsHtml(q.tips)}
        ${fuHtml}
      </div>
    </div>`;
}

// ── Build one behavioral question card ────────────────────────────────────
function behavCardHtml(q, i) {
  const star  = esc(q.star_answer_outline || '');
  const compHtml = q.competency_tested
    ? `<span class="q-tag tag-competency">${esc(q.competency_tested)}</span>` : '';
  const rfHtml = (q.red_flags_to_avoid && q.red_flags_to_avoid.length)
    ? `<div class="q-section-label label-red" style="margin-top:.9rem">⚠️ Red Flags to Avoid</div>
       <div class="redflag-list">${q.red_flags_to_avoid.map(r =>
         `<div class="redflag-item"><span class="redflag-icon">✗</span><span>${esc(r)}</span></div>`
       ).join('')}</div>` : '';

  return `
    <div class="q-card behavioral">
      <div class="q-header">
        <span class="q-num">${i}</span>
        <div class="q-title-area">
          <div class="q-text">${esc(q.question)}</div>
          <div class="q-tags">${compHtml}</div>
        </div>
        <svg class="q-chevron" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
      </div>
      <div class="q-body">
        <div class="q-section-label label-green">⭐ STAR Answer Outline</div>
        <div class="star-box">${star}</div>
        <button class="tts-btn" onclick="readAloud(${JSON.stringify((q.question||'') + '. ' + (q.star_answer_outline||''))}, this)">🔊 Read aloud</button>
        ${rfHtml}
        ${tipsHtml(q.tips)}
      </div>
    </div>`;
}

// ── Build checklist tab HTML ───────────────────────────────────────────────
function checklistHtml(items) {
  const listItems = (items || []).map(item => `
    <div class="checklist-item">
      <div class="ci-box"></div>
      <span class="ci-text">${esc(item)}</span>
    </div>`).join('');
  return `
    <div class="checklist-progress">
      <div class="cp-label">
        <span>Your progress</span>
        <span class="cp-counter">0 / ${(items||[]).length}</span>
      </div>
      <div class="cp-bar-track"><div class="cp-bar-fill" style="width:0%"></div></div>
    </div>
    <div class="checklist-list">${listItems}</div>`;
}

// ── Build roadmap tab HTML ─────────────────────────────────────────────────
function roadmapHtml(roadmap) {
  if (!roadmap || typeof roadmap !== 'object') return '<p style="color:var(--muted)">No roadmap generated.</p>';
  const weekItems = (arr) => (arr || []).map(i =>
    `<div class="roadmap-item"><span class="roadmap-bullet">→</span><span>${esc(i)}</span></div>`
  ).join('');
  return `
    <div class="roadmap-grid">
      <div class="roadmap-col">
        <div class="roadmap-week-label">Week 1</div>
        <div class="roadmap-items">${weekItems(roadmap.week_1)}</div>
      </div>
      <div class="roadmap-col">
        <div class="roadmap-week-label">Week 2</div>
        <div class="roadmap-items">${weekItems(roadmap.week_2)}</div>
      </div>
      <div class="roadmap-col day-before">
        <div class="roadmap-week-label">Day Before</div>
        <div class="roadmap-items">${weekItems(roadmap.day_before)}</div>
      </div>
    </div>`;
}

// ── Build "questions to ask" tab HTML ─────────────────────────────────────
function askHtml(questions) {
  if (!questions || !questions.length) return '<p style="color:var(--muted)">No questions generated.</p>';
  return `<div class="ask-list">${questions.map((q,i) =>
    `<div class="ask-item"><span class="ask-num">${i+1}</span><span>${esc(q)}</span></div>`
  ).join('')}</div>`;
}

// ── Markdown download ──────────────────────────────────────────────────────
function buildMarkdown(kit, profile) {
  const lines = [];
  lines.push(`# Interview Prep Kit`);
  lines.push(`**Candidate:** ${profile.name}  |  **Role:** ${profile.role}  |  **Level:** ${profile.level}`);
  lines.push('');
  lines.push('---');
  lines.push('');
  lines.push('## 💻 Technical Questions');
  lines.push('');
  (kit.technical_questions || []).forEach((q,i) => {
    lines.push(`### Q${i+1}: ${q.question}`);
    lines.push(`*Difficulty: ${q.difficulty} | Why asked: ${q.why_asked}*`);
    lines.push('');
    lines.push('**Model Answer**');
    lines.push(q.model_answer || '');
    lines.push('');
    if (q.code_example) {
      lines.push('```');
      lines.push(q.code_example);
      lines.push('```');
      lines.push('');
    }
    if (q.tips && q.tips.length) {
      lines.push('**Tips**');
      q.tips.forEach(t => lines.push(`- ${t}`));
    }
    if (q.follow_up_question) {
      lines.push('');
      lines.push(`*Follow-up: ${q.follow_up_question}*`);
    }
    lines.push('');
  });
  lines.push('---');
  lines.push('');
  lines.push('## 🤝 Behavioral / HR Questions');
  lines.push('');
  (kit.behavioral_questions || []).forEach((q,i) => {
    lines.push(`### HR${i+1}: ${q.question}`);
    lines.push(`*Competency: ${q.competency_tested}*`);
    lines.push('');
    lines.push('**STAR Answer Outline**');
    lines.push(q.star_answer_outline || '');
    lines.push('');
    if (q.red_flags_to_avoid && q.red_flags_to_avoid.length) {
      lines.push('**Red Flags to Avoid**');
      q.red_flags_to_avoid.forEach(r => lines.push(`- ✗ ${r}`));
      lines.push('');
    }
    if (q.tips && q.tips.length) {
      lines.push('**Tips**');
      q.tips.forEach(t => lines.push(`- ${t}`));
    }
    lines.push('');
  });
  lines.push('---');
  lines.push('');
  lines.push('## ✅ Confidence Checklist');
  (kit.confidence_checklist || []).forEach(i => lines.push(`- [ ] ${i}`));
  lines.push('');
  lines.push('---');
  lines.push('');
  lines.push('## 📅 Study Roadmap');
  const rm = kit.role_study_roadmap || {};
  if (rm.week_1 && rm.week_1.length) {
    lines.push('**Week 1**');
    rm.week_1.forEach(i => lines.push(`- ${i}`));
    lines.push('');
  }
  if (rm.week_2 && rm.week_2.length) {
    lines.push('**Week 2**');
    rm.week_2.forEach(i => lines.push(`- ${i}`));
    lines.push('');
  }
  if (rm.day_before && rm.day_before.length) {
    lines.push('**Day Before**');
    rm.day_before.forEach(i => lines.push(`- ${i}`));
    lines.push('');
  }
  lines.push('---');
  lines.push('');
  lines.push('## 💬 Questions to Ask Your Interviewer');
  (kit.questions_to_ask_interviewer || []).forEach((q,i) => lines.push(`${i+1}. ${q}`));
  lines.push('');
  lines.push('---');
  lines.push('*Generated by Interview Trainer Agent · IBM Granite · watsonx.ai*');
  return lines.join('\n');
}

function downloadFile(content, filename, mime) {
  const a  = document.createElement('a');
  a.href   = URL.createObjectURL(new Blob([content], { type: mime }));
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

// ── Main render function ───────────────────────────────────────────────────
function renderKit(kit, profile) {
  const tech  = kit.technical_questions  || [];
  const behav = kit.behavioral_questions || [];
  const check = kit.confidence_checklist || [];
  const ask   = kit.questions_to_ask_interviewer || [];
  const road  = kit.role_study_roadmap   || {};

  const now = new Date().toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' });

  const html = `
    <!-- Kit header -->
    <div class="kit-header">
      <div>
        <div class="kit-profile-name">${esc(profile.name)}'s Prep Kit</div>
        <div class="kit-meta">
          <span class="kit-badge kit-badge-role">${esc(profile.role)}</span>
          <span class="kit-badge kit-badge-level">${esc(profile.level)}</span>
          <span class="kit-badge kit-badge-ts">${esc(now)}</span>
        </div>
      </div>
      <div class="kit-actions">
        <button class="btn-dl" id="mdDlBtn">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Markdown
        </button>
        <button class="btn-dl btn-dl-primary" onclick="window.print()">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
          Print / PDF
        </button>
      </div>
    </div>

    <!-- Stats row -->
    <div class="stats-row">
      <div class="stat-tile"><div class="stat-num">${tech.length}</div><div class="stat-label">Technical Questions</div></div>
      <div class="stat-tile"><div class="stat-num">${behav.length}</div><div class="stat-label">Behavioral Questions</div></div>
      <div class="stat-tile"><div class="stat-num">${check.length}</div><div class="stat-label">Checklist Items</div></div>
      <div class="stat-tile"><div class="stat-num">${ask.length}</div><div class="stat-label">Questions to Ask</div></div>
    </div>

    <!-- Tabs -->
    <div class="kit-tabs">
      <button class="kit-tab active" data-tab="technical">
        💻 Technical <span class="tab-count">${tech.length}</span>
      </button>
      <button class="kit-tab" data-tab="behavioral">
        🤝 Behavioral <span class="tab-count">${behav.length}</span>
      </button>
      <button class="kit-tab" data-tab="checklist">
        ✅ Checklist <span class="tab-count">${check.length}</span>
      </button>
      <button class="kit-tab" data-tab="roadmap">
        📅 Roadmap
      </button>
      <button class="kit-tab" data-tab="ask">
        💬 Ask Them <span class="tab-count">${ask.length}</span>
      </button>
    </div>

    <!-- Technical tab -->
    <div class="kit-tab-panel active" data-panel="technical">
      ${tech.length ? tech.map((q,i) => techCardHtml(q, i+1)).join('') : '<p style="color:var(--muted)">No technical questions generated.</p>'}
    </div>

    <!-- Behavioral tab -->
    <div class="kit-tab-panel" data-panel="behavioral">
      ${behav.length ? behav.map((q,i) => behavCardHtml(q, i+1)).join('') : '<p style="color:var(--muted)">No behavioral questions generated.</p>'}
    </div>

    <!-- Checklist tab -->
    <div class="kit-tab-panel" data-panel="checklist">
      ${checklistHtml(check)}
    </div>

    <!-- Roadmap tab -->
    <div class="kit-tab-panel" data-panel="roadmap">
      ${roadmapHtml(road)}
    </div>

    <!-- Ask Them tab -->
    <div class="kit-tab-panel" data-panel="ask">
      ${askHtml(ask)}
    </div>
  `;

  const panel = document.getElementById('resultsPanel');
  panel.innerHTML = html;
  showPanel('resultsPanel');

  // Scroll results into view on mobile
  setTimeout(() => panel.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);

  // Wire up tabs, accordions, checklist
  initTabs(panel);
  initAccordions(panel);
  initChecklist(panel.querySelector('[data-panel="checklist"]'));

  // Markdown download
  const mdBtn = document.getElementById('mdDlBtn');
  if (mdBtn) {
    mdBtn.addEventListener('click', () => {
      downloadFile(buildMarkdown(kit, profile), 'interview_prep_kit.md', 'text/markdown');
    });
  }
}
