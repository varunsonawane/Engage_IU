const BASE_URL = window.location.origin;

function getToken() { return localStorage.getItem('engageiu_token'); }
function setToken(t) { localStorage.setItem('engageiu_token', t); }
function clearToken() { localStorage.removeItem('engageiu_token'); }
function isAdmin() { return !!getToken(); }

function authHeaders() {
  const token = getToken();
  const h = { 'Content-Type': 'application/json' };
  if (token) h['Authorization'] = `Bearer ${token}`;
  return h;
}

async function api(method, path, body = null, requiresAuth = false) {
  const opts = {
    method,
    headers: requiresAuth ? authHeaders() : { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(BASE_URL + path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

function formatDate(isoStr) {
  if (!isoStr) return '';
  return new Date(isoStr).toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric', year: 'numeric'
  });
}

function formatDateTime(isoStr) {
  if (!isoStr) return '';
  return new Date(isoStr).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
  });
}

function formatWeekRange(startIso, endIso) {
  if (!startIso || !endIso) return '';
  const s = new Date(startIso);
  const e = new Date(endIso);
  const fmt = d => d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  return `${fmt(s)} to ${fmt(e)}, ${e.getFullYear()}`;
}

const CAMPUSES = [
  'IU Bloomington', 'IU Indianapolis', 'IU East', 'IU Kokomo',
  'IU Northwest', 'IU South Bend', 'IU Southeast', 'IU Columbus', 'IU Fort Wayne',
];

function campusOptions(includeAll = true, selectedValue = '') {
  let html = includeAll ? `<option value="">All Campuses</option>` : '';
  CAMPUSES.forEach(c => {
    html += `<option value="${c}" ${c === selectedValue ? 'selected' : ''}>${c}</option>`;
  });
  return html;
}

function openModal(id) {
  document.getElementById(id).classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal(id) {
  document.getElementById(id).classList.remove('open');
  document.body.style.overflow = '';
}

document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
    document.body.style.overflow = '';
  }
});

function showAlert(containerId, message, type = 'error') {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.className = `alert alert-${type}`;
  el.textContent = message;
  el.classList.remove('hidden');
}

function hideAlert(containerId) {
  const el = document.getElementById(containerId);
  if (el) el.classList.add('hidden');
}

function applyAdminState() {
  const adminLinks = document.querySelectorAll('.admin-nav-link');
  if (isAdmin()) {
    document.body.classList.add('admin-logged');
    document.getElementById('btn-admin-login')?.classList.add('hidden');
    document.getElementById('btn-admin-logout')?.classList.remove('hidden');
    adminLinks.forEach(el => el.classList.remove('hidden'));
  } else {
    document.body.classList.remove('admin-logged');
    document.getElementById('btn-admin-login')?.classList.remove('hidden');
    document.getElementById('btn-admin-logout')?.classList.add('hidden');
    adminLinks.forEach(el => el.classList.add('hidden'));
  }
}

async function handleAdminLogin(e) {
  e.preventDefault();
  const username = document.getElementById('admin-username').value.trim();
  const password = document.getElementById('admin-password').value;
  hideAlert('admin-login-alert');
  try {
    const data = await api('POST', '/auth/login', { username, password });
    setToken(data.access_token);
    closeModal('admin-login-modal');
    applyAdminState();
    window.location.reload();
  } catch (err) {
    showAlert('admin-login-alert', err.message);
  }
}

function handleAdminLogout() {
  clearToken();
  applyAdminState();
  window.location.reload();
}

function rankBadge(rank) {
  const cls = rank === 1 ? 'gold' : rank === 2 ? 'silver' : rank === 3 ? 'bronze' : '';
  return `<span class="rank-num ${cls}">${rank}</span>`;
}

function rankLabel(rank) {
  const medals = { 1: '🥇', 2: '🥈', 3: '🥉' };
  return medals[rank] ? `${medals[rank]} ${rank}` : rank;
}

document.addEventListener('DOMContentLoaded', () => {
  applyAdminState();

  const loginForm = document.getElementById('admin-login-form');
  if (loginForm) loginForm.addEventListener('submit', handleAdminLogin);

  document.getElementById('btn-admin-login')?.addEventListener('click', () => openModal('admin-login-modal'));
  document.getElementById('btn-admin-logout')?.addEventListener('click', handleAdminLogout);

  document.querySelectorAll('[data-close-modal]').forEach(btn => {
    btn.addEventListener('click', () => closeModal(btn.dataset.closeModal));
  });

  const hamburger = document.getElementById('nav-hamburger');
  const nav = hamburger?.closest('.nav');
  if (hamburger && nav) {
    hamburger.addEventListener('click', () => {
      const open = nav.classList.toggle('nav-open');
      hamburger.classList.toggle('open', open);
    });
    document.addEventListener('click', e => {
      if (!nav.contains(e.target) && nav.classList.contains('nav-open')) {
        nav.classList.remove('nav-open');
        hamburger.classList.remove('open');
      }
    });
  }
});
