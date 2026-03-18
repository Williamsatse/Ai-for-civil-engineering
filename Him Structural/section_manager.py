# section_manager.py
"""
Module de gestion des sections transversales.

CORRECTIONS APPLIQUÉES :
  1. NameError : variable y_g utilisée hors de son bloc "if shape_type == T"
     → valeur par défaut y_g = h/2 pour tous les autres cas
  2. save_section définie deux fois → une seule définition conservée
"""

import json
from dataclasses import dataclass, field
from typing import Dict, Optional, List
from chinese_standard import ChineseConcrete

@dataclass
class Section:
    """
    Section transversale d'un élément structural.
    Supporte : rectangle, I (profils IPE / HEA / HEB), T
    """
    name: str
    shape_type: str
    material: str

    b: float = 0.0
    h: float = 0.0
    tw: float = 0.0
    tf: float = 0.0
    bf: float = 0.0
    web_position: str = "center"

    concrete_grade: str = "30"

    # Propriétés calculées
    area: float = 0.0
    Ix: float = 0.0
    Iy: float = 0.0
    Wx: float = 0.0
    Wy: float = 0.0

    def __post_init__(self):
        self.calculate_properties()

    def calculate_properties(self):
        """
        Calcule les propriétés géométriques de la section.

        ✅ FIX 1 : y_g (centre de gravité) était utilisé dans le bloc final
           pour TOUTES les sections, mais n'était défini que pour le cas T.
           Pour rectangle et I, y_g = h/2 (section symétrique par axe horizontal).
        """

        # Valeur par défaut : section symétrique → centre de gravité au milieu
        y_g = self.h / 2 if self.h > 0 else 0.0

        if self.shape_type == "rectangle":
            self.area = self.b * self.h
            self.Ix = (self.b * self.h ** 3) / 12
            self.Iy = (self.h * self.b ** 3) / 12
            y_g = self.h / 2  # centre de gravité = milieu pour rectangle symétrique

        elif self.shape_type in ("I", "IPE", "HEA", "HEB") or self.shape_type.startswith(("IPE", "HEA", "HEB")):
            # Profil en I symétrique
            if self.tw == 0 or self.tf == 0:
                # Valeurs par défaut proportionnelles si non fournies
                self.tw = max(self.b * 0.06, 4.0)
                self.tf = max(self.h * 0.04, 6.0)

            web_h = self.h - 2 * self.tf
            if web_h <= 0:
                web_h = self.h * 0.5  # garde-fou si dimensions incohérentes

            self.area = (self.b * self.tf * 2) + (self.tw * web_h)
            self.Ix = (self.b * self.h ** 3 / 12) - ((self.b - self.tw) * web_h ** 3 / 12)
            self.Iy = (2 * self.tf * self.b ** 3 / 12) + (web_h * self.tw ** 3 / 12)
            y_g = self.h / 2  # symétrique

        elif self.shape_type == "T":
            flange_area = self.bf * self.tf
            web_h = max(self.h - self.tf, 0.0)
            web_area = self.tw * web_h
            self.area = flange_area + web_area

            if self.area > 0:
                # Centre de gravité depuis le BAS de la section T
                y_g = (flange_area * (self.h - self.tf / 2) + web_area * (web_h / 2)) / self.area
            else:
                y_g = self.h / 2

            # Inertie par rapport au centre de gravité (Steiner)
            Ix_flange = (self.bf * self.tf ** 3 / 12) + flange_area * (self.h - self.tf / 2 - y_g) ** 2
            Ix_web = (self.tw * web_h ** 3 / 12) + web_area * (web_h / 2 - y_g) ** 2
            self.Ix = Ix_flange + Ix_web
            self.Iy = (self.tf * self.bf ** 3 / 12) + (web_h * self.tw ** 3 / 12)

        # Modules résistants (Wx et Wy)
        # ✅ FIX 1 : y_g est maintenant toujours défini avant cette section
        if self.Ix > 0 and self.area > 0:
            dist_max_x = max(y_g, self.h - y_g) if y_g != self.h / 2 else self.h / 2
            self.Wx = self.Ix / dist_max_x if dist_max_x > 0 else 0.0

        if self.Iy > 0:
            b_ref = self.bf if self.shape_type == "T" else self.b
            self.Wy = self.Iy / (b_ref / 2) if b_ref > 0 else 0.0

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "shape_type": self.shape_type,
            "material": self.material,
            "b": self.b,
            "h": self.h,
            "area": self.area,
            "Ix": self.Ix,
            "Iy": self.Iy,
            "Wx": self.Wx,
            "Wy": self.Wy,
            "concrete_grade": self.concrete_grade,
        }
        if self.shape_type in ("I", "T", "IPE", "HEA", "HEB") or self.shape_type.startswith(("IPE", "HEA", "HEB")):
            d.update({"tw": self.tw, "tf": self.tf})
        if self.shape_type == "T":
            d["bf"] = self.bf
            d["web_position"] = self.web_position
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Section":
        sec = cls(
            name=data["name"],
            shape_type=data["shape_type"],
            material=data.get("material", "Concrete"),
            b=data.get("b", 0.0),
            h=data.get("h", 0.0),
            concrete_grade=data.get("concrete_grade", "C30"),
        )
        sec.tw = data.get("tw", 0.0)
        sec.tf = data.get("tf", 0.0)
        sec.bf = data.get("bf", sec.b)
        sec.web_position = data.get("web_position", "center")
        sec.calculate_properties()
        return sec

    def summary(self) -> str:
        """Résumé lisible pour l'UI."""
        grade = f"| {self.concrete_grade}" if self.material == "Concrete" else ""
        return (
            f"{self.name} ({self.shape_type}) | {self.material}\n"
            f"  b={self.b:.0f}mm  h={self.h:.0f}mm\n"
            f"  Aire={self.area:.1f}mm²  Ix={self.Ix:.0f}mm⁴"
        )


class SectionLibrary:
    """
    Bibliothèque persistante des sections disponibles.

    ✅ FIX 2 : save_section était définie deux fois (doublon).
       Une seule définition propre conservée.
    """

    def __init__(self):
        self.sections: Dict[str, Section] = {}
        self.add_default_sections()

    def add_default_sections(self):
        """Sections prédéfinies au démarrage."""
        self.save_section(Section("Rect. 200x600", "rectangle", "Concrete", b=200, h=600))
        self.save_section(Section("Rect. 300x800", "rectangle", "Concrete", b=300, h=800))
        self.save_section(Section("IPE 200", "IPE", "Steel", b=100, h=200, tw=5.6, tf=8.5))
        self.save_section(Section("T 150x10", "T", "Concrete", bf=150, h=150, tw=10, tf=15))

    # ✅ FIX 2 : une seule définition de save_section
    def save_section(self, section: Section):
        """Ajoute ou met à jour une section dans la bibliothèque."""
        self.sections[section.name] = section

    def get_section(self, name: str) -> Optional[Section]:
        """Retourne une section par son nom, ou None."""
        return self.sections.get(name)

    def get_all_sections(self) -> List[Section]:
        """Retourne toutes les sections disponibles."""
        return list(self.sections.values())

    def delete_section(self, name: str) -> bool:
        """Supprime une section. Retourne True si elle existait."""
        if name in self.sections:
            del self.sections[name]
            return True
        return False

    def create_rectangular_section(self, name: str, width: float,
                                   height: float, material: str = "Concrete", concrete_grade: str = "C30") -> Section:
        """Crée et enregistre une section rectangulaire."""
        section = Section(name, "rectangle", material, b=width, h=height, concrete_grade=concrete_grade)
        self.save_section(section)
        return section

    def save_to_file(self, filepath: str):
        """Sauvegarde la bibliothèque en JSON."""
        data = {"sections": [s.to_dict() for s in self.get_all_sections()]}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, filepath: str) -> "SectionLibrary":
        """Charge une bibliothèque depuis un fichier JSON."""
        lib = cls()
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for sec_data in data.get("sections", []):
                lib.save_section(Section.from_dict(sec_data))
        except Exception as e:
            print(f"Erreur chargement bibliothèque sections : {e}")
        return lib
