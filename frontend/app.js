/**
 * app.js — AI Recipe Inventor frontend logic
 *
 * Responsibilities:
 *  - Tag-based ingredient input (Enter / comma to add,  to remove)
 *  - Quick suggestion buttons
 *  - Fetch /api/stats and /api/cuisines on load
 *  - POST /api/invent → render animated recipe cards
 *  - Collapsible Steps / Explanation / Tips sections
 *  - "Show all steps" toggle inside cards
 *  - Loading + error states
 */

'use strict';

const API = window.location.protocol.startsWith('http') ? window.location.origin : 'http://127.0.0.1:8000';

// ── Element refs ──────────────────────────────────────────────────────────
const tagContainer     = document.getElementById('tagContainer');
const ingredientInput  = document.getElementById('ingredientInput');
const clearBtn         = document.getElementById('clearBtn');
const inventBtn        = document.getElementById('inventBtn');
const btnLoader        = document.getElementById('btnLoader');
const cuisineFilter    = document.getElementById('cuisineFilter');
const difficultyFilter = document.getElementById('difficultyFilter');
const maxTimeFilter    = document.getElementById('maxTimeFilter');
const numRecipesRange  = document.getElementById('numRecipesRange');
const numRecipesVal    = document.getElementById('numRecipesVal');
const inputPanel       = document.getElementById('inputPanel');
const loadingOverlay   = document.getElementById('loadingOverlay');
const resultsSection   = document.getElementById('resultsSection');
const recipesGrid      = document.getElementById('recipesGrid');
const resultsMeta      = document.getElementById('resultsMeta');
const backBtn          = document.getElementById('backBtn');
const errorBox         = document.getElementById('errorBox');
const errorMsg         = document.getElementById('errorMsg');
const errorBackBtn     = document.getElementById('errorBackBtn');
const loadDbCount      = document.getElementById('loadDbCount');

// ── State ─────────────────────────────────────────────────────────────────
let tags = [];  // current ingredient tags

// ── Init ──────────────────────────────────────────────────────────────────
async function init() {
  await Promise.all([fetchStats(), fetchCuisines()]);
  bindEvents();
  initPlayground();
}

// ── Fetch stats ───────────────────────────────────────────────────────────
async function fetchStats() {
  try {
    const res  = await fetch(`${API}/api/stats`);
    const data = await res.json();
    document.getElementById('statRecipes').textContent  = data.total_recipes?.toLocaleString('ro') ?? '—';
    document.getElementById('statCuisines').textContent = data.cuisines ?? '—';
    document.getElementById('statAvgIng').textContent   = data.avg_ingredients ?? '—';
    if (loadDbCount) loadDbCount.textContent = data.total_recipes?.toLocaleString('ro') ?? '300+';
  } catch {
    /* silently ignore — stats are decorative */
  }
}

// ── Fetch cuisines ────────────────────────────────────────────────────────
async function fetchCuisines() {
  try {
    const res  = await fetch(`${API}/api/cuisines`);
    const list = await res.json();
    list.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c;
      opt.textContent = ` ${c}`;
      cuisineFilter.appendChild(opt);
    });
  } catch {
    /* ignore */
  }
}

// ── Tag management ────────────────────────────────────────────────────────
function addTag(raw) {
  const value = raw.trim().toLowerCase().replace(/,$/, '');
  if (!value || tags.includes(value)) return;
  tags.push(value);
  renderTags();
}

function removeTag(value) {
  tags = tags.filter(t => t !== value);
  renderTags();
}

function renderTags() {
  // Remove existing chips (not the input element)
  tagContainer.querySelectorAll('.tag-chip').forEach(el => el.remove());

  // Insert chips before the input
  tags.forEach(tag => {
    const chip = document.createElement('span');
    chip.className = 'tag-chip';
    chip.textContent = tag;
    const btn = document.createElement('button');
    btn.className = 'tag-remove';
    btn.type = 'button';
    btn.textContent = '';
    btn.setAttribute('aria-label', `Elimină ${tag}`);
    btn.addEventListener('click', () => removeTag(tag));
    chip.appendChild(btn);
    tagContainer.insertBefore(chip, ingredientInput);
  });
}

// ── Events ────────────────────────────────────────────────────────────────
function bindEvents() {
  // Tag container click → focus input
  tagContainer.addEventListener('click', () => ingredientInput.focus());

  // Ingredient input
  ingredientInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      const val = ingredientInput.value.trim().replace(/,$/, '');
      if (val) { addTag(val); ingredientInput.value = ''; }
    }
    if (e.key === 'Backspace' && !ingredientInput.value && tags.length) {
      removeTag(tags[tags.length - 1]);
    }
  });

  // On blur, commit partial input
  ingredientInput.addEventListener('blur', () => {
    const val = ingredientInput.value.trim().replace(/,$/, '');
    if (val) { addTag(val); ingredientInput.value = ''; }
  });

  // Clear all
  clearBtn.addEventListener('click', () => {
    tags = [];
    ingredientInput.value = '';
    renderTags();
    ingredientInput.focus();
  });

  // Quick suggestions
  document.querySelectorAll('.sugg-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      tags = [];
      const ings = btn.dataset.ingredients.split(',').map(s => s.trim());
      ings.forEach(i => addTag(i));
      ingredientInput.focus();
    });
  });

  // Num recipes range
  numRecipesRange.addEventListener('input', () => {
    numRecipesVal.textContent = numRecipesRange.value;
  });

  // Invent
  inventBtn.addEventListener('click', handleInvent);

  // Back buttons
  backBtn.addEventListener('click', showInputPanel);
  errorBackBtn.addEventListener('click', showInputPanel);

  // Creator Advanced RAG settings bindings
  const creatorRagMethod = document.getElementById('creatorRagMethod');
  const creatorRagAlpha = document.getElementById('creatorRagAlpha');
  const creatorAlphaVal = document.getElementById('creatorAlphaVal');
  const creatorAlphaGroup = document.getElementById('creatorAlphaGroup');
  const creatorRagThreshold = document.getElementById('creatorRagThreshold');
  const creatorThresholdVal = document.getElementById('creatorThresholdVal');
  const creatorMmrCheck = document.getElementById('creatorMmrCheck');
  const creatorMmrLambdaGroup = document.getElementById('creatorMmrLambdaGroup');
  const creatorMmrLambdaRange = document.getElementById('creatorMmrLambdaRange');
  const creatorMmrLambdaVal = document.getElementById('creatorMmrLambdaVal');

  if (creatorRagMethod) {
    window.toggleRagSettings = function() {
      const body = document.getElementById('ragSettingsBody');
      const arrow = document.getElementById('ragToggleArrow');
      if (!body) return;
      const isHidden = body.style.display === 'none' || body.style.display === '';
      if (isHidden) {
        body.style.display = 'block';
        arrow.textContent = '▲';
      } else {
        body.style.display = 'none';
        arrow.textContent = '▼';
      }
    };

    creatorRagAlpha.addEventListener('input', () => {
      creatorAlphaVal.textContent = parseFloat(creatorRagAlpha.value).toFixed(2);
    });

    creatorRagThreshold.addEventListener('input', () => {
      creatorThresholdVal.textContent = parseFloat(creatorRagThreshold.value).toFixed(2);
    });

    creatorMmrLambdaRange.addEventListener('input', () => {
      creatorMmrLambdaVal.textContent = parseFloat(creatorMmrLambdaRange.value).toFixed(2);
    });

    creatorMmrCheck.addEventListener('change', () => {
      const checked = creatorMmrCheck.checked;
      if (checked) {
        creatorMmrLambdaGroup.classList.remove('dimmed');
        creatorMmrLambdaGroup.style.opacity = '1';
        creatorMmrLambdaGroup.style.pointerEvents = 'auto';
      } else {
        creatorMmrLambdaGroup.classList.add('dimmed');
        creatorMmrLambdaGroup.style.opacity = '0.5';
        creatorMmrLambdaGroup.style.pointerEvents = 'none';
      }
    });

    creatorRagMethod.addEventListener('change', () => {
      const m = creatorRagMethod.value;
      if (m === 'sparse' || m === 'dense') {
        creatorAlphaGroup.style.opacity = '0.3';
        creatorAlphaGroup.style.pointerEvents = 'none';
      } else {
        creatorAlphaGroup.style.opacity = '1';
        creatorAlphaGroup.style.pointerEvents = 'auto';
      }
    });
  }

  // ── Fridge Photo Upload & Detector ──────────────────────────────────────
  const fridgeUploadInput = document.getElementById('fridgeUploadInput');
  const fridgeUploadStatus = document.getElementById('fridgeUploadStatus');
  const fridgePreviewContainer = document.getElementById('fridgePreviewContainer');
  const fridgeImagePreview = document.getElementById('fridgeImagePreview');
  const detectedIngredientsList = document.getElementById('detectedIngredientsList');
  const importDetectedBtn = document.getElementById('importDetectedBtn');
  let detectedIngredients = [];

  if (fridgeUploadInput) {
    fridgeUploadInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      if (fridgeUploadStatus) fridgeUploadStatus.textContent = `Se incarca: ${file.name}`;
      
      const reader = new FileReader();
      reader.onload = (event) => {
        if (fridgeImagePreview) fridgeImagePreview.src = event.target.result;
      };
      reader.readAsDataURL(file);

      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await fetch(`${API}/api/playground/upload_fridge`, {
          method: 'POST',
          body: formData
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();

        detectedIngredients = data.ingredients || [];
        if (fridgeUploadStatus) fridgeUploadStatus.textContent = `Detectat cu succes: ${file.name}`;
        
        if (fridgePreviewContainer) fridgePreviewContainer.style.display = 'grid';

        if (detectedIngredientsList) {
          if (detectedIngredients.length === 0) {
            detectedIngredientsList.innerHTML = '<span style="font-size: 0.8rem; color: var(--text-dim); font-style: italic;">Nu s-au detectat ingrediente cunoscute.</span>';
          } else {
            detectedIngredientsList.innerHTML = detectedIngredients.map(ing => `
              <span class="ing-chip user-ing" style="padding: 4px 10px; border-radius: var(--radius-sm); font-size: 0.8rem;">
                ${esc(ing)}
              </span>
            `).join('');
          }
        }
      } catch (error) {
        console.error('Eroare detectie obiecte:', error);
        if (fridgeUploadStatus) fridgeUploadStatus.textContent = 'Eroare la procesarea imaginii.';
      }
    });
  }

  if (importDetectedBtn) {
    importDetectedBtn.addEventListener('click', () => {
      if (detectedIngredients.length > 0) {
        detectedIngredients.forEach(ing => {
          if (!tags.includes(ing.toLowerCase())) {
            addTag(ing.toLowerCase());
          }
        });
        if (fridgePreviewContainer) fridgePreviewContainer.style.display = 'none';
        if (fridgeUploadInput) fridgeUploadInput.value = '';
        if (fridgeUploadStatus) fridgeUploadStatus.textContent = 'Nicio imagine selectata';
        detectedIngredients = [];
      }
    });
  }
}

// ── Invent ────────────────────────────────────────────────────────────────
async function handleInvent() {
  // Commit any pending input
  const pending = ingredientInput.value.trim().replace(/,$/, '');
  if (pending) { addTag(pending); ingredientInput.value = ''; }

  if (tags.length === 0) {
    ingredientInput.placeholder = ' Adaugă măcar un ingredient!';
    ingredientInput.focus();
    setTimeout(() => { ingredientInput.placeholder = 'Ex: pui, usturoi, lămâie… apasă Enter'; }, 2500);
    return;
  }

  showLoading();

  const payload = {
    ingredients:  tags,
    cuisine:      cuisineFilter.value,
    difficulty:   difficultyFilter.value,
    max_time:     maxTimeFilter.value ? parseInt(maxTimeFilter.value) : null,
    num_recipes:  parseInt(numRecipesRange.value),
    rag_method:   document.getElementById('creatorRagMethod').value,
    rag_alpha:    parseFloat(document.getElementById('creatorRagAlpha').value),
    rag_threshold:parseFloat(document.getElementById('creatorRagThreshold').value),
    use_mmr:      document.getElementById('creatorMmrCheck').checked,
    mmr_lambda:   parseFloat(document.getElementById('creatorMmrLambdaRange').value),
  };

  try {
    const res  = await fetch(`${API}/api/invent`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Eroare necunoscută.' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();
    showResults(data);
  } catch (err) {
    showError(err.message || 'Nu m-am putut conecta la server. Verifică că backend-ul rulează.');
  }
}

// ── Print Agent Logs to Terminal ──────────────────────────────────────────
function printLogsToTerminal(logs, callback) {
  const container = document.getElementById('agentTerminalContainer');
  const terminal = document.getElementById('agentTerminal');
  if (!container || !terminal || !logs || logs.length === 0) {
    if (container) container.classList.add('hidden');
    callback();
    return;
  }
  
  container.classList.remove('hidden');
  terminal.innerHTML = '';
  
  let lineIdx = 0;
  function printNextLine() {
    if (lineIdx < logs.length) {
      const lineText = logs[lineIdx];
      const p = document.createElement('div');
      p.className = 'agent-terminal-line';
      
      // Color-coding log prefixes
      if (lineText.includes('') || lineText.includes('successful')) {
        p.style.color = '#34d399';
      } else if (lineText.includes('️') || lineText.includes('too low') || lineText.includes('Self-critique')) {
        p.style.color = '#fbbf24';
      } else if (lineText.includes('[Iteration')) {
        p.style.color = '#60a5fa';
      } else if (lineText.includes('Dropped') || lineText.includes('Dropping') || lineText.includes('Aborting')) {
        p.style.color = '#f87171';
      }
      
      p.textContent = `> ${lineText}`;
      terminal.appendChild(p);
      terminal.scrollTop = terminal.scrollHeight;
      lineIdx++;
      
      // Fast print for long logs
      const delay = lineText.includes('Iteration') ? 400 : 150;
      setTimeout(printNextLine, delay);
    } else {
      // Add cursor
      const cursorLine = document.createElement('div');
      cursorLine.className = 'agent-terminal-line';
      cursorLine.innerHTML = `> Agent execution completed. Found optimal recipe match. <span class="agent-terminal-cursor"></span>`;
      terminal.appendChild(cursorLine);
      terminal.scrollTop = terminal.scrollHeight;
      
      setTimeout(callback, 400);
    }
  }
  printNextLine();
}

// ── Render results ────────────────────────────────────────────────────────
function showResults(data) {
  recipesGrid.innerHTML = '';
  loadingOverlay.classList.add('hidden');
  resultsSection.classList.remove('hidden');

  resultsMeta.textContent =
    `${data.recipes.length} rețete inventate • bazate pe ${data.retrieved_count} rețete similare ` +
    `din baza de date de ${data.total_db?.toLocaleString('ro') ?? '300+'} intrări`;

  // Print agent thinking logs, then show cards
  printLogsToTerminal(data.agent_logs, () => {
    // Initialize current recipes for shopping list
    window.currentRecipes = data.recipes || [];

    data.recipes.forEach((recipe, idx) => {
      const card = buildCard(recipe, idx, data.query || tags);
      recipesGrid.appendChild(card);
    });
  });
}

// ── Build a recipe card DOM element ──────────────────────────────────────
function buildCard(recipe, idx, userIngredients) {
  const card = document.createElement('article');
  card.className = 'recipe-card';
  card.style.animationDelay = `${idx * 0.08}s`;

  const diffClass = {
    'Easy':   'badge-easy',
    'Medium': 'badge-medium',
    'Hard':   'badge-hard',
  }[recipe.difficulty] || 'badge-medium';

  const diffEmoji = { 'Easy': '', 'Medium': '', 'Hard': '' }[recipe.difficulty] || '';

  const userSet = new Set(userIngredients.map(i => i.toLowerCase().trim()));

  // Ingredients HTML
  const ingHTML = (recipe.ingredients || []).map(ing => {
    const isUser = [...userSet].some(u => ing.toLowerCase().includes(u) || u.includes(ing.toLowerCase()));
    return `<span class="ing-chip ${isUser ? 'user-ing' : ''}">${esc(ing)}</span>`;
  }).join('');

  // Steps HTML (show first 3, rest collapsible)
  const steps      = recipe.steps || [];
  const visSteps   = steps.slice(0, 3);
  const extraSteps = steps.slice(3);

  const stepsHTML = visSteps.map((s, i) =>
    `<div class="step-item">
       <span class="step-num">${i + 1}</span>
       <p class="step-text">${esc(s)}</p>
     </div>`
  ).join('');

  const extraHTML = extraSteps.map((s, i) =>
    `<div class="step-item">
       <span class="step-num">${i + 4}</span>
       <p class="step-text">${esc(s)}</p>
     </div>`
  ).join('');

  // Flavor profile tags
  const flavorHTML = (recipe.flavor_profile || []).slice(0, 5).map(f =>
    `<span class="flavor-tag">${esc(f)}</span>`
  ).join('');

  // Tips HTML
  const tipsHTML = (recipe.tips || []).map(t =>
    `<div class="tip-item">${esc(t)}</div>`
  ).join('');

  // Nutrition Label HTML
  const nutr = recipe.nutrition || { calories: 350, protein: '15g', carbs: '45g', fat: '10g' };
  const nutritionHTML = `
    <div class="nutrition-grid">
      <div class="nutrition-item">
        <span class="nutrition-val">${nutr.calories}</span>
        <span class="nutrition-lbl">Kcal</span>
      </div>
      <div class="nutrition-item">
        <span class="nutrition-val">${nutr.protein}</span>
        <span class="nutrition-lbl">Proteine</span>
      </div>
      <div class="nutrition-item">
        <span class="nutrition-val">${nutr.carbs}</span>
        <span class="nutrition-lbl">Carbi</span>
      </div>
      <div class="nutrition-item">
        <span class="nutrition-val">${nutr.fat}</span>
        <span class="nutrition-lbl">Lipide</span>
      </div>
    </div>
  `;

  // Flavor Profile Grid HTML
  const flav = recipe.flavor_percentages || { sweet: 20, sour: 20, salty: 20, spicy: 10, creamy: 15, umami: 15 };
  const flavorGridHTML = `
    <div class="flavor-profile-grid">
      <div class="flavor-profile-item">
        <div class="flavor-profile-header">
          <span class="flavor-profile-name">Dulce</span>
          <span class="flavor-profile-pct">${flav.sweet}%</span>
        </div>
        <div class="flavor-bar-bg">
          <div class="flavor-bar-fill fill-sweet" style="width: ${flav.sweet}%"></div>
        </div>
      </div>
      <div class="flavor-profile-item">
        <div class="flavor-profile-header">
          <span class="flavor-profile-name">Acru</span>
          <span class="flavor-profile-pct">${flav.sour}%</span>
        </div>
        <div class="flavor-bar-bg">
          <div class="flavor-bar-fill fill-sour" style="width: ${flav.sour}%"></div>
        </div>
      </div>
      <div class="flavor-profile-item">
        <div class="flavor-profile-header">
          <span class="flavor-profile-name">Sărat</span>
          <span class="flavor-profile-pct">${flav.salty}%</span>
        </div>
        <div class="flavor-bar-bg">
          <div class="flavor-bar-fill fill-salty" style="width: ${flav.salty}%"></div>
        </div>
      </div>
      <div class="flavor-profile-item">
        <div class="flavor-profile-header">
          <span class="flavor-profile-name">Iute</span>
          <span class="flavor-profile-pct">${flav.spicy}%</span>
        </div>
        <div class="flavor-bar-bg">
          <div class="flavor-bar-fill fill-spicy" style="width: ${flav.spicy}%"></div>
        </div>
      </div>
      <div class="flavor-profile-item">
        <div class="flavor-profile-header">
          <span class="flavor-profile-name">Cremos</span>
          <span class="flavor-profile-pct">${flav.creamy}%</span>
        </div>
        <div class="flavor-bar-bg">
          <div class="flavor-bar-fill fill-creamy" style="width: ${flav.creamy}%"></div>
        </div>
      </div>
      <div class="flavor-profile-item">
        <div class="flavor-profile-header">
          <span class="flavor-profile-name">Umami</span>
          <span class="flavor-profile-pct">${flav.umami}%</span>
        </div>
        <div class="flavor-bar-bg">
          <div class="flavor-bar-fill fill-umami" style="width: ${flav.umami}%"></div>
        </div>
      </div>
    </div>
  `;

  const platingHTML = recipe.plating_guide ? `
    <div style="margin-top: 12px;">
      <span style="color: var(--cyan); font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; display: block;"> Chef's Plating Guide</span>
      <div class="plating-box">${esc(recipe.plating_guide)}</div>
    </div>
  ` : '';

  const pairingHTML = recipe.beverage_pairing ? `
    <div style="margin-top: 12px;">
      <span style="color: var(--amber); font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; display: block;"> Sommelier Beverage Pairing</span>
      <div class="pairing-box">${esc(recipe.beverage_pairing)}</div>
    </div>
  ` : '';

  card.innerHTML = `
    <div class="card-stripe"></div>
    <div class="card-body">

      <h3 class="card-title">${esc(recipe.title)}</h3>

      <div class="badges">
        <span class="badge badge-cuisine"> ${esc(recipe.cuisine)}</span>
        <span class="badge ${diffClass}">${diffEmoji} ${esc(recipe.difficulty)}</span>
        <span class="badge badge-time">⏱ ${recipe.time_minutes} min</span>
        <span class="badge badge-servings"> ${recipe.servings} porții</span>
      </div>

      <!-- Nutrition label -->
      ${nutritionHTML}

      <!-- Ingredients -->
      <div class="card-section">
        <div class="section-header">
          <span> Ingrediente (${recipe.ingredients?.length ?? 0})</span>
        </div>
        <div class="ingredients-list">${ingHTML}</div>
      </div>

      <!-- Steps -->
      <div class="card-section">
        <div class="section-header toggle-header" data-target="steps-${idx}">
          <span> Pași de preparare</span>
          <span class="toggle-icon">▼</span>
        </div>
        <div class="collapsible open" id="steps-${idx}">
          <div class="steps-list">
            ${stepsHTML}
            ${extraSteps.length ? `
              <div class="collapsible" id="extra-steps-${idx}">
                <div class="steps-list">${extraHTML}</div>
              </div>
              <button class="show-more-btn" id="show-more-${idx}" type="button">
                + Arată toți ${steps.length} pașii
              </button>` : ''}
          </div>
        </div>
      </div>

      <!-- Explanation -->
      <div class="card-section">
        <div class="section-header toggle-header" data-target="expl-${idx}">
          <span> De ce funcționează?</span>
          <span class="toggle-icon">▼</span>
        </div>
        <div class="collapsible open" id="expl-${idx}">
          <div class="explanation-box">${formatExplanation(recipe.explanation)}</div>
          ${recipe.cuisine_note ? `<p class="cuisine-note">${esc(recipe.cuisine_note)}</p>` : ''}
        </div>
      </div>

      <!-- Culinary Analysis -->
      <div class="card-section">
        <div class="section-header toggle-header" data-target="analysis-${idx}">
          <span>‍ Analiză Culinară & Sommelier</span>
          <span class="toggle-icon">▼</span>
        </div>
        <div class="collapsible" id="analysis-${idx}">
          <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 8px;">Scor profil de arome echilibrat:</div>
          ${flavorGridHTML}
          ${platingHTML}
          ${pairingHTML}
        </div>
      </div>

      <!-- Tips -->
      ${tipsHTML ? `
      <div class="card-section">
        <div class="section-header toggle-header" data-target="tips-${idx}">
          <span> Sfaturi pro</span>
          <span class="toggle-icon">▼</span>
        </div>
        <div class="collapsible" id="tips-${idx}">
          <div class="tips-list">${tipsHTML}</div>
        </div>
      </div>` : ''}

      <!-- Flavor profile -->
      ${flavorHTML ? `<div class="flavor-row">${flavorHTML}</div>` : ''}

      <!-- Inspired by -->
      <p class="inspired-by">
         Inspirat din: <em>${esc(recipe.inspired_by || '—')}</em>
        ${recipe.key_technique ? `· Tehnică cheie: <em>${esc(recipe.key_technique)}</em>` : ''}
      </p>

      <!-- Shopping List Button -->
      <div class="card-section" style="margin-top: 20px; display: flex; gap: 8px;">
        <button class="btn-invent" onclick="addToShoppingList(${idx})" style="flex: 1; padding: 10px 16px;">
           Adaugă la Shopping
        </button>
      </div>

    </div>
  `;

  // Bind toggle events after inserting into DOM
  requestAnimationFrame(() => {
    // Section toggles
    card.querySelectorAll('.toggle-header').forEach(header => {
      const targetId = header.dataset.target;
      const target   = card.querySelector(`#${targetId}`);
      if (!target) return;
      header.addEventListener('click', () => {
        const open = target.classList.toggle('open');
        header.classList.toggle('open', open);
      });
      // Start as open
      header.classList.add('open');
    });

    // Show more steps
    const showMoreBtn = card.querySelector(`#show-more-${idx}`);
    if (showMoreBtn) {
      const extraEl = card.querySelector(`#extra-steps-${idx}`);
      showMoreBtn.addEventListener('click', () => {
        const open = extraEl.classList.toggle('open');
        showMoreBtn.textContent = open
          ? `− Ascunde pașii extra`
          : `+ Arată toți ${steps.length} pașii`;
      });
    }
  });

  return card;
}

// ── Helpers ───────────────────────────────────────────────────────────────
function esc(str) {
  if (typeof str !== 'string') return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatExplanation(text) {
  if (!text) return '';
  // Bold the "Why X, Y, Z work together:" prefix
  return esc(text).replace(
    /^(Why [^:]+:)\s*/,
    '<strong>$1</strong> '
  );
}

// ── View transitions ──────────────────────────────────────────────────────
function showLoading() {
  inputPanel.classList.add('hidden');
  resultsSection.classList.add('hidden');
  errorBox.classList.add('hidden');
  loadingOverlay.classList.remove('hidden');

  inventBtn.disabled = true;
  btnLoader.classList.remove('hidden');
  inventBtn.querySelector('.btn-text').textContent = 'Se procesează…';
}

function showInputPanel() {
  loadingOverlay.classList.add('hidden');
  resultsSection.classList.add('hidden');
  errorBox.classList.add('hidden');
  inputPanel.classList.remove('hidden');

  inventBtn.disabled = false;
  btnLoader.classList.add('hidden');
  inventBtn.querySelector('.btn-text').textContent = 'Inventează Rețete!';
}

function showError(msg) {
  loadingOverlay.classList.add('hidden');
  resultsSection.classList.add('hidden');
  inputPanel.classList.add('hidden');
  errorBox.classList.remove('hidden');
  errorMsg.textContent = msg;

  inventBtn.disabled = false;
  btnLoader.classList.add('hidden');
  inventBtn.querySelector('.btn-text').textContent = 'Inventează Rețete!';
}

// ── RAG Playground ────────────────────────────────────────────────────────
function initPlayground() {
  const playQueryInput      = document.getElementById('playQueryInput');
  const playMethodSelect     = document.getElementById('playMethodSelect');
  const playAlphaRange      = document.getElementById('playAlphaRange');
  const playAlphaVal        = document.getElementById('playAlphaVal');
  const playAlphaGroup      = document.getElementById('playAlphaGroup');
  const playThresholdRange  = document.getElementById('playThresholdRange');
  const playThresholdVal    = document.getElementById('playThresholdVal');
  const playMmrCheck        = document.getElementById('playMmrCheck');
  const playMmrLambdaGroup  = document.getElementById('playMmrLambdaGroup');
  const playMmrLambdaRange  = document.getElementById('playMmrLambdaRange');
  const playMmrLambdaVal    = document.getElementById('playMmrLambdaVal');
  const playSearchBtn       = document.getElementById('playSearchBtn');
  const playResultsContainer = document.getElementById('playResultsContainer');
  const playResultCount     = document.getElementById('playResultCount');
  const playLatency         = document.getElementById('playLatency');
  const playDiscarded       = document.getElementById('playDiscarded');
  const playQueryUsed       = document.getElementById('playQueryUsed');
  const playResultsGrid     = document.getElementById('playResultsGrid');

  const runBenchmarkBtn     = document.getElementById('runBenchmarkBtn');
  const benchmarkLoader     = document.getElementById('benchmarkLoader');
  const benchmarkResults    = document.getElementById('benchmarkResults');

  const calcSimBtn          = document.getElementById('calcSimBtn');
  const simText1            = document.getElementById('simText1');
  const simText2            = document.getElementById('simText2');
  const simResultVal        = document.getElementById('simResultVal');

  const runModelBenchBtn    = document.getElementById('runModelBenchBtn');
  const modelBenchText      = document.getElementById('modelBenchText');
  const modelBenchResults   = document.getElementById('modelBenchResults');

  const dbQueryText         = document.getElementById('dbQueryText');
  const dbSelectorContainer = document.getElementById('dbSelectorContainer');
  const runDbQueryBtn       = document.getElementById('runDbQueryBtn');
  const dbQueryContainer    = document.getElementById('dbQueryContainer');
  const dbQueryCodeBlock    = document.getElementById('dbQueryCodeBlock');
  const dbQueryOutputBlock  = document.getElementById('dbQueryOutputBlock');
  const dbQueryLatency      = document.getElementById('dbQueryLatency');

  if (!playSearchBtn) return;

  // Sliders binding
  playAlphaRange.addEventListener('input', () => {
    playAlphaVal.textContent = parseFloat(playAlphaRange.value).toFixed(2);
  });

  playThresholdRange.addEventListener('input', () => {
    playThresholdVal.textContent = parseFloat(playThresholdRange.value).toFixed(2);
  });

  playMmrLambdaRange.addEventListener('input', () => {
    playMmrLambdaVal.textContent = parseFloat(playMmrLambdaRange.value).toFixed(2);
  });

  playMmrCheck.addEventListener('change', () => {
    const checked = playMmrCheck.checked;
    if (checked) {
      playMmrLambdaGroup.classList.remove('dimmed');
      playMmrLambdaGroup.style.opacity = '1';
      playMmrLambdaGroup.style.pointerEvents = 'auto';
    } else {
      playMmrLambdaGroup.classList.add('dimmed');
      playMmrLambdaGroup.style.opacity = '0.5';
      playMmrLambdaGroup.style.pointerEvents = 'none';
    }
  });

  playMethodSelect.addEventListener('change', () => {
    const m = playMethodSelect.value;
    if (m === 'sparse' || m === 'dense') {
      playAlphaGroup.style.opacity = '0.3';
      playAlphaGroup.style.pointerEvents = 'none';
    } else {
      playAlphaGroup.style.opacity = '1';
      playAlphaGroup.style.pointerEvents = 'auto';
    }
  });

  // Search execution
  playSearchBtn.addEventListener('click', async () => {
    const query = playQueryInput.value.trim();
    if (!query) return;

    playSearchBtn.disabled = true;
    playSearchBtn.textContent = 'Searching...';

    const payload = {
      query: query,
      method: playMethodSelect.value,
      alpha: parseFloat(playAlphaRange.value),
      threshold: parseFloat(playThresholdRange.value),
      use_mmr: playMmrCheck.checked,
      mmr_lambda: parseFloat(playMmrLambdaRange.value),
      cuisine: "Any",
      difficulty: "Any",
      max_time: null,
      top_k: 5
    };

    try {
      const res = await fetch(`${API}/api/playground/retrieve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      playResultCount.textContent = data.recipes.length;
      playLatency.textContent = data.latency_ms.toFixed(1);
      playDiscarded.textContent = data.discarded_count;
      playQueryUsed.textContent = `"${data.query_expanded}"`;

      if (data.recipes.length === 0) {
        playResultsGrid.innerHTML = `
          <div style="text-align: center; padding: 20px; color: var(--text-muted); font-style: italic;">
            Nicio rețetă nu a trecut pragul de relevanță setat sau filtrele selectate.
          </div>
        `;
      } else {
        playResultsGrid.innerHTML = data.recipes.map((r, idx) => `
          <div class="shopping-item" style="display: flex; flex-direction: column; align-items: stretch; gap: 8px; padding: 16px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: rgba(255,255,255,0.02);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; flex-wrap: wrap;">
              <h4 style="font-size: 1.05rem; font-weight: 600; color: #fff; margin: 0;">${idx + 1}. ${esc(r.title)}</h4>
              <div style="display: flex; gap: 6px; align-items: center;">
                <span style="font-size: 0.75rem; color: var(--text-muted); padding: 2px 6px; background: rgba(255,255,255,0.05); border-radius: 4px; border: 1px solid var(--border);">${esc(r.cuisine)}</span>
                <span style="background: rgba(6,182,212,0.15); color: var(--cyan); font-size: 0.8rem; font-weight: 700; padding: 3px 8px; border-radius: 4px; border: 1px solid rgba(6,182,212,0.25);">Score: ${r.retrieval_score.toFixed(3)}</span>
              </div>
            </div>
            <div style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.4;">${esc(r.description || 'Nicio descriere disponibilă.')}</div>
            <div style="font-size: 0.8rem; color: var(--text-muted);"><span style="color: var(--text-dim); font-weight: 600;">Ingrediente:</span> ${esc(r.ingredients.join(', '))}</div>
            <div style="display: flex; gap: 16px; font-size: 0.75rem; border-top: 1px solid rgba(255,255,255,0.04); padding-top: 8px; margin-top: 4px; flex-wrap: wrap;">
              <span style="color: var(--cyan); display: flex; align-items: center; gap: 4px;"> Dense (Semantic): <strong>${r.semantic_score.toFixed(3)}</strong></span>
              <span style="color: var(--rose-lt); display: flex; align-items: center; gap: 4px;"> Sparse (BM25): <strong>${r.bm25_score.toFixed(3)}</strong></span>
              <span style="color: var(--violet-lt); display: flex; align-items: center; gap: 4px;"> Hybrid Combined: <strong>${r.hybrid_score.toFixed(3)}</strong></span>
            </div>
          </div>
        `).join('');
      }

      playResultsContainer.style.display = 'block';
    } catch (e) {
      console.error(e);
      alert('Eroare la realizarea retrieval-ului.');
    } finally {
      playSearchBtn.disabled = false;
      playSearchBtn.textContent = ' Rulează Retrieval';
    }
  });

  // Benchmark Runner
  runBenchmarkBtn.addEventListener('click', async () => {
    runBenchmarkBtn.disabled = true;
    benchmarkLoader.classList.remove('hidden');
    benchmarkResults.style.display = 'none';

    try {
      const res = await fetch(`${API}/api/playground/benchmark`, {
        method: 'POST'
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const updateMetrics = (prefix, metrics) => {
        document.getElementById(`${prefix}P3`).textContent = (metrics.precision_3 * 100).toFixed(1) + '%';
        document.getElementById(`${prefix}P3Bar`).style.width = (metrics.precision_3 * 100) + '%';

        document.getElementById(`${prefix}P5`).textContent = (metrics.precision_5 * 100).toFixed(1) + '%';
        document.getElementById(`${prefix}P5Bar`).style.width = (metrics.precision_5 * 100) + '%';

        document.getElementById(`${prefix}R5`).textContent = (metrics.recall_5 * 100).toFixed(1) + '%';
        document.getElementById(`${prefix}R5Bar`).style.width = (metrics.recall_5 * 100) + '%';

        document.getElementById(`${prefix}Mrr`).textContent = metrics.mrr.toFixed(3);
        document.getElementById(`${prefix}MrrBar`).style.width = (metrics.mrr * 100) + '%';

        document.getElementById(`${prefix}Latency`).textContent = metrics.latency_ms.toFixed(1) + ' ms';
      };

      updateMetrics('bm25', data.sparse);
      updateMetrics('dense', data.dense);
      updateMetrics('hybrid', data.hybrid);

      benchmarkResults.style.display = 'block';
    } catch (e) {
      console.error(e);
      alert('Eroare la rularea benchmark-ului.');
    } finally {
      runBenchmarkBtn.disabled = false;
      benchmarkLoader.classList.add('hidden');
    }
  });

  // Similarity calculator
  calcSimBtn.addEventListener('click', async () => {
    const t1 = simText1.value.trim();
    const t2 = simText2.value.trim();
    if (!t1 || !t2) return;

    calcSimBtn.disabled = true;
    simResultVal.textContent = '...';
    simResultVal.style.color = 'var(--text-muted)';

    try {
      const res = await fetch(`${API}/api/playground/similarity`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text1: t1, text2: t2 })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const sim = data.similarity;
      simResultVal.textContent = sim.toFixed(4);

      if (sim > 0.6) {
        simResultVal.style.color = 'var(--emerald)';
      } else if (sim > 0.3) {
        simResultVal.style.color = 'var(--amber)';
      } else {
        simResultVal.style.color = 'var(--red)';
      }
    } catch (e) {
      console.error(e);
      simResultVal.textContent = 'Error';
      simResultVal.style.color = 'var(--red)';
    } finally {
      calcSimBtn.disabled = false;
    }
  });

  // ── Database query simulator ────────────────────────────────────────────
  let selectedDb = 'chromadb';

  if (dbSelectorContainer) {
    const dbButtons = dbSelectorContainer.querySelectorAll('button');
    dbButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        dbButtons.forEach(b => {
          b.classList.remove('active-db-btn');
          b.style.background = '';
          b.style.borderColor = '';
          b.style.color = '';
        });
        
        btn.classList.add('active-db-btn');
        btn.style.background = 'rgba(6,182,212,0.15)';
        btn.style.borderColor = 'var(--cyan)';
        btn.style.color = '#fff';
        
        selectedDb = btn.getAttribute('data-db');
        updateDbSyntaxOnly();
      });
    });
  }

  function updateDbSyntaxOnly() {
    const q = dbQueryText ? dbQueryText.value.trim() : 'pui';
    const short_emb_str = "[0.0124, -0.0452, 0.0891, 0.1102, ... (total 384 dim)]";
    
    let code = '';
    if (selectedDb === 'chromadb') {
      code = `# Python SDK (ChromaDB On-Premise)
import chromadb
client = chromadb.PersistentClient(path="data/chroma_db")
collection = client.get_collection("recipes")

query_vector = encoder.encode("${q}").tolist()
results = collection.query(
    query_embeddings=[query_vector],
    n_results=3,
    include=["distances", "metadatas"]
)
print(results)`;
    } else if (selectedDb === 'qdrant') {
      code = `# Python SDK (Qdrant On-Premise)
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)
query_vector = encoder.encode("${q}").tolist()

results = client.search(
    collection_name="recipes",
    query_vector=query_vector,
    limit=3
)
for hit in results:
    print(hit.id, hit.score, hit.payload)`;
    } else if (selectedDb === 'pgvector') {
      code = `-- PostgreSQL with pgvector (SQL Query)
-- Column 'embedding' is vector(384)
-- '<=>' is cosine distance operator

SELECT 
    id, 
    title, 
    cuisine,
    1 - (embedding <=> '${short_emb_str}'::vector) AS similarity
FROM recipes
ORDER BY embedding <=> '${short_emb_str}'::vector
LIMIT 3;`;
    } else {
      code = `# Python SDK (Milvus On-Premise)
from pymilvus import connections, Collection

connections.connect("default", host="localhost", port="19530")
collection = Collection("recipes")

query_vector = encoder.encode("${q}").tolist()
search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}

results = collection.search(
    data=[query_vector],
    anns_field="embedding",
    param=search_params,
    limit=3,
    output_fields=["title", "cuisine"]
)
for hits in results:
    for hit in hits:
        print(hit.id, hit.distance, hit.entity.get('title'))`;
    }
    
    if (dbQueryCodeBlock) {
      dbQueryCodeBlock.textContent = code;
    }
  }

  // Pre-populate syntax code template on startup
  updateDbSyntaxOnly();

  if (runDbQueryBtn) {
    runDbQueryBtn.addEventListener('click', async () => {
      const query = dbQueryText ? dbQueryText.value.trim() : 'pui usturoi';
      
      runDbQueryBtn.disabled = true;
      const originalText = runDbQueryBtn.innerHTML;
      runDbQueryBtn.innerHTML = '<span> Interogare...</span>';
      
      try {
        const res = await fetch(`${API}/api/playground/db_query`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: query, db_name: selectedDb })
        });
        
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        
        if (dbQueryCodeBlock) dbQueryCodeBlock.textContent = data.code;
        if (dbQueryOutputBlock) dbQueryOutputBlock.textContent = JSON.stringify(data.raw_output, null, 2);
        if (dbQueryLatency) dbQueryLatency.textContent = data.latency_ms.toFixed(2);
        
        if (dbQueryContainer) {
          dbQueryContainer.style.display = 'grid';
          dbQueryContainer.style.opacity = '0';
          dbQueryContainer.style.transition = 'opacity 0.4s ease';
          setTimeout(() => {
            dbQueryContainer.style.opacity = '1';
          }, 50);
        }
      } catch (e) {
        console.error(e);
        alert('Eroare la interogarea bazei de date vectoriale local-first.');
      } finally {
        runDbQueryBtn.disabled = false;
        runDbQueryBtn.innerHTML = originalText;
      }
    });
  }

  // ── Embedding models benchmarking ──────────────────────────────────────────
  if (runModelBenchBtn) {
    runModelBenchBtn.addEventListener('click', async () => {
      const text = modelBenchText ? modelBenchText.value.trim() : 'Ingrediente proaspete';
      
      runModelBenchBtn.disabled = true;
      const originalText = runModelBenchBtn.innerHTML;
      runModelBenchBtn.innerHTML = '<span> Se codifică...</span>';
      
      if (modelBenchResults) {
        modelBenchResults.innerHTML = `
          <div style="text-align: center; padding: 20px;">
            <div class="spinner-sm" style="margin: 0 auto 12px; width: 24px; height: 24px;"></div>
            <p style="color: var(--text-muted); font-size: 0.85rem;">Se calculează latența de codificare locală...</p>
          </div>
        `;
      }
      
      try {
        const res = await fetch(`${API}/api/playground/model_benchmark`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: text })
        });
        
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        
        const maxThroughput = Math.max(...data.models.map(m => m.throughput), 100);
        
        if (modelBenchResults) {
          modelBenchResults.innerHTML = data.models.map(m => {
            const pct = Math.min(100, (m.throughput / maxThroughput) * 100);
            
            let barColor = 'var(--cyan)';
            let statusText = 'Rapid';
            if (m.active) {
              barColor = 'var(--emerald)';
              statusText = 'Local Activ (Rapid)';
            } else if (m.throughput < 50) {
              barColor = 'var(--amber)';
              statusText = 'Moderat (Necesită GPU)';
            } else if (m.throughput > 150) {
              barColor = 'var(--cyan)';
              statusText = 'Rapid';
            } else {
              barColor = 'var(--violet-lt)';
              statusText = 'Mediu';
            }
            
            const badgeClass = m.active 
              ? 'background: rgba(16,185,129,0.15); color: var(--emerald); border: 1px solid rgba(16,185,129,0.25);'
              : 'background: rgba(255,255,255,0.05); color: var(--text-muted); border: 1px solid var(--border);';
              
            return `
              <div class="shopping-item" style="display: flex; flex-direction: column; align-items: stretch; gap: 8px; padding: 14px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: rgba(255,255,255,0.01);">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                  <div style="font-weight: 700; font-size: 0.95rem; color: #fff;">${esc(m.name)}</div>
                  <div style="display: flex; gap: 6px;">
                    <span style="font-size: 0.75rem; padding: 2px 6px; border-radius: 4px; ${badgeClass}">
                      ${m.active ? 'Activ' : 'Simulat'}
                    </span>
                    <span style="font-size: 0.75rem; padding: 2px 6px; border-radius: 4px; background: rgba(255,255,255,0.05); color: var(--text-dim); border: 1px solid var(--border);">
                      ${m.dimensions} dim
                    </span>
                  </div>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 8px; font-size: 0.8rem; color: var(--text-muted);">
                  <div> File size: <strong style="color: #fff;">${m.size_mb} MB</strong></div>
                  <div> RAM required: <strong style="color: #fff;">${m.ram_mb} MB</strong></div>
                  <div> Multilingual support: <strong style="color: #fff;">${esc(m.multilingual)}</strong></div>
                </div>

                <div style="margin-top: 4px;">
                  <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 4px;">
                    <span style="color: var(--text-muted);">Throughput: <strong style="color: #fff;">${m.throughput} vectors/sec</strong></span>
                    <span style="color: ${barColor};">Latență: <strong>${m.latency_ms.toFixed(1)} ms</strong></span>
                  </div>
                  <div style="height: 6px; background: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden;">
                    <div style="width: ${pct}%; height: 100%; background: ${barColor}; transition: width 0.8s ease;"></div>
                  </div>
                </div>
              </div>
            `;
          }).join('');
        }
      } catch (e) {
        console.error(e);
        if (modelBenchResults) {
          modelBenchResults.innerHTML = `
            <div style="text-align: center; padding: 20px; color: var(--rose-lt); font-style: italic;">
              Eroare la rularea testului de model embedding benchmark.
            </div>
          `;
        }
      } finally {
        runModelBenchBtn.disabled = false;
        runModelBenchBtn.innerHTML = originalText;
      }
    });
  }
}

// ── Boot ──────────────────────────────────────────────────────────────────
init();

