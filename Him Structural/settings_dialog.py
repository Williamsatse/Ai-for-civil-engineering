# settings_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QGroupBox, QFormLayout, QComboBox, QCheckBox, QLabel,
    QDoubleSpinBox, QSpinBox, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from language_manager import tr, set_language, get_language, register_language_callback, unregister_language_callback


class SettingsDialog(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self._build_ui()
        register_language_callback(self.retranslate_ui)

    def closeEvent(self, event):
        unregister_language_callback(self.retranslate_ui)
        super().closeEvent(event)

    def _build_ui(self):
        self.setWindowTitle(tr("settings_title"))
        self.resize(940, 680)
        self.setMinimumWidth(900)

        self.setStyleSheet("""
            QDialog { background: #18181b; color: #e0e0e0; }
            QTabWidget::pane { border: 1px solid #333; background: #1f1f2e; }
            QTabBar::tab { padding: 11px 24px; background: #25253a;
                           border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: #0078d7; color: white; }
            QGroupBox { font-weight: bold; border: 1px solid #444; margin-top: 14px; }
            QGroupBox::title { left: 12px; padding: 0 6px; }
            QLabel { color: #e0e0e0; }
            QComboBox { background: #25253a; color: #e0e0e0; border: 1px solid #555;
                        border-radius: 4px; padding: 4px 8px; min-height: 28px; }
            QComboBox::drop-down { border: none; }
            QSpinBox, QDoubleSpinBox { background: #25253a; color: #e0e0e0;
                border: 1px solid #555; border-radius: 4px; padding: 4px; }
            QCheckBox { color: #e0e0e0; }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(18)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        main_layout.addWidget(self.tabs)

        self._create_units_tab()
        self._create_conversion_tab()
        self._create_output_tab()
        self._create_language_tab()

        # Bouton Sauvegarder
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_save = QPushButton()
        self.btn_save.setFixedHeight(48)
        self.btn_save.setStyleSheet("""
            QPushButton { background: #0078d7; font-size: 15px; font-weight: bold;
                          border-radius: 8px; color: white; }
            QPushButton:hover { background: #1084e0; }
        """)
        self.btn_save.clicked.connect(self._save_and_apply)
        btn_layout.addWidget(self.btn_save)
        main_layout.addLayout(btn_layout)

        self.retranslate_ui()

    # ─── ONGLET UNITÉS ────────────────────────────────────────────────────────
    def _create_units_tab(self):
        self._tab_units = QWidget()
        layout = QFormLayout(self._tab_units)
        layout.setSpacing(14)

        self.unit_system = QComboBox()
        self.unit_system.addItems(["Metric", "Impérial"])
        self.unit_system.setCurrentText(self.main_window.settings.get("unit_system", "Metric"))

        self.length_unit = QComboBox()
        self.length_unit.addItems(["mm", "cm", "m"])
        self.length_unit.setCurrentText(self.main_window.settings.get("length_unit", "mm"))

        self.force_unit = QComboBox()
        self.force_unit.addItems(["kN", "N"])
        self.force_unit.setCurrentText(self.main_window.settings.get("force_unit", "kN"))

        self._row_unit_system = QLabel()
        self._row_length_unit = QLabel()
        self._row_force_unit  = QLabel()
        self._row_moment_unit = QLabel()
        self._lbl_moment_val  = QLabel()
        self._row_section     = QLabel()
        self._lbl_section_val = QLabel()

        layout.addRow(self._row_unit_system, self.unit_system)
        layout.addRow(self._row_length_unit, self.length_unit)
        layout.addRow(self._row_force_unit,  self.force_unit)
        layout.addRow(self._row_moment_unit, self._lbl_moment_val)
        layout.addRow(self._row_section,     self._lbl_section_val)

        self.tabs.addTab(self._tab_units, "")

    # ─── ONGLET CONVERSION ────────────────────────────────────────────────────
    def _create_conversion_tab(self):
        self._tab_convert = QWidget()
        layout = QVBoxLayout(self._tab_convert)

        self._grp_display = QGroupBox()
        f = QFormLayout(self._grp_display)
        self.spin_decimals = QSpinBox()
        self.spin_decimals.setValue(self.main_window.settings.get("decimals", 3))
        self._row_decimals = QLabel()
        f.addRow(self._row_decimals, self.spin_decimals)
        layout.addWidget(self._grp_display)
        layout.addStretch()

        self.tabs.addTab(self._tab_convert, "")

    # ─── ONGLET SORTIE ────────────────────────────────────────────────────────
    def _create_output_tab(self):
        self._tab_output = QWidget()
        layout = QVBoxLayout(self._tab_output)

        self.chk_bmd = QCheckBox()
        self.chk_bmd.setChecked(self.main_window.settings.get("invert_bmd", False))
        layout.addWidget(self.chk_bmd)
        layout.addStretch()

        self.tabs.addTab(self._tab_output, "")

    # ─── ONGLET LANGUE ────────────────────────────────────────────────────────
    def _create_language_tab(self):
        self._tab_lang = QWidget()
        layout = QVBoxLayout(self._tab_lang)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        self._grp_lang = QGroupBox()
        grp_layout = QVBoxLayout(self._grp_lang)
        grp_layout.setSpacing(14)

        # Ligne label + combo
        row = QHBoxLayout()
        self._lbl_language = QLabel()
        self._lbl_language.setFixedWidth(120)
        self.lang_combo = QComboBox()
        self.lang_combo.setFixedWidth(260)
        self.lang_combo.setStyleSheet("""
            QComboBox { font-size: 14px; padding: 6px 12px; min-height: 36px; }
        """)
        # Peupler (les textes seront mis à jour par retranslate_ui)
        self.lang_combo.addItem("", "fr")
        self.lang_combo.addItem("", "en")
        self.lang_combo.addItem("", "zh")

        # Sélectionner la langue courante
        current = get_language()
        idx = {"fr": 0, "en": 1, "zh": 2}.get(current, 0)
        self.lang_combo.setCurrentIndex(idx)

        row.addWidget(self._lbl_language)
        row.addWidget(self.lang_combo)
        row.addStretch()
        grp_layout.addLayout(row)

        # Note explicative
        self._lbl_lang_note = QLabel()
        self._lbl_lang_note.setStyleSheet("color: #888; font-size: 12px;")
        self._lbl_lang_note.setWordWrap(True)
        grp_layout.addWidget(self._lbl_lang_note)

        layout.addWidget(self._grp_lang)
        layout.addStretch()

        self.tabs.addTab(self._tab_lang, "")

    # ─── RETRANSLATION ────────────────────────────────────────────────────────
    def retranslate_ui(self):
        self.setWindowTitle(tr("settings_title"))
        self.btn_save.setText(tr("settings_save_btn"))

        # Onglets
        self.tabs.setTabText(0, tr("settings_tab_units"))
        self.tabs.setTabText(1, tr("settings_tab_convert"))
        self.tabs.setTabText(2, tr("settings_tab_output"))
        self.tabs.setTabText(3, tr("settings_tab_language"))

        # Unités
        self._row_unit_system.setText(tr("settings_unit_system"))
        self._row_length_unit.setText(tr("settings_length_unit"))
        self._row_force_unit.setText(tr("settings_force_unit"))
        self._row_moment_unit.setText(tr("settings_moment_unit"))
        self._lbl_moment_val.setText(tr("settings_moment_fixed"))
        self._row_section.setText(tr("settings_section_unit"))
        self._lbl_section_val.setText(tr("settings_section_fixed"))

        # Conversion
        self._grp_display.setTitle(tr("settings_display"))
        self._row_decimals.setText(tr("settings_decimals"))

        # Sortie
        self.chk_bmd.setText(tr("settings_invert_bmd"))

        # Langue
        self._grp_lang.setTitle(tr("settings_language_title"))
        self._lbl_language.setText(tr("settings_language_label"))
        self._lbl_lang_note.setText(tr("settings_language_note"))

        # Mettre à jour les textes du combo langue (sans changer la sélection)
        cur_idx = self.lang_combo.currentIndex()
        for i, key in enumerate(("lang_fr", "lang_en", "lang_zh")):
            self.lang_combo.setItemText(i, tr(key))
        self.lang_combo.setCurrentIndex(cur_idx)

    # ─── SAUVEGARDE ───────────────────────────────────────────────────────────
    def _save_and_apply(self):
        new_settings = {
            "unit_system": self.unit_system.currentText(),
            "length_unit": self.length_unit.currentText(),
            "force_unit":  self.force_unit.currentText(),
            "decimals":    self.spin_decimals.value(),
            "invert_bmd":  self.chk_bmd.isChecked(),
        }

        # Langue choisie
        lang_code = self.lang_combo.currentData()
        if lang_code and lang_code != get_language():
            new_settings["language"] = lang_code
            set_language(lang_code)   # notifie tous les callbacks
        elif lang_code:
            new_settings["language"] = lang_code

        self.main_window.apply_settings(new_settings)

        QMessageBox.information(
            self,
            tr("settings_success"),
            tr("settings_saved_msg"),
        )
        self.accept()