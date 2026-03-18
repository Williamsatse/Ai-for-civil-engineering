# language_manager.py
"""
Gestionnaire de langue — Singleton global pour Him Structural.

Usage :
    from language_manager import tr, set_language, get_language, register_language_callback

    # Traduire une clé
    label = tr("menu_file_save")

    # Changer la langue (déclenche tous les callbacks enregistrés)
    set_language("en")   # "fr" | "en" | "zh"

    # S'abonner aux changements de langue
    register_language_callback(my_widget.retranslate_ui)
"""

from translations import TRANSLATIONS

# ──────────────────────────────────────────────────────────────────────────────
# Langue courante (défaut : français)
# ──────────────────────────────────────────────────────────────────────────────
_current_language: str = "fr"

# Liste des callbacks à appeler lors d'un changement de langue
_callbacks: list = []


# ──────────────────────────────────────────────────────────────────────────────
# API publique
# ──────────────────────────────────────────────────────────────────────────────

def get_language() -> str:
    """Retourne le code de la langue courante ('fr', 'en' ou 'zh')."""
    return _current_language


def set_language(lang_code: str) -> None:
    """
    Change la langue courante et notifie tous les widgets abonnés.
    lang_code : 'fr' | 'en' | 'zh'
    """
    global _current_language
    if lang_code not in ("fr", "en", "zh"):
        raise ValueError(f"Langue non supportée : {lang_code!r}. Utilisez 'fr', 'en' ou 'zh'.")
    _current_language = lang_code
    _notify_all()


def tr(key: str, *args) -> str:
    """
    Traduit une clé dans la langue courante.
    Chaîne de substitution optionnelle : tr("status_saved", filename)
    Fallback : fr → en → clé brute
    """
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key  # clé inconnue → retourne la clé

    text = (
        entry.get(_current_language)
        or entry.get("fr")
        or entry.get("en")
        or key
    )

    # Substitution de paramètres positionnels (style .format)
    if args:
        try:
            text = text.format(*args)
        except (IndexError, KeyError):
            pass

    return text


def register_language_callback(callback) -> None:
    """
    Enregistre un callable qui sera invoqué sans argument lorsque
    la langue change.  Évite les doublons.
    """
    if callback not in _callbacks:
        _callbacks.append(callback)


def unregister_language_callback(callback) -> None:
    """Désenregistre un callback (utile quand un widget est détruit)."""
    if callback in _callbacks:
        _callbacks.remove(callback)


# ──────────────────────────────────────────────────────────────────────────────
# Interne
# ──────────────────────────────────────────────────────────────────────────────

def _notify_all() -> None:
    """Appelle tous les callbacks enregistrés (supprime les morts)."""
    dead = []
    for cb in list(_callbacks):
        try:
            cb()
        except Exception:
            dead.append(cb)
    for cb in dead:
        _callbacks.remove(cb)