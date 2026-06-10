/* ── admin.js – admin dashboard ── */

const MONTHS_SHORT = ['gen','feb','mar','apr','mag','giu','lug','ago','set','ott','nov','dic'];
const MONTHS_FULL  = ['gennaio','febbraio','marzo','aprile','maggio','giugno',
                      'luglio','agosto','settembre','ottobre','novembre','dicembre'];

let currentStatus    = 'confirmed';
let pendingToConfirm = null;
let confirmModal     = null;

function fmtDateShort(str) {
  const [, m, d] = str.split('-');
  return `${parseInt(d)} ${MONTHS_SHORT[parseInt(m)-1]}`;
}

function fmtDateFull(str) {
  const [y, m, d] = str.split('-');
  return `${parseInt(d)} ${MONTHS_FULL[parseInt(m)-1]} ${y}`;
}

function statusBadge(s) {
  if (s === 'pending')   return '<span class="badge bg-warning text-dark">In attesa</span>';
  if (s === 'confirmed') return '<span class="badge bg-success">Confermata</span>';
  if (s === 'rejected')  return '<span class="badge bg-danger">Rifiutata</span>';
  return '';
}

function cleanPhone(phone) {
  let p = phone.replace(/[^\d+]/g, '');
  if (p.startsWith('0039'))                         p = '+39' + p.slice(4);
  else if (p.startsWith('39') && !p.startsWith('+')) p = '+' + p;
  else if (!p.startsWith('+') && p.startsWith('3') && p.length >= 9) p = '+39' + p;
  return p;
}

function waUrl(phone, name, court, dateStr, time) {
  const msg = `Ciao ${name}! La tua prenotazione per Campo ${court} il ${fmtDateFull(dateStr)} alle ${time} è confermata ✅ A presto! 🎾`;
  return `https://wa.me/${cleanPhone(phone)}?text=${encodeURIComponent(msg)}`;
}

async function loadBookings() {
  const resp     = await fetch('/api/admin/bookings?status=' + currentStatus);
  const bookings = await resp.json();
  renderBookings(bookings);
  refreshBadge();
}

async function refreshBadge() {
  const resp    = await fetch('/api/admin/bookings?status=pending');
  const pending = await resp.json();
  const n       = pending.length;

  const badge    = document.getElementById('pendingBadge');
  const tabBadge = document.getElementById('tabBadge');

  badge.textContent    = n;
  tabBadge.textContent = n;
  badge.classList.toggle('d-none', n === 0);
  document.title = n > 0 ? `(${n}) Admin – Prenotazioni` : 'Admin – Prenotazioni';
}

function renderBookings(bookings) {
  const list = document.getElementById('bookingsList');

  if (!bookings.length) {
    list.innerHTML = `
      <div class="text-center text-muted py-5">
        <i class="bi bi-calendar-check fs-2 d-block mb-2"></i>
        Nessuna prenotazione
      </div>`;
    return;
  }

  list.innerHTML = bookings.map(b => `
    <div class="card mb-3 booking-card status-${b.status}" data-id="${b.id}">
      <div class="card-body py-3">
        <div class="d-flex justify-content-between align-items-start gap-2">
          <div>
            <div class="fw-bold">${b.name}</div>
            <div class="small text-muted mt-1">
              <i class="bi bi-telephone-fill me-1"></i>
              <a href="tel:${b.phone}" class="text-decoration-none">${b.phone}</a>
            </div>
          </div>
          <div class="text-end flex-shrink-0">
            ${statusBadge(b.status)}
            <div class="small text-muted mt-1">
              ${fmtDateShort(b.date)} · ${b.start_time}–${b.end_time}
            </div>
            <div class="small mt-1">
              <span class="badge bg-secondary">Campo ${b.court}</span>
            </div>
          </div>
        </div>

        ${b.status === 'pending' ? `
        <div class="mt-3 d-flex gap-2 flex-wrap">
          <button class="btn btn-success btn-sm confirm-btn"
                  data-id="${b.id}" data-name="${b.name}" data-court="${b.court}"
                  data-date="${b.date}" data-time="${b.start_time}">
            <i class="bi bi-check-lg me-1"></i>Conferma
          </button>
          <button class="btn btn-outline-danger btn-sm reject-btn" data-id="${b.id}">
            <i class="bi bi-x-lg me-1"></i>Rifiuta
          </button>
        </div>` : ''}

        ${b.status === 'confirmed' ? `
        <div class="mt-2 d-flex gap-2 flex-wrap">
          <a href="${waUrl(b.phone, b.name, b.court, b.date, b.start_time)}"
             target="_blank" class="btn btn-sm btn-outline-success">
            <i class="bi bi-whatsapp me-1"></i>Invia messaggio WhatsApp
          </a>
          <button class="btn btn-sm btn-outline-danger cancel-btn" data-id="${b.id}">
            <i class="bi bi-x-circle me-1"></i>Annulla prenotazione
          </button>
        </div>` : ''}
      </div>
    </div>
  `).join('');

  document.querySelectorAll('.confirm-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      pendingToConfirm = parseInt(btn.dataset.id);
      document.getElementById('confirmInfo').innerHTML =
        `<strong>${btn.dataset.name}</strong><br>
         Campo ${btn.dataset.court} · ${fmtDateFull(btn.dataset.date)} ore ${btn.dataset.time}`;
      confirmModal.show();
    });
  });

  document.querySelectorAll('.reject-btn').forEach(btn => {
    btn.addEventListener('click', () => rejectBooking(parseInt(btn.dataset.id)));
  });

  document.querySelectorAll('.cancel-btn').forEach(btn => {
    btn.addEventListener('click', () => cancelBooking(parseInt(btn.dataset.id)));
  });
}

async function cancelBooking(id) {
  if (!confirm('Annullare questa prenotazione? Lo slot tornerà disponibile per altri clienti.')) return;
  await fetch(`/api/admin/bookings/${id}`, { method: 'DELETE' });
  loadBookings();
}

async function confirmBooking() {
  if (!pendingToConfirm) return;
  const resp = await fetch(`/api/admin/bookings/${pendingToConfirm}/confirm`, { method: 'POST' });
  const data = await resp.json();
  confirmModal.hide();
  pendingToConfirm = null;
  if (data.ok) {
    loadBookings();
    window.open(data.wa_url, '_blank');
  }
}

async function rejectBooking(id) {
  if (!confirm('Rifiutare questa prenotazione?')) return;
  await fetch(`/api/admin/bookings/${id}/reject`, { method: 'POST' });
  loadBookings();
}

/* ── Push notifications ────────────────────────── */

function urlB64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64  = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw     = atob(base64);
  return Uint8Array.from([...raw].map(c => c.charCodeAt(0)));
}

async function enablePush() {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    alert('Il tuo browser non supporta le notifiche push.');
    return;
  }
  const { key } = await fetch('/api/push/key').then(r => r.json());
  if (!key) {
    alert('Notifiche push non configurate sul server (VAPID keys mancanti nel .env).');
    return;
  }
  const permission = await Notification.requestPermission();
  if (permission !== 'granted') { alert('Permesso negato.'); return; }

  const reg = await navigator.serviceWorker.register('/static/js/sw.js');
  await navigator.serviceWorker.ready;
  const sub = await reg.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlB64ToUint8Array(key)
  });
  await fetch('/api/push/subscribe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(sub)
  });
  const btn = document.getElementById('enablePushBtn');
  btn.innerHTML = '<i class="bi bi-bell-fill"></i>';
  btn.classList.add('active');
  btn.disabled = true;
  btn.title = 'Notifiche push attive';
}

/* ── Init ──────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
  confirmModal = new bootstrap.Modal(document.getElementById('confirmModal'));

  document.querySelectorAll('[data-status]').forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      document.querySelectorAll('[data-status]').forEach(l => l.classList.remove('active'));
      link.classList.add('active');
      currentStatus = link.dataset.status;
      loadBookings();
    });
  });

  document.getElementById('doConfirm').addEventListener('click', confirmBooking);
  document.getElementById('enablePushBtn').addEventListener('click', enablePush);

  // ── Test email ────────────────────────────────────────────
  document.getElementById('testEmailBtn').addEventListener('click', async () => {
    const btn = document.getElementById('testEmailBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    try {
      const resp = await fetch('/api/admin/test-email');
      const text = await resp.text();
      let data;
      try { data = JSON.parse(text); } catch { data = { ok: false, error: 'Risposta non valida: ' + text.substring(0, 120) }; }
      const toastEl = document.getElementById('emailToast');
      const toastBody = document.getElementById('emailToastBody');
      if (data.ok) {
        toastEl.className = 'toast align-items-center border-0 text-bg-success';
        toastBody.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i>' + (data.message || 'Email inviata!');
      } else {
        toastEl.className = 'toast align-items-center border-0 text-bg-danger';
        toastBody.innerHTML = '<i class="bi bi-exclamation-circle-fill me-1"></i>' + (data.error || 'Errore invio email');
      }
      bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 10000 }).show();
    } catch(e) {
      alert('Errore: ' + (e?.message || 'sconosciuto'));
    } finally {
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-envelope"></i>';
    }
  });

  // ── Blocchi ──────────────────────────────────────────────
  const blockModal = new bootstrap.Modal(document.getElementById('blockModal'));
  const HOURS = Array.from({length: 14}, (_, i) => `${(i+8).toString().padStart(2,'0')}:00`);

  // Popola orari
  function fillHours() {
    const from = document.getElementById('blockFrom');
    const to   = document.getElementById('blockTo');
    from.innerHTML = HOURS.map(h => `<option>${h}</option>`).join('');
    to.innerHTML   = HOURS.map(h => `<option>${h}</option>`).join('');
    to.value = '10:00';
  }

  document.getElementById('openBlockBtn').addEventListener('click', () => {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('blockDate').value = today;
    fillHours();
    loadBlocksForDate(today);
    blockModal.show();
  });

  document.getElementById('blockDate').addEventListener('change', e => {
    loadBlocksForDate(e.target.value);
  });

  document.getElementById('toggleBlocksBtn').addEventListener('click', () => {
    const bl = document.getElementById('blocksList');
    bl.classList.toggle('d-none');
  });

  async function loadBlocksForDate(dateStr) {
    const resp   = await fetch('/api/admin/blocks?date=' + dateStr);
    const blocks = await resp.json();
    const section = document.getElementById('blocksSection');
    const list    = document.getElementById('blocksList');

    if (blocks.length === 0) {
      section.classList.add('d-none');
      return;
    }
    section.classList.remove('d-none');
    list.innerHTML = blocks.map(b => `
      <div class="d-flex align-items-center justify-content-between py-1 border-bottom">
        <span class="small">
          <strong>Campo ${b.court}</strong> · ${b.start_time}–${b.end_time}
          ${b.note ? `<span class="text-muted ms-1">(${b.note})</span>` : ''}
        </span>
        <button class="btn btn-sm btn-outline-danger py-0 del-block-btn" data-id="${b.id}">
          <i class="bi bi-trash"></i>
        </button>
      </div>
    `).join('');

    list.querySelectorAll('.del-block-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        await fetch(`/api/admin/blocks/${btn.dataset.id}`, { method: 'DELETE' });
        loadBlocksForDate(dateStr);
      });
    });
  }

  document.getElementById('doBlock').addEventListener('click', async () => {
    const dateStr  = document.getElementById('blockDate').value;
    const courtVal = parseInt(document.getElementById('blockCourt').value);
    const from     = document.getElementById('blockFrom').value;
    const to       = document.getElementById('blockTo').value;
    const note     = document.getElementById('blockNote').value.trim();

    if (from >= to) { alert('L\'orario di fine deve essere dopo quello di inizio.'); return; }

    const courts = courtVal === 0 ? [1,2,3,4] : [courtVal];
    for (const c of courts) {
      // Blocca ogni ora nell'intervallo
      let h = parseInt(from);
      const hEnd = parseInt(to);
      while (h < hEnd) {
        const st = `${h.toString().padStart(2,'0')}:00`;
        const et = `${(h+1).toString().padStart(2,'0')}:00`;
        await fetch('/api/admin/blocks', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ court: c, date: dateStr, start_time: st, end_time: et, note })
        });
        h++;
      }
    }
    blockModal.hide();
    loadBookings();
  });

  loadBookings();
  setInterval(loadBookings, 30000);
});
