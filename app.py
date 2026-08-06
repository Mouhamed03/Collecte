import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

# === Configuration de la page ===
st.set_page_config(
    page_title="Data App",
    page_icon="📊",
    layout="wide"
)

st.title("DATA APPS")
st.markdown("---")

# === Chemins relatifs ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "data_collection.db")  # La base dans le dossier data/

# === Menu latéral ===
menu = st.sidebar.selectbox(
    "Navigation",
    [
        "Accueil",
        "Dashboard",
        "Téléchargement données brutes",
        "Formulaires d'évaluation"
    ]
)

# === PAGE ACCUEIL ===
if menu == "Accueil":
    st.header("Bienvenue dans votre application d'analyse de données")
    st.write("""
    Cette application permet de :
    - Visualiser des données nettoyées (Books to Scrape + Gaaraas)
    - Télécharger les données dans leurs états bruts (No-code)
    - Accéder aux formulaires d'évaluation
    """)

# === PAGE DASHBOARD ===
elif menu == "Dashboard":
    st.header("📈 Dashboard des données nettoyées")

    # Vérifier que la base existe
    if not os.path.exists(DB_PATH):
        st.error(f"Base de données introuvable à {DB_PATH}. Vérifie que le fichier data_collection.db est dans le dossier data/.")
    else:
        try:
            # Connexion à la base SQLite
            conn = sqlite3.connect(DB_PATH)

            choix = st.radio(
                "Choisir la source de données :",
                ["Livres (Books to Scrape)", "Voitures (Gaaraas)"],
                horizontal=True
            )

            # === SECTION LIVRES ===
            if choix == "Livres (Books to Scrape)":
                # Vérifier que la table books existe
                tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
                if "books" not in tables["name"].values:
                    st.error("La table 'books' n'existe pas dans la base de données.")
                else:
                    df = pd.read_sql("SELECT * FROM books", conn)
                    st.subheader(f"📚 {len(df)} livres récupérés")

                    # Colonne prix
                    price_col = "V2_Prix" if "V2_Prix" in df.columns else None
                    if price_col:
                        df["prix_clean"] = pd.to_numeric(df[price_col], errors="coerce")
                        prix_clean = df["prix_clean"]

                    # KPIs
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
                            fig = px.histogram(df, x="prix_clean", nbins=30, title="Distribution des prix")
                            st.plotly_chart(fig, use_container_width=True)
                    with col_b:
                        rating_col = "V5_Note" if "V5_Note" in df.columns else None
                        if rating_col:
                            rating_counts = df[rating_col].value_counts().reset_index()
                            rating_counts.columns = ["Note", "Nombre"]
                            fig = px.bar(rating_counts, x="Note", y="Nombre", title="Répartition des notes")
                            st.plotly_chart(fig, use_container_width=True)

                    avail_col = "V3_Disponibilite" if "V3_Disponibilite" in df.columns else None
                    if avail_col:
                        fig = px.pie(df, names=avail_col, title="Disponibilité des livres")
                        st.plotly_chart(fig, use_container_width=True)

                    with st.expander("Voir les données"):
                        st.dataframe(df, use_container_width=True)

            # === SECTION VOITURES ===
            else:
                tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
                if "cars" not in tables["name"].values:
                    st.error("La table 'cars' n'existe pas dans la base de données.")
                else:
                    df = pd.read_sql("SELECT * FROM cars", conn)
                    st.subheader(f"🚗 {len(df)} voitures récupérées")

                    marque_col = "V1_Marque" if "V1_Marque" in df.columns else None
                    region_col = "V7_Region" if "V7_Region" in df.columns else None

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
                            top = df[marque_col].value_counts().head(10).reset_index()
                            top.columns = ["Marque", "Nombre"]
                            fig = px.bar(top, x="Marque", y="Nombre", title="Top 10 des marques")
                            st.plotly_chart(fig, use_container_width=True)
                    with col_b:
                        boite_col = "V6_Boite" if "V6_Boite" in df.columns else None
                        if boite_col:
                            fig = px.pie(df, names=boite_col, title="Répartition des boîtes de vitesses")
                            st.plotly_chart(fig, use_container_width=True)

                    if region_col:
                        top_regions = df[region_col].value_counts().head(10).reset_index()
                        top_regions.columns = ["Région", "Nombre"]
                        fig = px.bar(top_regions, x="Région", y="Nombre", title="Top 10 des régions")
                        st.plotly_chart(fig, use_container_width=True)

                    with st.expander("Voir les données"):
                        st.dataframe(df, use_container_width=True)

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
                mime="text/csv"
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
                mime="text/csv"
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
            "https://ee.kobotoolbox.org/x/wjF8NPvg"
        )
    with col2:
        st.subheader("Formulaire Google Forms")
        st.link_button(
            "Remplir le formulaire Google Forms",
            "https://docs.google.com/forms/d/e/1FAIpQLScK9rU2LxRYeGuR7Z6yW0aYgPIH7P3una4jg8G3pY3a8fccvw/viewform"
        )
