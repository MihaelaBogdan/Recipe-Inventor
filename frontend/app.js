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
  if (calcSimBtn) {
    calcSimBtn.addEventListener('click', async () => {
      const t1 = simText1 ? simText1.value.trim() : '';
      const t2 = simText2 ? simText2.value.trim() : '';
      if (!t1 || !t2) return;

      calcSimBtn.disabled = true;
      if (simResultVal) {
        simResultVal.textContent = '...';
        simResultVal.style.color = 'var(--text-muted)';
      }

      try {
        const res = await fetch(`${API}/api/playground/similarity`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text1: t1, text2: t2 })
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        const sim = data.similarity;
        if (simResultVal) {
          simResultVal.textContent = sim.toFixed(4);

          if (sim > 0.6) {
            simResultVal.style.color = 'var(--emerald)';
          } else if (sim > 0.3) {
            simResultVal.style.color = 'var(--amber)';
          } else {
            simResultVal.style.color = 'var(--red)';
          }
        }
      } catch (e) {
        console.error(e);
        if (simResultVal) {
          simResultVal.textContent = 'Error';
          simResultVal.style.color = 'var(--red)';
        }
      } finally {
        calcSimBtn.disabled = false;
      }
    });
  }

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
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Inventare Rețete:</strong><span>Căutare semantică rapidă pe ingrediente</span></div>
          <div style="margin-top: 8px; font-size: 0.75rem; color: var(--text-dim); line-height: 1.3; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 6px;">
            ChromaDB este perfect pentru a inventa rețete rapid la nivel local. Permite stocarea simplă a setului de date culinare și căutarea semantică direct pe disc (în baza SQLite a metadatelor), fiind excelent pentru prototipuri rapide de generare de rețete pe baza ingredientelor pe care le ai deja în frigider.
          </div>
        `;
      } else if (selectedDb === 'qdrant') {
        detailsHtml = `
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Algoritm:</strong><span>HNSW cu Payload Filtering</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Distanță:</strong><span>Cosine, L2, Dot Product</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Filtrare Alergii:</strong><span>Filtre dure direct în graful HNSW</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Stocare:</strong><span>În memorie sau fișiere mapate (mmap)</span></div>
          <div style="margin-top: 8px; font-size: 0.75rem; color: var(--text-dim); line-height: 1.3; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 6px;">
            Pentru a inventa rețete adaptate nevoilor tale, filtrarea pe payload din Qdrant este ideală. Poți căuta semantic rețete similare cu ingredientele tale și, în același timp, să aplici filtre dure pentru alergii (ex. 'fără lactate', 'vegan') sau timp de preparare, asigurând că sugestiile inventate respectă restricțiile dietetice în timp real.
          </div>
        `;
      } else if (selectedDb === 'pgvector') {
        detailsHtml = `
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Algoritm:</strong><span>HNSW (v0.5.0+) sau IVFFlat (clustere)</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Distanță:</strong><span>Cosine (<=>), L2 (<->), IP (<#>)</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Cumpărături:</strong><span>JOIN direct cu listele utilizatorilor</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Index:</strong><span>CREATE INDEX USING hnsw</span></div>
          <div style="margin-top: 8px; font-size: 0.75rem; color: var(--text-dim); line-height: 1.3; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 6px;">
            pgvector este ideal dacă ai deja baza de date a utilizatorilor într-un PostgreSQL clasic. Poți corela istoricul de cumpărături, listele de ingrediente disponibile ale utilizatorilor și rețetele inventate folosind query-uri SQL native și JOIN-uri simple, combinând datele relaționale cu similitudinea vectorială.
          </div>
        `;
      } else {
        detailsHtml = `
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Algoritm:</strong><span>HNSW, IVF-Flat, ScaNN, IVF-PQ</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Distanță:</strong><span>Cosine, L2, IP, Jaccard</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Producție:</strong><span>Pregătit pentru milioane de rețete</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><strong>Scalare:</strong><span>Distribuită orizontal (Sharding)</span></div>
          <div style="margin-top: 8px; font-size: 0.75rem; color: var(--text-dim); line-height: 1.3; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 6px;">
            Milvus este excelent dacă dorești să scalezi sistemul de inventat rețete la milioane de utilizatori și milioane de variante culinare. Permite sharding-ul distribuit și optimizarea memoriei prin cuantizare, asigurând că latența de căutare semantică rămâne sub câteva milisecunde chiar și pentru un volum gigantic de date culinare globale.
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

                <div style="margin-top: 6px; padding: 6px 10px; background: rgba(255,255,255,0.02); border-radius: 6px; border: 1px solid rgba(255,255,255,0.04); font-size: 0.76rem; color: var(--text-muted); line-height: 1.4;">
                  <strong style="color: var(--violet-lt);">Impact Proiect:</strong> ${esc(m.applicability)}
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

    if (!recipeASelect || !recipeBSelect) return;

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

      // Draw radar chart on canvas
      const canvas = document.getElementById('thematicRadarCanvas');
      if (canvas) {
        const ctx = canvas.getContext('2d');
        if (ctx) {
          const devicePixelRatio = window.devicePixelRatio || 1;
          const displayWidth = 300;
          const displayHeight = 260;
          
          canvas.width = displayWidth * devicePixelRatio;
          canvas.height = displayHeight * devicePixelRatio;
          canvas.style.width = displayWidth + "px";
          canvas.style.height = displayHeight + "px";
          
          ctx.scale(devicePixelRatio, devicePixelRatio);
          ctx.clearRect(0, 0, displayWidth, displayHeight);

          const centerX = displayWidth / 2;
          const centerY = displayHeight / 2 + 10;
          const maxRadius = 80;

          // 1. Draw grid rings (concentric pentagons representing -1.0, 0.0, 1.0)
          // R-factor mapping: -1.0 -> 0.1, 0.0 -> 0.55, 1.0 -> 1.0
          const gridRings = [0.1, 0.55, 1.0];
          
          ctx.lineWidth = 1;
          gridRings.forEach(ring => {
            ctx.beginPath();
            for (let j = 0; j < 5; j++) {
              const angle = (j * 2 * Math.PI / 5) - Math.PI / 2;
              const x = centerX + Math.cos(angle) * maxRadius * ring;
              const y = centerY + Math.sin(angle) * maxRadius * ring;
              if (j === 0) ctx.moveTo(x, y);
              else ctx.lineTo(x, y);
            }
            ctx.closePath();
            if (ring === 0.55) {
              // Zero value line - dashed
              ctx.strokeStyle = "rgba(255, 255, 255, 0.18)";
              ctx.setLineDash([3, 3]);
            } else {
              ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
              ctx.setLineDash([]);
            }
            ctx.stroke();
          });
          ctx.setLineDash([]); // Reset line dash

          // 2. Draw 5 radial axis lines
          ctx.strokeStyle = "rgba(255, 255, 255, 0.12)";
          for (let j = 0; j < 5; j++) {
            const angle = (j * 2 * Math.PI / 5) - Math.PI / 2;
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.lineTo(centerX + Math.cos(angle) * maxRadius, centerY + Math.sin(angle) * maxRadius);
            ctx.stroke();
          }

          // 3. Draw grid labels along the vertical axis (shifted slightly to the left)
          ctx.font = "8px sans-serif";
          ctx.fillStyle = "rgba(255, 255, 255, 0.35)";
          ctx.textAlign = "right";
          ctx.textBaseline = "middle";
          ctx.fillText("-1.0", centerX - 4, centerY - maxRadius * 0.1);
          ctx.fillText("0.0", centerX - 4, centerY - maxRadius * 0.55);
          ctx.fillText("+1.0", centerX - 4, centerY - maxRadius * 1.0);

          // 4. Draw axis labels in Romanian
          const axisLabels = ["PROTEINE", "CONDIMENTE", "DESERT", "SOS", "EXOTIC"];
          ctx.font = "bold 9px sans-serif";
          ctx.fillStyle = "rgba(255, 255, 255, 0.55)";
          
          for (let j = 0; j < 5; j++) {
            const angle = (j * 2 * Math.PI / 5) - Math.PI / 2;
            const x = centerX + Math.cos(angle) * (maxRadius + 14);
            const y = centerY + Math.sin(angle) * (maxRadius + 10);
            
            // Adjust alignment depending on quadrant
            if (Math.abs(Math.cos(angle)) < 0.1) {
              ctx.textAlign = "center";
            } else if (Math.cos(angle) > 0) {
              ctx.textAlign = "left";
            } else {
              ctx.textAlign = "right";
            }
            
            if (Math.abs(Math.sin(angle)) < 0.1) {
              ctx.textBaseline = "middle";
            } else if (Math.sin(angle) > 0) {
              ctx.textBaseline = "top";
            } else {
              ctx.textBaseline = "bottom";
            }
            
            ctx.fillText(axisLabels[j], x, y);
          }

          // Helper to draw recipe radar polygon
          function drawRecipeRadar(vector, fillColor, strokeColor) {
            ctx.beginPath();
            for (let j = 0; j < 5; j++) {
              const val = vector[j];
              const rFactor = 0.1 + ((val + 1) / 2) * 0.9;
              const angle = (j * 2 * Math.PI / 5) - Math.PI / 2;
              const x = centerX + Math.cos(angle) * maxRadius * rFactor;
              const y = centerY + Math.sin(angle) * maxRadius * rFactor;
              if (j === 0) ctx.moveTo(x, y);
              else ctx.lineTo(x, y);
            }
            ctx.closePath();
            ctx.fillStyle = fillColor;
            ctx.fill();
            ctx.strokeStyle = strokeColor;
            ctx.lineWidth = 2;
            ctx.stroke();

            // Draw vertex dots
            for (let j = 0; j < 5; j++) {
              const val = vector[j];
              const rFactor = 0.1 + ((val + 1) / 2) * 0.9;
              const angle = (j * 2 * Math.PI / 5) - Math.PI / 2;
              const x = centerX + Math.cos(angle) * maxRadius * rFactor;
              const y = centerY + Math.sin(angle) * maxRadius * rFactor;
              
              ctx.beginPath();
              ctx.arc(x, y, 3, 0, 2 * Math.PI);
              ctx.fillStyle = strokeColor;
              ctx.fill();
              ctx.strokeStyle = "#ffffff";
              ctx.lineWidth = 1;
              ctx.stroke();
            }
          }

          // 5. Draw Recipe A (purple / violet-lt)
          drawRecipeRadar(rA.vector, "rgba(168, 85, 247, 0.18)", "rgba(168, 85, 247, 0.85)");

          // 6. Draw Recipe B (cyan)
          drawRecipeRadar(rB.vector, "rgba(6, 182, 212, 0.18)", "rgba(6, 182, 212, 0.85)");

          // 7. Draw Legend
          ctx.font = "9px sans-serif";
          ctx.textAlign = "left";
          ctx.textBaseline = "middle";

          const titleA = rA.title.split(' ').slice(0, 2).join(' ');
          const titleB = rB.title.split(' ').slice(0, 2).join(' ');

          // Recipe A Legend
          ctx.beginPath();
          ctx.arc(15, 15, 4, 0, 2 * Math.PI);
          ctx.fillStyle = "rgba(168, 85, 247, 0.25)";
          ctx.fill();
          ctx.strokeStyle = "rgba(168, 85, 247, 0.85)";
          ctx.lineWidth = 1.5;
          ctx.stroke();
          ctx.fillStyle = "rgba(255, 255, 255, 0.8)";
          ctx.fillText(titleA, 24, 15);

          // Recipe B Legend
          ctx.beginPath();
          ctx.arc(165, 15, 4, 0, 2 * Math.PI);
          ctx.fillStyle = "rgba(6, 182, 212, 0.25)";
          ctx.fill();
          ctx.strokeStyle = "rgba(6, 182, 212, 0.85)";
          ctx.lineWidth = 1.5;
          ctx.stroke();
          ctx.fillStyle = "rgba(255, 255, 255, 0.8)";
          ctx.fillText(titleB, 174, 15);
        }
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
    }

    // Interactive Dragging on Radar Map
    const canvas = document.getElementById('thematicRadarCanvas');
    let draggedPoint = null;

    function getVertexUnderMouse(mx, my) {
      const keyA = recipeASelect.value;
      const keyB = recipeBSelect.value;
      const rA = thematicRecipes[keyA];
      const rB = thematicRecipes[keyB];
      if (!rA || !rB) return null;

      const centerX = 150;
      const centerY = 130;
      const maxRadius = 80;
      const threshold = 9; // hit radius in CSS pixels

      // Check Recipe B first (so it's on top of A if overlapping)
      const keys = [
        { key: keyB, r: rB },
        { key: keyA, r: rA }
      ];

      for (const item of keys) {
        for (let j = 0; j < 5; j++) {
          const val = item.r.vector[j];
          const rFactor = 0.1 + ((val + 1) / 2) * 0.9;
          const angle = (j * 2 * Math.PI / 5) - Math.PI / 2;
          const x = centerX + Math.cos(angle) * maxRadius * rFactor;
          const y = centerY + Math.sin(angle) * maxRadius * rFactor;

          const dist = Math.hypot(mx - x, my - y);
          if (dist <= threshold) {
            return { recipeKey: item.key, dimIndex: j };
          }
        }
      }
      return null;
    }

    if (canvas) {
      function handleStart(e) {
        const rect = canvas.getBoundingClientRect();
        let clientX = e.clientX;
        let clientY = e.clientY;
        if (e.touches && e.touches.length > 0) {
          clientX = e.touches[0].clientX;
          clientY = e.touches[0].clientY;
          // Prevent screen scroll when interacting with the chart
          e.preventDefault();
        }
        const mx = clientX - rect.left;
        const my = clientY - rect.top;

        draggedPoint = getVertexUnderMouse(mx, my);
      }

      function handleMove(e) {
        const rect = canvas.getBoundingClientRect();
        let clientX = e.clientX;
        let clientY = e.clientY;
        if (e.touches && e.touches.length > 0) {
          clientX = e.touches[0].clientX;
          clientY = e.touches[0].clientY;
          e.preventDefault();
        }
        const mx = clientX - rect.left;
        const my = clientY - rect.top;

        if (draggedPoint) {
          const centerX = 150;
          const centerY = 130;
          const maxRadius = 80;

          const dx = mx - centerX;
          const dy = my - centerY;

          const j = draggedPoint.dimIndex;
          const angle = (j * 2 * Math.PI / 5) - Math.PI / 2;

          // Unit vector for the corresponding axis
          const ux = Math.cos(angle);
          const uy = Math.sin(angle);

          // Project vector onto axis unit vector
          const projection = dx * ux + dy * uy;
          let rFactor = projection / maxRadius;

          // Clamp factor to valid bounds
          rFactor = Math.max(0.1, Math.min(1.0, rFactor));

          // Map factor back to [-1.0, 1.0] range
          const v = ((rFactor - 0.1) / 0.9) * 2 - 1;

          // Update vector value in memory
          thematicRecipes[draggedPoint.recipeKey].vector[j] = parseFloat(v.toFixed(3));

          // Re-render and recalculate live stats
          updateThematicComparison();
        } else {
          // Dynamic cursor pointer visual feedback
          const hovered = getVertexUnderMouse(mx, my);
          canvas.style.cursor = hovered ? 'pointer' : 'default';
        }
      }

      function handleEnd() {
        draggedPoint = null;
      }

      canvas.addEventListener('mousedown', handleStart);
      canvas.addEventListener('mousemove', handleMove);
      window.addEventListener('mouseup', handleEnd);

      canvas.addEventListener('touchstart', handleStart, { passive: false });
      canvas.addEventListener('touchmove', handleMove, { passive: false });
      window.addEventListener('touchend', handleEnd);
    }

    recipeASelect.addEventListener('change', updateThematicComparison);
    recipeBSelect.addEventListener('change', updateThematicComparison);

    updateThematicComparison();
  }

  initThematicExplorer();

  // ── HNSW Graph Search Simulator ──────────────────────────────────────────
  function initHnswSimulator() {
    const svg = document.getElementById('hnswSvg');
    if (svg) {
      svg.setAttribute('viewBox', '0 0 500 260');
    }

    const graphNodes = {
      mamaliga:  { id: 'mamaliga',  label: 'Mămăligă',  x: 180, val: [0.0, 0.0, -0.3, -0.2, -0.9] },
      somon:     { id: 'somon',     label: 'Somon',     x: 320, val: [0.9, 0.0, -0.9, -0.6, 0.4] },
      sarmale:   { id: 'sarmale',   label: 'Sarmale',   x: 100, val: [0.8, 0.3, -0.9, 0.6, -0.9] },
      carbonara: { id: 'carbonara', label: 'Spaghete',  x: 400, val: [0.7, 0.2, -0.8, 0.4, 0.6] },
      papanasi:  { id: 'papanasi',  label: 'Papanași',  x: 40,  val: [-0.4, -0.6, 0.8, 0.3, -0.9] },
      curry:     { id: 'curry',     label: 'Curry Pui', x: 460, val: [0.8, 0.9, -0.4, 0.8, 0.9] }
    };

    const layers = {
      2: {
        nodes: ['mamaliga', 'somon'],
        links: [
          { source: 'mamaliga', target: 'somon' }
        ]
      },
      1: {
        nodes: ['mamaliga', 'somon', 'sarmale', 'carbonara'],
        links: [
          { source: 'mamaliga', target: 'sarmale' },
          { source: 'mamaliga', target: 'somon' },
          { source: 'mamaliga', target: 'carbonara' },
          { source: 'carbonara', target: 'somon' }
        ]
      },
      0: {
        nodes: ['mamaliga', 'sarmale', 'papanasi', 'carbonara', 'somon', 'curry'],
        links: [
          { source: 'mamaliga', target: 'sarmale' },
          { source: 'mamaliga', target: 'somon' },
          { source: 'mamaliga', target: 'carbonara' },
          { source: 'sarmale', target: 'papanasi' },
          { source: 'sarmale', target: 'curry' },
          { source: 'somon', target: 'curry' },
          { source: 'carbonara', target: 'somon' },
          { source: 'carbonara', target: 'papanasi' }
        ]
      }
    };

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

    let currentLayer = 2;
    let currentNode = null;
    let visitedLinks = []; // list of { source, target, layer }
    let verticalTransitions = []; // list of { nodeId, fromLayer, toLayer }
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

    function drawGraph() {
      const svgNodes = document.getElementById('hnswNodes');
      const svgLinks = document.getElementById('hnswLinks');
      if (!svgNodes || !svgLinks) return;

      svgNodes.innerHTML = '';
      svgLinks.innerHTML = '';

      // 1. Draw horizontal layer dividers
      [85, 165].forEach(y => {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', '10');
        line.setAttribute('y1', y);
        line.setAttribute('x2', '490');
        line.setAttribute('y2', y);
        line.setAttribute('stroke', 'rgba(255,255,255,0.06)');
        line.setAttribute('stroke-width', '1');
        line.setAttribute('stroke-dasharray', '5,5');
        svgLinks.appendChild(line);
      });

      // 2. Draw vertical projection lines connecting identical nodes across layers
      const nodesAcrossLayers = [
        { id: 'mamaliga', x: 180, startL: 2, endL: 0 },
        { id: 'somon', x: 320, startL: 2, endL: 0 },
        { id: 'sarmale', x: 100, startL: 1, endL: 0 },
        { id: 'carbonara', x: 400, startL: 1, endL: 0 }
      ];

      nodesAcrossLayers.forEach(node => {
        const yStart = 50 + (2 - node.startL) * 80;
        const yEnd = 50 + (2 - node.endL) * 80;

        // Check if this vertical path was active in transition history
        const isActive = verticalTransitions.some(t => 
          t.nodeId === node.id && 
          ((t.fromLayer === 2 && t.toLayer === 1 && yStart <= 50 && yEnd >= 130) ||
           (t.fromLayer === 1 && t.toLayer === 0 && yStart <= 130 && yEnd >= 210))
        );

        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', node.x);
        line.setAttribute('y1', yStart);
        line.setAttribute('x2', node.x);
        line.setAttribute('y2', yEnd);
        line.setAttribute('stroke', isActive ? 'var(--amber)' : 'rgba(255,255,255,0.06)');
        line.setAttribute('stroke-width', isActive ? '2' : '1');
        line.setAttribute('stroke-dasharray', isActive ? 'none' : '2,4');
        svgLinks.appendChild(line);
      });

      // 3. Draw horizontal active/visited links for each layer
      [2, 1, 0].forEach(L => {
        const y = 50 + (2 - L) * 80;
        layers[L].links.forEach(link => {
          const sNode = graphNodes[link.source];
          const tNode = graphNodes[link.target];
          
          const isVisited = visitedLinks.some(vl => 
            vl.layer === L && 
            ((vl.source === link.source && vl.target === link.target) ||
             (vl.source === link.target && vl.target === link.source))
          );

          const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
          line.setAttribute('x1', sNode.x);
          line.setAttribute('y1', y);
          line.setAttribute('x2', tNode.x);
          line.setAttribute('y2', y);
          line.setAttribute('stroke', isVisited ? 'var(--cyan)' : 'rgba(255,255,255,0.08)');
          line.setAttribute('stroke-width', isVisited ? '2.5' : '1.2');
          if (isVisited) {
            line.setAttribute('stroke-dasharray', 'none');
          } else {
            line.setAttribute('stroke-dasharray', '3,3');
          }
          svgLinks.appendChild(line);
        });
      });

      // 4. Draw Layer Info Text Labels in SVG
      const layersLabels = [
        { text: "LAYER 2: Entry Layer (Sparse Hops)", y: 22 },
        { text: "LAYER 1: Express Layer (Medium Hops)", y: 102 },
        { text: "LAYER 0: Base Layer (All Recipes)", y: 182 }
      ];

      const labelGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      layersLabels.forEach(lbl => {
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', '15');
        text.setAttribute('y', lbl.y);
        text.setAttribute('font-size', '8px');
        text.setAttribute('fill', 'rgba(255,255,255,0.3)');
        text.setAttribute('font-weight', 'bold');
        text.textContent = lbl.text;
        labelGroup.appendChild(text);
      });
      svgNodes.appendChild(labelGroup);

      // 5. Draw nodes for each layer
      [2, 1, 0].forEach(L => {
        const y = 50 + (2 - L) * 80;
        layers[L].nodes.forEach(nId => {
          const node = graphNodes[nId];
          const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
          
          const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
          circle.setAttribute('cx', node.x);
          circle.setAttribute('cy', y);
          circle.setAttribute('r', '14');
          
          let fill = 'rgba(255,255,255,0.03)';
          let stroke = 'var(--border)';
          let strokeWidth = '1';

          const isActive = (currentNode === nId && currentLayer === L && !isFinished);
          const isFinishedNode = (isFinished && currentNode === nId && L === 0);
          
          const wasVisited = (currentNode === nId && currentLayer === L) ||
                             visitedLinks.some(vl => (vl.source === nId || vl.target === nId) && vl.layer === L) || 
                             verticalTransitions.some(vt => vt.nodeId === nId && (vt.fromLayer === L || vt.toLayer === L));

          if (isFinishedNode) {
            fill = 'rgba(16,185,129,0.2)';
            stroke = 'var(--emerald)';
            strokeWidth = '2.5';
          } else if (isActive) {
            fill = 'rgba(245,158,11,0.25)';
            stroke = 'var(--amber)';
            strokeWidth = '2.5';
          } else if (wasVisited) {
            fill = 'rgba(6,182,212,0.15)';
            stroke = 'var(--cyan)';
            strokeWidth = '1.8';
          }

          circle.setAttribute('fill', fill);
          circle.setAttribute('stroke', stroke);
          circle.setAttribute('stroke-width', strokeWidth);
          g.appendChild(circle);

          const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
          text.setAttribute('x', node.x);
          text.setAttribute('y', y + 3);
          text.setAttribute('text-anchor', 'middle');
          text.setAttribute('font-size', '7.5px');
          text.setAttribute('fill', '#fff');
          text.setAttribute('font-weight', 'bold');
          text.textContent = node.label.substring(0, 5);
          g.appendChild(text);

          const titleEl = document.createElementNS('http://www.w3.org/2000/svg', 'title');
          titleEl.textContent = `${node.label} (Layer ${L})`;
          g.appendChild(titleEl);

          svgNodes.appendChild(g);
        });
      });
    }

    startBtn.addEventListener('click', () => {
      currentLayer = 2;
      currentNode = 'mamaliga';
      visitedLinks = [];
      verticalTransitions = [];
      isFinished = false;
      querySelect.disabled = true;
      startBtn.disabled = true;
      nextBtn.disabled = false;
      
      const targetQuery = targets[querySelect.value];
      const startSim = getCosineSimilarity(graphNodes.mamaliga.val, targetQuery.vector);

      statusText.innerHTML = `Indexul HNSW a fost inițializat.<br>
        <strong>Nod Curent:</strong> Mămăligă (Punct de intrare)<br>
        <strong>Strat Curent:</strong> Layer 2 (Top sparse)<br>
        <strong>Similitudine inițială:</strong> ${startSim.toFixed(3)}<br>
        Apasă 'Pasul Următor' pentru a evalua vecinii din acest strat.`;
      
      drawGraph();
    });

    nextBtn.addEventListener('click', () => {
      if (!currentNode || isFinished) return;

      const targetVal = querySelect.value;
      const targetQuery = targets[targetVal];
      const curSim = getCosineSimilarity(graphNodes[currentNode].val, targetQuery.vector);

      // Find neighbors of currentNode in the currentLayer
      const neighbors = [];
      layers[currentLayer].links.forEach(link => {
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
        // We found a better neighbor in the current layer: HOP
        visitedLinks.push({ source: currentNode, target: bestNeighbor, layer: currentLayer });
        const oldLabel = graphNodes[currentNode].label;
        currentNode = bestNeighbor;
        const newLabel = graphNodes[currentNode].label;

        statusText.innerHTML = `Săritură în <strong>Layer ${currentLayer}</strong>:<br>
          De la <strong>${oldLabel}</strong> la <strong>${newLabel}</strong><br>
          <strong>Similitudine nouă:</strong> ${bestSim.toFixed(3)} (Mai bună)<br>
          Apasă din nou 'Pasul Următor'.`;

        drawGraph();
      } else {
        // No better neighbor in the current layer: DROP LAYER or FINISH
        if (currentLayer > 0) {
          const nextLayer = currentLayer - 1;
          verticalTransitions.push({ nodeId: currentNode, fromLayer: currentLayer, toLayer: nextLayer });
          
          statusText.innerHTML = `Niciun vecin în <strong>Layer ${currentLayer}</strong> nu este mai apropiat.<br>
            Coborâm la <strong>Layer ${nextLayer}</strong> la nodul <strong>${graphNodes[currentNode].label}</strong>.<br>
            Apasă 'Pasul Următor' pentru a continua căutarea locală în noul strat.`;
            
          currentLayer = nextLayer;
          drawGraph();
        } else {
          // We are already at Layer 0 and no neighbor is better: FINISHED!
          isFinished = true;
          nextBtn.disabled = true;
          const finalLabel = graphNodes[currentNode].label;
          
          statusText.innerHTML = `<strong>Căutare HNSW finalizată!</strong><br>
            <strong>Nod Final găsit:</strong> ${finalLabel}<br>
            <strong>Similitudine maximă:</strong> ${curSim.toFixed(3)}<br>
            Algoritmul s-a oprit deoarece am atins un minim local în Layer 0. Am localizat rețeta optimă prin analizarea a doar câtorva noduri din graf.`;

          drawGraph();
        }
      }
    });

    resetBtn.addEventListener('click', () => {
      currentLayer = 2;
      currentNode = null;
      visitedLinks = [];
      verticalTransitions = [];
      isFinished = false;
      querySelect.disabled = false;
      startBtn.disabled = false;
      nextBtn.disabled = true;
      statusText.innerHTML = "Apasă 'Inițializează Căutare' pentru a plasa punctul de intrare.";
      drawGraph();
    });

    // Initial draw
    drawGraph();
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

  // ── Culinary Galaxy Particle Simulator ────────────────────────────────────
  function initCulinaryGalaxy() {
    const canvas = document.getElementById('galaxyCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const select = document.getElementById('galaxySeedSelect');
    const selectedTitle = document.getElementById('galaxySelectedTitle');
    const selectedDesc = document.getElementById('galaxySelectedDesc');
    const list = document.getElementById('galaxyCompanionsList');
    const useInCreatorBtn = document.getElementById('galaxyUseInCreatorBtn');
    const useInChatBtn = document.getElementById('galaxyUseInChatBtn');

    // Handle high DPI
    const devicePixelRatio = window.devicePixelRatio || 1;
    const originalWidth = 650;
    const originalHeight = 500;
    canvas.width = originalWidth * devicePixelRatio;
    canvas.height = originalHeight * devicePixelRatio;
    canvas.style.width = originalWidth + "px";
    canvas.style.height = originalHeight + "px";
    ctx.scale(devicePixelRatio, devicePixelRatio);

    const cx = originalWidth / 2;
    const cy = originalHeight / 2;

    const galaxyIngredients = [
      { name: "chicken", label: "pui", category: "protein", color: "#ec4899", desc: "Proteina centrala versatila, compatibila cu profiluri aromatice ierboase, usturoiate si citrice.", companions: [{ name: "garlic", score: 0.88 }, { name: "rosemary", score: 0.85 }, { name: "lemon", score: 0.82 }, { name: "butter", score: 0.79 }] },
      { name: "beef", label: "vita", category: "protein", color: "#ec4899", desc: "Carne rosie cu gust bogat, ideala pentru fripturi lente, burgeri sau sosuri consistente.", companions: [{ name: "onion", score: 0.84 }, { name: "garlic", score: 0.82 }, { name: "butter", score: 0.78 }, { name: "rosemary", score: 0.75 }] },
      { name: "shrimp", label: "creveti", category: "protein", color: "#ec4899", desc: "Fructe de mare delicate cu timp rapid de gatire, excelente cu sosuri acidulate si ierburi aromate.", companions: [{ name: "garlic", score: 0.91 }, { name: "lemon", score: 0.88 }, { name: "butter", score: 0.85 }, { name: "cilantro", score: 0.78 }] },
      { name: "salmon", label: "somon", category: "protein", color: "#ec4899", desc: "Peste gras bogat in acizi grasi Omega-3, cu gust pregnant, perfect pentru coacere sau grill.", companions: [{ name: "lemon", score: 0.90 }, { name: "butter", score: 0.84 }, { name: "garlic", score: 0.81 }, { name: "basil", score: 0.76 }] },
      { name: "tofu", label: "tofu", category: "protein", color: "#ec4899", desc: "Proteina vegetala din soia, absoarbe excelent marinadele si sosurile cu arome picante sau asiatice.", companions: [{ name: "ginger", score: 0.89 }, { name: "garlic", score: 0.85 }, { name: "onion", score: 0.78 }, { name: "chili", score: 0.76 }] },
      
      { name: "garlic", label: "usturoi", category: "vegetable", color: "#10b981", desc: "Ingredient aromatic fundamental, utilizat universal pentru a potenta gustul preparatelor sarate.", companions: [{ name: "olive oil", score: 0.94 }, { name: "onion", score: 0.89 }, { name: "chicken", score: 0.88 }, { name: "tomato", score: 0.85 }] },
      { name: "onion", label: "ceapa", category: "vegetable", color: "#10b981", desc: "Baza oricarui sos sau mancare gatita, ofera dulceata prin caramelizare sau iutime in stare cruda.", companions: [{ name: "garlic", score: 0.89 }, { name: "beef", score: 0.84 }, { name: "tomato", score: 0.82 }, { name: "butter", score: 0.80 }] },
      { name: "tomato", label: "rosii", category: "vegetable", color: "#10b981", desc: "Fruct zemos si acidulat, baza multor sosuri clasice, supe si salate proaspete de vara.", companions: [{ name: "basil", score: 0.95 }, { name: "olive oil", score: 0.91 }, { name: "garlic", score: 0.85 }, { name: "cheese", score: 0.83 }] },
      { name: "basil", label: "busuioc", category: "vegetable", color: "#10b981", desc: "Iarba aromatica proaspata si dulceaga, specifica bucatariei mediteraneene si sosului pesto.", companions: [{ name: "tomato", score: 0.95 }, { name: "olive oil", score: 0.92 }, { name: "cheese", score: 0.84 }, { name: "garlic", score: 0.81 }] },
      { name: "rosemary", label: "rozmarin", category: "vegetable", color: "#10b981", desc: "Iarba aromatica cu frunze aciculare si aroma puternica de pin, potrivita pentru fripturi la cuptor.", companions: [{ name: "garlic", score: 0.86 }, { name: "chicken", score: 0.85 }, { name: "butter", score: 0.81 }, { name: "beef", score: 0.75 }] },
      { name: "ginger", label: "ghimbir", category: "vegetable", color: "#10b981", desc: "Radacina picanta si proaspata, ideala in bucataria asiatica, ceaiuri, dulciuri sau sosuri curry.", companions: [{ name: "garlic", score: 0.89 }, { name: "tofu", score: 0.89 }, { name: "honey", score: 0.84 }, { name: "chili", score: 0.81 }] },
      { name: "lemon", label: "lamaie", category: "vegetable", color: "#10b981", desc: "Fruct citric folosit pentru aroma si aciditate.", companions: [{ name: "salmon", score: 0.90 }, { name: "shrimp", score: 0.88 }, { name: "chicken", score: 0.82 }, { name: "honey", score: 0.80 }] },
      { name: "cilantro", label: "coriandru", category: "vegetable", color: "#10b981", desc: "Iarba aromatica proaspata si citrica, esentiala in bucataria mexicana si asiatica.", companions: [{ name: "shrimp", score: 0.78 }, { name: "chili", score: 0.77 }, { name: "onion", score: 0.75 }, { name: "garlic", score: 0.72 }] },
      
      { name: "butter", label: "unt", category: "dairy", color: "#06b6d4", desc: "Grasime bogata obtinuta din lapte, adauga textura cremoasa si savoare de neegalat preparatelor.", companions: [{ name: "garlic", score: 0.86 }, { name: "shrimp", score: 0.85 }, { name: "chicken", score: 0.79 }, { name: "onion", score: 0.80 }] },
      { name: "cheese", label: "branza", category: "dairy", color: "#06b6d4", desc: "Produs lactat variat, de la fin si cremos la maturat si sarat, perfect pentru gratinat.", companions: [{ name: "basil", score: 0.84 }, { name: "tomato", score: 0.83 }, { name: "olive oil", score: 0.79 }, { name: "garlic", score: 0.71 }] },
      { name: "cream", label: "smantana", category: "dairy", color: "#06b6d4", desc: "Smantana grasa fermentata sau dulce, ideala pentru sosuri catifelate sau echilibrarea condimentelor.", companions: [{ name: "chicken", score: 0.78 }, { name: "butter", score: 0.76 }, { name: "vanilla", score: 0.74 }, { name: "chocolate", score: 0.72 }] },
      { name: "olive oil", label: "ulei de masline", category: "dairy", color: "#06b6d4", desc: "Ulei vegetal sanatos, baza sosurilor reci si a calirii legumelor in bucataria mediteraneana.", companions: [{ name: "garlic", score: 0.94 }, { name: "basil", score: 0.92 }, { name: "tomato", score: 0.91 }, { name: "cheese", score: 0.79 }] } ,

      { name: "honey", label: "miere", category: "spice", color: "#f59e0b", desc: "Indulcitor natural cu note florale.", companions: [{ name: "lemon", score: 0.80 }, { name: "ginger", score: 0.84 }, { name: "cinnamon", score: 0.79 }, { name: "chicken", score: 0.78 }] },
      { name: "cinnamon", label: "scortisoara", category: "spice", color: "#f59e0b", desc: "Condiment cald cu aroma dulce-lemnoasa.", companions: [{ name: "honey", score: 0.79 }, { name: "vanilla", score: 0.82 }, { name: "chocolate", score: 0.75 }, { name: "butter", score: 0.70 }] },
      { name: "vanilla", label: "vanilie", category: "spice", color: "#f59e0b", desc: "Aroma exotica dulce si delicata.", companions: [{ name: "chocolate", score: 0.88 }, { name: "cinnamon", score: 0.82 }, { name: "cream", score: 0.74 }, { name: "honey", score: 0.71 }] },
      { name: "chocolate", label: "ciocolata", category: "spice", color: "#f59e0b", desc: "Derivat bogat si dulce din cacao.", companions: [{ name: "vanilla", score: 0.88 }, { name: "chili", score: 0.80 }, { name: "cinnamon", score: 0.75 }, { name: "cream", score: 0.72 }] },
      { name: "chili", label: "chili", category: "spice", color: "#f59e0b", desc: "Ardei iute, adauga caldura si intensitate.", companions: [{ name: "chocolate", score: 0.80 }, { name: "ginger", score: 0.81 }, { name: "garlic", score: 0.78 }, { name: "cilantro", score: 0.77 }] }
    ];

    let activeSeedName = "chicken";

    // Populate dropdown
    select.innerHTML = galaxyIngredients.map(ing => `
      <option value="${ing.name}">${ing.label.toUpperCase()}</option>
    `).join('');
    select.value = activeSeedName;

    // Simulation nodes setup
    const nodes = galaxyIngredients.map((ing, idx) => {
      return {
        ...ing,
        angle: Math.random() * Math.PI * 2,
        speed: 0.0015 + Math.random() * 0.002,
        currentRadius: 180 + idx * 8,
        targetRadius: 180 + idx * 8,
        x: cx,
        y: cy
      };
    });

    function updateActiveSeed(name) {
      activeSeedName = name;
      select.value = name;
      const seedNode = nodes.find(n => n.name === name);
      if (!seedNode) return;

      // Update sidebar title and description
      selectedTitle.textContent = seedNode.label.toUpperCase();
      selectedTitle.style.color = seedNode.color;
      selectedDesc.textContent = seedNode.desc;

      // Update companion sidebar list
      const companionNames = seedNode.companions.map(c => c.name);
      const sortedCompanions = seedNode.companions.slice().sort((a, b) => b.score - a.score);
      
      list.innerHTML = sortedCompanions.map(c => {
        const matchingNode = nodes.find(n => n.name === c.name);
        const label = matchingNode ? matchingNode.label : c.name;
        const color = matchingNode ? matchingNode.color : "var(--text)";
        return `
          <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.02); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 8px 12px; font-size: 0.82rem;">
            <span style="font-weight: 600; color: ${color};">${label.toUpperCase()}</span>
            <span style="color: var(--text-muted); font-size: 0.76rem;">${Math.round(c.score * 100)}% Sinergie</span>
          </div>
        `;
      }).join('');

      // Recalculate target radii for orbit interpolation
      let companionIndex = 0;
      let nonCompanionIndex = 0;

      nodes.forEach(n => {
        if (n.name === name) {
          n.targetRadius = 0;
        } else {
          const companionObj = seedNode.companions.find(c => c.name === n.name);
          if (companionObj) {
            n.targetRadius = 55 + companionIndex * 35;
            companionIndex++;
          } else {
            n.targetRadius = 210 + nonCompanionIndex * 15;
            nonCompanionIndex++;
          }
        }
      });
    }

    // Canvas rendering loop
    let mouseX = -1000;
    let mouseY = -1000;

    canvas.addEventListener('mousemove', (e) => {
      const rect = canvas.getBoundingClientRect();
      mouseX = e.clientX - rect.left;
      mouseY = e.clientY - rect.top;
    });

    canvas.addEventListener('mouseleave', () => {
      mouseX = -1000;
      mouseY = -1000;
    });

    canvas.addEventListener('click', () => {
      let closestNode = null;
      let closestDist = 25; // Click radius
      nodes.forEach(n => {
        const d = Math.hypot(n.x - mouseX, n.y - mouseY);
        if (d < closestDist) {
          closestNode = n;
          closestDist = d;
        }
      });

      if (closestNode) {
        updateActiveSeed(closestNode.name);
      }
    });

    select.addEventListener('change', (e) => {
      updateActiveSeed(e.target.value);
    });

    function draw() {
      // Check if canvas container is visible (not tab hidden)
      if (canvas.offsetParent === null) {
        // Skip heavy drawing if galaxy tab is not active
        setTimeout(draw, 100);
        return;
      }

      ctx.clearRect(0, 0, originalWidth, originalHeight);

      // Draw background space elements (orbital tracks)
      ctx.strokeStyle = "rgba(255, 255, 255, 0.03)";
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 6]);
      [55, 90, 125, 160, 210, 240, 270].forEach(r => {
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.stroke();
      });
      ctx.setLineDash([]);

      // Update positions
      nodes.forEach(n => {
        n.angle += n.speed;
        n.currentRadius += (n.targetRadius - n.currentRadius) * 0.06;
        n.x = cx + n.currentRadius * Math.cos(n.angle);
        n.y = cy + n.currentRadius * Math.sin(n.angle);
      });

      // Draw connection lines to active seed's companions
      const seedNode = nodes.find(n => n.name === activeSeedName);
      if (seedNode) {
        nodes.forEach(n => {
          if (n.name !== activeSeedName) {
            const companionObj = seedNode.companions.find(c => c.name === n.name);
            if (companionObj) {
              ctx.beginPath();
              ctx.moveTo(seedNode.x, seedNode.y);
              ctx.lineTo(n.x, n.y);
              ctx.lineWidth = 1.5;
              const grad = ctx.createLinearGradient(seedNode.x, seedNode.y, n.x, n.y);
              grad.addColorStop(0, seedNode.color);
              grad.addColorStop(1, n.color);
              ctx.strokeStyle = grad;
              ctx.shadowColor = n.color;
              ctx.shadowBlur = 8;
              ctx.stroke();
              ctx.shadowBlur = 0;
            }
          }
        });
      }

      // Draw center core glow
      if (seedNode) {
        ctx.beginPath();
        ctx.arc(seedNode.x, seedNode.y, 22, 0, Math.PI * 2);
        const radialGrad = ctx.createRadialGradient(seedNode.x, seedNode.y, 0, seedNode.x, seedNode.y, 22);
        radialGrad.addColorStop(0, "rgba(255,255,255,0.4)");
        radialGrad.addColorStop(0.3, seedNode.color);
        radialGrad.addColorStop(1, "rgba(0,0,0,0)");
        ctx.fillStyle = radialGrad;
        ctx.shadowColor = seedNode.color;
        ctx.shadowBlur = 15;
        ctx.fill();
        ctx.shadowBlur = 0;
      }

      // Draw nodes
      let hoveredNode = null;
      nodes.forEach(n => {
        const isHovered = Math.hypot(n.x - mouseX, n.y - mouseY) < 12;
        if (isHovered) hoveredNode = n;

        ctx.beginPath();
        const nodeRadius = n.name === activeSeedName ? 10 : (isHovered ? 8 : 5);
        ctx.arc(n.x, n.y, nodeRadius, 0, Math.PI * 2);
        ctx.fillStyle = n.color;
        
        if (n.name === activeSeedName || isHovered) {
          ctx.shadowColor = n.color;
          ctx.shadowBlur = 10;
        }
        ctx.fill();
        ctx.shadowBlur = 0;

        // Label
        if (n.name !== activeSeedName) {
          ctx.font = isHovered ? "bold 11px Outfit" : "10px Outfit";
          ctx.fillStyle = isHovered ? "#fff" : "var(--text-muted)";
          ctx.fillText(n.label.toUpperCase(), n.x + 8, n.y + 3);
        }
      });

      // Draw central label
      if (seedNode) {
        ctx.font = "bold 12px Outfit";
        ctx.fillStyle = "#fff";
        ctx.shadowColor = "rgba(0,0,0,0.5)";
        ctx.shadowBlur = 4;
        ctx.fillText(seedNode.label.toUpperCase(), seedNode.x - 12, seedNode.y - 14);
        ctx.shadowBlur = 0;
      }

      // Draw hover tooltip on canvas
      if (hoveredNode) {
        ctx.fillStyle = "rgba(13, 18, 32, 0.95)";
        ctx.strokeStyle = hoveredNode.color;
        ctx.lineWidth = 1;
        
        const tooltipX = mouseX + 10;
        const tooltipY = mouseY - 45;
        
        ctx.beginPath();
        ctx.roundRect(tooltipX, tooltipY, 150, 36, 6);
        ctx.fill();
        ctx.stroke();

        ctx.font = "bold 11px Outfit";
        ctx.fillStyle = hoveredNode.color;
        ctx.fillText(hoveredNode.label.toUpperCase(), tooltipX + 8, tooltipY + 16);

        ctx.font = "9px Outfit";
        ctx.fillStyle = "var(--text-muted)";
        ctx.fillText(hoveredNode.category.toUpperCase(), tooltipX + 8, tooltipY + 28);
      }

      requestAnimationFrame(draw);
    }

    // Bind action buttons
    useInCreatorBtn.addEventListener('click', () => {
      const seedNode = nodes.find(n => n.name === activeSeedName);
      if (!seedNode) return;

      // Clear creator tags
      tags = [];
      addTag(seedNode.label);
      seedNode.companions.forEach(c => {
        const match = nodes.find(n => n.name === c.name);
        if (match) {
          addTag(match.label);
        }
      });

      // Switch tab to Creator
      const creatorTabBtn = document.querySelector('.tab-button[data-tab="creator"]');
      if (creatorTabBtn) {
        creatorTabBtn.click();
      }

      // Auto trigger recipe invention!
      if (typeof handleInvent === 'function') {
        handleInvent();
      }
    });

    useInChatBtn.addEventListener('click', () => {
      const seedNode = nodes.find(n => n.name === activeSeedName);
      if (!seedNode) return;

      const companionsLabels = seedNode.companions.map(c => {
        const match = nodes.find(n => n.name === c.name);
        return match ? match.label : c.name;
      });

      const allIngs = [seedNode.label, ...companionsLabels].join(', ');
      const promptText = `Propune o reteta inventiva care sa combine armonios urmatoarele ingrediente: ${allIngs}. Explica profilul de aroma rezultat.`;

      // Switch tab to Chatbot first
      const chatbotTabBtn = document.querySelector('.tab-button[data-tab="chatbot"]');
      if (chatbotTabBtn) {
        chatbotTabBtn.click();
      }

      // Populate iframe input and trigger send
      setTimeout(() => {
        const iframe = document.querySelector('.chatbot-container iframe');
        if (iframe && iframe.contentWindow) {
          try {
            // Direct DOM manipulation (extremely reliable on same-origin)
            const iframeDoc = iframe.contentWindow.document;
            const chatInput = iframeDoc.getElementById('chatInput');
            if (chatInput) {
              chatInput.value = promptText;
              chatInput.focus();
              
              // Call the global sendMessage function directly from the iframe's window scope
              if (typeof iframe.contentWindow.sendMessage === 'function') {
                iframe.contentWindow.sendMessage();
              } else {
                const sendBtn = iframeDoc.getElementById('sendBtn');
                if (sendBtn) sendBtn.click();
              }
              console.log("Direct iframe recipe prompt submitted successfully.");
              return; // Success
            }
          } catch (err) {
            console.warn("Direct iframe access failed, falling back to postMessage:", err);
          }
          
          // Fallback to postMessage
          iframe.contentWindow.postMessage({ action: "suggestRecipe", query: promptText }, "*");
        }
      }, 300);
    });

    // Start
    updateActiveSeed("chicken");
    draw();
  }

  initHnswSimulator();
  initShowdown();
  initThematicExplorer();
  initCulinaryGalaxy();
}

// ── HNSW Navigator Functions ──────────────────────────────────────────────
let selectedHNSWRecipe = null;
let hnswResults = [];

async function searchHNSW() {
  const query = document.getElementById('hnswQueryInput').value.trim();
  if (!query) {
    alert('Introduceți o interogare!');
    return;
  }

  const statusDiv = document.getElementById('hnswStatus');
  const resultsDiv = document.getElementById('hnswResultsList');
  const statsDiv = document.getElementById('hnswStats');
  const sendBtn = document.getElementById('hnswSendCreatorBtn');

  statusDiv.textContent = '🔄 Se caută cu HNSW...';
  resultsDiv.innerHTML = '';
  selectedHNSWRecipe = null;
  sendBtn.disabled = true;
  sendBtn.style.opacity = '0.5';

  try {
    const response = await fetch(`${API}/api/hnsw/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, target_recipe_id: null })
    });

    if (!response.ok) throw new Error('HNSW search failed');
    const data = await response.json();
    hnswResults = data.final_candidates || [];

    // Display results
    resultsDiv.innerHTML = hnswResults.map((recipe, idx) => `
      <div onclick="selectHNSWRecipe(${idx})" style="padding: 12px; background: rgba(6, 182, 212, 0.1); border: 1px solid rgba(6, 182, 212, 0.3); border-radius: var(--radius-sm); cursor: pointer; transition: all 0.3s ease; hover:background rgba(6, 182, 212, 0.2);">
        <div style="font-weight: 600; color: var(--cyan); font-size: 0.9rem; margin-bottom: 4px;">${idx + 1}. ${recipe.recipe_title}</div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <div style="flex: 1; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden;">
            <div style="height: 100%; width: ${recipe.similarity * 100}%; background: linear-gradient(90deg, var(--cyan), var(--emerald)); border-radius: 3px;"></div>
          </div>
          <div style="font-weight: 600; color: var(--cyan); font-size: 0.8rem; min-width: 45px;">${(recipe.similarity * 100).toFixed(1)}%</div>
        </div>
      </div>
    `).join('');

    // Show stats
    statsDiv.style.display = 'grid';
    statsDiv.innerHTML = `
      <div style="background: rgba(124, 58, 237, 0.1); border: 1px solid rgba(124, 58, 237, 0.2); padding: 16px; border-radius: var(--radius-sm);">
        <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 4px;">Total Pași</div>
        <div style="font-size: 1.3rem; font-weight: 700; color: var(--violet-lt);">${data.total_steps}</div>
      </div>
      <div style="background: rgba(6, 182, 212, 0.1); border: 1px solid rgba(6, 182, 212, 0.2); padding: 16px; border-radius: var(--radius-sm);">
        <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 4px;">Noduri Vizitate</div>
        <div style="font-size: 1.3rem; font-weight: 700; color: var(--cyan);">${data.visited_nodes.length}</div>
      </div>
      <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); padding: 16px; border-radius: var(--radius-sm);">
        <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 4px;">Entry Recipe</div>
        <div style="font-size: 0.9rem; font-weight: 600; color: var(--emerald);">${data.entry_recipe.substring(0, 20)}...</div>
      </div>
    `;

    statusDiv.textContent = `✅ Găsite ${hnswResults.length} rețete în ${data.total_steps} pași`;
  } catch (error) {
    statusDiv.textContent = `❌ Eroare: ${error.message}`;
    statusDiv.style.color = 'var(--amber)';
  }
}

function selectHNSWRecipe(idx) {
  selectedHNSWRecipe = hnswResults[idx];
  const sendBtn = document.getElementById('hnswSendCreatorBtn');
  sendBtn.disabled = false;
  sendBtn.style.opacity = '1';
  sendBtn.style.cursor = 'pointer';

  // Highlight selected
  document.querySelectorAll('#hnswResultsList > div').forEach((el, i) => {
    if (i === idx) {
      el.style.background = 'rgba(6, 182, 212, 0.3)';
      el.style.borderColor = 'rgba(6, 182, 212, 0.6)';
    } else {
      el.style.background = 'rgba(6, 182, 212, 0.1)';
      el.style.borderColor = 'rgba(6, 182, 212, 0.3)';
    }
  });
}

async function sendHNSWResultToCreator() {
  if (!selectedHNSWRecipe) return;

  // Extract ingredients from selected recipe
  const ingredients = selectedHNSWRecipe.ingredients || [];
  const recipeName = selectedHNSWRecipe.recipe_title;

  // Switch to Creator tab
  const creatorTabBtn = document.querySelector('.tab-button[data-tab="creator"]');
  if (creatorTabBtn) {
    creatorTabBtn.click();
  }

  // Add ingredients to Creator
  setTimeout(() => {
    // Global tags array from Creator
    if (typeof tags !== 'undefined' && Array.isArray(tags)) {
      tags = []; // Clear existing
      ingredients.forEach(ing => {
        if (ing && ing.trim()) {
          addTag(ing.trim());
        }
      });
    }

    // Show notification
    const notif = document.createElement('div');
    notif.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: linear-gradient(135deg, var(--emerald), var(--cyan));
      color: white;
      padding: 14px 20px;
      border-radius: 8px;
      font-weight: 600;
      z-index: 10000;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
      animation: slideIn 0.3s ease-out;
    `;
    notif.textContent = `✅ ${ingredients.length} ingrediente din "${recipeName}" adăugate`;
    document.body.appendChild(notif);
    setTimeout(() => notif.remove(), 3000);

    // Auto-trigger invention
    if (typeof handleInvent === 'function') {
      setTimeout(() => handleInvent(), 500);
    }
  }, 300);
}

// Listen to message events from standalone HNSW tab/window
window.addEventListener('message', (event) => {
  const data = event.data;
  if (data && data.type === 'HNSW_ADD_INGREDIENTS') {
    const ingredients = data.ingredients || [];
    const recipeName = data.recipe || 'Rețetă';

    // Switch to Creator tab
    const creatorTabBtn = document.querySelector('.tab-button[data-tab="creator"]');
    if (creatorTabBtn) {
      creatorTabBtn.click();
    }

    setTimeout(() => {
      if (typeof tags !== 'undefined' && Array.isArray(tags)) {
        // Clear existing tags array
        tags.length = 0;
        
        // Clear visual tags from DOM
        const tagsUl = document.getElementById('tagsList');
        if (tagsUl) tagsUl.innerHTML = '';
        
        ingredients.forEach(ing => {
          if (ing && ing.trim()) {
            addTag(ing.trim());
          }
        });
      }

      // Show notification
      const notif = document.createElement('div');
      notif.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, var(--emerald), var(--cyan));
        color: white;
        padding: 14px 20px;
        border-radius: 8px;
        font-weight: 600;
        z-index: 10000;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        animation: slideIn 0.3s ease-out;
      `;
      notif.textContent = `✅ ${ingredients.length} ingrediente din "${recipeName}" adăugate în Creator`;
      document.body.appendChild(notif);
      setTimeout(() => notif.remove(), 3000);

      // Auto-trigger invention
      if (typeof handleInvent === 'function') {
        setTimeout(() => handleInvent(), 500);
      }
    }, 300);
  }
});

// ── Boot ──────────────────────────────────────────────────────────────────
init();

