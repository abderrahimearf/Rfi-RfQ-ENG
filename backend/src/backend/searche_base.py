import weaviate
from sentence_transformers import SentenceTransformer

# 1. Initialiser le client Weaviate
client = weaviate.Client("http://localhost:8080")

# 2. Charger le modèle de vectorisation
model = SentenceTransformer('./models/intfloat_multilingual-e5-small')


# 3. Fonction de recherche sémantique
def search_chunks(query_text, top_k=3):
    print(f"🔍 Requête utilisateur : {query_text}")
    
    query_vector = model.encode(query_text)

    response = client.query.get(
        class_name="Chunk",
        properties=["contenu", "page", "indexchunk", "ofDocument"],
    ).with_near_vector({
        "vector": query_vector.tolist()
    }).with_limit(top_k).do()

    results = response.get("data", {}).get("Get", {}).get("Chunk", [])
    
    if not results:
        print("❌ Aucun résultat trouvé.")
        return []

    print(f"\n✅ {len(results)} résultats trouvés :\n")

    for i, chunk in enumerate(results, 1):
        print(f"🔹 Résultat {i}")
        print(f"📄 Page        : {chunk.get('page')}")
        print(f"🔢 Chunk Index : {chunk.get('indexchunk')}")
        print(f"🧩 Contenu     :\n{chunk.get('contenu')}\n")
        print("-" * 80)

    return results

# 4. Utilisation directe
if __name__ == "__main__":
    while True:
        user_input = input("📝 Entrez votre question (ou 'exit'): ").strip()
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("👋 Fin de session.")
            break

        search_chunks(user_input)
