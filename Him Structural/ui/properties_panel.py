# properties_panel.py — VERSION AMÉLIORÉE

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QDoubleSpinBox,
    QComboBox, QGroupBox, QListWidget, QListWidgetItem,
    QMenu, QMessageBox, QPushButton
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt

from structural_model import Node, Beam, PointLoad, PointLoadOnBeam, DistributedLoad
from ui.loads_dialog import LoadsDialog
from chinese_standard import ChineseConcrete

class PropertiesPanel(QWidget):
    """Panneau de propriétés – Conditions d'appui en vedette (comme Robot Structural)"""

    def __init__(self, main_window=None):
        super().__init__(parent=None)
        self.main_window = main_window
        self.canvas = main_window.canvas if main_window else None
        self.section_library = None
        self.current_element = None
        self._updating = False
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(12)

        # Informations élément
        grp_info = QGroupBox("Informations élément")
        layout_info = QFormLayout()
        grp_info.setLayout(layout_info)

        self.lbl_type = QLabel("Aucun")
        self.lbl_id   = QLabel("-")
        self.x_spin   = QDoubleSpinBox()
        self.y_spin   = QDoubleSpinBox()
        self.len_lbl  = QLabel("-")

        for sp in (self.x_spin, self.y_spin):
            sp.setDecimals(2)
            sp.setRange(-99999, 99999)
            sp.setSingleStep(10)

        layout_info.addRow("Type :",    self.lbl_type)
        layout_info.addRow("ID :",      self.lbl_id)
        layout_info.addRow("X :",       self.x_spin)
        layout_info.addRow("Y :",       self.y_spin)
        layout_info.addRow("Longueur :", self.len_lbl)
        main_layout.addWidget(grp_info)

        # CONDITIONS D'APPUI (en vedette)
        self.grp_supports = QGroupBox("Conditions d'appui")
        layout_sup = QFormLayout()
        self.support_combo = QComboBox()
        self.support_combo.addItems([
            "⚪ Libre",
            "🔵 Articulé (dx=dy=0)",
            "🔄 Appui simple roulant (dy=0)",
            "⬛ Encastrement (dx=dy=rz=0)"
        ])
        layout_sup.addRow("Type d'appui :", self.support_combo)
        self.grp_supports.setLayout(layout_sup)
        main_layout.addWidget(self.grp_supports)
        self.grp_supports.setVisible(False)

        # Géométrie pour les poutres
        self.grp_geom = QGroupBox("Section & Matériau")
        geom_layout = QFormLayout()
        self.grp_geom.setLayout(geom_layout)
        self.combo_section = QComboBox()
        self.material_combo = QComboBox()
        self.grade_combo = QComboBox()
        self.grade_combo.addItems(list(ChineseConcrete.GRADES.keys()))
        self.grade_combo.currentTextChanged.connect(self._on_grade_changed)
        geom_layout.addRow("Grade beton :", self.grade_combo)
        self.grade_combo.setVisible(False)
        self.material_combo.addItems(["Steel", "Concrete", "Wood"])
        geom_layout.addRow("Section :", self.combo_section)
        geom_layout.addRow("Matériau :", self.material_combo)
        main_layout.addWidget(self.grp_geom)
        self.grp_geom.setVisible(False)

        # Charges
        grp_loads = QGroupBox("Charges appliquées")
        load_layout = QVBoxLayout()
        self.loads_list = QListWidget()
        self.loads_list.setMaximumHeight(200)
        self.loads_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.loads_list.customContextMenuRequested.connect(self._on_loads_context_menu)
        self.loads_list.itemDoubleClicked.connect(self._on_load_double_clicked)
        load_layout.addWidget(self.loads_list)

        btn_row = QHBoxLayout()
        btn_add = QPushButton("➕ Ajouter")
        btn_add.clicked.connect(self._on_add_load)
        btn_edit = QPushButton("✏️ Éditer")
        btn_edit.clicked.connect(self._on_edit_load)
        btn_delete = QPushButton("🗑 Supprimer")
        btn_delete.setStyleSheet("background:#7a2e2e;")
        btn_delete.clicked.connect(self._on_delete_load)
        btn_row.addWidget(btn_add); btn_row.addWidget(btn_edit); btn_row.addWidget(btn_delete)
        load_layout.addLayout(btn_row)
        grp_loads.setLayout(load_layout)
        main_layout.addWidget(grp_loads)

        main_layout.addStretch()

        # Connexions
        self.x_spin.valueChanged.connect(self._on_coord_changed)
        self.y_spin.valueChanged.connect(self._on_coord_changed)
        self.support_combo.currentIndexChanged.connect(self._on_support_changed)
        self.combo_section.currentTextChanged.connect(self._on_section_changed)
        self.material_combo.currentTextChanged.connect(self._on_material_changed)

    def set_section_library(self, library):
        self.section_library = library
        self.combo_section.clear()
        if library:
            for sec in library.get_all_sections():
                self.combo_section.addItem(sec.name)

    def refresh_from_settings(self):
        if self.current_element:
            self._fill_fields(self.current_element)
            self.canvas_refresh()

    def refresh_section_combo(self):
        self.combo_section.clear()
        if self.section_library:
            for sec in self.section_library.get_all_sections():
                self.combo_section.addItem(sec.name)

    def update_from_selection(self, element):
        self.current_element = element
        self._updating = True

        self.grp_supports.setVisible(False)
        self.grp_geom.setVisible(False)

        if element is None:
            self.lbl_type.setText("Aucun élément sélectionné")
            self.lbl_id.setText("-")
            self.len_lbl.setText("-")
        else:
            self._fill_fields(element)

        self._updating = False

    def _fill_fields(self, element):
        if isinstance(element, Node):
            self.lbl_type.setText("🔵 Nœud")
            self.lbl_id.setText(str(element.id))
            self.x_spin.setValue(element.x)
            self.y_spin.setValue(element.y)
            self.x_spin.setEnabled(True)
            self.y_spin.setEnabled(True)
            self.len_lbl.setText("-")
            self.grp_supports.setVisible(True)

            s = element.supports
            idx = 3 if s.get("dx") and s.get("dy") and s.get("rz") else \
                  1 if s.get("dx") and s.get("dy") else \
                  2 if s.get("dy") else 0
            self.support_combo.setCurrentIndex(idx)

        elif isinstance(element, Beam):
            self.lbl_type.setText("🟡 Poutre")
            self.lbl_id.setText(str(element.id))
            self.x_spin.setEnabled(False)
            self.y_spin.setEnabled(False)

            # beam.length est en pixels ; SCALE_PX_PER_M = 160 px/m (même valeur que loads_dialog)
            _SCALE = 160.0
            length_px  = getattr(element, 'length', 0)
            length_mm_real = (length_px / _SCALE) * 1000.0   # pixels → mm réels
            formatted = self.main_window.format_length(length_mm_real)
            self.len_lbl.setText(formatted)
            self.grp_geom.setVisible(True)

            idx = self.combo_section.findText(getattr(element, 'section_name', ''))
            if idx >= 0:
                self.combo_section.setCurrentIndex(idx)
            self.material_combo.setCurrentText(getattr(element, 'material', 'Concrete'))

            is_conc = element.material == "Concrete"
            self.grade_combo.setVisible(is_conc)
            if is_conc:
                idx = self.grade_combo.findText(getattr(element, 'concrete_grade', 'C30'))
                self.grade_combo.setCurrentIndex(idx if idx >= 0 else 0)

        self._update_loads_list(element)

    def _update_loads_list(self, element):
        self.loads_list.clear()
        if not element: 
            return

        if isinstance(element, Node):
            loads = element.point_loads
            title = "Charges ponctuelles sur ce nœud :"
        elif isinstance(element, Beam):
            # Afficher toutes les charges sur la poutre
            point_loads = getattr(element, 'point_loads_on_beam', [])
            dist_loads = getattr(element, 'distributed_loads', [])
            
            # En-tête
            header = QListWidgetItem(f"📍 Charges sur Poutre {element.id}")
            header.setBackground(QColor("#1e3a5f"))
            header.setForeground(QColor("#00ddff"))
            header.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.loads_list.addItem(header)
            
            # Charges ponctuelles sur poutre (NOUVEAU)
            if point_loads:
                subheader = QListWidgetItem("   Charges ponctuelles:")
                subheader.setForeground(QColor("#FFD700"))
                subheader.setFont(QFont("Segoe UI", 8, QFont.Bold))
                self.loads_list.addItem(subheader)
                
                for load in point_loads:
                    pos_pct = load.position_ratio * 100
                    txt = f"   @{pos_pct:.0f}%: Fx={load.fx:+.1f}kN, Fy={load.fy:+.1f}kN"
                    it = QListWidgetItem(txt)
                    it.setData(Qt.UserRole, load)
                    it.setForeground(QColor("#FFA500"))
                    self.loads_list.addItem(it)
            
            # Charges réparties
            if dist_loads:
                subheader = QListWidgetItem("   Charges réparties:")
                subheader.setForeground(QColor("#FF6B9D"))
                subheader.setFont(QFont("Segoe UI", 8, QFont.Bold))
                self.loads_list.addItem(subheader)
                
                for load in dist_loads:
                    txt = f"   w={load.w:+.1f}kN/m [{load.start_pos*100:.0f}%→{load.end_pos*100:.0f}%]"
                    it = QListWidgetItem(txt)
                    it.setData(Qt.UserRole, load)
                    it.setForeground(QColor("#FFB6C1"))
                    self.loads_list.addItem(it)
            
            if not point_loads and not dist_loads:
                empty = QListWidgetItem("   (aucune charge)")
                empty.setForeground(QColor("#777"))
                self.loads_list.addItem(empty)
            return
        else:
            loads = []
            title = "Charges :"

        header = QListWidgetItem(title)
        header.setBackground(QColor("#1e3a5f"))
        header.setForeground(QColor("#00ddff"))
        self.loads_list.addItem(header)

        if not loads:
            empty = QListWidgetItem("   (aucune charge)")
            empty.setForeground(QColor("#777"))
            self.loads_list.addItem(empty)
            return

        for load in loads:
            if isinstance(load, PointLoad):
                txt = f"Fx = {load.fx:+.2f} kN | Fy = {load.fy:+.2f} kN"
            else:
                txt = f"w = {load.w:+.2f} kN/m  [{load.start_pos*100:.0f}% → {load.end_pos*100:.0f}%]"
            it = QListWidgetItem(txt)
            it.setData(Qt.UserRole, load)
            self.loads_list.addItem(it)

    def _on_coord_changed(self):
        if self._updating or not isinstance(self.current_element, Node): 
            return
        n = self.current_element
        n.x = self.x_spin.value()
        n.y = self.y_spin.value()
        if hasattr(n, "graphics_item") and n.graphics_item:
            n.graphics_item.setPos(n.x, n.y)
        self.canvas_refresh()

    def _on_support_changed(self, index):
        if self._updating or not isinstance(self.current_element, Node):
            return
        n = self.current_element
        mapping = [
            {"dx": False, "dy": False, "rz": False},
            {"dx": True,  "dy": True,  "rz": False},
            {"dx": False, "dy": True,  "rz": False},
            {"dx": True,  "dy": True,  "rz": True}
        ]
        n.supports = mapping[index]

        if hasattr(n, "graphics_item") and n.graphics_item:
            n.graphics_item.update_support_symbol()
            
        self.canvas_refresh()

    def _on_section_changed(self, text):
        if self._updating or not isinstance(self.current_element, Beam): 
            return
        self.current_element.section_name = text
        self.canvas_refresh()

    def _on_material_changed(self, text):
        if self._updating or not isinstance(self.current_element, Beam): 
            return
        self.current_element.material = text
        self.grade_combo.setVisible(text == "Concrete")
        if text == "Concrete":
            self.current_element.concrete_grade = self.grade_combo.currentText()
        self.canvas_refresh()

        if hasattr(self.main_window, "sections_panel"):
            self.main_window.sections_panel.update_preview_from_beam(self.current_element)

    def _on_grade_changed(self, grade:str):
        """Sauvegarde IMMÉDIATEMENT le grade béton quand l'utilisateur change"""
        if self._updating or not isinstance(self.current_element, Beam):
            return
        if getattr(self.current_element, 'material', None) == "Concrete":
            self.current_element.concrete_grade = grade
            print(f"✅ Grade béton mis à jour → {grade} sur poutre {self.current_element.id}")
            self.canvas_refresh()

    def _on_add_load(self):
        if not self.current_element:
            QMessageBox.warning(self, "Attention", "Sélectionnez d'abord un nœud ou une poutre.")
            return
        dlg = LoadsDialog(self.main_window, self)
        dlg.exec()
        self._update_loads_list(self.current_element)
        self.canvas_refresh()

    def _get_selected_load(self):
        """Retourne la charge sélectionnée dans la liste, ou None."""
        item = self.loads_list.currentItem()
        if item is None:
            return None
        return item.data(Qt.UserRole)   # None pour les en-têtes

    def _on_load_double_clicked(self, item):
        """Double-clic sur un item → ouvrir l'éditeur."""
        load = item.data(Qt.UserRole)
        if load is None:
            return
        self._open_edit_dialog(load)

    def _on_edit_load(self):
        load = self._get_selected_load()
        if load is None:
            QMessageBox.information(self, "Sélection", "Sélectionnez une charge dans la liste.")
            return
        self._open_edit_dialog(load)

    def _open_edit_dialog(self, load):
        from ui.loads_dialog import EditLoadDialog
        dlg = EditLoadDialog(self.main_window, load, parent=self)
        if dlg.exec():
            self._update_loads_list(self.current_element)
            self.canvas_refresh()

    def _on_delete_load(self):
        load = self._get_selected_load()
        if load is None:
            QMessageBox.information(self, "Sélection", "Sélectionnez une charge dans la liste.")
            return
        self._delete_load(load)

    def _delete_load(self, load):
        from structural_model import PointLoadOnBeam, DistributedLoad, PointLoad
        model = self.main_window.model
        scene = self.main_window.canvas.scene

        reply = QMessageBox.question(
            self, "Supprimer la charge", "Supprimer cette charge ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # Retirer le graphique
        gi = getattr(load, "graphics_item", None)
        if gi is not None:
            try: scene.removeItem(gi)
            except Exception: pass
            load.graphics_item = None

        if isinstance(load, PointLoadOnBeam):
            if load.beam:
                if load in load.beam.point_loads_on_beam:
                    load.beam.point_loads_on_beam.remove(load)
            if load in model.point_loads_on_beams:
                model.point_loads_on_beams.remove(load)

        elif isinstance(load, DistributedLoad):
            member = getattr(load, "member", None) or getattr(load, "beam", None)
            if member and load in member.distributed_loads:
                member.distributed_loads.remove(load)
            if load in model.distributed_loads:
                model.distributed_loads.remove(load)

        elif isinstance(load, PointLoad):
            node = load.node
            if node and load in node.point_loads:
                node.point_loads.remove(load)
            if load in model.point_loads:
                model.point_loads.remove(load)

        self._update_loads_list(self.current_element)
        self.canvas_refresh()

    def _on_loads_context_menu(self, pos):
        """Menu contextuel clic-droit sur la liste des charges."""
        from PySide6.QtWidgets import QMenu
        item = self.loads_list.itemAt(pos)
        if item is None:
            return
        load = item.data(Qt.UserRole)
        if load is None:
            return   # en-têtes/sous-titres non interactifs

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background:#1e1e2e; color:#e0e0e0; border:1px solid #444; }
            QMenu::item:selected { background:#2e4a7a; }
        """)
        edit_action   = menu.addAction("✏️  Éditer cette charge")
        delete_action = menu.addAction("🗑  Supprimer cette charge")
        action = menu.exec(self.loads_list.viewport().mapToGlobal(pos))
        if action == edit_action:
            self._open_edit_dialog(load)
        elif action == delete_action:
            self._delete_load(load)

    def canvas_refresh(self):
        if self.canvas:
            self.canvas.scene.update()
            self.canvas.viewport().update()