import weaviate
from sentence_transformers import SentenceTransformer

# 1. Connexion à Weaviate
client = weaviate.Client("http://localhost:8080")

# 2. Charger le modèle local
model = SentenceTransformer('./models/intfloat_multilingual-e5-small')  # ou le chemin correct vers ton modèle

# 3. Requête utilisateur
query = "donner moi le Planning Prévisionnel pour ce projet de l'analyse vers le Déploiement"

# 4. Encoder la requête
query_vector = model.encode(query).tolist()

# 5. Recherche sémantique dans les chunks
response = (
    client.query
    .get("Chunk", ["contenu", "page"])
    .with_near_vector({"vector": query_vector})
    .with_limit(1)
    .do()
)

# 6. Afficher les résultats
results = response.get("data", {}).get("Get", {}).get("Chunk", [])
if not results:
    print("❌ Aucun résultat trouvé.")
else:
    print("✅ Résultats pertinents :\n")
    for i, chunk in enumerate(results, 1):
        print(f"🔹 Chunk {i} (Page {chunk.get('page')}):\n{chunk.get('contenu')}\n{'-'*60}")
