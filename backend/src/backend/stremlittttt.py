import streamlit as st
import json
from typing import Dict, Any
import traceback
from template_manager_tool import TemplateManagerTool

# Import de votre classe existante
from serchtool import AgentAdvisorTool

# Configuration de la page
st.set_page_config(
    page_title="Agent Advisor Interface",
    page_icon="🤖",
    layout="wide"
)

# Initialisation des variables de session
if 'agent_tool' not in st.session_state:
    st.session_state.agent_tool = None
if 'is_initialized' not in st.session_state:
    st.session_state.is_initialized = False
if 'sections_meta' not in st.session_state:
    st.session_state.sections_meta = {}
if 'template_id' not in st.session_state:
    st.session_state.template_id = "brief-001"

# Navigation entre les pages
page = st.sidebar.selectbox(
    "🔄 Choisir la page",
    ["👤 Interface Utilisateur", "⚙️ Configuration Admin"],
    help="Interface Utilisateur pour votre encadrant, Configuration pour vous"
)

st.sidebar.markdown("---")

# =====================================
# PAGE INTERFACE UTILISATEUR (ENCADRANT)
# =====================================

if page == "👤 Interface Utilisateur":
    st.title("🤖 Générateur de Contenu IA")
    st.markdown("*Interface simplifiée pour la génération automatique de contenu*")
    
    # Vérification que l'agent est configuré et initialisé
    if not st.session_state.is_initialized or not st.session_state.sections_meta:
        st.error("⚠️ **Configuration requise**")
        st.info("L'administrateur doit d'abord configurer et initialiser l'agent depuis la page 'Configuration Admin'")
        
        # Affichage du statut
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.sections_meta:
                st.success("✅ Sections configurées")
            else:
                st.error("❌ Sections non configurées")
        with col2:
            if st.session_state.is_initialized:
                st.success("✅ Agent initialisé")
            else:
                st.error("❌ Agent non initialisé")
    else:
        # Interface utilisateur principale
        st.success("🟢 **Système prêt** - Vous pouvez générer du contenu")
        
        # Conteneur principal
        with st.container():
            st.markdown("---")
            
            # Section selection et requête côte à côte
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader("📑 Section à traiter")
                
                # Liste des sections disponibles
                sections_list = list(st.session_state.sections_meta.keys())
                selected_section = st.selectbox(
                    "Choisissez la section :",
                    sections_list,
                    help="Sélectionnez la section que vous voulez remplir"
                )
                
                # Affichage des informations de la section
                if selected_section:
                    section_info = st.session_state.sections_meta[selected_section]
                    
                    st.info(f"**Description:**\n{section_info.get('contenu_initiale', 'N/A')}")
                    
                    with st.expander("🤖 Voir le prompt IA", expanded=False):
                        st.write(section_info.get('ia_prompt', 'Aucun prompt défini'))
            
            with col2:
                st.subheader("💬 Votre demande")
                
                user_query = st.text_area(
                    "Décrivez ce que vous voulez générer :",
                    height=150,
                    placeholder="Exemple : Analysez les tendances du marché e-commerce au Maroc en 2024 et rédigez une introduction complète pour notre rapport...",
                    help="Soyez précis sur ce que vous voulez que l'IA génère pour cette section"
                )
                
                # Bouton de génération
                st.markdown("---")
                
                if st.button("🚀 **Générer le Contenu**", type="primary", use_container_width=True):
                    if user_query and selected_section:
                        try:
                            # Processus de génération avec feedback visuel
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            # Étape 1: Recherche
                            status_text.text("🔍 Recherche dans la base de connaissances...")
                            progress_bar.progress(25)
                            passages = st.session_state.agent_tool.search_chunks(user_query, limit=2)
                            
                            # Étape 2: Récupération du prompt
                            status_text.text("🤖 Préparation de la génération IA...")
                            progress_bar.progress(50)
                            section_data = st.session_state.sections_meta.get(selected_section, {})
                            ia_prompt = section_data.get('ia_prompt', f"Générez du contenu pour {selected_section}")
                            
                            # Étape 3: Génération
                            status_text.text("✍️ Génération du contenu par l'IA...")
                            progress_bar.progress(75)
                            generated_content = st.session_state.agent_tool.call_deepseek(
                                question=user_query,
                                passages=passages,
                                ia_prompt=ia_prompt
                            )
                            
                            # Étape 4: Injection
                            status_text.text("💾 Sauvegarde dans le template...")
                            progress_bar.progress(100)
                            st.session_state.agent_tool.inject(selected_section, generated_content)
                            
                            # Nettoyage des éléments de progression
                            progress_bar.empty()
                            status_text.empty()
                            
                            # Affichage du succès
                            st.success(f"✅ **Contenu généré avec succès pour '{selected_section}'!**")
                            
                        except Exception as e:
                            st.error(f"❌ **Erreur lors de la génération:** {e}")
                            with st.expander("🔍 Détails de l'erreur (pour le support technique)"):
                                st.code(traceback.format_exc())
                    else:
                        if not user_query:
                            st.warning("⚠️ Veuillez saisir votre demande")
                        if not selected_section:
                            st.warning("⚠️ Veuillez sélectionner une section")
        
        # Section résultats (si du contenu a été généré)
        if 'generated_content' in locals():
            st.markdown("---")
            st.subheader(f"📋 Résultat pour '{selected_section}'")
            
            # Onglets pour différentes vues
            tab1, tab2 = st.tabs(["👁️ Aperçu", "📝 Code HTML"])
            
            with tab1:
                st.markdown("**Contenu généré et formaté :**")
                st.markdown(generated_content, unsafe_allow_html=True)
            
            with tab2:
                st.markdown("**Code HTML source :**")
                st.code(generated_content, language="html")
        
        # Statistiques en bas
        st.markdown("---")
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        with col_stat1:
            st.metric("📋 Sections", len(st.session_state.sections_meta))
        with col_stat2:
            st.metric("🏷️ Template", st.session_state.template_id)
        with col_stat3:
            if 'passages' in locals():
                st.metric("📄 Sources", len(passages))

# =====================================
# PAGE CONFIGURATION ADMIN
# =====================================

elif page == "⚙️ Configuration Admin":
    st.title("⚙️ Configuration Administrateur")
    st.markdown("*Page de configuration technique - Réservée à l'administrateur*")
    
    # Sidebar pour la configuration
    with st.sidebar:
        st.header("🔧 Paramètres Système")
        
        # Configuration de base
        st.subheader("Paramètres de base")
        template_id = st.text_input("Template ID", value=st.session_state.template_id)
        st.session_state.template_id = template_id
        
        model_path = st.text_input(
            "Modèle d'embeddings", 
            value="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Configuration Weaviate
        st.subheader("Configuration Weaviate")
        weaviate_host = st.text_input("Host", value="localhost")
        weaviate_port = st.number_input("Port", value=8080, min_value=1)
        grpc_port = st.number_input("gRPC Port", value=50051, min_value=1)
    
    # Interface principale de configuration
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📝 Configuration des Sections")
        
        sections_meta_json = st.text_area(
            "JSON de Configuration des Sections :",
            value="""{
  "client": {
    "contenu_initiale": "Nom ou organisation pour laquelle le projet est réalisé",
    "contenu": "{{ client }}",
    "ia_prompt": "Quel est le nom du client ou de l'organisation concernée par ce projet ?"
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
    "ia_prompt": "Rédige uniquement la section Introduction d’un rapport de projet. Cette introduction doit présenter le contexte général du projet ainsi que les acteurs impliqués, sans aborder d'autres parties du rapport (comme la problématique, le budget, les objectifs détaillés, etc.). Le texte rédigé devra être autonome, et rester strictement limité à l’introduction. Ignore toute autre information non liée au contexte ou aux acteurs."
  },
  "problematique": {
    "contenu_initiale": "Problème principal que le projet tente de résoudre",
    "contenu": "{{ problematique }}",
    "ia_prompt": "Rédige uniquement la section Planning d’un rapport de projet. Le texte doit présenter l’organisation temporelle du projet, les différentes phases ou étapes prévues, ainsi que les principales échéances ou livrables attendus. Le style doit rester professionnel et clair utuliser des tableux si besoin  ?"
  },
  "objectifs_et_attentes": {
    "contenu_initiale": "Objectifs spécifiques du projet et les résultats attendus",
    "contenu": "{{ objectifs_et_attentes }}",
    "ia_prompt": "Quels sont les objectifs du projet et les attentes en termes de résultats ?"
  }
}""",
            height=400
        )
        
        # Validation et sauvegarde du JSON
        try:
            sections_meta = json.loads(sections_meta_json)
            st.session_state.sections_meta = sections_meta
            st.success(f"✅ JSON valide - {len(sections_meta)} sections détectées")
            
            if st.button("💾 Sauvegarder Configuration", type="secondary"):
                st.success("✅ Configuration sauvegardée dans la session")
                
        except json.JSONDecodeError as e:
            st.error(f"❌ JSON invalide: {e}")
            sections_meta = {}
    
    with col2:
        st.header("🔧 Initialisation du Système")
        
        # Informations sur la configuration actuelle
        if st.session_state.sections_meta:
            st.success(f"📋 {len(st.session_state.sections_meta)} sections configurées")
            
            with st.expander("📋 Aperçu des sections", expanded=False):
                for section_name, section_data in st.session_state.sections_meta.items():
                    st.write(f"**{section_name}**")
                    st.write(f"- *Description:* {section_data.get('contenu_initiale', 'N/A')}")
                    st.write("---")
        else:
            st.warning("⚠️ Aucune section configurée")
        
        st.markdown("---")
        
        # Bouton d'initialisation
        if st.button("🚀 **Initialiser l'Agent IA**", type="primary", use_container_width=True):
            if st.session_state.sections_meta and template_id and model_path:
                try:
                    with st.spinner("🔄 Initialisation en cours..."):
                        agent_tool = AgentAdvisorTool(
                            template_id=template_id,
                            sections_meta=st.session_state.sections_meta,
                            model_path=model_path,
                            weaviate_host=weaviate_host,
                            weaviate_port=int(weaviate_port),
                            grpc_port=int(grpc_port)
                        )
                        
                        if agent_tool.initialize():
                            st.session_state.agent_tool = agent_tool
                            st.session_state.is_initialized = True
                            st.success("✅ **Agent initialisé avec succès!**")
                            st.info("🎉 L'interface utilisateur est maintenant prête à être utilisée")
                        else:
                            st.error("❌ Échec de l'initialisation de l'agent")
                            
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'initialisation: {e}")
                    with st.expander("🔍 Détails de l'erreur"):
                        st.code(traceback.format_exc())
            else:
                st.warning("⚠️ Veuillez configurer les sections et remplir tous les paramètres")
        
        # Test de l'agent (si initialisé)
        if st.session_state.is_initialized:
            st.markdown("---")
            st.subheader("🧪 Test de l'Agent")
            
            test_query = st.text_input("Requête de test:", "Test de fonctionnement")
            test_section = st.selectbox("Section de test:", list(st.session_state.sections_meta.keys()))
            
            if st.button("🧪 Tester", type="secondary"):
                if test_query and test_section:
                    try:
                        with st.spinner("Test en cours..."):
                            result = st.session_state.agent_tool.generate_section(test_section, test_query)
                            st.success("✅ Test réussi!")
                            st.code(result[:200] + "..." if len(result) > 200 else result)
                    except Exception as e:
                        st.error(f"❌ Test échoué: {e}")
    
    # État du système
    st.markdown("---")
    st.header("📊 État du Système")
    
    col_status1, col_status2, col_status3, col_status4 = st.columns(4)
    
    with col_status1:
        if st.session_state.is_initialized:
            st.success("🟢 Agent Prêt")
        else:
            st.warning("🟡 Non Initialisé")
    
    with col_status2:
        if st.session_state.sections_meta:
            st.success(f"📋 {len(st.session_state.sections_meta)} Sections")
        else:
            st.warning("📋 Pas de Sections")
    
    with col_status3:
        st.info(f"🏷️ {template_id}")
    
    with col_status4:
        if st.session_state.agent_tool:
            st.success("🔗 Weaviate OK")
        else:
            st.warning("🔗 Non Connecté")
    
    # Guide d'utilisation pour l'admin
    with st.expander("📖 Guide d'Utilisation Admin"):
        st.markdown("""
        ### 🔧 **Processus de Configuration:**
        
        1. **📝 Configurez les sections**: Modifiez le JSON selon vos besoins
        2. **💾 Sauvegardez**: Cliquez sur "Sauvegarder Configuration"  
        3. **🚀 Initialisez**: Cliquez sur "Initialiser l'Agent IA"
        4. **🧪 Testez**: Utilisez la section de test pour vérifier
        5. **👤 Basculez**: Allez sur "Interface Utilisateur" - c'est prêt !
        
        ### ⚠️ **Points Important:**
        - Weaviate doit être démarré avant l'initialisation
        - La configuration est sauvegardée dans la session
        - L'encadrant ne verra que l'interface utilisateur simplifiée
        
        ### 🔄 **Pour réinitialiser:**
        - Modifiez la configuration et re-cliquez sur "Initialiser"
        """)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("*Agent Advisor Tool v2.0*")
if page == "👤 Interface Utilisateur":
    st.sidebar.markdown("👤 **Mode Utilisateur**")
else:
    st.sidebar.markdown("⚙️ **Mode Admin**")