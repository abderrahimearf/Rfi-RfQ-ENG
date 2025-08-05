import os
import json
import time
import queue
import threading
import re
import ast

from flask import Flask, jsonify, Response, request
from flask_cors import CORS

# --- Imports pour LangChain ---
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from backend.ContentGeneratorTool import Generationtoll


app = Flask(__name__)
CORS(app)

DATA_DIR = r'C:\Users\DHM\Downloads\projetF\Backend\templates'


template_structure = {
    "client": {
        "contenu_initiale": "Nom ou organisation pour laquelle le projet est réalisé",
        "contenu": "maro data",
        "ia_prompt": "Quel est le nom du client ou de l'organisation concernée par ce projet ?"
    },
    "project": {
        "contenu_initiale": "Titre ou nom du projet",
        "contenu": "contenue ",
        "ia_prompt": "Quel est le nom ou le titre de ce projet ?"
    },
    "submission_time": {
        "contenu_initiale": "Date ou moment de soumission du projet ou du rapport",
        "contenu": "{{ submission_time }}",
        "ia_prompt": "Quand ce projet ou document a-t-il été soumis ?"
    },
    "introduction": {
        "contenu_initiale": "Présentation générale du projet, du contexte et des parties prenantes",
        "contenu": "{{ introduction }}",
        "ia_prompt": "Rédige une introduction pour un projet en précisant le contexte et les acteurs concernés."
    },
    "problematique": {
        "contenu_initiale": "Problème principal que le projet tente de résoudre",
        "contenu": "{{ problematique }}",
        "ia_prompt": "Quelle est la problématique principale que ce projet cherche à résoudre ?"
    },
    "objectifs_et_attentes": {
        "contenu_initiale": "Objectifs spécifiques du projet et les résultats attendus",
        "contenu": "{{ objectifs_et_attentes }}",
        "ia_prompt": "Quels sont les objectifs du projet et les attentes en termes de résultats ?"
    }
}


class MessageAnnouncer:
    def __init__(self):
        self.listeners = []

    def listen(self):
        q = queue.Queue(maxsize=5)
        self.listeners.append(q)
        return q

    def announce(self, msg):
        for i in reversed(range(len(self.listeners))):
            try:
                self.listeners[i].put_nowait(msg)
            except queue.Full:
                del self.listeners[i]

announcer = MessageAnnouncer()


def clean_json_input(input_str):
    """Nettoie et parse une entrée JSON de différentes formes."""
    if isinstance(input_str, dict):
        return input_str
    
   
    input_str = str(input_str).strip()
    
  
    if input_str.startswith('{\\') and not input_str.startswith('"{'):
        input_str = input_str.replace('\\', '')
    
 
    if (input_str.startswith("'") and input_str.endswith("'")) or \
       (input_str.startswith('"') and input_str.endswith('"')):
        input_str = input_str[1:-1]
    
    input_str = input_str.replace('\\"', '"')
    input_str = input_str.replace("\\'", "'")
    
  
    try:
        return json.loads(input_str)
    except json.JSONDecodeError:
     
        try:
            
            if input_str.startswith('{') and input_str.endswith('}'):
               
                import ast
                return ast.literal_eval(input_str)
        except:
            pass
        raise ValueError(f"Impossible de parser le JSON: {input_str}")

# --- DÉFINITION DES OUTILS POUR L'AGENT ---

def generationcontenu(user_input_str: str) -> str:
    """
    Outil pour générer le contenu d'une section. Accepte une chaîne JSON en entrée.
    Exemple d'entrée: '{{"section": "introduction", "query": "L'IA et le futur"}}'
    """
    print(f"TOOL 'generationcontenu' appelé avec: {user_input_str}")
    print(f"Type de l'entrée: {type(user_input_str)}")
    
    try:
        # CORRECTION: Vérifier si l'entrée est déjà un dictionnaire
        if isinstance(user_input_str, dict):
            user_input = user_input_str
        else:
            # Essayer plusieurs approches de nettoyage
            original_str = user_input_str
            
            # Approche 1: Si la chaîne commence par {\" sans guillemet d'ouverture
            if user_input_str.startswith('{\\') and not user_input_str.startswith('"{'):
                user_input_str = '"' + user_input_str
            
            # Approche 2: Si entouré de guillemets
            if user_input_str.startswith('"') and user_input_str.endswith('"'):
                user_input_str = user_input_str[1:-1]
            
            # Approche 3: Remplacer les échappements
            user_input_str = user_input_str.replace('\\"', '"')
            
            # Approche 4: Si ça ne marche toujours pas, essayer de nettoyer différemment
            try:
                user_input = json.loads(user_input_str)
            except json.JSONDecodeError:
                # Tentative finale: reconstruire le JSON proprement
                if "section" in original_str and "query" in original_str:
                    # Extraire les valeurs avec une regex simple
                    import re
                    section_match = re.search(r'"section"\s*:\s*"([^"]+)"', original_str)
                    query_match = re.search(r'"query"\s*:\s*"([^"]+)"', original_str)
                    
                    if section_match and query_match:
                        user_input = {
                            "section": section_match.group(1),
                            "query": query_match.group(1)
                        }
                    else:
                        raise ValueError("Impossible d'extraire section et query")
                else:
                    raise ValueError("Format JSON invalide")
            
            print(f"Chaîne nettoyée: {user_input_str}")
        
        print(f"Dictionnaire parsé: {user_input}")
      
        tool1 = Generationtoll(
            sections_meta=template_structure
        )
     
        raw_content = tool1.run_generation_tool(user_input)
        
     
        section_name = list(raw_content.keys())[0]
        html_content = raw_content[section_name]
        
        formatted_content_to_send = {
            section_name: {"contenu": html_content}
        }
        
      
        announcer.announce(msg=json.dumps(formatted_content_to_send))
    
        return "Action effectuée avec succès."
    except json.JSONDecodeError as e:
        print(f"Erreur JSONDecodeError: {e}")
        print(f"Chaîne reçue: '{user_input_str}'")
        return "Erreur : L'entrée n'est pas un JSON valide."
    except Exception as e:
        print(f"Erreur générale: {e}")
        return f"Erreur lors de l'exécution de l'outil de génération : {e}"

def directinjection(user_input_str: str) -> str:
    """
    Outil pour injecter directement du contenu. Accepte une chaîne JSON en entrée.
    Exemple d'entrée: '{{"problematique": {{"contenu": "Le nouveau contenu"}}}}'
    """
    print(f"TOOL 'directinjection' appelé avec: {user_input_str}")
    print(f"Type de l'entrée: {type(user_input_str)}")
    
    try:
   
        content_to_send = clean_json_input(user_input_str)
        print(f"Contenu à envoyer: {content_to_send}")
        

        announcer.announce(msg=json.dumps(content_to_send))
        
        return "Action effectuée avec succès."
        
    except Exception as e:
        print(f"Erreur: {e}")
        print(f"Entrée reçue: '{user_input_str}'")
        return f"Erreur lors de l'injection directe : {e}"

tools = [
    Tool(
        name="generation_de_contenu",
        func=generationcontenu,
        description="""Utilisé pour générer le contenu d'une section spécifique. L'entrée doit être un JSON sous forme de chaîne contenant "section" et "query". Exemple: {{"section": "introduction", "query": "L'impact de l'IA"}}"""
    ),
    Tool(
        name="injection_directe",
        func=directinjection,
        description="""Utilisé pour injecter directement du contenu dans une section. L'entrée doit être un JSON sous forme de chaîne. Exemple: {{"client": {{"contenu": "Nom du Client"}}}}"""
    ),
]


API_KEY = os.getenv("OPENROUTER_API_KEY", "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")

MODEL_NAME = "openai/gpt-3.5-turbo"  # ou "anthropic/
OPENROUTER_API_URL = "https://openrouter.ai/api/v1"

llm = ChatOpenAI(
    model=MODEL_NAME,
    base_url=OPENROUTER_API_URL,
    api_key=API_KEY,
    temperature=0,
    max_tokens=500,
    request_timeout=120,  # Augmenter le timeout
    stop=["Observation:", "\nObservation"],
    model_kwargs={"frequency_penalty": 0, "presence_penalty": 0}
)


prompt_template = """
Vous êtes un assistant IA qui aide à remplir un document en utilisant des outils.
Répondez aux questions de l'utilisateur en utilisant les outils à votre disposition.

Outils disponibles:
{tools}

Pour utiliser un outil, utilisez le format suivant STRICTEMENT :

```
Thought: Dois-je utiliser un outil ? Oui.
Action: Le nom de l'outil à utiliser, qui doit être l'un des suivants : [{tool_names}]
Action Input: L'entrée de l'outil sous forme JSON.
```

IMPORTANT: Pour Action Input, écrivez directement le JSON.
Format attendu pour generation_de_contenu: Un objet JSON avec les clés "section" et "query"
Format attendu pour injection_directe: Un objet JSON avec la structure de contenu à injecter

Après avoir reçu une `Observation` d'un outil, ne j'amis  produire une nouvelle pensée (`Thought:`).
.

Lorsque vous avez une réponse finale à donner à l'utilisateur, ou si vous n'avez pas besoin d'utiliser un outil, utilisez le format suivant :
```
Thought: Dois-je utiliser un outil ? Non.
Final Answer: [votre réponse finale ici]
```

Commencez !

Question: {input}
{agent_scratchpad}
"""
prompt = PromptTemplate.from_template(prompt_template)

agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=5,  # Limiter le nombre d'itérations
    return_intermediate_steps=False  
)


@app.route('/api/templates-files', methods=['GET'])
def list_templates():
    """Retourne la liste des fichiers .html dans le dossier."""
    try:
        files = [f for f in os.listdir(DATA_DIR) if f.endswith('.html')]
        return jsonify({'templates': files})
    except Exception as e:
        return jsonify({'error': f'Impossible de lister les templates: {e}'}), 500

@app.route('/api/documents/<path:filename>', methods=['GET'])
def serve_document_and_json(filename):
    """Sert le fichier HTML et son JSON correspondant."""
    try:
        html_path = os.path.join(DATA_DIR, filename)
        json_path = os.path.join(DATA_DIR, filename.replace('.html', '.json'))

        with open(html_path, 'r', encoding='utf-8') as f_html:
            html_content = f_html.read()
        with open(json_path, 'r', encoding='utf-8') as f_json:
            json_data = json.load(f_json)
        
     
        return jsonify({"html": html_content, "jsonData": json_data})

    except FileNotFoundError:
        return jsonify({'error': 'Fichier HTML ou JSON non trouvé'}), 404
    except Exception as e:
        return jsonify({'error': f'Une erreur est survenue: {e}'}), 500

@app.route('/stream')
def stream():
    def generate():
        q = announcer.listen()
        while True:
            msg = q.get()
            yield f"data: {msg}\n\n"
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')

    if not user_message:
        return jsonify({"error": "Message vide"}), 400

    try:
        def run_agent():
            response = agent_executor.invoke({"input": user_message})
            
            if response.get("output"):
                print(f"Advisor Final Answer: {response['output']}")

        threading.Thread(target=run_agent).start()
        
        return jsonify({"status": "La requête a été prise en charge par l'agent."})

    except Exception as e:
        return jsonify({"error": f"Erreur de l'agent : {e}"}), 500


if __name__ == '__main__':
    print("Serveur Python démarré sur http://localhost:5000")
    app.run(port=5000, threaded=True, debug=True)