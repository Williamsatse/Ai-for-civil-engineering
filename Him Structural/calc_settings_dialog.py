# calc_settings_dialog.py
"""
Dialogue « Hypothèses de ferraillage »
Permet de choisir l'enrobage et le type d'acier utilisés dans les calculs
de ferraillage (menu Calculs → Hypothèses de ferraillage).
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QLabel, QDoubleSpinBox, QComboBox,
    QPushButton, QFrame
)
from PySide6.QtCore import Qt
from chinese_standard import ChineseSteel


# ── Grades d'acier disponibles ────────────────────────────────────────────
STEEL_GRADES = list(ChineseSteel.GRADES_CONSTRUCTION.keys())

# Descriptions affichées dans le combo
STEEL_DESCRIPTIONS = {
    "HPB235": "HPB235  — fy = 210 MPa  (acier doux)",
    "HRB335": "HRB335  — fy = 300 MPa  (courant)",
    "HRB400": "HRB400  — fy = 360 MPa  (haute résistance)",
    "RRB400": "RRB400  — fy = 360 MPa  (haute résistance, recyclé)",
    "HRB500": "HRB500  — fy = 435 MPa  (très haute résistance)",
}


class CalcSettingsDialog(QDialog):
    """Dialogue de paramétrage des hypothèses de ferraillage."""

    STYLE = """
        QDialog        { background: #12121f; color: #e0e0e0; }
        QGroupBox      { font-weight: bold; border: 1px solid #2e4a7a;
                         border-radius: 6px; margin-top: 14px; color: #4fc3f7; }
        QGroupBox::title { left: 12px; padding: 0 6px; }
        QLabel         { color: #d0d0d0; }
        QDoubleSpinBox { background: #1e1e30; color: #e0e0e0;
                         border: 1px solid #3a5a8a; border-radius: 4px;
                         padding: 4px 8px; min-height: 28px; }
        QDoubleSpinBox:focus { border: 1px solid #4fc3f7; }
        QComboBox      { background: #1e1e30; color: #e0e0e0;
                         border: 1px solid #3a5a8a; border-radius: 4px;
                         padding: 4px 8px; min-height: 28px; }
        QComboBox::drop-down { border: none; }
        QComboBox QAbstractItemView { background: #1e1e30; color: #e0e0e0;
                                      selection-background-color: #2e4a7a; }
        QPushButton    { background: #1a4a8a; color: #fff; border: none;
                         border-radius: 5px; padding: 8px 24px; font-size: 13px; }
        QPushButton:hover  { background: #2060b0; }
        QPushButton#cancel { background: #333; }
        QPushButton#cancel:hover { background: #444; }
        QFrame#sep     { background: #2e4a7a; }
    """

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("Configuration")
        self.setStyleSheet(self.STYLE)
        self.resize(480, 340)
        self.setModal(True)
        self._build_ui()
        self._load_current_settings()

    # ── Construction UI ──────────────────────────────────────────────────
    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(24, 20, 24, 20)
        main.setSpacing(16)

        # ── Titre ─────────────────────────────────────────────────────────
        title = QLabel("⚙️  Configuration de ferraillage — GB 50010")
        title.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #4fc3f7; "
            "padding-bottom: 4px;"
        )
        main.addWidget(title)

        sep = QFrame(); sep.setObjectName("sep")
        sep.setFrameShape(QFrame.HLine); sep.setFixedHeight(1)
        main.addWidget(sep)

        # ── Groupe Enrobage ───────────────────────────────────────────────
        grp_cover = QGroupBox("Enrobage")
        fl_cover  = QFormLayout(grp_cover)
        fl_cover.setSpacing(10)

        self.cover_spin = QDoubleSpinBox()
        self.cover_spin.setRange(10.0, 120.0)
        self.cover_spin.setDecimals(0)
        self.cover_spin.setSingleStep(5.0)
        self.cover_spin.setSuffix(" mm")
        self.cover_spin.setMinimumWidth(120)

        cover_note = QLabel(
            "<small style='color:#888;'>"
            "Enrobage nominal a<sub>s</sub> (distance fibre extrême → centre armature)"
            "</small>"
        )
        cover_note.setTextFormat(Qt.RichText)
        cover_note.setWordWrap(True)

        fl_cover.addRow("Enrobage a<sub>s</sub> :", self.cover_spin)
        fl_cover.addRow(cover_note)
        main.addWidget(grp_cover)

        # ── Groupe Type d'acier ───────────────────────────────────────────
        grp_steel = QGroupBox("Type d'acier")
        fl_steel  = QFormLayout(grp_steel)
        fl_steel.setSpacing(10)

        self.steel_combo = QComboBox()
        for grade in STEEL_GRADES:
            desc = STEEL_DESCRIPTIONS.get(grade, grade)
            self.steel_combo.addItem(desc, userData=grade)
        self.steel_combo.currentIndexChanged.connect(self._on_steel_changed)
        self.steel_combo.setMinimumWidth(260)

        self.steel_info_lbl = QLabel()
        self.steel_info_lbl.setStyleSheet("color:#4fc3f7; font-size:12px;")

        fl_steel.addRow("Grade :", self.steel_combo)
        fl_steel.addRow(self.steel_info_lbl)
        main.addWidget(grp_steel)

        main.addStretch()

        # ── Boutons ───────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("✅  Appliquer")
        btn_ok.clicked.connect(self._apply)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        main.addLayout(btn_row)

    # ── Chargement des settings actuels ──────────────────────────────────
    def _load_current_settings(self):
        s = self.main_window.settings

        cover = float(s.get("calc_cover", 30.0))
        self.cover_spin.setValue(cover)

        steel = s.get("calc_steel_grade", "HRB400").upper()
        for i in range(self.steel_combo.count()):
            if self.steel_combo.itemData(i) == steel:
                self.steel_combo.setCurrentIndex(i)
                break

        self._on_steel_changed()

    # ── Info acier dynamique ──────────────────────────────────────────────
    def _on_steel_changed(self):
        grade = self.steel_combo.currentData() or "HRB400"
        props = ChineseSteel.get_properties(grade)
        fy  = props.get("fy",  360)
        fyd = props.get("fyd", 360)
        Es  = props.get("Es",  200000)
        xi_b_map = {
            "HPB235": 0.614, "HRB335": 0.550,
            "HRB400": 0.518, "HRB500": 0.482, "RRB400": 0.518,
        }
        xi_b = xi_b_map.get(grade, 0.518)
        self.steel_info_lbl.setText(
            f"fy = {fy} MPa  |  fyd = {fyd} MPa  |  "
            f"Es = {Es//1000} GPa  |  ξ<sub>b</sub> = {xi_b}"
        )
        self.steel_info_lbl.setTextFormat(Qt.RichText)

    # ── Appliquer ─────────────────────────────────────────────────────────
    def _apply(self):
        new_settings = {
            "calc_cover":       float(self.cover_spin.value()),
            "calc_steel_grade": self.steel_combo.currentData() or "HRB400",
        }
        self.main_window.settings.update(new_settings)
        self.main_window.save_settings_to_file()
        self.main_window.show_status_message(
            f"✅ Configuration mises à jour : "
            f"enrobage = {new_settings['calc_cover']:.0f} mm  |  "
            f"acier = {new_settings['calc_steel_grade']}",
            "success", 5000
        )
        self.accept()