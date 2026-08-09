import os
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------
# Fonctions utilitaires
# ---------------------------

def resolve_column(df, candidates):
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None


def apply_plotly_theme(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(family="Inter, Arial, sans-serif", size=13, color="#e2e8f0"),
        title=dict(font=dict(size=17, family="Inter, Arial, sans-serif", color="#f8fafc")),
        legend=dict(font=dict(size=12, color="#e2e8f0")),
    )
    fig.update_traces(marker_line_color="rgba(255,255,255,0.3)", marker_line_width=1)
    return fig


def metric_card(label, value, icon, color):
    """Carte de métrique pour fond sombre."""
    return f"""
    <div class="metric-card">
        <div class="metric-label">
            <i class="{icon}" style="color:{color};"></i>
            <span>{label}</span>
        </div>
        <div class="metric-value">{value}</div>
    </div>
    """


def section_header(title, description, icon, color):
    """En-tête de section pour fond sombre."""
    return f"""
    <div class="section-header" style="border-left-color: {color};">
        <h3>{icon} {title}</h3>
        <p>{description}</p>
    </div>
    """


# ---------------------------
# Chargement des données
# ---------------------------

@st.cache_data(ttl=300, show_spinner="Chargement des données...")
def load_table(db_path, table_name):
    if not os.path.exists(db_path):
        return pd.DataFrame()

    try:
        with sqlite3.connect(db_path) as conn:
            tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
            if table_name not in tables["name"].values:
                return pd.DataFrame()
            return pd.read_sql(f"SELECT * FROM {table_name}", conn)
    except Exception:
        return pd.DataFrame()


# ---------------------------
# Dashboard Livres
# ---------------------------

def build_books_dashboard(df):
    if df.empty:
        st.warning("Aucune donnée de livres trouvée. Vérifie que la table **books** existe dans la base.")
        return

    st.markdown(
        section_header(
            f"{len(df)} livres récupérés",
            "Aperçu des prix, des notes et de la disponibilité.",
            "📚",
            "#6366f1"
        ),
        unsafe_allow_html=True
    )

    # Nettoyage des prix
    price_col = resolve_column(df, ["V2_Prix", "prix", "price", "Prix"])
    if price_col:
        df = df.copy()
        df["prix_clean"] = (
            df[price_col]
            .astype(str)
            .str.replace(r"[^\d.,]", "", regex=True)
            .str.replace(",", ".", regex=False)
        )
        df["prix_clean"] = pd.to_numeric(df["prix_clean"], errors="coerce")
        prix_clean = df["prix_clean"].dropna()
    else:
        prix_clean = pd.Series(dtype="float64")

    # Métriques
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(metric_card("Total", f"{len(df)}", "fas fa-book", "#60a5fa"), unsafe_allow_html=True)
    with c2:
        val = f"{prix_clean.mean():.2f} £" if not prix_clean.empty else "—"
        st.markdown(metric_card("Prix moyen", val, "fas fa-pound-sign", "#34d399"), unsafe_allow_html=True)
    with c3:
        val = f"{prix_clean.min():.2f} £" if not prix_clean.empty else "—"
        st.markdown(metric_card("Prix min", val, "fas fa-arrow-down", "#fbbf24"), unsafe_allow_html=True)
    with c4:
        val = f"{prix_clean.max():.2f} £" if not prix_clean.empty else "—"
        st.markdown(metric_card("Prix max", val, "fas fa-arrow-up", "#f87171"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        if not prix_clean.empty:
            fig = px.histogram(
                df.dropna(subset=["prix_clean"]),
                x="prix_clean",
                nbins=25,
                title="Distribution des prix",
                color_discrete_sequence=["#6366f1"]
            )
            fig = apply_plotly_theme(fig)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Impossible d’afficher la distribution des prix.")

    with col_b:
        rating_col = resolve_column(df, ["V5_Note", "note", "rating", "Note"])
        if rating_col:
            rating_counts = df[rating_col].value_counts().sort_index().reset_index()
            rating_counts.columns = ["Note", "Nombre"]
            fig = px.bar(
                rating_counts,
                x="Note",
                y="Nombre",
                text="Nombre",
                title="Répartition des notes",
                color_discrete_sequence=["#10b981"]
            )
            fig = apply_plotly_theme(fig)
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Colonne des notes introuvable.")

    # Disponibilité
    availability_col = resolve_column(df, ["V3_Disponibilite", "disponibilite", "availability", "Disponibilité"])
    if availability_col:
        st.markdown("#### Disponibilité des livres ")
        fig = px.pie(
            df,
            names=availability_col,
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig = apply_plotly_theme(fig)
        fig.update_traces(textinfo="percent+label", textposition="inside")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with st.expander("Voir les données brutes"):
        st.dataframe(df, use_container_width=True)


# ---------------------------
# Dashboard Voitures
# ---------------------------

def build_cars_dashboard(df):
    if df.empty:
        st.warning("Aucune donnée de voitures trouvée. Vérifie que la table **cars** existe dans la base.")
        return

    st.markdown(
        section_header(
            f"{len(df)} voitures récupérées",
            "Aperçu des marques, boîtes de vitesses et régions.",
            "🚗",
            "#0f766e"
        ),
        unsafe_allow_html=True
    )

    marque_col = resolve_column(df, ["marque", "V1_Marque", "Marque", "schema_brand", "brand"])
    region_col = resolve_column(df, ["region", "V7_Region", "Région", "location", "Region"])
    boite_col = resolve_column(df, ["data8", "boite", "V6_Boite", "Boite", "boîte", "transmission", "gearbox"])

    # Nettoyage marque
    if marque_col:
        df = df.copy()
        df["marque_clean"] = (
            df[marque_col]
            .astype(str)
            .str.replace(r"(?i)^détail\s*", "", regex=True)
            .str.strip()
        )
        marque_col_clean = "marque_clean"
    else:
        marque_col_clean = None

    # Métriques
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(metric_card("Total", f"{len(df)}", "fas fa-car", "#60a5fa"), unsafe_allow_html=True)
    with c2:
        nb = df[marque_col].nunique() if marque_col else "—"
        st.markdown(metric_card("Marques", str(nb), "fas fa-tag", "#f472b6"), unsafe_allow_html=True)
    with c3:
        nb = df[region_col].nunique() if region_col else "—"
        st.markdown(metric_card("Régions", str(nb), "fas fa-globe", "#34d399"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        # Top 10 des marques (barres horizontales)
        if marque_col_clean:
            top = df[marque_col_clean].value_counts().head(10).reset_index()
            top.columns = ["Marque", "Nombre"]
            fig1 = px.bar(
                top,
                x="Nombre",
                y="Marque",
                text="Nombre",
                title="Top 10 des marques (nombre de voitures)",
                orientation="h",
                color_discrete_sequence=["#0f766e"]
            )
            fig1 = apply_plotly_theme(fig1)
            fig1.update_traces(textposition="outside")
            st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Colonne marque non trouvée.")

        # Prix moyen par marque
        price_col = resolve_column(df, ["prix", "price", "V2_Prix", "Prix"])
        if price_col and marque_col_clean:
            df["prix_clean"] = pd.to_numeric(df[price_col], errors="coerce")
            avg_price = (
                df.groupby(marque_col_clean)["prix_clean"]
                .mean()
                .sort_values(ascending=False)
                .head(10)
                .reset_index()
            )
            avg_price.columns = ["Marque", "Prix moyen"]
            fig2 = px.bar(
                avg_price,
                x="Marque",
                y="Prix moyen",
                text="Prix moyen",
                title="Top 10 des marques par prix moyen",
                color_discrete_sequence=["#f59e0b"]
            )
            fig2 = apply_plotly_theme(fig2)
            fig2.update_traces(texttemplate='%{text:.0f} £', textposition="outside")
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Colonne prix non trouvée pour le prix moyen.")

    with col_b:
        if boite_col:
            fig = px.pie(
                df,
                names=boite_col,
                title="Répartition des boîtes",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig = apply_plotly_theme(fig)
            fig.update_traces(textinfo="percent+label", textposition="inside")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Colonne boîte de vitesses non trouvée.")

    if region_col:
        st.markdown("#### Top 10 des régions")
        top = df[region_col].value_counts().head(10).reset_index()
        top.columns = ["Région", "Nombre"]
        fig = px.bar(
            top, x="Région", y="Nombre", text="Nombre",
            color_discrete_sequence=["#f59e0b"]
        )
        fig = apply_plotly_theme(fig)
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with st.expander("Voir les données "):
        st.dataframe(df, use_container_width=True)


# ---------------------------
# Configuration page
# ---------------------------

st.set_page_config(
    page_title="Collecte & Analyse",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS pour un thème sombre cohérent
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">

<style>
/* ========== FOND ========== */
.stApp {
    background-color: #0f172a !important;
    font-family: 'Inter', system-ui, sans-serif;
    color: #e2e8f0;
}

[data-testid="stAppViewContainer"] > .main {
    background-color: #0f172a;
}

/* ========== SIDEBAR ========== */
[data-testid="stSidebar"] {
    background-color: #1e293b !important;
}

[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}

[data-testid="stSidebar"] .stRadio label {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(148,163,184,0.15) !important;
    border-radius: 12px !important;
    padding: 0.85rem 1.1rem !important;
    margin-bottom: 0.4rem !important;
    transition: all 0.2s ease;
}

[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,255,255,0.12) !important;
    transform: translateX(4px);
}

/* ========== CARTES MÉTRIQUES ========== */
.metric-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(148,163,184,0.15);
    border-radius: 14px;
    padding: 1.1rem 1.2rem;
    backdrop-filter: blur(6px);
    height: 100%;
}

.metric-label {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: #94a3b8;
}

.metric-label i {
    font-size: 1rem;
}

.metric-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: #f1f5f9;
    line-height: 1.2;
}

/* ========== EN-TÊTES ========== */
.section-header {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(148,163,184,0.12);
    border-left: 5px solid #6366f1;
    border-radius: 12px;
    padding: 1.1rem 1.4rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(6px);
}

.section-header h3 {
    margin: 0 0 0.25rem 0 !important;
    color: #f1f5f9 !important;
    font-size: 1.25rem !important;
    font-weight: 700 !important;
}

.section-header p {
    margin: 0 !important;
    color: #94a3b8 !important;
    font-size: 0.95rem !important;
}

/* ========== CARTES ACCUEIL ========== */
.hero-card, .section-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(148,163,184,0.12);
    border-radius: 16px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.4rem;
    backdrop-filter: blur(6px);
}

.hero-card h1 {
    color: #f1f5f9 !important;
    margin-top: 0 !important;
}

.section-card h2 {
    color: #f1f5f9 !important;
    margin-top: 0 !important;
}

.hero-card p, .section-card p, .section-card li {
    color: #cbd5e1 !important;
    line-height: 1.65;
}

.badge-custom {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    background: rgba(59, 130, 246, 0.2);
    color: #93c5fd;
    padding: 0.4rem 0.9rem;
    border-radius: 999px;
    font-weight: 600;
    font-size: 0.9rem;
    margin-top: 0.8rem;
}

/* ========== GRAPHIQUES ========== */
.stPlotlyChart {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(148,163,184,0.12);
    border-radius: 14px;
    padding: 0.5rem;
}

/* ========== EXPANDER ========== */
.streamlit-expanderHeader {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(148,163,184,0.12) !important;
    border-radius: 10px !important;
    color: #f1f5f9 !important;
    font-weight: 600 !important;
}

.streamlit-expanderContent {
    background: rgba(255,255,255,0.02) !important;
}

/* ========== BOUTONS ========== */
.stDownloadButton button, .stButton button {
    background: #2563eb !important;
    color: white !important;
    border: none !important;
    border-radius: 999px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.6rem !important;
}

.stDownloadButton button:hover, .stButton button:hover {
    background: #1d4ed8 !important;
}

/* ========== TITRES ========== */
h1, h2, h3 {
    color: #f1f5f9 !important;
}

/* ========== ALERTES ========== */
.stAlert {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(148,163,184,0.12) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}

/* ========== DATAFRAME ========== */
.dataframe {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 10px;
    border: 1px solid rgba(148,163,184,0.1);
}
.dataframe th {
    background: rgba(99,102,241,0.15) !important;
    color: #f1f5f9 !important;
}
.dataframe td {
    color: #cbd5e1 !important;
}

/* ========== RADIO ========== */
.stRadio label {
    color: #e2e8f0 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Chemins
# ---------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "data_collection.db")

# ---------------------------
# Navigation
# ---------------------------

st.sidebar.markdown("### Navigation")
menu = st.sidebar.radio(
    "Aller à",
    ["Accueil", "Dashboard", "Données brutes", "Formulaires"],
    format_func=lambda x: {
        "Accueil": "🏠  Accueil",
        "Dashboard": "📈  Dashboard",
        "Données brutes": "📥  Données brutes",
        "Formulaires": "📝  Formulaires",
    }[x],
    label_visibility="collapsed"
)

# ---------------------------
# Pages
# ---------------------------

if menu == "Accueil":
    st.markdown("""
    <div class="hero-card">
        <h1>Bienvenue 👋</h1>
        <p>Cette application te permet d’explorer facilement les données collectées sur les livres et les voitures.</p>
        <div class="badge-custom">
            <i class="fas fa-check-circle"></i> Simple · Clair · Pratique
        </div>
    </div>

    <div class="section-card">
        <h2>Ce que tu peux faire</h2>
        <ul>
            <li>Visualiser les tendances des livres et des voitures</li>
            <li>Consulter les métriques principales rapidement</li>
            <li>Télécharger les fichiers bruts</li>
            <li>Donner ton avis via les formulaires</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

elif menu == "Dashboard":
    st.header("Dashboard des données")

    if not os.path.exists(DB_PATH):
        st.error(f"""
        **Base de données introuvable**

        Chemin attendu :  
        `{DB_PATH}`

        Vérifie que le fichier `data_collection.db` se trouve bien dans le dossier `data/`.
        """)
    else:
        choix = st.radio(
            "Quelle source veux-tu explorer ?",
            ["Livres (Books to Scrape)", "Voitures (Gaaraas)"],
            horizontal=True
        )

        if choix.startswith("Livres"):
            df = load_table(DB_PATH, "books")
            build_books_dashboard(df)
        else:
            df = load_table(DB_PATH, "cars")
            build_cars_dashboard(df)

elif menu == "Données brutes":
    st.header("Téléchargement des données brutes")
    st.write("Télécharge les fichiers CSV issus du scraping.")

    col1, col2 = st.columns(2)

    with col1:
        path = os.path.join(DATA_DIR, "books_brut.csv")
        if os.path.exists(path):
            with open(path, "rb") as f:
                st.download_button(
                    "📚 Télécharger Books bruts",
                    data=f,
                    file_name="books_brut.csv",
                    mime="text/csv"
                )
        else:
            st.warning("Fichier `books_brut.csv` introuvable.")

    with col2:
        path = os.path.join(DATA_DIR, "gaaraas_brut.csv")
        if os.path.exists(path):
            with open(path, "rb") as f:
                st.download_button(
                    "🚗 Télécharger Gaaraas bruts",
                    data=f,
                    file_name="gaaraas_brut.csv",
                    mime="text/csv"
                )
        else:
            st.warning("Fichier `gaaraas_brut.csv` introuvable.")

elif menu == "Formulaires":
    st.header("Ton avis compte")
    st.write("Remplis l’un des formulaires ci-dessous pour m’aider à améliorer l’application.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Formulaire Kobo")
        st.link_button("Ouvrir le formulaire Kobo", "https://ee.kobotoolbox.org/x/wjF8NPvg")

    with col2:
        st.subheader("Formulaire Google Forms")
        st.link_button(
            "Ouvrir le formulaire Google",
            "https://docs.google.com/forms/d/e/1FAIpQLScK9rU2LxRYeGuR7Z6yW0aYgPIH7P3una4jg8G3pY3a8fccvw/viewform"
        )
