# app.py
import json
import os
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

# Chemin du fichier JSON de données
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "data_collection.json")
if not os.path.exists(JSON_PATH):
    JSON_PATH = os.path.join(BASE_DIR, "data", "data_collection.json")


def load_json_data():
    if not os.path.exists(JSON_PATH):
        return {"books": [], "cars": [], "generic_scraping": []}
    with open(JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_json_data(data):
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def append_json_table(table_name, records):
    if not records:
        return
    data = load_json_data()
    data.setdefault(table_name, [])
    data[table_name].extend(records)
    save_json_data(data)


def get_dataframe(table_name):
    data = load_json_data()
    return pd.DataFrame(data.get(table_name, []))


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
        books_df = get_dataframe("books")
        cars_df = get_dataframe("cars")

        choix = st.radio(
            "Choisir la source de données :",
            ["Livres (Books to Scrape)", "Voitures (Gaaraas)"],
            horizontal=True,
        )

        if choix == "Livres (Books to Scrape)":
            if books_df.empty:
                st.error("Aucune donnée de livres n'a été trouvée dans le fichier JSON.")
            else:
                st.subheader(f"📚 {len(books_df)} livres récupérés")

                price_col = next(
                    (c for c in ["prix", "V2_Prix", "Prix", "price"] if c in books_df.columns),
                    None,
                )
                rating_col = next(
                    (c for c in ["note", "V5_Note", "rating", "Note"] if c in books_df.columns),
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
                        if c in books_df.columns
                    ),
                    None,
                )

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Nombre total de livres", len(books_df))
                with col2:
                    if price_col:
                        prix_numeriques = pd.to_numeric(books_df[price_col], errors="coerce")
                        st.metric("Prix moyen", f"{prix_numeriques.mean():.2f} £")
                    else:
                        st.metric("Prix moyen", "N/A")
                with col3:
                    if price_col:
                        prix_numeriques = pd.to_numeric(books_df[price_col], errors="coerce")
                        st.metric("Prix minimum", f"{prix_numeriques.min():.2f} £")
                    else:
                        st.metric("Prix minimum", "N/A")
                with col4:
                    if price_col:
                        prix_numeriques = pd.to_numeric(books_df[price_col], errors="coerce")
                        st.metric("Prix maximum", f"{prix_numeriques.max():.2f} £")
                    else:
                        st.metric("Prix maximum", "N/A")

                st.markdown("---")

                col_a, col_b = st.columns(2)
                with col_a:
                    if price_col:
                        fig1 = px.histogram(
                            books_df,
                            x=price_col,
                            nbins=30,
                            title="Distribution des prix",
                        )
                        st.plotly_chart(fig1, use_container_width=True)
                    else:
                        st.info("Colonne prix non trouvée")

                with col_b:
                    if rating_col:
                        rating_counts = books_df[rating_col].value_counts().reset_index()
                        rating_counts.columns = ["Note", "Nombre"]
                        fig2 = px.bar(
                            rating_counts,
                            x="Note",
                            y="Nombre",
                            title="Répartition des notes",
                        )
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.info("Colonne note non trouvée")

                if avail_col:
                    fig3 = px.pie(
                        books_df,
                        names=avail_col,
                        title="Disponibilité des livres",
                    )
                    st.plotly_chart(fig3, use_container_width=True)

                with st.expander("Voir les données"):
                    st.dataframe(books_df, use_container_width=True)

        else:
            if cars_df.empty:
                st.error("Aucune donnée de voitures n'a été trouvée dans le fichier JSON.")
            else:
                st.subheader(f"🚗 {len(cars_df)} voitures récupérées")

                marque_col = next((c for c in ["marque", "V1_Marque", "Marque"] if c in cars_df.columns), None)
                prix_col = next((c for c in ["prix", "V4_Prix", "Prix", "price"] if c in cars_df.columns), None)
                region_col = next((c for c in ["region", "V7_Region", "Région", "location"] if c in cars_df.columns), None)
                boite_col = next((c for c in ["boite", "V6_Boite", "Boite", "transmission"] if c in cars_df.columns), None)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Nombre total de voitures", len(cars_df))
                with col2:
                    if marque_col:
                        st.metric("Nombre de marques", cars_df[marque_col].nunique())
                    else:
                        st.metric("Nombre de marques", "N/A")
                with col3:
                    if region_col:
                        st.metric("Nombre de régions", cars_df[region_col].nunique())
                    else:
                        st.metric("Nombre de régions", "N/A")

                st.markdown("---")

                col_a, col_b = st.columns(2)
                with col_a:
                    if marque_col:
                        top_marques = (
                            cars_df[marque_col].value_counts().head(10).reset_index()
                        )
                        top_marques.columns = ["Marque", "Nombre"]
                        fig1 = px.bar(
                            top_marques,
                            x="Marque",
                            y="Nombre",
                            title="Top 10 des marques",
                        )
                        st.plotly_chart(fig1, use_container_width=True)
                    else:
                        st.info("Colonne marque non trouvée")

                with col_b:
                    if boite_col:
                        fig2 = px.pie(
                            cars_df,
                            names=boite_col,
                            title="Répartition des boîtes de vitesses",
                        )
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.info("Colonne boîte non trouvée")

                if region_col:
                    top_regions = (
                        cars_df[region_col].value_counts().head(10).reset_index()
                    )
                    top_regions.columns = ["Région", "Nombre"]
                    fig3 = px.bar(
                        top_regions,
                        x="Région",
                        y="Nombre",
                        title="Top 10 des régions",
                    )
                    st.plotly_chart(fig3, use_container_width=True)

                with st.expander("Voir les données"):
                    st.dataframe(cars_df, use_container_width=True)

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
        os.path.join(data_dir, "books_raw_data.csv"),
        os.path.join(data_dir, "books_data.csv"),
    ]
    car_files = [
        os.path.join(data_dir, "gaaraas_brut.csv"),
        os.path.join(data_dir, "cars_raw_data.csv"),
        os.path.join(data_dir, "cars_data.csv"),
    ]

    file_downloaded = False
    for file_path in book_files:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                st.download_button(
                    label=f"Télécharger {os.path.basename(file_path)}",
                    data=f,
                    file_name=os.path.basename(file_path),
                    mime="text/csv",
                )
            file_downloaded = True
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
            file_downloaded = True
            break

    if not file_downloaded:
        st.info("Aucun fichier brut trouvé dans le dossier data.")

# Page Scraping data
elif menu == "Scraping data":
    st.header("🔍 Scraping multi-pages avec Selenium")
    st.write("Colle un lien et lance le scraping sur plusieurs pages. Les données seront stockées dans le fichier JSON.")

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
                                    "V1_Titre": title,
                                    "V2_Prix": price,
                                    "V3_Disponibilite": availability,
                                    "V5_Note": rating,
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

                        if "books.toscrape.com" in url:
                            records = df_scraped.where(pd.notnull(df_scraped), None).to_dict(orient="records")
                            append_json_table("books", records)
                            st.info("Les données de livres ont été enregistrées dans data_collection.json")
                        elif "gaaraas.com" in url:
                            records = df_scraped.where(pd.notnull(df_scraped), None).to_dict(orient="records")
                            append_json_table("cars", records)
                            st.info("Les données de voitures ont été enregistrées dans data_collection.json")
                        else:
                            records = df_scraped.where(pd.notnull(df_scraped), None).to_dict(orient="records")
                            append_json_table("generic_scraping", records)
                            st.info("Les données génériques ont été enregistrées dans data_collection.json")

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
                        "pip install selenium webdriver-manager"
                    )
                except Exception as e:
                    st.error(f"Erreur Selenium : {e}")

# Page Formulaires
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
            "https://docs.google.com/forms/d/e/1FAIpQLScK9rU2LxRYeGuR7Z6yW0aYgPIH7P3una4jg8G3pY3a8fccvw/viewform?usp=header",
        )
