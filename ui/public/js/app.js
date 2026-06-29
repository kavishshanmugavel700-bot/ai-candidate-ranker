// ── Char counter ──────────────────────────────────────────────
const textarea  = document.getElementById('jd-input');
const charCount = document.getElementById('char-count');

textarea.addEventListener('input', () => {
  const n = textarea.value.length;
  charCount.textContent = `${n} character${n !== 1 ? 's' : ''}`;
});

// ── Helpers ───────────────────────────────────────────────────
function scoreClass(s) {
  if (s >= 80) return 'green';
  if (s >= 60) return 'orange';
  return 'red';
}

function rankClass(i) {
  if (i === 1) return 'rank-1';
  if (i === 2) return 'rank-2';
  if (i === 3) return 'rank-3';
  return 'rank-other';
}

function rankEmoji(i) {
  if (i === 1) return '🥇';
  if (i === 2) return '🥈';
  if (i === 3) return '🥉';
  return `#${i}`;
}

function buildBar(label, value) {
  const cls = scoreClass(value);
  return `
    <div class="bar-row">
      <span class="bar-label">${label}</span>
      <div class="bar-track">
        <div
          class="bar-fill bar-${cls}"
          data-width="${value}"
          style="width:0%"
        ></div>
      </div>
      <span class="bar-val">${value}</span>
    </div>`;
}

function buildRing(score) {
  const cls   = scoreClass(score);
  const circ  = 163;
  const offset = circ - (score / 100) * circ;
  return `
    <div class="score-ring">
      <svg width="64" height="64" viewBox="0 0 64 64">
        <circle class="score-ring-bg"   cx="32" cy="32" r="26"/>
        <circle
          class="score-ring-fill ring-${cls}"
          cx="32" cy="32" r="26"
          data-offset="${offset}"
          style="stroke-dashoffset:${circ}"
        />
      </svg>
      <div class="score-label score-${cls}">${score}</div>
    </div>
    <span class="score-tag">Score</span>`;
}

function buildCard(c, idx) {
  const rank = idx + 1;
  return `
    <div class="candidate-card" style="animation-delay:${idx * 0.07}s">
      <div class="card-rank ${rankClass(rank)}">${rankEmoji(rank)}</div>
      <div class="card-body">
        <div class="card-name">${escapeHTML(c.name)}</div>
        <div class="card-reason">${escapeHTML(c.reason)}</div>
        <div class="card-bars">
          ${buildBar('Skills',     c.skills_score)}
          ${buildBar('Experience', c.experience_score)}
          ${buildBar('Growth',     c.growth_score)}
        </div>
      </div>
      <div class="card-score">
        ${buildRing(c.total_score)}
      </div>
    </div>`;
}

function escapeHTML(str) {
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// Trigger bar / ring animations after DOM insert
function animateCards() {
  // Bars
  document.querySelectorAll('.bar-fill[data-width]').forEach(el => {
    const w = el.dataset.width;
    requestAnimationFrame(() => { el.style.width = w + '%'; });
  });
  // Rings
  document.querySelectorAll('.score-ring-fill[data-offset]').forEach(el => {
    const off = el.dataset.offset;
    requestAnimationFrame(() => { el.style.strokeDashoffset = off; });
  });
}

// ── Main function ─────────────────────────────────────────────
async function rankCandidates() {
  const jd = textarea.value.trim();

  // Clear state
  document.getElementById('error-box').style.display    = 'none';
  document.getElementById('results-header').style.display = 'none';
  document.getElementById('results-list').innerHTML     = '';

  if (!jd) {
    showError('Please paste a job description before searching.');
    return;
  }

  // Loading
  const btn = document.getElementById('rank-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="btn-icon">⏳</span> Ranking...';
  document.getElementById('skeleton-list').style.display = 'flex';
  document.getElementById('skeleton-list').style.flexDirection = 'column';

  try {
    const res = await fetch('/api/rank', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ job_description: jd }),
    });

    if (!res.ok) throw new Error(`Server error ${res.status}`);

    const data = await res.json();

    if (!data.success) throw new Error(data.message || 'Ranking failed.');

    const candidates = data.candidates || [];

    // Render
    document.getElementById('results-header').style.display = 'flex';
    document.getElementById('results-count').textContent =
      `${candidates.length} candidate${candidates.length !== 1 ? 's' : ''}`;

    document.getElementById('results-list').innerHTML =
      candidates.map((c, i) => buildCard(c, i)).join('');

    // Kick off animations on next frame
    setTimeout(animateCards, 60);

    // Smooth scroll to results
    document.getElementById('results-header').scrollIntoView({ behavior: 'smooth', block: 'start' });

  } catch (err) {
    showError(err.message || 'Could not connect to the ranking service. Make sure the Flask server is running on port 5000.');
  } finally {
    document.getElementById('skeleton-list').style.display = 'none';
    btn.disabled = false;
    btn.innerHTML = '<span class="btn-icon">🔍</span> Find Top Candidates';
  }
}

function showError(msg) {
  const box = document.getElementById('error-box');
  document.getElementById('error-msg').textContent = msg;
  box.style.display = 'flex';
}

// Allow Enter shortcut (Ctrl/Cmd+Enter in textarea)
textarea.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') rankCandidates();
});