import sqlite3
import pandas as pd
import os

print("🔧 Création de la base de données...")

# Chemin du dossier data
data_dir = "data"
os.makedirs(data_dir, exist_ok=True)

# Chemins des CSV
books_csv = os.path.join(data_dir, "books_brut.csv")
cars_csv = os.path.join(data_dir, "gaaraas_brut.csv")

# Vérifier que les fichiers existent
if not os.path.exists(books_csv):
    print(f"❌ Fichier introuvable : {books_csv}")
    exit(1)
if not os.path.exists(cars_csv):
    print(f"❌ Fichier introuvable : {cars_csv}")
    exit(1)

# Charger les CSV
df_books = pd.read_csv(books_csv)
df_cars = pd.read_csv(cars_csv)

print(f"📚 Livres chargés : {len(df_books)} lignes")
print(f"🚗 Voitures chargées : {len(df_cars)} lignes")
print("Colonnes livres :", df_books.columns.tolist())
print("Colonnes voitures :", df_cars.columns.tolist())

# Créer la base
db_path = os.path.join(data_dir, "data_collection.db")
conn = sqlite3.connect(db_path)

# Écrire les tables
df_books.to_sql("books", conn, if_exists="replace", index=False)
df_cars.to_sql("cars", conn, if_exists="replace", index=False)

conn.close()

print(f"✅ Base de données créée avec succès : {db_path}")
print(f"   - Table 'books' : {len(df_books)} enregistrements")
print(f"   - Table 'cars'  : {len(df_cars)} enregistrements")
