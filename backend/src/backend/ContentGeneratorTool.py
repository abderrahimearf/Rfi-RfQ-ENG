import json
import os
import requests
from typing import Dict, Any
import weaviate
from sentence_transformers import SentenceTransformer

# --- Constantes ---
API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-r1-0528:free"

class Generationtoll:
    
    def __init__(self, sections_meta: Dict[str, Any], 
                 weaviate_host: str = "localhost",
                 weaviate_port: int = 8080,
                 grpc_port: int = 50051):
        
        print("Initialisation de Generationtoll...")
        self.sections_meta = sections_meta
        self.weaviate_host = weaviate_host
        self.weaviate_port = weaviate_port
        self.grpc_port = grpc_port
        model_name_or_path = 'intfloat/multilingual-e5-small'
        
        print(f"Chargement du modèle de vectorisation : '{model_name_or_path}'...")
        print("Cela peut prendre un moment lors du premier lancement.")
        
        try:
          
            self.model = SentenceTransformer(model_name_or_path)
            print("Modèle chargé avec succès.")
        except Exception as e:
            print(f"ERREUR CRITIQUE: Impossible de télécharger ou de charger le modèle '{model_name_or_path}'.")
            print("Vérifiez votre connexion Internet ou le nom du modèle.")
            raise e

        self.client = None
        self._connect_to_weaviate()

    def _search_chunks(self, query: str, limit: int = 2) -> str:
        """
        Effectue une recherche hybride (sémantique + mots-clés) dans Weaviate.
        """
        print(f"Exécution d'une recherche hybride pour: '{query}'")
        
        try:
            question_vector = self.model.encode(query).tolist()
            
            response = self.chunks_collection.query.hybrid(
                query=query,
                vector=question_vector,
                limit=limit,
                alpha=0.5
            )
            
            if not response.objects: 
                print("Aucun contexte pertinent trouvé dans Weaviate.")
                return "Aucun contexte pertinent trouvé."
                
            print(f"{len(response.objects)} chunks pertinents trouvés.")
            return "\n\n".join([obj.properties.get('contenu', '') for obj in response.objects])
        except Exception as e:
            print(f"Erreur lors de la recherche dans Weaviate: {e}")
            return "Erreur lors de la recherche de contexte."
    
    def _connect_to_weaviate(self):
        try:
            print(f"Connexion à Weaviate sur {self.weaviate_host}:{self.weaviate_port}...")
            self.client = weaviate.connect_to_local(
                host=self.weaviate_host, 
                port=self.weaviate_port, 
                grpc_port=self.grpc_port
            )
            if not self.client.is_ready(): 
                raise RuntimeError("Weaviate n'est pas disponible")
            self.chunks_collection = self.client.collections.get("Chunk")
            print("Connexion à Weaviate réussie.")
        except Exception as e:
            print(f"Erreur de connexion à Weaviate : {e}")
            print("ATTENTION: Weaviate n'est pas disponible. La recherche de contexte ne fonctionnera pas.")
            # Ne pas lever l'exception pour permettre au système de continuer sans Weaviate
            self.client = None
            self.chunks_collection = None

    def _get_ia_prompt(self, section: str) -> str:
        try: 
            return self.sections_meta[section]["ia_prompt"]
        except KeyError: 
            raise ValueError(f"Section '{section}' ou son 'ia_prompt' introuvable dans template_structure.")

    def run_generation_tool(self, input_data: Dict[str, str]) -> Dict[str, str]:
        print(f"run_generation_tool appelé avec: {input_data}")
        
        section = input_data.get("section")
        query = input_data.get("query")
        
        if not section or not query: 
            raise ValueError("L'entrée doit contenir 'section' et 'query'.")
        
        print(f"--- Lancement de la génération pour la section: '{section}' ---")
        print(f"Query: {query}")
        
        ia_prompt = self._get_ia_prompt(section)
        
        # Recherche du contexte si Weaviate est disponible
        if self.chunks_collection is not None:
            context = self._search_chunks(query)
        else:
            context = "Aucun contexte disponible (Weaviate non connecté)."
            print("Génération sans contexte Weaviate.")
        
        generated_content = self._call_llm(query, context, ia_prompt)
        
        return {section: generated_content}

    def _call_llm(self, question: str, context: str, ia_prompt: str) -> str:
        print("Appel au LLM pour génération de contenu...")
        
        full_prompt = (
    f"{ia_prompt}\n\n"
    "Vous êtes un assistant expert chargé de rédiger UNE RÉPONSE STRICTEMENT EN HTML VALIDE, "
    "destinée à être intégrée directement dans un document (sans texte libre en dehors des balises).\n\n"
    "<CONTEXT_START>\n"
    f"{context}\n"
    "<CONTEXT_END>\n\n"
    "<USER_REQUEST>\n"
    f"{question}\n"
    "<END_USER_REQUEST>\n\n"
    "Consignes de mise en forme (strictement HTML) :\n"
    "  • Utilisez uniquement <h4> à <h6> pour les titres et sous-titres (pas de <h1> ni <h2>).\n"
    "  • Encapsulez chaque paragraphe dans un <p>.\n"
    "  • Pour les listes, employez <ul> ou <ol> avec des <li>.\n"
    "  • Pour les données tabulaires, construisez un <table> comportant <thead>, <tbody>, <tr>, <th> et <td>.\n"
    "  • Ne sortez jamais du balisage HTML : toute la réponse doit être comprise entre les balises générées.\n\n"
    "Consignes de contenu :\n"
    "  1. Ne conservez que les éléments du contexte pertinents pour la question.\n"
    "  2. Copiez uniquement ce qui répond directement à la requête.\n"
    "  3. Reformulez ou synthétisez si nécessaire pour améliorer la clarté.\n"
    "  4. Encadrez toute citation du contexte dans un <blockquote> ou un <em>.\n\n"
    "Réponse (uniquement HTML) :\n"
)

        
        headers = {"Authorization": f"Bearer {API_KEY}"}
        payload = {
            "model": MODEL_NAME, 
            "messages": [{"role": "user", "content": full_prompt}]
        }
        
        try:
            response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
            print("Génération LLM réussie.")
            return content
        except requests.RequestException as e:
            print(f"Erreur lors de l'appel au LLM: {e}")
            return f"<p><b>Erreur de génération.</b> ({e})</p>"

# --- BLOC DE TEST (OPTIONNEL) ---
if __name__ == '__main__':
    
    TEMPLATE_FILE_PATH = r"C:\Users\DHM\Downloads\projetF\Backend1\templates\brief-001.json"
    
    print(f"Le fichier principal charge le template depuis '{TEMPLATE_FILE_PATH}'...")
    try:
        with open(TEMPLATE_FILE_PATH, 'r', encoding='utf-8') as f:
            template_structure = json.load(f)
        print("Template chargé avec succès.")
    except Exception as e:
        print(f"Erreur: Impossible de charger le fichier template. {e}")
        # Utiliser une structure de test par défaut
        template_structure = {
            "introduction": {
                "contenu_initiale": "Introduction du projet",
                "contenu": "{{ introduction }}",
                "ia_prompt": "Rédige une introduction pour ce projet."
            }
        }
        print("Utilisation d'une structure de template par défaut pour le test.")

    try:
        # L'outil est maintenant créé sans l'argument model_path.
        advisor = Generationtoll(
            sections_meta=template_structure 
        )

        user_input = {
            "section": "introduction",
            "query": "L'impact de l'IA sur le marché du travail"
        }
        final_result = advisor.run_generation_tool(user_input)

        print("\n--- JSON de Sortie Final ---")
        print(json.dumps(final_result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"\nUne erreur est survenue lors de l'exécution : {e}")