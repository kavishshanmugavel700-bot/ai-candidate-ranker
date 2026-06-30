// ── State & DOM references ───────────────────────────────────────
const textarea  = document.getElementById('jd-input');
const charCount = document.getElementById('char-count');

let rawCandidates    = [];
let activeFilterPill = 'all';

// ── Char Counter & Presets ──────────────────────────────────────
textarea.addEventListener('input', updateCharCount);

function updateCharCount() {
  const n = textarea.value.length;
  charCount.textContent = `${n} character${n !== 1 ? 's' : ''}`;
}

const PRESETS = {
  backend: "We're looking for a Senior Backend Engineer with 4+ years of experience in Python, Django, and PostgreSQL. The role involves designing microservices, leading code reviews, building scalable REST APIs, and collaborating cross-functionally with product teams.",
  frontend: "Looking for a Lead Frontend Engineer proficient in React, Modern JavaScript (ES6+), CSS Architecture, and UI performance optimization. Must have experience building interactive web applications with dynamic visual design and state management.",
  data: "Seeking a Data Scientist / AI Engineer with strong experience in Python, Machine Learning frameworks, NLP, and LLM orchestration. Responsibilities include building predictive models, data extraction pipelines, and candidate evaluation engines."
};

function fillPreset(type) {
  if (PRESETS[type]) {
    textarea.value = PRESETS[type];
    updateCharCount();
    textarea.focus();
  }
}

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
      <span class="bar-val" data-target="${value}">0</span>
    </div>`;
}

function buildRing(score) {
  const cls   = scoreClass(score);
  const circ  = 163;
  const offset = circ - (score / 100) * circ;
  return `
    <div class="score-ring">
      <svg width="64" height="64" viewBox="0 0 64 64">
        <circle class="score-ring-bg" cx="32" cy="32" r="26"/>
        <circle
          class="score-ring-fill ring-${cls}"
          cx="32" cy="32" r="26"
          data-offset="${offset}"
          style="stroke-dashoffset:${circ}"
        />
      </svg>
      <div class="score-label score-${cls}" data-target="${score}">0</div>
    </div>
    <span class="score-tag">Score</span>`;
}

function buildCard(c, idx) {
  const rank = idx + 1;
  return `
    <div class="candidate-card" style="animation-delay:${idx * 0.05}s">
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
  return String(str || '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// Trigger bar / ring animations & number counter tickers after DOM insert
function animateCards() {
  // 1. Bars
  document.querySelectorAll('.bar-fill[data-width]').forEach(el => {
    const w = el.dataset.width;
    requestAnimationFrame(() => { el.style.width = w + '%'; });
  });

  // 2. Rings
  document.querySelectorAll('.score-ring-fill[data-offset]').forEach(el => {
    const off = el.dataset.offset;
    requestAnimationFrame(() => { el.style.strokeDashoffset = off; });
  });

  // 3. Animated Number Counter Tickers
  document.querySelectorAll('[data-target]').forEach(el => {
    const target = parseInt(el.dataset.target, 10);
    if (isNaN(target)) return;

    let start = 0;
    const duration = 900; // ms
    const startTime = performance.now();

    function updateCounter(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out quad
      const easedProgress = 1 - (1 - progress) * (1 - progress);
      const currentVal = Math.floor(easedProgress * target);

      el.textContent = currentVal;

      if (progress < 1) {
        requestAnimationFrame(updateCounter);
      } else {
        el.textContent = target;
      }
    }
    requestAnimationFrame(updateCounter);
  });

  // 4. 3D Perspective Card Tilt
  initCard3DTilt();
}

function initCard3DTilt() {
  document.querySelectorAll('.candidate-card').forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const centerX = rect.width / 2;
      const centerY = rect.height / 2;

      const rotateX = ((y - centerY) / centerY) * -4; // Max 4 deg
      const rotateY = ((x - centerX) / centerX) * 4;

      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-2px)`;
    });

    card.addEventListener('mouseleave', () => {
      card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px)';
    });
  });
}

// ── Filtering & Sorting Logic ──────────────────────────────────
function setFilterPill(btn, filterVal) {
  activeFilterPill = filterVal;
  document.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  onFilterChange();
}

function onFilterChange() {
  if (!rawCandidates || rawCandidates.length === 0) return;

  const searchInput = document.getElementById('search-input');
  const query       = (searchInput ? searchInput.value : '').toLowerCase().trim();
  const sortSelect  = document.getElementById('sort-select');
  const sortKey     = sortSelect ? sortSelect.value : 'total_score';

  // 1. Filter candidates
  let filtered = rawCandidates.filter(c => {
    const nameMatch   = (c.name || '').toLowerCase().includes(query);
    const reasonMatch = (c.reason || '').toLowerCase().includes(query);
    const matchesSearch = !query || nameMatch || reasonMatch;

    let matchesScore = true;
    if (activeFilterPill === 'top') matchesScore = (c.total_score >= 80);
    else if (activeFilterPill === 'mid') matchesScore = (c.total_score >= 60);

    return matchesSearch && matchesScore;
  });

  // 2. Sort candidates
  filtered.sort((a, b) => (b[sortKey] || 0) - (a[sortKey] || 0));

  // 3. Render
  renderCandidates(filtered, rawCandidates.length);
}

function renderCandidates(list, totalCount) {
  const resultsCountEl = document.getElementById('results-count');
  const resultsListEl  = document.getElementById('results-list');

  if (resultsCountEl) {
    if (list.length === totalCount) {
      resultsCountEl.textContent = `${totalCount} candidate${totalCount !== 1 ? 's' : ''}`;
    } else {
      resultsCountEl.textContent = `Showing ${list.length} of ${totalCount} candidates`;
    }
  }

  if (!resultsListEl) return;

  if (list.length === 0) {
    resultsListEl.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🔍</div>
        <div class="empty-title">No candidates match your filter</div>
        <div class="empty-sub">Try adjusting your search query or score filter pills.</div>
      </div>`;
    return;
  }

  resultsListEl.innerHTML = list.map((c, i) => buildCard(c, i)).join('');
  setTimeout(animateCards, 60);
}

// ── Main ranking function with live telemetry ─────────────────
async function rankCandidates() {
  const jd = textarea.value.trim();

  // Clear state
  document.getElementById('error-box').style.display      = 'none';
  document.getElementById('results-header').style.display   = 'none';
  document.getElementById('results-list').innerHTML       = '';

  if (!jd) {
    showError('Please paste a job description before searching.');
    return;
  }

  // Loading & Telemetry status simulation
  const btn = document.getElementById('rank-btn');
  btn.disabled = true;

  const telemetrySteps = [
    { btn: '<span class="btn-icon">⚡</span> Extracting Requirements...', title: 'Extracting Requirements...' },
    { btn: '<span class="btn-icon">🔍</span> Scanning Candidate Database...', title: 'Scanning Candidate Database...' },
    { btn: '<span class="btn-icon">🧠</span> Scoring via Groq AI...', title: 'Scoring Candidates with Groq LLM...' },
    { btn: '<span class="btn-icon">📊</span> Generating Rank Order...', title: 'Generating Final Rank Order...' }
  ];
  let stepIdx = 0;
  const loaderTitle = document.getElementById('loader-status-title');

  btn.innerHTML = telemetrySteps[stepIdx].btn;
  if (loaderTitle) loaderTitle.textContent = telemetrySteps[stepIdx].title;

  const telemetryInterval = setInterval(() => {
    stepIdx = (stepIdx + 1) % telemetrySteps.length;
    btn.innerHTML = telemetrySteps[stepIdx].btn;
    if (loaderTitle) loaderTitle.textContent = telemetrySteps[stepIdx].title;
  }, 1200);

  document.getElementById('skeleton-list').style.display = 'flex';

  try {
    const res = await fetch('/api/rank', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ job_description: jd }),
    });

    if (!res.ok) throw new Error(`Server error ${res.status}`);

    const data = await res.json();

    if (!data.success) throw new Error(data.message || 'Ranking failed.');

    rawCandidates = data.candidates || [];

    // Reset controls to defaults
    const searchInput = document.getElementById('search-input');
    if (searchInput) searchInput.value = '';
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) sortSelect.value = 'total_score';

    // Show results section and apply initial render
    document.getElementById('results-header').style.display = 'flex';
    onFilterChange();

    // Smooth scroll to results
    document.getElementById('results-header').scrollIntoView({ behavior: 'smooth', block: 'start' });

  } catch (err) {
    showError(err.message || 'Could not connect to the ranking service. Make sure the Flask server is running on port 5000.');
  } finally {
    clearInterval(telemetryInterval);
    document.getElementById('skeleton-list').style.display = 'none';
    btn.disabled = false;
    btn.innerHTML = '<span class="btn-icon">✨</span> Find Top Candidates';
  }
}

function showError(msg) {
  const box = document.getElementById('error-box');
  document.getElementById('error-msg').textContent = msg;
  box.style.display = 'flex';
}

// ── Export Report Functions ────────────────────────────────────
function exportToExcel() {
  if (!rawCandidates || rawCandidates.length === 0) {
    alert("No candidates loaded to export!");
    return;
  }

  const jdText = textarea.value.trim();

  // Construct sheet layout
  const data = [];
  data.push(["RankAI - AI Candidate Ranking Report"]);
  data.push(["Generated At:", new Date().toLocaleString()]);
  data.push([]); // spacer

  data.push(["Job Description Details:"]);
  data.push([jdText]);
  data.push([]); // spacer

  data.push([
    "Rank",
    "Candidate Name",
    "Total Score",
    "Skills Score",
    "Experience Score",
    "Growth Score",
    "AI Evaluation Reason"
  ]);

  rawCandidates.forEach((c, index) => {
    data.push([
      index + 1,
      c.name || "Unknown",
      c.total_score || 0,
      c.skills_score || 0,
      c.experience_score || 0,
      c.growth_score || 0,
      c.reason || ""
    ]);
  });

  const ws = XLSX.utils.aoa_to_sheet(data);
  ws['!cols'] = [
    { wch: 8 },   // Rank
    { wch: 24 },  // Candidate Name
    { wch: 12 },  // Total Score
    { wch: 12 },  // Skills
    { wch: 12 },  // Experience
    { wch: 12 },  // Growth
    { wch: 80 }   // AI Reason
  ];

  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Candidate Rankings");
  XLSX.writeFile(wb, "AI_Candidate_Rankings.xlsx");
}

function exportToPDF() {
  if (!rawCandidates || rawCandidates.length === 0) {
    alert("No candidates loaded to export!");
    return;
  }

  const jdText = textarea.value.trim();
  const dateStr = new Date().toLocaleString();

  const container = document.createElement('div');
  container.className = 'pdf-report';

  // 1. Header
  const header = document.createElement('div');
  header.className = 'pdf-header';
  header.innerHTML = `
    <div class="pdf-logo">⚡ RankAI</div>
    <div class="pdf-meta">
      <strong>Evaluation Report</strong><br/>
      Date: ${dateStr}<br/>
      Source: Groq AI Ranker
    </div>
  `;
  container.appendChild(header);

  // 2. Job Description Section
  const jdSection = document.createElement('div');
  jdSection.className = 'pdf-section';
  jdSection.innerHTML = `
    <div class="pdf-section-title">Job Description Details</div>
    <div class="pdf-jd-box">${escapeHTML(jdText)}</div>
  `;
  container.appendChild(jdSection);

  // 3. Summary Table Section
  const summarySection = document.createElement('div');
  summarySection.className = 'pdf-section';
  
  let tableRows = '';
  rawCandidates.forEach((c, index) => {
    const total = c.total_score || 0;
    const scoreCls = scoreClass(total);
    tableRows += `
      <tr>
        <td><strong>#${index + 1}</strong></td>
        <td><strong>${escapeHTML(c.name)}</strong></td>
        <td class="pdf-badge-score ${scoreCls}">${total}</td>
        <td>${c.skills_score || 0}</td>
        <td>${c.experience_score || 0}</td>
        <td>${c.growth_score || 0}</td>
      </tr>
    `;
  });

  summarySection.innerHTML = `
    <div class="pdf-section-title">Ranked Candidate Summary</div>
    <table class="pdf-table">
      <thead>
        <tr>
          <th>Rank</th>
          <th>Name</th>
          <th>Total Score</th>
          <th>Skills</th>
          <th>Experience</th>
          <th>Growth</th>
        </tr>
      </thead>
      <tbody>
        ${tableRows}
      </tbody>
    </table>
  `;
  container.appendChild(summarySection);

  // 4. Candidate Details Section (forces page break)
  const detailSection = document.createElement('div');
  detailSection.className = 'pdf-section';
  detailSection.style.pageBreakBefore = 'always';
  
  let detailsHtml = '<div class="pdf-section-title">Detailed Candidate Evaluations</div>';
  rawCandidates.forEach((c, index) => {
    detailsHtml += `
      <div class="pdf-candidate-detail">
        <div class="pdf-candidate-name">#${index + 1} - ${escapeHTML(c.name)}</div>
        <div class="pdf-candidate-scores">
          <span>Overall: ${c.total_score || 0}</span> | 
          <span>Skills: ${c.skills_score || 0}</span> | 
          <span>Experience: ${c.experience_score || 0}</span> | 
          <span>Growth: ${c.growth_score || 0}</span>
        </div>
        <div class="pdf-candidate-reason">${escapeHTML(c.reason)}</div>
      </div>
    `;
  });
  detailSection.innerHTML = detailsHtml;
  container.appendChild(detailSection);

  // Options for html2pdf
  const opt = {
    margin:       10,
    filename:     'AI_Candidate_Rank_Report.pdf',
    image:        { type: 'jpeg', quality: 0.98 },
    html2canvas:  { scale: 2, useCORS: true },
    jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
  };

  html2pdf().set(opt).from(container).save().catch(err => {
    console.error('PDF generation error:', err);
    alert('Failed to generate PDF.');
  });
}

// Allow Enter shortcut (Ctrl/Cmd+Enter in textarea)
textarea.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') rankCandidates();
});