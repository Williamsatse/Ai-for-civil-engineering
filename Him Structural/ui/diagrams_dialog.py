# ui/diagrams_dialog.py
"""
Dialogue de personnalisation des diagrammes (BMD, SFD) — Style Robot Structural

Fonctionnalités :
  - Choix des diagrammes à afficher (BMD, SFD, Axial, Déformée)
  - Échelle personnalisée (automatique ou manuelle)
  - Options d'affichage (hachures, valeurs, lignes de référence)
  - Couleurs personnalisables
  - Épaisseur des lignes
  - Affichage des valeurs max/min
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QGroupBox, QFormLayout, QCheckBox, QDoubleSpinBox, QComboBox,
    QLabel, QPushButton, QColorDialog, QSpinBox, QSlider,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QSplitter, QFrame, QGridLayout, QRadioButton,
    QButtonGroup, QLineEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
import json
import os


class ColorButton(QPushButton):
    """Bouton de sélection de couleur avec aperçu"""
    color_changed = Signal(QColor)
    
    def __init__(self, color=QColor("#ef4444"), parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(60, 28)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()
        self.clicked.connect(self._choose_color)
    
    @property
    def color(self):
        return self._color
    
    @color.setter
    def color(self, value):
        self._color = value
        self._update_style()
        self.color_changed.emit(value)
    
    def _update_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color.name()};
                border: 2px solid #555;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid #fff;
            }}
        """)
    
    def _choose_color(self):
        color = QColorDialog.getColor(self._color, self, "Choisir une couleur")
        if color.isValid():
            self.color = color


class DiagramsDialog(QDialog):
    """
    Dialogue principal de configuration des diagrammes.
    Inspiré de l'interface de Robot Structural Analysis.
    """
    settings_applied = Signal(dict)
    
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("Diagrams — Configuration d'affichage")
        self.resize(900, 700)
        self.setMinimumSize(800, 600)
        
        # Configuration par défaut
        self.default_settings = {
            # Diagrammes à afficher
            "show_bmd": True,
            "show_sfd": True,
            "show_axial": False,
            "show_deflected": False,
            
            # Échelles
            "bmd_scale_mode": "auto",
            "bmd_scale_value": 1.0,
            "sfd_scale_mode": "auto",
            "sfd_scale_value": 1.0,
            
            # Options d'affichage BMD
            "bmd_color": "#ef4444",
            "bmd_line_width": 2.5,
            "bmd_fill": True,
            "bmd_fill_alpha": 30,
            "bmd_hatch_positive": "none",
            "bmd_hatch_negative": "none",
            "bmd_show_values": True,
            "bmd_show_max": True,
            "bmd_show_min": True,
            "bmd_invert_sign": False,
            
            # Options d'affichage SFD
            "sfd_color": "#3b82f6",
            "sfd_line_width": 2.5,
            "sfd_fill": False,
            "sfd_fill_alpha": 20,
            "sfd_hatch_positive": "none",
            "sfd_hatch_negative": "none",
            "sfd_show_values": True,
            "sfd_show_max": True,
            "sfd_show_min": True,
            
            # Options générales
            "show_reference_line": True,
            "reference_line_style": "dash",
            "show_zero_line": True,
            "text_font_size": 9,
            "text_color": "#ffffff",
            "diagram_offset": 80,
            
            # Unités
            "value_format": "%.2f",
            "show_units": True,
            "unit_moment": "kN·m",
            "unit_shear": "kN",
        }
        
        self.settings = self._load_settings()
        self._build_ui()
        self._populate_values()
        
    def _load_settings(self):
        """Charge les paramètres sauvegardés"""
        settings_file = "diagrams_settings.json"
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    result = self.default_settings.copy()
                    result.update(loaded)
                    return result
            except:
                pass
        return self.default_settings.copy()
    
    def _save_settings(self):
        """Sauvegarde les paramètres"""
        try:
            with open("diagrams_settings.json", 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur sauvegarde paramètres diagrammes: {e}")
    
    def _build_ui(self):
        """Construit l'interface utilisateur"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)
        
        # Titre
        title = QLabel("⚙️ Configuration des diagrammes de résultats")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #4fc3f7; margin-bottom: 10px;")
        main_layout.addWidget(title)
        
        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)
        
        # Panneau gauche : Liste des diagrammes
        left_panel = self._build_left_panel()
        splitter.addWidget(left_panel)
        
        # Panneau droit : Onglets de configuration
        right_panel = self._build_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([250, 650])
        main_layout.addWidget(splitter)
        
        # Boutons d'action
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_reset = QPushButton("🔄 Réinitialiser")
        btn_reset.setToolTip("Restaurer les paramètres par défaut")
        btn_reset.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(btn_reset)
        
        btn_preview = QPushButton("👁️ Aperçu")
        btn_preview.setToolTip("Mettre à jour l'aperçu sur le canvas")
        btn_preview.clicked.connect(self._apply_preview)
        btn_layout.addWidget(btn_preview)
        
        btn_apply = QPushButton("✅ Appliquer")
        btn_apply.setStyleSheet("""
            QPushButton {
                background: #22c55e;
                color: white;
                font-weight: bold;
                padding: 10px 25px;
                border-radius: 6px;
            }
            QPushButton:hover { background: #16a34a; }
        """)
        btn_apply.clicked.connect(self._apply_settings)
        btn_layout.addWidget(btn_apply)
        
        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        
        main_layout.addLayout(btn_layout)
        
        # Barre de statut
        self.status_label = QLabel("Prêt")
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        main_layout.addWidget(self.status_label)
    
    def _build_left_panel(self):
        """Construit le panneau de sélection des diagrammes"""
        panel = QFrame()
        panel.setFrameShape(QFrame.StyledPanel)
        panel.setMaximumWidth(280)
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # Groupe : Diagrammes disponibles
        group_avail = QGroupBox("📊 Diagrammes à afficher")
        avail_layout = QVBoxLayout(group_avail)
        
        self.chk_bmd = QCheckBox("Moment fléchissant (BMD)")
        self.chk_bmd.setToolTip("Bending Moment Diagram")
        self.chk_sfd = QCheckBox("Effort tranchant (SFD)")
        self.chk_sfd.setToolTip("Shear Force Diagram")
        self.chk_axial = QCheckBox("Effort normal (Axial)")
        self.chk_axial.setToolTip("Axial Force Diagram")
        self.chk_deflected = QCheckBox("Déformée (Deflected)")
        self.chk_deflected.setToolTip("Déformée de la structure")
        
        for chk in [self.chk_bmd, self.chk_sfd, self.chk_axial, self.chk_deflected]:
            chk.setStyleSheet("QCheckBox { spacing: 8px; font-size: 12px; }")
            avail_layout.addWidget(chk)
        
        layout.addWidget(group_avail)
        
        # Groupe : Informations
        group_info = QGroupBox("ℹ️ Informations")
        info_layout = QVBoxLayout(group_info)
        
        info_text = QLabel(
            "Sélectionnez les diagrammes à afficher sur le canvas.\n\n"
            "Chaque diagramme peut être personnalisé dans les onglets de droite."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #aaa; font-size: 11px;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(group_info)
        layout.addStretch()
        
        return panel
    
    def _build_right_panel(self):
        """Construit le panneau d'onglets de configuration"""
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        # Onglet Général
        self.tabs.addTab(self._build_general_tab(), "⚙️ Général")
        
        # Onglet BMD (Moment)
        self.tabs.addTab(self._build_bmd_tab(), "📐 Moment (BMD)")
        
        # Onglet SFD (Shear)
        self.tabs.addTab(self._build_sfd_tab(), "✂️ Tranchant (SFD)")
        
        # Onglet Axial
        self.tabs.addTab(self._build_axial_tab(), "📏 Axial")
        
        # Onglet Déformée
        self.tabs.addTab(self._build_deflection_tab(), "〰️ Déformée")
        
        return self.tabs
    
    def _build_general_tab(self):
        """Onglet des paramètres généraux"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Groupe : Échelles globales
        group_scale = QGroupBox("📏 Échelles d'affichage")
        scale_layout = QGridLayout(group_scale)
        
        self.scale_mode_group = QButtonGroup(self)
        self.radio_scale_auto = QRadioButton("Échelle automatique")
        self.radio_scale_auto.setToolTip("Ajuste automatiquement l'échelle pour chaque poutre")
        self.radio_scale_manual = QRadioButton("Échelle manuelle globale")
        self.radio_scale_manual.setToolTip("Utilise la même échelle pour toutes les poutres")
        
        self.scale_mode_group.addButton(self.radio_scale_auto, 0)
        self.scale_mode_group.addButton(self.radio_scale_manual, 1)
        
        scale_layout.addWidget(self.radio_scale_auto, 0, 0, 1, 2)
        scale_layout.addWidget(self.radio_scale_manual, 1, 0, 1, 2)
        
        scale_layout.addWidget(QLabel("Échelle globale:"), 2, 0)
        self.spin_global_scale = QDoubleSpinBox()
        self.spin_global_scale.setRange(0.001, 1000.0)
        self.spin_global_scale.setDecimals(3)
        self.spin_global_scale.setValue(1.0)
        self.spin_global_scale.setSuffix(" ×")
        scale_layout.addWidget(self.spin_global_scale, 2, 1)
        
        layout.addWidget(group_scale)
        
        # Groupe : Apparence générale
        group_appearance = QGroupBox("🎨 Apparence générale")
        app_layout = QFormLayout(group_appearance)
        
        self.chk_ref_line = QCheckBox("Afficher la ligne de référence")
        app_layout.addRow(self.chk_ref_line)
        
        self.combo_ref_style = QComboBox()
        self.combo_ref_style.addItems(["Trait plein", "Tirets", "Points", "Tirets-points"])
        app_layout.addRow("Style ligne réf.:", self.combo_ref_style)
        
        self.chk_zero_line = QCheckBox("Afficher la ligne zéro")
        app_layout.addRow(self.chk_zero_line)
        
        self.spin_offset = QSpinBox()
        self.spin_offset.setRange(20, 300)
        self.spin_offset.setSuffix(" px")
        app_layout.addRow("Distance poutre/diagramme:", self.spin_offset)
        
        self.spin_font_size = QSpinBox()
        self.spin_font_size.setRange(6, 20)
        self.spin_font_size.setSuffix(" pt")
        app_layout.addRow("Taille police:", self.spin_font_size)
        
        self.btn_text_color = ColorButton(QColor("#ffffff"))
        app_layout.addRow("Couleur texte:", self.btn_text_color)
        
        layout.addWidget(group_appearance)
        
        # Groupe : Unités
        group_units = QGroupBox("📐 Unités affichées")
        units_layout = QFormLayout(group_units)
        
        self.chk_show_units = QCheckBox("Afficher les unités")
        units_layout.addRow(self.chk_show_units)
        
        self.edit_unit_moment = QLineEdit("kN·m")
        units_layout.addRow("Unité moment:", self.edit_unit_moment)
        
        self.edit_unit_shear = QLineEdit("kN")
        units_layout.addRow("Unité tranchant:", self.edit_unit_shear)
        
        layout.addWidget(group_units)
        layout.addStretch()
        
        return tab
    
    def _build_bmd_tab(self):
        """Onglet de configuration du BMD"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Échelle spécifique
        group_scale = QGroupBox("📏 Échelle BMD")
        scale_layout = QFormLayout(group_scale)
        
        self.bmd_scale_mode = QComboBox()
        self.bmd_scale_mode.addItems(["Hériter du global", "Automatique", "Manuel"])
        scale_layout.addRow("Mode d'échelle:", self.bmd_scale_mode)
        
        self.spin_bmd_scale = QDoubleSpinBox()
        self.spin_bmd_scale.setRange(0.001, 1000.0)
        self.spin_bmd_scale.setDecimals(3)
        self.spin_bmd_scale.setValue(1.0)
        self.spin_bmd_scale.setSuffix(" mm/kN·m")
        scale_layout.addRow("Valeur échelle:", self.spin_bmd_scale)
        
        layout.addWidget(group_scale)
        
        # Couleurs et style
        group_style = QGroupBox("🎨 Style du diagramme")
        style_layout = QFormLayout(group_style)
        
        self.btn_bmd_color = ColorButton(QColor("#ef4444"))
        style_layout.addRow("Couleur ligne:", self.btn_bmd_color)
        
        self.spin_bmd_width = QDoubleSpinBox()
        self.spin_bmd_width.setRange(0.5, 10.0)
        self.spin_bmd_width.setDecimals(1)
        self.spin_bmd_width.setSuffix(" px")
        style_layout.addRow("Épaisseur ligne:", self.spin_bmd_width)
        
        layout.addWidget(group_style)
        
        # Remplissage et hachures
        group_fill = QGroupBox("🖌️ Remplissage et hachures")
        fill_layout = QFormLayout(group_fill)
        
        self.chk_bmd_fill = QCheckBox("Remplir le diagramme")
        fill_layout.addRow(self.chk_bmd_fill)
        
        self.slider_bmd_alpha = QSlider(Qt.Horizontal)
        self.slider_bmd_alpha.setRange(0, 100)
        self.slider_bmd_alpha.setValue(30)
        fill_layout.addRow("Transparence:", self.slider_bmd_alpha)
        
        self.combo_bmd_hatch_pos = QComboBox()
        self.combo_bmd_hatch_pos.addItems(["Aucune", "Hachures simples", "Hachures croisées", "Lignes horizontales", "Lignes verticales"])
        fill_layout.addRow("Hachures moments (+):", self.combo_bmd_hatch_pos)
        
        self.combo_bmd_hatch_neg = QComboBox()
        self.combo_bmd_hatch_neg.addItems(["Aucune", "Hachures simples", "Hachures croisées", "Lignes horizontales", "Lignes verticales"])
        fill_layout.addRow("Hachures moments (-):", self.combo_bmd_hatch_neg)
        
        layout.addWidget(group_fill)
        
        # Valeurs affichées
        group_values = QGroupBox("🔢 Valeurs affichées")
        values_layout = QVBoxLayout(group_values)
        
        self.chk_bmd_values = QCheckBox("Afficher les valeurs sur le diagramme")
        values_layout.addWidget(self.chk_bmd_values)
        
        self.chk_bmd_max = QCheckBox("Marquer la valeur maximale")
        values_layout.addWidget(self.chk_bmd_max)
        
        self.chk_bmd_min = QCheckBox("Marquer la valeur minimale")
        values_layout.addWidget(self.chk_bmd_min)
        
        self.chk_bmd_invert = QCheckBox("Inverser la convention de signe (sagging = négatif)")
        values_layout.addWidget(self.chk_bmd_invert)
        
        layout.addWidget(group_values)
        layout.addStretch()
        
        return tab
    
    def _build_sfd_tab(self):
        """Onglet de configuration du SFD"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Similaire au BMD mais pour le SFD
        group_scale = QGroupBox("📏 Échelle SFD")
        scale_layout = QFormLayout(group_scale)
        
        self.sfd_scale_mode = QComboBox()
        self.sfd_scale_mode.addItems(["Hériter du global", "Automatique", "Manuel"])
        scale_layout.addRow("Mode d'échelle:", self.sfd_scale_mode)
        
        self.spin_sfd_scale = QDoubleSpinBox()
        self.spin_sfd_scale.setRange(0.001, 1000.0)
        self.spin_sfd_scale.setDecimals(3)
        self.spin_sfd_scale.setValue(1.0)
        self.spin_sfd_scale.setSuffix(" mm/kN")
        scale_layout.addRow("Valeur échelle:", self.spin_sfd_scale)
        
        layout.addWidget(group_scale)
        
        # Couleurs et style
        group_style = QGroupBox("🎨 Style du diagramme")
        style_layout = QFormLayout(group_style)
        
        self.btn_sfd_color = ColorButton(QColor("#3b82f6"))
        style_layout.addRow("Couleur ligne:", self.btn_sfd_color)
        
        self.spin_sfd_width = QDoubleSpinBox()
        self.spin_sfd_width.setRange(0.5, 10.0)
        self.spin_sfd_width.setDecimals(1)
        self.spin_sfd_width.setSuffix(" px")
        style_layout.addRow("Épaisseur ligne:", self.spin_sfd_width)
        
        layout.addWidget(group_style)
        
        # Remplissage
        group_fill = QGroupBox("🖌️ Remplissage et hachures")
        fill_layout = QFormLayout(group_fill)
        
        self.chk_sfd_fill = QCheckBox("Remplir le diagramme")
        fill_layout.addRow(self.chk_sfd_fill)
        
        self.slider_sfd_alpha = QSlider(Qt.Horizontal)
        self.slider_sfd_alpha.setRange(0, 100)
        self.slider_sfd_alpha.setValue(20)
        fill_layout.addRow("Transparence:", self.slider_sfd_alpha)
        
        self.combo_sfd_hatch_pos = QComboBox()
        self.combo_sfd_hatch_pos.addItems(["Aucune", "Hachures simples", "Hachures croisées"])
        fill_layout.addRow("Hachures efforts (+):", self.combo_sfd_hatch_pos)
        
        self.combo_sfd_hatch_neg = QComboBox()
        self.combo_sfd_hatch_neg.addItems(["Aucune", "Hachures simples", "Hachures croisées"])
        fill_layout.addRow("Hachures efforts (-):", self.combo_sfd_hatch_neg)
        
        layout.addWidget(group_fill)
        
        # Valeurs
        group_values = QGroupBox("🔢 Valeurs affichées")
        values_layout = QVBoxLayout(group_values)
        
        self.chk_sfd_values = QCheckBox("Afficher les valeurs sur le diagramme")
        values_layout.addWidget(self.chk_sfd_values)
        
        self.chk_sfd_max = QCheckBox("Marquer la valeur maximale")
        values_layout.addWidget(self.chk_sfd_max)
        
        self.chk_sfd_min = QCheckBox("Marquer la valeur minimale")
        values_layout.addWidget(self.chk_sfd_min)
        
        layout.addWidget(group_values)
        layout.addStretch()
        
        return tab
    
    def _build_axial_tab(self):
        """Onglet de configuration de l'effort normal"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        info = QLabel("Configuration de l'effort normal (compression/traction)")
        info.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(info)
        
        placeholder = QLabel("🔧 Cette fonctionnalité sera disponible dans une prochaine version.")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("color: #666; padding: 50px;")
        layout.addWidget(placeholder)
        
        layout.addStretch()
        return tab
    
    def _build_deflection_tab(self):
        """Onglet de configuration de la déformée"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        info = QLabel("Configuration de la déformée (déplacements)")
        info.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(info)
        
        placeholder = QLabel("🔧 Cette fonctionnalité sera disponible dans une prochaine version.\n\n"
                            "La déformée nécessite le calcul des déplacements nodaux.")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("color: #666; padding: 50px;")
        layout.addWidget(placeholder)
        
        layout.addStretch()
        return tab
    
    def _populate_values(self):
        """Remplit les widgets avec les valeurs des settings"""
        s = self.settings
        
        # Diagrammes à afficher
        self.chk_bmd.setChecked(s.get("show_bmd", True))
        self.chk_sfd.setChecked(s.get("show_sfd", True))
        self.chk_axial.setChecked(s.get("show_axial", False))
        self.chk_deflected.setChecked(s.get("show_deflected", False))
        
        # Échelle globale
        if s.get("bmd_scale_mode") == "auto":
            self.radio_scale_auto.setChecked(True)
        else:
            self.radio_scale_manual.setChecked(True)
        self.spin_global_scale.setValue(s.get("bmd_scale_value", 1.0))
        
        # Général
        self.chk_ref_line.setChecked(s.get("show_reference_line", True))
        self.chk_zero_line.setChecked(s.get("show_zero_line", True))
        self.spin_offset.setValue(s.get("diagram_offset", 80))
        self.spin_font_size.setValue(s.get("text_font_size", 9))
        self.btn_text_color.color = QColor(s.get("text_color", "#ffffff"))
        self.chk_show_units.setChecked(s.get("show_units", True))
        self.edit_unit_moment.setText(s.get("unit_moment", "kN·m"))
        self.edit_unit_shear.setText(s.get("unit_shear", "kN"))
        
        # BMD
        bmd_mode = s.get("bmd_scale_mode", "auto")
        self.bmd_scale_mode.setCurrentIndex({"auto": 1, "manual": 2}.get(bmd_mode, 0))
        self.spin_bmd_scale.setValue(s.get("bmd_scale_value", 1.0))
        self.btn_bmd_color.color = QColor(s.get("bmd_color", "#ef4444"))
        self.spin_bmd_width.setValue(s.get("bmd_line_width", 2.5))
        self.chk_bmd_fill.setChecked(s.get("bmd_fill", True))
        self.slider_bmd_alpha.setValue(s.get("bmd_fill_alpha", 30))
        self.combo_bmd_hatch_pos.setCurrentIndex({"none": 0, "solid": 1, "cross": 2, "horizontal": 3, "vertical": 4}.get(s.get("bmd_hatch_positive"), 0))
        self.combo_bmd_hatch_neg.setCurrentIndex({"none": 0, "solid": 1, "cross": 2, "horizontal": 3, "vertical": 4}.get(s.get("bmd_hatch_negative"), 0))
        self.chk_bmd_values.setChecked(s.get("bmd_show_values", True))
        self.chk_bmd_max.setChecked(s.get("bmd_show_max", True))
        self.chk_bmd_min.setChecked(s.get("bmd_show_min", True))
        self.chk_bmd_invert.setChecked(s.get("bmd_invert_sign", False))
        
        # SFD
        sfd_mode = s.get("sfd_scale_mode", "auto")
        self.sfd_scale_mode.setCurrentIndex({"auto": 1, "manual": 2}.get(sfd_mode, 0))
        self.spin_sfd_scale.setValue(s.get("sfd_scale_value", 1.0))
        self.btn_sfd_color.color = QColor(s.get("sfd_color", "#3b82f6"))
        self.spin_sfd_width.setValue(s.get("sfd_line_width", 2.5))
        self.chk_sfd_fill.setChecked(s.get("sfd_fill", False))
        self.slider_sfd_alpha.setValue(s.get("sfd_fill_alpha", 20))
        self.combo_sfd_hatch_pos.setCurrentIndex({"none": 0, "solid": 1, "cross": 2}.get(s.get("sfd_hatch_positive"), 0))
        self.combo_sfd_hatch_neg.setCurrentIndex({"none": 0, "solid": 1, "cross": 2}.get(s.get("sfd_hatch_negative"), 0))
        self.chk_sfd_values.setChecked(s.get("sfd_show_values", True))
        self.chk_sfd_max.setChecked(s.get("sfd_show_max", True))
        self.chk_sfd_min.setChecked(s.get("sfd_show_min", True))
    
    def _collect_settings(self):
        """Collecte les valeurs des widgets dans un dictionnaire"""
        return {
            # Affichage
            "show_bmd": self.chk_bmd.isChecked(),
            "show_sfd": self.chk_sfd.isChecked(),
            "show_axial": self.chk_axial.isChecked(),
            "show_deflected": self.chk_deflected.isChecked(),
            
            # Échelles
            "bmd_scale_mode": "auto" if self.radio_scale_auto.isChecked() else "manual",
            "bmd_scale_value": self.spin_global_scale.value(),
            "sfd_scale_mode": "auto" if self.radio_scale_auto.isChecked() else "manual",
            "sfd_scale_value": self.spin_global_scale.value(),
            
            # Général
            "show_reference_line": self.chk_ref_line.isChecked(),
            "show_zero_line": self.chk_zero_line.isChecked(),
            "diagram_offset": self.spin_offset.value(),
            "text_font_size": self.spin_font_size.value(),
            "text_color": self.btn_text_color.color.name(),
            "show_units": self.chk_show_units.isChecked(),
            "unit_moment": self.edit_unit_moment.text(),
            "unit_shear": self.edit_unit_shear.text(),
            
            # BMD
            "bmd_color": self.btn_bmd_color.color.name(),
            "bmd_line_width": self.spin_bmd_width.value(),
            "bmd_fill": self.chk_bmd_fill.isChecked(),
            "bmd_fill_alpha": self.slider_bmd_alpha.value(),
            "bmd_hatch_positive": ["none", "solid", "cross", "horizontal", "vertical"][self.combo_bmd_hatch_pos.currentIndex()],
            "bmd_hatch_negative": ["none", "solid", "cross", "horizontal", "vertical"][self.combo_bmd_hatch_neg.currentIndex()],
            "bmd_show_values": self.chk_bmd_values.isChecked(),
            "bmd_show_max": self.chk_bmd_max.isChecked(),
            "bmd_show_min": self.chk_bmd_min.isChecked(),
            "bmd_invert_sign": self.chk_bmd_invert.isChecked(),
            
            # SFD
            "sfd_color": self.btn_sfd_color.color.name(),
            "sfd_line_width": self.spin_sfd_width.value(),
            "sfd_fill": self.chk_sfd_fill.isChecked(),
            "sfd_fill_alpha": self.slider_sfd_alpha.value(),
            "sfd_hatch_positive": ["none", "solid", "cross"][self.combo_sfd_hatch_pos.currentIndex()],
            "sfd_hatch_negative": ["none", "solid", "cross"][self.combo_sfd_hatch_neg.currentIndex()],
            "sfd_show_values": self.chk_sfd_values.isChecked(),
            "sfd_show_max": self.chk_sfd_max.isChecked(),
            "sfd_show_min": self.chk_sfd_min.isChecked(),
        }
    
    def _apply_settings(self):
        """Applique les paramètres et ferme le dialogue"""
        self.settings = self._collect_settings()
        self._save_settings()
        self.settings_applied.emit(self.settings)
        self.status_label.setText("✅ Paramètres appliqués et sauvegardés")
        self.status_label.setStyleSheet("color: #22c55e; font-size: 11px;")
        
        # Mettre à jour le canvas si des résultats existent
        if hasattr(self.main_window, 'canvas') and self.main_window.canvas:
            if hasattr(self.main_window.canvas, 'diagram_settings'):
                self.main_window.canvas.diagram_settings = self.settings
            if hasattr(self.main_window.canvas, 'draw_analysis_diagrams'):
                results = self.main_window._get_displayed_results()
                if results:
                    self.main_window.canvas.draw_analysis_diagrams(results)
        
        QMessageBox.information(self, "Succès", "Les paramètres des diagrammes ont été appliqués.")
        self.accept()
    
    def _apply_preview(self):
        """Applique les paramètres pour aperçu sans fermer"""
        self.settings = self._collect_settings()
        self.settings_applied.emit(self.settings)
        self.status_label.setText("👁️ Aperçu mis à jour")
        self.status_label.setStyleSheet("color: #4fc3f7; font-size: 11px;")
        
        # Mettre à jour le canvas
        if hasattr(self.main_window, 'canvas') and self.main_window.canvas:
            self.main_window.canvas.diagram_settings = self.settings
            results = self.main_window._get_displayed_results()
            if results:
                self.main_window.canvas.draw_analysis_diagrams(results)
    
    def _reset_defaults(self):
        """Réinitialise aux valeurs par défaut"""
        reply = QMessageBox.question(
            self, "Confirmation",
            "Réinitialiser tous les paramètres aux valeurs par défaut ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.settings = self.default_settings.copy()
            self._populate_values()
            self.status_label.setText("🔄 Paramètres réinitialisés")
            self.status_label.setStyleSheet("color: #f59e0b; font-size: 11px;")