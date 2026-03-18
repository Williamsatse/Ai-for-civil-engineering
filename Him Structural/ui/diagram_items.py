from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainterPath, QPainter, QFontMetricsF
from PySide6.QtCore import Qt, QRectF, QPointF
import math


# ─────────────────────────────────────────────────────────────────────────────
# Utilitaire : étiquette avec fond arrondi
# ─────────────────────────────────────────────────────────────────────────────
def _draw_label(painter, text, cx, cy, text_color, bg_color, font_size=8):
    font_size = max(6, int(font_size) if font_size else 8)  # garde-fou Qt
    font = QFont("Segoe UI", font_size, QFont.Bold)
    painter.setFont(font)
    fm = QFontMetricsF(font)
    tw = fm.horizontalAdvance(text)
    th = fm.height()
    pad_x, pad_y = 5, 3
    rect = QRectF(cx - tw/2 - pad_x, cy - th/2 - pad_y, tw + 2*pad_x, th + 2*pad_y)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(bg_color))
    painter.drawRoundedRect(rect, 4, 4)
    painter.setPen(text_color)
    painter.drawText(rect, Qt.AlignCenter, text)


# ─────────────────────────────────────────────────────────────────────────────
# BMD — Bending Moment Diagram
# ─────────────────────────────────────────────────────────────────────────────
class BMDItem(QGraphicsItem):
    MAX_HEIGHT = 90

    def __init__(self, beam, results, settings=None):
        super().__init__()
        self.beam     = beam
        self.results  = results
        self.settings = settings or {}
        self.setZValue(15)
        ns = beam.node_start
        ne = beam.node_end
        self.setPos(ns.x, ns.y)
        dx = ne.x - ns.x
        dy = ne.y - ns.y
        self.angle  = math.degrees(math.atan2(dy, dx))
        self.length = math.hypot(dx, dy)

    def boundingRect(self):
        return QRectF(-60, -30, self.length + 120, self.MAX_HEIGHT + 80)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing, True)
        if not self.results or 'M_diagram' not in self.results:
            return

        points  = self.results['M_diagram']
        color   = QColor(self.settings.get("bmd_color", "#ef4444"))
        lw      = self.settings.get("bmd_line_width", 2.8)
        do_fill = self.settings.get("bmd_fill", True)
        alpha   = self.settings.get("bmd_fill_alpha", 35)
        invert  = -1 if self.settings.get("bmd_invert_sign", False) else 1
        show_max_label = self.settings.get("bmd_show_max", True)

        painter.rotate(-self.angle)

        max_m = max(abs(m) for _, m in points) + 1e-9
        scale = self.MAX_HEIGHT / max_m

        # ── Diagramme vers le BAS ──
        path = QPainterPath()
        for i, (x, m_val) in enumerate(points):
            y = m_val * scale * invert
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        painter.setPen(QPen(color, lw, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        # ── Remplissage ──
        if do_fill:
            fill_color = QColor(color)
            fill_color.setAlpha(alpha)
            fill_path = QPainterPath(path)
            fill_path.lineTo(self.length, 0)
            fill_path.lineTo(0, 0)
            fill_path.closeSubpath()
            painter.setBrush(QBrush(fill_color))
            painter.setPen(Qt.NoPen)
            painter.fillPath(fill_path, QBrush(fill_color))

        # ── Marqueur Mmax ──
        if show_max_label:
            Mmax_kNm = self.results.get('Mmax', 0)
            Lm       = self.results.get("L_m", self.length / 400)

            max_idx = max(range(len(points)), key=lambda i: abs(points[i][1]))
            x_max, m_max = points[max_idx]
            y_max = m_max * scale * invert

            # Ligne pointillée poutre → sommet
            painter.setPen(QPen(QColor("#ffffff60"), 1.2, Qt.DashLine))
            painter.drawLine(QPointF(x_max, 0), QPointF(x_max, y_max))

            # Cercle blanc au sommet
            painter.setPen(QPen(color, 1.5))
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawEllipse(QPointF(x_max, y_max), 4, 4)

            # Étiquette fond coloré
            label_text = f"Mmax = {abs(Mmax_kNm):.2f} kN·m   L = {Lm:.2f} m"
            font_size  = max(7, self.settings.get("text_font_size", 8) or 8)
            label_y    = y_max + 18
            _draw_label(
                painter, label_text, cx=x_max, cy=label_y,
                text_color=QColor("#ffffff"),
                bg_color=QColor(int(color.red()*0.5), int(color.green()*0.4),
                                int(color.blue()*0.4), 210),
                font_size=font_size
            )


# ─────────────────────────────────────────────────────────────────────────────
# SFD — Shear Force Diagram
# ─────────────────────────────────────────────────────────────────────────────
class SFDItem(QGraphicsItem):
    MAX_HEIGHT = 80

    def __init__(self, beam, results, settings=None):
        super().__init__()
        self.beam     = beam
        self.results  = results
        self.settings = settings or {}
        self.setZValue(14)
        ns = beam.node_start
        ne = beam.node_end
        self.setPos(ns.x, ns.y)
        dx = ne.x - ns.x
        dy = ne.y - ns.y
        self.angle  = math.degrees(math.atan2(dy, dx))
        self.length = math.hypot(dx, dy)

    def boundingRect(self):
        return QRectF(-60, -(self.MAX_HEIGHT + 30),
                      self.length + 120, 2*(self.MAX_HEIGHT + 50))

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing, True)
        if not self.results or 'V_diagram' not in self.results:
            return

        points     = self.results['V_diagram']
        color      = QColor(self.settings.get("sfd_color", "#3498db"))
        lw         = self.settings.get("sfd_line_width", 3.5)
        fill_alpha = self.settings.get("sfd_fill_alpha", 75)
        show_max_label = self.settings.get("sfd_show_max", True)

        painter.rotate(-self.angle)

        max_v = max(abs(v) for _, v in points) + 1e-9
        scale = self.MAX_HEIGHT / max_v

        # ── Ligne zéro sur la poutre ──
        painter.setPen(QPen(QColor("#6666aa"), 1.5, Qt.DashLine))
        painter.drawLine(QPointF(0, 0), QPointF(self.length, 0))

        # ── Diagramme (V+ → haut, V- → bas) ──
        path = QPainterPath()
        for i, (x, v) in enumerate(points):
            y = -v * scale
            if i == 0:
                path.moveTo(x, y)
            else:
                if abs(v - points[i-1][1]) > 0.5:
                    path.lineTo(x, path.currentPosition().y())
                path.lineTo(x, y)

        painter.setPen(QPen(color, lw, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        # ── Remplissage ──
        if self.settings.get("sfd_fill", False):
            fill_color = QColor(color)
            fill_color.setAlpha(fill_alpha)
            for i in range(len(points)-1):
                x1, v1 = points[i]
                x2, v2 = points[i+1]
                y1, y2 = -v1*scale, -v2*scale
                fp = QPainterPath()
                fp.moveTo(x1, 0); fp.lineTo(x1, y1)
                fp.lineTo(x2, y2); fp.lineTo(x2, 0)
                fp.closeSubpath()
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(fill_color))
                painter.drawPath(fp)

        # ── Marqueur Vmax ──
        if show_max_label:
            Vmax_kN = self.results.get('Vmax', 0)
            Lm      = self.results.get("L_m", self.length / 400)

            max_idx = max(range(len(points)), key=lambda i: abs(points[i][1]))
            x_max, v_max = points[max_idx]
            y_max = -v_max * scale

            # Ligne pointillée poutre → sommet
            painter.setPen(QPen(QColor("#ffffff60"), 1.2, Qt.DashLine))
            painter.drawLine(QPointF(x_max, 0), QPointF(x_max, y_max))

            # Cercle blanc au sommet
            painter.setPen(QPen(color, 1.5))
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawEllipse(QPointF(x_max, y_max), 4, 4)

            # Étiquette fond coloré — au-dessus si V positif, en-dessous si négatif
            label_text = f"Vmax = {abs(Vmax_kN):.2f} kN   L = {Lm:.2f} m"
            font_size  = max(7, self.settings.get("text_font_size", 8) or 8)
            label_y    = y_max - 18 if y_max < 0 else y_max + 18
            _draw_label(
                painter, label_text, cx=x_max, cy=label_y,
                text_color=QColor("#ffffff"),
                bg_color=QColor(int(color.red()*0.4), int(color.green()*0.4),
                                int(color.blue()*0.7), 210),
                font_size=font_size
            )