import weaviate
from sentence_transformers import SentenceTransformer
from weaviate.classes.query import Filter, QueryReference
from typing import Dict, List, Any, Optional

class Rechercheur:
    def __init__(self, client: weaviate.WeaviateClient, model: SentenceTransformer, maxdoc: int = 2, maxchnunks: int = 2):
        self.client = client
        self.model = model
        self.documents = client.collections.get("Document")
        self.chunks = client.collections.get("Chunk")
        self.maxdoc = maxdoc
        self.maxchnunks = maxchnunks
    
    def recherche_complete(self, search_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recherche complète en 3 phases
        """
        print(f"🚀 Démarrage de la recherche en 3 phases (max {self.maxdoc} docs, {self.maxchnunks} chunks)...")
        
        # Phase 1: Filtres exacts
        documents_filtres = self._phase1_filtres_exacts(search_input)
        if not documents_filtres:
            return {"documents": [], "chunks": [], "message": "Aucun document trouvé avec les filtres exacts"}
        
        # Phase 2: Recherche hybride sur documents
        documents_candidats = self._phase2_recherche_hybride_documents(documents_filtres, search_input)
        if not documents_candidats:
            return {"documents": [], "chunks": [], "message": "Aucun document candidat trouvé"}
        
        # Phase 3: Recherche hybride sur chunks
        chunks_finaux = self._phase3_recherche_hybride_chunks(documents_candidats, search_input)
        
        return {
            "documents": documents_candidats,
            "chunks": chunks_finaux,
            "message": f"Trouvé {len(documents_candidats)} document(s) et {len(chunks_finaux)} chunk(s)"
        }
    
    def _phase1_filtres_exacts(self, search_input: Dict[str, Any]) -> List[Any]:
        """
        Phase 1: Filtres exacts sur title, client, document_type
        """
        print("📋 Phase 1: Application des filtres exacts...")
        
        try:
            # Construction des filtres exacts
            filters = []
            
            if search_input.get("title"):
                title_values = search_input["title"]
                for title in title_values:
                    filters.append(Filter.by_property("title").equal(title))
            
            if search_input.get("client"):
                client_values = search_input["client"]
                for client in client_values:
                    filters.append(Filter.by_property("client").equal(client))
            
            if search_input.get("document_type"):
                doc_type_values = search_input["document_type"]
                for doc_type in doc_type_values:
                    filters.append(Filter.by_property("document_type").equal(doc_type))
            
            # Application des filtres
            if filters:
                # Combine avec OR pour chaque type, puis AND entre les types
                combined_filter = filters[0]
                for f in filters[1:]:
                    combined_filter = combined_filter | f
                
                response = self.documents.query.fetch_objects(
                    where=combined_filter,
                    limit=50  # Large limite pour la phase 2
                )
            else:
                # Pas de filtres, prendre tous les documents
                response = self.documents.query.fetch_objects(limit=50)
            
            documents = response.objects
            print(f"   ✅ {len(documents)} document(s) après filtrage exact")
            return documents
            
        except Exception as e:
            print(f"   ⚠️ Erreur filtres exacts, fallback sans filtres: {e}")
            # Fallback: récupération manuelle avec filtrage
            return self._fallback_filtrage_manuel(search_input)
    
    def _fallback_filtrage_manuel(self, search_input: Dict[str, Any]) -> List[Any]:
        """
        Filtrage manuel en cas d'échec des filtres Weaviate
        """
        try:
            response = self.documents.query.fetch_objects(limit=50)
            all_docs = response.objects
            
            filtered_docs = []
            for doc in all_docs:
                match = True
                
                # Vérifie title
                if search_input.get("title"):
                    doc_title = doc.properties.get("title", "")
                    if not any(title in doc_title for title in search_input["title"]):
                        match = False
                
                # Vérifie client
                if match and search_input.get("client"):
                    doc_client = doc.properties.get("client", "")
                    if doc_client not in search_input["client"]:
                        match = False
                
                # Vérifie document_type
                if match and search_input.get("document_type"):
                    doc_type = doc.properties.get("document_type", "")
                    if doc_type not in search_input["document_type"]:
                        match = False
                
                if match:
                    filtered_docs.append(doc)
            
            print(f"   ✅ {len(filtered_docs)} document(s) après filtrage manuel")
            return filtered_docs
            
        except Exception as e:
            print(f"   ❌ Erreur filtrage manuel: {e}")
            return []
    
    def _phase2_recherche_hybride_documents(self, documents_filtres: List[Any], search_input: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Phase 2: Recherche hybride sur documents avec summary, keywords, sector
        """
        print("🔍 Phase 2: Recherche hybride sur documents...")
        
        # Construction de la requête hybride
        query_parts = []
        
        if search_input.get("summary"):
            query_parts.append(search_input["summary"])
        
        if search_input.get("keywords"):
            query_parts.extend(search_input["keywords"])
        
        if search_input.get("sector"):
            query_parts.extend(search_input["sector"])
        
        if not query_parts:
            # Pas de critères hybrides, prendre les premiers documents filtrés
            print(f"   ⚠️ Pas de critères hybrides, sélection des {self.maxdoc} premiers documents")
            return self._format_documents(documents_filtres[:self.maxdoc])
        
        query_text = " ".join(query_parts)
        print(f"   🎯 Requête vectorielle: '{query_text[:100]}...'")
        
        try:
            # Encode manuellement la requête puisque pas de vectorizer automatique
            query_vector = self.model.encode(query_text)
            
            # Recherche vectorielle manuelle dans les documents
            response = self.documents.query.near_vector(
                near_vector=query_vector.tolist(),
                limit=self.maxdoc * 3  # Plus large pour filtrer ensuite
            )
            
            hybrid_docs = response.objects
            
            # Filtrer pour ne garder que les documents de la phase 1
            doc_ids_phase1 = [str(doc.uuid) for doc in documents_filtres]
            documents_candidats = []
            
            for doc in hybrid_docs:
                if str(doc.uuid) in doc_ids_phase1:
                    documents_candidats.append(doc)
                    if len(documents_candidats) >= self.maxdoc:
                        break
            
            # Si pas assez de résultats hybrides, compléter avec les documents filtrés
            if len(documents_candidats) < self.maxdoc:
                for doc in documents_filtres:
                    if str(doc.uuid) not in [str(d.uuid) for d in documents_candidats]:
                        documents_candidats.append(doc)
                        if len(documents_candidats) >= self.maxdoc:
                            break
            
            print(f"   ✅ {len(documents_candidats)} document(s) candidat(s) sélectionné(s)")
            return self._format_documents(documents_candidats)
            
        except Exception as e:
            print(f"   ⚠️ Erreur recherche vectorielle documents: {e}")
            # Fallback: sélectionner les premiers documents filtrés
            return self._format_documents(documents_filtres[:self.maxdoc])
    
    def _phase3_recherche_hybride_chunks(self, documents_candidats: List[Dict[str, Any]], search_input: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Phase 3: Recherche hybride dans les chunks avec la query
        """
        print("🎯 Phase 3: Recherche vectorielle dans les chunks...")
        
        query = search_input.get("query", "")
        if not query:
            print("   ⚠️ Pas de query fournie")
            return []
        
        print(f"   🎯 Query: '{query}'")
        
        # IDs des documents candidats
        doc_ids = [doc["id"] for doc in documents_candidats]
        
        try:
            # Encode manuellement la query puisque pas de vectorizer automatique
            query_vector = self.model.encode(query)
            
            # Recherche vectorielle manuelle dans les chunks
            response = self.chunks.query.near_vector(
                near_vector=query_vector.tolist(),
                limit=self.maxchnunks * 5  # Plus large pour filtrer ensuite
            )
            
            all_chunks = response.objects
            print(f"   📊 {len(all_chunks)} chunk(s) trouvé(s) au total")
            print(f"   🎯 Documents candidats IDs: {doc_ids}")
            
            # Debug: afficher la structure du premier chunk
            if len(all_chunks) > 0:
                first_chunk = all_chunks[0]
                print(f"   🔍 Structure du premier chunk:")
                print(f"      - UUID: {first_chunk.uuid}")
                print(f"      - Properties: {list(first_chunk.properties.keys()) if first_chunk.properties else 'None'}")
                print(f"      - Has references attr: {hasattr(first_chunk, 'references')}")
                if hasattr(first_chunk, 'references'):
                    print(f"      - References: {first_chunk.references}")
                    if first_chunk.references:
                        print(f"      - References keys: {list(first_chunk.references.keys())}")
            
            # Filtrer pour ne garder que les chunks des documents candidats
            chunks_filtres = []
            for i, chunk in enumerate(all_chunks):
                try:
                    print(f"   🔍 Chunk {i+1}: analyse...")
                    
                    # Méthode 1: Vérifier les références
                    ref_doc_id = None
                    if hasattr(chunk, 'references') and chunk.references:
                        if chunk.references.get("ofDocument"):
                            if hasattr(chunk.references["ofDocument"], 'objects') and chunk.references["ofDocument"].objects:
                                ref_doc_id = str(chunk.references["ofDocument"].objects[0].uuid)
                                print(f"      ✅ Référence trouvée: {ref_doc_id}")
                            else:
                                print(f"      ⚠️ ofDocument existe mais pas d'objects")
                        else:
                            print(f"      ❌ Pas de référence ofDocument")
                    else:
                        print(f"      ❌ Pas de références du tout")
                    
                    # Si on a trouvé une référence valide
                    if ref_doc_id and ref_doc_id in doc_ids:
                        chunks_filtres.append(chunk)
                        print(f"      ✅ Chunk ajouté ! ({len(chunks_filtres)}/{self.maxchnunks})")
                        if len(chunks_filtres) >= self.maxchnunks:
                            break
                    elif ref_doc_id:
                        print(f"      ❌ Document ID '{ref_doc_id}' non dans candidats {doc_ids}")
                        
                except Exception as ref_error:
                    print(f"      ⚠️ Erreur référence chunk {i+1}: {ref_error}")
                    continue
            
            print(f"   ✅ {len(chunks_filtres)} chunk(s) pertinent(s) trouvé(s)")
            
            # Si aucun chunk trouvé avec filtrage, essai sans filtrage
            if len(chunks_filtres) == 0 and len(all_chunks) > 0:
                print(f"   🔄 Fallback: prise des {self.maxchnunks} premiers chunks sans filtrage")
                chunks_filtres = all_chunks[:self.maxchnunks]
            
            return self._format_chunks(chunks_filtres)
            
        except Exception as e:
            print(f"   ⚠️ Erreur recherche vectorielle chunks: {e}")
            # Fallback: recherche vectorielle simple
            return self._fallback_chunks_vectoriel(doc_ids, query)
    
    def _fallback_chunks_vectoriel(self, doc_ids: List[str], query: str) -> List[Dict[str, Any]]:
        """
        Fallback: recherche vectorielle simple dans les chunks
        """
        try:
            query_vector = self.model.encode(query)
            
            response = self.chunks.query.near_vector(
                near_vector=query_vector.tolist(),
                limit=self.maxchnunks * 5
            )
            
            all_chunks = response.objects
            
            # Filtrage manuel
            chunks_filtres = []
            for chunk in all_chunks:
                try:
                    if hasattr(chunk, 'references') and chunk.references.get("ofDocument"):
                        ref_doc_id = str(chunk.references["ofDocument"].objects[0].uuid)
                        if ref_doc_id in doc_ids:
                            chunks_filtres.append(chunk)
                            if len(chunks_filtres) >= self.maxchnunks:
                                break
                except:
                    continue
            
            print(f"   ✅ Fallback vectoriel: {len(chunks_filtres)} chunk(s)")
            return self._format_chunks(chunks_filtres)
            
        except Exception as e:
            print(f"   ❌ Erreur fallback chunks: {e}")
            return []
    
    def _format_documents(self, docs: List[Any]) -> List[Dict[str, Any]]:
        """Formate les documents pour la réponse"""
        formatted = []
        for doc in docs:
            formatted.append({
                "id": str(doc.uuid),
                "title": doc.properties.get("title", ""),
                "client": doc.properties.get("client", ""),
                "document_type": doc.properties.get("document_type", ""),
                "summary": doc.properties.get("summary", ""),
                "keywords": doc.properties.get("keywords", []),
                "sector": doc.properties.get("sector", []),
                "budget": doc.properties.get("budget", 0),
                "date": doc.properties.get("date", "")
            })
        return formatted
    
    def _format_chunks(self, chunks: List[Any]) -> List[Dict[str, Any]]:
        """Formate les chunks pour la réponse"""
        formatted = []
        for chunk in chunks:
            doc_id = "unknown"
            try:
                if hasattr(chunk, 'references') and chunk.references.get("ofDocument"):
                    doc_id = str(chunk.references["ofDocument"].objects[0].uuid)
            except:
                pass
            
            formatted.append({
                "id": str(chunk.uuid),
                "contenu": chunk.properties.get("contenu", ""),
                "page": chunk.properties.get("page", 0),
                "indexchunk": chunk.properties.get("indexchunk", 0),
                "document_id": doc_id
            })
        return formatted

# Fonction principale pour utiliser le module
def recherche(search_input: Dict[str, Any], maxdoc: int = 2, maxchnunks: int = 2, model: SentenceTransformer = None) -> Dict[str, Any]:
    """
    Point d'entrée principal du module de recherche
    
    Args:
        search_input: JSON avec les critères de recherche
        maxdoc: Nombre maximum de documents à retourner (défaut: 2)
        maxchnunks: Nombre maximum de chunks à retourner (défaut: 2)
        model: Modèle SentenceTransformer pour la vectorisation
    """
    client = None
    try:
        # Vérification du modèle
        if model is None:
            return {"error": "Le modèle SentenceTransformer est requis"}
        
        # Connexion à Weaviate
        client = weaviate.connect_to_local(
            host="localhost",
            port=8080,
            grpc_port=50051,
        )
        
        if not client.is_ready():
            return {"error": "Weaviate n'est pas disponible"}
        
        # Création du rechercheur avec le modèle fourni
        rechercheur = Rechercheur(client, model, maxdoc, maxchnunks)
        
        # Exécution de la recherche
        results = rechercheur.recherche_complete(search_input)
        
        return results
        
    except Exception as e:
        return {"error": f"Erreur lors de la recherche: {e}"}
    finally:
        if client:
            client.close()

# Test du module
if __name__ == "__main__":
    # Chargement du modèle à l'extérieur
    print("📥 Chargement du modèle d'embeddings...")
    model = SentenceTransformer('./models/intfloat_multilingual-e5-small')
    print("✅ Modèle chargé.")
    
    search_input = {
        "title": ["Offre Client ABC"],
        "document_type": ["offre"],
        "client": ["Client ABC"],
        "summary": "Résumé de l'offre",
        "keywords": ["Proposition de Solution Technique", "Société MarocData"],
        "sector": ["Consulting"],
        "query": "donner moi le Planning Prévisionnel pour ce projet de l'analyse vers le Déploiement"
    }
    
    print("🧪 Test du module de recherche...")
    results = recherche(search_input, maxdoc=2, maxchnunks=2, model=model)
    
    if "error" in results:
        print(f"❌ Erreur: {results['error']}")
    else:
        print(f"\n🎉 Résultats:")
        print(f"📋 Documents trouvés: {len(results['documents'])}")
        print(f"📝 Chunks trouvés: {len(results['chunks'])}")
        print(f"💬 Message: {results['message']}")
        
        for i, doc in enumerate(results['documents']):
            print(f"\n📋 Document {i+1}: {doc['title']}")
        
        for i, chunk in enumerate(results['chunks']):
            print(f"\n📝 Chunk {i+1}: {chunk['contenu'][:1000]}...")