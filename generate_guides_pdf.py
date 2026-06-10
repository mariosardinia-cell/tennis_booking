"""Genera GUIDA_UTENTE.pdf e GUIDA_ADMIN.pdf a partire dai contenuti delle guide."""

import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (HRFlowable, Image, ListFlowable, ListItem,
                                 Paragraph, SimpleDocTemplate, Spacer, Table,
                                 TableStyle)

# ── Fonts (Segoe UI – buona copertura unicode, già presente su Windows) ──────
FONT_DIR = r'C:\Windows\Fonts'
pdfmetrics.registerFont(TTFont('Segoe', f'{FONT_DIR}\\segoeui.ttf'))
pdfmetrics.registerFont(TTFont('Segoe-Bold', f'{FONT_DIR}\\segoeuib.ttf'))
pdfmetrics.registerFont(TTFont('Segoe-Italic', f'{FONT_DIR}\\segoeuii.ttf'))
pdfmetrics.registerFontFamily('Segoe', normal='Segoe', bold='Segoe-Bold', italic='Segoe-Italic')

# ── Colori brand (coerenti con style.css / bootstrap) ────────────────────────
GREEN   = colors.HexColor('#198754')
YELLOW  = colors.HexColor('#ffc107')
RED     = colors.HexColor('#dc3545')
GREY    = colors.HexColor('#adb5bd')
LIGHTBG = colors.HexColor('#f8f9fa')
NOTEBG  = colors.HexColor('#e7f5ec')
DARK    = colors.HexColor('#212529')
MUTED   = colors.HexColor('#6c757d')

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm
CONTENT_W = PAGE_W - 2 * MARGIN

# ── Pulizia testo: rimuove emoji, converte **bold** in <b> ───────────────────
EMOJI_PATTERN = re.compile(
    '['
    '\U0001F000-\U0001FFFF'   # emoji pittografiche
    '\U00002600-\U000027BF'   # simboli/dingbats (✅❌⚠️❓ ecc.)
    '\U00002100-\U0000218F'   # simboli letterlike (ℹ️ ecc.)
    '\U0000FE00-\U0000FE0F'   # variation selectors
    '\U00002B00-\U00002BFF'   # frecce/simboli vari
    ']+',
    flags=re.UNICODE
)


def clean(text):
    text = EMOJI_PATTERN.sub('', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r' {2,}', ' ', text).strip()
    return text


# ── Stili ──────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

H1 = ParagraphStyle('H1', parent=styles['Title'], fontName='Segoe-Bold',
                     fontSize=22, textColor=GREEN, spaceAfter=2, leading=26)
SUB = ParagraphStyle('Sub', parent=styles['Normal'], fontName='Segoe',
                      fontSize=11, textColor=MUTED, alignment=TA_CENTER, spaceAfter=16)
H2 = ParagraphStyle('H2', parent=styles['Heading2'], fontName='Segoe-Bold',
                     fontSize=14, textColor=GREEN, spaceBefore=14, spaceAfter=6)
H3 = ParagraphStyle('H3', parent=styles['Heading3'], fontName='Segoe-Bold',
                     fontSize=11.5, textColor=DARK, spaceBefore=10, spaceAfter=4)
BODY = ParagraphStyle('Body', parent=styles['Normal'], fontName='Segoe',
                       fontSize=10, leading=14, spaceAfter=4)
BODY_CELL = ParagraphStyle('BodyCell', parent=BODY, fontSize=9.5, leading=13, spaceAfter=0)
HEADCELL = ParagraphStyle('HeadCell', parent=BODY_CELL, fontName='Segoe-Bold', textColor=colors.white)


def H(text):
    return Paragraph(clean(text), H2)


def H_sub(text):
    return Paragraph(clean(text), H3)


def P(text):
    return Paragraph(clean(text), BODY)


def bullets(items):
    return ListFlowable(
        [ListItem(Paragraph(clean(t), BODY), spaceAfter=2) for t in items],
        bulletType='bullet', start='•', leftIndent=14, bulletFontSize=9
    )


def numbers(items):
    return ListFlowable(
        [ListItem(Paragraph(clean(t), BODY), spaceAfter=3) for t in items],
        bulletType='1', leftIndent=18
    )


def note(text, bg=NOTEBG, border=GREEN):
    t = Table([[Paragraph(clean(text), BODY)]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('BOX', (0, 0), (-1, -1), 0.75, border),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t


def hr():
    return HRFlowable(width='100%', thickness=0.75, color=colors.HexColor('#dee2e6'),
                       spaceBefore=10, spaceAfter=10)


def header(title, subtitle):
    story = []
    try:
        img = Image('static/logo.png')
        ratio = img.imageHeight / img.imageWidth
        img.drawWidth = 3 * cm
        img.drawHeight = 3 * cm * ratio
        img.hAlign = 'CENTER'
        story.append(img)
        story.append(Spacer(1, 6))
    except Exception:
        pass
    story.append(Paragraph(clean(title), H1))
    story.append(Paragraph(clean(subtitle), ParagraphStyle('SubC', parent=SUB)))
    story.append(hr())
    return story


def legend_table(rows):
    """rows: list of (color, label, description)"""
    data = [[Paragraph('', BODY_CELL), Paragraph('<b>Stato</b>', BODY_CELL), Paragraph('<b>Significato</b>', BODY_CELL)]]
    for _, label, desc in rows:
        data.append(['', Paragraph(f'<b>{label}</b>', BODY_CELL), Paragraph(clean(desc), BODY_CELL)])

    t = Table(data, colWidths=[1.0 * cm, 3.2 * cm, CONTENT_W - 4.2 * cm])
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (1, 0), (-1, -1), 8),
    ]
    for i, (color, _, _) in enumerate(rows, start=1):
        style.append(('BACKGROUND', (0, i), (0, i), color))
    t.setStyle(TableStyle(style))
    return t


def info_table(header_labels, rows, col_widths):
    """rows: list of (col1, col2)"""
    data = [[Paragraph(f'<b>{h}</b>', HEADCELL) for h in header_labels]]
    for r in rows:
        data.append([Paragraph(clean(c), BODY_CELL) for c in r])
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GREEN),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHTBG]),
    ]))
    return t


def build(filename, title, subtitle, story_body):
    doc = SimpleDocTemplate(
        filename, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        title=title
    )
    story = header(title, subtitle) + story_body
    doc.build(story)
    print(f'Creato {filename}')


# ════════════════════════════════════════════════════════════════════════════
# GUIDA UTENTE
# ════════════════════════════════════════════════════════════════════════════

utente_body = []

utente_body.append(H('Come prenotare un campo (in 4 semplici passi)'))

utente_body.append(H_sub('1. Apri il sito'))
utente_body.append(P('Vai all\'indirizzo: **https://geovillage2026.up.railway.app**'))
utente_body.append(P('Consiglio: salva questo indirizzo tra i preferiti del telefono per averlo sempre a portata di mano.'))

utente_body.append(H_sub('2. Scegli giorno e orario'))
utente_body.append(bullets([
    'In alto trovi la **data**: con le frecce ← → puoi cambiare giorno',
    'Sotto trovi la **griglia** con i 4 campi e gli orari disponibili',
]))
utente_body.append(Spacer(1, 6))
utente_body.append(P('<b>Significato dei simboli nella griglia:</b>'))
utente_body.append(Spacer(1, 4))
utente_body.append(legend_table([
    (GREEN,  'Libero',            'Puoi prenotare questo slot'),
    (YELLOW, 'In attesa',         'Richiesta inviata, in attesa di conferma del gestore'),
    (RED,    'Occupato',          'Slot già confermato, non prenotabile'),
    (GREY,   'Non disponibile',   'Campo bloccato (lezione, manutenzione, ecc.)'),
]))

utente_body.append(H_sub('3. Clicca sullo slot libero (verde) che vuoi'))
utente_body.append(P('Si apre una finestra con il riepilogo (campo, giorno, orario). Inserisci:'))
utente_body.append(bullets([
    '**Nome e Cognome**',
    '**Numero di telefono** (es. 333 1234567)',
]))
utente_body.append(P('Poi premi <b>"Invia richiesta"</b>.'))

utente_body.append(H_sub('4. Aspetta la conferma su WhatsApp'))
utente_body.append(P(
    'La tua richiesta viene inviata al gestore del circolo, che ti confermerà '
    '<b>entro breve tempo tramite messaggio WhatsApp</b>.'
))

utente_body.append(H('Cose da sapere'))
utente_body.append(bullets([
    '**Pagamento in loco** – si paga direttamente al circolo, niente carte o pagamenti online',
    '**Una prenotazione attiva per persona** – finché ne hai una in corso (in attesa o confermata) '
    'non puoi farne un\'altra. Se devi modificarla, contatta il circolo',
    'Lo slot diventa **giallo** (in attesa) appena invii la richiesta: è normale, significa che è stata ricevuta',
    'Quando il gestore conferma, ricevi un messaggio WhatsApp con i dettagli',
]))

utente_body.append(H('Problemi comuni'))
utente_body.append(P('<b>"Hai già una prenotazione attiva"</b>'))
utente_body.append(P('→ Hai già una richiesta in corso con quel numero di telefono. Contatta il circolo se vuoi cambiarla o cancellarla.'))
utente_body.append(Spacer(1, 4))
utente_body.append(P('<b>"Slot non più disponibile"</b>'))
utente_body.append(P('→ Qualcun altro ha prenotato quell\'orario un attimo prima di te. Scegli un altro slot.'))
utente_body.append(Spacer(1, 4))
utente_body.append(P('<b>Non ricevo il messaggio WhatsApp</b>'))
utente_body.append(P('→ Verifica di aver scritto il numero di telefono corretto. Se il problema persiste, contatta direttamente il circolo.'))

build('GUIDA_UTENTE.pdf',
      'Guida Prenotazione Campi',
      'Geovillage Sporting Club',
      utente_body)


# ════════════════════════════════════════════════════════════════════════════
# GUIDA ADMIN
# ════════════════════════════════════════════════════════════════════════════

admin_body = []

admin_body.append(H('Accesso al pannello'))
admin_body.append(numbers([
    'Vai su: **https://geovillage2026.up.railway.app/admin**',
    'Inserisci la **password admin** (quella impostata su Railway in ADMIN_PASSWORD)',
    'Sei dentro!',
]))
admin_body.append(note('Consiglio: salva questa pagina tra i preferiti / sulla home del telefono per accedere velocemente.'))

admin_body.append(H('1. Gestire le prenotazioni'))
admin_body.append(P('Il pannello mostra 3 schede in alto:'))
admin_body.append(Spacer(1, 4))
admin_body.append(info_table(
    ['Scheda', 'Cosa mostra'],
    [
        ('In attesa', 'Le nuove richieste da confermare/rifiutare (badge giallo con numero)'),
        ('Confermate', 'Le prenotazioni già confermate'),
        ('Tutte', 'Lo storico completo'),
    ],
    [3.5 * cm, CONTENT_W - 3.5 * cm]
))

admin_body.append(H_sub('Confermare una prenotazione'))
admin_body.append(numbers([
    'Nella scheda **"In attesa"**, trovi le card con nome, telefono, campo, data e ora',
    'Clicca **"Conferma"** (pulsante verde)',
    'Si apre un riepilogo → clicca **"Conferma e apri WhatsApp"**',
    'Si aprirà WhatsApp Web/App con un messaggio già scritto per il cliente',
    'Premi solo invio/invia su WhatsApp per mandare la conferma',
]))

admin_body.append(H_sub('Rifiutare una prenotazione'))
admin_body.append(bullets([
    'Clicca **"Rifiuta"** (pulsante rosso) sulla card → conferma il popup',
    'Lo slot torna disponibile per altri clienti',
]))

admin_body.append(H_sub('Inviare messaggio WhatsApp di conferma in seguito'))
admin_body.append(bullets([
    'Nella scheda **"Confermate"**, ogni prenotazione ha un pulsante verde '
    '**"Invia messaggio WhatsApp"** per riscrivere/reinviare la conferma in qualsiasi momento',
]))

admin_body.append(H_sub('Annullare una prenotazione confermata (es. il cliente disdice)'))
admin_body.append(bullets([
    'Nella scheda **"Confermate"**, clicca il pulsante rosso **"Annulla prenotazione"**',
    'Conferma il popup → la prenotazione viene eliminata e <b>lo slot torna libero (verde)</b> '
    'sulla griglia pubblica, pronto per essere riprenotato da altri clienti',
]))

admin_body.append(H('2. Bloccare campi (lezioni, scuola tennis, manutenzione...)'))
admin_body.append(numbers([
    'Clicca il pulsante rosso **"Blocca slot"** in alto',
    'Scegli: <b>Data</b> · <b>Campo</b> (singolo oppure "Tutti i campi") · <b>Orario da/a</b> · <b>Nota</b> (facoltativa)',
    'Clicca **"Blocca"**',
]))
admin_body.append(P('Gli slot bloccati appariranno **grigi** nella griglia pubblica e i clienti non potranno prenotarli.'))

admin_body.append(H_sub('Rimuovere un blocco'))
admin_body.append(bullets([
    'Riapri **"Blocca slot"**, seleziona la data → vedrai la lista dei blocchi attivi',
    'Clicca l\'icona del cestino per rimuoverlo',
]))

admin_body.append(H('3. Notifiche nuove prenotazioni'))
admin_body.append(P('Quando un cliente invia una richiesta, ricevi automaticamente:'))
admin_body.append(bullets([
    '**Una email** (se configurata)',
    '**Una notifica push** sul telefono/PC (se attivata)',
]))

admin_body.append(H_sub('Attivare le notifiche push'))
admin_body.append(numbers([
    'Clicca l\'icona della <b>campanella</b> in alto a destra',
    'Il browser chiederà il permesso → accetta',
    'Da quel momento riceverai una notifica push ogni volta che arriva una nuova richiesta',
]))
admin_body.append(note('Attenzione: va attivata su ogni dispositivo/browser dove vuoi ricevere le notifiche.',
                        bg=colors.HexColor('#fff8e1'), border=YELLOW))

admin_body.append(H_sub('Testare le email'))
admin_body.append(bullets([
    'Clicca l\'icona della <b>busta</b> in alto',
    'Comparirà un messaggio in basso a destra: verde = email inviata correttamente, '
    'rosso = errore (con dettaglio del problema)',
]))

admin_body.append(H('4. Aggiornamento automatico'))
admin_body.append(P(
    'La pagina admin si <b>aggiorna da sola ogni 30 secondi</b>, quindi puoi tenerla aperta '
    'e vedrai apparire le nuove richieste senza dover ricaricare.'
))

admin_body.append(H('5. Logout'))
admin_body.append(P('Icona in alto a destra (porta/uscita) per uscire dal pannello admin.'))

admin_body.append(H('Riepilogo flusso giornaliero'))
admin_body.append(numbers([
    'Cliente prenota dal sito → arriva email + notifica push',
    'Apri /admin → scheda "In attesa"',
    'Clicca <b>Conferma</b> → si apre WhatsApp → invia il messaggio',
    'Il cliente si presenta al campo e <b>paga in loco</b>',
    'Se serve bloccare un campo per lezioni → usa <b>"Blocca slot"</b>',
]))

build('GUIDA_ADMIN.pdf',
      'Guida Gestione App',
      'Pannello Admin – Geovillage Sporting Club',
      admin_body)
