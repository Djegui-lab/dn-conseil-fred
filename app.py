import streamlit as st
import pandas as pd
import sqlite3
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def calculer_total_frais(cb1, cb2):
    total_cb1 = sum(float(str(value).replace(',', '.').replace(' ', '')) for value in cb1)
    total_cb2 = sum(float(str(value).replace(',', '.').replace(' ', '')) for value in cb2)
    return total_cb1 + total_cb2

# Fonction pour créer ou se connecter à la base de données SQLite
def creer_connexion():
    conn = sqlite3.connect("contrats.db")
    return conn

# Fonction pour créer la table si elle n'existe pas
def creer_table_si_non_existe(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contrats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            courtier TEXT,
            fiche INTEGER,
            frais REAL,
            statut_fiche TEXT,
            mail_client TEXT,
            date_reception TEXT,
            cb1 TEXT,
            cb2 TEXT,
            total_frais REAL,
            tel_client INTEGER,
            documents_recus TEXT
        )
    ''')
    conn.commit()

# Fonction pour insérer une fiche dans la base de données
def inserer_contrat(conn, fiche):
    cursor = conn.cursor()

    # Convertir la liste en chaîne séparée par des virgules
    documents_recus_str = ','.join(fiche['documents_recus'])

    cursor.execute('''
        INSERT INTO contrats (courtier, fiche, frais, statut_fiche, mail_client, date_reception , cb1, cb2, total_frais, tel_client, documents_recus)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        fiche['courtier'], fiche['fiche'], fiche['frais'], fiche['statut_fiche'],
        fiche['mail_client'], fiche['date_reception '], ','.join(map(str, fiche['CB1'])),
        ','.join(map(str, fiche['CB2'])), fiche['TOTAL-FRAIS'], fiche['tel_client'], documents_recus_str
    ))
    conn.commit()

# Fonction pour récupérer les fiches depuis la base de données
def recuperer_contrats(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contrats')
    contrats = cursor.fetchall()
    return contrats
# Fonction pour ajouter chaque enregistrement dans Google Sheets
def ajouter_dans_google_sheets(fiche):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        'test-wague-9a205da3c6ca.json',
        ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    )
    gc = gspread.authorize(credentials)

    spreadsheet = gc.open('courtier1')
    sheet = spreadsheet.sheet1

    # Convertir les valeurs de la liste des documents reçus en une seule chaîne séparée par des virgules
    documents_recus_str = ','.join(map(str, fiche['documents_recus']))

    nouvelle_ligne = [fiche['courtier'], fiche['fiche'], fiche['frais'], fiche['statut_fiche'],
                      fiche['mail_client'], fiche['date_reception '], ','.join(map(str, fiche['CB1'])),
                      ','.join(map(str, fiche['CB2'])), fiche['TOTAL-FRAIS'], fiche['tel_client'], documents_recus_str]
    
    # Ajouter la nouvelle ligne à la feuille de calcul
    sheet.append_row(nouvelle_ligne)



# Fonction pour récupérer les données de la feuille de calcul Google Sheets
def recuperer_donnees_google_sheets():
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        'test-wague-9a205da3c6ca.json',
        ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    )
    gc = gspread.authorize(credentials)

    spreadsheet = gc.open('courtier1')
    sheet = spreadsheet.sheet1

    # Récupérer toutes les valeurs dans la feuille de calcul
    data = sheet.get_all_values()

    # Colonnes spécifiques
    columns_to_rename = {
        'TOTAL-FRAIS(pour CB1 & CB2)': 'TOTAL-FRAIS_CB1_CB2',
        'STATUT-FICHES': 'STATUT-FICHES',
        'MAIL-CLIENTS': 'MAIL-CLIENTS',
        'DATE-SOUSCRIPTION': 'DATE-SOUSCRIPTION',
        'TEL-CLIENTS': 'TEL-CLIENTS',
        'documents_recus': 'documents_recus'
    }

    # Renommer les colonnes
    new_header = [columns_to_rename.get(col, col) for col in data[0]]

    # Créer un DataFrame pandas avec les données
    df = pd.DataFrame(data[1:], columns=new_header)

    return df

# Interface utilisateur avec Streamlit
st.title("Application Streamlit pour suivre les fiches")

# Créer la connexion à la base de données
conn = creer_connexion()

# Créer la table si elle n'existe pas
creer_table_si_non_existe(conn)

# Utiliser st.columns pour créer une disposition en colonnes
col1, col2, col3 = st.columns(3)

# Colonne 1  
with col1:
    courtier_options = ['Iness', 'Simon', 'Benoit', 'Sarah', 'Frédéric']
    courtier = st.selectbox("Courtier :", courtier_options)
    numero_fiche = st.number_input("CONTRAT :", min_value=0, step=1, max_value=1)
    frais = st.number_input("Total-Frais-Honoraire-Courtage :")
    statut_fiche = st.selectbox("Statut de la fiche :", ['RAPPEL','OK-CONTRAT', 'NRP','FAUX-NUMERO', 'FAUSSE-FICHE'])

# Colonne 2
with col2:
    mail_client = st.text_input("Mail-client :")
    tel_client = st.text_input("Téléphone client :")
    
    # Sélection des documents reçus
    documents_recus = st.multiselect("Sélectionnez les documents reçus", ["En attente de docs", "Carte grise", "Permis de conduire", "Relevé d'information", "Copie du jugement", "Ordonnance pénale", "48SI"])

# Colonne 3
with col3:
    cb1_input = st.text_input("CB1 (en cas de paiement par tranche) :")
    cb2_input = st.text_input("CB2 (en cas de paiement par tranche) :")
    date_reception  = st.date_input("date_reception  :")

    # Validation des entrées
    try:
        # Convertir les entrées en listes de nombres flottants
        cb1 = [float(value.replace(',', '.').replace(' ', '')) for value in cb1_input.split(',')] if cb1_input else []
        cb2 = [float(value.replace(',', '.').replace(' ', '')) for value in cb2_input.split(',')] if cb2_input else []
    except ValueError:
        st.error("Veuillez saisir des valeurs numériques valides pour CB1 et CB2.")
        st.stop()

# Validation de l'entrée pour tel_client et frais
if st.button("Ajouter la fiche ", key="ajouter_fiche_button"):
    # Vérifier si les documents ont été sélectionnés
    if not documents_recus:
        st.error("Veuillez sélectionner au moins un document avant d'ajouter la fiche.")
        st.stop()

    try:
        # Convertir tel_client en entier
        tel_client = int(tel_client)
    except ValueError:
        st.error("Veuillez saisir un numéro de téléphone valide.")
        st.stop()
    
    # Calcul du TOTAL-FRAIS
    total_frais = calculer_total_frais(cb1, cb2)

    # Créer une fiche temporaire
    fiche_temp = {'courtier': courtier, 'fiche': numero_fiche, 'frais': frais, 'statut_fiche': statut_fiche,
                    'mail_client': mail_client, 'date_reception ': str(date_reception ),
                    'CB1': cb1, 'CB2': cb2, 'TOTAL-FRAIS': total_frais, 'tel_client': tel_client, 'documents_recus': documents_recus}

    # Ajouter la fiche temporaire à la base de données
    inserer_contrat(conn, fiche_temp)

    # Ajouter la fiche à Google Sheets
    ajouter_dans_google_sheets(fiche_temp)

    st.success("Fiche ajoutée avec succès!")

# ... (Le reste de votre code reste inchangé)

# Afficher les fiches depuis la base de données
st.subheader("Tableau des fiches depuis la base de données SQLite:")
fiches_sqlite = recuperer_contrats(conn)
df_sqlite = pd.DataFrame(fiches_sqlite, columns=['id', 'courtier', 'fiche', 'frais', 'statut_fiche', 'mail_client',
                                     'date_reception ', 'cb1', 'cb2', 'total_frais', 'tel_client', 'documents_recus'])
#st.write(df_sqlite)

# Afficher les fiches depuis la feuille de calcul Google Sheets
st.subheader("Tableau des fiches depuis la feuille de calcul Google Sheets:")
donnees_google_sheets = recuperer_donnees_google_sheets()
st.write(donnees_google_sheets)

# Fermer la connexion à la base de données à la fin de l'application
conn.close()

