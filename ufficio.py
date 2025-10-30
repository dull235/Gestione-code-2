import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from database import get_ticket_attivi, get_ticket_storico, aggiorna_stato

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Ufficio Carico/Scarico", layout="wide")

# --- LOGIN SEMPLICE ---
# puoi modificare qui gli utenti ammessi
USERS = {
    "admin": "admin",
    "ufficio": "pesa2025"
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Login Ufficio")
    user = st.text_input("👤 Utente")
    pwd = st.text_input("🔑 Password", type="password")

    if st.button("Accedi"):
        if user in USERS and USERS[user] == pwd:
            st.session_state.logged_in = True
            st.success(f"Benvenuto, {user}!")
            st.rerun()
        else:
            st.error("Credenziali errate. Riprova.")
    st.stop()

# --- CONTENUTO DELL’UFFICIO (solo dopo login) ---
st.sidebar.title("📋 Menu")
view = st.sidebar.radio("Seleziona vista:", ["Ticket Aperti", "Storico Ticket"])
if st.sidebar.button("🔒 Esci"):
    st.session_state.logged_in = False
    st.rerun()

st.title("🏢 Gestione Ticket Ufficio")

notifiche_testi = {
    "Chiamata": "È il tuo turno. Sei pregato di recarti in pesa con il tuo automezzo.",
    "Sollecito": "Sollecito: È il tuo turno. Sei pregato di recarti in pesa con il tuo automezzo.",
    "Annulla": "Attività di Carico/Scarico Annullata. Per favore recati all'ufficio pesa per ulteriori informazioni.",
    "Non Presentato": "Attività di Carico/Scarico Annullata a causa della tua assenza.",
    "Termina Servizio": "Grazie mille per la sua visita."
}

# --- VISTA TICKET APERTI ---
if view == "Ticket Aperti":
    tickets = get_ticket_attivi()
    if tickets:
        df = pd.DataFrame(tickets, columns=[
            "ID", "Nome", "Azienda", "Targa", "Rimorchio", "Tipo", "Destinazione",
            "Produttore", "Stato", "Attivo", "Data_creazione", "Data_chiamata",
            "Data_chiusura", "Durata_servizio", "Ultima_notifica", "Lat", "Lon"
        ])
        st.dataframe(df, use_container_width=True)

        selected_id = st.selectbox("Seleziona ticket:", df["ID"])

        col1, col2, col3, col4, col5 = st.columns(5)
        if col1.button("CHIAMATA"):
            aggiorna_stato(selected_id, "Chiamato", notifiche_testi["È il tuo turno. Sei pregato di recarti in pesa con il tuo automezzo."])
            st.success("Notifica CHIAMATA inviata.")
        if col2.button("SOLLECITO"):
            aggiorna_stato(selected_id, "Sollecito", notifiche_testi["Sollecito, È il tuo turno. Sei pregato di recarti in pesa con il tuo automezzo."])
            st.success("Notifica SOLLECITO inviata.")
        if col3.button("ANNULLA"):
            aggiorna_stato(selected_id, "Annullato", notifiche_testi["Annulla, Attività di Carico/Scarico Annullata. Per favore recati all'ufficio pesa per ulteriori informazioni."])
            st.warning("Ticket annullato.")
        if col4.button("NON PRESENTATO"):
            aggiorna_stato(selected_id, "Non Presentato", notifiche_testi["Non Presentato, Attività di Carico/Scarico Annullata a causa della tua assenza."])
            st.error("Segnalato come non presentato.")
        if col5.button("TERMINA SERVIZIO"):
            aggiorna_stato(selected_id, "Terminato", notifiche_testi["Termina Servizio, Grazie mille per la sua visita"])
            st.success("Ticket terminato.")

        # --- Mappa in tempo reale ---
        st.subheader("📍 Posizione Ticket Attivi")
        avg_lat = df["Lat"].mean() if not df["Lat"].isna().all() else 45.0
        avg_lon = df["Lon"].mean() if not df["Lon"].isna().all() else 9.0
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=6)
        for _, r in df.iterrows():
            if r["Lat"] and r["Lon"]:
                folium.Marker(
                    [r["Lat"], r["Lon"]],
                    popup=f"{r['Nome']} - {r['Tipo']}",
                    tooltip=r["Stato"]
                ).add_to(m)
        st_folium(m, height=500, width='100%')
    else:
        st.info("Nessun ticket aperto al momento.")

# --- VISTA STORICO ---
else:
    st.subheader("📜 Storico Ticket")
    storico = get_ticket_storico()
    if storico:
        df_s = pd.DataFrame(storico, columns=[
            "ID", "Nome", "Azienda", "Targa", "Rimorchio", "Tipo", "Destinazione",
            "Produttore", "Stato", "Attivo", "Data_creazione", "Data_chiamata",
            "Data_chiusura", "Durata_servizio", "Ultima_notifica", "Lat", "Lon"
        ])
        st.dataframe(df_s, use_container_width=True)
        csv = df_s.to_csv(index=False).encode("utf-8")
        st.download_button("📤 Esporta Storico CSV", csv, "storico_tickets.csv", "text/csv")
    else:
        st.info("Nessun ticket chiuso presente nello storico.")
