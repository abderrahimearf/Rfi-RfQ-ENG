#!/usr/bin/env python3
# test_agent_advisor.py

import json

from serchtool import  AgentAdvisorTool
# JSON statique des métadonnées
sections_meta = {
    "client": {
        "contenu_initiale": "Nom ou organisation pour laquelle le projet est réalisé",
        "contenu": "{{ client }}",
        "ia_prompt": "Quel est le nom du client ou de l’organisation concernée par ce projet ?"
    },
    "project": {
        "contenu_initiale": "Titre ou nom du projet",
        "contenu": "{{ project }}",
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
        "ia_prompt": "Rédige une introduction pour un projet en précisant le planing en détaille."
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

# JSON d'entrée pour le test
user_input = {
    "section": "introduction",
    "query": "le planing Planning Prévisionnel de la proposition de solution technique"
}

def main():
    # 1) Instanciation de l’outil
    tool = AgentAdvisorTool(
        template_id="brief-001",
        sections_meta=sections_meta,
        model_path="./models/intfloat_multilingual-e5-small"
    )

    # 2) Chargement des embeddings et connexion Weaviate
    if not tool.initialize():
        print("❌ Échec de l'initialisation, vérifiez le modèle et Weaviate")
        return

    # 3) Génération de la section demandée
    section = user_input["section"]
    query   = user_input["query"]
    print(f"➡️  Génération de la section '{section}' pour la requête :\n   {query}\n")
    resultat = tool.generate_section(section, query)

    # 4) Affichage du résultat
    print("===== Résultat généré =====")
    print(resultat)
    print("===========================\n")

    # 5) Injection dans le template
    tool.inject(section, resultat)
    print(f"✅ Contenu injecté dans la section '{section}' du template")

    # 6) Export en PDF de test
    output_pdf = "test_brief_001.pdf"
    # Si votre classe n’a pas de méthode export_pdf, faites :
    tool.templatemanager.export_as_pdf(output_pdf)
    print(f"📄 PDF de test généré : {output_pdf}")

if __name__ == "__main__":
    main()
