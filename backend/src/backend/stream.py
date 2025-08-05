import weaviate
import requests
import json
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import streamlit as st
from datetime import datetime

# Configuration API DeepSeek
API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-r1-0528:free"

class ChatRAG:
    def __init__(self):
        """Initialise le système Chat RAG"""
        self.model = None
        self.client = None
        self.chunks_collection = None
        
    def initialize(self):
        """Initialise les connexions et modèles"""
        try:
            # Chargement du modèle d'embeddings
            st.info(" Chargement du modèle d'embeddings...")
            self.model = SentenceTransformer('./models/intfloat_multilingual-e5-small')
            
            # Connexion à Weaviate
            st.info(" Connexion à Weaviate...")
            self.client = weaviate.connect_to_local(
                host="localhost",
                port=8080,
                grpc_port=50051,
            )
            
            if not self.client.is_ready():
                raise RuntimeError("Weaviate n'est pas disponible")
            
            self.chunks_collection = self.client.collections.get("Chunk")
            st.success("Système initialisé avec succès !")
            return True
            
        except Exception as e:
            st.error(f" Erreur d'initialisation: {e}")
            return False
    
    def search_chunks(self, question: str, limit: int = 2) -> List[Dict[str, Any]]:
        """Recherche vectorielle dans les chunks"""
        try:
            # Vectorisation de la question
            question_vector = self.model.encode(question)
            
            # Recherche vectorielle
            response = self.chunks_collection.query.near_vector(
                near_vector=question_vector.tolist(),
                limit=limit,
                include_vector=False
            )
            
            chunks = []
            for i, chunk in enumerate(response.objects):
                # Calcul du score de similarité (approximatif)
                score = 0.9 - (i * 0.1)  # Score décroissant
                
                chunk_data = {
                    'text': chunk.properties.get('contenu', ''),
                    'page': chunk.properties.get('page', 0),
                    'source': f"Document_{chunk.properties.get('indexchunk', i)}",
                    'score': score,
                    'chunk_id': str(chunk.uuid)
                }
                chunks.append(chunk_data)
            
            return chunks
            
        except Exception as e:
            st.error(f" Erreur lors de la recherche: {e}")
            return []
    
    def call_deepseek(self, question: str, passages: List[Dict[str, Any]]) -> str:
        """Appel à l'API DeepSeek avec le contexte RAG"""
        try:
            # Construction du contexte
            context = "\n\n".join(
                f"— Source: {p['source']} (page {p['page']}, score {p['score']:.4f})\n{p['text']}"
                for p in passages
            )
            
            # Prompt système
            system_prompt = (
                "Réponds en français. En utilisant les informations récupérées par notre système RAG, "
                "réponds à la question de l'utilisateur. Les informations peuvent être sous forme de tableaux "
                "ou de texte structuré - formate-les de manière claire et lisible. "
                "Si les informations ne permettent pas de répondre complètement, indique-le clairement. "
                "Utilise des titres, des listes à puces, des tableaux Markdown si nécessaire pour une meilleure lisibilité."
            )
            
            # Message utilisateur avec contexte
            user_message = f"""Question: {question}

Contexte récupéré:
{context}

Réponds à la question en utilisant principalement les informations du contexte ci-dessus."""
            
            # Appel API
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.7,
                "max_tokens": 1500
            }
            
            response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            return f" Erreur lors de l'appel à l'IA: {e}"
    
    def process_question(self, question: str) -> Dict[str, Any]:
        """Traite une question complète (RAG + LLM)"""
        # Recherche des chunks pertinents
        chunks = self.search_chunks(question, limit=2)
        
        if not chunks:
            return {
                'answer': " Aucune information pertinente trouvée dans la base de données.",
                'sources': [],
                'context_used': ""
            }
        
        # Appel au LLM
        answer = self.call_deepseek(question, chunks)
        
        return {
            'answer': answer,
            'sources': chunks,
            'context_used': len(chunks)
        }
    
    def cleanup(self):
        """Nettoie les ressources"""
        if self.client:
            self.client.close()

def main():
    """Interface Streamlit pour le chat"""
    st.set_page_config(
        page_title="Chat RAG - Assistant IA",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 Assistant IA ")
    st.markdown("*Posez vos questions et obtenez des réponses basées sur vos documents*")
    
    # Initialisation du système
    if 'chat_rag' not in st.session_state:
        st.session_state.chat_rag = ChatRAG()
        st.session_state.initialized = False
    
    if not st.session_state.initialized:
        if st.session_state.chat_rag.initialize():
            st.session_state.initialized = True
            st.rerun()
        else:
            st.stop()
    
    # Historique des conversations
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Affichage de l'historique
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.markdown(message["content"])
                if "sources" in message and message["sources"]:
                    with st.expander("📚 Sources utilisées"):
                        for i, source in enumerate(message["sources"], 1):
                            st.markdown(f"""
                            **Source {i}**: {source['source']} (Page {source['page']})
                            - Score: {source['score']:.3f}
                            - Extrait: {source['text'][:200]}...
                            """)
            else:
                st.markdown(message["content"])
    
    # Zone de saisie
    if prompt := st.chat_input("Posez votre question..."):
        # Ajout du message utilisateur
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Traitement de la question
        with st.chat_message("assistant"):
            with st.spinner(" Recherche d'informations..."):
                result = st.session_state.chat_rag.process_question(prompt)
            
            # Affichage de la réponse
            st.markdown(result['answer'])
            
            # Ajout à l'historique
            st.session_state.messages.append({
                "role": "assistant", 
                "content": result['answer'],
                "sources": result['sources']
            })
        
        st.rerun()
    
    # Barre latérale avec informations
    with st.sidebar:
        st.markdown("### Informations")
        st.markdown(f"**Messages**: {len(st.session_state.messages)}")
        st.markdown(f"**Statut**: {' Connecté' if st.session_state.initialized else '❌ Déconnecté'}")
        
        if st.button("🗑️ Vider l'historique"):
            st.session_state.messages = []
            st.rerun()
        
        if st.button(" Redémarrer"):
            st.session_state.chat_rag.cleanup()
            st.session_state.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("###  Conseils d'utilisation")
        st.markdown("""
        - Posez des questions précises
        - Les réponses sont basées sur vos documents
        - Consultez les sources pour plus de détails
        - Utilisez des mots-clés pertinents
        """)

# Version console alternative
def console_version():
    """Version console du chat RAG"""
    print("🤖 Assistant IA ")
    print("=" * 50)
    
    # Initialisation
    chat_rag = ChatRAG()
    print("Initialisation du système...")
    
    try:
        chat_rag.model = SentenceTransformer('./models/intfloat_multilingual-e5-small')
        chat_rag.client = weaviate.connect_to_local(
            host="localhost", port=8080, grpc_port=50051
        )
        chat_rag.chunks_collection = chat_rag.client.collections.get("Chunk")
        print(" Système initialisé !")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    print("\n Commencez à poser vos questions (tapez 'quit' pour quitter)")
    print("-" * 50)
    
    try:
        while True:
            question = input("\n Vous: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
            
            if not question:
                continue
            
            print("🔍 Recherche en cours...")
            result = chat_rag.process_question(question)
            
            print(f"\n🤖 Assistant:")
            print(result['answer'])
            
            if result['sources']:
                print(f"\n Sources ({len(result['sources'])}):")
                for i, source in enumerate(result['sources'], 1):
                    print(f"  {i}. {source['source']} (page {source['page']}, score: {source['score']:.3f})")
            
            print("-" * 50)
    
    except KeyboardInterrupt:
        print("\n Au revoir !")
    
    finally:
        chat_rag.cleanup()

if __name__ == "__main__":
    # Choix de l'interface
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--console":
        console_version()
    else:
        # Interface Streamlit par défaut
        main()