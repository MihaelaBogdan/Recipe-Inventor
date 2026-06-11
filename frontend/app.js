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
  const dbEmbeddingGrid     = document.getElementById('dbEmbeddingGrid');
  const dbEmbeddingSummary  = document.getElementById('dbEmbeddingSummary');
  const dbIndexDetails      = document.getElementById('dbIndexDetails');

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

  // Toggle Prompt Inspector binding
  const togglePromptInspectorBtn = document.getElementById('togglePromptInspectorBtn');
  const promptInspectorContainer = document.getElementById('promptInspectorContainer');
  const promptInspectorCode = document.getElementById('promptInspectorCode');
  if (togglePromptInspectorBtn && promptInspectorContainer) {
    togglePromptInspectorBtn.addEventListener('click', () => {
      const isHidden = promptInspectorContainer.style.display === 'none' || promptInspectorContainer.style.display === '';
      if (isHidden) {
        promptInspectorContainer.style.display = 'block';
        togglePromptInspectorBtn.textContent = 'Ascunde Prompt-ul RAG Augmented';
      } else {
        promptInspectorContainer.style.display = 'none';
        togglePromptInspectorBtn.textContent = 'Vizualizează Prompt-ul RAG Augmented trimis la LLM';
      }
    });
  }

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

      if (promptInspectorCode && data.recipes) {
        let contextText = data.recipes.map((r, i) => {
          return `DOCUMENT [${i+1}]:\nTitlu: ${r.title}\nCuisine: ${r.cuisine}\nIngrediente: ${r.ingredients.join(', ')}\nDescriere: ${r.description || 'Fără descriere.'}`;
        }).join('\n\n');

        let promptStr = `SYSTEM INSTRUCTIONS:
Ești un asistent culinar inteligent și experimentat. Sarcina ta este să creezi rețete noi sau să răspunzi la întrebări pe baza documentelor culinare puse la dispoziție în CONTEXT. Fii factual și nu inventa detalii în afara contextului.

CONTEXT DE RETRIEVAL (Din Vector Database):
${contextText}

USER QUERY:
"${query}"

RESPONSE (Generat factual pe baza documentelor furnizate):`;
        promptInspectorCode.textContent = promptStr;
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

    if (dbIndexDetails) {
      let detailsHtml = '';
      if (selectedDb === 'chromadb') {
        detailsHtml = `
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Algoritm:</strong><span>HNSW (Hierarchical Navigable Small World)</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Distanță:</strong><span>Cosine Similarity (1 - CosSim)</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Metadate:</strong><span>SQLite local pe disc</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Indexare:</strong><span>Automată la adăugarea documentului</span></div>
          <div style="margin-top: 8px; font-size: 0.75rem; color: var(--text-dim); line-height: 1.3; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 6px;">
            ChromaDB creează în mod implicit un graf HNSW local. Este ideal pentru colecții locale de rețete (ex. meniul unui restaurant) deoarece vectorii sunt asociați cu metadatele și sunt stocați direct într-o bază SQLite locală, fiind optimizat pentru o inițializare rapidă și zero-config.
          </div>
        `;
      } else if (selectedDb === 'qdrant') {
        detailsHtml = `
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Algoritm:</strong><span>HNSW cu Payload Filtering</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Distanță:</strong><span>Cosine, L2, Dot Product</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Engine:</strong><span>Rust, ultra-rapid</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Stocare:</strong><span>În memorie sau fișiere mapate (mmap)</span></div>
          <div style="margin-top: 8px; font-size: 0.75rem; color: var(--text-dim); line-height: 1.3; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 6px;">
            Qdrant este ideal când vrei să filtrezi rețetele în timp ce cauți semantici (ex. cauți 'desert ciocolată' dar doar cele cu eticheta 'fără gluten'). Qdrant permite filtrarea pe payload direct în timpul parcurgerii grafului HNSW, accelerând masiv interogările complexe.
          </div>
        `;
      } else if (selectedDb === 'pgvector') {
        detailsHtml = `
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Algoritm:</strong><span>HNSW (v0.5.0+) sau IVFFlat (clustere)</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Distanță:</strong><span>Cosine (<=>), L2 (<->), IP (<#>)</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Integrare:</strong><span>Tabel relațional Postgres normal</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Index:</strong><span>CREATE INDEX USING hnsw</span></div>
          <div style="margin-top: 8px; font-size: 0.75rem; color: var(--text-dim); line-height: 1.3; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 6px;">
            pgvector stochează embedding-urile direct în rândurile tabelelor SQL normale. Este ideal dacă aplicația ta are deja o bază de date relațională (ex. tabele pentru utilizatori, comenzi, rețete preferate), permițând JOIN-uri și interogări SQL native combinate direct.
          </div>
        `;
      } else {
        detailsHtml = `
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Algoritm:</strong><span>HNSW, IVF-Flat, ScaNN, IVF-PQ</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Distanță:</strong><span>Cosine, L2, IP, Jaccard</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Stocare:</strong><span>MinIO (Vectori) + etcd (Metadate)</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Scalare:</strong><span>Distribuită orizontal (Sharding)</span></div>
          <div style="margin-top: 8px; font-size: 0.75rem; color: var(--text-dim); line-height: 1.3; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 6px;">
            Milvus fragmentează datele în segmente distribuite. Este ideal pentru platforme globale (ex. milioane de rețete culinare de la mii de utilizatori) deoarece folosește cuantizarea scalară (PQ/SQ) pentru a comprima vectorii rețetelor, reducând memoria ocupată.
          </div>
        `;
      }
      dbIndexDetails.innerHTML = detailsHtml;
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
        
        // Draw embedding vector footprint
        if (dbEmbeddingGrid && data.query_vector) {
          dbEmbeddingGrid.innerHTML = '';
          data.query_vector.forEach(v => {
            const cell = document.createElement('div');
            cell.style.width = '100%';
            cell.style.paddingBottom = '100%';
            cell.style.borderRadius = '1px';
            
            // Amplify float ranges to make visual differences apparent
            const opacity = Math.min(1, Math.max(0.15, Math.abs(v) * 6.0));
            if (v > 0) {
              cell.style.backgroundColor = `rgba(6, 182, 212, ${opacity})`; // Cyan
            } else {
              cell.style.backgroundColor = `rgba(245, 158, 11, ${opacity})`; // Amber
            }
            dbEmbeddingGrid.appendChild(cell);
          });
        }
        
        if (dbEmbeddingSummary && data.query_vector) {
          const vals = data.query_vector.slice(0, 5).map(x => x.toFixed(4)).join(', ');
          dbEmbeddingSummary.textContent = `[${vals}, ... (total 384 dim)]`;
        }
        
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

  // ── Thematic Culinary Embedding Explorer ─────────────────────────────────
  function initThematicExplorer() {
    const thematicRecipes = {
      sarmale: {
        title: "Sarmale Românești cu Mămăligă",
        desc: "Savuroase, tradiționale, învelite în varză acră și servite cu mămăligă caldă.",
        vector: [0.8, 0.3, -0.9, 0.6, -0.9],
        ingredients: ["carne tocata", "varza acra", "orez", "ceapa", "mamaliga"]
      },
      tort: {
        title: "Tort de Ciocolată cu Cireșe",
        desc: "Un desert fin, cremos, intens îndulcit și plin de cacao.",
        vector: [-0.6, -0.8, 1.0, 0.1, 0.2],
        ingredients: ["ciocolata", "frisca", "cirese", "faina", "zahar"]
      },
      cezar: {
        title: "Salată Cezar cu Pui",
        desc: "O salată proaspătă cu salată romană, crutoane, pui la grătar și dressing cremos.",
        vector: [0.5, 0.1, -0.7, -0.4, 0.5],
        ingredients: ["salata romana", "piept de pui", "parmezan", "crutoane", "dressing"]
      },
      carbonara: {
        title: "Spaghete Carbonara",
        desc: "Un clasic italian bogat în grăsimi aromate, gălbenuș de ou și pecorino.",
        vector: [0.7, 0.2, -0.8, 0.4, 0.6],
        ingredients: ["spaghete", "guanciale", "galbenus ou", "pecorino", "piper"]
      },
      somon: {
        title: "Somon la Grătar cu Broccoli",
        desc: "O masă sănătoasă, bogată în grăsimi bune și proteine, cu legume gătite la abur.",
        vector: [0.9, 0.0, -0.9, -0.6, 0.4],
        ingredients: ["somon", "broccoli", "lamaie", "ulei de masline"]
      },
      curry: {
        title: "Curry de Pui Indian",
        desc: "O explozie de mirodenii asiatice într-un sos dens de roșii și lapte de cocos.",
        vector: [0.8, 0.9, -0.4, 0.8, 0.9],
        ingredients: ["piept de pui", "garam masala", "ghimbir", "lapte de cocos", "curry"]
      }
    };

    const recipeASelect = document.getElementById('thematicRecipeA');
    const recipeBSelect = document.getElementById('thematicRecipeB');
    const thematicSimVal = document.getElementById('thematicSimVal');
    const thematicExplanation = document.getElementById('thematicExplanation');
    const vectorDimGrid = document.getElementById('vectorDimGrid');

    if (!recipeASelect || !recipeBSelect) return;

    // Dimensions labels & metadata
    const dimensions = [
      { name: "Proteine & Structură (Sărat vs Dulce)", desc: "Savuros, carne/pește vs texturi ușoare/zahăr" },
      { name: "Intensitate Condimente & Mirodenii", desc: "Cantitatea de piper, ierburi aromatice, ghimbir, chili" },
      { name: "Dulceață & Profil Desert", desc: "Zahăr, ciocolată, fructe dulci, vanilie" },
      { name: "Umiditate & Densitate Sos", desc: "Sosuri abundente, supe, tocănițe vs preparate uscate/grătar" },
      { name: "Origine & Caracter Exotic", desc: "Rețete globale, asiatice/mediteraneene vs preparate pur tradiționale" }
    ];

    function updateThematicComparison() {
      const keyA = recipeASelect.value;
      const keyB = recipeBSelect.value;
      const rA = thematicRecipes[keyA];
      const rB = thematicRecipes[keyB];

      if (!rA || !rB) return;

      // Cosine similarity computation
      let dot = 0;
      let normA = 0;
      let normB = 0;
      for (let i = 0; i < 5; i++) {
        dot += rA.vector[i] * rB.vector[i];
        normA += rA.vector[i] * rA.vector[i];
        normB += rB.vector[i] * rB.vector[i];
      }
      normA = Math.sqrt(normA);
      normB = Math.sqrt(normB);
      const similarity = normA > 0 && normB > 0 ? (dot / (normA * normB)) : 0;

      // Display similarity score
      thematicSimVal.textContent = similarity.toFixed(3);
      if (similarity > 0.6) {
        thematicSimVal.style.color = "var(--emerald)";
      } else if (similarity > 0.1) {
        thematicSimVal.style.color = "var(--amber)";
      } else {
        thematicSimVal.style.color = "var(--red)";
      }

      // Semantic explanation
      let expl = "";
      if (similarity > 0.6) {
        expl = `Asemănare semantică puternică! Ambele rețete împart caracteristici culinare majore. În spațiul vectorial dens, acestea sunt amplasate foarte aproape datorită ingredientelor de bază comune și a profilului de aromă similar (de exemplu, ambele fiind feluri de mâncare sărate, calde, bogate în proteine).`;
      } else if (similarity > 0.1) {
        expl = `Similitudine moderată. Preparatele au unele corelații (de exemplu, sunt ambele rețete sărate de origine internațională), dar diferă semnificativ prin ingredientele cheie și modul de gătire (unul este uscat, celălalt sos/supă, sau folosesc condimente foarte diferite).`;
      } else {
        expl = `Similitudine foarte mică sau negativă! Cele două rețete reprezintă concepte culinare opuse în spațiul vectorial. De exemplu, una este un fel principal tradițional și sărat (sarmale), iar cealaltă este un desert dulce internațional (tort de ciocolată). Un algoritm RAG va ști că o interogare pentru una dintre ele nu trebuie să returneze cealaltă.`;
      }
      thematicExplanation.innerHTML = `<strong>Analiză semantică:</strong> ${expl} <br><br>
        <span style="color: var(--text-muted); font-size: 0.8rem;">
          Notă: Modelele reale folosesc 384 de astfel de dimensiuni abstracte (nu doar 5 dimensiuni umane). Fiecare dimensiune captează asocieri subtile de limbaj și concepte (ex: 'grătar' cu 'cărbuni', 'somon' cu 'pește').
        </span>`;

      // Render the comparison table / progress bars
      let gridHtml = `
        <div style="display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 12px; font-weight: 700; font-size: 0.8rem; color: var(--text-muted); border-bottom: 1px solid var(--border); padding-bottom: 8px; margin-bottom: 12px;">
          <div>Dimensiune Conceptuală</div>
          <div style="text-align: center;">${rA.title.split(' ')[0]}</div>
          <div style="text-align: center;">${rB.title.split(' ')[0]}</div>
        </div>
      `;

      for (let i = 0; i < 5; i++) {
        const valA = rA.vector[i];
        const valB = rB.vector[i];

        // Format to percentage
        const pctA = Math.round((valA + 1) * 50); // Map -1..1 to 0..100%
        const pctB = Math.round((valB + 1) * 50);

        const colorA = valA > 0 ? "var(--cyan)" : "var(--amber)";
        const colorB = valB > 0 ? "var(--cyan)" : "var(--amber)";

        gridHtml += `
          <div style="display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 12px; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.03); font-size: 0.85rem;">
            <div>
              <div style="font-weight: 600; color: #fff;">${dimensions[i].name}</div>
              <div style="font-size: 0.72rem; color: var(--text-muted);">${dimensions[i].desc}</div>
            </div>
            
            <!-- Recipe A Bar -->
            <div style="padding: 0 4px;">
              <div style="display: flex; justify-content: space-between; font-size: 0.75rem; margin-bottom: 2px;">
                <span style="color: ${colorA}; font-weight: bold;">${valA > 0 ? '+' : ''}${valA.toFixed(1)}</span>
              </div>
              <div style="height: 6px; background: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden;">
                <div style="width: ${pctA}%; height: 100%; background: ${colorA};"></div>
              </div>
            </div>

            <!-- Recipe B Bar -->
            <div style="padding: 0 4px;">
              <div style="display: flex; justify-content: space-between; font-size: 0.75rem; margin-bottom: 2px;">
                <span style="color: ${colorB}; font-weight: bold;">${valB > 0 ? '+' : ''}${valB.toFixed(1)}</span>
              </div>
              <div style="height: 6px; background: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden;">
                <div style="width: ${pctB}%; height: 100%; background: ${colorB};"></div>
              </div>
            </div>
          </div>
        `;
      }

      vectorDimGrid.innerHTML = gridHtml;
    }

    recipeASelect.addEventListener('change', updateThematicComparison);
    recipeBSelect.addEventListener('change', updateThematicComparison);

    updateThematicComparison();
  }

  initThematicExplorer();

  // ── HNSW Graph Search Simulator ──────────────────────────────────────────
  function initHnswSimulator() {
    const graphNodes = {
      mamaliga:  { id: 'mamaliga',  label: 'Mămăligă',  x: 250, y: 130, val: [0.0, 0.0, -0.3, -0.2, -0.9] },
      sarmale:   { id: 'sarmale',   label: 'Sarmale',   x: 170, y: 190, val: [0.8, 0.3, -0.9, 0.6, -0.9] },
      papanasi:  { id: 'papanasi',  label: 'Papanași',  x: 80,  y: 130, val: [-0.4, -0.6, 0.8, 0.3, -0.9] },
      carbonara: { id: 'carbonara', label: 'Spaghete',  x: 250, y: 50,  val: [0.7, 0.2, -0.8, 0.4, 0.6] },
      somon:     { id: 'somon',     label: 'Somon',     x: 420, y: 130, val: [0.9, 0.0, -0.9, -0.6, 0.4] },
      curry:     { id: 'curry',     label: 'Curry Pui', x: 330, y: 190, val: [0.8, 0.9, -0.4, 0.8, 0.9] }
    };

    const graphLinks = [
      { source: 'mamaliga', target: 'sarmale' },
      { source: 'mamaliga', target: 'somon' },
      { source: 'mamaliga', target: 'carbonara' },
      { source: 'sarmale', target: 'papanasi' },
      { source: 'sarmale', target: 'curry' },
      { source: 'somon', target: 'curry' },
      { source: 'carbonara', target: 'somon' },
      { source: 'carbonara', target: 'papanasi' }
    ];

    const targets = {
      desert:      { name: "'ceva dulce și cald'", vector: [-0.5, -0.7, 0.9, 0.2, -0.8] },
      peste:       { name: "'pește ușor cu legume'", vector: [0.9, 0.0, -0.9, -0.7, 0.5] },
      paste:       { name: "'spaghete italienești cremoase'", vector: [0.7, 0.2, -0.8, 0.5, 0.6] },
      traditional: { name: "'mâncare românească tradițională'", vector: [0.8, 0.3, -0.9, 0.5, -0.9] }
    };

    const querySelect = document.getElementById('hnswQuerySelect');
    const startBtn    = document.getElementById('hnswStartBtn');
    const nextBtn     = document.getElementById('hnswNextBtn');
    const resetBtn    = document.getElementById('hnswResetBtn');
    const statusText  = document.getElementById('hnswStatusText');

    if (!querySelect || !startBtn) return;

    let currentNode = null;
    let visitedLinks = [];
    let isFinished = false;

    function getCosineSimilarity(v1, v2) {
      let dot = 0;
      let n1 = 0;
      let n2 = 0;
      for (let i = 0; i < 5; i++) {
        dot += v1[i] * v2[i];
        n1 += v1[i] * v1[i];
        n2 += v2[i] * v2[i];
      }
      return n1 > 0 && n2 > 0 ? (dot / (Math.sqrt(n1) * Math.sqrt(n2))) : 0;
    }

    function drawGraph(activeNodeId, finishedNodeId) {
      const svgNodes = document.getElementById('hnswNodes');
      const svgLinks = document.getElementById('hnswLinks');
      if (!svgNodes || !svgLinks) return;

      svgNodes.innerHTML = '';
      svgLinks.innerHTML = '';

      // Draw links
      graphLinks.forEach(link => {
        const sNode = graphNodes[link.source];
        const tNode = graphNodes[link.target];
        const isVisited = visitedLinks.some(vl => 
          (vl.source === link.source && vl.target === link.target) ||
          (vl.source === link.target && vl.target === link.source)
        );

        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', sNode.x);
        line.setAttribute('y1', sNode.y);
        line.setAttribute('x2', tNode.x);
        line.setAttribute('y2', tNode.y);
        line.setAttribute('stroke', isVisited ? 'var(--cyan)' : 'rgba(255,255,255,0.08)');
        line.setAttribute('stroke-width', isVisited ? '3' : '1.5');
        if (isVisited) {
          line.setAttribute('stroke-dasharray', 'none');
        } else {
          line.setAttribute('stroke-dasharray', '3,3');
        }
        svgLinks.appendChild(line);
      });

      // Draw nodes
      Object.values(graphNodes).forEach(node => {
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', node.x);
        circle.setAttribute('cy', node.y);
        circle.setAttribute('r', '20');
        
        let fill = 'rgba(255,255,255,0.05)';
        let stroke = 'var(--border)';
        let strokeWidth = '1.5';

        if (node.id === finishedNodeId) {
          fill = 'rgba(16,185,129,0.2)';
          stroke = 'var(--emerald)';
          strokeWidth = '3';
        } else if (node.id === activeNodeId) {
          fill = 'rgba(245,158,11,0.2)';
          stroke = 'var(--amber)';
          strokeWidth = '3';
        } else if (visitedLinks.some(vl => vl.source === node.id || vl.target === node.id)) {
          fill = 'rgba(6,182,212,0.1)';
          stroke = 'var(--cyan)';
          strokeWidth = '2';
        }

        circle.setAttribute('fill', fill);
        circle.setAttribute('stroke', stroke);
        circle.setAttribute('stroke-width', strokeWidth);
        g.appendChild(circle);

        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', node.x);
        text.setAttribute('y', node.y + 4);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('font-size', '9px');
        text.setAttribute('fill', '#fff');
        text.setAttribute('font-weight', 'bold');
        text.textContent = node.label;
        g.appendChild(text);

        svgNodes.appendChild(g);
      });
    }

    startBtn.addEventListener('click', () => {
      currentNode = 'mamaliga';
      visitedLinks = [];
      isFinished = false;
      querySelect.disabled = true;
      startBtn.disabled = true;
      nextBtn.disabled = false;
      
      const targetQuery = targets[querySelect.value];
      const startSim = getCosineSimilarity(graphNodes.mamaliga.val, targetQuery.vector);

      statusText.innerHTML = `Căutarea HNSW a fost inițializată.<br>
        <strong>Nod Curent:</strong> Mămăligă (Punct de intrare)<br>
        <strong>Similitudine inițială:</strong> ${startSim.toFixed(3)}<br>
        Apasă 'Pasul Următor' pentru a evalua vecinii.`;
      
      drawGraph(currentNode, null);
    });

    nextBtn.addEventListener('click', () => {
      if (!currentNode || isFinished) return;

      const targetVal = querySelect.value;
      const targetQuery = targets[targetVal];
      const curSim = getCosineSimilarity(graphNodes[currentNode].val, targetQuery.vector);

      // Find neighbors
      const neighbors = [];
      graphLinks.forEach(link => {
        if (link.source === currentNode) neighbors.push(link.target);
        else if (link.target === currentNode) neighbors.push(link.source);
      });

      let bestNeighbor = null;
      let bestSim = curSim;

      neighbors.forEach(nId => {
        const sim = getCosineSimilarity(graphNodes[nId].val, targetQuery.vector);
        if (sim > bestSim) {
          bestSim = sim;
          bestNeighbor = nId;
        }
      });

      if (bestNeighbor) {
        visitedLinks.push({ source: currentNode, target: bestNeighbor });
        const oldNodeLabel = graphNodes[currentNode].label;
        currentNode = bestNeighbor;
        const newNodeLabel = graphNodes[currentNode].label;

        statusText.innerHTML = `Săritură efectuată în graf:<br>
          <strong>De la:</strong> ${oldNodeLabel} -> <strong>La:</strong> ${newNodeLabel}<br>
          <strong>Similitudine nouă:</strong> ${bestSim.toFixed(3)} (Mai bună)<br>
          Apasă din nou 'Pasul Următor'.`;

        drawGraph(currentNode, null);
      } else {
        // Stop, we reached local minimum
        isFinished = true;
        nextBtn.disabled = true;
        const finalLabel = graphNodes[currentNode].label;
        
        statusText.innerHTML = `Căutarea HNSW s-a finalizat!<br>
          <strong>Nod Final:</strong> ${finalLabel}<br>
          <strong>Similitudine maximă locală:</strong> ${curSim.toFixed(3)}<br>
          Algoritmul s-a oprit deoarece niciun nod vecin nu oferă o similitudine mai mare. Am găsit rețeta fără a citi celelalte noduri din baza de date.`;

        drawGraph(null, currentNode);
      }
    });

    resetBtn.addEventListener('click', () => {
      currentNode = null;
      visitedLinks = [];
      isFinished = false;
      querySelect.disabled = false;
      startBtn.disabled = false;
      nextBtn.disabled = true;
      statusText.innerHTML = "Apasă 'Inițializează Căutare' pentru a plasa punctul de intrare.";
      drawGraph(null, null);
    });

    // Initial draw
    drawGraph(null, null);
  }

  // ── RAG vs Pure LLM Showdown ─────────────────────────────────────────────
  function initShowdown() {
    const selector = document.getElementById('showdownQuerySelect');
    const llmConsole = document.getElementById('showdownLlmConsole');
    const ragConsole = document.getElementById('showdownRagConsole');

    if (!selector || !llmConsole || !ragConsole) return;

    const database = {
      pui_dacian: {
        query: "Cum se prepară 'Pui Dacian cu Sos Secret' în aplicația noastră?",
        llm: "Puiul Dacian cu Sos Secret este o reteta straveche preparata din piept de pui fript pe jar, uns cu miere si mirodenii din padurile Carpatilor. Sosul secret este facut din vin alb dacic, miere de albine salbatice, piper pisat, untura si putin otet de mere fermentat cu usturoi. Totul se fierbe in ceaun pana cand scade si capata o culoare aramie.",
        rag: "[Căutare Vectorială: 'Pui Dacian cu Sos Secret']\n[ChromaDB a găsit 1 document relevant, Scor: 0.912]\n[Injectare rețetă ID 83 în Contextul Prompt-ului]\n\nConform rețetei din baza de date:\nIngrediente principale: piept de pui, ciuperci champignon, unt, smântână de gătit, vin alb sec, usturoi, cimbru.\nPreparare: Pieptul de pui se prăjește în unt cu usturoi, apoi se adaugă ciupercile tăiate felii. Se stinge totul cu vin alb sec și se adaugă smântâna lichidă. Se reduce sosul la foc mic cu cimbru. Sosul secret este emulsia naturală de unt, smântână și reducerea de vin cu ciuperci."
      },
      albinuta: {
        query: "Care sunt ingredientele exacte pentru Prăjitura 'Albinuța' din baza de date?",
        llm: "Prăjitura Albinuța tradițională se prepară din: foi pufoase de pandișpan cu vanilie, o cremă aromată de mascarpone cu frișcă lichidă și miere de albine, jeleu de fructe de pădure la mijloc, acoperită cu fulgi mari de nucă de cocos și fistic mărunțit pentru decor.",
        rag: "[Căutare Vectorială: 'Prăjitura Albinuța']\n[ChromaDB a găsit 1 document relevant, Scor: 0.887]\n[Injectare rețetă ID 142 în Contextul Prompt-ului]\n\nIngredientele oficiale stocate sunt:\nFoi pe fundul tăvii: făină de grâu, miere naturală de albine (3 linguri), unt topit, zahăr pudră, ouă întregi, bicarbonat de sodiu stins cu lămâie.\nCremă fină de griș: lapte dulce, griș de grâu (4 linguri), unt la temperatura camerei, zahăr pudră, coajă și suc de lămâie.\nStrat intermediar: gem acrișor de prune românești."
      },
      somon_carpati: {
        query: "Cum gătesc rețeta de 'Somon în Coajă de Pâine a Carpaților'?",
        llm: "Aceasta este o rețetă montană dacică. Somonul proaspăt pescuit din râurile Carpaților se condimentează cu sare de salină, se învelește într-un aluat dospit din făină de secară și semințe de in, se unge cu gălbenuș de ou și se coace direct în spuză sau în cuptor cu lemne timp de 45 de minute până pâinea devine crocantă.",
        rag: "[Căutare Vectorială: 'Somon în Coajă de Pâine a Carpaților']\n[ChromaDB a găsit 1 document relevant, Scor: 0.945]\n[Injectare rețetă ID 208 în Contextul Prompt-ului]\n\nConform bazei de date culinare:\nSomonul se unge cu muștar de Dijon amestecat cu miere. Crusta (coaja de pâine) este realizată din crutoane de pâine albă mărunțite, amestecate cu mărar proaspăt tocat, parmezan ras și ulei de măsline. Peștele se coace pe tavă timp de 12-15 minute la 200 de grade până când crusta este aurie. Nu se folosește aluat de pâine."
      }
    };

    let typingTimerLlm = null;
    let typingTimerRag = null;

    function typeEffect(element, text, delay = 15) {
      element.textContent = "";
      let index = 0;
      
      function type() {
        if (index < text.length) {
          element.textContent += text.charAt(index);
          index++;
          element.scrollTop = element.scrollHeight;
          return setTimeout(type, delay);
        }
      }
      return type();
    }

    function runShowdown() {
      // Clear timers
      if (typingTimerLlm) clearTimeout(typingTimerLlm);
      if (typingTimerRag) clearTimeout(typingTimerRag);

      const val = selector.value;
      const data = database[val];

      if (!data) return;

      llmConsole.textContent = "Se generează răspunsul LLM simplu...";
      ragConsole.textContent = "Se interoghează baza de date vectorială și se augmentează promptul...";

      typingTimerLlm = typeEffect(llmConsole, data.llm, 12);
      typingTimerRag = typeEffect(ragConsole, data.rag, 10);
    }

    selector.addEventListener('change', runShowdown);

    // Run first time on load
    runShowdown();
  }

  initHnswSimulator();
  initShowdown();
  initThematicExplorer();
}

// ── Boot ──────────────────────────────────────────────────────────────────
init();

