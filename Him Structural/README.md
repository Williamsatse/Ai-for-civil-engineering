# Him Structural

Logiciel d'analyse structurelle avec interface graphique pour le calcul des structures et poutres.

## Installation

1. Cloner le repository :
```bash
git clone https://github.com/Williamsatse/Ai-for-civil-engineering.git
cd "Ai-for-civil-engineering/Him Structural"
```

2. Créer un environnement virtuel :
```bash
python -m venv env
env\Scripts\activate  # Windows
source env/bin/activate  # Linux/Mac
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Configuration API

### Fichier .env

Créez un fichier `.env` à la racine du dossier `Him Structural` avec votre clé API :

```env
API_KEY=votre_cle_api_ici
```

### Où obtenir la clé API ?

Ce logiciel utilise une API pour certaines fonctionnalités avancées (analyse IA, calculs complexes). 

- Inscrivez-vous sur le site du fournisseur d'API
- Générez votre clé API
- Copiez-la dans le fichier `.env`

### Comment l'API est utilisée dans le code

Le fichier `.env` est lu automatiquement par le module `dotenv` :

```python
from dotenv import load_dotenv
import os

# Chargement des variables d'environnement
load_dotenv()

# Récupération de la clé API
api_key = os.getenv("API_KEY")

# Utilisation dans les requêtes
headers = {"Authorization": f"Bearer {api_key}"}
```

**⚠️ Sécurité :**
- Ne jamais commiter le fichier `.env` dans le repository
- Le fichier `.gitignore` exclut déjà `.env`
- Gardez votre clé API secrète

## Lancement

```bash
python main.py
```

## Fonctionnalités

- 🏗️ Analyse structurelle des poutres et portiques
- 📊 Calcul des réactions d'appui
- 🎨 Interface graphique intuitive (Flet)
- 📐 Support des normes chinoises (Chinese Standard)
- 💾 Sauvegarde et chargement des projets

## Structure du projet

```
Him Structural/
├── main.py              # Point d'entrée principal
├── canvas.py            # Canvas de dessin
├── chinese_standard.py  # Normes structurelles chinoises
├── data_manager.py      # Gestion des données
├── language_manager.py  # Multi-langue
├── moteur_calculations.py # Moteur de calcul
├── section_manager.py   # Gestion des sections
├── settings_dialog.py   # Dialogues de paramètres
├── structural_model.py  # Modèle structurel
├── translations.py      # Traductions
├── icons/               # Icônes de l'interface
├── models/              # Modèles de calcul
├── ui/                  # Composants UI
└── calculation/         # Modules de calcul
```

## Documentation

- `anastruct.ipynb` - Exemples avec la bibliothèque anastruct
- `pynite.ipynb` - Exemples avec la bibliothèque pynite

## Licence

Projet éducatif pour l'ingénierie civile.