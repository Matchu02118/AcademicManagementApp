import sys
import csv
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QHeaderView, QListWidgetItem
from PyQt6 import uic

class main(QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi("UI/window.ui", self) 
        
        # Start at Home tab
        self.tabWidget.setCurrentIndex(0)

        # Connect buttons to functions
        self.addNoteButton.clicked.connect(self.add_note)
        self.deleteNote.clicked.connect(self.delete_note)
        self.addSchedButton.clicked.connect(self.add_schedule)
        self.removeSchedButton.clicked.connect(self.delete_schedule)

    def load_csv_to_table(self, file_path, table_widget):
        with open(file_path, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            data = list(reader)

            if not data:
                return

            table_widget.setRowCount(len(data) - 1)
            table_widget.setColumnCount(len(data[0]))
            
            table_widget.setHorizontalHeaderLabels(data[0])
            for row_idx, row in enumerate(data[1:]):
                for col_idx, cell in enumerate(row):
                    table_widget.setItem(row_idx, col_idx, QTableWidgetItem(cell))

    def add_note(self):
        note = self.lineEdit.text()
        if note:
            self.listWidget.addItem(QListWidgetItem(note))
            self.lineEdit.clear()

    def delete_note(self):
        selected_items = self.listWidget.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            self.listWidget.takeItem(self.listWidget.row(item))

    def add_schedule(self):
        schedule = self.scheduleInput.text()
        if schedule:
            row_position = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row_position)
            self.tableWidget.setItem(row_position, 0, QTableWidgetItem(schedule))
            self.scheduleInput.clear()

    def delete_schedule(self):
        selected_items = self.tableWidget.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            self.tableWidget.removeRow(item.row())

app = QApplication(sys.argv)
window = main()
window.show()
sys.exit(app.exec())
