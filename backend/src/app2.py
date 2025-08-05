import os
import json
import time
import queue
import threading
import re
import ast
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from cerebras.cloud.sdk import Cerebras

# --- Imports de vos outils (inchangés) ---
from backend.ContentGeneratorTool import Generationtoll

# --- CONFIGURATION DE L'APPLICATION ---
app = Flask(__name__)
CORS(app)

DATA_DIR = r'C:\Users\DHM\Downloads\projetF\Backend\templates'

# --- CONFIGURATION DE CEREBRAS ---
# Mettez votre clé API Cerebras ici ou dans les variables d'environnement
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY", "votre_clé_api_cerebras_ici")
CEREBRAS_MODEL = "qwen-3-235b-a22b-thinking-2507"

client = None
if CEREBRAS_API_KEY != "votre_clé_api_cerebras_ici":
    client = Cerebras(api_key=CEREBRAS_API_KEY)
    print("Client Cerebras initialisé avec succès.")
else:
    print("ATTENTION : La clé API Cerebras n'est pas configurée.")

# --- STRUCTURE DU TEMPLATE (INCHANGÉE) ---
template_structure = {
    "client": {"contenu_initiale": "Nom du client", "contenu": "maro data", "ia_prompt": "Quel est le nom du client ?"},
    "project": {"contenu_initiale": "Titre du projet", "contenu": "contenue ", "ia_prompt": "Quel est le nom du projet ?"},
    "submission_time": {"contenu_initiale": "Date de soumission", "contenu": "{{ submission_time }}", "ia_prompt": "Quand ce projet a-t-il été soumis ?"},
    "introduction": {"contenu_initiale": "Présentation générale", "contenu": "{{ introduction }}", "ia_prompt": "Rédige une introduction."},
    "problematique": {"contenu_initiale": "Problème principal", "contenu": "{{ problematique }}", "ia_prompt": "Quelle est la problématique ?"},
    "objectifs_et_attentes": {"contenu_initiale": "Objectifs et résultats attendus", "contenu": "{{ objectifs_et_attentes }}", "ia_prompt": "Quels sont les objectifs ?"}
}

# --- SYSTÈME D'ANNONCE SSE (INCHANGÉ) ---
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

# --- DÉFINITION DES OUTILS (LOGIQUE INCHANGÉE) ---
def generationcontenu(user_input_str: str) -> str:
    """
    Outil pour générer le contenu d'une section. Accepte une chaîne JSON en entrée.
    Exemple d'entrée: '{{"section": "introduction", "query": "L'IA et le futur"}}'
    """
    print(f"TOOL 'generationcontenu' appelé avec: {user_input_str}")
    try:
        # Le parsing a été simplifié car le modèle 'thinking' est plus fiable
        user_input = ast.literal_eval(user_input_str) if isinstance(user_input_str, str) else user_input_str
        
        tool1 = Generationtoll(sections_meta=template_structure)
        raw_content = tool1.run_generation_tool(user_input)
        
        section_name = list(raw_content.keys())[0]
        html_content = raw_content[section_name]
        
        formatted_content_to_send = {section_name: {"contenu": html_content}}
        announcer.announce(msg=json.dumps(formatted_content_to_send))
        return "Action effectuée avec succès. Le contenu a été généré et envoyé au client."
    except Exception as e:
        print(f"Erreur dans 'generationcontenu': {e}")
        return f"Erreur lors de l'exécution de l'outil de génération : {e}"

def directinjection(user_input_str: str) -> str:
    """
    Outil pour injecter directement du contenu. Accepte une chaîne JSON en entrée.
    Exemple d'entrée: '{{"problematique": {{"contenu": "Le nouveau contenu"}}}}'
    """
    print(f"TOOL 'directinjection' appelé avec: {user_input_str}")
    try:
        content_to_send = ast.literal_eval(user_input_str) if isinstance(user_input_str, str) else user_input_str
        announcer.announce(msg=json.dumps(content_to_send))
        return "Action effectuée avec succès. Le contenu a été injecté."
    except Exception as e:
        print(f"Erreur dans 'directinjection': {e}")
        return f"Erreur lors de l'injection directe : {e}"

# --- MAPPING DES OUTILS POUR L'AGENT ---
tools = {
    "generation_de_contenu": {
        "func": generationcontenu,
        "description": "Utilisé pour générer le contenu d'une section spécifique. L'entrée doit être un dictionnaire Python avec les clés 'section' et 'query'."
    },
    "injection_directe": {
        "func": directinjection,
        "description": "Utilisé pour injecter directement du contenu dans une section. L'entrée doit être un dictionnaire Python représentant la structure du contenu à injecter."
    }
}

# --- NOUVELLE LOGIQUE DE L'AGENT AVEC CEREBRAS ---
def run_cerebras_agent(user_message):
    if not client:
        print("Agent non exécuté car le client Cerebras n'est pas initialisé.")
        return

    print(f"\n--- DÉBUT DE LA SESSION DE L'AGENT POUR : '{user_message}' ---")
    
    # Création du prompt système dynamique
    tool_descriptions = "\n".join([f"- {name}: {details['description']}" for name, details in tools.items()])
    system_prompt = f"""
Tu es un assistant IA expert qui aide à remplir un document en utilisant des outils.
Réponds aux questions de l'utilisateur en utilisant les outils à ta disposition.

Outils disponibles:
{tool_descriptions}

Ton processus de décision est le suivant, en boucle:
1. **Thought**: Analyse la demande et décide si un outil est nécessaire.
2. **Action**: Si un outil est nécessaire, écris le nom de l'outil à utiliser.
3. **Action Input**: Écris l'entrée de l'outil sous forme de dictionnaire Python.
4. Si aucun outil n'est nécessaire, réponds directement à l'utilisateur avec "Final Answer: [ta réponse]".

Exemple d'appel d'outil:
Thought: L'utilisateur veut générer l'introduction. Je dois utiliser l'outil 'generation_de_contenu'.
Action: generation_de_contenu
Action Input: {{"section": "introduction", "query": "L'impact de l'IA sur la société"}}

Après l'appel, tu recevras une 'Observation'. Analyse-la et continue le processus.
"""
    
    history = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    max_iterations = 5
    for i in range(max_iterations):
        print(f"\n--- Itération {i+1} ---")
        
        try:
            response = client.chat.completions.create(
                model=CEREBRAS_MODEL,
                messages=history,
                temperature=0.0,
                stop=["Observation:"] # Arrête la génération avant l'observation
            )
            response_text = response.choices[0].message.content
            print(f"Réponse du modèle:\n{response_text}")
            history.append({"role": "assistant", "content": response_text})

            # Analyse de la réponse
            if "Final Answer:" in response_text:
                final_answer = response_text.split("Final Answer:")[-1].strip()
                print(f"--- FIN DE LA SESSION DE L'AGENT --- \nRéponse finale: {final_answer}")
                break

            action_match = re.search(r"Action:\s*(\w+)", response_text)
            action_input_match = re.search(r"Action Input:\s*({.*})", response_text, re.DOTALL)

            if action_match and action_input_match:
                action = action_match.group(1).strip()
                action_input = action_input_match.group(1).strip()
                
                if action in tools:
                    tool_func = tools[action]["func"]
                    observation = tool_func(action_input)
                    print(f"Observation de l'outil '{action}': {observation}")
                    history.append({"role": "tool", "content": f"Observation: {observation}"})
                else:
                    history.append({"role": "tool", "content": f"Observation: Erreur, l'outil '{action}' n'existe pas."})
            else:
                print("Le modèle n'a pas suivi le format Action/Action Input. Fin de la session.")
                break
        except Exception as e:
            print(f"Erreur durant l'itération de l'agent: {e}")
            break
    else:
        print("Nombre maximum d'itérations atteint.")

# --- ROUTES DE L'API FLASK (INCHANGÉES SAUF /api/chat) ---

@app.route('/api/templates-files', methods=['GET'])
def list_templates():
    try:
        files = [f for f in os.listdir(DATA_DIR) if f.endswith('.html')]
        return jsonify({'templates': files})
    except Exception as e:
        return jsonify({'error': f'Impossible de lister les templates: {e}'}), 500

@app.route('/api/documents/<path:filename>', methods=['GET'])
def serve_document_and_json(filename):
    try:
        html_path = os.path.join(DATA_DIR, filename)
        json_path = os.path.join(DATA_DIR, filename.replace('.html', '.json'))
        with open(html_path, 'r', encoding='utf-8') as f_html:
            html_content = f_html.read()
        with open(json_path, 'r', encoding='utf-8') as f_json:
            json_data = json.load(f_json)
        return jsonify({"html": html_content, "jsonData": json_data})
    except FileNotFoundError:
        return jsonify({'error': 'Fichier non trouvé'}), 404
    except Exception as e:
        return jsonify({'error': f'Erreur: {e}'}), 500

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

    # Lancer le nouvel agent Cerebras dans un thread
    threading.Thread(target=run_cerebras_agent, args=(user_message,)).start()
    return jsonify({"status": "La requête a été prise en charge par l'agent Cerebras."})

# --- DÉMARRAGE DU SERVEUR ---
if __name__ == '__main__':
    print("Serveur Python démarré sur http://localhost:5000")
    if client:
        print(f"Connecté à Cerebras et utilisant le modèle : {CEREBRAS_MODEL}")
    app.run(port=5000, threaded=True, debug=False)
