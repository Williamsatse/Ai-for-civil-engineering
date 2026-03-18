# Him Structural

**Him Structural** est un logiciel de calcul de structure bâti en Python, conçu pour les ingénieurs du BTP. Il permet de modéliser, calculer et analyser des structures porteuses de bâtiments et d'ouvrages d'art.

## 🎯 Fonctionnalités

- **Modélisation graphique** : Interface intuitive pour dessiner structures, charges et appuis
- **Calcul de portiques** : Analyse des efforts intérieurs (moment, effort tranchant, effort normal)
- **Combinaisons d'actions** : Gestion automatique des combinaisons selon les normes
- **Normes intégrées** :
  - Eurocodes (EN 1990-EN 1997)
  - Normes chinoises (GB 50009, GB 50010, GB 50011, GB 50017)
- **Gestion des langues** : Interface multilingue (Français, Anglais)
- **Export de rapports** : Génération de rapport de calcul
- **Visualisation 3D** : Rendu graphique des structures et résultats

## 📁 Structure du projet

```
Him Structural/
├── main.py                     # Point d'entrée principal
├── canvas.py                   # Zone de dessin graphique
├── moteur_calculations.py      # Moteur de calcul structurel
├── structural_model.py         # Modèle de données structure
├── section_manager.py          # Gestionnaire de sections
├── data_manager.py             # Gestionnaire de données
├── language_manager.py         # Gestion multilingue
├── translations.py             # Traductions
├── chinese_standard.py         # Implémentation normes chinoises
├── settings_dialog.py          # Boîte de dialogue paramètres
├── calc_settings_dialog.py     # Paramètres de calcul
├── runtime_hook_openblas.py    # Configuration OpenBLAS
├── test.json                   # Données de test
├── settings.json             # Configuration utilisateur
├── diagrams_settings.json      # Paramètres des diagrammes
├── load_combinations.json      # Combinaisons de charges
├── icons/                      # Icônes de l'interface
│   ├── add_load.png
│   ├── beam.png
│   ├── column.png
│   ├── line.png
│   ├── node.png
│   ├── select.png
│   └── worker.ico
├── ui/                         # Composants UI
│   ├── diagram_items.py        # Éléments de diagramme
│   ├── diagrams_dialog.py      # Dialogue diagrammes
│   ├── him_ai_dialog.py        # Dialogue IA
│   ├── load_combinations_dialog.py
│   ├── load_items.py           # Éléments de charge
│   ├── loads_dialog.py         # Dialogue charges
│   ├── properties_panel.py     # Panneau propriétés
│   └── sections_panel.py       # Panneau sections
└── .vscode/
    └── settings.json           # Config VS Code
```

## 🚀 Installation

### Prérequis
- Python 3.10+
- pip

### Dépendances principales
```
PyQt6
numpy
matplotlib
scipy
```

### Installation

1. **Cloner le repository**
```bash
git clone https://github.com/Williamsatse/Ai-for-civil-engineering.git
cd Ai-for-civil-engineering/Him Structural
```

2. **Créer un environnement virtuel**
```bash
python -m venv env
source env/bin/activate  # Linux/Mac
# ou
env\Scripts\activate  # Windows
```

3. **Installer les dépendances**
```bash
pip install PyQt6 numpy matplotlib scipy
```

4. **Lancer l'application**
```bash
python main.py
```

## 📝 Utilisation

### Démarrage rapide
1. Lancez `main.py`
2. Créez un nouveau projet ou ouvrez-en un existant
3. Dessinez votre structure dans la zone graphique
4. Définissez les charges et conditions aux limites
5. Lancez le calcul
6. Visualisez les résultats (diagrammes, déformées)

### Workflow typique
1. **Création de la structure**
   - Ajoutez des nœuds
   - Reliez-les par des éléments (poutres, colonnes)
   - Définissez les sections et matériaux

2. **Application des charges**
   - Charges permanentes (G)
   - Charges d'exploitation (Q)
   - Charges climatiques (vent, neige)

3. **Paramétrage du calcul**
   - Choix de la norme
   - Combinaisons d'actions
   - Options de modélisation

4. **Résultats**
   - Diagrammes des efforts internes
   - Déformées
   - Réactions d'appui
   - Rapport de vérification

## ⚙️ Configuration

### Paramètres utilisateur
Modifiez `settings.json` pour personnaliser :
- Langue (fr/en)
- Unités (SI/Impérial)
- Thème de l'interface
- Chemins par défaut

### Normes de calcul
Les normes sont configurables dans :
- `load_combinations.json` : Combinaisons d'actions
- `chinese_standard.py` : Implémentation des normes GB

## 🔧 Développement

### Architecture
Le logiciel suit une architecture modulaire :
- **Vue** : Interface Qt/PyQt6 (`ui/`)
- **Modèle** : Données structurelles (`structural_model.py`)
- **Contrôleur** : Logique métier (`moteur_calculations.py`)

### Ajouter une norme
1. Créez un fichier `nom_norme.py`
2. Implémentez les classes de calcul selon le modèle `chinese_standard.py`
3. Mettez à jour `language_manager.py` pour les traductions

## 🛡️ Sécurité

⚠️ **Important** : Ne jamais commiter de tokens ou mots de passe.

Créez un fichier `.env` local (non versionné) :
```bash
# .env
GITHUB_TOKEN=votre_token_ici
```

Et ajoutez-le au `.gitignore` :
```
.env
dist/
build/
__pycache__/
env/
```

## 📄 Licence

Projet open source - Voir le fichier LICENSE pour plus de détails.

## 👤 Auteur

**Williamsatse** - [@Williamsatse](https://github.com/Williamsatse)

---
*Développé avec Python 🐍 pour les ingénieurs du BTP* 🏗️
