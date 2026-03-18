# him_ai_dialog.py
"""
Him AI — Assistant intelligent intégré dans Foster Structural.
Capacités 2026 :
  • Créer / supprimer : nœuds, poutres, sections, charges
  • Configurer les appuis
  • Lancer l'analyse structurale et afficher les résultats
  • Afficher / masquer / configurer BMD et SFD
  • Modifier les paramètres des diagrammes (show_max, couleurs…)
  • Répondre à des questions textuelles sur le modèle
"""

import os
import json
import re

from openai import OpenAI
from dotenv import load_dotenv
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QMessageBox, QProgressBar, QLabel
)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QFont
from chinese_standard import format_rebar_selection_for_ai
from chinese_standard import RectangularSection
from canvas import NodeItem, BeamItem
from section_manager import SectionLibrary, Section
from language_manager import tr, get_language, register_language_callback, unregister_language_callback

load_dotenv()

GITHUB_TOKEN   = os.environ.get("GITHUB_TOKEN", "")
GITHUB_API_URL = "https://models.inference.ai.azure.com"
MODEL_NAME     = "gpt-4.1"


# ═══════════════════════════════════════════════════════════════════════════
#  HELPER — Tableau HTML solutions ferraillage (Uniforme + Mixte)
# ═══════════════════════════════════════════════════════════════════════════

def _fmt_solutions_table(top_solutions: list, title: str = "Options",
                          max_show: int = 7) -> str:
    """
    Génère un tableau HTML compact montrant toutes les solutions triées.
    Badge [U] = Uniforme (même Ø)  /  [M] = Mixte (2 Ø différents).
    """
    if not top_solutions:
        return ""

    rows = ""
    for sol in top_solutions[:max_show]:
        typ   = "M" if sol.get("is_mixed") else "U"
        disp  = sol.get("disposition", "—")
        area  = sol.get("area_provided_mm2", 0)
        ecart = sol.get("oversize_mm2", 0)
        eta   = sol.get("efficiency", 0) * 100
        sc    = sol.get("constructibility", sol.get("constructibility_score", 0))
        best  = sol.get("rank", 99) == 1

        if best:
            bg = "#0d2d0d"; fg = "#66ff88"; star = "🏆 "
        elif typ == "M":
            bg = "#0d1f35"; fg = "#88ccff"; star = "⚡ "
        else:
            bg = "#1e1e30"; fg = "#cccccc"; star = ""

        badge = (
            "<span style='background:#1a3a6a;color:#88ccff;"
            "padding:1px 5px;border-radius:3px;font-size:10px;font-weight:bold;'>M</span>&nbsp;"
            if typ == "M" else
            "<span style='background:#1a3a1a;color:#88ee88;"
            "padding:1px 5px;border-radius:3px;font-size:10px;font-weight:bold;'>U</span>&nbsp;"
        )
        rows += (
            f"<tr style='background:{bg};'>"
            f"<td style='padding:3px 8px;color:{fg};'>{badge}{star}{disp}</td>"
            f"<td style='padding:3px 8px;color:{fg};text-align:right;font-weight:bold;'>{area:.0f}</td>"
            f"<td style='padding:3px 8px;color:#ffaa44;text-align:right;'>{ecart:+.1f}</td>"
            f"<td style='padding:3px 8px;color:#88ffaa;text-align:right;'>{eta:.1f}%</td>"
            f"<td style='padding:3px 8px;color:#aaaaaa;text-align:right;'>{sc:.0f}</td>"
            "</tr>"
        )

    return (
        f"<br><span style='color:#8899aa;font-size:11px;'><b>{title}</b> "
        f"— <span style='background:#1a3a1a;color:#88ee88;padding:0 4px;border-radius:2px;font-size:10px;'>U</span> Uniforme "
        f"&nbsp;<span style='background:#1a3a6a;color:#88ccff;padding:0 4px;border-radius:2px;font-size:10px;'>M</span> Mixte"
        f"&nbsp;&nbsp;η=efficacité&nbsp;&nbsp;Sc=constructibilité</span><br>"
        f"<table style='border-collapse:collapse;font-size:11px;width:100%;margin:3px 0 8px 0;'>"
        f"<tr style='background:#182030;color:#6688aa;font-size:10px;'>"
        f"<th style='padding:3px 8px;text-align:left;'>Disposition</th>"
        f"<th style='padding:3px 8px;'>As mm²</th>"
        f"<th style='padding:3px 8px;'>Écart</th>"
        f"<th style='padding:3px 8px;'>η</th>"
        f"<th style='padding:3px 8px;'>Sc</th>"
        "</tr>"
        f"{rows}"
        "</table>"
    )


# ═══════════════════════════════════════════════════════════════════════════
#  WORKER — appel API dans un thread séparé
# ═══════════════════════════════════════════════════════════════════════════
class HimAIWorker(QThread):
    response_received = Signal(str)
    error_occurred    = Signal(str)

    def __init__(self, prompt: str, canvas, main_window, history: list):
        super().__init__()
        self.prompt  = prompt
        self.canvas  = canvas
        self.main_window = main_window
        self.history = history   # liste de dict {role, content}

    # ────────────────────────────────────────────────────────────────────────
    def _build_system_prompt(self) -> str:
        model = self.canvas.model

        # ── État des nœuds ──
        nodes_lines = []
        for n in model.nodes:
            sup = n.supports
            sup_str = (
                "encastrement" if sup.get("dx") and sup.get("dy") and sup.get("rz") else
                "articulé"     if sup.get("dx") and sup.get("dy") else
                "roulant"      if sup.get("dy") else
                "libre"
            )
            nodes_lines.append(
                f"  {n.id}: ({n.x:.0f}, {n.y:.0f})px  appui={sup_str}"
            )
        nodes_txt = "\n".join(nodes_lines) or "  (aucun)"

        # ── État des poutres ──
        beams_lines = []
        for b in model.beams:
            L_m = b.length / 160.0
            pl  = len(getattr(b, "point_loads_on_beam", []))
            dl  = len(getattr(b, "distributed_loads",   []))
            res = getattr(b, "analysis_results", None)
            res_str = f" | Mmax={res['Mmax']:.2f}kN·m Vmax={res['Vmax']:.2f}kN" if res else " | non analysée"
            beams_lines.append(
                f"  {b.id}: {b.node_start.id}→{b.node_end.id}  "
                f"L={L_m:.2f}m  section={b.section_name}  "
                f"chg_ponctuelles={pl}  chg_reparties={dl}{res_str}"
            )
        beams_txt = "\n".join(beams_lines) or "  (aucune)"

        # ── Charges ponctuelles sur poutres ──
        plb_lines = []
        for p in model.point_loads_on_beams:
            plb_lines.append(
                f"  {p.id}: poutre={p.beam.id}  @{p.position_ratio*100:.0f}%  "
                f"Fx={p.fx:+.2f}kN  Fy={p.fy:+.2f}kN"
            )
        plb_txt = "\n".join(plb_lines) or "  (aucune)"

        # ── Charges réparties ──
        dl_lines = []
        for d in model.distributed_loads:
            mid = getattr(d, "member", None) or getattr(d, "beam", None)
            mid_id = mid.id if mid else "?"
            dl_lines.append(
                f"  {d.id}: poutre={mid_id}  w={d.w:+.2f}kN/m  "
                f"[{d.start_pos*100:.0f}%→{d.end_pos*100:.0f}%]"
            )
        dl_txt = "\n".join(dl_lines) or "  (aucune)"

        # ── Sections ──
        sec_lines = [
            f"  {s.name} ({s.shape_type}, {s.material}, b={s.b}mm, h={s.h}mm, "
            f"Ix={s.Ix:.0f}mm⁴)"
            for s in self.canvas.section_library.get_all_sections()
        ]
        sec_txt = "\n".join(sec_lines) or "  (aucune)"


        # ── RÉSULTATS D'ANALYSE (res_txt) ── DEFINI UNE SEULE FOIS ICI
        results = (getattr(self.main_window, "full_analysis_results", None) or
                    getattr(self.canvas, "_last_results", None) or {})
        res_lines = []
        for bid, combos in results.items():
            if isinstance(combos, dict) and combos:
                 # On prend la pire combinaison (ou la première)
                worst = max(combos.values(), key=lambda x: abs(x.get('Mmax', 0)))
                res_lines.append(
                    f"  {bid}: Mmax={worst.get('Mmax',0):.2f} kN·m | "
                    f"Vmax={worst.get('Vmax',0):.2f} kN"
                )
        res_txt = "\n".join(res_lines) or "  (aucun résultat d'analyse)"


        # ── Ferraillage stocké ──
        rebar_lines = []
        for b in model.beams:
            rb = getattr(b, "rebar_results", None)
            if rb:
                if rb.get("type") == "single":
                    best = (rb.get("best_bar_label") or
                            rb.get("best_disposition") or "—")
                    rebar_lines.append(
                        f"  {b.id}: SIMPLE As={rb.get('As_final_mm2',0):.0f}mm² "
                        f"| {best} | {rb.get('status','')}"
                    )
                else:
                    bt = (rb.get("best_tension_label") or
                          rb.get("best_disposition_tension") or "—")
                    bc = (rb.get("best_comp_label") or
                          rb.get("best_disposition_compression") or "—")
                    rebar_lines.append(
                        f"  {b.id}: DOUBLE As={rb.get('As_final_mm2',0):.0f}mm² "
                        f"As'={rb.get('As_prime_mm2',0):.0f}mm² "
                        f"| tens:{bt} comp:{bc} | {rb.get('status','')}"
                    )
        rebar_txt = "\n".join(rebar_lines) or "  (aucun ferraillage calculé)"

        # ── Settings diagrammes ──
        dsettings = getattr(self.canvas, "diagram_settings", {})
        diag_txt = json.dumps(dsettings, ensure_ascii=False, indent=2)

        # ── Instruction de langue ──────────────────────────────────────────
        lang_instruction = tr("ai_lang_instruction")

        return f"""Tu es Him AI, assistant expert en analyse structurale 2D et béton armé GB 50010.

═══ ÉTAT DU MODÈLE ═══
Nœuds ({len(model.nodes)}) :
{nodes_txt}

Poutres ({len(model.beams)}) :
{beams_txt}

Charges ponctuelles sur poutres ({len(model.point_loads_on_beams)}) :
{plb_txt}

Charges réparties ({len(model.distributed_loads)}) :
{dl_txt}

Sections disponibles :
{sec_txt}

Résultats d'analyse :
{res_txt}

Ferraillage calculé :
{rebar_txt}

Diagrammes : {diag_txt}
Snap grille : {"activé" if self.canvas.snap_to_grid else "désactivé"}

═══ CONNAISSANCE BÉTON ARMÉ GB 50010 (MÉMORISÉE) ═══
── Dimensions normalisées §4.1.1 ──
b (mm)  : 100,120,150,180,200,220,250,300,350,400
h (mm)  : 250,300,350,400,450,500,550,600,650,700,750,800,900,1000
h/b rect: 2,0–3,5  |  h/b T: 2,5–4,0

── Barres longitudinales §9.2 ──
Poutres : Φ12,Φ14,Φ16,Φ18,Φ20,Φ22,Φ25,Φ28 mm (classe II–III)
Dalles  : Φ8,Φ10,Φ12,Φ14,Φ16 mm
d_min   : ≥10mm si h≥300mm ; ≥8mm si h<300mm | n_min=3 barres
Espacement min : max(25mm, Φ_barre)

── Aires (mm²) ──
Φ8=50 Φ10=79 Φ12=113 Φ14=154 Φ16=201 Φ18=254 Φ20=314 Φ22=380 Φ25=491 Φ28=616

── Aciers fy (N/mm²) ──
HPB235:210 | HRB335:300 | HRB400:360 | HRB500:435

── Béton fc (N/mm²) ──
C20:9.6 | C25:11.9 | C30:14.3 | C35:16.7 | C40:19.1 | C50:23.1

── ξ_b ──
HPB235:0.614 | HRB335:0.550 | HRB400:0.518 | HRB500:0.482

── Algorithme ferraillage ──
1. Mu_max=α₁·fc·b·(ξ_b·h₀)·(h₀−ξ_b·h₀/2)
2. Si M≤Mu_max → SIMPLE : α_s=M/(α₁·fc·b·h₀²) ; ξ=1−√(1−2α_s) ; As=α₁·fc·b·ξ·h₀/fy
3. Si M>Mu_max → DOUBLE : Mu2=M−Mu1 ; As'=Mu2/(fy'·(h₀−a')) ; As=As1+As2 ; vérif x_b≥2a'
4. ρ_min=max(0.2%, 0.45·ft/fy·100%) ; As=max(As_calc, ρ_min·b·h)
5. b_min=2·cover+n·d+(n−1)·max(25,d) ≤ b — sélectionner le moins de barres possible

═══ RÈGLES ═══
1. JSON valide uniquement pour les actions (pas de markdown).
2. Plusieurs actions → liste JSON : [{{...}}, {{...}}]
3. Réponse textuelle si pas d'action.
4. 1m=160px | Forces en kN | Fy<0 = vers le bas

═══ ACTIONS DISPONIBLES ═══
── Nœuds ──
{{"action":"create_node","x":<px>,"y":<px>}}
{{"action":"delete_node","node_id":"<id>"}}

── Poutres ──
{{"action":"create_beam","start_node_id":"<id>","end_node_id":"<id>","section":"<nom>"}}
{{"action":"delete_beam","beam_id":"<id>"}}

── Sections ──
{{"action":"create_section","name":"<nom>","shape_type":"rectangle|I|T","material":"Concrete|Steel","b":<mm>,"h":<mm>,"tw":<mm>,"tf":<mm>,"bf":<mm>}}

── Appuis ──
{{"action":"set_support","node_id":"<id>","type":"libre|articulé|roulant|encastrement"}}

── Charges nœud ──
{{"action":"add_point_load","node_id":"<id>","fx":<kN>,"fy":<kN>}}
{{"action":"delete_point_load","node_id":"<id>"}}

── Charges ponctuelle sur poutre ──
{{"action":"add_point_load_on_beam","beam_id":"<id>","position_ratio":<0-1>,"fx":<kN>,"fy":<kN>}}
{{"action":"delete_point_load_on_beam","load_id":"<id>"}}
{{"action":"delete_all_point_loads_on_beam","beam_id":"<id>"}}

── Charges réparties ──
{{"action":"add_distributed_load","beam_id":"<id>","w":<kN/m>,"start_pos":<0-1>,"end_pos":<0-1>,"load_type":"G|Q"}}
{{"action":"delete_distributed_load","beam_id":"<id>"}}

── Analyse ──
{{"action":"run_analysis"}}
{{"action":"show_results"}}

── Ferraillage (NOUVEAU) ──
{{"action":"calculate_rebar","beam_id":"<id>","concrete_grade":"C25","steel_grade":"HRB335","cover":40,"a_prime":35,"preferred_diameters":[16,18,20,25]}}
  → Utilise Mmax des résultats d'analyse pour la poutre beam_id
  → Choisit auto simple ou double selon M vs Mu_max
  → preferred_diameters optionnel (défaut : tous diamètres poutres)

{{"action":"calculate_rebar_manual","b":<mm>,"h":<mm>,"M_kNm":<val>,"concrete_grade":"C30","steel_grade":"HRB335","cover":40,"a_prime":35,"preferred_diameters":[16,20,25]}}
  → Calcul libre sans référence à une poutre existante

── Diagrammes ──
{{"action":"toggle_bmd"}}
{{"action":"toggle_sfd"}}
{{"action":"set_diagram_setting","key":"<clé>","value":<val>}}

── Nettoyage ──
{{"action":"clear_all"}}

═══ EXEMPLES ═══
"Ferre la poutre B123 en C30/HRB335" →
[{{"action":"calculate_rebar","beam_id":"B123","concrete_grade":"C30","steel_grade":"HRB335","cover":40}}]

"Section 200×450 C25/HRB335 peut-elle reprendre 174 kN·m ?" →
[{{"action":"calculate_rebar_manual","b":200,"h":450,"M_kNm":174,"concrete_grade":"C25","steel_grade":"HRB335","cover":60,"a_prime":35}}]

"Lance l'analyse puis calcule le ferraillage de toutes les poutres" →
[{{"action":"run_analysis"}}, {{"action":"calculate_rebar","beam_id":"<id1>",...}}, ...]
"""

    def run(self):
        if not GITHUB_TOKEN:
            self.error_occurred.emit(
                "GITHUB_TOKEN manquant.\n"
                "Crée un token sur https://github.com/settings/tokens "
                "(scope 'models:read') et relance l'app."
            )
            return
        try:
            client = OpenAI(base_url=GITHUB_API_URL, api_key=GITHUB_TOKEN)
            messages = [{"role": "system", "content": self._build_system_prompt()}]
            messages += self.history
            messages.append({"role": "user", "content": self.prompt})

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.05,
                max_tokens=2048,
                top_p=0.95,
            )
            answer = response.choices[0].message.content.strip()
            self.response_received.emit(answer)
        except Exception as e:
            self.error_occurred.emit(f"Erreur API ({MODEL_NAME}) : {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
#  DIALOG PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════
class HimAIDialog(QDialog):

    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.canvas      = canvas
        self.main_window = parent
        self.worker      = None
        self._history    = []   # mémoire multi-tours

        # Sync section_library
        if not getattr(canvas, "section_library", None):
            canvas.section_library = SectionLibrary()
        if parent and hasattr(parent, "section_library"):
            self.section_library    = parent.section_library
            canvas.section_library  = parent.section_library
        else:
            self.section_library = canvas.section_library

        self.setWindowTitle(f"Him AI  ·  {MODEL_NAME}")
        self.resize(720, 580)
        self.setModal(False)
        self._build_ui()
        self._check_token()

    # ────────────────────────────────────────────────────────────────────────
    # UI
    # ────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)

        self.setStyleSheet("""
            QDialog      { background:#12121f; color:#e0e0e0; }
            QTextEdit    { background:#1a1a2e; color:#e0e0e0;
                           font-family:Consolas,monospace; font-size:12px;
                           border:1px solid #2d2d4a; border-radius:6px; }
            QLineEdit    { background:#1f1f35; color:#ffffff;
                           border:1px solid #2d2d4a; border-radius:5px;
                           padding:6px 10px; font-size:13px; }
            QPushButton  { background:#1a4a8a; color:#fff; border:none;
                           border-radius:5px; padding:7px 18px; font-size:13px; }
            QPushButton:hover   { background:#2060b0; }
            QPushButton:disabled{ background:#333; color:#777; }
            QPushButton#btn_clear { background:#3a1a1a; }
            QPushButton#btn_clear:hover { background:#5a2a2a; }
        """)

        # ── En-tête ──
        header = QLabel(f"🤖  Him AI  <span style='color:#555;font-size:10px'>propulsé par {MODEL_NAME}</span>")
        header.setTextFormat(Qt.RichText)
        header.setFont(QFont("Segoe UI", 11, QFont.Bold))
        layout.addWidget(header)

        # ── Chat ──
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display, stretch=1)

        # ── Barre de progression ──
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.progress.setFixedHeight(4)
        self.progress.setStyleSheet(
            "QProgressBar{background:#1a1a2e;border:none;}"
            "QProgressBar::chunk{background:#4fc3f7;}"
        )
        layout.addWidget(self.progress)

        # ── Input ──
        input_row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText(tr("ai_placeholder"))
        self.input.returnPressed.connect(self.send_message)
        input_row.addWidget(self.input)

        self.send_btn = QPushButton(tr("ai_send") + " ↵")
        self.send_btn.setFixedWidth(110)
        self.send_btn.clicked.connect(self.send_message)
        input_row.addWidget(self.send_btn)

        btn_clear = QPushButton("🗑")
        btn_clear.setObjectName("btn_clear")
        btn_clear.setFixedWidth(40)
        btn_clear.setToolTip(tr("ai_clear"))
        btn_clear.clicked.connect(self._clear_chat)
        input_row.addWidget(btn_clear)

        layout.addLayout(input_row)

        # ── Raccourcis rapides ──
        quick_row = QHBoxLayout()
        quick_row.setSpacing(5)
        shortcuts = [
            ("⚡ Analyser",           "Lance l'analyse structurale"),
            ("📊 Résultats",          "Affiche les résultats de l'analyse"),
            ("📈 BMD max",            "Affiche les valeurs maximales du BMD sur le canvas"),
            ("📉 SFD max",            "Affiche les valeurs maximales du SFD sur le canvas"),
            ("🗑 Tout effacer",       "Efface tout et recommence"),
        ]
        for label, prompt in shortcuts:
            btn = QPushButton(label)
            btn.setFixedHeight(26)
            btn.setStyleSheet(
                "QPushButton{background:#1e2a3a;color:#9dd;font-size:10px;"
                "border:1px solid #2a3a4a;border-radius:4px;padding:0 6px;}"
                "QPushButton:hover{background:#2a3a4a;}"
            )
            btn.clicked.connect(lambda _, p=prompt: self._quick_send(p))
            quick_row.addWidget(btn)

        quick_row.addStretch()
        layout.addLayout(quick_row)

        # Message de bienvenue (traduit)
        self._append("Him AI", tr("ai_welcome"))

    # ────────────────────────────────────────────────────────────────────────
    def _check_token(self):
        if not GITHUB_TOKEN:
            self._append(
                "⚠️ Config",
                "La variable <code>GITHUB_TOKEN</code> est vide.<br>"
                "→ Crée un token sur "
                "<a href='https://github.com/settings/tokens'>github.com/settings/tokens</a> "
                "(scope <code>models:read</code>) puis relance l'app."
            )

    def _clear_chat(self):
        self._history.clear()
        self.chat_display.clear()
        self._append("Him AI", tr("ai_cleared"))

    def _quick_send(self, prompt: str):
        self.input.setText(prompt)
        self.send_message()

    # ────────────────────────────────────────────────────────────────────────
    # Affichage
    # ────────────────────────────────────────────────────────────────────────
    def _append(self, sender: str, html: str):
        colors = {
            "Him AI":    "#4fc3f7",
            "Vous":      "#a5d6a7",
            "⚠️ Config": "#ffb74d",
            "✅":        "#66bb6a",
            "❌":        "#ef5350",
        }
        color = colors.get(sender, "#e0e0e0")
        self.chat_display.append(
            f'<span style="color:{color};font-weight:bold">{sender} :</span> {html}<br>'
        )
        self.chat_display.ensureCursorVisible()

    # ────────────────────────────────────────────────────────────────────────
    # Envoi
    # ────────────────────────────────────────────────────────────────────────
    def send_message(self):
        text = self.input.text().strip()
        if not text:
            return
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "En cours", "Une requête est déjà en cours.")
            return

        self._append("Vous", text)
        self._history.append({"role": "user", "content": text})
        self.input.clear()
        self.input.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.progress.setVisible(True)

        self.worker = HimAIWorker(text, self.canvas, self.main_window, list(self._history[:-1]))
        self.worker.response_received.connect(self._on_response)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_finished(self):
        self.progress.setVisible(False)
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.worker = None

    # ────────────────────────────────────────────────────────────────────────
    # Traitement réponse
    # ────────────────────────────────────────────────────────────────────────
    def _on_response(self, answer: str):
        print("─── HIM AI RAW ───")
        print(answer[:400])
        print("──────────────────")

        self._history.append({"role": "assistant", "content": answer})
        # Garder max 20 tours
        if len(self._history) > 40:
            self._history = self._history[-40:]

        cleaned = re.sub(r"```(?:json)?\s*", "", answer, flags=re.IGNORECASE)
        cleaned = re.sub(r"```", "", cleaned)

        cmds = self._extract_json_blocks(cleaned)

        if cmds:
            executed = 0
            for cmd in cmds:
                if isinstance(cmd, list):
                    for sub in cmd:
                        if isinstance(sub, dict) and "action" in sub:
                            try:
                                self.execute_command(sub)
                                executed += 1
                            except Exception as e:
                                self._append("Him AI", f"⚠️ {e}")
                elif isinstance(cmd, dict) and "action" in cmd:
                    try:
                        self.execute_command(cmd)
                        executed += 1
                    except Exception as e:
                        self._append("Him AI", f"⚠️ {e}")

            text_part = self._strip_json_from_text(cleaned)
            if text_part:
                self._append("Him AI", text_part.replace("\n", "<br>"))
            if executed > 0:
                self._append("✅", f"<b>{executed}</b> action(s) exécutée(s).")
        else:
            self._append("Him AI", answer.replace("\n", "<br>"))

    def _extract_json_blocks(self, text: str) -> list:
        results = []
        i = 0
        while i < len(text):
            ch = text[i]
            if ch in ('{', '['):
                close = '}' if ch == '{' else ']'
                depth = 0
                j = i
                while j < len(text):
                    if text[j] in ('{', '['):
                        depth += 1
                    elif text[j] in ('}', ']'):
                        depth -= 1
                        if depth == 0:
                            try:
                                obj = json.loads(text[i:j+1])
                                results.append(obj)
                            except json.JSONDecodeError:
                                pass
                            i = j + 1
                            break
                    j += 1
                else:
                    i += 1
            else:
                i += 1
        return results

    def _strip_json_from_text(self, text: str) -> str:
        cleaned = re.sub(r'\[[^\[\]]*\]', '', text)
        cleaned = re.sub(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)?\}', '', cleaned)
        return cleaned.strip(" \n,")

    # ────────────────────────────────────────────────────────────────────────
    # Exécution des commandes
    # ────────────────────────────────────────────────────────────────────────
    def execute_command(self, cmd: dict):
        print("CMD:", cmd)
        action = cmd.get("action", "")
        model  = self.canvas.model
        scene  = self.canvas.scene

        # ── Analyse ────────────────────────────────────────────────────────
        if action == "run_analysis":
            if not self.main_window:
                raise ValueError("main_window non disponible")
            self._append("Him AI", "🚀 Lancement de l'analyse structurale…")
            self.main_window.run_structural_analysis()
            # Récupérer les résultats via _get_displayed_results (enveloppe)
            results = None
            if hasattr(self.main_window, "_get_displayed_results"):
                results = self.main_window._get_displayed_results() or None
            if not results:
                results = getattr(self.main_window, "full_analysis_results", None)
            if results:
                # Cache les résultats plats sur le canvas pour le system prompt
                self.canvas._last_results = results
                lines = []
                # Support both flat {bid:{Mmax}} and nested {bid:{combo:{Mmax}}}
                for bid, r in results.items():
                    if isinstance(r, dict) and "Mmax" not in r:
                        r = max(r.values(), key=lambda x: abs(x.get("Mmax", 0)))
                    lines.append(
                        f"  <b>{bid}</b> : "
                        f"Mmax = <b>{r['Mmax']:.3f} kN·m</b>  |  "
                        f"Vmax = <b>{r['Vmax']:.3f} kN</b>  |  "
                        f"L = {r['L_m']:.2f} m"
                    )
                self._append(
                    "Him AI",
                    "✅ Analyse terminée :<br>" + "<br>".join(lines)
                )
            else:
                self._append("Him AI", "⚠️ L'analyse n'a pas produit de résultats.")

        elif action == "show_results":
            results = None
            if hasattr(self.main_window, "_get_displayed_results"):
                results = self.main_window._get_displayed_results() or None
            if not results:
                results = getattr(self.canvas, "_last_results", None) or {}
            if not results:
                self._append("Him AI", "Aucun résultat disponible. Lance d'abord l'analyse.")
                return
            lines = []
            for bid, r in results.items():
                if isinstance(r, dict) and "Mmax" not in r:
                    r = max(r.values(), key=lambda x: abs(x.get("Mmax", 0)))
                lines.append(
                    f"  <b>{bid}</b> : "
                    f"Mmax = <b>{r['Mmax']:.3f} kN·m</b>  |  "
                    f"Vmax = <b>{r['Vmax']:.3f} kN</b>  |  "
                    f"L = {r['L_m']:.2f} m"
                )
            self._append("Him AI", "📊 Résultats de l'analyse :<br>" + "<br>".join(lines))

        # ── Diagrammes ─────────────────────────────────────────────────────

        # ── Calcul ferraillage sur une poutre analysée ───────────────────────
        elif action == "calculate_rebar":
            from chinese_standard import RectangularSection
            beam_id = str(cmd.get("beam_id", ""))
            beam = next((b for b in model.beams if b.id == beam_id), None)
            if not beam:
                raise ValueError(f"Poutre '{beam_id}' introuvable")

            # Récupérer Mmax depuis les résultats d'analyse
            results = (getattr(self.main_window, "full_analysis_results", None)
                       or getattr(self.canvas, "_last_results", None) or {})
            beam_res = results.get(beam_id)
            if not beam_res:
                # Essayer aussi les resultats directs sur la poutre
                beam_res = getattr(beam, "analysis_results", None)
            if not beam_res:
                raise ValueError(
                    f"Aucun résultat d'analyse pour '{beam_id}'. "
                    "Lance d'abord l'analyse structurale."
                )

            # Paramètres section
            sec = self.canvas.section_library.get_section(
                getattr(beam, "section_name", None)
            )
            b_mm = sec.b if sec else float(cmd.get("b", 200))
            h_mm = sec.h if sec else float(cmd.get("h", 400))

            M_kNm = beam_res.get("Mmax", 0.0)
            if M_kNm <= 0:
                self._append("Him AI",
                    f"ℹ️ Poutre <b>{beam_id}</b> : Mmax={M_kNm:.3f} kN·m — "
                    "aucun ferraillage nécessaire (moment nul ou positif).")
                return

            # Paramètres calcul
            concrete  = str(cmd.get("concrete_grade", "C30"))
            steel     = str(cmd.get("steel_grade",    "HRB335"))
            cover     = float(cmd.get("cover",   40.0))
            a_prime   = float(cmd.get("a_prime", 35.0))
            pref_dias = cmd.get("preferred_diameters", None)

            sec_calc = RectangularSection(
                b_mm, h_mm, concrete, steel, cover, a_prime
            )
            result = sec_calc.calculate_flexure(M_kNm, pref_dias)

            # Stocker le résultat sur la poutre
            beam.rebar_results = result

            # Affichage résultats
            rtype = result.get("type", "?")
            if rtype == "single":
                top_sols = result.get("top_solutions_full", [])
                html = (
                    f"🔩 <b>Ferraillage SIMPLE</b> — Poutre <b>{beam_id}</b><br>"
                    f"Section: {b_mm:.0f}×{h_mm:.0f} mm | {concrete}/{steel}<br>"
                    f"M = {M_kNm:.2f} kN·m &le; Mu_max = {result['Mu_max_kNm']:.2f} kN·m<br>"
                    f"α_s = {result['alpha_s']} | ξ = {result['xi']} ≤ ξ_b = {result['xi_b']}<br>"
                    f"As requis = <b>{result['As_final_mm2']:.0f} mm²</b><br>"
                    f"<b>🏆 {result['best_bar_label']}</b><br>"
                    + _fmt_solutions_table(top_sols, "Toutes les solutions (Uniforme + Mixte)") +
                    f"Mu_cap = {result['Mu_capacity_kNm']} kN·m — {result['status']}"
                )
            else:
                top_tens = result.get("top_solutions_tension", [])
                top_comp = result.get("top_solutions_compression", [])
                html = (
                    f"🔩 <b>Ferraillage DOUBLE</b> — Poutre <b>{beam_id}</b><br>"
                    f"Section: {b_mm:.0f}×{h_mm:.0f} mm | {concrete}/{steel}<br>"
                    f"M = {M_kNm:.2f} kN·m &gt; Mu_max = {result['Mu_max_kNm']:.2f} kN·m → DOUBLE<br>"
                    f"x_b = {result['x_b_mm']} mm | {result['x_check_status']}<br>"
                    f"Mu1 = {result['Mu1_kNm']} | Mu2 = {result['Mu2_kNm']} kN·m<br>"
                    f"<b>As' (compression) = {result['As_prime_mm2']:.0f} mm²</b> → 🏆 {result['best_comp_label']}<br>"
                    + _fmt_solutions_table(top_comp, "Compression — options (U + M)", 4) +
                    f"<b>As (traction) = {result['As_final_mm2']:.0f} mm²</b> → 🏆 {result['best_tension_label']}<br>"
                    + _fmt_solutions_table(top_tens, "Traction — options (U + M)", 7) +
                    f"Mu_cap = {result['Mu_capacity_kNm']} kN·m — {result['status']}"
                )
            self._append("Him AI", html)

        elif action == "select_rebars_optimized":

            As_traction = float(cmd.get("As_traction", 0))
            As_compression = float(cmd.get("As_compression", 0))
            b = float(cmd.get("b", 250))
            h = float(cmd.get("h", 500))
            cover = float(cmd.get("cover", 40))
            concrete = str(cmd.get("concrete_grade", "C30"))
            steel = str(cmd.get("steel_grade", "HRB400"))
            if As_traction <= 0:
                raise ValueError("As_traction doit être > 0")
            
            result_text = format_rebar_selection_for_ai(
                As_traction=As_traction,
                As_compression=As_compression,
                b=b, h=h, cover=cover,
                concrete_grade=concrete,
                steel_grade=steel
            )

            self._append("Him AI", f"<pre style='font-family:monospace;font-size:11px'>{result_text}</pre>")
        
        elif action == "calculate_rebar_with_ai_selection":
            b = float(cmd.get("b", 200))
            h = float(cmd.get("h", 400))
            M_kNm = float(cmd.get("M_kNm", 0))
            concrete = str(cmd.get("concrete_grade", "C30"))
            steel = str(cmd.get("steel_grade", "HRB335"))
            cover = float(cmd.get("cover", 40))
            a_prime = float(cmd.get("a_prime", 35))

            if M_kNm <= 0:
                raise ValueError("M_kNm doit être > 0")
            
            rc = RectangularSection(b, h, concrete, steel, cover, a_prime)
            result = rc.calculate_flexure(M_kNm)
            ai_data = result.get("ai_bar_selection", {})
            rec = ai_data.get("recommendation", {}) if isinstance(ai_data, dict) else {}

            html = f"""
            <h3>🔩 Calcul Ferraillage + Sélection AI Optimisée</h3>
            <b>Section:</b> {b:.0f}×{h:.0f} mm | {concrete}/{steel}<br>
            <b>Moment:</b> {M_kNm:.2f} kN·m<br>
            <b>Type:</b> {'DOUBLE' if result.get('double_required') else 'SIMPLE'}<br><br>
            
            <b>📊 Résultats calcul:</b><br>
            • As requis = {result.get('As_final_mm2', 0):.0f} mm²<br>
            • Mu_cap = {result.get('Mu_capacity_kNm', 0):.2f} kN·m<br>
            • Status: {result.get('status', 'N/A')}<br><br>
            
            <b>🤖 Sélection AI Recommandée:</b><br>
            <pre style='background:#1a1a2e;padding:10px;border-radius:5px;font-size:12px'>
            {rec.get('disposition', 'N/A')}

            Justification: {rec.get('justification', 'N/A')}
            </pre>
            """
            self._append("Him AI", html)
            result["beam_id"] = cmd.get("beam_id", "manual")





        # ── Calcul ferraillage manuel (sans poutre de référence) ─────────────
        elif action == "calculate_rebar_manual":
            from chinese_standard import RectangularSection
            b_mm    = float(cmd.get("b", 200))
            h_mm    = float(cmd.get("h", 400))
            M_kNm   = float(cmd.get("M_kNm", 0))
            concrete = str(cmd.get("concrete_grade", "C30"))
            steel    = str(cmd.get("steel_grade",    "HRB335"))
            cover    = float(cmd.get("cover",   40.0))
            a_prime  = float(cmd.get("a_prime", 35.0))
            pref_dias = cmd.get("preferred_diameters", None)

            if M_kNm <= 0:
                raise ValueError("M_kNm doit être > 0")

            sec_calc = RectangularSection(b_mm, h_mm, concrete, steel, cover, a_prime)
            result = sec_calc.calculate_flexure(M_kNm, pref_dias)

            rtype = result.get("type", "?")
            double_note = (
                f"⚠️ M = {M_kNm} kN·m &gt; Mu_max = {result['Mu_max_kNm']} kN·m "
                f"→ <b>FERRAILLAGE DOUBLE</b><br>"
            ) if rtype == "double" else (
                f"✅ M = {M_kNm} kN·m &le; Mu_max = {result['Mu_max_kNm']} kN·m "
                f"→ <b>FERRAILLAGE SIMPLE</b><br>"
            )

            if rtype == "single":
                top_sols = result.get("top_solutions_full", [])
                html = (
                    f"📐 <b>Calcul manuel</b> — {b_mm:.0f}×{h_mm:.0f} mm "
                    f"{concrete}/{steel} M={M_kNm} kN·m<br>"
                    + double_note +
                    f"As = <b>{result['As_final_mm2']:.0f} mm²</b><br>"
                    f"<b>🏆 {result['best_bar_label']}</b><br>"
                    + _fmt_solutions_table(top_sols, "Toutes les solutions (Uniforme + Mixte)") +
                    f"Mu_cap = {result['Mu_capacity_kNm']} kN·m — {result['status']}"
                )
            else:
                top_tens = result.get("top_solutions_tension", [])
                top_comp = result.get("top_solutions_compression", [])
                html = (
                    f"📐 <b>Calcul manuel</b> — {b_mm:.0f}×{h_mm:.0f} mm "
                    f"{concrete}/{steel} M={M_kNm} kN·m<br>"
                    + double_note +
                    f"x_b = {result['x_b_mm']} mm | {result['x_check_status']}<br>"
                    f"<b>As' = {result['As_prime_mm2']:.0f} mm²</b> → 🏆 {result['best_comp_label']}<br>"
                    + _fmt_solutions_table(top_comp, "Compression — options (U + M)", 4) +
                    f"<b>As = {result['As_final_mm2']:.0f} mm²</b> → 🏆 {result['best_tension_label']}<br>"
                    + _fmt_solutions_table(top_tens, "Traction — options (U + M)", 7) +
                    f"Mu_cap = {result['Mu_capacity_kNm']} kN·m — {result['status']}"
                )
            self._append("Him AI", html)

        elif action == "toggle_bmd":
            if self.main_window:
                self.main_window.toggle_bmd()
                state = self.canvas.diagram_settings.get("show_bmd", True)
                self._append("Him AI", f"📊 BMD {'affiché' if state else 'masqué'}")
            else:
                raise ValueError("main_window non disponible")

        elif action == "toggle_sfd":
            if self.main_window:
                self.main_window.toggle_sfd()
                state = self.canvas.diagram_settings.get("show_sfd", True)
                self._append("Him AI", f"📉 SFD {'affiché' if state else 'masqué'}")
            else:
                raise ValueError("main_window non disponible")

        elif action == "set_diagram_setting":
            key   = cmd.get("key", "")
            value = cmd.get("value")
            if not key:
                raise ValueError("'key' obligatoire pour set_diagram_setting")
            if not hasattr(self.canvas, "diagram_settings"):
                self.canvas.diagram_settings = {}
            self.canvas.diagram_settings[key] = value
            # Redessiner les diagrammes si des résultats existent
            results = getattr(self.main_window, "full_analysis_results", None) or \
                      getattr(self.canvas, "_last_results", None)
            flat_results = None
            if hasattr(self.main_window, "_get_displayed_results"):
                flat_results = self.main_window._get_displayed_results() or None
            if not flat_results:
                flat_results = getattr(self.canvas, "_last_results", None)
            if flat_results:
                self.canvas.draw_analysis_diagrams(flat_results)
            self._append(
                "Him AI",
                f"⚙️ Paramètre diagramme <b>{key}</b> = <code>{value}</code>"
            )

        # ── Nœuds ──────────────────────────────────────────────────────────
        elif action == "create_node":
            x = float(cmd.get("x", 0))
            y = float(cmd.get("y", 0))
            node = model.add_node(x, y)
            node.graphics_item = NodeItem(node)
            scene.addItem(node.graphics_item)
            self.canvas.viewport().update()
            self._append("Him AI", f"📍 Nœud <b>{node.id}</b> → ({x:.0f}, {y:.0f}) px")

        elif action == "delete_node":
            node_id = str(cmd.get("node_id", ""))
            node = next((n for n in model.nodes if n.id == node_id), None)
            if not node:
                raise ValueError(f"Nœud {node_id} introuvable")
            for beam in list(node.connected_beams):
                self._delete_beam(beam)
            model.nodes.remove(node)
            if node.graphics_item:
                if hasattr(node.graphics_item, "support_symbol") and node.graphics_item.support_symbol:
                    scene.removeItem(node.graphics_item.support_symbol)
                scene.removeItem(node.graphics_item)
            self._append("Him AI", f"🗑️ Nœud <b>{node_id}</b> + ses poutres supprimés")

        # ── Poutres ────────────────────────────────────────────────────────
        elif action == "create_beam":
            start_id = str(cmd.get("start_node_id", ""))
            end_id   = str(cmd.get("end_node_id",   ""))
            start    = next((n for n in model.nodes if str(n.id) == start_id), None)
            end      = next((n for n in model.nodes if str(n.id) == end_id),   None)
            if not start or not end:
                available = [str(n.id) for n in model.nodes]
                raise ValueError(
                    f"Nœud introuvable (start='{start_id}', end='{end_id}'). "
                    f"IDs disponibles : {available}"
                )
            section_name = cmd.get("section", "default")
            beam = model.add_beam(start, end, section_name=section_name)
            bi = BeamItem(beam)
            beam.graphics_item = bi
            scene.addItem(bi)
            self.canvas.viewport().update()
            L_m = beam.length / 160.0
            self._append(
                "Him AI",
                f"📐 Poutre <b>{beam.id}</b> ({start_id}→{end_id}) "
                f"L={L_m:.2f}m section=<i>{section_name}</i>"
            )

        elif action == "delete_beam":
            beam_id = str(cmd.get("beam_id", ""))
            beam = next((b for b in model.beams if b.id == beam_id), None)
            if not beam:
                raise ValueError(f"Poutre {beam_id} introuvable")
            self._delete_beam(beam)
            self._append("Him AI", f"🗑️ Poutre <b>{beam_id}</b> supprimée")

        # ── Sections ───────────────────────────────────────────────────────
        elif action == "create_section":
            name = cmd.get("name")
            if not name:
                raise ValueError("'name' obligatoire")
            section = Section(
                name         = name,
                shape_type   = cmd.get("shape_type", "rectangle"),
                material     = cmd.get("material", "Concrete"),
                b            = float(cmd.get("b",  0)),
                h            = float(cmd.get("h",  0)),
                tw           = float(cmd.get("tw", 0)),
                tf           = float(cmd.get("tf", 0)),
                bf           = float(cmd.get("bf", cmd.get("b", 0))),
                web_position = cmd.get("web_position", "center"),
            )
            self.section_library.save_section(section)
            if self.main_window:
                if hasattr(self.main_window, "refresh_all_section_combos"):
                    self.main_window.refresh_all_section_combos()
                if hasattr(self.main_window, "sections_panel"):
                    self.main_window.sections_panel.update_section_list()
            self._append(
                "Him AI",
                f"📦 Section <b>{name}</b> — {section.shape_type} | {section.material} "
                f"| {section.b}×{section.h} mm | Ix={section.Ix:.0f} mm⁴"
            )

        # ── Appuis ─────────────────────────────────────────────────────────
        elif action == "set_support":
            node_id      = str(cmd.get("node_id", ""))
            support_type = str(cmd.get("type", "")).lower()
            node = next((n for n in model.nodes if str(n.id) == node_id), None)
            if not node:
                raise ValueError(f"Nœud '{node_id}' introuvable")
            mapping = {
                "libre":         {"dx": False, "dy": False, "rz": False},
                "articulé":      {"dx": True,  "dy": True,  "rz": False},
                "roulant":       {"dx": False, "dy": True,  "rz": False},
                "encastrement":  {"dx": True,  "dy": True,  "rz": True},
            }
            if support_type not in mapping:
                raise ValueError(f"Type d'appui '{support_type}' inconnu. "
                                 "Choisir: libre|articulé|roulant|encastrement")
            node.supports = mapping[support_type]
            if hasattr(node, "graphics_item") and node.graphics_item:
                gi = node.graphics_item
                if gi.support_symbol is None:
                    gi.create_support_symbol(scene)
                gi.update_support_symbol()
            scene.update()
            self.canvas.viewport().update()
            self._append("Him AI", f"🔩 Nœud <b>{node_id}</b> → <i>{support_type}</i>")

        # ── Charge ponctuelle sur nœud ──────────────────────────────────────
        elif action == "add_point_load":
            node_id = str(cmd.get("node_id", ""))
            node = next((n for n in model.nodes if str(n.id) == node_id), None)
            if not node:
                raise ValueError(f"Nœud '{node_id}' introuvable")
            from structural_model import PointLoad
            load = PointLoad(node, fx=float(cmd.get("fx", 0)), fy=float(cmd.get("fy", 0)))
            model.point_loads.append(load)
            self.canvas.add_point_load_visual(load)
            self._append(
                "Him AI",
                f"⬇️ Charge sur <b>{node_id}</b> — "
                f"Fx={load.fx:+.2f} kN  Fy={load.fy:+.2f} kN"
            )

        elif action == "delete_point_load":
            node_id = str(cmd.get("node_id", ""))
            node = next((n for n in model.nodes if n.id == node_id), None)
            if not node:
                raise ValueError(f"Nœud {node_id} introuvable")
            count = len(node.point_loads)
            for load in list(node.point_loads):
                if hasattr(load, "graphics_item") and load.graphics_item:
                    scene.removeItem(load.graphics_item)
                if load in model.point_loads:
                    model.point_loads.remove(load)
            node.point_loads.clear()
            self._append("Him AI", f"🗑️ {count} charge(s) supprimée(s) sur <b>{node_id}</b>")

        # ── Charge ponctuelle sur poutre ────────────────────────────────────
        elif action == "add_point_load_on_beam":
            beam_id = str(cmd.get("beam_id", ""))
            beam = next((b for b in model.beams if b.id == beam_id), None)
            if not beam:
                raise ValueError(f"Poutre '{beam_id}' introuvable")
            position_ratio = float(cmd.get("position_ratio", 0.5))
            fx = float(cmd.get("fx", 0))
            fy = float(cmd.get("fy", 0))
            load = model.add_point_load_on_beam(beam, position_ratio, fx, fy)
            self.canvas.add_point_load_on_beam_visual(load)
            self._append(
                "Him AI",
                f"📍 Charge ponctuelle sur <b>{beam_id}</b> "
                f"@ {position_ratio*100:.0f}% — "
                f"Fx={fx:+.2f} kN  Fy={fy:+.2f} kN"
            )

        elif action == "delete_point_load_on_beam":
            load_id = str(cmd.get("load_id", ""))
            load = next((p for p in model.point_loads_on_beams if p.id == load_id), None)
            if not load:
                raise ValueError(f"Charge '{load_id}' introuvable")
            if hasattr(load, "graphics_item") and load.graphics_item:
                scene.removeItem(load.graphics_item)
            model.remove_point_load_on_beam(load)
            self._append("Him AI", f"🗑️ Charge <b>{load_id}</b> supprimée")

        elif action == "delete_all_point_loads_on_beam":
            beam_id = str(cmd.get("beam_id", ""))
            beam = next((b for b in model.beams if b.id == beam_id), None)
            if not beam:
                raise ValueError(f"Poutre '{beam_id}' introuvable")
            count = len(beam.point_loads_on_beam)
            for load in list(beam.point_loads_on_beam):
                if hasattr(load, "graphics_item") and load.graphics_item:
                    scene.removeItem(load.graphics_item)
                model.remove_point_load_on_beam(load)
            self._append("Him AI", f"🗑️ {count} charge(s) ponctuelle(s) supprimée(s) sur <b>{beam_id}</b>")

        # ── Charge répartie ─────────────────────────────────────────────────
        elif action == "add_distributed_load":
            beam_id = str(cmd.get("beam_id", ""))
            beam = next((b for b in model.beams if b.id == beam_id), None)
            if not beam:
                raise ValueError(f"Poutre '{beam_id}' introuvable")
            from structural_model import DistributedLoad
            load_type = str(cmd.get("load_type", "G")).upper()
            if load_type not in ("G", "Q", "G+Q"):
                load_type = "G"
            load = DistributedLoad(
                beam,
                w         = float(cmd.get("w", 0)),
                start_pos = float(cmd.get("start_pos", 0.0)),
                end_pos   = float(cmd.get("end_pos",   1.0)),
                load_type = load_type,
            )
            beam.distributed_loads.append(load)
            model.distributed_loads.append(load)
            self.canvas.add_distributed_load_visual(load)
            self._append(
                "Him AI",
                f"〰️ Charge répartie [{load_type}] sur <b>{beam_id}</b> — "
                f"w={load.w:+.2f} kN/m  "
                f"[{load.start_pos*100:.0f}%→{load.end_pos*100:.0f}%]"
            )

        elif action == "delete_distributed_load":
            beam_id = str(cmd.get("beam_id", ""))
            beam = next((b for b in model.beams if b.id == beam_id), None)
            if not beam:
                raise ValueError(f"Poutre '{beam_id}' introuvable")
            count = len(beam.distributed_loads)
            for load in list(beam.distributed_loads):
                if hasattr(load, "graphics_item") and load.graphics_item:
                    scene.removeItem(load.graphics_item)
                if load in model.distributed_loads:
                    model.distributed_loads.remove(load)
            beam.distributed_loads.clear()
            self._append("Him AI", f"🗑️ {count} charge(s) répartie(s) supprimée(s) sur <b>{beam_id}</b>")

        # ── Tout effacer ────────────────────────────────────────────────────
        elif action == "clear_all":
            scene.clear()
            model.nodes.clear()
            model.beams.clear()
            model.columns.clear()
            model.point_loads.clear()
            model.point_loads_on_beams.clear()
            model.distributed_loads.clear()
            model.lines.clear()
            self.canvas.temp_start = None
            if hasattr(self.canvas, "_last_results"):
                self.canvas._last_results = {}
            self._append("Him AI", "🗑️ <b>Tout effacé</b> — projet vierge prêt")

        else:
            self._append("Him AI", f"⚠️ Action inconnue : <code>{action}</code>")

    # ────────────────────────────────────────────────────────────────────────
    # Suppression propre d'une poutre
    # ────────────────────────────────────────────────────────────────────────
    def _delete_beam(self, beam):
        model = self.canvas.model
        scene = self.canvas.scene
        for n in (beam.node_start, beam.node_end):
            if beam in n.connected_beams:
                n.connected_beams.remove(beam)
        # Supprimer les charges ponctuelles sur la poutre
        for load in list(getattr(beam, "point_loads_on_beam", [])):
            gi = getattr(load, "graphics_item", None)
            if gi is not None:
                try:
                    scene.removeItem(gi)
                except Exception:
                    pass
                load.graphics_item = None
            if load in model.point_loads_on_beams:
                model.point_loads_on_beams.remove(load)
        beam.point_loads_on_beam.clear()
        # Supprimer les charges réparties sur la poutre
        for load in list(getattr(beam, "distributed_loads", [])):
            gi = getattr(load, "graphics_item", None)
            if gi is not None:
                try:
                    scene.removeItem(gi)
                except Exception:
                    pass
                load.graphics_item = None
            if load in model.distributed_loads:
                model.distributed_loads.remove(load)
        beam.distributed_loads.clear()
        if beam in model.beams:
            model.beams.remove(beam)
        if beam.graphics_item:
            scene.removeItem(beam.graphics_item)

    # ────────────────────────────────────────────────────────────────────────
    def _on_error(self, error: str):
        self._append("❌", f'<span style="color:#ef5350">{error}</span>')