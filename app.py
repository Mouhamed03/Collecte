import os
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

# ========================
# Configuration de la page
# ========================
st.set_page_config(
    page_title="Data Apps | Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================
# CSS PERSONNALISÉ (Design premium)
# ========================
st.markdown("""
<style>
/* ===== GLOBAL ===== */
.stApp {
    background: linear-gradient(160deg, #f1f5f9 0%, #e0e7ff 45%, #f8fafc 100%);
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}

[data-testid="stAppViewContainer"] {
    background: transparent;
}

/* ===== SIDEBAR ===== */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    border-right: 1px solid #334155;
}

[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}

[data-testid="stSidebar"] .stSelectbox label {
    color: #94a3b8 !important;
    font-weight: 500;
}

[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background-color: #1e293b !important;
    border: 1px solid #475569 !important;
    border-radius: 10px !important;
}

/* ===== TITRES ===== */
h1, h2, h3 {
    color: #0f172a !important;
    font-weight: 700 !important;
    letter-spacing: -0.3px;
}

/* ===== CARTES MÉTRIQUES ===== */
.metric-card {
    background: white;
    border-radius: 16px;
    padding: 1.25rem 1.4rem;
    box-shadow: 0 4px 20px rgba(15, 23, 42, 0.06);
    border: 1px solid #e2e8f0;
    transition: all 0.25s ease;
    height: 100%;
}

.metric-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 25px rgba(15, 23, 42, 0.1);
}

.metric-label {
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 0.35rem;
}

.metric-value {
    font-size: 1.85rem;
    font-weight: 800;
    line-height: 1.1;
}

/* ===== HEADER SECTION ===== */
.header-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    border-radius: 18px;
    padding: 1.4rem 1.8rem;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 15px rgba(15, 23, 42, 0.04);
    margin-bottom: 1.8rem;
}

/* ===== GRAPHIQUES ===== */
.stPlotlyChart {
    background: white;
    border-radius: 16px;
    padding: 0.8rem;
    box-shadow: 0 4px 20px rgba(15, 23, 42, 0.05);
    border: 1px solid #e2e8f0;
}

/* ===== EXPANDER ===== */
.streamlit-expanderHeader {
    background: white !important;
    border-radius: 12px !important;
    border: 1px solid #e2e8f0 !important;
    font-weight: 600 !important;
    color: #1e293b !important;
}

/* ===== BOUTONS ===== */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.55rem 1.6rem !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 18px rgba(99, 102, 241, 0.4) !important;
}

.stDownloadButton > button {
    background: linear-gradient(135deg, #0f766e, #0d9488) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
}

/* ===== RADIO ===== */
div[role="radiogroup"] label {
    background: white;
    border-radius: 10px;
    padding: 0.4rem 1rem;
    border: 1px solid #e2e8f0;
    margin-right: 0.5rem;
}

/* ===== SÉPARATEUR ===== */
hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, #cbd5e1, transparent);
    margin: 2rem 0;
}

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar {
    width: 8px;
}
::-webkit-scrollbar-track {
    background: #f1f5f9;
}
::-webkit-scrollbar-thumb {
    background: #94a3b8;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)


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
        margin=dict(l=20, r=20, t=55, b=20),
        font=dict(family="Inter, Arial", size=13, color="#334155"),
        title=dict(
            font=dict(size=16, family="Inter, Arial", color="#0f172a", weight="bold"),
            x=0.02,
            xanchor="left"
        ),
        legend=dict(
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#e2e8f0",
            borderwidth=1,
            font=dict(size=12)
        ),
        xaxis=dict(showgrid=True, gridcolor="#f1f5f9", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9", zeroline=False),
    )
    fig.update_traces(marker_line_color="#ffffff", marker_line_width=1.2)
    return fig


def build_books_dashboard(conn):
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
    if "books" not in tables["name"].values:
        st.error("❌ La table 'books' n'existe pas dans la base de données.")
        return

    df = pd.read_sql("SELECT * FROM books", conn)

    # Header
    st.markdown(f"""
    <div class="header-card">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="background: #eef2ff; width: 52px; height: 52px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 1.6rem;">
                📚
            </div>
            <div>
                <h3 style="margin: 0; color: #0f172a; font-size: 1.45rem;">{len(df)} livres récupérés</h3>
                <p style="margin: 0.15rem 0 0 0; color: #64748b; font-size: 0.95rem;">
                    Visualisation des prix, notes et disponibilité • Books to Scrape
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    price_col = resolve_column(df, ["V2_Prix", "prix", "price"])
    if price_col:
        df["prix_clean"] = pd.to_numeric(df[price_col], errors="coerce")
        prix_clean = df["prix_clean"]
    else:
        prix_clean = pd.Series([pd.NA] * len(df), dtype="float64")

    # ===== MÉTRIQUES =====
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label" style="color: #3b82f6;">📦 Total</div>
            <div class="metric-value" style="color: #1e40af;">{len(df)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        avg_price = f"{prix_clean.mean():.2f} £" if price_col else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label" style="color: #10b981;">💰 Prix moyen</div>
            <div class="metric-value" style="color: #047857;">{avg_price}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        min_price = f"{prix_clean.min():.2f} £" if price_col else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label" style="color: #f59e0b;">⬇️ Prix min</div>
            <div class="metric-value" style="color: #b45309;">{min_price}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        max_price = f"{prix_clean.max():.2f} £" if price_col else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label" style="color: #ef4444;">⬆️ Prix max</div>
            <div class="metric-value" style="color: #b91c1c;">{max_price}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ===== GRAPHIQUES =====
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
            fig.update_traces(textposition="outside", textfont_size=12)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Disponibilité
    availability_col = resolve_column(df, ["V3_Disponibilite", "disponibilite", "availability"])
    if availability_col:
        st.markdown("### 📊 Disponibilité des livres")
        fig = px.pie(
            df,
            names=availability_col,
            hole=0.48,
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig = apply_plotly_theme(fig)
        fig.update_traces(textinfo="percent+label", textposition="inside", textfont_size=13)
        fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with st.expander("📋 Voir les données brutes", expanded=False):
        st.dataframe(df, use_container_width=True, height=400)


def build_cars_dashboard(conn):
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
    if "cars" not in tables["name"].values:
        st.error("❌ La table 'cars' n'existe pas dans la base de données.")
        return

    df = pd.read_sql("SELECT * FROM cars", conn)

    # Header
    st.markdown(f"""
    <div class="header-card">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="background: #ecfdf5; width: 52px; height: 52px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 1.6rem;">
                🚗
            </div>
            <div>
                <h3 style="margin: 0; color: #0f172a; font-size: 1.45rem;">{len(df)} voitures récupérées</h3>
                <p style="margin: 0.15rem 0 0 0; color: #64748b; font-size: 0.95rem;">
                    Marques, boîtes de vitesses et régions • Gaaraas
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    marque_col = resolve_column(df, ["marque", "V1_Marque", "Marque", "schema_brand"])
    region_col = resolve_column(df, ["region", "V7_Region", "Région", "location"])
    boite_col = resolve_column(df, ["boite", "V6_Boite", "Boite", "numberOfDoors"])

    # ===== MÉTRIQUES =====
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label" style="color: #3b82f6;">🚘 Total</div>
            <div class="metric-value" style="color: #1e40af;">{len(df)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        nb_marques = df[marque_col].nunique() if marque_col else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label" style="color: #ec4899;">🏷️ Marques</div>
            <div class="metric-value" style="color: #be185d;">{nb_marques}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        nb_regions = df[region_col].nunique() if region_col else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label" style="color: #10b981;">🌍 Régions</div>
            <div class="metric-value" style="color: #047857;">{nb_regions}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ===== GRAPHIQUES =====
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
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Colonne marque non trouvée")

    with col_b:
        if boite_col:
            fig = px.pie(
                df,
                names=boite_col,
                title="Répartition des boîtes",
                hole=0.48,
                color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig = apply_plotly_theme(fig)
            fig.update_traces(textinfo="percent+label", textposition="inside")
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
            color_discrete_sequence=["#f59e0b"],
        )
        fig = apply_plotly_theme(fig)
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with st.expander("📋 Voir les données brutes", expanded=False):
        st.dataframe(df, use_container_width=True, height=400)


# ========================
# APPLICATION PRINCIPALE
# ========================
st.title("📊 DATA APPS")
st.caption("Plateforme d'analyse et de visualisation de données scrapées")

# Chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "data_collection.db")

# Menu latéral
menu = st.sidebar.selectbox(
    "Navigation",
    ["Accueil", "Dashboard", "Téléchargement données brutes", "Formulaires d'évaluation"],
    index=1  # Dashboard par défaut
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="padding: 0.5rem 0.8rem; background: #1e293b; border-radius: 10px; font-size: 0.85rem; color: #94a3b8;">
    <strong style="color: #e2e8f0;">Astuce</strong><br>
    Utilisez le menu pour naviguer entre les sections.
</div>
""", unsafe_allow_html=True)

# === PAGE ACCUEIL ===
if menu == "Accueil":
    st.header("🏠 Bienvenue")
    st.markdown("""
    Cette application vous permet de :
    - **Visualiser** les données nettoyées (Books to Scrape + Gaaraas)
    - **Télécharger** les fichiers bruts (No-code)
    - **Évaluer** l'application via les formulaires
    """)
    
    st.image("https://img.icons8.com/fluency/96/000000/data-configuration.png", width=90)

# === PAGE DASHBOARD ===
elif menu == "Dashboard":
    st.header("📈 Dashboard des données nettoyées")
    
    if not os.path.exists(DB_PATH):
        st.error(f"❌ Base de données introuvable à `{DB_PATH}`.\n\nVérifie que le fichier `data_collection.db` est bien dans le dossier `data/`.")
    else:
        try:
            conn = sqlite3.connect(DB_PATH)
            
            choix = st.radio(
                "Choisir la source de données :",
                ["Livres (Books to Scrape)", "Voitures (Gaaraas)"],
                horizontal=True,
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if choix == "Livres (Books to Scrape)":
                build_books_dashboard(conn)
            else:
                build_cars_dashboard(conn)
                
            conn.close()
        except Exception as e:
            st.error(f"❌ Erreur lors de la lecture de la base : {e}")

# === PAGE TÉLÉCHARGEMENT ===
elif menu == "Téléchargement données brutes":
    st.header("📥 Téléchargement des données brutes")
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
                    use_container_width=True
                )
        else:
            st.warning("Fichier `books_brut.csv` non trouvé.")

    cars_csv = os.path.join(DATA_DIR, "gaaraas_brut.csv")
    with col2:
        if os.path.exists(cars_csv):
            with open(cars_csv, "rb") as f:
                st.download_button(
                    label="🚗 Télécharger Gaaraas bruts",
                    data=f,
                    file_name="gaaraas_brut.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.warning("Fichier `gaaraas_brut.csv` non trouvé.")

# === PAGE FORMULAIRES ===
elif menu == "Formulaires d'évaluation":
    st.header("📝 Formulaires d'évaluation")
    st.write("Votre avis nous aide à améliorer l'application.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Formulaire Kobo")
        st.link_button("Remplir le formulaire Kobo", "https://ee.kobotoolbox.org/x/wjF8NPvg", use_container_width=True)
    
    with col2:
        st.subheader("📋 Formulaire Google Forms")
        st.link_button(
            "Remplir le formulaire Google Forms",
            "https://docs.google.com/forms/d/e/1FAIpQLScK9rU2LxRYeGuR7Z6yW0aYgPIH7P3una4jg8G3pY3a8fccvw/viewform",
            use_container_width=True
        )
