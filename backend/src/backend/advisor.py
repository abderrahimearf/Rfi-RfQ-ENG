import os
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from typing import Dict, Any
import json

# --- Configuration API OpenRouter + DeepSeek ---
# Masquer la clé API dans les variables d'environnement pour la sécurité
API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
MODEL_NAME = "deepseek/deepseek-r1"  # Modèle mis à jour
OPENROUTER_API_URL = "https://openrouter.ai/api/v1"

# Créer LLM compatible OpenAI mais connecté à OpenRouter
llm = ChatOpenAI(
    model=MODEL_NAME,
    base_url=OPENROUTER_API_URL,
    api_key=API_KEY,
    temperature=0,  # Temperature à 0 pour plus de consistance
    max_tokens=2000,
    request_timeout=60,
    # Paramètres pour améliorer la consistance du format de sortie
    model_kwargs={
        "stop": ["Observation:", "\nObservation"],
        "frequency_penalty": 0,
        "presence_penalty": 0
    }
)

# --- Tools (fonctions avec logique et validation améliorées) ---

def analyse_ventes(input_str: str) -> str:
    """Analyse les ventes mensuelles avec validation robuste."""
    try:
        # Nettoyage de l'input
        input_str = input_str.strip()
        
        # Si l'input n'est pas du JSON, essayer de l'extraire
        if not input_str.startswith('{'):
            # Rechercher un nom de mois dans le texte
            mois_possibles = ["janvier", "février", "mars", "avril", "mai", "juin", 
                            "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
            mois_trouve = None
            for mois in mois_possibles:
                if mois.lower() in input_str.lower():
                    mois_trouve = mois
                    break
            
            if mois_trouve:
                input_str = json.dumps({"mois": mois_trouve})
            else:
                return "Erreur: Aucun mois identifié. Mentionnez un mois (ex: juin, janvier...)"
        
        data = json.loads(input_str)
        mois = data.get("mois", "").lower()
        
        if not mois:
            return "Erreur: Mois manquant. Format: {\"mois\": \"juin\"}"
        
        # Base de données des ventes mensuelles
        ventes_mensuelles = {
            "janvier": 8000, "février": 4500, "mars": 6200, "avril": 5800,
            "mai": 7200, "juin": 3000, "juillet": 4800, "août": 5200,
            "septembre": 6800, "octobre": 7800, "novembre": 9200, "décembre": 15000
        }
        
        total = ventes_mensuelles.get(mois, 0)
        
        if total == 0:
            return f"Erreur: Données indisponibles pour {mois}"
        
        # Analyse simple
        if total < 5000:
            return f"Ventes de {mois.capitalize()}: {total:,}€ - FAIBLES (alerte)"
        elif total < 8000:
            return f"Ventes de {mois.capitalize()}: {total:,}€ - MOYENNES"
        else:
            return f"Ventes de {mois.capitalize()}: {total:,}€ - EXCELLENTES"
        
    except json.JSONDecodeError:
        return "Erreur: Format JSON invalide"
    except Exception as e:
        return f"Erreur analyse_ventes: {str(e)}"

def generer_rapport(input_str: str) -> str:
    """Génère un rapport formaté."""
    try:
        data = json.loads(input_str)
        titre = data.get("titre", "Rapport Mensuel")
        contenu = data.get("contenu", "Aucun contenu fourni")
        
        return f"Rapport: {titre} - {contenu}"
        
    except Exception as e:
        return f"Erreur génération rapport: {str(e)}"


def conseiller_ventes(input_str: str) -> str:
    """Fournit des conseils personnalisés selon la situation."""
    try:
        data = json.loads(input_str)
        mois = data.get("mois", "ce mois")
        niveau = data.get("niveau", "faible")
        
        if niveau == "faible":
            return f"Conseils pour {mois}: Lancer promotions urgentes, relancer clients inactifs, partenariats locaux"
        elif niveau == "moyen":
            return f"Conseils pour {mois}: Augmenter budget marketing, programmes fidélité, tester nouveaux messages"
        else:
            return f"Conseils pour {mois}: Explorer nouveaux marchés, recruter commerciaux, optimiser processus"
        
    except Exception as e:
        return f"Erreur conseiller_ventes: {str(e)}"


# --- Déclaration des outils pour l'agent ---
tools = [
    Tool(
        name="AnalyseVentes",
        func=analyse_ventes,
        description="Analyze monthly sales data. Input format: {\"mois\": \"january\"} or {\"mois\": \"juin\"}"
    ),
    Tool(
        name="GenererRapport", 
        func=generer_rapport,
        description="Generate a formatted report. Input format: {\"titre\": \"title\", \"contenu\": \"content\"}"
    ),
    Tool(
        name="ConseillerVentes",
        func=conseiller_ventes,
        description="Provide sales advice based on performance level. Input format: {\"mois\": \"month\", \"niveau\": \"faible|moyen|bon\"}"
    ),
]

# --- Prompt template pour l'agent ---
template = """You are a highly accurate and disciplined commercial assistant.
You are ONLY allowed to answer questions about sales if you have used a TOOL to get the data.
Never guess. Never assume. You must be precise.

You have access to the following tools to answer sales-related questions:

TOOLS:
{tools}

RULES:
- You MUST always follow the Thought/Action/Observation protocol exactly.
- You MUST use one of the tools listed above to get any numeric or factual data.
- You are NOT allowed to invent numbers or summaries — use tool outputs only.
- If the question lacks required input (like the month), ask for clarification.

Use the following format EXACTLY:

Thought: I need to think about what to do
Action: [one of {tool_names}]
Action Input: [valid JSON input for the tool]
Observation: [result from the tool must use to genrate the reponse]

Final Answer: [your response to the human]

Begin!

Question: {input}
{agent_scratchpad}
"""

prompt = PromptTemplate.from_template(template)

# --- Création de l'agent avec la nouvelle API ---
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True,
    max_iterations=5,
    handle_parsing_errors=True,
    return_intermediate_steps=True,
    early_stopping_method="generate"
)

# --- État pour LangGraph ---
class AgentState(dict):
    message: str
    response: str = ""

# --- LangGraph : nœud principal ---
def advisor_node(state: AgentState) -> Dict[str, Any]:
    """Nœud principal de l'agent advisor."""
    try:
        user_input = state["message"]
        result = agent_executor.invoke({"input": user_input})
        
        # Extraction de la réponse
        response = result.get("output", "Aucune réponse générée")
        
        return {
            **state,
            "response": response
        }
        
    except Exception as e:
        error_msg = f"❌ Erreur dans advisor_node: {str(e)}"
        return {
            **state, 
            "response": error_msg
        }

# --- Construction du graphe ---
workflow = StateGraph(AgentState)
workflow.add_node("advisor", advisor_node)
workflow.set_entry_point("advisor")
workflow.add_edge("advisor", END)

app = workflow.compile()

# --- Interface utilisateur améliorée ---
def main():
    print("🤖 === ASSISTANT ADVISOR COMMERCIAL ===")
    print("💡 Je peux analyser vos ventes, générer des rapports et donner des conseils")
    print("📝 Exemples: 'Analyse juin', 'Conseils pour février', 'Rapport mensuel'")
    print("⌨️  Tapez 'aide' pour plus d'infos ou 'q' pour quitter\n")
    
    while True:
        try:
            question = input("🧾 Votre question: ").strip()
            
            if question.lower() in ['q', 'quit', 'quitter']:
                print("👋 Au revoir et bonne vente!")
                break
                
            if question.lower() in ['aide', 'help', 'h']:
                print("""
📚 === GUIDE D'UTILISATION ===

🔍 ANALYSES:
  • "Analyse juin" - Analyser les ventes d'un mois
  • "Comment ça va en février?" - Statut des ventes
  
📊 RAPPORTS:
  • "Génère un rapport pour Q1" 
  • "Rapport des ventes de décembre"
  
💡 CONSEILS:
  • "Que faire si les ventes sont faibles?"
  • "Conseils pour améliorer juin"
  
⚡ L'assistant comprend le langage naturel!
                """)
                continue
                
            if not question:
                print("❓ Veuillez poser une question")
                continue
            
            # Exécuter avec LangGraph
            print("🔄 Traitement en cours...")
            result = app.invoke({"message": question})
            
            print(f"\n📌 Réponse:\n{result['response']}")
            
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")
            break
        except Exception as e:
            print(f"❌ Erreur système: {e}")
        
        print("-" * 60)

if __name__ == "__main__":
    main()