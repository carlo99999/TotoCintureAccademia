import pandas as pd
import streamlit as st
from supabase import create_client
from datetime import datetime
import os
from dotenv import load_dotenv
import asyncio
from typing import Dict

# Carica le variabili d'ambiente
load_dotenv()

# Configurazione iniziale di Streamlit
st.set_page_config(
    page_title="Toto Cinture Accademia",
    page_icon="🥋",
    initial_sidebar_state="expanded"
)

# Inizializza il client Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SERVICE_ROLE_KEY")
)

# Funzione asincrona per salvare le predizioni
async def save_prediction(prediction_data: Dict) -> None:
    """Salva una predizione in Supabase in modo asincrono"""
    supabase.table('IscrittiAccademia').upsert(prediction_data).execute()

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
selected_username = st.sidebar.selectbox("Seleziona il tuo nome", ["Seleziona...", "Carlo", "Nini (amica di GU)", "Jack", "Mariadna", "Frengo","Matteozzo"])

if st.sidebar.button("Accedi"):
    if selected_username != "Seleziona...":
        st.session_state.logged_in = True
        st.session_state.current_user = selected_username
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
    # Carica predizioni esistenti da Supabase
    existing_predictions = supabase.table('IscrittiAccademia').select(
        'student_name, prediction'
    ).eq('username', st.session_state.current_user).execute()
    
    # Converti il risultato in DataFrame
    existing_predictions_df = pd.DataFrame(existing_predictions.data)

    # Opzioni per le predizioni
    prediction_options = ["Nulla", "Tacchetta", "Cintura"]
    
    st.write("# Fai le tue predizioni:")
    
    # Itera sugli studenti nel dataframe originale
    for idx, row in df.iterrows():
        student_surname = row.iloc[0]
        student_name = row.iloc[1]
        student_full_name = f"{student_surname} {student_name}"
        
        # Trova la predizione esistente per questo studente
        existing_prediction = "Nulla"
        if not existing_predictions_df.empty and 'student_name' in existing_predictions_df.columns:
            mask = existing_predictions_df['student_name'] == student_full_name
            if not existing_predictions_df[mask].empty:
                existing_prediction = existing_predictions_df[mask]['prediction'].iloc[0]
        
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
            
            # Salva la predizione in Supabase quando viene modificata
            if prediction != existing_prediction:
                prediction_data = {
                    'username': st.session_state.current_user,
                    'student_name': student_full_name,
                    'prediction': prediction,
                    'timestamp': datetime.now().isoformat()
                }
                asyncio.run(save_prediction(prediction_data))
    
    # Mostra tutte le predizioni
    if st.button("Mostra tutte le predizioni"):
        all_predictions = supabase.table('IscrittiAccademia').select(
            'username, student_name, prediction, timestamp'
        ).order('student_name,username').execute()
        
        st.write("Predizioni di tutti gli utenti:")
        st.dataframe(pd.DataFrame(all_predictions.data))
else:
    st.warning("Per favore, seleziona il tuo nome e clicca 'Accedi' per fare le tue predizioni.")
