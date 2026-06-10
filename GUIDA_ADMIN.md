# 🎾 Guida Gestione App – Pannello Admin (Geovillage Sporting Club)

## Accesso al pannello

1. Vai su: **https://geovillage2026.up.railway.app/admin**
2. Inserisci la **password admin** (quella impostata su Railway in `ADMIN_PASSWORD`)
3. Sei dentro 🎉

> 💡 Consiglio: salva questa pagina tra i preferiti / sulla home del telefono per accedere velocemente.

---

## 1. Gestire le prenotazioni

Il pannello mostra 3 schede in alto:

| Scheda | Cosa mostra |
|--------|-------------|
| **In attesa** | Le nuove richieste da confermare/rifiutare (badge giallo con numero) |
| **Confermate** | Le prenotazioni già confermate |
| **Tutte** | Lo storico completo |

### ✅ Confermare una prenotazione
1. Nella scheda **"In attesa"**, trovi le card con nome, telefono, campo, data e ora
2. Clicca **"Conferma"** (pulsante verde)
3. Si apre un riepilogo → clicca **"Conferma e apri WhatsApp"**
4. Si aprirà **WhatsApp Web/App** con un messaggio già scritto per il cliente
5. Premi solo **invio/invia** su WhatsApp per mandare la conferma

### ❌ Rifiutare una prenotazione
- Clicca **"Rifiuta"** (pulsante rosso) sulla card → conferma il popup
- Lo slot torna disponibile per altri clienti

### 📲 Inviare messaggio WhatsApp di conferma in seguito
- Nella scheda **"Confermate"**, ogni prenotazione ha un pulsante verde
  **"Invia messaggio WhatsApp"** per riscrivere/reinviare la conferma in qualsiasi momento

### 🔓 Annullare una prenotazione confermata (es. il cliente disdice)
- Nella scheda **"Confermate"**, clicca il pulsante rosso **"Annulla prenotazione"**
- Conferma il popup → la prenotazione viene eliminata e **lo slot torna libero (verde)**
  sulla griglia pubblica, pronto per essere riprenotato da altri clienti

---

## 2. Bloccare campi (lezioni, scuola tennis, manutenzione...)

1. Clicca il pulsante rosso **"Blocca slot"** in alto
2. Scegli:
   - **Data**
   - **Campo** (singolo oppure "Tutti i campi")
   - **Orario da / a**
   - **Nota** (facoltativa, es. "Lezione privata")
3. Clicca **"Blocca"**

Gli slot bloccati appariranno **grigi** ⚪ nella griglia pubblica e i clienti non potranno prenotarli.

### Rimuovere un blocco
- Riapri **"Blocca slot"**, seleziona la data → vedrai la lista dei blocchi attivi
- Clicca l'icona del **cestino** 🗑️ per rimuoverlo

---

## 3. Notifiche nuove prenotazioni

Quando un cliente invia una richiesta, ricevi automaticamente:

- 📧 **Una email** (se configurata)
- 🔔 **Una notifica push** sul telefono/PC (se attivata)

### Attivare le notifiche push
1. Clicca l'icona della **campanella** 🔔 in alto a destra
2. Il browser chiederà il permesso → accetta
3. Da quel momento riceverai una notifica push ogni volta che arriva una nuova richiesta

> ⚠️ Va attivata su **ogni dispositivo/browser** dove vuoi ricevere le notifiche.

### Testare le email
- Clicca l'icona della **busta** 📧 in alto
- Comparirà un messaggio (in basso a destra):
  - 🟢 Verde = email inviata correttamente
  - 🔴 Rosso = errore (con dettaglio del problema)

---

## 4. Aggiornamento automatico

La pagina admin si **aggiorna da sola ogni 30 secondi**, quindi puoi tenerla
aperta e vedrai apparire le nuove richieste senza dover ricaricare.

---

## 5. Logout

- Icona in alto a destra (porta/uscita) per uscire dal pannello admin

---

## 📋 Riepilogo flusso giornaliero

1. Cliente prenota dal sito → arriva email + notifica push
2. Apri `/admin` → scheda "In attesa"
3. Clicca **Conferma** → si apre WhatsApp → invia il messaggio
4. Il cliente si presenta al campo e **paga in loco**
5. Se serve bloccare un campo per lezioni → usa **"Blocca slot"**
