import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import time

# ============================================================
# CONFIGURATION DE LA PAGE
# ============================================================
st.set_page_config(
    page_title="Data App",
    page_icon="📊",
    layout="wide"
)

# ============================================================
# TITRE PRINCIPAL
# ============================================================
st.title("DATA APPS")
st.markdown("---")

# ============================================================
# MENU LATÉRAL (NAVIGATION)
# ============================================================
menu = st.sidebar.selectbox(
    "Navigation",
    [
        "Accueil",
        "Dashboard",
        "Téléchargement données brutes",
        "Scraping data",
        "Formulaires d'évaluation"
    ]
)

# ============================================================
# PAGE : ACCUEIL
# ============================================================
if menu == "Accueil":
    st.header("Bienvenue dans votre application d'analyse de données")
    st.write("""
    Cette application permet de :
    - Visualiser des données nettoyées (Books to Scrape + Gaaraas)
    - Télécharger les données dans leurs états bruts (No-code)
    - Lancer un scraping
    - Accéder aux formulaires d'évaluation
    """)

# ============================================================
# PAGE : DASHBOARD
# ============================================================
elif menu == "Dashboard":
    st.header("📈 Dashboard des données nettoyées")

    # Chemin de la base de données (modifiable selon ton environnement)
    # Sur Colab : /content/data_collection.db
    # En local : "data_collection.db" (si le fichier est dans le même dossier)
    DB_PATH = "/content/data_collection.db"

    try:
        # Tentative de connexion à la base SQLite
        conn = sqlite3.connect(DB_PATH)

        # Choix de la source de données
        choix = st.radio(
            "Choisir la source de données :",
            ["Livres (Books to Scrape)", "Voitures (Gaaraas)"],
            horizontal=True
        )

        # ====================================================
        # SECTION LIVRES
        # ====================================================
        if choix == "Livres (Books to Scrape)":
            # Vérification que la table "books" existe
            tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
            if "books" not in tables["name"].values:
                st.error("La table 'books' n'existe pas dans la base de données.")
            else:
                df = pd.read_sql("SELECT * FROM books", conn)

                st.subheader(f"📚 {len(df)} livres récupérés")

                # Détection automatique des colonnes (noms possibles)
                price_col = next((c for c in ["prix", "V2_Prix", "Prix", "price"] if c in df.columns), None)
                rating_col = next((c for c in ["note", "V5_Note", "rating", "Note"] if c in df.columns), None)
                avail_col = next((c for c in ["disponibilite", "V3_Disponibilite", "availability", "Disponibilité"] if c in df.columns), None)

                # --- KPIs ---
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Nombre total de livres", len(df))

                with col2:
                    if price_col:
                        # Conversion forcée en float + gestion des erreurs
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

                # --- Graphiques ---
                col_a, col_b = st.columns(2)

                with col_a:
                    if price_col:
                        fig1 = px.histogram(
                            df,
                            x=price_col,
                            nbins=30,
                            title="Distribution des prix"
                        )
                        st.plotly_chart(fig1, use_container_width=True)
                    else:
                        st.info("Colonne prix non trouvée → graphique non affiché")

                with col_b:
                    if rating_col:
                        rating_counts = df[rating_col].value_counts().reset_index()
                        rating_counts.columns = ["Note", "Nombre"]
                        fig2 = px.bar(
                            rating_counts,
                            x="Note",
                            y="Nombre",
                            title="Répartition des notes"
                        )
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.info("Colonne note non trouvée → graphique non affiché")

                # Graphique disponibilité
                if avail_col:
                    fig3 = px.pie(
                        df,
                        names=avail_col,
                        title="Disponibilité des livres"
                    )
                    st.plotly_chart(fig3, use_container_width=True)

                # Affichage du tableau de données
                with st.expander("Voir les données"):
                    st.dataframe(df, use_container_width=True)

        # ====================================================
        # SECTION VOITURES
        # ====================================================
        else:
            tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
            if "cars" not in tables["name"].values:
                st.error("La table 'cars' n'existe pas dans la base de données.")
            else:
                df = pd.read_sql("SELECT * FROM cars", conn)

                st.subheader(f"🚗 {len(df)} voitures récupérées")

                # Détection des colonnes
                marque_col = next((c for c in ["marque", "V1_Marque", "Marque"] if c in df.columns), None)
                prix_col = next((c for c in ["prix", "V4_Prix", "Prix"] if c in df.columns), None)
                annee_col = next((c for c in ["annee", "V3_Annee", "Année"] if c in df.columns), None)
                boite_col = next((c for c in ["boite", "V6_Boite", "Boite"] if c in df.columns), None)
                region_col = next((c for c in ["region", "V7_Region", "Région"] if c in df.columns), None)

                # --- KPIs ---
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

                # --- Graphiques ---
                col_a, col_b = st.columns(2)

                with col_a:
                    if marque_col:
                        top_marques = df[marque_col].value_counts().head(10).reset_index()
                        top_marques.columns = ["Marque", "Nombre"]
                        fig1 = px.bar(
                            top_marques,
                            x="Marque",
                            y="Nombre",
                            title="Top 10 des marques"
                        )
                        st.plotly_chart(fig1, use_container_width=True)
                    else:
                        st.info("Colonne marque non trouvée")

                with col_b:
                    if boite_col:
                        fig2 = px.pie(
                            df,
                            names=boite_col,
                            title="Répartition des boîtes de vitesses"
                        )
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.info("Colonne boîte non trouvée")

                # Graphique régions
                if region_col:
                    top_regions = df[region_col].value_counts().head(10).reset_index()
                    top_regions.columns = ["Région", "Nombre"]
                    fig3 = px.bar(
                        top_regions,
                        x="Région",
                        y="Nombre",
                        title="Top 10 des régions"
                    )
                    st.plotly_chart(fig3, use_container_width=True)

                with st.expander("Voir les données"):
                    st.dataframe(df, use_container_width=True)

        # Fermeture de la connexion
        conn.close()

    except FileNotFoundError:
        st.error(f"Fichier de base de données introuvable : {DB_PATH}")
        st.info("Vérifie que le fichier data_collection.db existe bien à cet emplacement.")
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")

# ============================================================
# PAGE : TÉLÉCHARGEMENT DES DONNÉES BRUTES
# ============================================================
elif menu == "Téléchargement données brutes":
    st.header("📥 Téléchargement des données brutes (No-code)")

    st.write("Téléchargez les fichiers CSV bruts issus de Web Scraper :")

    # Fichier Books
    try:
        with open("/content/drive/MyDrive/Data_collecte/bookscrape_data.csv", "rb") as f:
            st.download_button(
                label="Télécharger Books bruts",
                data=f,
                file_name="books_brut.csv",
                mime="text/csv"
            )
    except FileNotFoundError:
        st.warning("Fichier books_brut.csv non trouvé. Vérifie le chemin Google Drive.")
    except Exception as e:
        st.warning(f"Erreur Books : {e}")

    # Fichier Gaaraas
    try:
        with open("/content/drive/MyDrive/Data_collecte/gaaraas-com-2026-08-04.csv", "rb") as f:
            st.download_button(
                label="Télécharger Gaaraas bruts",
                data=f,
                file_name="gaaraas_brut.csv",
                mime="text/csv"
            )
    except FileNotFoundError:
        st.warning("Fichier gaaraas_brut.csv non trouvé. Vérifie le chemin Google Drive.")
    except Exception as e:
        st.warning(f"Erreur Gaaraas : {e}")

# ============================================================
# PAGE : SCRAPING (Selenium)
# ============================================================
elif menu == "Scraping data":
    st.header("🔍 Scraping avec Selenium")

    st.write("Colle une URL et lance le scraping (Selenium uniquement).")

    # Champ URL
    url = st.text_input(
        "URL à scraper",
        value="",
        placeholder="https://..."
    )

    # Nombre de pages
    nb_pages = st.number_input(
        "Nombre de pages",
        min_value=1,
        max_value=5,
        value=1
    )

    if st.button("Lancer le scraping", type="primary"):

        if not url:
            st.warning("Veuillez entrer une URL.")
        else:
            with st.spinner("Scraping en cours... Veuillez patienter !!"):
                try:
                    from selenium import webdriver
                    from selenium.webdriver.chrome.options import Options
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.chrome.service import Service
                    from webdriver_manager.chrome import ChromeDriverManager
                    import re

                    # Configuration Chrome headless
                    chrome_options = Options()
                    chrome_options.add_argument("--headless")
                    chrome_options.add_argument("--no-sandbox")
                    chrome_options.add_argument("--disable-dev-shm-usage")
                    chrome_options.add_argument("--window-size=1920,1080")
                    chrome_options.add_argument("--disable-gpu")

                    driver = webdriver.Chrome(
                        service=Service(ChromeDriverManager().install()),
                        options=chrome_options
                    )

                    data = []

                    # ====================================================
                    # CAS 1 : books.toscrape.com
                    # ====================================================
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
                                    "Note": rating
                                })

                    # ====================================================
                    # CAS 2 : gaaraas.com
                    # ====================================================
                    elif "gaaraas.com" in url:
                        for page in range(1, nb_pages + 1):
                            page_url = f"https://www.gaaraas.com/petites-annonces-voitures?page={page}"
                            driver.get(page_url)
                            time.sleep(2)

                            # Récupération du texte de la page
                            texte = driver.find_element(By.TAG_NAME, "body").text

                            # Découpage approximatif des annonces
                            blocs = re.split(r'\n(?=\d+\n\d{4}\s)', texte)

                            for bloc in blocs:
                                try:
                                    lignes = [l.strip() for l in bloc.split('\n') if l.strip()]

                                    if len(lignes) < 6:
                                        continue

                                    # Trouver la ligne Année + Marque + Modèle
                                    titre_line = None
                                    for l in lignes:
                                        if re.match(r'^\d{4}\s+\w+', l):
                                            titre_line = l
                                            break

                                    if not titre_line:
                                        continue

                                    parts = titre_line.split(' ', 2)
                                    annee = parts[0]
                                    marque = parts[1] if len(parts) > 1 else ""
                                    modele = parts[2] if len(parts) > 2 else ""

                                    # Région
                                    region = ""
                                    for l in lignes:
                                        if (l not in ["PRIX", "KILOMÉTRAGE"]
                                            and not l.startswith("CFA")
                                            and not l.startswith("Négociable")
                                            and "KM" not in l
                                            and l not in ["Manuelle", "Automatique"]
                                            and not l.startswith("Publié")
                                            and not re.match(r'^\d+$', l)
                                            and l != titre_line):
                                            region = l
                                            break

                                    # Prix
                                    prix = "Négociable"
                                    for i, l in enumerate(lignes):
                                        if "PRIX" in l and i + 1 < len(lignes):
                                            prix = lignes[i+1].replace("CFA", "").replace(" ", "").strip()
                                            break

                                    # Kilométrage
                                    kilometrage = "N/A"
                                    for i, l in enumerate(lignes):
                                        if "KILOMÉTRAGE" in l and i + 1 < len(lignes):
                                            kilometrage = lignes[i+1].replace("KM", "").replace(" ", "").strip()
                                            break

                                    # Boîte
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
                                        "V7_Region": region
                                    })

                                except Exception:
                                    continue

                    # ====================================================
                    # CAS 3 : Autres sites (générique)
                    # ====================================================
                    else:
                        driver.get(url)
                        time.sleep(2)

                        links = driver.find_elements(By.TAG_NAME, "a")
                        for link in links[:100]:
                            text = link.text.strip()
                            href = link.get_attribute("href")
                            if text and href:
                                data.append({
                                    "Texte": text,
                                    "Lien": href
                                })

                    # Fermeture du navigateur
                    driver.quit()

                    # Affichage des résultats
                    if data:
                        df_scraped = pd.DataFrame(data)
                        st.success(f"✅ {len(df_scraped)} éléments récupérés avec Selenium")
                        st.dataframe(df_scraped, use_container_width=True)

                        csv = df_scraped.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            label="📥 Télécharger les données",
                            data=csv,
                            file_name="scraping_selenium.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning("Aucune donnée trouvée.")

                except ImportError:
                    st.error(
                        "Selenium ou webdriver-manager n'est pas installé.\n\n"
                        "Installe-les avec :\n"
                        "`!pip install selenium webdriver-manager`"
                    )
                except Exception as e:
                    st.error(f"Erreur Selenium : {e}")

# ============================================================
# PAGE : FORMULAIRES D'ÉVALUATION
# ============================================================
elif menu == "Formulaires d'évaluation":
    st.header("📝 Formulaires d'évaluation de l'application")
    st.write("Votre avis nous aide à améliorer l'application.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Formulaire Kobo")
        st.write("Version KoboToolbox")
        st.link_button(
            "Remplir le formulaire Kobo",
            "https://ee.kobotoolbox.org/x/wjF8NPvg"
        )

    with col2:
        st.subheader("Formulaire Google Forms")
        st.write("Version Google Forms")
        st.link_button(
            "Remplir le formulaire Google Forms",
            "https://docs.google.com/forms/d/e/1FAIpQLScK9rU2LxRYeGuR7Z6yW0aYgPIH7P3una4jg8G3pY3a8fccvw/viewform?usp=header"
        )
