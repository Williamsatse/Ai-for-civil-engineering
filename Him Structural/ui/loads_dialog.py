# loads_dialog.py
"""
Dialogue d'ajout/édition de charges — Foster Structural
  • Charge ponctuelle sur poutre (avec type G/Q)
  • Charge répartie : distance depuis côté A ou B + longueur en mètres, type G/Q
  • Edition en place d'une charge existante via EditLoadDialog
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QDoubleSpinBox, QRadioButton,
    QButtonGroup, QGroupBox, QComboBox, QCheckBox,
    QFrame, QSizePolicy, QMessageBox, QTabWidget, QWidget,
    QFormLayout
)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QFont
from structural_model import PointLoad, PointLoadOnBeam, DistributedLoad

SCALE_PX_PER_M = 160.0   # 1 m = 4 carreaux × 40 px


# ══════════════════════════════════════════════════════
# Schéma visuel — charge ponctuelle
# ══════════════════════════════════════════════════════
class LoadSchemeWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(260, 140)
        self.setMaximumSize(340, 160)
        self.setStyleSheet("background:#2a2a3a; border:1px solid #444; border-radius:6px;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, QColor("#2a2a3a"))
        beam_y = h * 0.58; beam_x0 = w * 0.10; beam_x1 = w * 0.90; mid_x = (beam_x0 + beam_x1) / 2
        painter.setPen(QPen(QColor("#1e3a8a"), 2)); painter.setBrush(QColor("#fcd34d"))
        for nx in (beam_x0, beam_x1): painter.drawEllipse(QPointF(nx, beam_y), 7, 7)
        painter.setPen(QPen(QColor("#fcd34d"), 4, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(beam_x0, beam_y), QPointF(beam_x1, beam_y))
        arrow_top = beam_y - 52
        painter.setPen(QPen(QColor("#ef4444"), 2.5, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(mid_x, arrow_top), QPointF(mid_x, beam_y - 7))
        painter.setBrush(QColor("#ef4444")); painter.setPen(Qt.NoPen)
        tri = QPainterPath()
        tri.moveTo(mid_x, beam_y - 7); tri.lineTo(mid_x - 6, beam_y - 19); tri.lineTo(mid_x + 6, beam_y - 19)
        tri.closeSubpath(); painter.drawPath(tri)
        painter.setPen(QColor("#ef4444")); painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.drawText(QPointF(mid_x + 8, arrow_top + 14), "F")
        cote_y = beam_y + 22
        painter.setPen(QPen(QColor("#cccccc"), 1.5))
        painter.drawLine(QPointF(beam_x0, cote_y), QPointF(mid_x - 4, cote_y))
        painter.setBrush(QColor("#cccccc")); painter.setPen(Qt.NoPen)
        for tip_x, dir_x in [(beam_x0, 1), (mid_x, -1)]:
            p = QPainterPath(); p.moveTo(tip_x, cote_y)
            p.lineTo(tip_x + dir_x * 8, cote_y - 4); p.lineTo(tip_x + dir_x * 8, cote_y + 4)
            p.closeSubpath(); painter.drawPath(p)
        painter.setPen(QColor("#cccccc")); painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(QPointF((beam_x0 + mid_x) / 2 - 5, cote_y + 14), "x")


# ══════════════════════════════════════════════════════
# Schéma visuel — charge répartie (dynamique)
# ══════════════════════════════════════════════════════
class DistLoadSchemeWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(260, 115); self.setMaximumSize(420, 125)
        self.setStyleSheet("background:#2a2a3a; border:1px solid #444; border-radius:6px;")
        self.start_ratio = 0.0; self.end_ratio = 1.0; self.w_value = -8.0; self.load_type = "G"

    def update_view(self, start_ratio, end_ratio, w, load_type="G"):
        self.start_ratio = max(0.0, min(1.0, start_ratio))
        self.end_ratio   = max(0.0, min(1.0, end_ratio))
        self.w_value     = w; self.load_type = load_type; self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, QColor("#2a2a3a"))

        beam_y = h * 0.74
        beam_x0 = w * 0.07
        beam_x1 = w * 0.93
        beam_len = beam_x1 - beam_x0

        # === Labels A / B ===
        painter.setPen(QColor("#aaa"))
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        painter.drawText(QPointF(beam_x0 - 2, beam_y + 18), "A")
        painter.drawText(QPointF(beam_x1 - 4, beam_y + 18), "B")

        # === Poutre + nœuds ===
        painter.setPen(QPen(QColor("#1e3a8a"), 2))
        painter.setBrush(QColor("#fcd34d"))
        for nx in (beam_x0, beam_x1):
            painter.drawEllipse(QPointF(nx, beam_y), 5, 5)

        painter.setPen(QPen(QColor("#fcd34d"), 3.5, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(beam_x0, beam_y), QPointF(beam_x1, beam_y))

        # === CHARGE RÉPARTIE ===
        load_x0 = beam_x0 + self.start_ratio * beam_len
        load_x1 = beam_x0 + self.end_ratio   * beam_len

        arrow_color = QColor("#ef4444") if self.load_type == "G" else QColor("#FF9800")

        # === LIGNE INVERSÉE ICI ===
        downward = self.w_value >= 0          # ← CHANGEMENT (était <= 0)

        arrow_h = 34
        n = max(2, int((load_x1 - load_x0) / 20))

        painter.setBrush(QBrush(arrow_color))
        for i in range(n + 1):
            t = i / n if n > 0 else 0
            ax = load_x0 + t * (load_x1 - load_x0)
            tail_y = beam_y - arrow_h if downward else beam_y + arrow_h
            tip_y  = beam_y - 4       if downward else beam_y + 4

            painter.setPen(QPen(arrow_color, 1.8))
            painter.drawLine(QPointF(ax, tail_y), QPointF(ax, tip_y))

            # Tête de flèche
            painter.setPen(Qt.NoPen)
            tri = QPainterPath()
            if downward:
                tri.moveTo(ax, tip_y)
                tri.lineTo(ax - 4, tip_y - 8)
                tri.lineTo(ax + 4, tip_y - 8)
            else:
                tri.moveTo(ax, tip_y)
                tri.lineTo(ax - 4, tip_y + 8)
                tri.lineTo(ax + 4, tip_y + 8)
            tri.closeSubpath()
            painter.drawPath(tri)

        # Ligne de base
        tail_y = beam_y - arrow_h if downward else beam_y + arrow_h
        painter.setPen(QPen(arrow_color, 2.0))
        painter.drawLine(QPointF(load_x0, tail_y), QPointF(load_x1, tail_y))

        # Label
        lbl = "G" if self.load_type == "G" else "Q"
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        mid_lx = (load_x0 + load_x1) / 2
        painter.drawText(QPointF(mid_lx - 14, tail_y - 4 if downward else tail_y + 14),
                         f"{lbl} {self.w_value:+.1f} kN/m")


# ══════════════════════════════════════════════════════
# Dialogue d'EDITION d'une charge existante
# ══════════════════════════════════════════════════════
class EditLoadDialog(QDialog):
    """
    Ouvre un formulaire pré-rempli pour modifier une charge existante
    (PointLoadOnBeam ou DistributedLoad).
    """
    STYLE = """
        QDialog        { background:#1e1e2e; color:#e0e0e0; }
        QGroupBox      { border:1px solid #444; border-radius:5px; margin-top:8px;
                         color:#a0c4ff; font-weight:bold; padding:6px; }
        QGroupBox::title { subcontrol-origin:margin; left:10px; }
        QLabel         { color:#d0d0d0; }
        QDoubleSpinBox { background:#2a2a3a; color:#fff; border:1px solid #555;
                         border-radius:3px; padding:2px 4px; }
        QComboBox      { background:#2a2a3a; color:#fff; border:1px solid #555;
                         border-radius:3px; padding:2px 6px; }
        QRadioButton   { color:#d0d0d0; spacing:6px; }
        QPushButton    { background:#2e4a7a; color:#fff; border:none;
                         border-radius:4px; padding:6px 18px; }
        QPushButton:hover  { background:#3a5fa0; }
        QPushButton#cancel { background:#3a2e2e; }
        QPushButton#cancel:hover { background:#5a3a3a; }
    """

    def __init__(self, main_window, load, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.load = load
        self.setStyleSheet(self.STYLE)
        self.setMinimumWidth(400)

        if isinstance(load, PointLoadOnBeam):
            self.setWindowTitle("✏️  Éditer une charge ponctuelle")
            self._build_point_ui()
        elif isinstance(load, DistributedLoad):
            self.setWindowTitle("✏️  Éditer une charge répartie")
            self._build_dist_ui()
        else:
            QMessageBox.warning(parent, "Erreur", "Type de charge non éditable.")
            self.reject()

    # ── Formulaire charge ponctuelle ──────────────────
    def _build_point_ui(self):
        load = self.load
        root = QVBoxLayout(self)
        root.setSpacing(10); root.setContentsMargins(14, 14, 14, 14)

        root.addWidget(QLabel(f"<b>Poutre :</b> {load.beam.id}  |  "
                              f"L = {load.beam.length / SCALE_PX_PER_M:.3f} m",
                              self))

        # Type
        type_grp = QGroupBox("Type de charge")
        tr = QHBoxLayout(type_grp)
        self.p_radio_G = QRadioButton("🏗 Permanente (G)")
        self.p_radio_Q = QRadioButton("💨 Variable (Q)")
        ptg = QButtonGroup(self); ptg.addButton(self.p_radio_G); ptg.addButton(self.p_radio_Q)
        current_type = getattr(load, "load_type", "G")
        (self.p_radio_G if current_type == "G" else self.p_radio_Q).setChecked(True)
        tr.addWidget(self.p_radio_G); tr.addWidget(self.p_radio_Q)
        root.addWidget(type_grp)

        # Valeurs
        val_grp = QGroupBox("Valeurs de la force")
        vf = QFormLayout(val_grp)
        self.p_fx = QDoubleSpinBox(); self.p_fx.setRange(-5000,5000); self.p_fx.setDecimals(2)
        self.p_fx.setValue(load.fx); self.p_fx.setSuffix(" kN")
        self.p_fy = QDoubleSpinBox(); self.p_fy.setRange(-5000,5000); self.p_fy.setDecimals(2)
        self.p_fy.setValue(load.fy); self.p_fy.setSuffix(" kN")
        vf.addRow("Fx :", self.p_fx); vf.addRow("Fy :", self.p_fy)
        root.addWidget(val_grp)

        # Position
        pos_grp = QGroupBox("Position")
        pf = QFormLayout(pos_grp)
        self.p_pos = QDoubleSpinBox(); self.p_pos.setRange(0,1); self.p_pos.setDecimals(4)
        self.p_pos.setValue(load.position_ratio); self.p_pos.setSingleStep(0.05)
        self.p_pos.setPrefix("x/L = ")
        pf.addRow("Position (0→1) :", self.p_pos)
        L_m = load.beam.length / SCALE_PX_PER_M
        pos_m = QLabel(f"({load.position_ratio * L_m:.3f} m depuis A)")
        pos_m.setStyleSheet("color:#888; font-size:11px;")
        self.p_pos.valueChanged.connect(lambda v: pos_m.setText(f"({v * L_m:.3f} m depuis A)"))
        pf.addRow(pos_m)
        root.addWidget(pos_grp)

        self._add_buttons(root)

    # ── Formulaire charge répartie ────────────────────
    def _build_dist_ui(self):
        load = self.load
        member = getattr(load, "member", None) or getattr(load, "beam", None)
        L_m = member.length / SCALE_PX_PER_M if member else 1.0
        root = QVBoxLayout(self)
        root.setSpacing(10); root.setContentsMargins(14, 14, 14, 14)

        root.addWidget(QLabel(f"<b>Poutre :</b> {member.id if member else '?'}  |  "
                              f"L = {L_m:.3f} m", self))

        # Schéma
        self.scheme = DistLoadSchemeWidget()
        sr = QHBoxLayout(); sr.addStretch(); sr.addWidget(self.scheme); sr.addStretch()
        root.addLayout(sr)

        # Type
        type_grp = QGroupBox("Type de charge")
        tr = QHBoxLayout(type_grp)
        self.d_radio_G = QRadioButton("🏗 Permanente (G)")
        self.d_radio_Q = QRadioButton("💨 Variable (Q)")
        dtg = QButtonGroup(self); dtg.addButton(self.d_radio_G); dtg.addButton(self.d_radio_Q)
        current_type = getattr(load, "load_type", "G")
        (self.d_radio_G if current_type == "G" else self.d_radio_Q).setChecked(True)
        self.d_radio_G.toggled.connect(self._refresh_scheme)
        tr.addWidget(self.d_radio_G); tr.addWidget(self.d_radio_Q)
        root.addWidget(type_grp)

        # Intensité
        int_grp = QGroupBox("Intensité")
        inf = QFormLayout(int_grp)
        self.d_w = QDoubleSpinBox(); self.d_w.setRange(-5000,5000); self.d_w.setDecimals(2)
        self.d_w.setValue(load.w); self.d_w.setSuffix(" kN/m")
        self.d_w.valueChanged.connect(self._refresh_scheme)
        inf.addRow("w :", self.d_w)
        inf.addRow(QLabel("<small><i style='color:#888'>Négatif = vers le bas</i></small>"))
        root.addWidget(int_grp)

        # Position par côté + longueur
        pos_grp = QGroupBox("Position (depuis un côté)")
        pf = QFormLayout(pos_grp)

        sr_row = QHBoxLayout()
        self.d_from_left  = QRadioButton("Gauche (A)")
        self.d_from_right = QRadioButton("Droite (B)")
        self.d_from_left.setChecked(True)
        sg = QButtonGroup(self); sg.addButton(self.d_from_left); sg.addButton(self.d_from_right)
        self.d_from_left.toggled.connect(self._refresh_scheme)
        sr_row.addWidget(self.d_from_left); sr_row.addWidget(self.d_from_right)
        pf.addRow("Côté de référence :", sr_row)

        # Reconvertir start_pos/end_pos → offset + length depuis la gauche
        self._L_m = L_m
        offset_m = load.start_pos * L_m
        length_m = (load.end_pos - load.start_pos) * L_m

        self.d_offset = QDoubleSpinBox(); self.d_offset.setRange(0, L_m); self.d_offset.setDecimals(3)
        self.d_offset.setSuffix(" m"); self.d_offset.setValue(offset_m); self.d_offset.setSingleStep(0.1)
        self.d_offset.valueChanged.connect(self._refresh_scheme)
        pf.addRow("Distance depuis le côté :", self.d_offset)

        self.d_length = QDoubleSpinBox(); self.d_length.setRange(0.001, L_m); self.d_length.setDecimals(3)
        self.d_length.setSuffix(" m"); self.d_length.setValue(length_m); self.d_length.setSingleStep(0.1)
        self.d_length.valueChanged.connect(self._refresh_scheme)
        pf.addRow("Longueur de la charge :", self.d_length)
        root.addWidget(pos_grp)

        self._add_buttons(root)
        self._refresh_scheme()

    def _refresh_scheme(self):
        """Mise à jour du schéma visuel depuis les valeurs actuelles."""
        L_m = self._L_m
        if L_m <= 0: return
        offset_m = self.d_offset.value(); length_m = self.d_length.value()
        if self.d_from_right.isChecked():
            start_m = L_m - offset_m - length_m; end_m = L_m - offset_m
        else:
            start_m = offset_m; end_m = offset_m + length_m
        sr = max(0.0, min(1.0, start_m / L_m)); er = max(0.0, min(1.0, end_m / L_m))
        lt = "G" if self.d_radio_G.isChecked() else "Q"
        self.scheme.update_view(sr, er, self.d_w.value(), lt)

    def _add_buttons(self, root):
        btn_row = QHBoxLayout(); btn_row.addStretch()
        save_btn = QPushButton("💾 Enregistrer")
        save_btn.setFixedHeight(34); save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Annuler"); cancel_btn.setObjectName("cancel")
        cancel_btn.setFixedHeight(34); cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn); btn_row.addWidget(cancel_btn)
        root.addLayout(btn_row)

    def _save(self):
        load = self.load
        if isinstance(load, PointLoadOnBeam):
            load.fx = self.p_fx.value()
            load.fy = self.p_fy.value()
            load.position_ratio = self.p_pos.value()
            load.load_type = "G" if self.p_radio_G.isChecked() else "Q"
            # Mettre à jour le graphique
            gi = getattr(load, "graphics_item", None)
            if gi:
                gi._update_label_text(); gi._update_position(); gi.update()

        elif isinstance(load, DistributedLoad):
            load.w = self.d_w.value()
            load.load_type = "G" if self.d_radio_G.isChecked() else "Q"
            L_m = self._L_m
            offset_m = self.d_offset.value(); length_m = self.d_length.value()
            if self.d_from_right.isChecked():
                start_m = L_m - offset_m - length_m; end_m = L_m - offset_m
            else:
                start_m = offset_m; end_m = offset_m + length_m
            load.start_pos = max(0.0, min(1.0, start_m / L_m))
            load.end_pos   = max(0.0, min(1.0, end_m   / L_m))
            # Mettre à jour le graphique
            gi = getattr(load, "graphics_item", None)
            if gi:
                gi.update()

        if self.main_window and hasattr(self.main_window, "canvas"):
            self.main_window.canvas.scene.update()
            self.main_window.canvas.viewport().update()
        self.accept()


# ══════════════════════════════════════════════════════
# Dialogue principal d'AJOUT de charges
# ══════════════════════════════════════════════════════
class LoadsDialog(QDialog):
    """Deux onglets : charge ponctuelle et charge répartie."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setWindowTitle("Ajout de charges — Foster Structural")
        self.setMinimumWidth(500); self.setMaximumWidth(600)
        self.setStyleSheet("""
            QDialog        { background:#1e1e2e; color:#e0e0e0; }
            QGroupBox      { border:1px solid #444; border-radius:5px; margin-top:8px;
                             color:#a0c4ff; font-weight:bold; padding:6px; }
            QGroupBox::title { subcontrol-origin:margin; left:10px; }
            QLabel         { color:#d0d0d0; }
            QDoubleSpinBox { background:#2a2a3a; color:#fff; border:1px solid #555;
                             border-radius:3px; padding:2px 4px; }
            QComboBox      { background:#2a2a3a; color:#fff; border:1px solid #555;
                             border-radius:3px; padding:2px 6px; }
            QRadioButton   { color:#d0d0d0; spacing:6px; }
            QCheckBox      { color:#d0d0d0; spacing:6px; }
            QPushButton    { background:#2e4a7a; color:#fff; border:none;
                             border-radius:4px; padding:6px 18px; }
            QPushButton:hover  { background:#3a5fa0; }
            QPushButton#btn_cancel { background:#3a2e2e; }
            QPushButton#btn_cancel:hover { background:#5a3a3a; }
        """)
        self._build_ui()
        self._fill_beams_combo()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(10); root.setContentsMargins(14, 14, 14, 14)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane  { border:1px solid #444; background:#1e1e2e; }
            QTabBar::tab      { background:#2a2a3a; color:#aaa; padding:6px 16px;
                                border-radius:4px 4px 0 0; }
            QTabBar::tab:selected { background:#1e1e2e; color:#fff;
                                    border-bottom:2px solid #4fc3f7; }
        """)
        root.addWidget(self.tabs)

        tab_point = QWidget(); self._build_point_tab(tab_point)
        self.tabs.addTab(tab_point, "⬇  Charge ponctuelle")

        tab_dist = QWidget(); self._build_dist_tab(tab_dist)
        self.tabs.addTab(tab_dist, "〰  Charge répartie")

        btn_row = QHBoxLayout(); btn_row.addStretch()
        self.btn_add = QPushButton("Ajouter")
        self.btn_add.setFixedHeight(34); self.btn_add.clicked.connect(self._on_add)
        btn_close = QPushButton("Fermer"); btn_close.setObjectName("btn_cancel")
        btn_close.setFixedHeight(34); btn_close.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_add); btn_row.addWidget(btn_close)
        root.addLayout(btn_row)

    # ── Tab charge ponctuelle ──────────────────────────
    def _build_point_tab(self, tab):
        layout = QVBoxLayout(tab); layout.setSpacing(8)
        sr = QHBoxLayout(); sr.addStretch(); sr.addWidget(LoadSchemeWidget()); sr.addStretch()
        layout.addLayout(sr)

        beam_row = QHBoxLayout(); beam_row.addWidget(QLabel("Poutre :"))
        self.beam_combo = QComboBox()
        self.beam_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        beam_row.addWidget(self.beam_combo); layout.addLayout(beam_row)

        type_grp = QGroupBox("Type de charge"); tr = QHBoxLayout(type_grp)
        self.point_radio_G = QRadioButton("🏗 Permanente (G)")
        self.point_radio_Q = QRadioButton("💨 Variable / Dynamique (Q)")
        self.point_radio_G.setChecked(True)
        ptg = QButtonGroup(self); ptg.addButton(self.point_radio_G); ptg.addButton(self.point_radio_Q)
        tr.addWidget(self.point_radio_G); tr.addWidget(self.point_radio_Q)
        layout.addWidget(type_grp)

        val_group = QGroupBox("Valeurs"); val_grid = QGridLayout(val_group)
        for col, txt in enumerate(["", "F (kN)", "M (kN·m)", "▽ (Deg)"], 0):
            lbl = QLabel(txt); lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color:#a0c4ff; font-weight:bold;")
            val_grid.addWidget(lbl, 0, col)

        def spin(lo=-5000, hi=5000, dec=2, val=0.0):
            s = QDoubleSpinBox(); s.setRange(lo, hi); s.setDecimals(dec)
            s.setValue(val); s.setFixedHeight(28); return s

        val_grid.addWidget(QLabel("X :"), 1, 0)
        self.fx_spin = spin(val=0.0);  val_grid.addWidget(self.fx_spin, 1, 1)
        self.mx_spin = spin(val=0.0);  val_grid.addWidget(self.mx_spin, 1, 2)
        self.ax_spin = spin(-360,360,1,0.0); val_grid.addWidget(self.ax_spin, 1, 3)
        val_grid.addWidget(QLabel("Y :"), 2, 0)
        self.fy_spin = spin(val=-10.0); val_grid.addWidget(self.fy_spin, 2, 1)
        self.my_spin = spin(val=0.0);  val_grid.addWidget(self.my_spin, 2, 2)
        self.ay_spin = spin(-360,360,1,0.0); val_grid.addWidget(self.ay_spin, 2, 3)
        val_grid.addWidget(QLabel("Z :"), 3, 0)
        self.fz_spin = spin(val=0.0);  val_grid.addWidget(self.fz_spin, 3, 1)
        self.mz_spin = spin(val=0.0);  val_grid.addWidget(self.mz_spin, 3, 2)
        self.az_spin = spin(-360,360,1,0.0); val_grid.addWidget(self.az_spin, 3, 3)
        layout.addWidget(val_group)

        ref_group = QGroupBox("Dans le repère :"); ref_row = QHBoxLayout(ref_group)
        self.radio_global = QRadioButton("global"); self.radio_local = QRadioButton("local")
        self.radio_global.setChecked(True)
        rg = QButtonGroup(self); rg.addButton(self.radio_global); rg.addButton(self.radio_local)
        ref_row.addWidget(self.radio_global); ref_row.addWidget(self.radio_local); ref_row.addStretch()
        layout.addWidget(ref_group)

        coord_group = QGroupBox("Coordonnée"); coord_layout = QGridLayout(coord_group)
        coord_layout.addWidget(QLabel("x ="), 0, 0)
        self.x_pos_spin = QDoubleSpinBox(); self.x_pos_spin.setRange(0, 10000)
        self.x_pos_spin.setDecimals(3); self.x_pos_spin.setValue(0.50); self.x_pos_spin.setFixedHeight(28)
        coord_layout.addWidget(self.x_pos_spin, 0, 1)
        self.radio_relative = QRadioButton("relative  (x/L)")
        self.radio_absolue  = QRadioButton("absolue   (m)"); self.radio_absolue.setChecked(True)
        cg = QButtonGroup(self); cg.addButton(self.radio_relative); cg.addButton(self.radio_absolue)
        coord_layout.addWidget(self.radio_relative, 0, 2); coord_layout.addWidget(self.radio_absolue, 1, 2)
        layout.addWidget(coord_group)
        layout.addStretch()

    # ── Tab charge répartie ────────────────────────────
    def _build_dist_tab(self, tab):
        layout = QVBoxLayout(tab); layout.setSpacing(8); layout.setContentsMargins(12, 12, 12, 12)
        self.dist_scheme = DistLoadSchemeWidget()
        sr = QHBoxLayout(); sr.addStretch(); sr.addWidget(self.dist_scheme); sr.addStretch()
        layout.addLayout(sr)

        beam_row = QHBoxLayout(); beam_row.addWidget(QLabel("Poutre :"))
        self.beam_combo_dist = QComboBox()
        self.beam_combo_dist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.beam_combo_dist.currentIndexChanged.connect(self._on_dist_beam_changed)
        beam_row.addWidget(self.beam_combo_dist); layout.addLayout(beam_row)

        type_grp = QGroupBox("Type de charge"); tr = QHBoxLayout(type_grp)
        self.dist_radio_G = QRadioButton("🏗 Permanente G")
        self.dist_radio_Q = QRadioButton("💨 Variable / Dynamique Q")
        self.dist_radio_G.setChecked(True)
        dtg = QButtonGroup(self); dtg.addButton(self.dist_radio_G); dtg.addButton(self.dist_radio_Q)
        self.dist_radio_G.toggled.connect(self._update_dist_scheme)
        tr.addWidget(self.dist_radio_G); tr.addWidget(self.dist_radio_Q); layout.addWidget(type_grp)

        int_grp = QGroupBox("Intensité"); inf = QFormLayout(int_grp)
        self.w_spin = QDoubleSpinBox(); self.w_spin.setRange(-5000,5000); self.w_spin.setDecimals(2)
        self.w_spin.setSuffix(" kN/m"); self.w_spin.setValue(8)
        self.w_spin.valueChanged.connect(self._update_dist_scheme)
        inf.addRow("Intensité w :", self.w_spin)
        #inf.addRow(QLabel("<small><i style='color:#888'>Négatif = vers le bas (gravité)</i></small>"))
        layout.addWidget(int_grp)

        pos_grp = QGroupBox("Position de la charge"); pf = QFormLayout(pos_grp)
        side_row = QHBoxLayout()
        self.radio_from_left  = QRadioButton("Depuis le côté Gauche (A)")
        self.radio_from_right = QRadioButton("Depuis le côté Droit (B)")
        self.radio_from_left.setChecked(True)
        sg = QButtonGroup(self); sg.addButton(self.radio_from_left); sg.addButton(self.radio_from_right)
        self.radio_from_left.toggled.connect(self._update_dist_scheme)
        side_row.addWidget(self.radio_from_left); side_row.addWidget(self.radio_from_right)
        pf.addRow("Côté de référence :", side_row)

        self.dist_offset_spin = QDoubleSpinBox(); self.dist_offset_spin.setRange(0, 10000)
        self.dist_offset_spin.setDecimals(3); self.dist_offset_spin.setSuffix(" m")
        self.dist_offset_spin.setValue(0.0); self.dist_offset_spin.setSingleStep(0.1)
        self.dist_offset_spin.valueChanged.connect(self._update_dist_scheme)
        pf.addRow("Distance depuis le côté :", self.dist_offset_spin)

        self.dist_length_spin = QDoubleSpinBox(); self.dist_length_spin.setRange(0.001, 10000)
        self.dist_length_spin.setDecimals(3); self.dist_length_spin.setSuffix(" m")
        self.dist_length_spin.setValue(1.0); self.dist_length_spin.setSingleStep(0.1)
        self.dist_length_spin.valueChanged.connect(self._update_dist_scheme)
        pf.addRow("Longueur de la charge :", self.dist_length_spin)

        self.dist_info_label = QLabel("Longueur totale de la poutre : – m")
        self.dist_info_label.setStyleSheet("color:#888; font-size:11px;")
        pf.addRow(self.dist_info_label)
        layout.addWidget(pos_grp); layout.addStretch()

    # ── Helpers ──────────────────────────────────────
    def _fill_beams_combo(self):
        beams = self.main_window.model.beams
        for combo in (self.beam_combo, self.beam_combo_dist):
            combo.clear()
            if not beams:
                combo.addItem("Aucune poutre disponible"); continue
            for b in beams:
                L_m = b.length / SCALE_PX_PER_M
                combo.addItem(f"Poutre {b.id}  ({b.node_start.id}→{b.node_end.id})  L={L_m:.2f}m",
                              userData=b)
        self._on_dist_beam_changed()

    def _on_dist_beam_changed(self):
        beam = self.beam_combo_dist.currentData()
        if beam:
            L_m = beam.length / SCALE_PX_PER_M
            self.dist_info_label.setText(f"Longueur totale de la poutre : {L_m:.3f} m")
            self.dist_offset_spin.setMaximum(L_m); self.dist_length_spin.setMaximum(L_m)
            if self.dist_length_spin.value() > L_m: self.dist_length_spin.setValue(L_m)
        self._update_dist_scheme()

    def _get_dist_ratios(self):
        beam = self.beam_combo_dist.currentData()
        if not beam: return 0.0, 1.0
        L_m = beam.length / SCALE_PX_PER_M
        if L_m <= 0: return 0.0, 1.0
        offset_m = self.dist_offset_spin.value(); length_m = self.dist_length_spin.value()
        if self.radio_from_right.isChecked():
            start_m = L_m - offset_m - length_m; end_m = L_m - offset_m
        else:
            start_m = offset_m; end_m = offset_m + length_m
        return max(0.0, min(1.0, start_m / L_m)), max(0.0, min(1.0, end_m / L_m))

    def _update_dist_scheme(self):
        start, end = self._get_dist_ratios()
        lt = "G" if self.dist_radio_G.isChecked() else "Q"
        self.dist_scheme.update_view(start, end, self.w_spin.value(), lt)

    # ── Actions ──────────────────────────────────────
    def _on_add(self):
        if self.tabs.currentIndex() == 0:
            self._add_point_load()
        else:
            self._add_distributed_load()

    def _add_point_load(self):
        beam = self.beam_combo.currentData()
        if beam is None:
            QMessageBox.warning(self, "Erreur", "Aucune poutre disponible."); return
        fx = self.fx_spin.value(); fy = self.fy_spin.value(); mz = self.mz_spin.value()
        if fx == 0 and fy == 0 and mz == 0:
            QMessageBox.warning(self, "Erreur", "Au moins une composante doit être non nulle.")
            return
        x_val = self.x_pos_spin.value(); L_m = beam.length / SCALE_PX_PER_M
        if self.radio_relative.isChecked():
            position_ratio = max(0.0, min(1.0, x_val))
        else:
            position_ratio = max(0.0, min(1.0, x_val / L_m)) if L_m > 0 else 0.0
        load_type = "G" if self.point_radio_G.isChecked() else "Q"
        load = self.main_window.model.add_point_load_on_beam(beam, position_ratio, fx, fy)
        load.load_type = load_type
        self.main_window.canvas.add_point_load_on_beam_visual(load)
        self.main_window.show_status_message(
            f"✅ Charge {load_type} sur {beam.id}  Fy={fy:+.2f}kN  @ {position_ratio*100:.1f}%",
            "success", 4000)
        self.fy_spin.setValue(-10.0)

    def _add_distributed_load(self):
        beam = self.beam_combo_dist.currentData()
        if beam is None:
            QMessageBox.warning(self, "Erreur", "Aucune poutre disponible."); return
        w = self.w_spin.value()
        if w == 0:
            QMessageBox.warning(self, "Erreur", "L'intensité w ne peut pas être 0."); return
        start, end = self._get_dist_ratios()
        if start >= end:
            QMessageBox.warning(self, "Erreur",
                "Position début >= fin. Vérifiez la distance et la longueur."); return
        load_type = "G" if self.dist_radio_G.isChecked() else "Q"
        load = DistributedLoad(beam, w, start, end)
        load.load_type = load_type
        beam.distributed_loads.append(load)
        self.main_window.model.distributed_loads.append(load)
        self.main_window.canvas.add_distributed_load_visual(load)
        side_txt = "droite (B)" if self.radio_from_right.isChecked() else "gauche (A)"
        self.main_window.show_status_message(
            f"✅ {load_type} {w:+.2f}kN/m | depuis {side_txt} "
            f"à {self.dist_offset_spin.value():.2f}m | L={self.dist_length_spin.value():.2f}m",
            "success", 4000)