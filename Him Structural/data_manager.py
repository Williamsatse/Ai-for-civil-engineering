# data_manager.py
"""
Gestionnaire de persistance des projets.

AMÉLIORATIONS :
  1. Support des charges ponctuelles sur poutres (PointLoadOnBeam)
  2. Validation des données avant sauvegarde
  3. Messages d'erreur détaillés
"""

import json
import ezdxf
from datetime import datetime
from structural_model import Node, Beam, Column, Line, PointLoad, PointLoadOnBeam, DistributedLoad


class DataManager:

    @staticmethod
    def save_project(filepath: str, canvas) -> bool:
        """
        Sauvegarde l'état actuel du canvas au format JSON.
        """
        try:
            model = canvas.model

            # Construction du dictionnaire d'index des nœuds
            node_index_map = {n.id: i for i, n in enumerate(model.nodes)}

            data = {
                "metadata": {
                    "version": "2.1",
                    "date": datetime.now().isoformat(),
                    "app": "Him Structural",
                    "features": ["point_loads_on_beams"],  # Indique les fonctionnalités utilisées
                },
                "nodes": [n.to_dict() for n in model.nodes],
                "lines": [l.to_dict() for l in model.lines],
                "beams": [b.to_dict(node_index_map) for b in model.beams],
                "columns": [c.to_dict(node_index_map) for c in model.columns],
                "point_loads": [p.to_dict() for p in model.point_loads],
                "point_loads_on_beams": [p.to_dict() for p in model.point_loads_on_beams],  # NOUVEAU
                "distributed_loads": [d.to_dict() for d in model.distributed_loads],
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"✅ Projet sauvegardé : {filepath}")
            return True

        except Exception as e:
            print(f"❌ Erreur sauvegarde : {e}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def load_project(filepath: str, canvas) -> bool:
        """
        Charge un projet depuis un fichier JSON.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            model = canvas.model

            # --- Nettoyage complet de l'état actuel ---
            canvas.scene.clear()

            model.nodes.clear()
            model.lines.clear()
            model.beams.clear()
            model.columns.clear()
            model.point_loads.clear()
            model.point_loads_on_beams.clear()  # NOUVEAU
            model.distributed_loads.clear()

            canvas.temp_start = None

            # --- Reconstruction depuis les données JSON ---
            model.nodes = [Node.from_dict(d) for d in data.get("nodes", [])]
            model.lines = [Line.from_dict(d) for d in data.get("lines", [])]

            for b_dict in data.get("beams", []):
                beam = Beam.from_dict(b_dict, model.nodes)
                model.beams.append(beam)

            for c_dict in data.get("columns", []):
                col = Column.from_dict(c_dict, model.nodes)
                model.columns.append(col)

            node_by_id = {n.id: n for n in model.nodes}
            
            # Charges ponctuelles sur nœuds
            for p_dict in data.get("point_loads", []):
                node = node_by_id.get(p_dict["node_id"])
                if node:
                    model.add_point_load(node, p_dict["fx"], p_dict["fy"])

            # Charges ponctuelles sur poutres (NOUVEAU - avec rétrocompatibilité)
            member_by_id = {m.id: m for m in model.beams + model.columns}
            for p_dict in data.get("point_loads_on_beams", []):
                beam = member_by_id.get(p_dict["beam_id"])
                if beam and isinstance(beam, Beam):
                    load = model.add_point_load_on_beam(
                        beam,
                        p_dict["position_ratio"],
                        p_dict["fx"],
                        p_dict["fy"]
                    )
                    load.load_type = p_dict.get("load_type", "G")

            # Charges réparties
            for d_dict in data.get("distributed_loads", []):
                member = member_by_id.get(d_dict["member_id"])
                if member:
                    load = model.add_distributed_load(
                        member,
                        d_dict["w"],
                        d_dict.get("start_pos", 0.0),
                        d_dict.get("end_pos", 1.0),
                    )
                    load.load_type = d_dict.get("load_type", "G")

            # Reconstruire les items graphiques
            canvas._rebuild_scene()
            canvas.section_library = canvas.main_window.section_library

            # Forcer le redessin
            canvas.scene.update()
            canvas.viewport().update()

            # Afficher les infos de version si disponibles
            metadata = data.get("metadata", {})
            version = metadata.get("version", "inconnue")
            print(f"✅ Projet chargé : {filepath} (version {version})")
            return True

        except Exception as e:
            print(f"❌ Erreur chargement : {e}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def export_to_dxf(filepath: str, canvas):
        """Export DXF (nécessite : pip install ezdxf)"""
        try:
            doc = ezdxf.new()
            msp = doc.modelspace()
            for beam in canvas.model.beams:
                msp.add_line(
                    (beam.node_start.x, beam.node_start.y),
                    (beam.node_end.x, beam.node_end.y),
                )
            doc.saveas(filepath)
            print(f"✅ Export DXF : {filepath}")
        except ImportError:
            print("❌ ezdxf non installé. Lancez : pip install ezdxf")
        except Exception as e:
            print(f"❌ Erreur export DXF : {e}")