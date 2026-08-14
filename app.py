import os
import time
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ---------------------------
#  utilitaires
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
# Configuration Headless(Selenium)
# ---------------------------

def create_driver():
    """Chrome headless optimisé pour Streamlit Cloud"""
    options = Options()
    
    # Options essentielles pour Streamlit Cloud
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--single-process")          # important sur Streamlit Cloud
    options.add_argument("--disable-extensions")
    options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Chemin possible de Chrome/Chromium sur Streamlit Cloud
    chrome_paths = [
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable"
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            options.binary_location = path
            break

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        # Fallback : essayer sans webdriver-manager
        st.warning(f"webdriver-manager a échoué, tentative alternative... ({e})")
        driver = webdriver.Chrome(options=options)
        return driver


# ---------------------------
# SCRAPING Selenium - Books to Scrape
# ---------------------------

def scrape_books_selenium(start_url: str, max_pages: int = 3):
    """Scrape multi-pages uniquement avec Selenium"""
    driver = None
    all_books = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        driver = create_driver()
        current_url = start_url
        page = 1

        while current_url and page <= max_pages:
            status_text.info(f"📄 Page {page}/{max_pages} en cours de scraping (Selenium)...")
            
            driver.get(current_url)
            time.sleep(1.5)  # lle temps de charger

            # Attendre que les livres apparaissent
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article.product_pod"))
            )

            books = driver.find_elements(By.CSS_SELECTOR, "article.product_pod")

            for book in books:
                try:
                    title = book.find_element(By.CSS_SELECTOR, "h3 a").get_attribute("title")
                except:
                    title = "N/A"

                try:
                    price = book.find_element(By.CSS_SELECTOR, "p.price_color").text
                except:
                    price = "N/A"

                try:
                    rating_elem = book.find_element(By.CSS_SELECTOR, "p.star-rating")
                    rating = rating_elem.get_attribute("class").split()[-1]
                except:
                    rating = "N/A"

                try:
                    availability = book.find_element(By.CSS_SELECTOR, "p.instock.availability").text.strip()
                except:
                    availability = "N/A"

                try:
                    link = book.find_element(By.CSS_SELECTOR, "h3 a").get_attribute("href")
                except:
                    link = ""

                all_books.append({
                    "Titre": title,
                    "Prix": price,
                    "Note": rating,
                    "Disponibilité": availability,
                    "Lien": link,
                    "Page": page
                })

            # Pagination
            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, "li.next a")
                current_url = next_btn.get_attribute("href")
                page += 1
                progress_bar.progress(min(page / max_pages, 1.0))
            except:
                break  # plus de page suivante

        progress_bar.progress(1.0)
        status_text.success(f" Scraping terminé  — {len(all_books)} livres récupérés")

    except Exception as e:
        st.error(f"Erreur Selenium : {e}")
    finally:
        if driver:
            driver.quit()

    return pd.DataFrame(all_books)


# ---------------------------
# SCRAPING  avec Selenium
# ---------------------------

def scrape_generic_selenium(url: str, max_items: int = 30):
    """Scraper générique uniquement avec Selenium"""
    driver = None
    data = []

    try:
        driver = create_driver()
        driver.get(url)
        time.sleep(2)

        # Extraire les liens
        links = driver.find_elements(By.TAG_NAME, "a")[:max_items]

        for link in links:
            try:
                text = link.text.strip()
                href = link.get_attribute("href")
                if text and len(text) > 4 and href:
                    data.append({
                        "Texte": text[:180],
                        "Lien": href,
                        "Source": url
                    })
            except:
                continue

        # Si peu de résultats, prendre aussi les titres
        if len(data) < 5:
            for tag in ["h1", "h2", "h3"]:
                elements = driver.find_elements(By.TAG_NAME, tag)
                for el in elements[:15]:
                    text = el.text.strip()
                    if text:
                        data.append({
                            "Texte": text[:180],
                            "Lien": url,
                            "Source": url
                        })

    except Exception as e:
        st.error(f"Erreur Selenium : {e}")
    finally:
        if driver:
            driver.quit()

    return pd.DataFrame(data)


# ---------------------------
# Dashboard Livres
# ---------------------------

def build_books_dashboard(df):
    if df.empty:
        st.warning("Aucune donnée de livres trouvée.")
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

    availability_col = resolve_column(df, ["V3_Disponibilite", "disponibilite", "availability", "Disponibilité"])
    if availability_col:
        st.markdown("#### Disponibilité des livres")
        fig = px.pie(
            df,
            names=availability_col,
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig = apply_plotly_theme(fig)
        fig.update_traces(textinfo="percent+label", textposition="inside")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with st.expander("Voir les données "):
        st.dataframe(df, use_container_width=True)


# ---------------------------
# Dashboard Voitures
# ---------------------------

def build_cars_dashboard(df):
    if df.empty:
        st.warning("Aucune donnée de voitures trouvée.")
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

    if marque_col:
        df = df.copy()
        df["marque_clean"] = (
            df[marque_col]
            .astype(str)
            .str.replace(r"(?i)^détails\s*", "", regex=True)
            .str.strip()
        )
        marque_col_clean = "marque_clean"
    else:
        marque_col_clean = None

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
        if marque_col_clean:
            top = df[marque_col_clean].value_counts().head(10).reset_index()
            top.columns = ["Marque", "Nombre"]
            fig1 = px.bar(
                top, x="Nombre", y="Marque", text="Nombre",
                title="Top 10 des marques", orientation="h",
                color_discrete_sequence=["#0f766e"]
            )
            fig1 = apply_plotly_theme(fig1)
            fig1.update_traces(textposition="outside")
            st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

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
                avg_price, x="Marque", y="Prix moyen", text="Prix moyen",
                title="Top 10 marques par prix moyen",
                color_discrete_sequence=["#f59e0b"]
            )
            fig2 = apply_plotly_theme(fig2)
            fig2.update_traces(texttemplate='%{text:.0f} F cfa', textposition="outside")
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    with col_b:
        if boite_col:
            fig = px.pie(
                df, names=boite_col, title="Répartition des boîtes",
                hole=0.45, color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig = apply_plotly_theme(fig)
            fig.update_traces(textinfo="percent+label", textposition="inside")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    if region_col:
        st.markdown("#### Top 10 des régions")
        top = df[region_col].value_counts().head(10).reset_index()
        top.columns = ["Région", "Nombre"]
        fig = px.bar(top, x="Région", y="Nombre", text="Nombre", color_discrete_sequence=["#f59e0b"])
        fig = apply_plotly_theme(fig)
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with st.expander("Voir les données"):
        st.dataframe(df, use_container_width=True)


# ---------------------------
# Configuration page
# ---------------------------

st.set_page_config(
    page_title="Collecte & Analyse",
    page_icon="⌗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS (identique)
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
.stApp { background-color: #0f172a !important; font-family: 'Inter', system-ui, sans-serif; color: #e2e8f0; }
[data-testid="stAppViewContainer"] > .main { background-color: #0f172a; }
[data-testid="stSidebar"] { background-color: #1e293b !important; }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stRadio label {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(148,163,184,0.15) !important;
    border-radius: 12px !important;
    padding: 0.85rem 1.1rem !important;
    margin-bottom: 0.4rem !important;
}
.metric-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(148,163,184,0.15);
    border-radius: 14px;
    padding: 1.1rem 1.2rem;
}
.metric-label { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 0.72rem; font-weight: 600; color: #94a3b8; }
.metric-value { font-size: 1.75rem; font-weight: 700; color: #f1f5f9; }
.section-header {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(148,163,184,0.12);
    border-left: 5px solid #6366f1;
    border-radius: 12px;
    padding: 1.1rem 1.4rem;
    margin-bottom: 1.5rem;
}
.section-header h3 { margin: 0 0 0.25rem 0 !important; color: #f1f5f9 !important; font-size: 1.25rem !important; }
.section-header p { margin: 0 !important; color: #94a3b8 !important; }
.hero-card, .section-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(148,163,184,0.12);
    border-radius: 16px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.4rem;
}
.stDownloadButton button, .stButton button {
    background: #2563eb !important;
    color: white !important;
    border-radius: 999px !important;
    font-weight: 600 !important;
}
h1, h2, h3 { color: #f1f5f9 !important; }
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
    ["Accueil", "Scraping", "Dashboard", "Données brutes", "Formulaires"],
    format_func=lambda x: {
        "Accueil": "🏠  Accueil",
        "Scraping": "🕸️  Scraping (Selenium)",
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
        <h1>Bienvenue - Welcome - Bienvenido</h1>
        <p>Application de collecte et d'analyse de données issues de differentes methodes de recuperation de donnees.</p>
    </div>
    <div class="section-card">
        <h2>Fonctionnalités</h2>
        <ul>
            <li>🕸️ Scraping multi-pages </li>
            <li>📈 Dashboard des données nettoyées</li>
            <li>📥 Téléchargement des données brutes</li>
            <li>📝 Formulaires d'évaluation dde notre application</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


elif menu == "Scraping":
    st.header("🕸️ Scraping avec Selenium")
    st.markdown("**Tout le scraping se fait exclusivement avec Selenium** .")

    scrape_type = st.radio(
        "Type de scraping",
        ["Books to Scrape (recommandé)", "URL personnalisée"],
        horizontal=True
    )

    if scrape_type.startswith("Books"):
        st.info("Site d'entraînement idéal : [books.toscrape.com](https://books.toscrape.com)")

        col1, col2 = st.columns([3, 1])
        with col1:
            start_url = st.text_input(
                "URL de départ",
                value="https://books.toscrape.com/catalogue/page-1.html"
            )
        with col2:
            max_pages = st.number_input("Nombre de pages", min_value=1, max_value=20, value=3)

        if st.button(" Lancer le scraping Selenium", type="primary"):
            with st.spinner("Selenium en cours d'exécution..."):
                df_scraped = scrape_books_selenium(start_url, max_pages)

            if not df_scraped.empty:
                st.success(f"**{len(df_scraped)} livres** récupérés avec Selenium")
                st.dataframe(df_scraped, use_container_width=True)

                csv = df_scraped.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Télécharger les données brutes scrapées (CSV)",
                    data=csv,
                    file_name="books_selenium.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Aucune donnée récupérée.")

    else:
        custom_url = st.text_input("Colle l'URL à scraper", placeholder="https://exemple.com")
        max_items = st.slider("Nombre max d'éléments", 10, 100, 30)

        if st.button(" Lancer le scraping générique (Selenium)", type="primary"):
            if not custom_url:
                st.error("Merci d'entrer une URL.")
            else:
                with st.spinner("Selenium en cours..."):
                    df_scraped = scrape_generic_selenium(custom_url, max_items)

                if not df_scraped.empty:
                    st.success(f"**{len(df_scraped)} éléments** récupérés")
                    st.dataframe(df_scraped, use_container_width=True)

                    csv = df_scraped.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "📥 Télécharger (CSV)",
                        data=csv,
                        file_name="scraping_selenium.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("Aucune donnée exploitable trouvée.")


elif menu == "Dashboard":
    st.header("Dashboard des données")

    if not os.path.exists(DB_PATH):
        st.error(f"Base de données introuvable : `{DB_PATH}`")
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
    st.write("Fichiers issus du scraping (no-code)")

    col1, col2 = st.columns(2)

    with col1:
        path = os.path.join(DATA_DIR, "books_brut.csv")
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = f.read()
            st.download_button(
                "📚 Books bruts",
                data=data,
                file_name="books_brut.csv",
                mime="text/csv"
            )
        else:
            st.warning("Fichier `books_brut.csv` introuvable.")

    with col2:
        path = os.path.join(DATA_DIR, "gaaraas_brut.csv")
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = f.read()
            st.download_button(
                "🚗 Gaaraas bruts",
                data=data,
                file_name="gaaraas_brut.csv",
                mime="text/csv"
            )
        else:
            st.warning("Fichier `gaaraas_brut.csv` introuvable.")


elif menu == "Formulaires":
    st.header("Ton avis compte")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Formulaire Kobotools 📋")
        st.link_button("Ouvrir Kobo", "https://ee.kobotoolbox.org/x/wjF8NPvg")

    with col2:
        st.subheader("Formulaire Google Forms")
        st.link_button(
            "Ouvrir Google Forms 📋",
            "https://docs.google.com/forms/d/e/1FAIpQLScK9rU2LxRYeGuR7Z6yW0aYgPIH7P3una4jg8G3pY3a8fccvw/viewform"
        )
