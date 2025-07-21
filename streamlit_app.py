# streamlit_app.py

import streamlit as st
import json
import requests
from datetime import datetime
import re
from unidecode import unidecode
import time

# Configuration
GITHUB_OWNER = "younessemlali"
GITHUB_REPO = "pixid-provisioning"
GITHUB_BRANCH = "main"

# Configuration de la page
st.set_page_config(
    page_title="Création Utilisateur Pixid - Randstad",
    page_icon="🔐",
    layout="centered"
)

# CSS personnalisé avec couleurs Randstad
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #E30613;
        padding: 20px 0;
        border-bottom: 3px solid #E30613;
        margin-bottom: 30px;
    }
    .success-message {
        padding: 20px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        color: #155724;
        margin: 20px 0;
    }
    .error-message {
        padding: 20px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        color: #721c24;
        margin: 20px 0;
    }
    .stButton > button {
        background-color: #E30613;
        color: white;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #B30510;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# En-tête
st.markdown('<h1 class="main-header">🔐 Création Utilisateur Pixid</h1>', unsafe_allow_html=True)

# Initialisation session state
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False
if 'submission_time' not in st.session_state:
    st.session_state.submission_time = None

# Fonction pour normaliser les noms/prénoms
def normalize_name(name):
    """Normalise les noms pour les emails (supprime accents, garde tirets)"""
    # Convertir en minuscules et supprimer les accents
    normalized = unidecode(name.lower())
    # Garder uniquement lettres, chiffres et tirets
    normalized = re.sub(r'[^a-z0-9-]', '', normalized)
    return normalized

# Fonction pour charger les agences depuis GitHub
@st.cache_data(ttl=900)  # Cache 15 minutes
def load_agencies():
    """Charge la liste des agences depuis GitHub"""
    try:
        url = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/{GITHUB_BRANCH}/reference/agencies.json"
        response = requests.get(url)
        response.raise_for_status()
        agencies = response.json()
        
        # Créer un dictionnaire pour l'affichage
        agencies_dict = {}
        for agency in agencies:
            key = f"{agency['code_unite']} - {agency['libelle_agence']}"
            agencies_dict[key] = agency['code_unite']
        
        return agencies_dict
    except Exception as e:
        st.error(f"Erreur lors du chargement des agences : {str(e)}")
        return {}

# Fonction pour obtenir le token GitHub depuis les secrets Streamlit
def get_github_token():
    """Récupère le token GitHub depuis les secrets Streamlit"""
    try:
        return st.secrets["github"]["token"]
    except:
        st.error("⚠️ Token GitHub non configuré dans les secrets Streamlit")
        return None

# Fonction pour créer un commit sur GitHub
def create_github_commit(user_data):
    """Crée un fichier JSON dans le dossier pending/ sur GitHub"""
    token = get_github_token()
    if not token:
        return False, "Token GitHub manquant"
    
    # Nom du fichier avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"pending/user_{timestamp}_{user_data['email'].replace('@', '_at_')}.json"
    
    # Contenu du fichier
    content = json.dumps(user_data, indent=2, ensure_ascii=False)
    
    # Encodage en base64
    import base64
    content_base64 = base64.b64encode(content.encode()).decode()
    
    # Préparation de la requête
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{filename}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    payload = {
        "message": f"Nouvelle création utilisateur: {user_data['prenom']} {user_data['nom']}",
        "content": content_base64,
        "branch": GITHUB_BRANCH
    }
    
    try:
        response = requests.put(url, json=payload, headers=headers)
        response.raise_for_status()
        return True, filename
    except requests.exceptions.HTTPError as e:
        return False, f"Erreur HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

# Liste des profils Pixid
PROFILS_PIXID = [
    "Agence",
    "Administrateur Délégué ETT",
    "Administrateur Délégué - SELF",
    "Administrateur+BI+myPixid+SELF",
    "AdministrationPaieIntérimaire",
    "Agence avec proposition",
    "CSBO",
    "Facture",
    "Implant",
    "Kam",
    "PDFSigné",
    "PSI",
    "Reporting",
    "SGF&P",
    "Side",
    "Support Applicatif AI"
]

# Chargement des agences
agencies = load_agencies()

# Reset du formulaire si soumission il y a plus de 5 secondes
if st.session_state.form_submitted and st.session_state.submission_time:
    if time.time() - st.session_state.submission_time > 5:
        st.session_state.form_submitted = False

# Affichage du message de succès
if st.session_state.form_submitted:
    st.markdown("""
        <div class="success-message">
            <h3>✅ Demande enregistrée avec succès !</h3>
            <p>La création de l'utilisateur sera traitée automatiquement dans quelques minutes.</p>
            <p>Vous recevrez un email de confirmation à l'adresse : <strong>younes.semlali@randstad.fr</strong></p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("Créer un autre utilisateur"):
        st.session_state.form_submitted = False
        st.rerun()
else:
    # Formulaire de création
    with st.form("creation_user", clear_on_submit=True):
        st.markdown("### Informations de l'utilisateur")
        
        col1, col2 = st.columns(2)
        
        with col1:
            prenom = st.text_input("Prénom *", placeholder="Jean")
        
        with col2:
            nom = st.text_input("Nom *", placeholder="Dupont")
        
        # Email généré automatiquement
        if prenom and nom:
            email_genere = f"{normalize_name(prenom)}.{normalize_name(nom)}@randstad.fr"
            st.info(f"📧 Email généré : **{email_genere}**")
        else:
            email_genere = ""
            st.info("📧 L'email sera généré automatiquement : prenom.nom@randstad.fr")
        
        telephone = st.text_input("Téléphone (optionnel)", placeholder="01 23 45 67 89")
        
        st.markdown("### Affectation")
        
        # Sélection de l'agence
        if agencies:
            agence_selectionnee = st.selectbox(
                "Agence *",
                options=list(agencies.keys()),
                help="Sélectionnez l'agence de rattachement"
            )
            code_agence = agencies[agence_selectionnee]
        else:
            st.error("Impossible de charger la liste des agences")
            agence_selectionnee = None
            code_agence = None
        
        # Sélection du profil
        profil = st.selectbox(
            "Profil Pixid *",
            options=PROFILS_PIXID,
            help="Sélectionnez le profil utilisateur dans Pixid"
        )
        
        st.markdown("---")
        
        # Boutons
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            submit_button = st.form_submit_button(
                "🚀 Créer l'utilisateur",
                use_container_width=True
            )
        
        with col2:
            test_sftp = st.form_submit_button(
                "🔌 Tester connexion SFTP",
                use_container_width=True
            )
        
        # Validation et soumission
        if submit_button:
            # Validation des champs obligatoires
            if not prenom:
                st.error("❌ Le prénom est obligatoire")
            elif not nom:
                st.error("❌ Le nom est obligatoire")
            elif not agence_selectionnee:
                st.error("❌ L'agence est obligatoire")
            elif not profil:
                st.error("❌ Le profil est obligatoire")
            else:
                # Préparation des données
                user_data = {
                    "prenom": prenom.strip(),
                    "nom": nom.strip(),
                    "email": email_genere,
                    "telephone": telephone.strip() if telephone else "",
                    "code_agence": code_agence,
                    "libelle_agence": agence_selectionnee,
                    "profil": profil,
                    "date_creation": datetime.now().isoformat(),
                    "created_by": "streamlit_app"
                }
                
                # Création du commit
                with st.spinner("Envoi de la demande..."):
                    success, result = create_github_commit(user_data)
                
                if success:
                    st.session_state.form_submitted = True
                    st.session_state.submission_time = time.time()
                    st.rerun()
                else:
                    st.error(f"❌ Erreur lors de l'envoi : {result}")
        
        elif test_sftp:
            # Test de connexion SFTP
            with st.spinner("Test de connexion au serveur SFTP Pixid..."):
                try:
                    import paramiko
                    
                    # Récupération des credentials depuis les secrets
                    sftp_host = st.secrets.get("pixid", {}).get("sftp_host", "integrationprod.pixid-services.net")
                    sftp_user = st.secrets.get("pixid", {}).get("sftp_user", "EXT4005")
                    sftp_pass = st.secrets.get("pixid", {}).get("sftp_pass", "")
                    
                    if not sftp_pass:
                        st.warning("⚠️ Mot de passe SFTP non configuré dans les secrets")
                    else:
                        # Test de connexion
                        transport = paramiko.Transport((sftp_host, 22))
                        transport.connect(username=sftp_user, password=sftp_pass)
                        sftp = paramiko.SFTPClient.from_transport(transport)
                        
                        # Test listing du répertoire
                        sftp.listdir('/inbox/')
                        
                        sftp.close()
                        transport.close()
                        
                        st.success("✅ Connexion SFTP réussie !")
                except Exception as e:
                    st.error(f"❌ Erreur de connexion SFTP : {str(e)}")

# Pied de page
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Randstad France - Système de provisioning Pixid</p>
        <p style='font-size: 0.8em;'>En cas de problème, contactez : younes.semlali@randstad.fr</p>
    </div>
    """,
    unsafe_allow_html=True
)
