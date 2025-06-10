import pandas as pd
import streamlit as st
import sqlite3
from datetime import datetime

# Configurazione iniziale di Streamlit
st.set_page_config(page_title="Toto Cinture Accademia", page_icon="🥋")

# Inizializzazione del database
def init_db():
    conn = sqlite3.connect('predictions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS predictions
                 (username TEXT,
                  student_name TEXT,
                  prediction TEXT,
                  timestamp DATETIME,
                  PRIMARY KEY (username, student_name))''')
    conn.commit()
    conn.close()

# Inizializza il database
init_db()

# Inizializza lo stato della sessione
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# Carica i dati degli studenti
data_path = "data.xlsx"
df = pd.read_excel(data_path)
df = df.loc[df["Attivo"]=="SI"].drop(columns=["Attivo"])

# Sidebar per login
st.sidebar.title("Login")
selected_username = st.sidebar.selectbox("Seleziona il tuo nome", ["Seleziona...", "Carlo", "Nini (amica di GU)", "Jack", "Mariadna", "Frengo"])

if st.sidebar.button("Accedi"):
    if selected_username != "Seleziona...":
        st.session_state.logged_in = True
        st.session_state.current_user = selected_username
        conn = sqlite3.connect('predictions.db')
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (selected_username,))
        conn.commit()
        conn.close()
        st.sidebar.success(f"Benvenuto, {selected_username}!")
    else:
        st.sidebar.error("Per favore, seleziona un nome prima di accedere")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.rerun()

# Main content
st.title("🥋 Toto Cinture Accademia")

if st.session_state.logged_in and st.session_state.current_user:
    # Carica predizioni esistenti
    conn = sqlite3.connect('predictions.db')
    existing_predictions = pd.read_sql_query(
        "SELECT student_name, prediction FROM predictions WHERE username = ?",
        conn,
        params=(st.session_state.current_user,)
    )
    conn.close()

    # Opzioni per le predizioni
    prediction_options = ["Nulla", "Tacchetta", "Cintura"]
    
    st.write("# Fai le tue predizioni:")#
    
    # Itera sugli studenti nel dataframe originale
    for idx, row in df.iterrows():
        student_surname = row.iloc[0]
        student_name = row.iloc[1]
        student_full_name = f"{student_surname} {student_name}"
        
        # Trova la predizione esistente per questo studente
        existing_prediction = existing_predictions[
            existing_predictions['student_name'] == student_full_name
        ]['prediction'].iloc[0] if not existing_predictions[
            existing_predictions['student_name'] == student_full_name
        ].empty else "Nulla"
        
        col1, col2 = st.columns([3, 2])
        with col1:
            st.write(student_full_name)
        with col2:
            prediction = st.selectbox(
                f"Predizione per {student_full_name}",
                options=prediction_options,
                key=f"pred_{idx}",
                index=prediction_options.index(existing_prediction) if existing_prediction in prediction_options else 0
            )
            
            # Salva la predizione nel database quando viene modificata
            if prediction != existing_prediction:
                conn = sqlite3.connect('predictions.db')
                c = conn.cursor()
                c.execute("""
                    INSERT OR REPLACE INTO predictions (username, student_name, prediction, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (st.session_state.current_user, student_full_name, prediction, datetime.now()))
                conn.commit()
                conn.close()
    
    # Mostra tutte le predizioni
    if st.button("Mostra tutte le predizioni"):
        conn = sqlite3.connect('predictions.db')
        all_predictions = pd.read_sql_query("""
            SELECT username, student_name, prediction, timestamp
            FROM predictions
            ORDER BY student_name, username
        """, conn)
        conn.close()
        
        st.write("Predizioni di tutti gli utenti:")
        st.dataframe(all_predictions)
else:
    st.warning("Per favore, seleziona il tuo nome e clicca 'Accedi' per fare le tue predizioni.")
