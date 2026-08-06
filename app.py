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
        font=dict(family="Arial", size=13, color="#1e293b"),
        title=dict(font=dict(size=18, family="Arial Black", color="#0f172a")),
        legend=dict(font=dict(size=12)),
    )
    fig.update_traces(marker_line_color="rgba(255,255,255,0.3)", marker_line_width=1)
    return fig


def build_books_dashboard(conn):
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
    if "books" not in tables["name"].values:
        st.error("❌ La table 'books' n'existe pas dans la base de données.")
        return

    df = pd.read_sql("SELECT * FROM books", conn)

    st.markdown(
        f"""
        <div style="background: rgba(99, 102, 241, 0.08); backdrop-filter: blur(6px); padding: 1.2rem 1.5rem; border-radius: 16px; border: 1px solid rgba(99, 102, 241, 0.2); margin-bottom: 1.5rem;">
            <h3 style="margin: 0; color: #e2e8f0;">📚 {len(df)} livres récupérés</h3>
            <p style="margin: 0.2rem 0 0 0; color: #94a3b8; font-size: 0.95rem;">Visualisation rapide des prix, des notes et de la disponibilité.</p>
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

    # Métriques sans fond blanc
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
            <div style="background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 12px; padding: 0.8rem 1rem; backdrop-filter: blur(4px);">
                <div style="font-size: 0.75rem; color: #93c5fd; text-transform: uppercase; letter-spacing: 0.5px;">📦 Total</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: #bfdbfe;">{len(df)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 12px; padding: 0.8rem 1rem; backdrop-filter: blur(4px);">
                <div style="font-size: 0.75rem; color: #6ee7b7; text-transform: uppercase; letter-spacing: 0.5px;">💰 Prix moyen</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: #a7f3d0;">{f"{prix_clean.mean():.2f} £" if price_col else "N/A"}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.2); border-radius: 12px; padding: 0.8rem 1rem; backdrop-filter: blur(4px);">
                <div style="font-size: 0.75rem; color: #fcd34d; text-transform: uppercase; letter-spacing: 0.5px;">⬇️ Prix min</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: #fde68a;">{f"{prix_clean.min():.2f} £" if price_col else "N/A"}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
            <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 12px; padding: 0.8rem 1rem; backdrop-filter: blur(4px);">
                <div style="font-size: 0.75rem; color: #fca5a5; text-transform: uppercase; letter-spacing: 0.5px;">⬆️ Prix max</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: #fca5a5;">{f"{prix_clean.max():.2f} £" if price_col else "N/A"}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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
            fig.update_layout(title_font_color="#e2e8f0")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

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
            fig.update_layout(title_font_color="#e2e8f0")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    availability_col = resolve_column(df, ["V3_Disponibilite", "disponibilite", "availability"])
    if availability_col:
        st.markdown("### 📊 Disponibilité des livres")
        fig = px.pie(
            df,
            names=availability_col,
            title="",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        fig = apply_plotly_theme(fig)
        fig.update_traces(textinfo="percent+label", textposition="inside")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with st.expander("📋 Voir les données brutes", expanded=False):
        st.dataframe(df, use_container_width=True)


def build_cars_dashboard(conn):
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
    if "cars" not in tables["name"].values:
        st.error("❌ La table 'cars' n'existe pas dans la base de données.")
        return

    df = pd.read_sql("SELECT * FROM cars", conn)

    st.markdown(
        f"""
        <div style="background: rgba(15, 118, 110, 0.08); backdrop-filter: blur(6px); padding: 1.2rem 1.5rem; border-radius: 16px; border: 1px solid rgba(15, 118, 110, 0.2); margin-bottom: 1.5rem;">
            <h3 style="margin: 0; color: #e2e8f0;">🚗 {len(df)} voitures récupérées</h3>
            <p style="margin: 0.2rem 0 0 0; color: #94a3b8; font-size: 0.95rem;">Mise en avant des marques, boîtes de vitesses et régions.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    marque_col = resolve_column(df, ["marque", "V1_Marque", "Marque", "schema_brand"])
    region_col = resolve_column(df, ["region", "V7_Region", "Région", "location"])
    boite_col = resolve_column(df, ["boite", "V6_Boite", "Boite", "numberOfDoors"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div style="background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 12px; padding: 0.8rem 1rem; backdrop-filter: blur(4px);">
                <div style="font-size: 0.75rem; color: #93c5fd; text-transform: uppercase; letter-spacing: 0.5px;">🚘 Total</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: #bfdbfe;">{len(df)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        nb_marques = df[marque_col].nunique() if marque_col else "N/A"
        st.markdown(
            f"""
            <div style="background: rgba(236, 72, 153, 0.15); border: 1px solid rgba(236, 72, 153, 0.2); border-radius: 12px; padding: 0.8rem 1rem; backdrop-filter: blur(4px);">
                <div style="font-size: 0.75rem; color: #f9a8d4; text-transform: uppercase; letter-spacing: 0.5px;">🏷️ Marques</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: #fbcfe8;">{nb_marques}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        nb_regions = df[region_col].nunique() if region_col else "N/A"
        st.markdown(
            f"""
            <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 12px; padding: 0.8rem 1rem; backdrop-filter: blur(4px);">
                <div style="font-size: 0.75rem; color: #6ee7b7; text-transform: uppercase; letter-spacing: 0.5px;">🌍 Régions</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: #a7f3d0;">{nb_regions}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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
            fig.update_layout(title_font_color="#e2e8f0")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Colonne marque non trouvée")

    with col_b:
        if boite_col:
            fig = px.pie(
                df,
                names=boite_col,
                title="Répartition des boîtes",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig = apply_plotly_theme(fig)
            fig.update_traces(textinfo="percent+label", textposition="inside")
            fig.update_layout(title_font_color="#e2e8f0")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Colonne boîte non trouvée")

    if region_col:
        st.markdown("### 🗺️ Top 10 des régions")
        top_regions = df[region_col].value_counts().head(10).reset_index()
        top_regions.columns = ["Région", "Nombre"]
        fig = px.bar(
            top_regions,
            x="Région",
            y="Nombre",
            text="Nombre",
            title="",
            color_discrete_sequence=["#f59e0b"],
        )
        fig = apply_plotly_theme(fig)
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with st.expander("📋 Voir les données brutes", expanded=False):
        st.dataframe(df, use_container_width=True)


# ========================
# Configuration de la page
# ========================
st.set_page_config(page_title="Data App", page_icon="📊", layout="wide")

# CSS personnalisé pour un fond sans blanc
st.markdown(
    """
    <style>
    /* Fond général - dégradé sans blanc */
    .stApp {
        background: linear-gradient(145deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        color: #e2e8f0;
    }
    [data-testid="stAppViewContainer"] {
        background: transparent;
    }
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(30, 41, 59, 0.8);
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(148, 163, 184, 0.1);
    }
    [data-testid="stSidebar"] .css-1d391kg, 
    [data-testid="stSidebar"] .css-1v3fvcr {
        color: #e2e8f0;
    }
    [data-testid="stSidebar"] .stSelectbox label {
        color: #94a3b8;
    }
    /* Conteneurs métriques */
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.05) !important;
        backdrop-filter: blur(6px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 1rem;
    }
    /* Graphiques - pas de fond blanc */
    .stPlotlyChart {
        background: transparent !important;
        border-radius: 16px;
        backdrop-filter: blur(2px);
        padding: 0.5rem;
    }
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.05) !important;
        border-radius: 10px !important;
        font-weight: 600;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255,255,255,0.06);
        backdrop-filter: blur(4px);
    }
    .streamlit-expanderHeader:hover {
        background: rgba(255,255,255,0.1) !important;
    }
    .streamlit-expanderContent {
        background: rgba(255,255,255,0.03) !important;
        border-radius: 0 0 10px 10px;
        border: 1px solid rgba(255,255,255,0.05);
        border-top: none;
    }
    /* Séparateur */
    hr {
        margin: 1.8rem 0;
        border: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, #6366f1, #8b5cf6, transparent);
        opacity: 0.3;
    }
    /* Titres */
    h1, h2, h3, h4, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #f1f5f9 !important;
        font-family: 'Arial Black', sans-serif;
    }
    /* Métriques personnalisées */
    .stMetric label {
        color: #94a3b8 !important;
    }
    .stMetric div[data-testid="stMetricValue"] {
        color: #e2e8f0 !important;
    }
    /* Boutons */
    .stButton button {
        background: #6366f1;
        color: white;
        border-radius: 30px;
        border: none;
        padding: 0.5rem 1.8rem;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
        transition: all 0.2s;
    }
    .stButton button:hover {
        transform: scale(1.02);
        background: #4f46e5;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
    }
    .stDownloadButton button {
        background: #0f766e;
        color: white;
        border-radius: 30px;
        border: none;
        padding: 0.5rem 1.8rem;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(15, 118, 110, 0.3);
        transition: all 0.2s;
    }
    .stDownloadButton button:hover {
        transform: scale(1.02);
        background: #0d6b63;
        box-shadow: 0 6px 20px rgba(15, 118, 110, 0.5);
    }
    /* Dataframe */
    .dataframe {
        background: rgba(255,255,255,0.05) !important;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.06);
    }
    .dataframe th {
        background: rgba(99, 102, 241, 0.2) !important;
        color: #e2e8f0 !important;
    }
    .dataframe td {
        color: #cbd5e1 !important;
    }
    /* Info, warning, error */
    .stAlert {
        background: rgba(255,255,255,0.05) !important;
        backdrop-filter: blur(6px);
        border: 1px solid rgba(255,255,255,0.1);
        color: #e2e8f0;
    }
    .stAlert svg {
        fill: #e2e8f0 !important;
    }
    /* Radio buttons */
    .stRadio label {
        color: #e2e8f0 !important;
    }
    .stRadio div[role="radiogroup"] {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 0.3rem;
        backdrop-filter: blur(4px);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 DATA APPS")
st.markdown("---")

# === Chemins relatifs ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "data_collection.db")

# === Menu latéral ===
menu = st.sidebar.selectbox(
    "Navigation",
    [
        "Accueil",
        "Dashboard",
        "Téléchargement données brutes",
        "Formulaires d'évaluation",
    ],
)

# === PAGE ACCUEIL ===
if menu == "Accueil":
    st.header("🏠 Bienvenue dans votre application d'analyse de données")
    st.write(
        """
    Cette application permet de :
    - Visualiser des données nettoyées (Books to Scrape + Gaaraas)
    - Télécharger les données dans leurs états bruts (No-code)
    - Accéder aux formulaires d'évaluation
    """
    )
    st.image(
        "https://img.icons8.com/fluency/96/000000/data-configuration.png",
        width=80,
    )

# === PAGE DASHBOARD ===
elif menu == "Dashboard":
    st.header("📈 Dashboard des données nettoyées")

    if not os.path.exists(DB_PATH):
        st.error(
            f"❌ Base de données introuvable à {DB_PATH}. Vérifie que le fichier data_collection.db est dans le dossier data/."
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
            st.error(f"❌ Erreur lors de la lecture de la base : {e}")

# === PAGE TÉLÉCHARGEMENT ===
elif menu == "Téléchargement données brutes":
    st.header("📥 Téléchargement des données brutes (No-code)")
    st.write("Téléchargez les fichiers CSV bruts issus de Web Scraper :")

    col1, col2 = st.columns(2)
    books_csv = os.path.join(DATA_DIR, "books_brut.csv")
    with col1:
        if os.path.exists(books_csv):
            with open(books_csv, "rb") as f:
                st.download_button(
                    label="📚 Télécharger Books bruts",
                    data=f,
                    file_name="books_brut.csv",
                    mime="text/csv",
                )
        else:
            st.warning("Fichier books_brut.csv non trouvé dans data/.")

    cars_csv = os.path.join(DATA_DIR, "gaaraas_brut.csv")
    with col2:
        if os.path.exists(cars_csv):
            with open(cars_csv, "rb") as f:
                st.download_button(
                    label="🚗 Télécharger Gaaraas bruts",
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
        st.subheader("📋 Formulaire Kobo")
        st.link_button(
            "Remplir le formulaire Kobo",
            "https://ee.kobotoolbox.org/x/wjF8NPvg",
        )
    with col2:
        st.subheader("📋 Formulaire Google Forms")
        st.link_button(
            "Remplir le formulaire Google Forms",
            "https://docs.google.com/forms/d/e/1FAIpQLScK9rU2LxRYeGuR7Z6yW0aYgPIH7P3una4jg8G3pY3a8fccvw/viewform",
        )
