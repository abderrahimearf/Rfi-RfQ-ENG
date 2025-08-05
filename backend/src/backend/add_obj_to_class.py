import uuid
import weaviate
from pathlib import Path
from sentence_transformers import SentenceTransformer
from extract_doc import process_file

def upload_document_and_chunks(
    client: weaviate.WeaviateClient,
    document_json: dict,
    file_path: str,
    model: SentenceTransformer,
    max_chars: int = 500,
    overlap_chars: int = 50
):
    
   
    try:
        
        documents = client.collections.get("Document")
        chunks_collection = client.collections.get("Chunk")
        
       
        doc_uuid = str(uuid.uuid4())
        document_json["docid"] = doc_uuid
        
       
        keywords_text = ""
        if isinstance(document_json.get("keywords"), list):
            keywords_text = " ".join(document_json.get("keywords", []))
        else:
            keywords_text = document_json.get("keywords", "")
            
        sector_text = ""
        if isinstance(document_json.get("sector"), list):
            sector_text = " ".join(document_json.get("sector", []))
        else:
            sector_text = document_json.get("sector", "")
        
        full_text = " ".join([
            document_json.get("title", ""),
            document_json.get("summary", ""),
            keywords_text,
            sector_text,
            document_json.get("client", "")
        ])
        
        doc_vector = model.encode(full_text)
        print(f"Nouveau document → docid: {doc_uuid}")
        
     
        document_data = document_json.copy()
        
  
        print(f" Données document: sector={document_data.get('sector')} (type: {type(document_data.get('sector'))})")
        print(f" Keywords: {document_data.get('keywords')} (type: {type(document_data.get('keywords'))})")
        
    
        documents.data.insert(
            properties=document_data,
            uuid=doc_uuid,
            vector=doc_vector.tolist()
        )
        print("Document ajouté à Weaviate.")
        
      
        chunks = process_file(file_path, max_chars=max_chars, overlap_chars=overlap_chars)
        if not chunks:
            print("Aucun chunk extrait du fichier.")
            return
        
        print(f"Ajout de {len(chunks)} chunks...")
        
     
        successful_chunks = 0
        errors = []
        
        for i, chunk in enumerate(chunks):
            try:
                chunk_uuid = str(uuid.uuid4())
                chunk_vector = model.encode(chunk["contenu"])
                
              
                chunks_collection.data.insert(
                    properties={
                        "indexchunk": chunk.get("indexchunk", i),
                        "contenu": chunk["contenu"],
                        "page": chunk.get("page", 1),
                    },
                    uuid=chunk_uuid,
                    vector=chunk_vector.tolist(),
                    references={"ofDocument": doc_uuid}
                )
                successful_chunks += 1
                print(f"  Chunk {i+1}/{len(chunks)} ajouté")
                
            except Exception as e:
                error_msg = f"Erreur chunk {i+1}: {e}"
                errors.append(error_msg)
                print(f"   {error_msg}")
        
       
        if errors:
            print(f"{successful_chunks}/{len(chunks)} chunks ajoutés avec succès.")
            print("Erreurs rencontrées:")
            for error in errors[:3]:  
                print(f"  - {error}")
        else:
            print(f" Tous les chunks ({successful_chunks}) ont été ajoutés avec succès !")
            
    except Exception as e:
        print(f"Erreur lors de l'upload: {e}")
        raise