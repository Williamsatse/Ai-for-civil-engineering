# sections_panel.py  ← Remplace tout le fichier par celui-ci

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QPushButton,
    QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
    QComboBox, QLabel, QDialogButtonBox, QMessageBox, QListWidgetItem
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush
from PySide6.QtCore import Qt, QRectF, Signal
from section_manager import Section
from chinese_standard import ChineseConcrete


# ════════════════════════════════════════════════════════════
# WIDGET DE PRÉVISUALISATION DE SECTION (déplacé ici)
# ════════════════════════════════════════════════════════════
class SectionPreviewWidget(QWidget):
    MARGIN = 20

    def __init__(self, parent=None):
        super().__init__(parent)
        self.section = None
        self.setFixedHeight(170)

    def set_section(self, section):
        self.section = section
        self.update()

    def clear(self):
        self.section = None
        self.update()

    def _compute_scale(self) -> float:
        if not self.section: return 1.0
        max_dim = max(getattr(self.section, "b", 1) or 1,
                      getattr(self.section, "bf", 1) or 1,
                      getattr(self.section, "h", 1) or 1)
        avail = min(self.width(), self.height()) - 2 * self.MARGIN
        return (avail / max_dim) * 0.82 if max_dim > 0 else 1.0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#1a1a2e"))

        if not self.section:
            painter.setPen(QColor("#555"))
            painter.drawText(self.rect(), Qt.AlignCenter, "Aucune section sélectionnée")
            return

        sec = self.section
        scale = self._compute_scale()
        cx, cy = self.width() / 2, self.height() / 2

        mat = getattr(sec, "material", "Steel").lower()
        if any(x in mat for x in ["steel", "acier"]):
            fill_color = QColor("#4fc3f7")  # Bleu clair pour l'acier
        elif any(x in mat for x in ["concrete", "béton"]):
            fill_color = QColor("#9e9e9e")  # Gris pour le béton
        elif any(x in mat for x in ["wood", "bois"]):
            fill_color = QColor("#a5d6a7")  # Vert clair pour le bois
        else:
            fill_color = QColor("#94a3b8")

        painter.setPen(QPen(QColor("#ffffff"), 2))
        painter.setBrush(QBrush(fill_color))

        shape = getattr(sec, "shape_type", "rectangle").lower()
        if shape == "rectangle":
            w, h = sec.b * scale, sec.h * scale
            painter.drawRect(QRectF(cx - w/2, cy - h/2, w, h))
        elif shape in ("i", "ipe", "hea", "heb") or shape.startswith(("ipe", "hea", "heb")):
            b, h, tw, tf = sec.b*scale, sec.h*scale, max(sec.tw*scale, 3), max(sec.tf*scale, 3)
            x0, y0 = cx - b/2, cy - h/2
            painter.drawRect(QRectF(x0, y0, b, tf))
            painter.drawRect(QRectF(x0, y0 + h - tf, b, tf))
            painter.drawRect(QRectF(cx - tw/2, y0 + tf, tw, h - 2*tf))
        elif shape == "t":
            bf, h, tw, tf = (sec.bf or sec.b)*scale, sec.h*scale, max(sec.tw*scale, 3), max(sec.tf*scale, 3)
            x0, y0 = cx - bf/2, cy - h/2
            painter.drawRect(QRectF(x0, y0, bf, tf))
            painter.drawRect(QRectF(cx - tw/2, y0 + tf, tw, h - tf))

        painter.setPen(QColor("#e0e0e0"))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(QRectF(0, self.height()-28, self.width(), 25), Qt.AlignCenter,
                         f"{sec.name}  |  {sec.material}")


class NewSectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("new section")
        self.setMinimumWidth(380)

        outer = QVBoxLayout(self)

        self.shape_combo = QComboBox()
        self.shape_combo.addItems(["Rectangle", "T", "I / HEA-IPE"])
        outer.addWidget(QLabel("Section type :"))
        outer.addWidget(self.shape_combo)

        # Combo grade beton
        self.grade_combo = QComboBox()
        self.grade_combo.addItems(list(ChineseConcrete.GRADES.keys()))
        self.grade_combo.setCurrentText("C30")
        self.grade_label = QLabel("Grade béton :")
        outer.addWidget(self.grade_label)
        outer.addWidget(self.grade_combo)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["— Custom —", "IPE 200", "IPE 300", "IPE 400", "HEA 200", "HEA 300", "HEA 400"])
        outer.addWidget(QLabel("Preset :"))
        outer.addWidget(self.preset_combo)
        self.preset_combo.currentTextChanged.connect(self._load_preset)

        self.form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("ex : Rect. 250x500")
        self.material_combo = QComboBox()
        self.material_combo.addItems(["Concrete", "Steel", "Wood"])
        self.form.addRow("Nom :", self.name_edit)
        self.form.addRow("Matériau :", self.material_combo)

        form_widget = QWidget()
        form_widget.setLayout(self.form)
        outer.addWidget(form_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

        self.current_b_spin = self.current_h_spin = self.current_tw_spin = None
        self.current_tf_spin = self.current_bf_spin = None

        self.shape_combo.currentTextChanged.connect(self._update_fields)
        self._update_fields("Rectangle")

        self.material_combo.currentTextChanged.connect(self._on_material_changed)
        self._on_material_changed("Concrete Type")

    def _on_material_changed(self, mat: str):
        is_concrete = mat == "Concrete Type"
        self.grade_label.setVisible(is_concrete)
        self.grade_combo.setVisible(is_concrete)

    def _load_preset(self, name: str):
        if name.startswith("—"): return
        presets = {
            "IPE 200": {"b": 100, "h": 200, "tw": 5.6, "tf": 8.5, "bf": None},
            "IPE 300": {"b": 150, "h": 300, "tw": 6.3, "tf": 10.5, "bf": None},
            "HEA 200": {"b": 200, "h": 200, "tw": 6.0, "tf": 10.0, "bf": None},
        }  

        if name in presets:
            p = presets[name]
            self.current_b_spin.setValue(p["b"])
            self.current_h_spin.setValue(p["h"])
            self.current_tw_spin.setValue(p["tw"])
            self.current_tf_spin.setValue(p["tf"])
            if p["bf"] is not None:
                self.current_bf_spin.setValue(p["bf"])

    def _update_fields(self, shape_text: str):
        while self.form.rowCount() > 2:
            self.form.removeRow(2)

        def spinbox(min_val, max_val, default, suffix="mm"):
            sp = QDoubleSpinBox()
            sp.setRange(min_val, max_val)
            sp.setValue(default)
            sp.setSuffix(f" {suffix}")
            sp.setDecimals(1)
            return sp

        b_sp = spinbox(10, 2000, 300)
        h_sp = spinbox(20, 3000, 500)
        tw_sp = spinbox(2, 200, 10)
        tf_sp = spinbox(2, 200, 15)
        bf_sp = spinbox(10, 2000, 200)

        shape = shape_text.lower()
        if "rectangle" in shape:
            self.form.addRow("Largeur b :", b_sp)
            self.form.addRow("Hauteur h :", h_sp)
        elif "t" == shape.strip():
            self.form.addRow("Largeur flange bf :", bf_sp)
            self.form.addRow("Hauteur totale h :", h_sp)
            self.form.addRow("Épaisseur âme tw :", tw_sp)
            self.form.addRow("Épaisseur flange tf :", tf_sp)
        else:
            self.form.addRow("Largeur ailes b :", b_sp)
            self.form.addRow("Hauteur totale h :", h_sp)
            self.form.addRow("Épaisseur âme tw :", tw_sp)
            self.form.addRow("Épaisseur ailes tf :", tf_sp)

        self.current_b_spin = b_sp
        self.current_h_spin = h_sp
        self.current_tw_spin = tw_sp
        self.current_tf_spin = tf_sp
        self.current_bf_spin = bf_sp

    def get_values(self) -> dict:
        return {
            "b": self.current_b_spin.value() if self.current_b_spin else 0,
            "h": self.current_h_spin.value() if self.current_h_spin else 0,
            "tw": self.current_tw_spin.value() if self.current_tw_spin else 0,
            "tf": self.current_tf_spin.value() if self.current_tf_spin else 0,
            "bf": self.current_bf_spin.value() if self.current_bf_spin else 0,
            "concrete_grade": self.grade_combo.currentText() if self.material_combo.currentText() == "Concrete" else None,
        }
# ════════════════════════════════════════════════════════════
# PANNEAU SECTIONS (avec preview en bas)
# ════════════════════════════════════════════════════════════
class SectionsPanel(QWidget):
    sectionChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_section_name = None
        self.main_window = parent
        self._build_ui()
        self.update_section_list()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Active section in the drawing :"))
        self.section_combo = QComboBox()
        self.section_combo.currentTextChanged.connect(self._on_section_selected)
        layout.addWidget(self.section_combo)

        layout.addWidget(QLabel("Sections library :"))
        self.sections_list = QListWidget()
        self.sections_list.setAlternatingRowColors(True)
        self.sections_list.currentItemChanged.connect(self._on_list_selection_changed)
        layout.addWidget(self.sections_list)

        btn_new = QPushButton("➕  New section")
        btn_new.clicked.connect(self._on_new_section)
        layout.addWidget(btn_new)

        btn_edit = QPushButton("✏  Modify")
        btn_edit.clicked.connect(self._on_edit_section)
        layout.addWidget(btn_edit)

        btn_delete = QPushButton("🗑  Delete")
        btn_delete.clicked.connect(self._on_delete_section)
        layout.addWidget(btn_delete)

        # Prévisualisation (toujours visible)
        layout.addWidget(QLabel("Preview of the section :"))
        self.preview_widget = SectionPreviewWidget()
        self.preview_widget.setStyleSheet(
            "background: #1a1a2e; border: 1px solid #444; border-radius: 6px;"
        )
        layout.addWidget(self.preview_widget)

        layout.addStretch()

    # ──────────────────────────────────────────────────────
    # NOUVEAU : mise à jour intelligente selon la beam sélectionnée
    # ──────────────────────────────────────────────────────
    def update_preview_from_beam(self, beam):
        """Affiche la section de la poutre sélectionnée (priorité n°1)"""
        if beam and hasattr(beam, 'section_name') and self.main_window.section_library:
            base_sec = self.main_window.section_library.get_section(beam.section_name)
            if base_sec:
                preview_sec = Section(
                    name=base_sec.name,
                    shape_type=base_sec.shape_type,
                    material=beam.material or base_sec.material,
                    b=base_sec.b,
                    h=base_sec.h,
                    tw=base_sec.tw,
                    tf=base_sec.tf,
                    bf=base_sec.bf,
                    web_position=base_sec.web_position
                )
                self.preview_widget.set_section(preview_sec)
                return

        # Fallback : si aucune beam sélectionnée, on montre la sélection de la liste
        current_item = self.sections_list.currentItem()
        if current_item:
            name = current_item.data(Qt.UserRole)
            sec = self.main_window.section_library.get_section(name)
            if sec:
                self.preview_widget.set_section(sec)
                return

        self.preview_widget.clear()

    def _on_list_selection_changed(self, current, previous):
        if current:
            self.update_preview_from_beam(None)

    def update_section_list(self):
        library = getattr(self.main_window, "section_library", None)
        if not library: return

        self.section_combo.blockSignals(True)
        current = self.section_combo.currentText()
        self.section_combo.clear()
        self.section_combo.addItem("Aucune section sélectionnée")
        for sec in library.get_all_sections():
            self.section_combo.addItem(sec.name)
        idx = self.section_combo.findText(current)
        self.section_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.section_combo.blockSignals(False)

        self.sections_list.clear()
        for sec in library.get_all_sections():
            item = QListWidgetItem(f"{sec.name}  —  {sec.shape_type} / {sec.material}")
            item.setData(Qt.UserRole, sec.name)
            self.sections_list.addItem(item)

    def _on_section_selected(self, text: str):
        self.current_section_name = None if text == "Aucune section sélectionnée" else text
        self.sectionChanged.emit(self.current_section_name or "")


    def get_active_section_name(self) -> str:
        return self.current_section_name or ""

    # ──────────────────────────────────────────────────────
    # Actions CRUD
    # ──────────────────────────────────────────────────────
    def _on_new_section(self):
        dlg = NewSectionDialog(self)
        if not dlg.exec():
            return

        name = dlg.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Nom requis", "Le nom ne peut pas être vide.")
            return

        shape_map = {"Rectangle": "rectangle", "T": "T", "I / HEA-IPE": "I"}
        shape = shape_map.get(dlg.shape_combo.currentText(), "rectangle")
        values = dlg.get_values()

        sec = Section(
            name=name,
            shape_type=shape,
            material=dlg.material_combo.currentText(),
            b=values["b"],
            h=values["h"],
            tw=values["tw"],
            tf=values["tf"],
            bf=values["bf"] if shape == "T" else values["b"],
            concrete_grade=values.get("concrete_grade", "C30"),
        )
        self.main_window.section_library.save_section(sec)
        self.main_window.refresh_all_section_combos()  # Rafraîchit tous les combos liés aux sections

    def _on_edit_section(self):
        current_item = self.sections_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Aucune sélection",
                                "Sélectionnez une section à modifier.")
            return

        old_name = current_item.data(Qt.UserRole)
        section = self.main_window.section_library.get_section(old_name)
        if not section:
            QMessageBox.critical(self, "Erreur", f"Section '{old_name}' introuvable.")
            return

        dlg = NewSectionDialog(self)
        dlg.setWindowTitle("Modifier la section")

        # Pré-remplir le type
        shape_to_ui = {
            "rectangle": "Rectangle",
            "T": "T",
            "I": "I / HEA-IPE",
            "IPE": "I / HEA-IPE",
            "HEA": "I / HEA-IPE",
            "HEB": "I / HEA-IPE",
        }
        ui_shape = shape_to_ui.get(section.shape_type, "Rectangle")
        dlg.shape_combo.setCurrentText(ui_shape)
        dlg._update_fields(ui_shape)  # Force la mise à jour des champs

        # Pré-remplir les valeurs
        dlg.name_edit.setText(section.name)
        dlg.material_combo.setCurrentText(section.material)

        # ✅ FIX 1 : utiliser current_b_spin etc., PAS b_spin (qui n'existe pas !)
        #    Avant : dlg.b_spin.value()         ← AttributeError
        #    Après : dlg.current_b_spin.value() ← Correct
        dlg.current_b_spin.setValue(section.b)
        dlg.current_h_spin.setValue(section.h)
        dlg.current_tw_spin.setValue(section.tw)
        dlg.current_tf_spin.setValue(section.tf)
        dlg.current_bf_spin.setValue(section.bf if section.bf else section.b)

        if not dlg.exec():
            return

        new_name = dlg.name_edit.text().strip()
        if not new_name:
            QMessageBox.warning(self, "Nom requis", "Le nom ne peut pas être vide.")
            return

        shape_map = {"Rectangle": "rectangle", "T": "T", "I / HEA-IPE": "I"}
        new_shape = shape_map.get(dlg.shape_combo.currentText(), "rectangle")
        values = dlg.get_values()  # ✅ utilise current_*_spin en interne

        updated = Section(
            name=new_name,
            shape_type=new_shape,
            material=dlg.material_combo.currentText(),
            b=values["b"],
            h=values["h"],
            tw=values["tw"],
            tf=values["tf"],
            bf=values["bf"] if new_shape == "T" else values["b"],
            concrete_grade=values.get("concrete_grade", "C30"),
        )

        # Supprimer l'ancienne entrée si le nom a changé
        if new_name != old_name and old_name in self.main_window.section_library.sections:
            del self.main_window.section_library.sections[old_name]

        self.main_window.section_library.save_section(updated)
        self.update_section_list()

        self.main_window.refresh_all_section_combos()  # Rafraîchit tous les combos liés aux sections

        # Rafraîchir le panneau de propriétés si nécessaire
        if hasattr(self.main_window, "properties_panel"):
            el = self.main_window.properties_panel.current_element
            if el:
                self.main_window.properties_panel.update_from_selection(el)

    def _on_delete_section(self):
        current_item = self.sections_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Aucune sélection",
                                "Sélectionnez une section à supprimer.")
            return

        name = current_item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "Confirmer",
            f"Supprimer la section '{name}' ?\n\nCette action est irréversible.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        library = self.main_window.section_library
        deleted = library.delete_section(name)

        if deleted:
            if self.current_section_name == name:
                self.current_section_name = None
                self.sectionChanged.emit("")

            self.update_section_list()

            self.main_window.refresh_all_section_combos()  # Rafraîchit tous les combos liés aux sections

            # Avertir si des poutres utilisaient cette section
            used_by = [
                b for b in getattr(self.main_window.model, "beams", [])
                if getattr(b, "section_name", None) == name
            ]
            if used_by:
                QMessageBox.warning(
                    self, "Attention",
                    f"La section '{name}' était utilisée par {len(used_by)} poutre(s).\n"
                    "Réassignez une section à ces éléments.",
                )
        else:
            QMessageBox.warning(self, "Erreur", f"Section '{name}' introuvable.")

