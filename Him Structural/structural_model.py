# structural_model.py
"""
Modèle structural central - Version améliorée avec charges ponctuelles sur poutres

AMÉLIORATIONS :
  1. Nouvelle classe PointLoadOnBeam pour les charges à position exacte sur poutre
  2. Gestion robuste des IDs uniques
  3. Validation des données à la création
  4. Support complet des charges réparties partielles
"""

from typing import List, Dict, Optional, Tuple, Union
import uuid
import math


class Node:
    """Nœud de la structure"""
    _counter = 0

    def __init__(self, x: float, y: float, id: Optional[str] = None):
        self.x = float(x)
        self.y = float(y)
        self.id = id if id is not None else f"N{Node._counter:04d}"
        Node._counter += 1

        self.point_loads: List["PointLoad"] = []
        self.connected_beams: List["Beam"] = []
        self.connected_columns: List["Column"] = []
        self.supports: Dict[str, bool] = {"dx": False, "dy": False, "rz": False}
        self.graphics_item = None

    @property
    def position(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def add_point_load(self, load: "PointLoad"):
        """Ajoute une charge ponctuelle au nœud."""
        if load not in self.point_loads:
            self.point_loads.append(load)

    def remove_point_load(self, load: "PointLoad"):
        """Supprime une charge ponctuelle du nœud."""
        if load in self.point_loads:
            self.point_loads.remove(load)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "supports": self.supports.copy(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Node":
        node = cls(d["x"], d["y"], id=d.get("id"))
        node.supports = d.get("supports", {"dx": False, "dy": False, "rz": False})
        return node


class Line:
    """Ligne auxiliaire (non structurale)"""
    def __init__(self, p1: Tuple[float, float], p2: Tuple[float, float]):
        self.p1 = p1
        self.p2 = p2
        self.id = f"L{uuid.uuid4().hex[:6]}"

    def length(self) -> float:
        return math.hypot(self.p2[0] - self.p1[0], self.p2[1] - self.p1[1])

    def to_dict(self) -> dict:
        return {"p1": list(self.p1), "p2": list(self.p2), "id": self.id}

    @classmethod
    def from_dict(cls, d: dict) -> "Line":
        return cls(tuple(d["p1"]), tuple(d["p2"]))


class Beam:
    """Élément de type poutre (horizontale ou inclinée)"""
    def __init__(self, node_start: Node, node_end: Node, section_name: str = "default"):
        self.node_start = node_start
        self.node_end = node_end
        self.section_name = section_name
        self.distributed_loads: List["DistributedLoad"] = []
        self.point_loads_on_beam: List["PointLoadOnBeam"] = []  # NOUVEAU
        self.id = f"B{uuid.uuid4().hex[:6]}"
        self.material = "Steel"
        self.concrete_grade: str = "C30"

        node_start.connected_beams.append(self)
        node_end.connected_beams.append(self)
        self.graphics_item = None

    @property
    def length(self) -> float:
        return math.hypot(
            self.node_end.x - self.node_start.x,
            self.node_end.y - self.node_start.y
        )

    def add_point_load_on_beam(self, load: "PointLoadOnBeam"):
        """Ajoute une charge ponctuelle sur la poutre."""
        if load not in self.point_loads_on_beam:
            self.point_loads_on_beam.append(load)

    def remove_point_load_on_beam(self, load: "PointLoadOnBeam"):
        """Supprime une charge ponctuelle de la poutre."""
        if load in self.point_loads_on_beam:
            self.point_loads_on_beam.remove(load)

    def get_position_at(self, ratio: float) -> Tuple[float, float]:
        """Retourne les coordonnées à une position relative sur la poutre (0-1)."""
        ratio = max(0.0, min(1.0, ratio))  # Clamper entre 0 et 1
        x = self.node_start.x + ratio * (self.node_end.x - self.node_start.x)
        y = self.node_start.y + ratio * (self.node_end.y - self.node_start.y)
        return (x, y)

    def to_dict(self, node_index_map: Dict[str, int]) -> dict:
        return {
            "id": self.id,
            "start_node": node_index_map[self.node_start.id],
            "end_node": node_index_map[self.node_end.id],
            "section_name": self.section_name,
            "material": self.material,
            "concrete_grade": getattr(self, "concrete_grade", "C30"),
        }

    @classmethod
    def from_dict(cls, d: dict, nodes_by_index: List[Node]) -> "Beam":
        beam = cls(
            nodes_by_index[d["start_node"]],
            nodes_by_index[d["end_node"]],
            section_name=d.get("section_name", "default"),
        )
        beam.id = d.get("id", beam.id)
        beam.material = d.get("material", "Steel")
        beam.concrete_grade = d.get("concrete_grade", "C30")
        return beam


class Column(Beam):
    """Poteau (héritage de Beam)"""
    def __init__(self, node_start: Node, node_end: Node, section_name: str = "default"):
        super().__init__(node_start, node_end, section_name)
        self.id = f"C{uuid.uuid4().hex[:6]}"


class PointLoad:
    """Charge ponctuelle appliquée sur un nœud."""
    def __init__(self, node: Node, fx: float = 0.0, fy: float = 0.0):
        self.node = node
        self.fx = float(fx)
        self.fy = float(fy)
        node.add_point_load(self)

    def to_dict(self) -> dict:
        return {"node_id": self.node.id, "fx": self.fx, "fy": self.fy}


class PointLoadOnBeam:
    """
    Charge ponctuelle appliquée à une position exacte sur une poutre.
    
    AMÉLIORATION MAJEURE: Permet de placer une charge à n'importe quelle
    position sur la poutre, pas seulement aux nœuds.
    
    Args:
        beam: La poutre sur laquelle appliquer la charge
        position_ratio: Position relative sur la poutre (0.0 = début, 1.0 = fin)
        fx: Composante horizontale de la force (kN)
        fy: Composante verticale de la force (kN)
    """
    def __init__(self, beam: Beam, position_ratio: float, fx: float = 0.0, fy: float = 0.0,
                 load_type: str = "G"):
        self.beam = beam
        self.position_ratio = float(max(0.0, min(1.0, position_ratio)))  # Clamper 0-1
        self.fx = float(fx)
        self.fy = float(fy)
        self.id = f"PLB{uuid.uuid4().hex[:6]}"
        self.load_type = load_type  # "G" = Permanente, "Q" = Variable/Dynamique
        
        # Ajouter à la poutre
        beam.add_point_load_on_beam(self)
        
        # Référence graphique
        self.graphics_item = None

    @property
    def position(self) -> Tuple[float, float]:
        """Retourne les coordonnées absolues de la charge sur la poutre."""
        return self.beam.get_position_at(self.position_ratio)

    @property
    def distance_from_start(self) -> float:
        """Distance depuis le début de la poutre (mm)."""
        return self.position_ratio * self.beam.length

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "beam_id": self.beam.id,
            "position_ratio": self.position_ratio,
            "fx": self.fx,
            "fy": self.fy,
            "load_type": getattr(self, "load_type", "G"),
        }


class DistributedLoad:
    """Charge répartie sur une poutre ou un poteau."""

    def __init__(self, member: Union[Beam, Column], w: float,
                 start_pos: float = 0.0, end_pos: float = 1.0, load_type: str = "G"):
        self.member = member
        self.w = float(w)
        self.start_pos = float(max(0.0, min(1.0, start_pos)))
        self.end_pos = float(max(0.0, min(1.0, end_pos)))
        self.load_type = load_type  # "G" = Permanente, "Q" = Variable, "G+Q" = Superposée
        
        # S'assurer que start < end
        if self.start_pos > self.end_pos:
            self.start_pos, self.end_pos = self.end_pos, self.start_pos
            
        self.id = f"DL{uuid.uuid4().hex[:6]}"
        self.graphics_item = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "member_id": self.member.id,
            "w": self.w,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "load_type": getattr(self, "load_type", "G"),
        }


class StructuralModel:
    """Modèle structural complet."""
    
    def __init__(self):
        self.nodes: List[Node] = []
        self.lines: List[Line] = []
        self.beams: List[Beam] = []
        self.columns: List[Column] = []
        self.point_loads: List[PointLoad] = []
        self.point_loads_on_beams: List[PointLoadOnBeam] = []  # NOUVEAU
        self.distributed_loads: List[DistributedLoad] = []
        self.section_library = None

    def set_section_library(self, library):
        self.section_library = library

    def add_node(self, x: float, y: float) -> Node:
        node = Node(x, y)
        self.nodes.append(node)
        return node

    def add_beam(self, start: Node, end: Node, section_name: str = "default") -> Beam:
        beam = Beam(start, end, section_name=section_name)
        self.beams.append(beam)
        return beam

    def add_column(self, start: Node, end: Node, section_name: str = "default") -> Column:
        column = Column(start, end, section_name)
        self.columns.append(column)
        return column

    def add_point_load(self, node: Node, fx: float = 0, fy: float = 0) -> PointLoad:
        load = PointLoad(node, fx, fy)
        self.point_loads.append(load)
        return load

    def add_point_load_on_beam(self, beam: Beam, position_ratio: float, 
                                fx: float = 0, fy: float = 0) -> PointLoadOnBeam:
        """
        Ajoute une charge ponctuelle à une position exacte sur une poutre.
        
        Args:
            beam: La poutre cible
            position_ratio: Position relative (0.0 = début, 1.0 = fin)
            fx: Force horizontale en kN
            fy: Force verticale en kN
            
        Returns:
            L'objet PointLoadOnBeam créé
        """
        load = PointLoadOnBeam(beam, position_ratio, fx, fy)
        self.point_loads_on_beams.append(load)
        return load

    def add_distributed_load(self, member: Union[Beam, Column],
                              w: float, start_pos: float = 0.0,
                              end_pos: float = 1.0) -> DistributedLoad:
        load = DistributedLoad(member, w, start_pos, end_pos)
        self.distributed_loads.append(load)
        return load

    def remove_point_load_on_beam(self, load: PointLoadOnBeam):
        """Supprime une charge ponctuelle sur poutre."""
        if load.beam:
            load.beam.remove_point_load_on_beam(load)
        if load in self.point_loads_on_beams:
            self.point_loads_on_beams.remove(load)

    def validate_for_analysis(self) -> Tuple[bool, str]:
        """
        Valide que le modèle est prêt pour l'analyse.
        
        Returns:
            Tuple (est_valide, message_erreur)
        """
        if not self.nodes:
            return False, "Aucun nœud défini. Créez d'abord des nœuds."
            
        if not self.beams and not self.columns:
            return False, "Aucun élément structural (poutre/poteau) défini."
        
        # Vérifier les appuis
        has_support = any(
            n.supports.get("dx") or n.supports.get("dy") or n.supports.get("rz")
            for n in self.nodes
        )
        if not has_support:
            return False, "Aucun appui défini. Définissez au moins un appui."
        
        # Vérifier les éléments sans section
        beams_no_section = [b for b in self.beams if not getattr(b, 'section_name', None)]
        if beams_no_section:
            return False, f"{len(beams_no_section)} poutre(s) sans section définie."
        
        return True, "Modèle valide"

    def to_dict(self) -> dict:
        node_index = {n.id: i for i, n in enumerate(self.nodes)}
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "lines": [l.to_dict() for l in self.lines],
            "beams": [b.to_dict(node_index) for b in self.beams],
            "columns": [c.to_dict(node_index) for c in self.columns],
            "point_loads": [p.to_dict() for p in self.point_loads],
            "point_loads_on_beams": [p.to_dict() for p in self.point_loads_on_beams],  # NOUVEAU
            "distributed_loads": [d.to_dict() for d in self.distributed_loads],
            "version": "2026.02",
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StructuralModel":
        model = cls()

        # 1. Nœuds
        model.nodes = [Node.from_dict(d) for d in data.get("nodes", [])]
        node_by_id = {n.id: n for n in model.nodes}

        # 2. Lines
        model.lines = [Line.from_dict(d) for d in data.get("lines", [])]

        # 3. Beams
        for b_dict in data.get("beams", []):
            beam = Beam.from_dict(b_dict, model.nodes)
            model.beams.append(beam)

        # 4. Columns
        for c_dict in data.get("columns", []):
            col = Column.from_dict(c_dict, model.nodes)
            model.columns.append(col)

        # 5. Charges ponctuelles sur nœuds
        for p_dict in data.get("point_loads", []):
            node = node_by_id.get(p_dict["node_id"])
            if node:
                model.add_point_load(node, p_dict["fx"], p_dict["fy"])

        # 6. Charges ponctuelles sur poutres (NOUVEAU)
        member_by_id = {m.id: m for m in model.beams + model.columns}
        for p_dict in data.get("point_loads_on_beams", []):
            beam = member_by_id.get(p_dict["beam_id"])
            if beam and isinstance(beam, Beam):
                model.add_point_load_on_beam(
                    beam,
                    p_dict["position_ratio"],
                    p_dict["fx"],
                    p_dict["fy"]
                )

        # 7. Charges réparties
        for d_dict in data.get("distributed_loads", []):
            member = member_by_id.get(d_dict["member_id"])
            if member:
                model.add_distributed_load(
                    member,
                    d_dict["w"],
                    d_dict.get("start_pos", 0.0),
                    d_dict.get("end_pos", 1.0),
                )

        return model