/**
 * app.js — AI Recipe Inventor frontend logic
 *
 * Responsibilities:
 *  - Tag-based ingredient input (Enter / comma to add, ✕ to remove)
 *  - Quick suggestion buttons
 *  - Fetch /api/stats and /api/cuisines on load
 *  - POST /api/invent → render animated recipe cards
 *  - Collapsible Steps / Explanation / Tips sections
 *  - "Show all steps" toggle inside cards
 *  - Loading + error states
 */

'use strict';

const API = window.location.origin;

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
      opt.textContent = `🍽 ${c}`;
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
    btn.textContent = '✕';
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
}

// ── Invent ────────────────────────────────────────────────────────────────
async function handleInvent() {
  // Commit any pending input
  const pending = ingredientInput.value.trim().replace(/,$/, '');
  if (pending) { addTag(pending); ingredientInput.value = ''; }

  if (tags.length === 0) {
    ingredientInput.placeholder = '⚠ Adaugă măcar un ingredient!';
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

// ── Render results ────────────────────────────────────────────────────────
function showResults(data) {
  recipesGrid.innerHTML = '';

  // Initialize current recipes for shopping list
  window.currentRecipes = data.recipes || [];

  resultsMeta.textContent =
    `${data.recipes.length} rețete inventate • bazate pe ${data.retrieved_count} rețete similare ` +
    `din baza de date de ${data.total_db?.toLocaleString('ro') ?? '300+'} intrări`;

  data.recipes.forEach((recipe, idx) => {
    const card = buildCard(recipe, idx, data.query || tags);
    recipesGrid.appendChild(card);
  });

  loadingOverlay.classList.add('hidden');
  resultsSection.classList.remove('hidden');
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

  const diffEmoji = { 'Easy': '🟢', 'Medium': '🟡', 'Hard': '🔴' }[recipe.difficulty] || '🟡';

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

  card.innerHTML = `
    <div class="card-stripe"></div>
    <div class="card-body">

      <h3 class="card-title">${esc(recipe.title)}</h3>

      <div class="badges">
        <span class="badge badge-cuisine">🌍 ${esc(recipe.cuisine)}</span>
        <span class="badge ${diffClass}">${diffEmoji} ${esc(recipe.difficulty)}</span>
        <span class="badge badge-time">⏱ ${recipe.time_minutes} min</span>
        <span class="badge badge-servings">👥 ${recipe.servings} porții</span>
      </div>

      <!-- Ingredients -->
      <div class="card-section">
        <div class="section-header">
          <span>🥬 Ingrediente (${recipe.ingredients?.length ?? 0})</span>
        </div>
        <div class="ingredients-list">${ingHTML}</div>
      </div>

      <!-- Steps -->
      <div class="card-section">
        <div class="section-header toggle-header" data-target="steps-${idx}">
          <span>📋 Pași de preparare</span>
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
          <span>🔬 De ce funcționează?</span>
          <span class="toggle-icon">▼</span>
        </div>
        <div class="collapsible open" id="expl-${idx}">
          <div class="explanation-box">${formatExplanation(recipe.explanation)}</div>
          ${recipe.cuisine_note ? `<p class="cuisine-note">${esc(recipe.cuisine_note)}</p>` : ''}
        </div>
      </div>

      <!-- Tips -->
      ${tipsHTML ? `
      <div class="card-section">
        <div class="section-header toggle-header" data-target="tips-${idx}">
          <span>💡 Sfaturi pro</span>
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
        ✨ Inspirat din: <em>${esc(recipe.inspired_by || '—')}</em>
        ${recipe.key_technique ? `· Tehnică cheie: <em>${esc(recipe.key_technique)}</em>` : ''}
      </p>

      <!-- Shopping List Button -->
      <div class="card-section" style="margin-top: 20px; display: flex; gap: 8px;">
        <button class="btn-invent" onclick="addToShoppingList(${idx})" style="flex: 1; padding: 10px 16px;">
          🛒 Adaugă la Shopping
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

// ── Boot ──────────────────────────────────────────────────────────────────
init();
