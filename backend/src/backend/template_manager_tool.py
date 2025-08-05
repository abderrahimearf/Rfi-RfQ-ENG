import os
import json
import re
import unicodedata
from xhtml2pdf import pisa

class TemplateManagerTool:
    def __init__(self, template_id, templates_dir="templates", output_dir="outputs"):
        self.template_id = template_id
        self.templates_dir = templates_dir
        self.output_dir = output_dir

        self.html_path = os.path.join(templates_dir, f"{template_id}.html")
        self.json_path = os.path.join(templates_dir, f"{template_id}.json")
        self.output_html_path = os.path.join(output_dir, f"{template_id}.generated.html")
        self.state_path = os.path.join(output_dir, f"{template_id}.state.json")

        self.original_html = self._load_html()
        self.template_data = self._load_json()

        self.filled_data = {}
        self.removed_sections = set()
        self.dynamic_sections = {}

        self._load_state()
        self._update_html()
        self._save_html()

    def _load_html(self):
        with open(self.html_path, "r", encoding="utf-8") as f:
            return f.read()

    def _load_json(self):
        with open(self.json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_state(self):
        if os.path.exists(self.state_path):
            with open(self.state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.filled_data = data.get("filled_data", {})
                self.removed_sections = set(data.get("removed_sections", []))
                self.dynamic_sections = data.get("dynamic_sections", {})
        else:
            self.filled_data = {}
            self.removed_sections = set()
            self.dynamic_sections = {}

    def _save_state(self):
        os.makedirs(self.output_dir, exist_ok=True)
        state = {
            "filled_data": self.filled_data,
            "removed_sections": list(self.removed_sections),
            "dynamic_sections": self.dynamic_sections
        }
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def _apply_filled_data(self):
        updated_html = self.original_html
        for key, section_data in self.template_data.items():
            if not isinstance(section_data, dict) or key in self.removed_sections:
                continue
            placeholder = section_data.get("contenu")
            if not placeholder:
                continue
            value = self.filled_data.get(key, section_data.get("contenu_initiale", ""))
            updated_html = re.sub(re.escape(placeholder), str(value), updated_html)
        return updated_html

    def _update_html(self):
        updated = self._apply_filled_data()
        if self.dynamic_sections:
            idx = updated.rfind("</main>")
            if idx != -1:
                before, after = updated[:idx], updated[idx:]
                dyn_html = ""
                for key, sec in self.dynamic_sections.items():
                    dyn_html += (
                        f"\n<section id='{key}' class='section'>\n"
                        f"  <h2>{sec['titre']}</h2>\n"
                        f"  <div class='content'>{sec['contenu']}</div>\n"
                        "</section>\n"
                    )
                updated = before + dyn_html + after
        self.html_template = updated

    def _save_html(self):
        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.output_html_path, "w", encoding="utf-8") as f:
            f.write(self.html_template)

    def inject(self, section, content):
        """
        Injecte du contenu dans une section :
        - si la clé existe dans dynamic_sections, on met à jour son 'contenu'
        - sinon, si la clé existe dans template_data, on lève à filled_data pour 
          remplacer proprement le placeholder au prochain update
        - sinon, on lève une erreur.
        Après modification, on régénère le HTML, on sauve l'état et on écrit le fichier.
        """
        if section in self.dynamic_sections:
            self.dynamic_sections[section]['contenu'] = content
        elif section in self.template_data:
            self.filled_data[section] = content
        else:
            raise ValueError(f"Section inconnue : '{section}'")

        self._update_html()
        self._save_state()
        self._save_html()

    def add_section(self, titre, contenu):
        key = self._slugify(titre)
        self.dynamic_sections[key] = {"titre": titre, "contenu": contenu}
        self._update_html()
        self._save_state()
        self._save_html()

    def remove_section(self, key):
        self.removed_sections.add(key)
        self.dynamic_sections.pop(key, None)
        self._update_html()
        self._save_state()
        self._save_html()

    def create_and_initialize(self):
        for key, bloc in self.template_data.items():
            if isinstance(bloc, dict) and key not in self.filled_data:
                init = bloc.get("contenu_initiale")
                if init:
                    self.filled_data[key] = init
        self._update_html()
        self._save_state()
        self._save_html()

    def export_as_pdf(self, export_dir=None, filename="datadicos.pdf"):
        if not os.path.exists(self.output_html_path):
            raise FileNotFoundError("Le fichier HTML généré est introuvable.")
        export_dir = export_dir or self.output_dir
        os.makedirs(export_dir, exist_ok=True)
        out_path = os.path.join(export_dir, filename)
        with open(self.output_html_path, "r", encoding="utf-8") as f:
            html = f.read()
        with open(out_path, "w+b") as pdf_f:
            pisa_status = pisa.CreatePDF(html, dest=pdf_f)
        if pisa_status.err:
            print(f"❌ Erreur génération PDF : {pisa_status.err}")
        else:
            print(f"✅ PDF exporté : {out_path}")

    def render(self):
        return self.html_template

    def get_output_path(self):
        return self.output_html_path

    def _slugify(self, text):
        text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        text = re.sub(r"[^\w\s-]", "", text).strip().lower()
        return re.sub(r"[\s_-]+", "_", text)
