# app.py
import os
import sqlite3
import time

import pandas as pd
import plotly.express as px
import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Data App",
    page_icon="📊",
    layout="wide",
)

st.title("DATA APPS")
st.markdown("---")

# Chemin de la base de données
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data_collection.db")


def ensure_sqlite_tables(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            Titre TEXT,
            Prix TEXT,
            Disponibilite TEXT,
            Note TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cars (
            V1_Marque TEXT,
            V2_Modele TEXT,
            V3_Annee TEXT,
            V4_Prix TEXT,
            V5_Kilometrage TEXT,
            V6_Boite TEXT,
            V7_Region TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_books (
            source_url TEXT,
            pages_scraped TEXT,
            Titre TEXT,
            Prix TEXT,
            Disponibilite TEXT,
            Note TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_cars (
            source_url TEXT,
            pages_scraped TEXT,
            V1_Marque TEXT,
            V2_Modele TEXT,
            V3_Annee TEXT,
            V4_Prix TEXT,
            V5_Kilometrage TEXT,
            V6_Boite TEXT,
            V7_Region TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS generic_scraping (
            Texte TEXT,
            Lien TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_generic_scraping (
            source_url TEXT,
            pages_scraped TEXT,
            Texte TEXT,
            Lien TEXT
        )
        """
    )
    conn.commit()
    return True


def save_scraped_to_sqlite(conn, table_name, df):
    if df.empty:
        return
    df.to_sql(table_name, conn, if_exists="append", index=False)
    conn.commit()


# Menu
menu = st.sidebar.selectbox(
    "Navigation",
    [
        "Accueil",
        "Dashboard",
        "Téléchargement données brutes",
        "Scraping data",
        "Formulaires d'évaluation",
    ],
)

# Page Accueil
if menu == "Accueil":
    st.header("Bienvenue dans votre application d'analyse de données")
    st.write(
        """
    Cette application permet de :
        - Scraper des données sur plusieurs pages via Selenium
        - Télécharger les données brutes issues du scraping (non nettoyées)
        - Visualiser un dashboard des données nettoyées
        - Accéder aux formulaires d'évaluation
        """
    )

# Page Dashboard
elif menu == "Dashboard":
    st.header("📈 Dashboard des données nettoyées")

    try:
        with sqlite3.connect(DB_PATH) as conn:
            ensure_sqlite_tables(conn)

            choix = st.radio(
                "Choisir la source de données :",
                ["Livres (Books to Scrape)", "Voitures (Gaaraas)"],
                horizontal=True,
            )

            if choix == "Livres (Books to Scrape)":
                tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
                if "books" not in tables["name"].values:
                    st.error("La table 'books' n'existe pas dans la base de données.")
                else:
                    df = pd.read_sql("SELECT * FROM books", conn)
                    st.subheader(f"📚 {len(df)} livres récupérés")

                    price_col = next(
                        (c for c in ["prix", "V2_Prix", "Prix", "price"] if c in df.columns),
                        None,
                    )
                    rating_col = next(
                        (c for c in ["note", "V5_Note", "rating", "Note"] if c in df.columns),
                        None,
                    )
                    avail_col = next(
                        (
                            c
                            for c in [
                                "disponibilite",
                                "V3_Disponibilite",
                                "availability",
                                "Disponibilité",
                            ]
                            if c in df.columns
                        ),
                        None,
                    )

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Nombre total de livres", len(df))
                    with col2:
                        if price_col:
                            prix_numeriques = pd.to_numeric(df[price_col], errors="coerce")
                            st.metric("Prix moyen", f"{prix_numeriques.mean():.2f} £")
                        else:
                            st.metric("Prix moyen", "N/A")
                    with col3:
                        if price_col:
                            prix_numeriques = pd.to_numeric(df[price_col], errors="coerce")
                            st.metric("Prix minimum", f"{prix_numeriques.min():.2f} £")
                        else:
                            st.metric("Prix minimum", "N/A")
                    with col4:
                        if price_col:
                            prix_numeriques = pd.to_numeric(df[price_col], errors="coerce")
                            st.metric("Prix maximum", f"{prix_numeriques.max():.2f} £")
                        else:
                            st.metric("Prix maximum", "N/A")

                    st.markdown("---")

                    col_a, col_b = st.columns(2)
                    with col_a:
                        if price_col:
                            fig1 = px.histogram(df, x=price_col, nbins=30, title="Distribution des prix")
                            st.plotly_chart(fig1, use_container_width=True)
                        else:
                            st.info("Colonne prix non trouvée")

                    with col_b:
                        if rating_col:
                            rating_counts = df[rating_col].value_counts().reset_index()
                            rating_counts.columns = ["Note", "Nombre"]
                            fig2 = px.bar(rating_counts, x="Note", y="Nombre", title="Répartition des notes")
                            st.plotly_chart(fig2, use_container_width=True)
                        else:
                            st.info("Colonne note non trouvée")

                    if avail_col:
                        fig3 = px.pie(df, names=avail_col, title="Disponibilité des livres")
                        st.plotly_chart(fig3, use_container_width=True)

                    with st.expander("Voir les données"):
                        st.dataframe(df, use_container_width=True)

            else:
                tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
                if "cars" not in tables["name"].values:
                    st.error("La table 'cars' n'existe pas dans la base de données.")
                else:
                    df = pd.read_sql("SELECT * FROM cars", conn)
                    st.subheader(f"🚗 {len(df)} voitures récupérées")

                    marque_col = next((c for c in ["marque", "V1_Marque", "Marque"] if c in df.columns), None)
                    prix_col = next((c for c in ["prix", "V4_Prix", "Prix"] if c in df.columns), None)
                    region_col = next((c for c in ["region", "V7_Region", "Région"] if c in df.columns), None)
                    boite_col = next((c for c in ["boite", "V6_Boite", "Boite"] if c in df.columns), None)

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Nombre total de voitures", len(df))
                    with col2:
                        if marque_col:
                            st.metric("Nombre de marques", df[marque_col].nunique())
                        else:
                            st.metric("Nombre de marques", "N/A")
                    with col3:
                        if region_col:
                            st.metric("Nombre de régions", df[region_col].nunique())
                        else:
                            st.metric("Nombre de régions", "N/A")

                    st.markdown("---")

                    col_a, col_b = st.columns(2)
                    with col_a:
                        if marque_col:
                            top_marques = df[marque_col].value_counts().head(10).reset_index()
                            top_marques.columns = ["Marque", "Nombre"]
                            fig1 = px.bar(top_marques, x="Marque", y="Nombre", title="Top 10 des marques")
                            st.plotly_chart(fig1, use_container_width=True)
                        else:
                            st.info("Colonne marque non trouvée")

                    with col_b:
                        if boite_col:
                            fig2 = px.pie(df, names=boite_col, title="Répartition des boîtes de vitesses")
                            st.plotly_chart(fig2, use_container_width=True)
                        else:
                            st.info("Colonne boîte non trouvée")

                    if region_col:
                        top_regions = df[region_col].value_counts().head(10).reset_index()
                        top_regions.columns = ["Région", "Nombre"]
                        fig3 = px.bar(top_regions, x="Région", y="Nombre", title="Top 10 des régions")
                        st.plotly_chart(fig3, use_container_width=True)

                    with st.expander("Voir les données"):
                        st.dataframe(df, use_container_width=True)

    except FileNotFoundError:
        st.error(f"Fichier de base de données introuvable : {DB_PATH}")
        st.info("Vérifie que le fichier data_collection.db existe bien à cet emplacement.")
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")

# Page Téléchargement
elif menu == "Téléchargement données brutes":
    st.header("📥 Téléchargement des données brutes")
    st.write("Télécharge les fichiers bruts stockés dans le dossier data.")

    data_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)

    book_files = [
        os.path.join(data_dir, "books_brut.csv"),
        os.path.join(data_dir,"books_brut.csv"),
    ]
    car_files = [
        os.path.join(data_dir, "gaaraas_brut.csv"),
        os.path.join(data_dir, "gaaraas_brut.csv"),
    ]

    for file_path in book_files:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                st.download_button(
                    label=f"Télécharger {os.path.basename(file_path)}",
                    data=f,
                    file_name=os.path.basename(file_path),
                    mime="text/csv",
                )
            break

    for file_path in car_files:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                st.download_button(
                    label=f"Télécharger {os.path.basename(file_path)}",
                    data=f,
                    file_name=os.path.basename(file_path),
                    mime="text/csv",
                )
            break

    if not any(os.path.exists(p) for p in book_files + car_files):
        st.info("Aucun fichier brut n'a encore été enregistré dans le dossier data.")

# Page Scraping data
elif menu == "Scraping data":
    st.header("🔍 Scraping multi-pages avec Selenium")
    st.write("Colle un lien et lance le scraping sur plusieurs pages. Les données brutes et nettoyées seront stockées dans la base SQLite.")

    url = st.text_input("URL à scraper", value="", placeholder="https://...")
    nb_pages = st.number_input("Nombre de pages", min_value=1, max_value=5, value=1)

    if st.button("Lancer le scraping", type="primary"):
        if not url:
            st.warning("Veuillez entrer une URL.")
        else:
            with st.spinner("Scraping en cours... Veuillez patienter"):
                try:
                    from selenium import webdriver
                    from selenium.webdriver.chrome.options import Options
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.chrome.service import Service
                    from webdriver_manager.chrome import ChromeDriverManager
                    import re

                    chrome_options = Options()
                    chrome_options.add_argument("--headless")
                    chrome_options.add_argument("--no-sandbox")
                    chrome_options.add_argument("--disable-dev-shm-usage")
                    chrome_options.add_argument("--window-size=1920,1080")
                    chrome_options.add_argument("--disable-gpu")

                    driver = webdriver.Chrome(
                        service=Service(ChromeDriverManager().install()),
                        options=chrome_options,
                    )

                    data = []

                    if "books.toscrape.com" in url:
                        for page in range(1, nb_pages + 1):
                            page_url = f"https://books.toscrape.com/catalogue/page-{page}.html"
                            driver.get(page_url)
                            time.sleep(1.5)
                            books = driver.find_elements(By.CSS_SELECTOR, "article.product_pod")
                            for book in books:
                                title = book.find_element(By.CSS_SELECTOR, "h3 a").get_attribute("title")
                                price = book.find_element(By.CLASS_NAME, "price_color").text.replace("£", "").strip()
                                availability = book.find_element(By.CLASS_NAME, "availability").text.strip()
                                rating = book.find_element(By.CLASS_NAME, "star-rating").get_attribute("class")
                                rating = rating.replace("star-rating", "").strip()
                                data.append({
                                    "Titre": title,
                                    "Prix": price,
                                    "Disponibilité": availability,
                                    "Note": rating,
                                })
                    elif "gaaraas.com" in url:
                        for page in range(1, nb_pages + 1):
                            page_url = f"https://www.gaaraas.com/petites-annonces-voitures?page={page}"
                            driver.get(page_url)
                            time.sleep(2)
                            texte = driver.find_element(By.TAG_NAME, "body").text
                            blocs = re.split(r"\n(?=\d+\n\d{4}\s)", texte)
                            for bloc in blocs:
                                try:
                                    lignes = [l.strip() for l in bloc.split("\n") if l.strip()]
                                    if len(lignes) < 6:
                                        continue
                                    titre_line = None
                                    for l in lignes:
                                        if re.match(r"^\d{4}\s+\w+", l):
                                            titre_line = l
                                            break
                                    if not titre_line:
                                        continue
                                    parts = titre_line.split(" ", 2)
                                    annee = parts[0]
                                    marque = parts[1] if len(parts) > 1 else ""
                                    modele = parts[2] if len(parts) > 2 else ""
                                    region = ""
                                    for l in lignes:
                                        if (
                                            l not in ["PRIX", "KILOMÉTRAGE"]
                                            and not l.startswith("CFA")
                                            and not l.startswith("Négociable")
                                            and "KM" not in l
                                            and l not in ["Manuelle", "Automatique"]
                                            and not l.startswith("Publié")
                                            and not re.match(r"^\d+$", l)
                                            and l != titre_line
                                        ):
                                            region = l
                                            break
                                    prix = "Négociable"
                                    for i, l in enumerate(lignes):
                                        if "PRIX" in l and i + 1 < len(lignes):
                                            prix = lignes[i + 1].replace("CFA", "").replace(" ", "").strip()
                                            break
                                    kilometrage = "N/A"
                                    for i, l in enumerate(lignes):
                                        if "KILOMÉTRAGE" in l and i + 1 < len(lignes):
                                            kilometrage = lignes[i + 1].replace("KM", "").replace(" ", "").strip()
                                            break
                                    boite = ""
                                    for l in lignes:
                                        if l in ["Manuelle", "Automatique"]:
                                            boite = l
                                            break
                                    data.append({
                                        "V1_Marque": marque,
                                        "V2_Modele": modele,
                                        "V3_Annee": annee,
                                        "V4_Prix": prix,
                                        "V5_Kilometrage": kilometrage,
                                        "V6_Boite": boite,
                                        "V7_Region": region,
                                    })
                                except Exception:
                                    continue
                    else:
                        driver.get(url)
                        time.sleep(2)
                        links = driver.find_elements(By.TAG_NAME, "a")
                        for link in links[:100]:
                            text = link.text.strip()
                            href = link.get_attribute("href")
                            if text and href:
                                data.append({"Texte": text, "Lien": href})

                    driver.quit()

                    if data:
                        df_scraped = pd.DataFrame(data)
                        st.success(f"✅ {len(df_scraped)} éléments récupérés avec Selenium")
                        st.dataframe(df_scraped, use_container_width=True)

                        with sqlite3.connect(DB_PATH) as conn:
                            ensure_sqlite_tables(conn)
                            if "books.toscrape.com" in url:
                                books_df = df_scraped.rename(columns={"Disponibilité": "Disponibilite"})
                                books_df = books_df[["Titre", "Prix", "Disponibilite", "Note"]]
                                books_df = books_df.copy()
                                save_scraped_to_sqlite(conn, "books", books_df)

                                raw_books_df = books_df.copy()
                                raw_books_df.insert(0, "source_url", url)
                                raw_books_df.insert(1, "pages_scraped", str(nb_pages))
                                save_scraped_to_sqlite(conn, "raw_books", raw_books_df)
                                st.info("Les données livres nettoyées et brutes ont été enregistrées dans la base SQLite data_collection.db")
                            elif "gaaraas.com" in url:
                                cars_df = df_scraped.copy()
                                save_scraped_to_sqlite(conn, "cars", cars_df)

                                raw_cars_df = cars_df.copy()
                                raw_cars_df.insert(0, "source_url", url)
                                raw_cars_df.insert(1, "pages_scraped", str(nb_pages))
                                save_scraped_to_sqlite(conn, "raw_cars", raw_cars_df)
                                st.info("Les données voitures nettoyées et brutes ont été enregistrées dans la base SQLite data_collection.db")
                            else:
                                generic_df = df_scraped.copy()
                                save_scraped_to_sqlite(conn, "generic_scraping", generic_df)

                                raw_generic_df = generic_df.copy()
                                raw_generic_df.insert(0, "source_url", url)
                                raw_generic_df.insert(1, "pages_scraped", str(nb_pages))
                                save_scraped_to_sqlite(conn, "raw_generic_scraping", raw_generic_df)
                                st.info("Les données génériques brutes et nettoyées ont été enregistrées dans la base SQLite data_collection.db")

                        csv = df_scraped.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            label="📥 Télécharger les données du scraping",
                            data=csv,
                            file_name="scraping_selenium.csv",
                            mime="text/csv",
                        )
                    else:
                        st.warning("Aucune donnée trouvée.")
                except ImportError:
                    st.error(
                        "Selenium ou webdriver-manager n'est pas installé.\n\n"
                        "Installe-les avec :\n"
                        "`pip install selenium webdriver-manager`"
                    )
                except Exception as e:
                    st.error(f"Erreur Selenium : {e}")

# Page Formulaires
elif menu == "Formulaires d'évaluation":
    st.header("Formulaires d'évaluation de l'application")
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
            "https://docs.google.com/forms/d/e/1FAIpQLScK9rU2LxRYeGuR7Z6yW0aYgPIH7P3una4jg8G3pY3a8fccvw/viewform?usp=header",
        )
