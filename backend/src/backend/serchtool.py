import json
from typing import List, Dict, Any
import requests
from sentence_transformers import SentenceTransformer
import weaviate
from template_manager_tool import TemplateManagerTool

API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-r1-0528:free"

class AgentAdvisorTool:
    def __init__(
        self,
        template_id: str,
        sections_meta: Dict[str, Dict[str, str]],
        model_path: str,
        weaviate_host: str = "localhost",
        weaviate_port: int = 8080,
        grpc_port: int = 50051
    ):
        self.template_id = template_id
        self.sections_meta = sections_meta
        self.model_path = model_path
        self.weaviate_host = weaviate_host
        self.weaviate_port = weaviate_port
        self.grpc_port = grpc_port
        self.templatemanager = TemplateManagerTool(template_id)

    def initialize(self) -> bool:
        """Charge le modèle et connecte à Weaviate."""
        try:
            print("Chargement du modèle d'embeddings…")
            self.model = SentenceTransformer(self.model_path)

            print("Connexion à Weaviate…")
            self.client = weaviate.connect_to_local(
                host=self.weaviate_host,
                port=self.weaviate_port,
                grpc_port=self.grpc_port
            )
            if not self.client.is_ready():
                raise RuntimeError("Weaviate n’est pas disponible")
            self.chunks_collection = self.client.collections.get("Chunk")
            print("Initialisation réussie.")
            return True
        except Exception as e:
            print(f"Erreur d'initialisation : {e}")
            return False

    def get_ia_prompt(self, section: str) -> str:
        """Retourne le ia_prompt pour la section donnée."""
        meta = self.sections_meta.get(section)
        if not meta:
            raise KeyError(f"Section '{section}' introuvable dans sections_meta")
        return meta["ia_prompt"]

    def search_chunks(self, question: str, limit: int = 2) -> List[Dict[str, Any]]:
        """Recherche vectorielle dans Weaviate et retourne jusqu’à `limit` chunks."""
        question_vector = self.model.encode(question).tolist()
        response = self.chunks_collection.query.near_vector(
            near_vector=question_vector,
            limit=limit,
            include_vector=False
        )

        chunks: List[Dict[str, Any]] = []
        for i, chunk in enumerate(response.objects):
            score = 0.9 - (i * 0.1)
            chunk_data = {
                'text':   chunk.properties.get('contenu', ''),
                'page':   chunk.properties.get('page', 0),
                'source': chunk.properties.get('source', ''),
                'score':  score
            }
            chunks.append(chunk_data)
        if chunks:
            print("les passages  trouvées")
        return chunks

    def call_deepseek(
        self,
        question: str,
        passages: List[Dict[str, Any]],
        ia_prompt: str
    ) -> str:
        """Envoie le prompt + contexte à DeepSeek via OpenRouter et renvoie la réponse."""
        context = "\n\n".join(
            f"— Source: {p['source']} (page {p['page']}, score {p['score']:.4f})\n{p['text']}"
            for p in passages
        )
        full_prompt = (
    # Instruction système ou prompt initial
    f"{ia_prompt}\n\n"
    "Vous êtes un assistant expert chargé de rédiger une réponse HTML structurée.\n\n"
    f"<CONTEXT_START>\n{context}\n<CONTEXT_END>\n\n"
    f"<USER_REQUEST>\n{question}\n<END_USER_REQUEST>\n\n"
    "Consignes de mise en forme (strictement HTML) :\n"
    "  • Utilisez <h3>→<h6> pour les titres et sous-titres selon la hiérarchie.\n"
    "  • Chaque idée principale doit être dans un <p> (paragraphe).\n"
    "  • Si vous énumérez plusieurs points, utilisez <ul> ou <ol> avec <li>.\n"
    "  • Si vous présentez des données tabulaires, construisez un <table> avec <thead>, <tbody>, <tr>, <th>, <td>.\n"
    "  • Ne sortez jamais du balisage HTML : toute la réponse doit être comprise entre les balises que vous générez.\n\n"

    # Consignes de contenu
    "Consignes de contenu :\n"
    "  1. Parcourez l’intégralité du contexte fourni et identifiez uniquement les éléments pertinents pour la requête.\n"
    "  2. Ne copiez QUE ce qui est directement lié à la question.\n"
    "  3. Reformulez ou synthétisez si nécessaire pour la clarté.\n"
    "  4. Si vous citez une donnée ou un fait du contexte, encadrez-le d’un élément HTML distinct (ex. <blockquote> ou <em>).\n\n"

    # Marqueur de début de réponse
    "Réponse (uniquement HTML) :\n"
)


        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": "Vous êtes un assistant expert de rédaction."},
                {"role": "user",   "content": full_prompt}
            ],
            "temperature": 0.2,
            "stream": False
        }
        r = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

    def generate_section(self, section: str, query: str) -> str:
        """Récupère le ia_prompt + les chunks + appelle DeepSeek."""
        ia_prompt = self.get_ia_prompt(section)
        passages = self.search_chunks(query, limit=2)
        return self.call_deepseek(query, passages, ia_prompt)

    def inject(self, section: str, content: str) -> None:
        """Injecte le contenu généré dans la section du template."""
        self.templatemanager.inject(section, content)

