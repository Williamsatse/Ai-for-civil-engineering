# ui/load_combinations_dialog.py
"""
Dialogue Load Combinations — Interface identique à Robot Structural
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QMessageBox, QHeaderView,
    QDoubleSpinBox, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class LoadCombinationsDialog(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("Load Combinations")
        self.resize(1280, 720)
        self.setMinimumWidth(1150)

        self.setStyleSheet("""
            QDialog { background: #18181b; color: #e0e0e0; }
            QTableWidget { 
                background: #1f1f2e; 
                gridline-color: #333; 
                alternate-background-color: #25253a;
                selection-background-color: #0078d7;
            }
            QHeaderView::section { 
                background: #25253a; 
                padding: 8px; 
                font-weight: bold; 
            }
            QPushButton { 
                padding: 10px 20px; 
                border-radius: 6px; 
                font-size: 13px; 
                font-weight: bold; 
            }
        """)

        self._build_ui()
        self._populate_table()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Titre
        title = QLabel("Load Combinations")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        layout.addWidget(title)

        # Boutons haut
        top = QHBoxLayout()
        import_btn = QPushButton("Importer du Code de Conception")
        import_btn.setStyleSheet("background: #334155;")
        import_btn.clicked.connect(self._import_code)

        delete_all_btn = QPushButton("Tout Supprimer")
        delete_all_btn.setStyleSheet("background: #ef4444; color: white;")
        delete_all_btn.clicked.connect(self._delete_all)

        add_btn = QPushButton("Ajouter une Ligne")
        add_btn.setStyleSheet("background: #0078d7; color: white;")
        add_btn.clicked.connect(self._add_row)

        top.addWidget(import_btn)
        top.addStretch()
        top.addWidget(delete_all_btn)
        top.addWidget(add_btn)
        layout.addLayout(top)

        # Tableau
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        headers = ["ID", "Nom", "Dead Load", "Live Load", "Wind Load", "Roof Load",
                   "Rain Load", "Snow Load", "Earthquake Load", "Self Weight Load",
                   "Criteria", " "]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)   # Nom large
        self.table.horizontalHeader().setSectionResizeMode(11, QHeaderView.ResizeToContents)  # Delete
        self.table.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Bouton Sauvegarder
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        save_btn = QPushButton("💾 Sauvegarder")
        save_btn.setFixedHeight(52)
        save_btn.setStyleSheet("background: #22c55e; font-size: 15px;")
        save_btn.clicked.connect(self._save)
        save_layout.addWidget(save_btn)
        layout.addLayout(save_layout)

    def _populate_table(self):
        self.table.setRowCount(0)
        for comb in self.main_window.load_combinations:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # ID (non éditable)
            id_item = QTableWidgetItem(str(comb["id"]))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, id_item)

            # Nom
            self.table.setItem(row, 1, QTableWidgetItem(comb["name"]))

            # Coefficients (QDoubleSpinBox)
            for i, key in enumerate(["dead", "live", "wind", "roof", "rain", "snow", "earthquake", "selfweight"]):
                spin = QDoubleSpinBox()
                spin.setRange(0.0, 10.0)
                spin.setDecimals(2)
                spin.setSingleStep(0.05)
                spin.setValue(comb.get(key, 1.0))
                spin.setStyleSheet("background: #1f1f2e; color: white;")
                self.table.setCellWidget(row, i + 2, spin)

            # Criteria
            combo = QComboBox()
            combo.addItems(["Force", "SLS", "ULS"])
            combo.setCurrentText(comb.get("criteria", "Force"))
            self.table.setCellWidget(row, 10, combo)

            # Bouton supprimer
            del_btn = QPushButton("🗑")
            del_btn.setFixedWidth(45)
            del_btn.setStyleSheet("background: #ef4444; color: white;")
            del_btn.clicked.connect(lambda _, r=row: self._delete_row(r))
            self.table.setCellWidget(row, 11, del_btn)

    def _add_row(self):
        new_id = len(self.main_window.load_combinations) + 1
        new_comb = {
            "id": new_id,
            "name": f"Load Combination {new_id}",
            "dead": 1.35, "live": 1.5, "wind": 1.0, "roof": 1.0,
            "rain": 1.0, "snow": 1.5, "earthquake": 1.0, "selfweight": 1.0,
            "criteria": "Force"
        }
        self.main_window.load_combinations.append(new_comb)
        self._populate_table()

    def _delete_row(self, row):
        if QMessageBox.question(self, "Confirmation", "Supprimer cette combinaison ?") == QMessageBox.Yes:
            self.table.removeRow(row)
            del self.main_window.load_combinations[row]
            self._populate_table()

    def _delete_all(self):
        if QMessageBox.question(self, "Attention", "Tout supprimer ?\nAction irréversible.", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.main_window.load_combinations.clear()
            self._populate_table()

    def _import_code(self):
        QMessageBox.information(self, "Import", "Fonctionnalité Eurocode / ASCE bientôt disponible.")

    def _save(self):
        # Mise à jour des données depuis le tableau
        for row in range(self.table.rowCount()):
            comb = self.main_window.load_combinations[row]
            comb["name"] = self.table.item(row, 1).text()

            for i, key in enumerate(["dead", "live", "wind", "roof", "rain", "snow", "earthquake", "selfweight"]):
                spin = self.table.cellWidget(row, i + 2)
                comb[key] = spin.value()

            criteria_combo = self.table.cellWidget(row, 10)
            comb["criteria"] = criteria_combo.currentText()

        self.main_window.save_combinations_to_file()
        QMessageBox.information(self, "Succès", f"{len(self.main_window.load_combinations)} combinaison(s) sauvegardée(s).")
        self.accept()