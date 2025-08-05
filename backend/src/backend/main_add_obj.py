import weaviate
from sentence_transformers import SentenceTransformer
from add_class_to_data import setup_schema
from add_obj_to_class import upload_document_and_chunks

def main():
    client = None
    try:
     
        client = weaviate.connect_to_local(
            host="localhost",
            port=8080,
            grpc_port=50051, 
        )
        
       
        if not client.is_ready():
            raise RuntimeError("Weaviate n'est pas prêt ! Vérifiez que le service tourne bien.")
        print(" Connexion réussie à Weaviate.")
        
        
        print("Chargement du modèle d'embeddings...")
        
        model = SentenceTransformer('intfloat/multilingual-e5-small')
        print(" Modèle chargé.")
        
       
        print("🔧 Configuration du schéma...")
        setup_schema(client)
        
        
        document = {
            "title": "Offre Client ABC",
            "document_type": "offre",
            "summary": "Résumé de l'offre pour le client ABC incluant les solutions techniques proposées.",
            "keywords": ["offre", "client", "technique", "solution"],
            "client": "Client ABC",
            "sector": ["Consulting", "IT"],  
            "attachments": "offre_abc.pdf",
            "budget": 15000,
            "date": "2024-12-01",
            "userid": "user-001"
        }
        
       
        file_path = r"C:\Users\DHM\Downloads\Proposition_Solution_Technique_MarocData.pdf"
        
       
        from pathlib import Path
        if not Path(file_path).exists():
            print(f"Fichier non trouvé: {file_path}")
            print("Veuillez vérifier le chemin du fichier.")
            return
        
       
        print(" Upload du document et de ses chunks...")
        upload_document_and_chunks(
            client=client,
            document_json=document,
            file_path=file_path,
            model=model,
            max_chars=500,
            overlap_chars=50
        )
        
        print(" Processus terminé avec succès!")
        
    except Exception as e:
        print(f"Erreur: {e}")
        raise
    finally:
        if client:
            client.close()
            print(" Connexion fermée.")

if __name__ == "__main__":
    main()

