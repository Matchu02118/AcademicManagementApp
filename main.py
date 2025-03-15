import sys
import csv
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6 import uic

class main(QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi("UI/window.ui", self) 
        
        # Start at 'Home' tab
        self.tabWidget.setCurrentIndex(0)
        
        self.load_csv_to_table("csv/ExamSchedule-ESTORGA.csv", self.classSchedTable) 
        self.load_csv_to_table("csv/ExamSchedule-ESTORGA.csv", self.examSchedTable) 

    def load_csv_to_table(self, file_path, table_widget):
        """Loads CSV data into a QTableWidget"""
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

app = QApplication(sys.argv)
window = main()
window.show()
sys.exit(app.exec())
