import weaviate
from sentence_transformers import SentenceTransformer

def vector_search(client: weaviate.WeaviateClient, model: SentenceTransformer, query: str, limit: int = 5):
    try:
        chunks = client.collections.get("Chunk")
        print(f"Recherche vectorielle pour: '{query}'")

        query_vector = model.encode(query)

        response = chunks.query.near_vector(
            near_vector=query_vector.tolist(),
            limit=limit,
            include_vector=False
        )

        found_chunks = response.objects
        print(f"{len(found_chunks)} chunk(s) trouvé(s)\n")

        results = []
        for i, chunk in enumerate(found_chunks):
            result = {
                "chunk_id": str(chunk.uuid),
                "contenu": chunk.properties.get("contenu", ""),
                "page": chunk.properties.get("page", 0),
                "indexchunk": chunk.properties.get("indexchunk", 0),
            }
            results.append(result)

            print(f"📄Chunk {i+1}:")
            print(f"   Page {result['page']}, Index {result['indexchunk']}")
            print(f"   Contenu: {result['contenu'][:600]}...")
            print(f"   ID: {result['chunk_id']}")
            print()

        return results

    except Exception as e:
        print(f"Erreur lors de la recherche: {e}")
        return []

    
   
client = weaviate.connect_to_local(
            host="localhost",
            port=8080,
            grpc_port=50051,
        )

       

print("Connexion réussie à Weaviate.")
print("Chargement du modèle d'embeddings...")
model = SentenceTransformer('./models/intfloat_multilingual-e5-small')
print("Modèle chargé.\n")

query = "donner moi le Planning Prévisionnel pour ce projet de l'analyse vers le Déploiement"

results = vector_search(client, model, query, limit=2)

if results:
            print(f"Recherche terminée ! {len(results)} résultat(s) trouvé(s).")
else:
            print("Aucun résultat trouvé.")

    
  


