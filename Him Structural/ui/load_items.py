from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainter, QPolygonF, QPainterPath
from PySide6.QtCore import Qt, QRectF, QPointF
import math


# ════════════════════════════════════════════════════════════
# CHARGE PONCTUELLE SUR NŒUD
# ════════════════════════════════════════════════════════════
class PointLoadItem(QGraphicsItem):
    """
    Flèche représentant une charge ponctuelle sur un nœud.
    La pointe de la flèche est toujours dirigée vers le nœud.
    """
    ARROW_LENGTH = 100    # longueur visible de la tige de la flèche
    ARROW_HEAD   = 14     # taille de la tête de flèche
    LINE_WIDTH   = 2.5

    def __init__(self, load):
        super().__init__()
        self.load = load
        self.setZValue(30)

        if hasattr(load, "node"):
            self.setPos(load.node.x, load.node.y)

        # Label créé une seule fois
        self._label = QGraphicsTextItem(self)
        self._label.setDefaultTextColor(QColor("#FFFB8A"))
        self._label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self._update_label_text()

    def _update_label_text(self):
        fy = getattr(self.load, "fy", 0)
        fx = getattr(self.load, "fx", 0)
        lines = []
        if abs(fx) > 0.001:
            lines.append(f"Fx = {fx:+.2f} kN")
        if abs(fy) > 0.001:
            lines.append(f"Fy = {fy:+.2f} kN")
        self._label.setPlainText("\n".join(lines) if lines else "0 kN")

    def boundingRect(self) -> QRectF:
        return QRectF(-120, -240, 240, 360)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        fy = getattr(self.load, "fy", 0)
        length = self.ARROW_LENGTH
        head   = self.ARROW_HEAD

        color = QColor("#FF3A3A")
        painter.setPen(QPen(color, self.LINE_WIDTH, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(QBrush(color))

        # Direction de la flèche : elle POINTE vers le nœud (origin = 0,0)
        if fy <= 0:
            # Force vers le bas → flèche vient du haut, tête en bas
            start_y = -length
            end_y   = 0
            tip     = QPointF(0, end_y)
            left    = QPointF(-head / 2, end_y - head * 1.2)
            right   = QPointF( head / 2, end_y - head * 1.2)
            label_y = start_y - 30
        else:
            # Force vers le haut → flèche vient du bas, tête en haut
            start_y = length
            end_y   = 0
            tip     = QPointF(0, end_y)
            left    = QPointF(-head / 2, end_y + head * 1.2)
            right   = QPointF( head / 2, end_y + head * 1.2)
            label_y = start_y + 10

        # Tige
        painter.drawLine(QPointF(0, start_y), QPointF(0, end_y))

        # Tête de flèche (triangle rempli)
        painter.drawPolygon(QPolygonF([tip, left, right]))

        # Repositionner le label
        lw = self._label.boundingRect().width()
        self._label.setPos(-lw / 2 + 14, label_y)


# ════════════════════════════════════════════════════════════
# CHARGE PONCTUELLE SUR POUTRE (NOUVEAU)
# ════════════════════════════════════════════════════════════
class PointLoadOnBeamItem(QGraphicsItem):
    """
    Flèche représentant une charge ponctuelle à une position exacte sur une poutre.
    
    Cet item est positionné aux coordonnées absolues de la charge sur la poutre
    et s'oriente perpendiculairement à la poutre.
    """
    ARROW_LENGTH = 80     # longueur visible de la flèche
    ARROW_HEAD   = 12     # taille de la tête de flèche
    LINE_WIDTH   = 2.5
    CIRCLE_RADIUS = 6     # cercle marquant le point d'application

    def __init__(self, load):
        super().__init__()
        self.load = load
        self.setZValue(32)  # Au-dessus des autres éléments
        
        # Référence inverse pour la mise à jour
        load.graphics_item = self
        
        # Mettre à jour la position initiale
        self._update_position()
        
        # Label créé une seule fois
        self._label = QGraphicsTextItem(self)
        self._label.setDefaultTextColor(QColor("#FFD700"))  # Or pour différencier
        self._label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self._update_label_text()

    def _update_position(self):
        """Met à jour la position de l'item selon la position sur la poutre."""
        if self.load and self.load.beam:
            x, y = self.load.position
            self.setPos(x, y)
            
            # Calculer l'angle de la poutre pour l'orientation
            beam = self.load.beam
            dx = beam.node_end.x - beam.node_start.x
            dy = beam.node_end.y - beam.node_start.y
            angle = math.degrees(math.atan2(dy, dx))
            self._beam_angle = angle

    def _update_label_text(self):
        fy = getattr(self.load, "fy", 0)
        fx = getattr(self.load, "fx", 0)
        pos = getattr(self.load, "position_ratio", 0) * 100
        
        lines = [f"@{pos:.0f}%"]
        if abs(fx) > 0.001:
            lines.append(f"Fx={fx:+.1f}kN")
        if abs(fy) > 0.001:
            lines.append(f"Fy={fy:+.1f}kN")
        self._label.setPlainText("\n".join(lines))

    def boundingRect(self) -> QRectF:
        return QRectF(-100, -150, 200, 300)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Mettre à jour la position si la poutre a bougé
        self._update_position()

        fy = getattr(self.load, "fy", 0)
        length = self.ARROW_LENGTH
        head   = self.ARROW_HEAD

        # Couleur distinctive pour les charges sur poutre (orange/rouge vif)
        color = QColor("#FF6B35")
        painter.setPen(QPen(color, self.LINE_WIDTH, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(QBrush(color))

        # Cercle marquant le point d'application sur la poutre
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(QPointF(0, 0), self.CIRCLE_RADIUS, self.CIRCLE_RADIUS)
        painter.setBrush(QBrush(color))

        # Direction de la flèche
        if fy <= 0:
            # Force vers le bas
            start_y = -length
            end_y   = 0
            tip     = QPointF(0, end_y)
            left    = QPointF(-head / 2, end_y - head * 1.2)
            right   = QPointF( head / 2, end_y - head * 1.2)
            label_y = start_y - 35
        else:
            # Force vers le haut
            start_y = length
            end_y   = 0
            tip     = QPointF(0, end_y)
            left    = QPointF(-head / 2, end_y + head * 1.2)
            right   = QPointF( head / 2, end_y + head * 1.2)
            label_y = start_y + 15

        # Tige
        painter.drawLine(QPointF(0, start_y), QPointF(0, end_y))

        # Tête de flèche
        painter.drawPolygon(QPolygonF([tip, left, right]))

        # Repositionner le label
        lw = self._label.boundingRect().width()
        self._label.setPos(-lw / 2, label_y)


# ════════════════════════════════════════════════════════════
# CHARGE RÉPARTIE
# ════════════════════════════════════════════════════════════
class DistributedLoadItem(QGraphicsItem):
    """
    Charge répartie — flèches identiques aux charges ponctuelles sur poutre :
      • même couleur (#FF6B35)
      • même tête de flèche triangulaire pleine
      • ligne de base horizontale reliant les queues de flèches
      • densité élevée (1 flèche tous les ~25 px)
    """

    ARROW_LENGTH  = 80     # hauteur de chaque flèche (identique à PointLoadOnBeamItem)
    ARROW_HEAD    = 12     # taille tête (identique)
    LINE_WIDTH    = 2.5    # épaisseur trait
    COLOR         = QColor("#FF6B35")   # même couleur que PointLoadOnBeamItem
    LABEL_COLOR   = QColor("#FFD700")

    def __init__(self, load):
        super().__init__()
        self.load = load
        self.setZValue(26)

        # Couleur initiale selon type
        load_type = getattr(load, "load_type", "G")
        if load_type == "Q":
            label_color = QColor("#FF9800")
        elif load_type == "G+Q":
            label_color = QColor("#AA44FF")
        else:
            label_color = self.LABEL_COLOR

        self._label = QGraphicsTextItem(self)
        self._label.setDefaultTextColor(label_color)
        self._label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        w = getattr(load, "w", 0)
        type_tag = f"[{load_type}] " if load_type != "G" else ""
        self._label.setPlainText(f"{type_tag}w = {w:+.2f} kN/m")

    def boundingRect(self) -> QRectF:
        return QRectF(-3000, -3000, 6000, 6000)

    def paint(self, painter: QPainter, option, widget=None):
        beam = getattr(self.load, "member", None) or getattr(self.load, "beam", None)
        if not beam:
            return

        ns, ne = beam.node_start, beam.node_end
        dx_beam = ne.x - ns.x
        dy_beam = ne.y - ns.y
        beam_len = math.hypot(dx_beam, dy_beam)
        if beam_len < 15:
            return

        # Couleur selon le type de charge
        load_type = getattr(self.load, "load_type", "G")
        if load_type == "Q":
            draw_color = QColor("#FF9800")   # orange = variable/dynamique
        elif load_type == "G+Q":
            draw_color = QColor("#AA44FF")   # violet = superposition
        else:
            draw_color = self.COLOR          # rouge = permanente (défaut)

        ux, uy = dx_beam / beam_len, dy_beam / beam_len
        px, py = -uy, ux

        sign = 1 if self.load.w <= 0 else -1

        arrow_len = self.ARROW_LENGTH
        head      = self.ARROW_HEAD
        hw        = head * 0.6

        sp = getattr(self.load, "start_pos", 0.0)
        ep = getattr(self.load, "end_pos",   1.0)
        ax = ns.x + sp * dx_beam
        ay = ns.y + sp * dy_beam
        bx = ns.x + ep * dx_beam
        by = ns.y + ep * dy_beam
        zone_len = beam_len * (ep - sp)

        n_arrows = max(3, int(zone_len / 25))

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(draw_color, self.LINE_WIDTH, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QBrush(draw_color))

        arrow_positions = []

        for i in range(n_arrows + 1):
            t = i / n_arrows
            tip_x = ax + t * (bx - ax)
            tip_y = ay + t * (by - ay)
            tail_x = tip_x + px * arrow_len * sign
            tail_y = tip_y + py * arrow_len * sign
            arrow_positions.append((tail_x, tail_y))

            painter.drawLine(QPointF(tail_x, tail_y), QPointF(tip_x, tip_y))

            fdx = tip_x - tail_x
            fdy = tip_y - tail_y
            flen = math.hypot(fdx, fdy)
            if flen < 1e-6:
                continue
            fux, fuy = fdx / flen, fdy / flen
            fpx, fpy = -fuy, fux

            base_x = tip_x - fux * head
            base_y = tip_y - fuy * head
            left_x  = base_x + fpx * hw;  left_y  = base_y + fpy * hw
            right_x = base_x - fpx * hw;  right_y = base_y - fpy * hw

            tri = QPainterPath()
            tri.moveTo(tip_x, tip_y); tri.lineTo(left_x, left_y)
            tri.lineTo(right_x, right_y); tri.closeSubpath()
            painter.drawPath(tri)

        if len(arrow_positions) >= 2:
            base_path = QPainterPath()
            base_path.moveTo(arrow_positions[0][0], arrow_positions[0][1])
            for (qx, qy) in arrow_positions[1:]:
                base_path.lineTo(qx, qy)
            painter.setPen(QPen(draw_color, self.LINE_WIDTH + 0.5, Qt.SolidLine, Qt.RoundCap))
            painter.drawPath(base_path)

        # Mise à jour du label avec type + valeur
        w = self.load.w
        type_tag = f"[{load_type}] " if load_type != "G" else ""
        self._label.setPlainText(f"{type_tag}w = {w:+.2f} kN/m")
        self._label.setDefaultTextColor(draw_color)

        mid_t = 0.5
        mid_beam_x = ax + mid_t * (bx - ax)
        mid_beam_y = ay + mid_t * (by - ay)
        lbl_x = mid_beam_x + px * (arrow_len + 18) * sign
        lbl_y = mid_beam_y + py * (arrow_len + 18) * sign
        lw = self._label.boundingRect().width()
        lh = self._label.boundingRect().height()
        self._label.setPos(lbl_x - lw / 2, lbl_y - lh / 2)