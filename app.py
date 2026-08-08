import os
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st


def resolve_column(df, candidates):
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None


def apply_plotly_theme(fig):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(family="Arial", size=13, color="#111827"),
        title=dict(font=dict(size=18, family="Arial Black", color="#111827")),
    )
    fig.update_traces(marker_line_color="#ffffff", marker_line_width=1.5)
    return fig


def build_books_dashboard(conn):
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
    if "books" not in tables["name"].values:
        st.error("La table 'books' n'existe pas dans la base de données.")
        return

    df = pd.read_sql("SELECT * FROM books", conn)
    st.subheader(f"📚 {len(df)} livres récupérés")

    st.markdown(
        """
        <div style="background: linear-gradient(90deg, #eef2ff 0%, #f8fafc 100%); padding: 1rem 1.2rem; border-radius: 14px; border: 1px solid #e5e7eb; margin-bottom: 1rem;">
            <strong>Analyse des livres</strong><br>
            Visualisation rapide des prix, des notes et de la disponibilité.
        </div>
        """,
        unsafe_allow_html=True,
    )

    price_col = resolve_column(df, ["V2_Prix", "prix", "price"])
    if price_col:
        df["prix_clean"] = pd.to_numeric(df[price_col], errors="coerce")
        prix_clean = df["prix_clean"]
    else:
        prix_clean = pd.Series([pd.NA] * len(df), dtype="float64")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Nombre total de livres", len(df))
    with col2:
        st.metric("Prix moyen", f"{prix_clean.mean():.2f} £" if price_col else "N/A")
    with col3:
        st.metric("Prix minimum", f"{prix_clean.min():.2f} £" if price_col else "N/A")
    with col4:
        st.metric("Prix maximum", f"{prix_clean.max():.2f} £" if price_col else "N/A")

    st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        if price_col:
            fig = px.histogram(
                df,
                x="prix_clean",
                nbins=25,
                title="Distribution des prix",
                color_discrete_sequence=["#6366f1"],
            )
            fig = apply_plotly_theme(fig)
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        rating_col = resolve_column(df, ["V5_Note", "note", "rating"])
        if rating_col:
            rating_counts = df[rating_col].value_counts().sort_index().reset_index()
            rating_counts.columns = ["Note", "Nombre"]
            fig = px.bar(
                rating_counts,
                x="Note",
                y="Nombre",
                text="Nombre",
                title="Répartition des notes",
                color_discrete_sequence=["#10b981"],
            )
            fig = apply_plotly_theme(fig)
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

    availability_col = resolve_column(df, ["V3_Disponibilite", "disponibilite", "availability"])
    if availability_col:
        fig = px.pie(
            df,
            names=availability_col,
            title="Disponibilité des livres",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        fig = apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("Voir les données"):
        st.dataframe(df, use_container_width=True)


def build_cars_dashboard(conn):
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
    if "cars" not in tables["name"].values:
        st.error("La table 'cars' n'existe pas dans la base de données.")
        return

    df = pd.read_sql("SELECT * FROM cars", conn)
    st.subheader(f"🚗 {len(df)} voitures récupérées")

    st.markdown(
        """
        <div style="background: linear-gradient(90deg, #ecfeff 0%, #f8fafc 100%); padding: 1rem 1.2rem; border-radius: 14px; border: 1px solid #e5e7eb; margin-bottom: 1rem;">
            <strong>Analyse des voitures</strong><br>
            Mise en avant des marques, des boîtes de vitesses et des régions.
        </div>
        """,
        unsafe_allow_html=True,
    )

    marque_col = resolve_column(df, ["marque", "V1_Marque", "Marque", "schema_brand"])
    region_col = resolve_column(df, ["region", "V7_Region", "Région", "location"])
    boite_col = resolve_column(df, ["boite", "V6_Boite", "Boite", "numberOfDoors"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nombre total de voitures", len(df))
    with col2:
        st.metric("Nombre de marques", df[marque_col].nunique() if marque_col else "N/A")
    with col3:
        st.metric("Nombre de régions", df[region_col].nunique() if region_col else "N/A")

    st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        if marque_col:
            top_marques = df[marque_col].value_counts().head(10).reset_index()
            top_marques.columns = ["Marque", "Nombre"]
            fig = px.bar(
                top_marques,
                x="Marque",
                y="Nombre",
                text="Nombre",
                title="Top 10 des marques",
                color_discrete_sequence=["#0f766e"],
            )
            fig = apply_plotly_theme(fig)
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Colonne marque non trouvée")

    with col_b:
        if boite_col:
            fig = px.pie(
                df,
                names=boite_col,
                title="Répartition des boîtes de vitesses",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig = apply_plotly_theme(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Colonne boîte non trouvée")

    if region_col:
        top_regions = df[region_col].value_counts().head(10).reset_index()
        top_regions.columns = ["Région", "Nombre"]
        fig = px.bar(
            top_regions,
            x="Région",
            y="Nombre",
            text="Nombre",
            title="Top 10 des régions",
            color_discrete_sequence=["#f59e0b"],
        )
        fig = apply_plotly_theme(fig)
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("Voir les données"):
        st.dataframe(df, use_container_width=True)


# === Configuration de la page ===
st.set_page_config(page_title="Data App", page_icon="📊", layout="wide")

st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
    body {
        font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background: #f1f5f9;
        color: #0f172a;
    }
    [data-testid="stAppViewContainer"] {
        background: transparent;
        padding: 1.2rem 1.2rem 2rem;
    }
    [data-testid="stSidebar"] {
        background: #0d1f36 !important;
        color: #e2e8f0;
        border-right: 1px solid rgba(226, 232, 240, 0.08);
    }
    [data-testid="stSidebar"] .block-container {
        padding: 1.1rem 1rem 1.5rem !important;
    }
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label {
        color: #e2e8f0 !important;
    }
    .sidebar-menu {
        margin-bottom: 1rem;
        padding: 0.8rem 0.8rem 0.9rem;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 18px;
    }
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.94);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 18px;
        padding: 1rem 1rem 0.8rem;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.06);
    }
    div[data-testid="stMetric"] span[data-testid="stMetricLabel"] {
        color: #475569;
        font-weight: 600;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #0f172a;
        font-size: 1.45rem;
        font-weight: 700;
    }
    section[data-testid="stExpander"] > div:first-child {
        border-radius: 18px;
        border: 1px solid rgba(148, 163, 184, 0.14);
        background: rgba(255, 255, 255, 0.96);
        box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06);
    }
    .stPlotlyChart,
    .stChart {
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 16px 32px rgba(15, 23, 42, 0.06);
    }
    button,
    button:focus-visible,
    button:hover {
        border-radius: 999px !important;
        background: #2563eb !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 10px 25px rgba(37, 99, 235, 0.18) !important;
    }
    button:hover {
        transform: translateY(-1px);
    }
    a,
    a:visited {
        color: #1d4ed8;
    }
    .hero-card,
    .section-card {
        background: rgba(255, 255, 255, 0.98);
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 22px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1.3rem;
        box-shadow: 0 14px 30px rgba(15, 23, 42, 0.05);
    }
    .hero-card h1,
    .section-card h2 {
        margin-top: 0;
        color: #0f172a;
    }
    .hero-card p,
    .section-card p,
    .section-card ul {
        color: #475569;
        line-height: 1.75;
    }
    .badge-custom {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.4rem;
        border-radius: 999px;
        background: #e0f2fe;
        color: #1d4ed8;
        padding: 0.6rem 0.9rem;
        font-weight: 600;
        margin-top: 0.75rem;
    }
    @media (max-width: 768px) {
        [data-testid="stAppViewContainer"] {
            padding: 1rem;
        }
        .hero-card,
        .section-card {
            padding: 1.1rem 1.1rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Collecte & Analyse")
st.markdown("---")

# === Chemins relatifs ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "data_collection.db")

# === Menu latéral ===
st.sidebar.markdown("### Menu")
menu = st.sidebar.radio(
    "",
    [
        "🏠 Accueil",
        "📊 Dashboard",
        "📥 Données brutes",
        "📝 Formulaires",
    ],
    index=0,
)

# === PAGE ACCUEIL ===
if menu == "Accueil":
    st.markdown(
        """
        <div class="hero-card">
            <h1>Bienvenue sur votre application de collecte et d'analyse</h1>
            <p>Une interface claire pour explorer les données nettoyées et télécharger les données brutes en un clic.</p>
            <div class="badge-custom">Facile à lire · Données visibles · Navigation simple</div>
        </div>
        <div class="section-card">
            <h2>Que pouvez-vous faire ici ?</h2>
            <ul>
                <li>Voir les tendances des livres et des voitures</li>
                <li>Analyser les métriques principales sans surcharge visuelle</li>
                <li>Télécharger les données brutes pour un usage offline</li>
                <li>Accéder rapidement aux formulaires d'évaluation</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

# === PAGE DASHBOARD ===
elif menu == "Dashboard":
    st.header("📈 Dashboard des données nettoyées")

    if not os.path.exists(DB_PATH):
        st.error(
            f"Base de données introuvable à {DB_PATH}. Vérifie que le fichier data_collection.db est dans le dossier data/."
        )
    else:
        try:
            conn = sqlite3.connect(DB_PATH)

            choix = st.radio(
                "Choisir la source de données :",
                ["Livres (Books to Scrape)", "Voitures (Gaaraas)"],
                horizontal=True,
            )

            if choix == "Livres (Books to Scrape)":
                build_books_dashboard(conn)
            else:
                build_cars_dashboard(conn)

            conn.close()

        except Exception as e:
            st.error(f"Erreur lors de la lecture de la base : {e}")

# === PAGE TÉLÉCHARGEMENT ===
elif menu == "Téléchargement données brutes":
    st.header("📥 Téléchargement des données brutes (No-code)")
    st.write("Téléchargez les fichiers CSV bruts issus de Web Scraper :")

    books_csv = os.path.join(DATA_DIR, "books_brut.csv")
    if os.path.exists(books_csv):
        with open(books_csv, "rb") as f:
            st.download_button(
                label="Télécharger Books bruts",
                data=f,
                file_name="books_brut.csv",
                mime="text/csv",
            )
    else:
        st.warning("Fichier books_brut.csv non trouvé dans data/.")

    cars_csv = os.path.join(DATA_DIR, "gaaraas_brut.csv")
    if os.path.exists(cars_csv):
        with open(cars_csv, "rb") as f:
            st.download_button(
                label="Télécharger Gaaraas bruts",
                data=f,
                file_name="gaaraas_brut.csv",
                mime="text/csv",
            )
    else:
        st.warning("Fichier gaaraas_brut.csv non trouvé dans data/.")

# === PAGE FORMULAIRES ===
elif menu == "Formulaires d'évaluation":
    st.header("📝 Formulaires d'évaluation de l'application")
    st.write("Votre avis nous aide à améliorer l'application.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Formulaire Kobo")
        st.link_button(
            "Remplir le formulaire Kobo",
            "https://ee.kobotoolbox.org/x/wjF8NPvg",
        )
    with col2:
        st.subheader("Formulaire Google Forms")
        st.link_button(
            "Remplir le formulaire Google Forms",
            "https://docs.google.com/forms/d/e/1FAIpQLScK9rU2LxRYeGuR7Z6yW0aYgPIH7P3una4jg8G3pY3a8fccvw/viewform",
        )
