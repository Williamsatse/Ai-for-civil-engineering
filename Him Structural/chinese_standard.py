# chinese_standard_v3.py — VERSION FINALE AVEC DIAGNOSTIC ET TOUTES COMBINAISONS

import math
from itertools import combinations_with_replacement
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import Counter


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 1: DONNÉES MATÉRIAUX GB 50010
# ═════════════════════════════════════════════════════════════════════════════

class ChineseConcrete:
    GRADES = {
        "C15": {"fcuk": 15.0, "fck": 10.0, "fc": 7.2,  "fcd": 7.2,  "fctk": 1.27, "ft": 0.91, "fctd": 0.91, "Ec": 22000, "alpha1": 1.0,  "beta1": 0.80},
        "C20": {"fcuk": 20.0, "fck": 13.4, "fc": 9.6,  "fcd": 9.6,  "fctk": 1.54, "ft": 1.10, "fctd": 1.10, "Ec": 25500, "alpha1": 1.0,  "beta1": 0.80},
        "C25": {"fcuk": 25.0, "fck": 16.7, "fc": 11.9, "fcd": 11.9, "fctk": 1.78, "ft": 1.27, "fctd": 1.27, "Ec": 28000, "alpha1": 1.0,  "beta1": 0.80},
        "C30": {"fcuk": 30.0, "fck": 20.1, "fc": 14.3, "fcd": 14.3, "fctk": 2.01, "ft": 1.43, "fctd": 1.43, "Ec": 30000, "alpha1": 1.0,  "beta1": 0.80},
        "C35": {"fcuk": 35.0, "fck": 23.4, "fc": 16.7, "fcd": 16.7, "fctk": 2.20, "ft": 1.57, "fctd": 1.57, "Ec": 31500, "alpha1": 1.0,  "beta1": 0.80},
        "C40": {"fcuk": 40.0, "fck": 26.8, "fc": 19.1, "fcd": 19.1, "fctk": 2.39, "ft": 1.71, "fctd": 1.71, "Ec": 32500, "alpha1": 1.0,  "beta1": 0.80},
        "C45": {"fcuk": 45.0, "fck": 29.6, "fc": 21.1, "fcd": 21.1, "fctk": 2.51, "ft": 1.80, "fctd": 1.80, "Ec": 33500, "alpha1": 1.0,  "beta1": 0.80},
        "C50": {"fcuk": 50.0, "fck": 32.4, "fc": 23.1, "fcd": 23.1, "fctk": 2.65, "ft": 1.89, "fctd": 1.89, "Ec": 34500, "alpha1": 1.0,  "beta1": 0.80},
        "C55": {"fcuk": 55.0, "fck": 35.5, "fc": 25.3, "fcd": 25.3, "fctk": 2.74, "ft": 1.96, "fctd": 1.96, "Ec": 35500, "alpha1": 0.99, "beta1": 0.79},
        "C60": {"fcuk": 60.0, "fck": 38.5, "fc": 27.5, "fcd": 27.5, "fctk": 2.85, "ft": 2.04, "fctd": 2.04, "Ec": 36000, "alpha1": 0.98, "beta1": 0.78},
        "C65": {"fcuk": 65.0, "fck": 41.5, "fc": 29.7, "fcd": 29.7, "fctk": 2.93, "ft": 2.09, "fctd": 2.09, "Ec": 36500, "alpha1": 0.97, "beta1": 0.77},
        "C70": {"fcuk": 70.0, "fck": 44.5, "fc": 31.8, "fcd": 31.8, "fctk": 3.00, "ft": 2.14, "fctd": 2.14, "Ec": 37000, "alpha1": 0.96, "beta1": 0.76},
        "C75": {"fcuk": 75.0, "fck": 47.4, "fc": 33.8, "fcd": 33.8, "fctk": 3.05, "ft": 2.18, "fctd": 2.18, "Ec": 37000, "alpha1": 0.95, "beta1": 0.75},
        "C80": {"fcuk": 80.0, "fck": 50.2, "fc": 35.9, "fcd": 35.9, "fctk": 3.10, "ft": 2.22, "fctd": 2.22, "Ec": 38000, "alpha1": 0.94, "beta1": 0.74},
    }

    @staticmethod
    def get_properties(grade="C30"):
        return ChineseConcrete.GRADES.get(grade.upper(), ChineseConcrete.GRADES["C30"])


class ChineseSteel:
    GRADES_CONSTRUCTION = {
        "RRB400": {"fyk": 400.0, "fy": 360.0, "fyd": 360.0, "fd": 360.0, "Es": 200000},
        "HRB400": {"fyk": 400.0, "fy": 360.0, "fyd": 360.0, "fd": 360.0, "Es": 200000},
        "HRB335": {"fyk": 335.0, "fy": 300.0, "fyd": 300.0, "fd": 300.0, "Es": 200000},
        "HPB235": {"fyk": 235.0, "fy": 210.0, "fyd": 210.0, "fd": 210.0, "Es": 210000},
        "HRB500": {"fyk": 500.0, "fy": 435.0, "fyd": 435.0, "fd": 435.0, "Es": 200000},
    }

    @staticmethod
    def get_properties(grade="HRB400", rule="construction"):
        return ChineseSteel.GRADES_CONSTRUCTION.get(grade.upper(), 
                ChineseSteel.GRADES_CONSTRUCTION["HRB400"])


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 2: DONNÉES BARRES
# ═════════════════════════════════════════════════════════════════════════════

REBAR_AREAS: Dict[int, float] = {
    8: 50.3, 10: 78.5, 12: 113.1, 14: 153.9, 16: 201.1,
    18: 254.5, 20: 314.2, 22: 380.1, 25: 490.9, 28: 615.8,
}

ALL_DIAMETERS: List[int] = sorted(REBAR_AREAS.keys())

MIN_CLEAR_SPACING = {"beam_bottom": 25, "beam_top": 30, "side_cover": 25}


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 3: SÉLECTEUR SIMPLIFIÉ AVEC DIAGNOSTIC
# ═════════════════════════════════════════════════════════════════════════════

class SimpleBarSelector:
    """
    Sélecteur de ferraillage amélioré avec détection intelligente des solutions.
    """

    def __init__(self, b_section: float, h_section: float, cover: float = 40.0,
                 max_bars_total: int = 12, max_bars_per_layer: int = 6,
                 max_layers: int = 3, diameters: List[int] = None):

        self.b = float(b_section)
        self.h = float(h_section)
        self.cover = float(cover)
        self.h0 = h_section - cover
        self.max_bars_total = max_bars_total
        self.max_bars_per_layer = max_bars_per_layer
        self.max_layers = max_layers
        self.diameters = sorted(diameters if diameters else ALL_DIAMETERS)

    def _calculate_as(self, combo: Tuple[int, ...]) -> float:
        return sum(REBAR_AREAS[d] for d in combo)

    def _format_combo(self, combo: Tuple[int, ...]) -> str:
        if not combo:
            return ""
        counts = Counter(combo)
        return " + ".join(f"{n}Ø{d}" for d, n in sorted(counts.items(), reverse=True))

    def _distribute_in_layers(self, n_bars: int, max_per_layer: int, force_multi_layer: bool = False) -> List[int]:
        if n_bars == 0:
            return []
        
        # Calculer le nombre optimal de couches
        if force_multi_layer and n_bars > 3:
            # Forcer au moins 2 couches si possible
            n_layers = min(max(2, math.ceil(n_bars / max_per_layer)), self.max_layers)
        else:
            n_layers = min(math.ceil(n_bars / max_per_layer), self.max_layers)
        
        if n_layers == 0:
            return []
        
        base, extra = divmod(n_bars, n_layers)
        return sorted([base + (1 if i < extra else 0) for i in range(n_layers)], reverse=True)

    def _check_fit(self, combo: Tuple[int, ...], force_multi_layer: bool = False) -> Tuple[bool, Optional[Dict]]:
        if not combo:
            return False, None

        n_bars = len(combo)
        max_dia = max(combo)

        if n_bars > self.max_bars_total:
            return False, None

        # Essayer différentes configurations de couches
        best_config = None
        best_score = -1
        
        for n_layers in range(1, self.max_layers + 1):
            if n_layers == 1:
                layers = [n_bars]
            else:
                # Distribution équilibrée
                base, extra = divmod(n_bars, n_layers)
                layers = sorted([base + (1 if i < extra else 0) for i in range(n_layers)], reverse=True)
            
            if max(layers) > self.max_bars_per_layer:
                continue
            
            max_in_layer = layers[0]

            # Hauteur disponible
            s_vert = max(25.0, float(max_dia))
            h_needed = n_layers * max_dia + (n_layers - 1) * s_vert
            
            # Largeur nécessaire
            s_horiz = max(MIN_CLEAR_SPACING["beam_bottom"], max_dia)
            b_needed = 2 * self.cover + max_in_layer * max_dia + (max_in_layer - 1) * s_horiz

            # Score de constructibilité (plus haut = mieux)
            score = 0
            fits = True
            
            if h_needed > self.h0 - self.cover:
                fits = False
                score -= 100  # Pénalité sévère pour hauteur insuffisante
            
            if b_needed > self.b:
                fits = False
                score -= (b_needed - self.b)  # Pénalité proportionnelle
            
            if fits:
                score += 100  # Bonus si ça rentre
                score += (self.b - b_needed) * 0.5  # Bonus pour marge de manœuvre
                score -= (n_layers - 1) * 10  # Légère pénalité par couche supplémentaire
            
            # Priorité aux solutions multi-couches si demandé
            if force_multi_layer and n_layers >= 2:
                score += 20
            
            if score > best_score:
                best_score = score
                clear = (self.b - 2 * self.cover - max_in_layer * max_dia) / (max_in_layer - 1) if max_in_layer > 1 else float('inf')
                best_config = {
                    "fits": fits,
                    "n_layers": n_layers,
                    "bars_per_layer": layers,
                    "max_in_layer": max_in_layer,
                    "clear_spacing": clear if clear > 0 else 0,
                    "b_required": b_needed,
                    "h_required": h_needed,
                    "score": score
                }
        
        if best_config is None:
            return False, None
            
        return best_config["fits"], best_config


    def search(self, As_required: float, top_n: int = 15, 
               tolerance_oversize: float = 0.50,
               allow_undersize: float = 0.05,
               force_multi_layer: bool = False,
               max_diameter_types: int = 2) -> Tuple[List[Dict], Optional[Dict]]:
        """
        Recherche les solutions avec tolérances élargies.
        """
        candidates = []
        
        As_min = As_required * (1 - allow_undersize)
        As_max = As_required * (1 + tolerance_oversize)

        for n_bars in range(2, self.max_bars_total + 1):
            for combo in combinations_with_replacement(self.diameters, n_bars):

                unique_diameters = len(set(combo))
                if unique_diameters > max_diameter_types:
                    continue


                As_provided = self._calculate_as(combo)

                # Vérifier la plage de section d'acier
                if As_provided < As_min or As_provided > As_max:
                    continue

                fits, geo = self._check_fit(combo, force_multi_layer=force_multi_layer)
                
                # Accepter même les solutions qui ne rentrent pas parfaitement
                # si on force les alternatives
                if not fits and not force_multi_layer:
                    continue

                delta = As_provided - As_required
                delta_pct = (delta / As_required) * 100

                # Score de constructibilité amélioré
                constructibility = 100
                if geo:
                    constructibility += min(geo.get("clear_spacing", 0) - 25, 20)  # Bonus espacement
                    constructibility -= (geo["n_layers"] - 1) * 5  # Pénalité couches
                    if not geo.get("fits", False):
                        constructibility -= 30  # Pénalité si ne rentre pas parfaitement
                
                constructibility = max(0, min(100, constructibility))

                candidates.append({
                    "combo": combo,
                    "disposition": self._format_combo(combo),
                    "As_provided": round(As_provided, 1),
                    "As_required": round(As_required, 1),
                    "delta_mm2": round(delta, 1),
                    "delta_percent": round(delta_pct, 2),
                    "n_bars": n_bars,
                    "n_layers": geo["n_layers"] if geo else 1,
                    "bars_per_layer": geo["bars_per_layer"] if geo else [n_bars],
                    "max_diameter": max(combo),
                    "min_diameter": min(combo),
                    "clear_spacing_mm": round(geo.get("clear_spacing", 0), 1) if geo else 0,
                    "b_required_mm": round(geo.get("b_required", self.b), 1) if geo else self.b,
                    "h_required_mm": round(geo.get("h_required", self.h), 1) if geo else self.h,
                    "fits_geometry": geo.get("fits", False) if geo else False,
                    "constructibility": round(constructibility, 1),
                    "is_uniform": len(set(combo)) == 1,
                    "diameter_types": len(set(combo)),
                    "priority_score": abs(delta) + (0 if (geo and geo.get("fits")) else 1000),  # Pénaliser les non-fits
                })

        # === DIAGNOSTIC SI AUCUNE SOLUTION ===
        diagnostic = None
        if not candidates:
            diagnostic = self._generate_diagnostic(As_required, tolerance_oversize)

        # Tri : d'abord celles qui rentrent, puis par proximité de As
        candidates.sort(key=lambda c: (not c["fits_geometry"], c["priority_score"], -c["constructibility"]))
        
        return candidates[:top_n], diagnostic
    

    def _generate_forced_solutions(self, As_required: float, max_diameter_types: int = 2) -> List[Dict]:
        """
        Génère des solutions "forcées" quand aucune solution standard ne convient.
        Utile pour proposer des alternatives comme 6Ø20 en 2 couches.
        """
        forced = []
        
        # Trouver le meilleur diamètre pour 2 couches
        if max_diameter_types >= 1:
            for dia in [25, 22, 20, 18, 16, 14]:
                for n_total in [2, 3, 4, 5, 6, 7, 8]:
                    if n_total > self.max_bars_total:
                        continue
                
                    # Calculer répartition en 2 couches max
                    n_per_layer = min(n_total, self.max_bars_per_layer)
                    n_layers = 1 if n_total <= n_per_layer else 2
                
                    if n_layers > self.max_layers:
                        continue
                
                    layers = [n_per_layer, n_total - n_per_layer] if n_layers == 2 else [n_total]
                
                    # Vérifier largeur
                    s = max(25, dia)
                    b_needed = 2 * self.cover + max(layers) * dia + (max(layers) - 1) * s
                
                    area_per_bar = REBAR_AREAS.get(dia, 0)
                    total_area = n_total * area_per_bar
                
                    if total_area < As_required * 0.75:  # Au moins 75%
                        continue
                
                    combo = tuple([dia] * n_total)
                
                    forced.append({
                        "combo": combo,
                        "disposition": self._format_combo(combo),
                        "As_provided": round(total_area, 1),
                        "As_required": round(As_required, 1),
                        "delta_mm2": round(total_area - As_required, 1),
                        "delta_percent": round((total_area - As_required) / As_required * 100, 2),
                        "n_bars": n_total,
                        "n_layers": n_layers,
                        "bars_per_layer": layers,
                        "max_diameter": dia,
                        "min_diameter": dia,
                        "clear_spacing_mm": (self.b - 2 * self.cover - max(layers) * dia) / (max(layers) - 1) if max(layers) > 1 else 50,
                        "b_required_mm": b_needed,
                        "h_required_mm": n_layers * dia + (n_layers - 1) * 25,
                        "fits_geometry": b_needed <= self.b,
                        "constructibility": 80 if b_needed <= self.b else 40,  # Haute constructibilité pour uniforme
                        "is_uniform": True,
                        "diameter_types": 1,
                        "priority_score": abs(total_area - As_required),
                        "forced": True,
                    })
    
        # Stratégie 2 : Solutions MIXTES (2 Ø max) - si autorisé
        if max_diameter_types >= 2:
            for dia_large in [25, 22, 20, 18]:
                for dia_small in [20, 18, 16, 14, 12]:
                    if dia_small >= dia_large:
                        continue
                
                    for n_large in range(1, 5):
                        for n_small in range(1, 5):
                            n_total = n_large + n_small
                        
                            if n_total > self.max_bars_total or n_total < 2:
                                continue
                        
                            # Répartition 2 couches max
                            n_per_layer = min(n_total, self.max_bars_per_layer)
                            n_layers = 1 if n_total <= n_per_layer else 2
                        
                            if n_layers > self.max_layers:
                               continue
                          
                            layers = [n_per_layer, n_total - n_per_layer] if n_layers == 2 else [n_total]
                        
                            # Vérifier largeur avec le plus gros Ø
                            s = max(25, dia_large)
                            b_needed = 2 * self.cover + max(layers) * dia_large + (max(layers) - 1) * s
                        
                            area = n_large * REBAR_AREAS.get(dia_large, 0) + n_small * REBAR_AREAS.get(dia_small, 0)
                            
                            if area < As_required * 0.75:
                                continue
                        
                            combo = tuple([dia_large] * n_large + [dia_small] * n_small)
                        
                            forced.append({
                                "combo": combo,
                                "disposition": self._format_combo(combo),
                                "As_provided": round(area, 1),
                                "As_required": round(As_required, 1),
                                "delta_mm2": round(area - As_required, 1),
                                "delta_percent": round((area - As_required) / As_required * 100, 2),
                                "n_bars": n_total,
                                "n_layers": n_layers,
                                "bars_per_layer": layers,
                                "max_diameter": dia_large,
                                "min_diameter": dia_small,
                                "clear_spacing_mm": (self.b - 2 * self.cover - max(layers) * dia_large) / (max(layers) - 1) if max(layers) > 1 else 50,
                                "b_required_mm": b_needed,
                                "h_required_mm": n_layers * dia_large + (n_layers - 1) * 25,
                                "fits_geometry": b_needed <= self.b,
                                "constructibility": 60 if b_needed <= self.b else 30,
                                "is_uniform": False,
                                "diameter_types": 2,
                                "priority_score": abs(area - As_required),
                                "forced": True,
                            })
    
        # Trier : uniformes d'abord, puis par proximité
        forced.sort(key=lambda c: (not c["is_uniform"], not c["fits_geometry"], c["priority_score"]))
        return forced[:10]

    def _generate_diagnostic(self, As_required: float, tolerance: float) -> Dict:
        """Génère un diagnostic détaillé quand aucune solution ne tient."""

        # Trouver la meilleure solution théorique (sans contrainte géométrique)
        best_theoretical = None
        best_score = float('inf')

        for n_bars in range(2, self.max_bars_total + 1):
            for combo in combinations_with_replacement(self.diameters, n_bars):
                As_prov = self._calculate_as(combo)
                # Score: distance à As_req + pénalité si trop petit
                if As_prov < As_required * 0.95:
                    score = abs(As_prov - As_required) * 2  # pénalité si sous-dimensionné
                else:
                    score = abs(As_prov - As_required)

                if score < best_score:
                    best_score = score
                    best_theoretical = (combo, As_prov)

        if not best_theoretical:
            return {"error": "Impossible de trouver une solution théorique"}

        combo, As_prov = best_theoretical
        max_dia = max(combo)
        n = len(combo)
        s_min = max(25, max_dia)

        # Calculs des largeurs nécessaires
        b_needed_1layer = 2 * self.cover + n * max_dia + (n - 1) * s_min

        # En 2 couches
        n_per_layer_2 = min(4, (n + 1) // 2)
        b_needed_2layers = 2 * self.cover + n_per_layer_2 * max_dia + (n_per_layer_2 - 1) * s_min

        # En 3 couches
        n_per_layer_3 = min(4, (n + 2) // 3)
        b_needed_3layers = 2 * self.cover + n_per_layer_3 * max_dia + (n_per_layer_3 - 1) * s_min

        proposals = []

        if b_needed_1layer > self.b:
            proposals.append({
                "description": f"Augmenter largeur à b={b_needed_1layer:.0f}mm (1 couche)",
                "new_b": b_needed_1layer,
                "n_layers": 1
            })

        if b_needed_2layers > self.b and n >= 3:
            proposals.append({
                "description": f"Augmenter largeur à b={b_needed_2layers:.0f}mm (2 couches)",
                "new_b": b_needed_2layers,
                "n_layers": 2
            })

        if self.cover > 35:
            b_with_less_cover = 2 * 35 + n * max_dia + (n - 1) * s_min
            if b_with_less_cover <= self.b + 50:  # Seulement si ça aide significativement
                proposals.append({
                    "description": f"Diminuer enrobage à 35mm (nécessite b≥{b_with_less_cover:.0f}mm)",
                    "new_cover": 35,
                    "new_b_needed": b_with_less_cover
                })

        # Alternative: barres plus petites
        smaller_alternatives = []
        for alt_combo in combinations_with_replacement([d for d in self.diameters if d < max_dia], min(n + 2, self.max_bars_total)):
            alt_As = self._calculate_as(alt_combo)
            if As_required * 0.95 <= alt_As <= As_required * (1 + tolerance):
                alt_max_dia = max(alt_combo)
                alt_n = len(alt_combo)
                alt_b_needed = 2 * self.cover + min(4, alt_n) * alt_max_dia + (min(4, alt_n) - 1) * max(25, alt_max_dia)
                if alt_b_needed <= self.b:
                    smaller_alternatives.append({
                        "disposition": self._format_combo(alt_combo),
                        "As": alt_As,
                        "delta": alt_As - As_required
                    })

        smaller_alternatives.sort(key=lambda x: abs(x["delta"]))

        return {
            "section_too_small": True,
            "current_b": self.b,
            "current_h": self.h,
            "current_cover": self.cover,
            "As_required": As_required,
            "best_theoretical": {
                "disposition": self._format_combo(combo),
                "As": As_prov,
                "n_bars": n,
                "max_diameter": max_dia,
            },
            "width_needed": {
                "1_layer": b_needed_1layer,
                "2_layers": b_needed_2layers,
                "3_layers": b_needed_3layers,
            },
            "proposals": proposals,
            "smaller_bar_alternatives": smaller_alternatives[:5],
            "message": f"Section {self.b:.0f}×{self.h:.0f}mm trop petite pour As={As_required:.0f}mm²"
        }


def select_rebar_simple(As_required: float, b: float, h: float,
                        cover: float = 40.0, **kwargs) -> Dict:
    """Fonction principale de sélection de ferraillage."""
    
    # Paramètres avec valeurs par défaut plus permissives
    max_bars_total = kwargs.get('max_bars_total', 12)
    max_bars_per_layer = kwargs.get('max_bars_per_layer', 6)
    max_layers = kwargs.get('max_layers', 2)
    tolerance_oversize = kwargs.get('tolerance_oversize', 0.50)  # 50% par défaut
    allow_undersize = kwargs.get('allow_undersize', 0.05)  # Permet 5% de sous-section
    max_diameter_types = kwargs.get('max_diameter_types', 2)  # DÉFAUT = 2
    preferred_uniform = kwargs.get('preferred_uniform', False)
    
    sel = SimpleBarSelector(
        b_section=b, 
        h_section=h, 
        cover=cover,
        max_bars_total=max_bars_total,
        max_bars_per_layer=max_bars_per_layer,
        max_layers=max_layers,
    )

    if preferred_uniform:
        solutions, diagnostic = sel.search(
            As_required,
            top_n=15,
            tolerance_oversize=tolerance_oversize,
            allow_undersize=allow_undersize,
            max_diameter_types=1  # Uniquement même Ø =1,
        )

        if solutions:
            return _format_solutions(solutions, As_required)
    
    # Premier essai avec tolérance normale
    solutions, diagnostic = sel.search(
        As_required, 
        top_n=15,
        tolerance_oversize=tolerance_oversize,
        allow_undersize=allow_undersize,
        max_diameter_types=max_diameter_types,
    )
    
    # Si aucune solution, essayer avec paramètres plus permissifs
    if not solutions:
        print(f"   ⚠️  Aucune solution standard, essai avec paramètres élargis...")
        solutions, diagnostic = sel.search(
            As_required,
            top_n=15,
            tolerance_oversize=0.80,  # 80% de dépassement autorisé
            allow_undersize=0.10,      # 10% de sous-section autorisé
            force_multi_layer=True,      # Forcer l'étude des solutions multi-couches
            max_diameter_types=max_diameter_types
        )
    
    # Si toujours rien, générer des solutions "forcées"
    if not solutions and diagnostic:
        print(f"   🔧 Génération de solutions alternatives...")
        solutions = sel._generate_forced_solutions(As_required)
        diagnostic = None if solutions else diagnostic

    if diagnostic:
        return {
            "error": diagnostic["message"],
            "diagnostic": diagnostic,
            "As_required": As_required,
            "b": b, "h": h, "cover": cover,
            "top_solutions": [],
            "best": None,
        }

    if not solutions:
        return {
            "error": f"Aucune solution trouvée pour As={As_required:.0f}mm²",
            "As_required": As_required, "b": b, "h": h,
            "top_solutions": [], "best": None,
        }

    return _format_solutions(solutions, As_required)

def _format_solutions(solutions: List[Dict], As_required: float) -> Dict:
    """Formate les solutions pour l'UI."""
    best = solutions[0]

    top_formatted = []
    for i, sol in enumerate(solutions, 1):
        top_formatted.append({
            "rank": i,
            "disposition": sol["disposition"],
            "is_mixed": not sol["is_uniform"],
            "is_uniform": sol["is_uniform"],
            "diameter_types": sol["diameter_types"],
            "area_provided_mm2": sol["As_provided"],
            "area_required_mm2": sol["As_required"],
            "oversize_mm2": sol["delta_mm2"],
            "oversize_percent": sol["delta_percent"],
            "efficiency": sol["As_required"] / sol["As_provided"] if sol["As_provided"] > 0 else 0,
            "constructibility": sol["constructibility"],
            "constructibility_score": sol["constructibility"],
            "layers": sol["n_layers"],
            "bars_per_layer": sol["bars_per_layer"],
            "n_bars": sol["n_bars"],
            "clear_spacing_mm": sol["clear_spacing_mm"],
            "max_diameter": sol["max_diameter"],
            "min_diameter": sol["min_diameter"],
        })

    return {
        "As_required_mm2": round(As_required, 1),
        "best": top_formatted[0],
        "top_solutions": top_formatted,
        "diagnostic": None,
    }


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 4: CLASSE RectangularSection
# ═════════════════════════════════════════════════════════════════════════════

class RectangularSection:
    """Calcul de section rectangulaire — GB 50010."""

    def __init__(self, b: float, h: float,
                 concrete_grade: str = "C30", steel_grade: str = "HRB335",
                 cover: float = 60.0, a_prime: float = 35.0, **kwargs):

        self.b = float(b)
        self.h = float(h)
        self.concrete_grade = concrete_grade.upper()
        self.steel_grade = steel_grade.upper()
        self.cover = float(cover)
        self.a_prime = float(a_prime)
        self.a_s = cover
        self.h0 = self.h - self.a_s

        c = ChineseConcrete.get_properties(self.concrete_grade)
        s = ChineseSteel.get_properties(self.steel_grade)

        self.fc = c["fc"]
        self.ft = c["ft"]
        self.alpha1 = c.get("alpha1", 1.0)
        self.Ec = c["Ec"]
        self.fy = s["fy"]

        xi_b_map = {"HPB235": 0.614, "HRB335": 0.550, "HRB400": 0.518, "HRB500": 0.482}
        self.xi_b = 0.550
        for key, val in xi_b_map.items():
            if key in self.steel_grade:
                self.xi_b = val
                break

        x_b = self.xi_b * self.h0
        self.Mu_max_Nm = self.alpha1 * self.fc * self.b * x_b * (self.h0 - x_b / 2)
        self.Mu_max_kNm = self.Mu_max_Nm / 1_000_000
        self.rho_min = max(0.20, 0.45 * self.ft / self.fy * 100)

    def needs_double_reinforcement(self, M_kNm: float) -> bool:
        return M_kNm > self.Mu_max_kNm

    def calculate_flexure(self, M_design_kNm: float, **kwargs) -> Dict:
        if self.needs_double_reinforcement(M_design_kNm):
            return self._calc_double(M_design_kNm, **kwargs)
        return self._calc_single(M_design_kNm, **kwargs)

    def _select_bars(self, As_req: float, label: str) -> Dict:
        """Sélectionne les barres avec le nouveau sélecteur."""
        print(f"\n{'='*60}")
        print(f"SÉLECTION {label}: As_req = {As_req:.1f} mm²")
        print(f"{'='*60}")

        result_uniform = select_rebar_simple(
            As_required=As_req,
            b=self.b,
            h=self.h,
            cover=self.cover,
            max_bars_total=12,
            max_bars_per_layer=6,
            max_layers=2,
            tolerance_oversize=0.50,
            allow_undersize=0.05,
            max_diameter_types=1,  # UNIQUEMENT MÊME Ø
            preferred_uniform=True,
        )
    
         # Essai 2 : Solutions mixtes mais max 2 Ø différents
        result_mixed = select_rebar_simple(
            As_required=As_req,
            b=self.b,
            h=self.h,
            cover=self.cover,
            max_bars_total=12,
            max_bars_per_layer=6,
            max_layers=2,  # MAX 2 COUCHES
            tolerance_oversize=0.60,
            allow_undersize=0.10,
            max_diameter_types=2,  # MAX 2 TYPES DE Ø
        )
    
        # Combiner les résultats : uniformes d'abord, puis mixtes
        all_solutions = []
    
        if result_uniform.get("top_solutions"):
            for sol in result_uniform["top_solutions"]:
                sol["priority"] = 1  # Haute priorité
                all_solutions.append(sol)

    
        if result_mixed.get("top_solutions"):
            for sol in result_mixed["top_solutions"]:
                # Éviter les doublons
                if not any(s["disposition"] == sol["disposition"] for s in all_solutions):
                    sol["priority"] = 2  # Priorité moyenne
                    all_solutions.append(sol)
    
        # Trier par priorité puis par écart
        all_solutions.sort(key=lambda x: (x["priority"], abs(x.get("oversize_mm2", 0))))
        best = all_solutions[0] if all_solutions else None

        if best and best.get("is_uniform"):
            print(f"   ✅ Solution uniforme privilégiée : {best['disposition']}")

        else:
            print(f"   ✅ Meilleure solution : {best['disposition'] if best else '—'}")

        # Si rien ne marche, retourner le diagnostic
        return {
            "As_required_mm2": round(As_req, 1),
            "best": best,
            "top_solutions": all_solutions[:12],
            "diagnostic": None,
        }

    def _calc_single(self, M_kNm: float, **kwargs) -> Dict:
        M = M_kNm * 1e6
        alpha_s = M / (self.alpha1 * self.fc * self.b * self.h0**2)

        if alpha_s >= 0.5:
            return self._calc_double(M_kNm, **kwargs)

        xi = 1.0 - math.sqrt(1.0 - 2.0 * alpha_s)
        x = xi * self.h0

        if xi > self.xi_b:
            return self._calc_double(M_kNm, **kwargs)

        As = (self.alpha1 * self.fc * self.b * x) / self.fy
        As_min = self.rho_min / 100.0 * self.b * self.h
        As_fin = max(As, As_min)

        Mu_kNm = (self.alpha1 * self.fc * self.b * x * (self.h0 - x/2)) / 1e6
        rho = As_fin / (self.b * self.h) * 100.0

        # Sélection des barres
        bar_result = self._select_bars(As_fin, "TRACTION")

        safe = Mu_kNm >= M_kNm
        status = "✅ OK" if safe else "❌ Échec"

        best = bar_result.get("best", {}) or {}
        top_sols = bar_result.get("top_solutions", [])
        diagnostic = bar_result.get("diagnostic")

        result = {
            "type": "single",
            "double_required": False,
            "M_design_kNm": round(M_kNm, 3),
            "Mu_max_kNm": round(self.Mu_max_kNm, 3),
            "Mu_capacity_kNm": round(Mu_kNm, 3),
            "b_mm": self.b, "h_mm": self.h, "h0_mm": round(self.h0, 1),
            "fc_MPa": self.fc, "fy_MPa": self.fy,
            "alpha1": self.alpha1, "xi_b": self.xi_b,
            "alpha_s": round(alpha_s, 5), "xi": round(xi, 4), "x_mm": round(x, 1),
            "As_required_mm2": round(As, 1),
            "As_min_mm2": round(As_min, 1),
            "As_final_mm2": round(As_fin, 1),
            "rho_percent": round(rho, 3),
            "rho_min_percent": round(self.rho_min, 3),
            "concrete_grade": self.concrete_grade,
            "steel_grade": self.steel_grade,
            "safe": safe,
            "status": status,
            "best_disposition": best.get("disposition", "—"),
            "best_bar_label": best.get("disposition", "—"),
            "top_solutions_full": top_sols,
            "bar_options": [s["disposition"] for s in top_sols],
            "has_diagnostic": diagnostic is not None,
            "diagnostic": diagnostic,
        }

        self._print_result(result, "SIMPLE")
        return result

    def _calc_double(self, M_kNm: float, **kwargs) -> Dict:
        M = M_kNm * 1e6
        x_b = self.xi_b * self.h0
        fy_pr = self.fy

        Mu1_Nm = self.alpha1 * self.fc * self.b * x_b * (self.h0 - x_b/2)
        Mu1_kNm = Mu1_Nm / 1e6
        Mu2_Nm = M - Mu1_Nm

        x_ok = x_b >= 2.0 * self.a_prime
        x_txt = f"{'✅' if x_ok else '⚠️'} x_b={x_b:.1f}mm vs 2a'={2*self.a_prime:.1f}mm"

        As_prime = Mu2_Nm / (fy_pr * (self.h0 - self.a_prime))
        As1 = (self.alpha1 * self.fc * self.b * x_b) / self.fy
        As_tot = As1 + (fy_pr * As_prime) / self.fy
        As_min = self.rho_min / 100.0 * self.b * self.h
        As_fin = max(As_tot, As_min)

        Mu_cap = (Mu1_Nm + fy_pr * As_prime * (self.h0 - self.a_prime)) / 1e6
        rho = As_fin / (self.b * self.h) * 100.0

        # Sélection des barres pour les deux faces
        print(f"\n{'='*60}")
        print(f"FERRAILLAGE DOUBLE")
        print(f"{'='*60}")

        comp_result = self._select_bars(As_prime, "COMPRESSION (As')")
        tens_result = self._select_bars(As_fin, "TRACTION (As)")

        safe = Mu_cap >= M_kNm and x_ok
        status = "✅ OK" if safe else "❌ Échec"

        best_comp = comp_result.get("best", {}) or {}
        best_tens = tens_result.get("best", {}) or {}

        result = {
            "type": "double",
            "double_required": True,
            "M_design_kNm": round(M_kNm, 3),
            "Mu_max_kNm": round(Mu1_kNm, 3),
            "Mu_capacity_kNm": round(Mu_cap, 3),
            "b_mm": self.b, "h_mm": self.h, "h0_mm": round(self.h0, 1),
            "a_prime_mm": self.a_prime,
            "fc_MPa": self.fc, "fy_MPa": self.fy,
            "alpha1": self.alpha1, "xi_b": self.xi_b, "x_b_mm": round(x_b, 1),
            "x_check_ok": x_ok, "x_check_status": x_txt,
            "Mu1_kNm": round(Mu1_kNm, 3), "Mu2_kNm": round(Mu2_Nm/1e6, 3),
            "As1_mm2": round(As1, 1),
            "As_total_mm2": round(As_tot, 1),
            "As_final_mm2": round(As_fin, 1),
            "As_prime_mm2": round(As_prime, 1),
            "As_min_mm2": round(As_min, 1),
            "rho_percent": round(rho, 3),
            "rho_min_percent": round(self.rho_min, 3),
            "concrete_grade": self.concrete_grade,
            "steel_grade": self.steel_grade,
            "safe": safe,
            "status": status,
            "best_disposition_compression": best_comp.get("disposition", "—"),
            "best_disposition_tension": best_tens.get("disposition", "—"),
            "best_comp_label": best_comp.get("disposition", "—"),
            "best_tension_label": best_tens.get("disposition", "—"),
            "top_solutions_compression": comp_result.get("top_solutions", []),
            "top_solutions_tension": tens_result.get("top_solutions", []),
            "comp_bar_options": [s["disposition"] for s in comp_result.get("top_solutions", [])],
            "tension_bar_options": [s["disposition"] for s in tens_result.get("top_solutions", [])],
            "has_diagnostic": (comp_result.get("diagnostic") is not None or 
                              tens_result.get("diagnostic") is not None),
            "diagnostic_compression": comp_result.get("diagnostic"),
            "diagnostic_tension": tens_result.get("diagnostic"),
        }

        self._print_result(result, "DOUBLE")
        return result

    def _print_result(self, r, rtype):
        sep = "═" * 60
        print(f"\n{sep}")
        print(f"FERRAILLAGE {rtype} — GB 50010")
        print(f"{sep}")
        print(f"Section: {r['b_mm']}×{r['h_mm']} mm, h₀={r['h0_mm']} mm")
        print(f"M={r['M_design_kNm']} kN·m, Mu_max={r['Mu_max_kNm']} kN·m")

        if rtype == "DOUBLE":
            print(f"As'={r['As_prime_mm2']} mm² → {r['best_comp_label']}")
            print(f"As ={r['As_final_mm2']} mm² → {r['best_tension_label']}")
        else:
            print(f"As={r['As_final_mm2']} mm² → {r['best_bar_label']}")

        print(f"Mu_cap={r['Mu_capacity_kNm']} kN·m — {r['status']}")

        if r.get("has_diagnostic"):
            print(f"\n⚠️  PROBLÈME GÉOMÉTRIQUE DÉTECTÉ")
            diag = r.get("diagnostic") or r.get("diagnostic_tension") or r.get("diagnostic_compression")
            if diag:
                print(f"   {diag.get('message', '')}")
                for p in diag.get("proposals", []):
                    print(f"   → {p['description']}")

        print(f"{sep}\n")


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 5: FONCTIONS UTILITAIRES
# ═════════════════════════════════════════════════════════════════════════════

def format_rebar_selection_for_ai(As_traction: float, As_compression: float = 0,
                                   b: float = 250, h: float = 500, cover: float = 40,
                                   concrete_grade: str = "C30",
                                   steel_grade: str = "HRB400") -> str:
    """Format pour affichage AI."""
    lines = [f"SÉLECTION FERRAILLAGE — {concrete_grade}/{steel_grade}",
             f"Section {b:.0f}×{h:.0f} mm, enrobage={cover:.0f} mm", ""]

    rep_t = select_rebar_simple(As_traction, b, h, cover)
    lines.append(f"TRACTION As={As_traction:.1f} mm²")

    if "error" in rep_t:
        lines.append(f"  ❌ {rep_t['error']}")
        if rep_t.get("diagnostic"):
            diag = rep_t["diagnostic"]
            lines.append(f"\n  📊 Diagnostic:")
            lines.append(f"     Meilleure solution théorique: {diag['best_theoretical']['disposition']}")
            lines.append(f"     Nécessite b≥{diag['width_needed']['1_layer']:.0f}mm en 1 couche")
            for p in diag.get("proposals", []):
                lines.append(f"     → {p['description']}")
    else:
        lines.append(f"  🏆 {rep_t['best']['disposition']}")
        for sol in rep_t.get("top_solutions", [])[:4]:
            typ = "U" if sol["is_uniform"] else f"M{sol['diameter_types']}"
            lines.append(f"  [{typ}] {sol['disposition']:<30} As={sol['area_provided_mm2']:.0f}mm² Δ={sol['oversize_mm2']:+.1f}")

    if As_compression > 10:
        lines.append("")
        rep_c = select_rebar_simple(As_compression, b, h, cover)
        lines.append(f"COMPRESSION As'={As_compression:.1f} mm²")
        if "error" in rep_c:
            lines.append(f"  ❌ {rep_c['error']}")
        else:
            lines.append(f"  🏆 {rep_c['best']['disposition']}")
            for sol in rep_c.get("top_solutions", [])[:3]:
                typ = "U" if sol["is_uniform"] else f"M{sol['diameter_types']}"
                lines.append(f"  [{typ}] {sol['disposition']:<30} As={sol['area_provided_mm2']:.0f}mm²")

    return "\n".join(lines)


# Compatibilité arrière
class ExhaustiveBarSelector(SimpleBarSelector):
    """Wrapper legacy."""
    pass

def find_best_rebar(As_required, b, h, **kwargs):
    """Wrapper legacy."""
    return select_rebar_simple(As_required, b, h, **kwargs)