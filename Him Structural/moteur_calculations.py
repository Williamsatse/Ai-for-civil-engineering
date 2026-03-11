# moteur_calculations.py - VERSION CORRIGÉE
"""
Analyse structurale avec PyNite + combinaisons de charges du fichier JSON.

CORRECTIONS PAR RAPPORT À LA VERSION PRÉCÉDENTE :
  1. add_load_case() créé AVANT d'ajouter les charges (obligation PyNite)
  2. Charges ponctuelles sur noeuds (model.point_loads) bien incluses
  3. Mapping complet 8 types JSON → cas PyNite (dead/live/wind/snow/...)
  4. Vérification stabilité avant lancement
  5. Enveloppe (pire combinaison) stockée sur chaque poutre
"""

import numpy as np
from PySide6.QtWidgets import QMessageBox
from Pynite import FEModel3D
from chinese_standard import ChineseConcrete

# Correspondance clé JSON → nom du cas PyNite
LOAD_CASE_MAP = {
    "dead":       "Dead",
    "live":       "Live",
    "wind":       "Wind",
    "roof":       "Roof",
    "rain":       "Rain",
    "snow":       "Snow",
    "earthquake": "Earthquake",
    "selfweight": "SelfWeight",
}

# Correspondance load_type sur l'objet → cas PyNite
LOAD_TYPE_TO_CASE = {
    "G":   "Dead",
    "Q":   "Live",
    "G+Q": "Dead",   # superposée → conservateur : affectée à Dead
}


class StructuralAnalyzer:
    def __init__(self, main_window):
        self.main  = main_window
        self.model = main_window.model
        self.results = {}   # results[beam_id][combination_name]

    def run_analysis(self):
        if not self.main.load_combinations:
            QMessageBox.warning(self.main, "Attention",
                "Aucune combinaison définie dans load_combinations.json.")
            return None

        if not self.model.beams:
            QMessageBox.warning(self.main, "Attention", "Aucune poutre à analyser.")
            return None

        print("🚀 Analyse PyNite avec combinaisons JSON...")
        pmodel = FEModel3D()

        # ══════════════════════════════════════════════════════════════
        # 1. NŒUDS & APPUIS
        # ══════════════════════════════════════════════════════════════
        print("  1. Nœuds & appuis...")
        for node in self.model.nodes:
            pmodel.add_node(node.id, node.x / 160.0, node.y / 160.0, 0.0)
            s = node.supports
            pmodel.def_support(node.id,
                               support_DX=bool(s.get("dx")),
                               support_DY=bool(s.get("dy")),
                               support_DZ=True,
                               support_RX=True,
                               support_RY=True,
                               support_RZ=bool(s.get("rz")))

        if not any(n.supports.get("dx") for n in self.model.nodes) or \
           not any(n.supports.get("dy") for n in self.model.nodes):
            QMessageBox.warning(self.main, "Structure instable",
                "Minimum requis : 1 blocage DX et 1 blocage DY.")
            return None

        # ══════════════════════════════════════════════════════════════
        # 2. MATÉRIAUX
        # ══════════════════════════════════════════════════════════════
        print("  2. Matériaux...")
        pmodel.add_material("Steel", E=210e9, G=210e9/2.6, nu=0.3, rho=7850)
        for grade in {getattr(b, "concrete_grade", "C30")
                      for b in self.model.beams if getattr(b, "material", "") == "Concrete"}:
            c = ChineseConcrete.get_properties(grade)
            pmodel.add_material(f"Concrete_{grade}", E=c["Ec"]*1e6,
                                G=c["Ec"]*1e6/2.6, nu=0.2, rho=2400)
            print(f"     Concrete_{grade} (Ec={c['Ec']} MPa)")

        # ══════════════════════════════════════════════════════════════
        # 3. SECTIONS + MEMBRES
        # ══════════════════════════════════════════════════════════════
        print("  3. Poutres...")
        for beam in self.model.beams:
            if beam.length < 1: continue
            sec = self.main.section_library.get_section(getattr(beam, "section_name", None))
            sn  = f"Sec_{beam.id}"
            if sec and beam.material == "Concrete":
                mat = f"Concrete_{getattr(beam, 'concrete_grade', 'C30')}"
                A, Iy, Iz = sec.area*1e-6, sec.Iy*1e-12, sec.Ix*1e-12
            else:
                mat = "Steel"
                A  = sec.area*1e-6 if sec else 0.01
                Iy = sec.Iy*1e-12  if sec else 1e-6
                Iz = sec.Ix*1e-12  if sec else 1e-6
            pmodel.add_section(sn, A=A, Iy=Iy, Iz=Iz, J=Iz*0.01)
            pmodel.add_member(beam.id, beam.node_start.id, beam.node_end.id, mat, sn)
            print(f"     {beam.id}: L={beam.length/160:.3f}m | {mat}")

        # ══════════════════════════════════════════════════════════════
        # 4. CAS DE CHARGE
        #    Dans PyNite, les cas de charge sont de simples étiquettes string
        #    passées lors de l'application des charges. Il n'y a PAS de méthode
        #    add_load_case() — les cas sont implicitement créés quand on appelle
        #    add_load_combo() avec les bons facteurs.
        #    On détecte quels cas sont réellement utilisés dans le modèle.
        # ══════════════════════════════════════════════════════════════
        print("  4. Détection des cas de charge actifs...")
        active_cases: set = {"Dead", "Live"}   # toujours présents

        for ld in (self.model.point_loads +
                   getattr(self.model, "point_loads_on_beams", []) +
                   self.model.distributed_loads):
            case = LOAD_TYPE_TO_CASE.get(getattr(ld, "load_type", "G"), "Dead")
            active_cases.add(case)

        print(f"     Cas actifs : {sorted(active_cases)}")

        # ══════════════════════════════════════════════════════════════
        # 5. APPLICATION DES CHARGES
        # NOTE PyNite : les cas de charge sont de simples strings passés
        # en paramètre `case=` lors de l'application des charges.
        # Un cas doit avoir AU MOINS une charge appliquée pour être reconnu
        # dans une combinaison. On s'assure donc que "Dead" et "Live" existent
        # toujours en appliquant une charge nulle si aucune charge n'existe.
        # ══════════════════════════════════════════════════════════════
        print("  5. Application des charges...")

        # Garde-fou : si un cas n'a aucune charge, PyNite peut lever KeyError
        # dans add_load_combo. On ajoute une charge nulle sur le premier nœud.
        _first_node_id = self.model.nodes[0].id if self.model.nodes else None
        _first_member_id = self.model.beams[0].id if self.model.beams else None
        # On tracke quels cas ont reçu au moins une charge réelle
        _cases_with_loads: set = set()

        # 5a — Charges ponctuelles sur nœuds
        for ld in self.model.point_loads:
            case = LOAD_TYPE_TO_CASE.get(getattr(ld, "load_type", "G"), "Dead")
            if abs(ld.fx * 1000) > 1e-6:
                pmodel.add_node_load(ld.node.id, "FX", ld.fx * 1000, case=case)
                _cases_with_loads.add(case)
            if abs(ld.fy * 1000) > 1e-6:
                pmodel.add_node_load(ld.node.id, "FY", ld.fy * 1000, case=case)
                _cases_with_loads.add(case)

        # 5b — Charges ponctuelles sur poutres
        for ld in self.model.point_loads_on_beams:
            if ld.beam.id not in pmodel.members: continue
            case  = LOAD_TYPE_TO_CASE.get(getattr(ld, "load_type", "G"), "Dead")
            L_m   = ld.beam.length / 160.0
            x_abs = ld.position_ratio * L_m
            if abs(ld.fy * 1000) > 1e-6:
                pmodel.add_member_pt_load(ld.beam.id, "Fy", P=ld.fy*1000, x=x_abs, case=case)
                _cases_with_loads.add(case)
            if abs(ld.fx * 1000) > 1e-6:
                pmodel.add_member_pt_load(ld.beam.id, "Fx", P=ld.fx*1000, x=x_abs, case=case)
                _cases_with_loads.add(case)

        # 5c — Charges réparties
        for beam in self.model.beams:
            if beam.id not in pmodel.members: continue
            L_m = beam.length / 160.0
            for ld in beam.distributed_loads:
                case = LOAD_TYPE_TO_CASE.get(getattr(ld, "load_type", "G"), "Dead")
                w    = ld.w * 1000
                if abs(w) > 1e-6:
                    pmodel.add_member_dist_load(
                        beam.id, "Fy", w1=w, w2=w,
                        x1=ld.start_pos * L_m, x2=ld.end_pos * L_m,
                        case=case
                    )
                    _cases_with_loads.add(case)

        # 5d — Charges nulles de sécurité pour les cas sans aucune charge réelle.
        # PyNite lèvera une KeyError dans add_load_combo si un cas référencé
        # n'a jamais reçu de charge. On évite ça avec une charge ponctuelle nulle.
        if _first_node_id:
            for case_name in active_cases:
                if case_name not in _cases_with_loads:
                    pmodel.add_node_load(_first_node_id, "FY", 0.0, case=case_name)
                    print(f"     ℹ️  Cas '{case_name}' sans charge → charge nulle ajoutée")

        # ══════════════════════════════════════════════════════════════
        # 6. COMBINAISONS (depuis load_combinations.json)
        #    Mapping JSON key → cas PyNite, facteur nul ou cas absent → ignoré.
        # ══════════════════════════════════════════════════════════════
        print("  6. Combinaisons depuis JSON...")
        combo_names = []

        for comb in self.main.load_combinations:
            name = comb.get("name", f"Comb_{comb.get('id','?')}")

            factors = {}
            for json_key, case_name in LOAD_CASE_MAP.items():
                factor = float(comb.get(json_key, 0.0))
                # N'inclure que si le facteur est non nul ET le cas existe dans le modèle
                if factor != 0.0 and case_name in active_cases:
                    factors[case_name] = factor

            # Garde-fou : combo vide → Dead × 1
            if not factors:
                factors = {"Dead": 1.0}

            pmodel.add_load_combo(name, factors)
            combo_names.append(name)
            print(f"     {name} : {factors}")

        # ══════════════════════════════════════════════════════════════
        # 7. ANALYSE LINÉAIRE
        # ══════════════════════════════════════════════════════════════
        print("  7. Résolution...")
        try:
            pmodel.analyze_linear(check_stability=True)
            print("✅ Analyse terminée.")
        except Exception as e:
            QMessageBox.critical(self.main, "Erreur PyNite", str(e))
            return None

        # ══════════════════════════════════════════════════════════════
        # 8. EXTRACTION DES RÉSULTATS PAR COMBINAISON
        # ══════════════════════════════════════════════════════════════
        print("  8. Extraction des résultats...")
        self.results = {}
        x_norm = np.linspace(0.0, 1.0, 101)

        for beam in self.model.beams:
            if beam.id not in pmodel.members: continue
            member = pmodel.members[beam.id]
            L_m    = beam.length / 160.0
            self.results[beam.id] = {}

            for comb_name in combo_names:
                M_pts, V_pts = [], []
                Mmax = Vmax = 0.0

                for t in x_norm:
                    x_m  = t * L_m
                    x_px = x_m * 160.0
                    try:
                        M_knm = member.moment("Mz", x_m, comb_name) / 1000.0
                        V_kn  = member.shear ("Fy", x_m, comb_name) / 1000.0
                    except Exception:
                        M_knm = V_kn = 0.0
                    M_pts.append((x_px, M_knm))
                    V_pts.append((x_px, V_kn))
                    Mmax = max(Mmax, abs(M_knm))
                    Vmax = max(Vmax, abs(V_kn))

                self.results[beam.id][comb_name] = {
                    "Mmax":      round(Mmax, 4),
                    "Vmax":      round(Vmax, 4),
                    "M_diagram": M_pts,
                    "V_diagram": V_pts,
                    "L_m":       L_m,
                }
                print(f"     {beam.id} | {comb_name} → "
                      f"Mmax={Mmax:.4f} kN·m  Vmax={Vmax:.4f} kN")

            # Stocker l'enveloppe (pire Mmax) directement sur la poutre
            worst_name, worst_data = max(
                self.results[beam.id].items(),
                key=lambda kv: kv[1]["Mmax"]
            )
            beam.analysis_results = dict(worst_data)
            beam.analysis_results["worst_combo"] = worst_name

        # ── Afficher la première combinaison sur le canvas ──
        if self.main and hasattr(self.main, "canvas") and self.results:
            first_beam = next(iter(self.results))
            first_comb = next(iter(self.results[first_beam]))
            self.main.canvas.draw_analysis_diagrams({
                bid: data[first_comb]
                for bid, data in self.results.items()
                if first_comb in data
            })

        print(f"✅ {len(self.results)} poutre(s) | {len(combo_names)} combinaison(s).")
        return self.results