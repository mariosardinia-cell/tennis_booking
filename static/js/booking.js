/* ── booking.js – public court grid & booking modal ── */

const COURTS = [1, 2, 3, 4];
const MONTHS = ['gennaio','febbraio','marzo','aprile','maggio','giugno',
                 'luglio','agosto','settembre','ottobre','novembre','dicembre'];
const DAYS   = ['Domenica','Lunedì','Martedì','Mercoledì','Giovedì','Venerdì','Sabato'];

let currentDate = new Date();
currentDate.setHours(0, 0, 0, 0);
let selectedSlot = null;
let bookingModal  = null;

function toISO(d) {
  const y  = d.getFullYear();
  const m  = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${dd}`;
}

function labelDate(d) {
  const today    = new Date(); today.setHours(0,0,0,0);
  const tomorrow = new Date(today); tomorrow.setDate(today.getDate() + 1);
  if (d.getTime() === today.getTime())    return 'Oggi';
  if (d.getTime() === tomorrow.getTime()) return 'Domani';
  return DAYS[d.getDay()];
}

function subDate(d) {
  return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
}

async function loadSlots() {
  document.getElementById('dateDisplay').textContent    = labelDate(currentDate);
  document.getElementById('dateSubDisplay').textContent = subDate(currentDate);

  const resp  = await fetch('/api/slots?date=' + toISO(currentDate));
  const slots = await resp.json();

  // group by time → { '08:00': { 1: 'available', 2: 'confirmed', … }, … }
  const byTime = {};
  slots.forEach(s => {
    if (!byTime[s.time]) byTime[s.time] = {};
    byTime[s.time][s.court] = s.status;
  });

  const tbody  = document.getElementById('gridBody');
  const now    = new Date();
  const isToday = toISO(currentDate) === toISO(now);

  tbody.innerHTML = '';

  Object.entries(byTime).forEach(([time, courts]) => {
    const hour   = parseInt(time);
    const isPast = isToday && hour <= now.getHours();

    const tr = document.createElement('tr');
    if (isPast) tr.classList.add('past-row');

    const timeTd = document.createElement('td');
    timeTd.className = 'time-col text-center';
    timeTd.textContent = time;
    tr.appendChild(timeTd);

    COURTS.forEach(c => {
      const status = courts[c] || 'available';
      const td = document.createElement('td');
      td.className = `slot-cell ${status}`;

      if (status === 'available' && !isPast) {
        td.innerHTML = '<i class="bi bi-circle text-success fs-5"></i>';
        td.addEventListener('click', () => openBooking(c, time));
      } else if (status === 'pending') {
        td.innerHTML = '<i class="bi bi-clock-fill text-warning fs-5"></i>';
        td.title = 'In attesa di conferma';
      } else if (status === 'confirmed') {
        td.innerHTML = '<i class="bi bi-x-circle-fill text-danger fs-5"></i>';
        td.title = 'Occupato';
      } else if (status === 'blocked') {
        td.innerHTML = '<i class="bi bi-slash-circle text-secondary fs-5"></i>';
        td.title = 'Non disponibile';
      } else {
        td.innerHTML = '<span class="text-muted">–</span>';
      }
      tr.appendChild(td);
    });

    tbody.appendChild(tr);
  });
}

function openBooking(court, time) {
  selectedSlot = { court, start_time: time, date: toISO(currentDate) };
  document.getElementById('bookingInfo').textContent =
    `Campo ${court}  ·  ${labelDate(currentDate)} ${subDate(currentDate)}  ·  ore ${time}`;
  document.getElementById('bookingForm').classList.remove('d-none');
  document.getElementById('bookingResult').classList.add('d-none');
  document.getElementById('modalFooter').classList.remove('d-none');
  document.getElementById('bookName').value  = '';
  document.getElementById('bookPhone').value = '';
  bookingModal.show();
  setTimeout(() => document.getElementById('bookName').focus(), 400);
}

async function submitBooking() {
  const name  = document.getElementById('bookName').value.trim();
  const phone = document.getElementById('bookPhone').value.trim();

  if (!name || !phone) {
    document.getElementById('bookName').classList.toggle('is-invalid', !name);
    document.getElementById('bookPhone').classList.toggle('is-invalid', !phone);
    return;
  }

  const btn = document.getElementById('submitBook');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Invio…';

  try {
    const resp = await fetch('/api/book', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...selectedSlot, name, phone })
    });
    const data = await resp.json();
    const resultDiv = document.getElementById('bookingResult');
    resultDiv.classList.remove('d-none');

    if (resp.ok && data.ok) {
      document.getElementById('bookingForm').classList.add('d-none');
      document.getElementById('modalFooter').classList.add('d-none');
      resultDiv.innerHTML = `
        <div class="alert alert-success">
          <i class="bi bi-check-circle-fill me-1"></i>
          <strong>Prenotazione confermata!</strong><br>${data.message}
        </div>`;
      loadSlots();
    } else {
      resultDiv.innerHTML = `
        <div class="alert alert-danger py-2">
          <i class="bi bi-exclamation-circle-fill me-1"></i>${data.error || 'Errore, riprova.'}
        </div>`;
    }
  } catch {
    alert('Errore di rete, riprova.');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-send-fill me-1"></i>Invia richiesta';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  bookingModal = new bootstrap.Modal(document.getElementById('bookingModal'));

  document.getElementById('prevDay').addEventListener('click', () => {
    currentDate.setDate(currentDate.getDate() - 1);
    loadSlots();
  });
  document.getElementById('nextDay').addEventListener('click', () => {
    currentDate.setDate(currentDate.getDate() + 1);
    loadSlots();
  });
  document.getElementById('submitBook').addEventListener('click', submitBooking);

  // Clear validation on input
  ['bookName','bookPhone'].forEach(id => {
    document.getElementById(id).addEventListener('input', e => e.target.classList.remove('is-invalid'));
  });

  loadSlots();
});
