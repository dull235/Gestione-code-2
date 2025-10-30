import streamlit as st
import sqlite3
from datetime import datetime
import threading
import time

# --- Connessione DB ---
conn = sqlite3.connect("tickets.db", check_same_thread=False)
c = conn.cursor()

st.title("🚚 App Autista - Ticket Carico/Scarico")

# --- SESSION STATE ---
if 'ticket_inviato' not in st.session_state:
    st.session_state['ticket_inviato'] = False
if 'notifiche' not in st.session_state:
    st.session_state['notifiche'] = []
if 'thread_refresh' not in st.session_state:
    st.session_state['thread_refresh'] = False

# --- FUNZIONI ---
def fetch_notifiche():
    c.execute("SELECT ID, Stato, Data_creazione FROM tickets WHERE Attivo=1 ORDER BY Data_creazione DESC")
    tickets = c.fetchall()
    notifiche = []
    for t in tickets:
        stato = t[1]
        if stato in ["Chiamato", "Sollecito", "Annullato", "Non Presentato", "Terminato"]:
            msg = f"{t[2]} - {stato} sul ticket {t[0]}"
            notifiche.append(msg)
    st.session_state['notifiche'] = notifiche

def play_notification(msg):
    # Suono e popup
    html = f"""
    <audio autoplay>
      <source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg">
    </audio>
    <script>alert("{msg}");</script>
    """
    st.components.v1.html(html, height=0)

def auto_refresh_notifiche():
    while True:
        time.sleep(5)
        fetch_notifiche()

# --- AVVIA THREAD AUTO-REFRESH ---
if not st.session_state['thread_refresh']:
    thread = threading.Thread(target=auto_refresh_notifiche, daemon=True)
    thread.start()
    st.session_state['thread_refresh'] = True

# --- LOGICA FORM ---
if not st.session_state['ticket_inviato']:
    st.subheader("📋 Compila il Ticket")
    nome = st.text_input("Nome e Cognome")
    azienda = st.text_input("Azienda")
    targa_motrice = st.text_input("Targa Motrice")
    rimorchio_flag = st.radio("Hai un rimorchio?", ["No", "Si"])
    targa_rimorchio = st.text_input("Targa Rimorchio") if rimorchio_flag == "Si" else ""

    tipo_mod = st.radio("Tipo operazione", ["Carico", "Scarico"])
    destinazione = st.text_input("Destinazione") if tipo_mod == "Carico" else ""
    produttore = st.text_input("Produttore") if tipo_mod == "Scarico" else ""

    if st.button("📨 Invia Richiesta"):
        # Controlla campi obbligatori
        if not nome or not azienda or not targa_motrice:
            st.warning("Compila tutti i campi obbligatori!")
        else:
            c.execute("""
                INSERT INTO tickets (Nome, Azienda, Targa, Rimorchio, Tipo, Destinazione, Produttore, Stato, Attivo, Data_creazione)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (
                nome, azienda, targa_motrice,
                1 if rimorchio_flag=="Si" else 0,
                tipo_mod, destinazione, produttore,
                "Nuovo",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
            st.success("✅ Richiesta inviata all'ufficio!")
            st.session_state['ticket_inviato'] = True

# --- PAGINA NOTIFICHE ---
if st.session_state['ticket_inviato']:
    st.subheader("🔔 Notifiche in tempo reale")
    fetch_notifiche()
    for n in st.session_state['notifiche']:
        st.info(n)
        play_notification(n)

    if st.button("🔄 Aggiorna ora"):
        fetch_notifiche()

    st.info("Le notifiche vengono aggiornate automaticamente ogni 5 secondi.")
