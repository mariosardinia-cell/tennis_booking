import os
import json
import sqlite3
import smtplib
import threading
from datetime import date, datetime
from email.mime.text import MIMEText
from functools import wraps
from urllib.parse import quote

from flask import (Flask, abort, jsonify, redirect, render_template,
                   request, session, url_for)
from dotenv import load_dotenv

try:
    from pywebpush import webpush, WebPushException
    PUSH_ENABLED = True
except ImportError:
    PUSH_ENABLED = False

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'cambia-questa-chiave-segreta')

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'tennis2026')
COURTS = [1, 2, 3, 4]
OPEN_HOUR  = int(os.environ.get('OPEN_HOUR',  8))
CLOSE_HOUR = int(os.environ.get('CLOSE_HOUR', 22))
DB_PATH    = os.environ.get('DB_PATH', 'bookings.db')

CONFIRM_MSG = os.environ.get(
    'CONFIRM_MSG',
    'Ciao {name}! La tua prenotazione per Campo {court} il {date} alle {time} è confermata ✅ A presto! 🎾'
)

_MONTHS_IT = ['', 'gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno',
               'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']


# ─── Database ────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True) if os.path.dirname(DB_PATH) else None
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                phone      TEXT NOT NULL,
                court      INTEGER NOT NULL,
                date       TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time   TEXT NOT NULL,
                status     TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                notes      TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS push_subscriptions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                subscription TEXT NOT NULL UNIQUE,
                created_at   TEXT DEFAULT (datetime('now', 'localtime'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS blocks (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                court      INTEGER NOT NULL,
                date       TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time   TEXT NOT NULL,
                note       TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        ''')
        conn.commit()


init_db()


# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_time_slots():
    return [f'{h:02d}:00' for h in range(OPEN_HOUR, CLOSE_HOUR)]


def format_date_it(date_str):
    try:
        d = datetime.strptime(date_str, '%Y-%m-%d')
        return f"{d.day} {_MONTHS_IT[d.month]} {d.year}"
    except Exception:
        return date_str


def clean_phone(phone):
    """Normalize Italian phone to international format for wa.me links."""
    p = ''.join(c for c in phone if c.isdigit() or c == '+')
    if p.startswith('0039'):
        p = '+39' + p[4:]
    elif p.startswith('39') and not p.startswith('+'):
        p = '+' + p
    elif not p.startswith('+') and p.startswith('3') and len(p) >= 9:
        p = '+39' + p
    return p


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            if request.is_json:
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


# ─── Public routes ────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/slots')
def api_slots():
    date_str = request.args.get('date', date.today().isoformat())
    with get_db() as conn:
        rows = conn.execute(
            "SELECT court, start_time, status FROM bookings WHERE date=? AND status!='rejected'",
            (date_str,)
        ).fetchall()
        block_rows = conn.execute(
            "SELECT court, start_time FROM blocks WHERE date=?", (date_str,)
        ).fetchall()
    booked = {f"{r['court']}-{r['start_time']}": r['status'] for r in rows}
    for b in block_rows:
        booked[f"{b['court']}-{b['start_time']}"] = 'blocked'
    result = [
        {'court': c, 'time': t, 'status': booked.get(f'{c}-{t}', 'available')}
        for t in get_time_slots() for c in COURTS
    ]
    return jsonify(result)


@app.route('/api/book', methods=['POST'])
def api_book():
    data = request.get_json() or {}
    name       = data.get('name', '').strip()
    phone      = data.get('phone', '').strip()
    court      = data.get('court')
    date_str   = data.get('date', '')
    start_time = data.get('start_time', '')

    if not all([name, phone, court, date_str, start_time]):
        return jsonify({'error': 'Compila tutti i campi'}), 400

    try:
        court = int(court)
        if court not in COURTS:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'Campo non valido'}), 400

    h        = int(start_time.split(':')[0])
    end_time = f'{h + 1:02d}:00'

    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM bookings WHERE court=? AND date=? AND start_time=? AND status!='rejected'",
            (court, date_str, start_time)
        ).fetchone()
        if existing:
            return jsonify({'error': 'Slot non più disponibile, riprova con un altro orario.'}), 409

        already_booked = conn.execute(
            "SELECT id FROM bookings WHERE phone=? AND status IN ('pending','confirmed')",
            (phone,)
        ).fetchone()
        if already_booked:
            return jsonify({'error': 'Hai già una prenotazione attiva. Contattaci per modificarla.'}), 409

        conn.execute(
            'INSERT INTO bookings (name,phone,court,date,start_time,end_time) VALUES (?,?,?,?,?,?)',
            (name, phone, court, date_str, start_time, end_time)
        )
        conn.commit()

    # Notifiche in background — non bloccano la risposta
    threading.Thread(
        target=_notify_admin,
        args=(name, phone, court, date_str, start_time),
        daemon=True
    ).start()
    return jsonify({'ok': True, 'message': 'Richiesta inviata! Ti confermeremo a breve via WhatsApp.'})


# ─── Admin routes ─────────────────────────────────────────────────────────────

@app.route('/admin')
@admin_required
def admin():
    return render_template('admin.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin'))
        error = 'Password errata'
    return render_template('admin_login.html', error=error)


@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))


@app.route('/api/admin/bookings')
@admin_required
def api_admin_bookings():
    status = request.args.get('status', 'pending')
    with get_db() as conn:
        if status == 'all':
            rows = conn.execute(
                'SELECT * FROM bookings ORDER BY date DESC, start_time DESC'
            ).fetchall()
        else:
            rows = conn.execute(
                'SELECT * FROM bookings WHERE status=? ORDER BY date ASC, start_time ASC',
                (status,)
            ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/admin/bookings/<int:bid>/confirm', methods=['POST'])
@admin_required
def api_confirm(bid):
    with get_db() as conn:
        conn.execute("UPDATE bookings SET status='confirmed' WHERE id=?", (bid,))
        conn.commit()
        row = conn.execute('SELECT * FROM bookings WHERE id=?', (bid,)).fetchone()
    if not row:
        abort(404)
    b = dict(row)
    msg    = CONFIRM_MSG.format(name=b['name'], court=b['court'],
                                date=format_date_it(b['date']), time=b['start_time'])
    wa_url = f"https://wa.me/{clean_phone(b['phone'])}?text={quote(msg, safe='')}"
    return jsonify({'ok': True, 'wa_url': wa_url, 'booking': b})


@app.route('/api/admin/bookings/<int:bid>/reject', methods=['POST'])
@admin_required
def api_reject(bid):
    with get_db() as conn:
        conn.execute("UPDATE bookings SET status='rejected' WHERE id=?", (bid,))
        conn.commit()
    return jsonify({'ok': True})


@app.route('/api/admin/test-email')
@admin_required
def api_test_email():
    try:
        _send_email('Test', '3331234567', 1, date.today().isoformat(), '10:00')
        return jsonify({'ok': True, 'message': 'Email inviata! Controlla la casella.'})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# ─── Blocchi admin ────────────────────────────────────────────────────────────

@app.route('/api/admin/blocks', methods=['GET'])
@admin_required
def api_get_blocks():
    date_str = request.args.get('date', date.today().isoformat())
    with get_db() as conn:
        rows = conn.execute(
            'SELECT * FROM blocks WHERE date=? ORDER BY court, start_time', (date_str,)
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/admin/blocks', methods=['POST'])
@admin_required
def api_create_block():
    data       = request.get_json() or {}
    court      = data.get('court')
    date_str   = data.get('date', '')
    start_time = data.get('start_time', '')
    end_time   = data.get('end_time', '')
    note       = data.get('note', '')

    if not all([court, date_str, start_time, end_time]):
        return jsonify({'error': 'Dati mancanti'}), 400

    with get_db() as conn:
        conn.execute(
            'INSERT INTO blocks (court, date, start_time, end_time, note) VALUES (?,?,?,?,?)',
            (court, date_str, start_time, end_time, note)
        )
        conn.commit()
    return jsonify({'ok': True})


@app.route('/api/admin/blocks/<int:bid>', methods=['DELETE'])
@admin_required
def api_delete_block(bid):
    with get_db() as conn:
        conn.execute('DELETE FROM blocks WHERE id=?', (bid,))
        conn.commit()
    return jsonify({'ok': True})


@app.route('/api/admin/bookings/<int:bid>', methods=['DELETE'])
@admin_required
def api_delete_booking(bid):
    with get_db() as conn:
        conn.execute('DELETE FROM bookings WHERE id=?', (bid,))
        conn.commit()
    return jsonify({'ok': True})


# ─── Push notifications ───────────────────────────────────────────────────────

@app.route('/api/push/key')
def api_push_key():
    return jsonify({'key': os.environ.get('VAPID_PUBLIC_KEY', '')})


@app.route('/api/push/subscribe', methods=['POST'])
@admin_required
def api_push_subscribe():
    sub = request.get_json()
    with get_db() as conn:
        conn.execute(
            'INSERT OR IGNORE INTO push_subscriptions (subscription) VALUES (?)',
            (json.dumps(sub),)
        )
        conn.commit()
    return jsonify({'ok': True})


# ─── Notification helpers ─────────────────────────────────────────────────────

def _notify_admin(name, phone, court, date_str, start_time):
    try:
        _send_push(name, court, date_str, start_time)
    except Exception as e:
        app.logger.warning(f'Push failed: {e}')
    try:
        _send_email(name, phone, court, date_str, start_time)
    except Exception as e:
        app.logger.warning(f'Email failed: {e}')


def _send_push(name, court, date_str, start_time):
    if not PUSH_ENABLED:
        return
    priv  = os.environ.get('VAPID_PRIVATE_KEY')
    email = os.environ.get('VAPID_EMAIL', 'mailto:admin@example.com')
    if not priv:
        return

    payload = json.dumps({
        'title': '🎾 Nuova prenotazione!',
        'body':  f'{name} · Campo {court} · {format_date_it(date_str)} ore {start_time}'
    })

    with get_db() as conn:
        subs = conn.execute('SELECT subscription FROM push_subscriptions').fetchall()

    dead = []
    for s in subs:
        try:
            webpush(
                subscription_info=json.loads(s['subscription']),
                data=payload,
                vapid_private_key=priv,
                vapid_claims={'sub': email}
            )
        except WebPushException as e:
            if e.response and e.response.status_code in (404, 410):
                dead.append(s['subscription'])
            app.logger.warning(f'Push error: {e}')

    if dead:
        with get_db() as conn:
            for d in dead:
                conn.execute('DELETE FROM push_subscriptions WHERE subscription=?', (d,))
            conn.commit()


def _send_email(name, phone, court, date_str, start_time):
    host  = os.environ.get('SMTP_HOST')
    port  = int(os.environ.get('SMTP_PORT', 587))
    user  = os.environ.get('SMTP_USER')
    pwd   = os.environ.get('SMTP_PASS')
    to_raw = os.environ.get('ADMIN_EMAIL', '')
    if not all([host, user, pwd, to_raw]):
        return

    # Supporta più email separate da virgola: "a@gmail.com,b@gmail.com"
    recipients = [e.strip() for e in to_raw.split(',') if e.strip()]
    if not recipients:
        return

    body = (
        f'Nuova richiesta di prenotazione:\n\n'
        f'Nome:     {name}\n'
        f'Telefono: {phone}\n'
        f'Campo:    {court}\n'
        f'Data:     {format_date_it(date_str)}\n'
        f'Ora:      {start_time}\n\n'
        f'Apri il pannello admin per confermare:\n'
        f'{os.environ.get("APP_URL", "http://localhost:5000")}/admin'
    )
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = f'🎾 Prenotazione {name} – Campo {court} ore {start_time}'
    msg['From']    = user
    msg['To']      = ', '.join(recipients)

    with smtplib.SMTP(host, port) as srv:
        srv.starttls()
        srv.login(user, pwd)
        srv.sendmail(user, recipients, msg.as_string())


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
