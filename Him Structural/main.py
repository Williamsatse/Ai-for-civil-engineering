# main.py
"""
Fenêtre principale de l'application Him Structural.

AMÉLIORATIONS :
  1. Messages de statut colorés et informatifs
  2. Confirmation avant suppression
  3. Validation des actions utilisateur
  4. Interface plus réactive
  5. Système multilingue (FR / EN / ZH) avec application immédiate
  6. Bugs corrigés :
     - Undo libellé "canceled" → tr("menu_edit_undo")
     - M = 174 hardcodé → utilise Mmax réel depuis full_analysis_results
     - last_analysis_results → full_analysis_results (unifié)
"""

import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QToolBar, QStatusBar,
    QFileDialog, QPushButton, QVBoxLayout, QLabel, QMessageBox, QDialog
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QIcon, QAction, QActionGroup, QColor, QPalette

from settings_dialog import SettingsDialog
from canvas import GraphicsCanvas
from structural_model import StructuralModel
from section_manager import SectionLibrary
from data_manager import DataManager
from ui.properties_panel import PropertiesPanel
from ui.sections_panel import SectionsPanel
from ui.loads_dialog import LoadsDialog
from ui.him_ai_dialog import HimAIDialog
from ui.load_combinations_dialog import LoadCombinationsDialog
from moteur_calculations import StructuralAnalyzer
from ui.diagrams_dialog import DiagramsDialog
from chinese_standard import RectangularSection
from language_manager import tr, set_language, get_language, register_language_callback
import json


class MainWindow(QMainWindow):
    settings_changed = Signal()

    def __init__(self):
        super().__init__()
        self.resize(1280, 820)
        self.setMinimumSize(960, 640)

        # ── Paramètres par défaut ──────────────────────────────────────────
        self.settings = {
            "unit_system": "Metric",
            "length_unit": "mm",
            "force_unit":  "kN",
            "decimals":    3,
            "invert_bmd":  False,
            "language":    "fr",
        }
        self.load_settings()

        # Appliquer la langue sauvegardée
        saved_lang = self.settings.get("language", "fr")
        if saved_lang in ("fr", "en", "zh"):
            set_language(saved_lang)

        self.setWindowTitle(tr("app_title"))

        self.full_analysis_results: dict = {}
        self.current_displayed_combo = None

        self.load_combinations = []
        self._load_combinations_from_file()

        # ── Modèle de données ─────────────────────────────────────────────
        self.model = StructuralModel()
        self.section_library = SectionLibrary()
        self.active_section_name = None

        # ── Canvas central ────────────────────────────────────────────────
        self.canvas = GraphicsCanvas(self.model)
        self.canvas.main_window = self
        self.canvas.diagram_settings = self._load_diagram_settings()
        self.setCentralWidget(self.canvas)

        # ── Barre de statut ───────────────────────────────────────────────
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._status_coords  = QLabel("X: 0.00  Y: 0.00")
        self._status_mode    = QLabel("")
        self._status_message = QLabel("")
        self.status.addWidget(self._status_message)
        self.status.addPermanentWidget(self._status_coords)
        self.status.addPermanentWidget(QLabel(" | "))
        self.status.addPermanentWidget(self._status_mode)
        self.canvas.mouse_moved.connect(self.update_status)

        # ── Panneaux latéraux ─────────────────────────────────────────────
        self.properties_panel = PropertiesPanel(self)
        self.sections_panel   = SectionsPanel(self)
        self.properties_panel.set_section_library(self.section_library)
        self.settings_changed.connect(self.properties_panel.refresh_from_settings)

        self._dock_right = QDockWidget("", self)
        self._dock_right.setWidget(self.properties_panel)
        self._dock_right.setMinimumWidth(240)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_right)

        self._dock_left = QDockWidget("", self)
        self._dock_left.setWidget(self.sections_panel)
        self._dock_left.setMinimumWidth(220)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_left)

        # ── Connexions ─────────────────────────────────────────────────────
        self.canvas.node_selected.connect(self.properties_panel.update_from_selection)
        self.canvas.beam_selected.connect(self.properties_panel.update_from_selection)
        self.canvas.beam_selected.connect(self.sections_panel.update_preview_from_beam)
        self.sections_panel.sectionChanged.connect(self.on_active_section_changed)

        # ── Menus & Toolbar ───────────────────────────────────────────────
        self._create_menus()
        self._create_toolbar()

        # ── S'abonner aux changements de langue ───────────────────────────
        register_language_callback(self._on_language_changed)

        # ── Mode par défaut ───────────────────────────────────────────────
        self.set_tool("select")
        self._update_dock_titles()
        self.show_status_message(tr("status_ready"), "success")

    # ══════════════════════════════════════════════════════════════════════
    # TRADUCTION EN DIRECT
    # ══════════════════════════════════════════════════════════════════════

    def _on_language_changed(self):
        """Callback déclenché à chaque changement de langue."""
        self.setWindowTitle(tr("app_title"))
        self._update_dock_titles()
        self._rebuild_menus()
        self._rebuild_toolbar()
        # Panneaux persistants
        if hasattr(self.properties_panel, "retranslate_ui"):
            self.properties_panel.retranslate_ui()
        if hasattr(self.sections_panel, "retranslate_ui"):
            self.sections_panel.retranslate_ui()

    def _update_dock_titles(self):
        self._dock_right.setWindowTitle(tr("dock_properties"))
        self._dock_left.setWindowTitle(tr("dock_sections"))

    def _rebuild_menus(self):
        """Reconstruit la barre de menus avec la nouvelle langue."""
        self.menuBar().clear()
        self._create_menus()

    def _rebuild_toolbar(self):
        """Reconstruit la toolbar avec la nouvelle langue."""
        for tb in self.findChildren(QToolBar):
            self.removeToolBar(tb)
            tb.deleteLater()
        self._create_toolbar()
        # Remettre le bon mode actif
        if hasattr(self, "canvas"):
            cur = getattr(self.canvas, "_mode", "select")
            self.set_tool(cur)

    # ══════════════════════════════════════════════════════════════════════
    # STATUT
    # ══════════════════════════════════════════════════════════════════════

    def show_status_message(self, message, msg_type="info", duration=5000):
        colors = {
            "success": "#22c55e",
            "error":   "#ef4444",
            "warning": "#f59e0b",
            "info":    "#60a5fa",
        }
        color = colors.get(msg_type, "#e0e0e0")
        self._status_message.setText(
            f"<span style='color:{color};font-weight:bold'>{message}</span>"
        )
        self._status_message.setStyleSheet(f"color: {color}; font-weight: bold;")
        if duration > 0:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(duration, lambda: self._status_message.setText(""))

    # ══════════════════════════════════════════════════════════════════════
    # PARAMÈTRES
    # ══════════════════════════════════════════════════════════════════════

    def load_settings(self):
        try:
            with open("settings.json", "r", encoding="utf-8") as f:
                loaded = json.load(f)
                self.settings.update(loaded)
        except Exception:
            self.save_settings_to_file()

    def save_settings_to_file(self):
        with open("settings.json", "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=2, ensure_ascii=False)

    def apply_settings(self, new_settings: dict):
        self.settings.update(new_settings)
        self.save_settings_to_file()
        self.settings_changed.emit()
        self.show_status_message(tr("status_settings_applied"), "success")
        if hasattr(self, "properties_panel"):
            self.properties_panel.refresh_from_settings()
        self.canvas.scene.update()
        self.canvas.viewport().update()

    # ══════════════════════════════════════════════════════════════════════
    # COMBINAISONS
    # ══════════════════════════════════════════════════════════════════════

    def open_load_combinations(self):
        dlg = LoadCombinationsDialog(self)
        dlg.exec()

    def _load_combinations_from_file(self):
        try:
            with open("load_combinations.json", "r", encoding="utf-8") as f:
                self.load_combinations = json.load(f)
        except Exception:
            self.load_combinations = self._default_combinations()

    def _default_combinations(self):
        return [{
            "id": 1,
            "name": "Load Combinaison 1",
            "dead": 1.35, "live": 1.5, "wind": 1.0, "snow": 1.0,
            "roof": 1.0, "rain": 1.0, "earthquake": 1.0,
            "selfweight": 1.25, "criteria": "ULS",
        }]

    def save_combinations_to_file(self):
        with open("load_combinations.json", "w", encoding="utf-8") as f:
            json.dump(self.load_combinations, f, indent=2, ensure_ascii=False)

    # ══════════════════════════════════════════════════════════════════════
    # MENUS
    # ══════════════════════════════════════════════════════════════════════

    def _create_menus(self):
        menubar = self.menuBar()

        # ── Fichier ──────────────────────────────────────────────────────
        file_menu = menubar.addMenu(tr("menu_file"))
        file_menu.addAction(tr("menu_file_save"), self.save_project, "Ctrl+S")
        file_menu.addAction(tr("menu_file_open"), self.load_project,  "Ctrl+O")
        file_menu.addSeparator()
        file_menu.addAction(tr("menu_file_exit"), self.close, "Ctrl+Q")

        settings_action = menubar.addAction(tr("menu_settings"))
        settings_action.triggered.connect(self.open_settings)

        # ── Édition ──────────────────────────────────────────────────────
        edit_menu = menubar.addMenu(tr("menu_edit"))
        # BUG CORRIGÉ : était "canceled" au lieu de "Annuler"
        edit_menu.addAction(tr("menu_edit_undo"),   self.canvas.undo, "Ctrl+Z")
        edit_menu.addAction(tr("menu_edit_redo"),   self.canvas.redo, "Ctrl+Y")
        edit_menu.addAction(tr("menu_edit_delete"), self._delete_selected, "Delete")

        # ── Vue ───────────────────────────────────────────────────────────
        view_menu = menubar.addMenu(tr("menu_view"))
        view_menu.addAction(tr("menu_view_section"), self.open_section_view)
        view_menu.addAction(tr("menu_view_2d"),       self.open_plan_view)

        snap_action = view_menu.addAction(tr("menu_view_snap"))
        snap_action.setCheckable(True)
        snap_action.setChecked(True)
        snap_action.toggled.connect(lambda v: setattr(self.canvas, "snap_to_grid", v))

        grid_action = view_menu.addAction(tr("menu_view_grid"))
        grid_action.setCheckable(True)
        grid_action.setChecked(True)
        grid_action.toggled.connect(self._toggle_grid)

        # ── Diagrammes ────────────────────────────────────────────────────
        diagrams_menu = menubar.addMenu(tr("menu_diagrams"))
        diagrams_menu.addAction(tr("menu_diagrams_config"), self.open_diagrams_dialog)
        diagrams_menu.addSeparator()
        self.combo_submenu = diagrams_menu.addMenu(tr("menu_diagrams_combo"))
        self.combo_submenu.aboutToShow.connect(self._populate_combo_menu)
        diagrams_menu.addAction(tr("menu_diagrams_show_bmd"), self.toggle_bmd)
        diagrams_menu.addAction(tr("menu_diagrams_show_sfd"), self.toggle_sfd)
        diagrams_menu.addSeparator()
        diagrams_menu.addAction(tr("menu_diagrams_auto_scale"),   self.set_auto_scale)
        diagrams_menu.addAction(tr("menu_diagrams_manual_scale"), self.set_manual_scale)

        # ── Calculs ───────────────────────────────────────────────────────
        calc_menu = menubar.addMenu(tr("menu_calc"))
        calc_menu.addAction(tr("menu_calc_combos"), self.open_load_combinations)
        calc_menu.addAction(tr("menu_calc_rebars"), self.Area_rebars)
        calc_menu.addAction(tr("menu_calc_run"),    self.run_structural_analysis)
        calc_menu.addSeparator()

        # ── Him IA ────────────────────────────────────────────────────────
        ia_menu = menubar.addMenu(tr("menu_him_ai"))
        ia_menu.addAction(tr("menu_him_ai_open"), self.open_him_ai)

        menubar.addMenu(tr("menu_help"))

    # ══════════════════════════════════════════════════════════════════════
    # TOOLBAR
    # ══════════════════════════════════════════════════════════════════════

    def _create_toolbar(self):
        toolbar = QToolBar(tr("tool_select"))
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)
        self.tools = {}

        def add_tool(name, icon_path, label_key, tip_key, mode):
            action = QAction(tr(label_key), self)
            icon = QIcon(icon_path)
            if not icon.isNull():
                action.setIcon(icon)
            action.setToolTip(tr(tip_key))
            action.setCheckable(True)
            action.setStatusTip(tr(tip_key))
            action.setData(mode)
            action.triggered.connect(
                lambda checked, m=mode: self.set_tool(m) if checked else None
            )
            toolbar.addAction(action)
            self.tool_group.addAction(action)
            self.tools[name] = action
            return action

        add_tool("select",   "icons/select.png",   "tool_select", "tool_select_tip", "select")
        toolbar.addSeparator()
        add_tool("node",     "icons/node.png",     "tool_node",   "tool_node_tip",   "node")
        add_tool("beam",     "icons/beam.png",     "tool_beam",   "tool_beam_tip",   "beam")
        toolbar.addSeparator()
        add_tool("add_load", "icons/add_load.png", "tool_load",   "tool_load_tip",   "add_load")

        self.tools["select"].setShortcut("S")
        self.tools["node"].setShortcut("N")
        self.tools["beam"].setShortcut("B")
        self.tools["add_load"].setShortcut("L")

        toolbar.setStyleSheet("""
            QToolBar {
                background: #1e1e2e;
                border-bottom: 1px solid #333;
                spacing: 4px;
                padding: 4px 6px;
            }
            QToolButton {
                padding: 6px 10px;
                border: 1px solid transparent;
                border-radius: 6px;
                color: #d0d0d0;
                font-size: 11px;
            }
            QToolButton:checked {
                background: rgba(0, 120, 215, 0.30);
                border: 1px solid #0078d7;
                color: #ffffff;
            }
            QToolButton:hover:!checked {
                background: rgba(255, 255, 255, 0.10);
                border: 1px solid #555;
            }
        """)

    # ══════════════════════════════════════════════════════════════════════
    # OUTILS & MODES
    # ══════════════════════════════════════════════════════════════════════

    def set_tool(self, mode: str):
        self.canvas.set_mode(mode)

        if mode == "add_load":
            if not self.model.nodes and not self.model.beams:
                QMessageBox.information(self, tr("info_title"), tr("loads_no_beam"))
                self.set_tool("select")
                return
            dlg = LoadsDialog(self)
            dlg.exec()
            self.set_tool("select")
            return

        for act in self.tool_group.actions():
            act.setChecked(act.data() == mode)

        mode_labels = {
            "select": tr("mode_select"),
            "node":   tr("mode_node"),
            "beam":   tr("mode_beam"),
        }
        label = mode_labels.get(mode, mode.capitalize())
        self._status_mode.setText(tr("status_mode", label))
        self.status.showMessage(tr("status_mode", label), 3000)

    def _delete_selected(self):
        self.canvas._delete_selected_with_confirmation()

    def _toggle_grid(self, visible: bool):
        self.canvas.show_grid = visible
        self.canvas.scene.update()

    # ══════════════════════════════════════════════════════════════════════
    # SECTIONS
    # ══════════════════════════════════════════════════════════════════════

    def on_active_section_changed(self, section_name: str):
        self.active_section_name = section_name or None
        self.canvas.active_section_name = self.active_section_name
        if self.active_section_name:
            msg = tr("status_section_active", self.active_section_name)
        else:
            msg = tr("status_no_section")
        self.show_status_message(msg, "info", 3500)

    def refresh_all_section_combos(self):
        if hasattr(self, "sections_panel"):
            self.sections_panel.update_section_list()
        if hasattr(self, "properties_panel"):
            self.properties_panel.refresh_section_combo()

    # ══════════════════════════════════════════════════════════════════════
    # COORDONNÉES
    # ══════════════════════════════════════════════════════════════════════

    def update_status(self, x: float, y: float):
        self._status_coords.setText(f"X: {x:.2f}  Y: {y:.2f}")

    # ══════════════════════════════════════════════════════════════════════
    # FICHIERS
    # ══════════════════════════════════════════════════════════════════════

    def save_project(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, tr("menu_file_save"), "", "Projet structure (*.json)"
        )
        if filename:
            ok = DataManager.save_project(filename, self.canvas)
            if ok:
                self.show_status_message(tr("status_saved", os.path.basename(filename)), "success", 5000)
            else:
                self.show_status_message(tr("status_save_error"), "error", 8000)

    def load_project(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, tr("menu_file_open"), "", "Projet structure (*.json)"
        )
        if filename:
            ok = DataManager.load_project(filename, self.canvas)
            if ok:
                self.properties_panel.update_from_selection(None)
                self.show_status_message(tr("status_loaded", os.path.basename(filename)), "success", 5000)
            else:
                self.show_status_message(tr("status_load_error"), "error", 8000)

    def open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    # ══════════════════════════════════════════════════════════════════════
    # HIM AI
    # ══════════════════════════════════════════════════════════════════════

    def open_him_ai(self):
        dlg = HimAIDialog(self.canvas, self)
        dlg.show()

    # ══════════════════════════════════════════════════════════════════════
    # ANALYSE STRUCTURALE
    # ══════════════════════════════════════════════════════════════════════

    def draw_analysis_diagrams(self, results_dict):
        for beam_id, res in results_dict.items():
            print(f"DEBUG: {beam_id}: Mmax={res.get('Mmax')}, Vmax={res.get('Vmax')}")

    def run_structural_analysis(self):
        is_valid, error_msg = self.model.validate_for_analysis()
        if not is_valid:
            QMessageBox.warning(self, tr("analysis_model_invalid"), error_msg)
            return

        analyzer = StructuralAnalyzer(self)
        results = analyzer.run_analysis()

        if results:
            self.full_analysis_results = results
            self.current_displayed_combo = None
            self.show_status_message(
                tr("status_analysis_ok", len(results)), "success", 5000
            )
            self.canvas.draw_analysis_diagrams(self._get_displayed_results())
        else:
            self.show_status_message(tr("status_analysis_error"), "error", 5000)

    def open_diagrams_dialog(self):
        dlg = DiagramsDialog(self)
        dlg.exec()

    def _populate_combo_menu(self):
        self.combo_submenu.clear()

        if not self.full_analysis_results:
            act = self.combo_submenu.addAction(tr("menu_diagrams_no_analysis"))
            act.setEnabled(False)
            return

        env = self.combo_submenu.addAction(tr("menu_diagrams_envelope"))
        env.setCheckable(True)
        env.setChecked(self.current_displayed_combo is None)
        env.triggered.connect(lambda checked, n=None: self._switch_combo(n) if checked else None)

        self.combo_submenu.addSeparator()

        combos = set()
        for data in self.full_analysis_results.values():
            combos.update(data.keys())
        for name in sorted(combos):
            act = self.combo_submenu.addAction(name)
            act.setCheckable(True)
            act.setChecked(self.current_displayed_combo == name)
            act.triggered.connect(lambda checked, n=name: self._switch_combo(n) if checked else None)

    def _switch_combo(self, combo_name):
        self.current_displayed_combo = combo_name
        displayed = self._get_displayed_results()
        if displayed and hasattr(self, "canvas"):
            self.canvas.draw_analysis_diagrams(displayed)
        txt = combo_name or tr("menu_diagrams_envelope")
        self.show_status_message(tr("status_combo_shown", txt), "success", 4000)

    def _get_displayed_results(self):
        """
        Retourne les résultats plats {beam_id: {Mmax, Vmax, L_m, …}} à afficher.
        Enveloppe = la combinaison avec le Mmax absolu le plus élevé pour chaque poutre.
        BUG CORRIGÉ : était incohérent avec last_analysis_results.
        """
        if not self.full_analysis_results:
            return {}

        if self.current_displayed_combo is None:
            # Enveloppe : pire Mmax pour chaque poutre
            return {
                bid: max(combos.values(), key=lambda r: abs(r.get("Mmax", 0)))
                for bid, combos in self.full_analysis_results.items()
            }
        else:
            return {
                bid: data[self.current_displayed_combo]
                for bid, data in self.full_analysis_results.items()
                if self.current_displayed_combo in data
            }

    def toggle_bmd(self):
        if hasattr(self.canvas, "diagram_settings"):
            self.canvas.diagram_settings["show_bmd"] = not self.canvas.diagram_settings.get("show_bmd", True)
            if self.full_analysis_results:
                self.canvas.draw_analysis_diagrams(self._get_displayed_results())

    def toggle_sfd(self):
        if hasattr(self.canvas, "diagram_settings"):
            self.canvas.diagram_settings["show_sfd"] = not self.canvas.diagram_settings.get("show_sfd", True)
            if self.full_analysis_results:
                self.canvas.draw_analysis_diagrams(self._get_displayed_results())

    def set_auto_scale(self):
        if hasattr(self.canvas, "diagram_settings"):
            self.canvas.diagram_settings["bmd_scale_mode"] = "auto"
            self.canvas.diagram_settings["sfd_scale_mode"] = "auto"
            displayed = self._get_displayed_results()
            if displayed:
                self.canvas.draw_analysis_diagrams(displayed)
            self.show_status_message(tr("status_auto_scale"), "success")

    def set_manual_scale(self):
        self.open_diagrams_dialog()

    def _load_diagram_settings(self):
        try:
            with open("diagrams_settings.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "show_bmd": True,
                "show_sfd": True,
                "bmd_color": "#ef4444",
                "sfd_color": "#3b82f6",
                "bmd_line_width": 2.5,
                "sfd_line_width": 2.5,
                "bmd_fill": True,
                "sfd_fill": False,
                "diagram_offset": 80,
            }

    def open_plan_view(self):
        pass

    def open_section_view(self):
        pass

    def format_length(self, mm: float) -> str:
        unit = self.settings.get("length_unit", "mm")
        dec  = self.settings.get("decimals", 3)
        if unit == "m":
            return f"{mm/1000:.{dec}f} m"
        elif unit == "cm":
            return f"{mm/10:.{dec-1}f} cm"
        else:
            return f"{mm:.{dec-1}f} mm"

    # ══════════════════════════════════════════════════════════════════════
    # FERRAILLAGE — BUG CORRIGÉ : M = 174 hardcodé → Mmax réel
    # ══════════════════════════════════════════════════════════════════════

    def Area_rebars(self):
        """Calcul et affichage des résultats de section rectangulaire (norme chinoise)."""
        # Trouver la poutre sélectionnée
        selected_beam = None
        for beam in self.model.beams:
            gi = getattr(beam, "graphics_item", None)
            if gi and (getattr(gi, "_selected", False) or gi.isSelected()):
                selected_beam = beam
                break

        if not selected_beam:
            QMessageBox.warning(
                self, tr("rebar_no_beam"), tr("rebar_no_beam_msg")
            )
            return

        # ── BUG CORRIGÉ : récupérer le Mmax réel depuis full_analysis_results ──
        beam_id = selected_beam.id
        M = None

        # 1. Chercher dans full_analysis_results (résultats complets par combinaison)
        if self.full_analysis_results and beam_id in self.full_analysis_results:
            combos = self.full_analysis_results[beam_id]
            if combos:
                # Utiliser la pire combinaison (Mmax absolu)
                best = max(combos.values(), key=lambda r: abs(r.get("Mmax", 0)))
                M = best.get("Mmax", 0.0)

        # 2. Fallback : résultats directs sur la poutre (ancienne API)
        if M is None:
            direct = getattr(selected_beam, "analysis_results", None)
            if direct:
                M = direct.get("Mmax", 0.0)

        if M is None:
            QMessageBox.warning(
                self, tr("rebar_no_analysis"), tr("rebar_no_analysis_msg")
            )
            return

        if M <= 0:
            QMessageBox.information(
                self, tr("rebar_zero_moment"),
                tr("rebar_zero_moment_msg", M)
            )
            return

        sec_name    = getattr(selected_beam, "section_name", None)
        section_obj = self.section_library.get_section(sec_name) if sec_name else None

        if not section_obj or section_obj.shape_type != "rectangle":
            QMessageBox.warning(
                self, tr("rebar_not_rect"), tr("rebar_not_rect_msg")
            )
            return

        current_grade = getattr(selected_beam, "concrete_grade", "C30")
        cover   = getattr(selected_beam, "cover",   60.0)
        a_prime = getattr(selected_beam, "a_prime", 35.0)

        rc = RectangularSection(
            b=section_obj.b, h=section_obj.h,
            concrete_grade=current_grade, steel_grade="HRB335",
            cover=cover, a_prime=a_prime,
        )
        result = rc.calculate_flexure(M)

        # ── Dialogue résultats ────────────────────────────────────────────
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("rebar_title", beam_id))
        dlg.resize(740, 700)
        dlg.setStyleSheet(
            "QDialog{background:#12121f;color:#e0e0e0;}"
            "QPushButton{background:#1a4a8a;color:#fff;border:none;"
            "border-radius:5px;padding:8px 22px;font-size:13px;}"
            "QPushButton:hover{background:#2060b0;}"
        )

        from PySide6.QtWidgets import QScrollArea
        lay = QVBoxLayout(dlg)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:#12121f;}")
        lbl = QLabel()
        lbl.setTextFormat(Qt.RichText)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size:12px;padding:14px;background:#12121f;color:#e0e0e0;")

        rtype     = result.get("type", "single")
        is_double = rtype == "double"
        fc_val    = result.get("fc_MPa", rc.fc)
        h0_val    = result.get("h0_mm", rc.h0)

        txt = (
            f"<h3 style='color:#4fc3f7;margin-bottom:4px;'>"
            f"Poutre {beam_id} — Ferraillage GB 50010 §9.2.1</h3>"
            f"<span style='color:#888;'>"
            f"b={section_obj.b:.0f} × h={section_obj.h:.0f} mm  |  "
            f"{current_grade} (fc={fc_val} N/mm²)  |  HRB335  |  h₀={h0_val:.1f} mm"
            f"</span><br>"
            f"<b style='font-size:14px;'>M = {M:.2f} kN·m</b><br><br>"
        )

        if is_double:
            txt += (
                f"<span style='color:#e74c3c;font-size:13px;'>"
                f"⚠️  FERRAILLAGE DOUBLE — M &gt; Mu_max = {result.get('Mu_max_kNm',0):.2f} kN·m</span><br>"
                f"{result.get('x_check_status','')}  &nbsp;|&nbsp; "
                f"Mu1 = {result.get('Mu1_kNm',0):.2f}  Mu2 = {result.get('Mu2_kNm',0):.2f} kN·m<br>"
                f"<b>As' (compression) = {result.get('As_prime_mm2',0):.0f} mm²</b><br>"
                f"<b>As  (traction)    = {result.get('As_final_mm2',0):.0f} mm²</b><br>"
                f"Mu_cap = {result.get('Mu_capacity_kNm',0):.2f} kN·m  &nbsp;&mdash;&nbsp; "
                f"{result.get('status','')}<br>"
            )
        else:
            txt += (
                f"<span style='color:#27ae60;font-size:13px;'>"
                f"✅  FERRAILLAGE SIMPLE — M ≤ Mu_max = {result.get('Mu_max_kNm',0):.2f} kN·m</span><br>"
                f"α_s = {result.get('alpha_s',0):.4f}  &nbsp;|&nbsp;  "
                f"ξ = {result.get('xi',0):.4f} ≤ ξ_b = {result.get('xi_b',0)}<br>"
                f"<b>As requis = {result.get('As_final_mm2',0):.0f} mm²</b><br>"
                f"Mu_cap = {result.get('Mu_capacity_kNm',0):.2f} kN·m  &nbsp;&mdash;&nbsp; "
                f"{result.get('status','')}<br>"
            )

        def _tbl(solutions, title, max_s=8):
            if not solutions:
                return ""
            rows = ""
            for sol in solutions[:max_s]:
                typ   = "M" if sol.get("is_mixed") else "U"
                disp  = sol.get("disposition", "—")
                area  = sol.get("area_provided_mm2", 0)
                ecart = sol.get("oversize_mm2", 0)
                eta   = sol.get("efficiency", 0) * 100
                sc    = sol.get("constructibility", sol.get("constructibility_score", 0))
                best  = sol.get("rank", 99) == 1
                if best:
                    bg = "#0a2a0a"; fg = "#55ee77"; star = "🏆 "
                elif typ == "M":
                    bg = "#0a1d33"; fg = "#77bbff"; star = "⚡ "
                else:
                    bg = "#1c1c2e"; fg = "#cccccc"; star = ""
                badge = (
                    "<span style='background:#1a3a6a;color:#77bbff;"
                    "padding:0 4px;border-radius:3px;font-size:10px;font-weight:bold;'>M</span> "
                    if typ == "M" else
                    "<span style='background:#1a3a1a;color:#77ee77;"
                    "padding:0 4px;border-radius:3px;font-size:10px;font-weight:bold;'>U</span> "
                )
                rows += (
                    f"<tr style='background:{bg};'>"
                    f"<td style='padding:4px 8px;color:{fg};'>{badge}{star}{disp}</td>"
                    f"<td style='padding:4px 8px;color:{fg};text-align:right;'><b>{area:.0f}</b></td>"
                    f"<td style='padding:4px 8px;color:#ffaa44;text-align:right;'>{ecart:+.1f}</td>"
                    f"<td style='padding:4px 8px;color:#88ffaa;text-align:right;'>{eta:.1f}%</td>"
                    f"<td style='padding:4px 8px;color:#aaa;text-align:right;'>{sc:.0f}</td>"
                    "</tr>"
                )
            return (
                f"<br><b style='color:#4fc3f7;'>{title}</b>"
                f"&nbsp;&nbsp;<span style='font-size:10px;color:#555;'>"
                f"<span style='background:#1a3a1a;color:#77ee77;padding:0 3px;"
                f"border-radius:2px;'>U</span> Uniforme (même Ø) &nbsp;"
                f"<span style='background:#1a3a6a;color:#77bbff;padding:0 3px;"
                f"border-radius:2px;'>M</span> Mixte (2 Ø différents)"
                f"</span><br>"
                f"<table style='border-collapse:collapse;font-size:11px;width:100%;margin:4px 0 10px 0;'>"
                f"<tr style='background:#18283a;color:#5577aa;font-size:10px;'>"
                f"<th style='padding:4px 8px;text-align:left;'>Disposition</th>"
                f"<th style='padding:4px 8px;'>As mm²</th>"
                f"<th style='padding:4px 8px;'>Écart</th>"
                f"<th style='padding:4px 8px;'>η</th>"
                f"<th style='padding:4px 8px;'>Sc</th>"
                f"</tr>{rows}</table>"
            )

        if is_double:
            best_c = result.get("best_comp_label") or result.get("best_disposition_compression", "—")
            best_t = result.get("best_tension_label") or result.get("best_disposition_tension", "—")
            txt += (
                f"<br><span style='color:#e74c3c;'>🏆 COMPRESSION : <b>{best_c}</b></span>"
                + _tbl(result.get("top_solutions_compression", []),
                       "Compression — toutes options (Uniforme + Mixte)", 6)
                + f"<span style='color:#27ae60;'>🏆 TRACTION : <b>{best_t}</b></span>"
                + _tbl(result.get("top_solutions_tension", []),
                       "Traction — toutes options (Uniforme + Mixte)", 8)
            )
        else:
            best_s = result.get("best_bar_label") or result.get("best_disposition", "—")
            txt += (
                f"<br><span style='color:#27ae60;'>🏆 MEILLEURE SOLUTION : <b>{best_s}</b></span>"
                + _tbl(result.get("top_solutions_full", []),
                       "Toutes les solutions (Uniforme + Mixte)", 8)
            )

        lbl.setText(txt)
        scroll.setWidget(lbl)
        lay.addWidget(scroll)
        btn_close = QPushButton(tr("rebar_close"))
        btn_close.clicked.connect(dlg.accept)
        lay.addWidget(btn_close)
        dlg.exec()


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())