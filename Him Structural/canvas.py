# canvas.py
"""
Canvas principal QGraphicsView — dessin et interaction avec la structure.

AMÉLIORATIONS :
  - Sélection visuelle plus claire (highlight + tooltip de coordonnées)
  - Pan (déplacement de la vue) avec clic molette ou clic droit maintenu
  - Undo/Redo fonctionnel
  - Aperçu de poutre en cours de création
  - Support des charges ponctuelles sur poutres (position exacte)
  - Confirmation avant suppression
"""

from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem,
    QGraphicsItem, QRubberBand, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QPointF, QRectF, QSize, QRect
from PySide6.QtGui import (
    QPen, QColor, QPainter, QPainterPath, QRadialGradient, QFont, QCursor
)
import math
from ui.load_items import PointLoadItem, PointLoadOnBeamItem, DistributedLoadItem
from section_manager import SectionLibrary
from structural_model import (
    StructuralModel, Node, Beam, PointLoad, DistributedLoad
)
import numpy as np
from ui.diagram_items import BMDItem, SFDItem


# ════════════════════════════════════════════════════════════
# ITEM NŒUD + SYMBOLES D'APPUI
# ════════════════════════════════════════════════════════════
class NodeItem(QGraphicsEllipseItem):
    RADIUS = 5.0

    def __init__(self, node: Node):
        r = self.RADIUS
        super().__init__(-r, -r, 2 * r, 2 * r)
        self.node = node
        self.main_window = None
        self.setPos(node.x, node.y)
        self.setToolTip(f"Nœud {node.id}\n({node.x:.1f}, {node.y:.1f})")

        self._apply_style(selected=False)
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsEllipseItem.ItemSendsGeometryChanges, True)
        self.setZValue(10)

        node.graphics_item = self
        self.support_symbol = None

    def _apply_style(self, selected: bool):
        if selected:
            self.setBrush(QColor("#ffffff"))
            self.setPen(QPen(QColor("#FF9800"), 0.8))
            self.setScale(1.25)
        else:
            self.setBrush(QColor("#67e8f9"))
            self.setPen(QPen(QColor("#1e3a8a"), 1))
            self.setScale(1.0)

    def set_selected(self, selected: bool):
        self._apply_style(selected)

    def create_support_symbol(self, scene):
        """Crée le symbole une fois que le nœud est dans la scène"""
        if self.support_symbol is None:
            self.support_symbol = SupportSymbolItem(self.node)
            scene.addItem(self.support_symbol)

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.ItemPositionHasChanged:
            self.node.x = self.pos().x()
            self.node.y = self.pos().y()
            self.setToolTip(f"Nœud {self.node.id}\n({self.node.x:.1f}, {self.node.y:.1f})")
            
            if self.support_symbol:
                self.support_symbol.setPos(self.node.x, self.node.y)

            # Mettre à jour les charges ponctuelles sur ce nœud
            for load in getattr(self.node, "point_loads", []):
                if hasattr(load, "graphics_item") and load.graphics_item:
                    load.graphics_item.setPos(self.node.x, self.node.y)
            
            # Mettre à jour les poutres connectées
            for beam in getattr(self.node, "connected_beams", []):
                gi = getattr(beam, "graphics_item", None)
                if gi:
                    gi.update_position()
                
                # Mettre à jour les charges sur cette poutre
                for load in getattr(beam, "point_loads_on_beam", []):
                    if hasattr(load, "graphics_item") and load.graphics_item:
                        load.graphics_item._update_position()
                        load.graphics_item.update()
                        
                for load in getattr(beam, "distributed_loads", []):
                    if hasattr(load, "graphics_item") and load.graphics_item:
                        load.graphics_item.update()
                        
        return super().itemChange(change, value)

    def update_support_symbol(self):
        if self.support_symbol:
            self.support_symbol.update_symbol()


# ════════════════════════════════════════════════════════════
# SYMBOLE D'APPUI (vectoriel)
# ════════════════════════════════════════════════════════════
class SupportSymbolItem(QGraphicsItem):
    def __init__(self, node: Node):
        super().__init__()
        self.node = node
        self.setPos(node.x, node.y)
        self.setZValue(9)

    def boundingRect(self):
        return QRectF(-40, -5, 80, 70)

    def update_symbol(self):
        self.prepareGeometryChange()
        self.update()

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing, True)
        s = self.node.supports

        pen_support = QPen(QColor("#4fc3f7"), 3.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        brush_support = QColor("#1e3a8a")

        if not s.get("dx") and not s.get("dy") and not s.get("rz"):          # Libre
            pass
        elif s.get("dx") and s.get("dy") and not s.get("rz"):                 # Articulé
            painter.setPen(pen_support)
            painter.setBrush(brush_support)

            # triangle classique
            path = QPainterPath()
            path.moveTo(-22, 25)
            path.lineTo(0, 7)
            path.lineTo(22, 25)
            path.closeSubpath()
            painter.drawPath(path)

            painter.drawLine(-25, 25, 25, 25)
            painter.setPen(QPen(QColor("#60a5fa"), 1.8))
            for x in range(-21, 24, 7):
                painter.drawLine(x, 26, x-6, 36)

        elif s.get("dy") and not s.get("dx") and not s.get("rz"):             # Roulant
            painter.setPen(pen_support)
            painter.setBrush(brush_support)

            # Triangle
            path = QPainterPath()
            path.moveTo(-20, 23)
            path.lineTo(0, 8)
            path.lineTo(20, 23)
            path.closeSubpath()
            painter.drawPath(path)

            # Ligne de roulement
            painter.drawLine(-24, 23, 24, 23)

            # Rouleaux
            painter.setBrush(QColor("#bae6fd"))
            painter.setPen(QPen(QColor("#0284c8"), 2.2))
            for x in [-14, 0, 14]:
                painter.drawEllipse(QPointF(x, 29), 5.5, 5.5)

        else:  # Encastrement
            wall_on_left = True
            for beam in getattr(self.node, 'connected_beams', []):
                if beam.node_start is self.node:
                    other_x = beam.node_end.x
                else:
                    other_x = beam.node_start.x

                if abs(other_x - self.node.x) > 10:
                    wall_on_left = (other_x > self.node.x)
                    break

            wall_w = 20
            wall_h = 100
            wall_y = -50

            if wall_on_left:
                wall_x = -20
            else:
                wall_x = 0

            # Rectangle rouge (mur)
            painter.setPen(QPen(QColor("#ef4444"), 4.5))
            painter.setBrush(QColor("#b91c1c"))
            painter.drawRect(QRectF(wall_x, wall_y, wall_w, wall_h))

        # ID du nœud
        painter.setPen(QColor("#bae6fd"))
        painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
        painter.drawText(QRectF(-35, 44, 70, 18), Qt.AlignCenter, self.node.id)


# ════════════════════════════════════════════════════════════
# ITEM POUTRE
# ════════════════════════════════════════════════════════════
class BeamItem(QGraphicsLineItem):
    def __init__(self, beam: Beam):
        super().__init__()
        self.beam = beam
        beam.graphics_item = self
        self._selected = False
        self._apply_style(selected=False)
        self.setFlag(QGraphicsLineItem.ItemIsSelectable, True)
        self.setZValue(2)
        self.update_position()

    def _apply_style(self, selected: bool):
        if selected:
            self.setPen(QPen(QColor("#FF9800"), 3.5, Qt.SolidLine, Qt.RoundCap))
            self.setZValue(10)
        else:
            self.setPen(QPen(QColor("#fcd34d"), 2.8, Qt.SolidLine, Qt.RoundCap))
            self.setZValue(2)

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_style(selected)
        sec = getattr(self.beam, "section_name", "?")
        mat = getattr(self.beam, "material", "?")
        L   = self.beam.length
        
        # Compter les charges sur cette poutre
        n_point_loads = len(getattr(self.beam, 'point_loads_on_beam', []))
        n_dist_loads = len(getattr(self.beam, 'distributed_loads', []))
        
        tooltip = (
            f"Poutre {self.beam.id}\n"
            f"Section : {sec}  |  Matériau : {mat}\n"
            f"Longueur : {L:.1f} mm\n"
            f"Charges ponctuelles : {n_point_loads}\n"
            f"Charges réparties : {n_dist_loads}"
        )
        self.setToolTip(tooltip)

    def update_position(self):
        self.setLine(
            self.beam.node_start.x, self.beam.node_start.y,
            self.beam.node_end.x,   self.beam.node_end.y,
        )


# ════════════════════════════════════════════════════════════
# CANVAS PRINCIPAL
# ════════════════════════════════════════════════════════════
class GraphicsCanvas(QGraphicsView):
    mouse_moved   = Signal(float, float)
    node_selected = Signal(object)
    beam_selected = Signal(object)

    def __init__(self, model: StructuralModel):
        super().__init__()
        self.model = model
        self.section_library = SectionLibrary()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        # Apparence
        self.setBackgroundBrush(QColor("#18181b"))
        self.grid_size   = 40
        self.show_grid   = True
        self.snap_to_grid = True
        self.show_axes   = True

        # État interaction
        self.mode = "select"
        self.temp_start = None
        self.active_section_name = "default"
        self.zoom_factor = 1.22
        self.undo_stack: list = []
        self.redo_stack: list = []

        # Pan avec clic droit / molette pressée
        self._panning = False
        self._pan_start = QPointF()
        self.rubberband = QRubberBand(QRubberBand.Rectangle, self)
        self.rubberband.setStyleSheet("""
            QRubberBand {
                border: 1px dashed #60a5fa;
                background-color: rgba(96, 165, 250, 40);
            }
         """)
        
        self.rubberband.hide()
        self.rubber_start = None

        self._rebuild_scene()

    def set_mode(self, mode: str):
        """Change l'outil actif."""
        self.mode = mode
        self.temp_start = None
        cursor_map = {
            "node":  Qt.CrossCursor,
            "beam":  Qt.CrossCursor,
        }
        self.viewport().setCursor(cursor_map.get(mode, Qt.ArrowCursor))

    def add_point_load_visual(self, load: PointLoad):
        """Ajoute l'affichage visuel d'une charge ponctuelle sur nœud."""
        item = PointLoadItem(load)
        self.scene.addItem(item)
        self.scene.update()

    def add_point_load_on_beam_visual(self, load):
        """Ajoute l'affichage visuel d'une charge ponctuelle sur poutre."""
        item = PointLoadOnBeamItem(load)
        self.scene.addItem(item)
        self.scene.update()

    def add_distributed_load_visual(self, load: DistributedLoad):
        """Ajoute l'affichage visuel d'une charge répartie."""
        item = DistributedLoadItem(load)
        self.scene.addItem(item)
        self.scene.update()

    def select_item(self, item):
        """Désélectionne tout, puis sélectionne 'item' si non None."""
        for beam in self.model.beams:
            gi = getattr(beam, "graphics_item", None)
            if gi:
                gi.set_selected(False)
        for node in self.model.nodes:
            gi = getattr(node, "graphics_item", None)
            if gi:
                gi.set_selected(False)
        if item:
            item.set_selected(True)

    def wheelEvent(self, event):
        if event.angleDelta().y() == 0:
            return
        factor = self.zoom_factor if event.angleDelta().y() > 0 else 1 / self.zoom_factor
        self.scale(factor, factor)

    def _snap(self, value: float) -> float:
        if not self.snap_to_grid:
            return value
        return round(value / self.grid_size) * self.grid_size

    def _scene_pos_snapped(self, event) -> QPointF:
        pos = self.mapToScene(event.pos())
        return QPointF(self._snap(pos.x()), self._snap(pos.y()))

    def mousePressEvent(self, event):
        # pan avec molette pressée
        if event.button() in (Qt.MiddleButton, Qt.RightButton):
            self._panning = True
            self._pan_start = event.pos()
            self.viewport().setCursor(Qt.ClosedHandCursor)
            return
        
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return

        # Selection par rectangle en mode selection
        if self.mode == "select":
            item = self.itemAt(event.pos())

            if isinstance(item, NodeItem):
                self.select_item(item)
                self.node_selected.emit(item.node)
                super().mousePressEvent(event)
                return
            elif isinstance(item, BeamItem):
                self.select_item(item)
                self.beam_selected.emit(item.beam)
                super().mousePressEvent(event)
                return
            
            # Sinon clic dans le vide → démarrer le rectangle de selection
            self.rubber_start = event.pos()
            self.rubberband.setGeometry(QRect(self.rubber_start, QSize()))
            self.rubberband.show()
            return

        # Modes creation(node, beam)
        pos = self._scene_pos_snapped(event)
        x, y = pos.x(), pos.y()
        
        if self.mode == "node":
            node = self._get_or_create_node(x, y)
            self._push_undo()
            self.node_selected.emit(node)

        elif self.mode == "beam":
            if self.temp_start is None:
                self.temp_start = (x, y)
            else:
                start_node = self._get_or_create_node(*self.temp_start)
                end_node   = self._get_or_create_node(x, y)
                if start_node is end_node:
                    self.temp_start = None
                    return
                beam = self.model.add_beam(
                    start_node, end_node,
                    section_name=self.active_section_name or "default",
                )
                item = BeamItem(beam)
                self.scene.addItem(item)
                self.beam_selected.emit(beam)
                self.temp_start = None
                self._push_undo()

                self.set_mode("select")
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Pan actif
        if self._panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            return
        
        if self.rubber_start is not None:
            rect = QRect(self.rubber_start, event.pos()).normalized()
            self.rubberband.setGeometry(rect)

        pos = self.mapToScene(event.pos())
        self.mouse_moved.emit(pos.x(), pos.y())

        if self.mode == "beam" and self.temp_start:
            self.scene.invalidate(QRectF(), QGraphicsScene.AllLayers)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() in (Qt.MiddleButton, Qt.RightButton) and self._panning:
            self._panning = False
            self.viewport().setCursor(Qt.ArrowCursor)
            return
        
        if event.button() == Qt.LeftButton and self.rubber_start is not None:
            self._perform_rubber_band_selection()
            self.rubberband.hide()
            self.rubber_start = None
            return
        
        super().mouseReleaseEvent(event)

    def _perform_rubber_band_selection(self):
        if not self.rubber_start:
            return

        view_rect = self.rubberband.geometry()
        scene_rect = QRectF(
            self.mapToScene(view_rect.topLeft()),
            self.mapToScene(view_rect.bottomRight())    
        ).normalized()

        self.select_item(None)

        for item in self.scene.items(scene_rect, Qt.IntersectsItemShape):
            if isinstance(item, NodeItem):
                item.set_selected(True)
                self.node_selected.emit(item.node)
            elif isinstance(item, BeamItem):
                item.set_selected(True)
                self.beam_selected.emit(item.beam)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.temp_start = None
            self.scene.invalidate()
        elif event.key() == Qt.Key_Delete:
            self._delete_selected_with_confirmation()
        super().keyPressEvent(event)

    def _delete_selected_with_confirmation(self):
        """Supprime l'élément sélectionné avec confirmation."""
        selected_items = [item for item in self.scene.selectedItems() 
                         if isinstance(item, (BeamItem, NodeItem))]
        
        if not selected_items:
            # Vérifier aussi les items non sélectionnés mais avec highlight
            for item in self.scene.items():
                if isinstance(item, BeamItem) and item._selected:
                    selected_items.append(item)
                elif isinstance(item, NodeItem):
                    # Vérifier si le nœud est "sélectionné" visuellement
                    pass
        
        if not selected_items:
            return
            
        # Demander confirmation
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Supprimer {len(selected_items)} élément(s) sélectionné(s) ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        self._delete_selected()

    def _delete_selected(self):
        """Supprime l'élément graphique sélectionné (nœud ou poutre)."""
        deleted = False
        beams_to_delete = []
        nodes_to_check = set()

        for item in list(self.scene.items()):
            if isinstance(item, BeamItem) and (item._selected or item.isSelected()):
                b = item.beam
                beams_to_delete.append(b)
                nodes_to_check.add(b.node_start)
                nodes_to_check.add(b.node_end)

                # Supprimer toutes les charges ponctuelles sur la poutre
                for load in list(getattr(b, 'point_loads_on_beam', [])):
                    gi = getattr(load, 'graphics_item', None)
                    if gi is not None:
                        try:
                            self.scene.removeItem(gi)
                        except Exception:
                            pass
                        load.graphics_item = None
                    if load in self.model.point_loads_on_beams:
                        self.model.point_loads_on_beams.remove(load)
                b.point_loads_on_beam.clear()

                # Supprimer toutes les charges réparties sur la poutre
                for load in list(getattr(b, 'distributed_loads', [])):
                    gi = getattr(load, 'graphics_item', None)
                    if gi is not None:
                        try:
                            self.scene.removeItem(gi)
                        except Exception:
                            pass
                        load.graphics_item = None
                    if load in self.model.distributed_loads:
                        self.model.distributed_loads.remove(load)
                b.distributed_loads.clear()

                if b in self.model.beams:
                    self.model.beams.remove(b)
                
                # Déconnecter les nœuds
                for n in (b.node_start, b.node_end):
                    if b in getattr(n, 'connected_beams', []):
                        n.connected_beams.remove(b)
                    if b in getattr(n, 'connected_columns', []):
                        n.connected_columns.remove(b)

                if b.graphics_item:
                    self.scene.removeItem(b.graphics_item)

                self.beam_selected.emit(None)
                deleted = True

        for node in list(nodes_to_check):

            if (len(getattr(node, 'connected_beams', [])) == 0 and
                len(getattr(node, 'connected_columns', [])) == 0):

                for load in list(getattr(node, 'point_loads', [])):
                    if load in self.model.point_loads:
                        self.model.point_loads.remove(load)
                    if hasattr(load, 'graphics_item') and load.graphics_item:
                        self.scene.removeItem(load.graphics_item)
                node.point_loads.clear()

                if node.graphics_item:
                    if node.graphics_item.support_symbol:
                        self.scene.removeItem(node.graphics_item.support_symbol)
                        node.graphics_item.support_symbol = None

                if node.graphics_item:
                    self.scene.removeItem(node.graphics_item)
                    node.graphics_item = None


                if node in self.model.nodes:
                    self.model.nodes.remove(node)

                deleted = True

        if deleted:
            self.scene.update()
            self.viewport().update()
            print("🗑️ Poutre(s) et éléments associés supprimés", "success")

            if hasattr(self, 'main_window') and hasattr(self.main_window, "show_status_message"):
                self.main_window.show_status_message(
                    "🗑️ Poutre et éléments associés supprimés", "success", 3500
                )


    def _get_or_create_node(self, x: float, y: float) -> Node:
        SNAP_TOL = 14
        for node in self.model.nodes:
            if math.hypot(node.x - x, node.y - y) < SNAP_TOL:
                return node
        node = self.model.add_node(x, y)
        item = NodeItem(node)
        self.scene.addItem(item)
        item.create_support_symbol(self.scene)
        return node

    def _push_undo(self):
        self.undo_stack.append(self.model.to_dict())
        self.redo_stack.clear()
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack:
            return
        self.redo_stack.append(self.model.to_dict())
        data = self.undo_stack.pop()
        self.model = StructuralModel.from_dict(data)
        self.scene.clear()
        self._rebuild_scene()

    def redo(self):
        if not self.redo_stack:
            return
        self.undo_stack.append(self.model.to_dict())
        data = self.redo_stack.pop()
        self.model = StructuralModel.from_dict(data)
        self.scene.clear()
        self._rebuild_scene()

    def _rebuild_scene(self):
        """Recrée tous les items graphiques à partir du modèle de données."""
        for node in self.model.nodes:
            item = NodeItem(node)
            self.scene.addItem(item)
            item.create_support_symbol(self.scene)

        for beam in self.model.beams:
            item = BeamItem(beam)
            self.scene.addItem(item)

        for col in self.model.columns:
            item = BeamItem(col)
            self.scene.addItem(item)

        for load in self.model.point_loads:
            self.add_point_load_visual(load)

        # NOUVEAU: Charges ponctuelles sur poutres
        for load in self.model.point_loads_on_beams:
            self.add_point_load_on_beam_visual(load)

        for load in self.model.distributed_loads:
            self.add_distributed_load_visual(load)

    def drawBackground(self, painter: QPainter, rect: QRectF):
        super().drawBackground(painter, rect)
        if self.show_grid:
            self._draw_grid(painter, rect)
        if self.mode == "beam" and self.temp_start:
            self._draw_beam_preview(painter)

    def _draw_grid(self, painter: QPainter, rect: QRectF):
        step = self.grid_size
        left   = math.floor(rect.left()   / step) * step
        right  = math.ceil (rect.right()  / step) * step
        top    = math.floor(rect.top()    / step) * step
        bottom = math.ceil (rect.bottom() / step) * step

        painter.setPen(QPen(QColor("#24242e"), 1))
        for x in range(int(left), int(right) + step, step):
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
        for y in range(int(top), int(bottom) + step, step):
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)

    def _draw_beam_preview(self, painter: QPainter):
        end = self.mapToScene(self.viewport().mapFromGlobal(QCursor.pos()))
        end = QPointF(self._snap(end.x()), self._snap(end.y()))
        pen = QPen(QColor("#4fc3f7"), 3.5, Qt.DashLine)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.drawLine(QPointF(*self.temp_start), end)
        painter.setBrush(QColor(100, 180, 255, 200))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(*self.temp_start), 7, 7)

    def draw_analysis_diagrams(self, results_dict):
        # Nettoyer les anciens diagrammes
        for item in list(self.scene.items()):
            if isinstance(item, (BMDItem, SFDItem)):
                self.scene.removeItem(item)

        settings = getattr(self, 'diagram_settings', {})
        show_bmd = settings.get("show_bmd", True)
        show_sfd = settings.get("show_sfd", True)

        for beam in self.model.beams:
            if beam.id in results_dict:
                res = results_dict[beam.id]
                if show_bmd:
                    self.scene.addItem(BMDItem(beam, res, settings))
                if show_sfd:
                    self.scene.addItem(SFDItem(beam, res, settings))

        self.scene.update()
        self.viewport().update()

    def save_to_file(self, filename: str):
        import json
        data = self.model.to_dict()
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, filename: str):
        import json
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.model = StructuralModel.from_dict(data)
        self.scene.clear()
        self._rebuild_scene()