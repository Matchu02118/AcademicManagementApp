import sys
import csv
import pandas as pd
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QHeaderView, QListWidgetItem, QDialog, QLineEdit, QPushButton, QVBoxLayout, QWidget
from PyQt6 import uic
import os
import json

class LoginPage(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("UI/userSelection.ui", self)
        self.login_button.clicked.connect(self.check_login)
        self.create_account_button.clicked.connect(self.create_account)
        self.logged_in_username = None  # Add this line

    def check_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if self.validate_credentials(username, password):
            self.logged_in_username = username  # Store the username
            self.accept()
        else:
            self.username_input.clear()
            self.password_input.clear()

    def create_account(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if username and password:
            self.save_credentials(username, password)
            self.username_input.clear()
            self.password_input.clear()

    def validate_credentials(self, username, password):
        if os.path.exists("credentials.json"):
            with open("credentials.json", "r") as file:
                credentials = json.load(file)
                return credentials.get(username) == password
        return False

    def save_credentials(self, username, password):
        credentials = {}
        if os.path.exists("credentials.json"):
            with open("credentials.json", "r") as file:
                credentials = json.load(file)
        credentials[username] = password
        with open("credentials.json", "w") as file:
            json.dump(credentials, file)

class main(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username

        uic.loadUi("UI/window.ui", self) 
        
        self.tabWidget.setCurrentIndex(0)

        # Connect buttons to functions
        self.addNoteButton.clicked.connect(self.add_note)
        self.deleteNoteButton.clicked.connect(self.delete_note)
        self.addSchedButton.clicked.connect(self.open_schedule_input)
        self.removeSchedButton.clicked.connect(self.delete_schedule)
        self.tableWidget.itemChanged.connect(self.update_schedule)

        # Load initial data
        self.load_csv_to_table(f"csv/{self.username}_ExamSchedule.csv", self.tableWidget)
        self.load_notes()

    def load_csv_to_table(self, file_path, table_widget):
        self.file_path = file_path
        if not os.path.exists(file_path):
            return

        df = pd.read_csv(file_path)
        if df.empty:
            return

        table_widget.setRowCount(len(df))
        table_widget.setColumnCount(len(df.columns))
        table_widget.setHorizontalHeaderLabels(df.columns)

        for row_idx, row in df.iterrows():
            for col_idx, cell in enumerate(row):
                table_widget.setItem(row_idx, col_idx, QTableWidgetItem(str(cell)))

    def open_schedule_input(self):
        dialog = ScheduleInputDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            schedule = dialog.get_schedule()
            if schedule:
                row_position = self.tableWidget.rowCount()
                self.tableWidget.insertRow(row_position)
                for col, data in enumerate(schedule):
                    self.tableWidget.setItem(row_position, col, QTableWidgetItem(data))
                self.save_schedule()

    def delete_schedule(self):
        selected_items = self.tableWidget.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            self.tableWidget.removeRow(item.row())
        self.save_schedule()

    def update_schedule(self, item):
        self.save_schedule()

    def save_schedule(self):
        # Save the table data to CSV
        row_count = self.tableWidget.rowCount()
        col_count = self.tableWidget.columnCount()
        headers = [self.tableWidget.horizontalHeaderItem(i).text() for i in range(col_count)]

        data = []
        for row in range(row_count):
            row_data = []
            for col in range(col_count):
                item = self.tableWidget.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)

        df = pd.DataFrame(data, columns=headers)
        df.to_csv(self.file_path, index=False)

    def load_notes(self):
        notes_file = f"notes/{self.username}_notes.json"
        if os.path.exists(notes_file):
            with open(notes_file, "r") as file:
                notes = json.load(file)
                for note in notes:
                    self.listWidget.addItem(QListWidgetItem(note))

    def save_notes(self):
        notes = []
        for index in range(self.listWidget.count()):
            notes.append(self.listWidget.item(index).text())
        notes_file = f"notes/{self.username}_notes.json"
        with open(notes_file, "w") as file:
            json.dump(notes, file)

    # Notes tab functions
    def add_note(self):
        note = self.lineEdit.text()
        if note:
            self.listWidget.addItem(QListWidgetItem(note))
            self.lineEdit.clear()
            self.save_notes()

    def delete_note(self):
        selected_items = self.listWidget.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            self.listWidget.takeItem(self.listWidget.row(item))
        self.save_notes()

class ScheduleInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("UI/scheduleInput.ui", self)

    def get_schedule(self):
        return [
            self.classCodeInput.text(),
            self.timeInput.text(),
            self.dayInput.text(),
            self.roomInput.text()
        ]

app = QApplication(sys.argv)
login = LoginPage()
if login.exec() == QDialog.DialogCode.Accepted:
    window = main(login.logged_in_username)  # Pass the stored username
    window.show()
    sys.exit(app.exec())
