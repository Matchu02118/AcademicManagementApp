import sys
import csv
import pandas as pd
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QHeaderView, QListWidgetItem, QDialog, QLineEdit, QPushButton, QVBoxLayout, QWidget, QMessageBox, QLabel, QHBoxLayout, QRadioButton, QButtonGroup
from PyQt6 import uic
import os
import json
import sqlite3
from PyQt6.QtGui import QFont  # Add this import for setting bold font

class LoginPage(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("UI/userSelection.ui", self)
        self.login_button.clicked.connect(self.login)
        self.create_account_button.clicked.connect(self.registerPage)
        self.logged_in_username = None

        # Initialize SQLite databases
        self.init_user_db()
        self.init_schedule_db()

    def init_user_db(self):
        self.conn = sqlite3.connect("user_accounts.db")
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def init_schedule_db(self):
        conn = sqlite3.connect("database/schedules.db")
        cursor = conn.cursor()

        # Ensure the schedule table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                class_code TEXT NOT NULL,
                time TEXT NOT NULL,
                day TEXT NOT NULL,
                room TEXT NOT NULL,
                schedule_type TEXT NOT NULL,
                FOREIGN KEY (username) REFERENCES users (username)
            )
        """)

        cursor.execute("PRAGMA table_info(schedule)")
        columns = [column[1] for column in cursor.fetchall()]
        if "schedule_type" not in columns:
            cursor.execute("ALTER TABLE schedule ADD COLUMN schedule_type TEXT NOT NULL DEFAULT 'Class'")

        conn.commit()
        conn.close()
        
    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if self.validate_credentials(username, password):
            self.logged_in_username = username
            self.accept()
        else:
            QMessageBox.warning(self, "Login Failed", "Incorrect username or password. Please try again.")
            self.username_input.clear()
            self.password_input.clear()

    def registerPage(self):
        register_dialog = RegisterPage(self.conn, self)
        register_dialog.exec()

    def validate_credentials(self, username, password):
        cursor = self.conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        return result is not None and result[0] == password

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)

class RegisterPage(QDialog):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        uic.loadUi("UI/register.ui", self)
        self.conn = conn
        self.createAccButton.clicked.connect(self.create_account)

    def create_account(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if username and password:
            if self.save_credentials(username, password):
                QMessageBox.information(self, "Account Created", "Your account has been created successfully.")
                self.accept()
            else:
                QMessageBox.warning(self, "Account Creation Failed", "An account with this username already exists.")
        else:
            QMessageBox.warning(self, "Invalid Input", "Please enter both a username and a password.")

    def save_credentials(self, username, password):
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

class main(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username

        uic.loadUi("UI/window.ui", self)

        self.tabWidget.setCurrentIndex(0)

        # Note Tab buttons
        self.addNoteButton.clicked.connect(self.addNote)
        
        # Schedule Tab buttons
        self.addSchedButton.clicked.connect(self.addSchedule)
        self.removeSchedButton.clicked.connect(self.deleteSchedule)
        self.viewSchedButton.clicked.connect(self.viewSchedule)
        self.updateSchedButton.clicked.connect(self.updateSchedule)

    def addNote(self):
        QMessageBox.information(self, "Add Note", "This feature is under construction. A popup dialog will be implemented here.")

    def open_delete_note_dialog(self):
        QMessageBox.information(self, "Delete Note", "This feature is under construction. A popup dialog will be implemented here.")

    def addSchedule(self):
        dialog = ScheduleInputDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            schedule_data = dialog.get_schedule()
            if self.save_schedule(schedule_data):
                QMessageBox.information(self, "Success", "Schedule added successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to add schedule. Please try again.")

    def save_schedule(self, schedule_data):
        try:
            conn = sqlite3.connect("database/schedules.db")  # Connect to schedules.db
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO schedule (username, class_code, time, day, room, schedule_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (self.username, *schedule_data))  # Insert schedule data
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
    
    def deleteSchedule(self):
        selected_row = self.scheduleTableWidget.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a schedule to delete.")
            return

        # Get the class code of the selected schedule
        class_code_item = self.scheduleTableWidget.item(selected_row, 0)
        if not class_code_item:
            QMessageBox.warning(self, "Error", "Failed to retrieve the selected schedule.")
            return

        class_code = class_code_item.text()

        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the schedule for class '{class_code}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                conn = sqlite3.connect("database/schedules.db")  # Connect to schedules.db
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM schedule 
                    WHERE username = ? AND class_code = ?
                """, (self.username, class_code))  # Delete the selected schedule
                conn.commit()
                conn.close()

                # Remove the row from the table widget
                self.scheduleTableWidget.removeRow(selected_row)

                QMessageBox.information(self, "Success", "Schedule deleted successfully.")
            except sqlite3.Error as e:
                QMessageBox.warning(self, "Error", f"Failed to delete schedule: {e}")
        
    def viewSchedule(self):
        dialog = ViewScheduleDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            schedule_type = dialog.get_selected_schedule_type()

            try:
                conn = sqlite3.connect("database/schedules.db")
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT class_code, time, day, room 
                    FROM schedule 
                    WHERE username = ? AND schedule_type = ?
                """, (self.username, schedule_type))
                schedules = cursor.fetchall()
                conn.close()

                # Clear the table widget before populating
                self.scheduleTableWidget.setColumnCount(4)
                self.scheduleTableWidget.setHorizontalHeaderLabels(["Class Code", "Time", "Day", "Room"])  # Removed "Type"

                header_font = QFont()
                header_font.setBold(True)
                for i in range(4):  # Updated range
                    self.scheduleTableWidget.horizontalHeaderItem(i).setFont(header_font)

                # Populate the table with schedule data
                self.scheduleTableWidget.setRowCount(0)  # Clear existing rows
                for row_idx, schedule in enumerate(schedules):
                    self.scheduleTableWidget.insertRow(row_idx)
                    for col_idx, value in enumerate(schedule):
                        self.scheduleTableWidget.setItem(row_idx, col_idx, QTableWidgetItem(value))

                if not schedules:
                    QMessageBox.information(self, "No Schedule", f"No {schedule_type} schedules found.")
            except sqlite3.Error as e:
                QMessageBox.warning(self, "Error", f"Failed to fetch schedules: {e}")
    
    def updateSchedule(self):
        selected_row = self.scheduleTableWidget.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a schedule to update.")
            return

        # Get the current schedule details from the selected row
        class_code = self.scheduleTableWidget.item(selected_row, 0).text()
        time = self.scheduleTableWidget.item(selected_row, 1).text()
        day = self.scheduleTableWidget.item(selected_row, 2).text()
        room = self.scheduleTableWidget.item(selected_row, 3).text()
        
        try:
            conn = sqlite3.connect("database/schedules.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT schedule_type 
                FROM schedule 
                WHERE username = ? AND class_code = ? AND time = ? AND day = ? AND room = ?
            """, (self.username, class_code, time, day, room))
            schedule_type = cursor.fetchone()[0]
            conn.close()
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Error", f"Failed to fetch schedule type: {e}")
            return

        # Open the update dialog
        dialog = UpdateScheduleDialog([class_code, time, day, room, schedule_type], self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_schedule = dialog.get_updated_schedule()

            # Update the schedule in the database
            try:
                conn = sqlite3.connect("database/schedules.db")
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE schedule 
                    SET class_code = ?, time = ?, day = ?, room = ?, schedule_type = ?
                    WHERE username = ? AND class_code = ? AND time = ? AND day = ? AND room = ?
                """, (*updated_schedule, self.username, class_code, time, day, room))
                conn.commit()
                conn.close()

                # Update the table widget
                self.scheduleTableWidget.item(selected_row, 0).setText(updated_schedule[0])
                self.scheduleTableWidget.item(selected_row, 1).setText(updated_schedule[1])
                self.scheduleTableWidget.item(selected_row, 2).setText(updated_schedule[2])
                self.scheduleTableWidget.item(selected_row, 3).setText(updated_schedule[3])

                QMessageBox.information(self, "Success", "Schedule updated successfully.")
            except sqlite3.Error as e:
                QMessageBox.warning(self, "Error", f"Failed to update schedule: {e}")

class ScheduleInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Schedule Input")

        self.classCodeInput = QLineEdit(self)
        self.timeInput = QLineEdit(self)
        self.dayInput = QLineEdit(self)
        self.roomInput = QLineEdit(self)

        # Radio buttons for schedule type
        self.classRadioButton = QRadioButton("Class", self)
        self.examRadioButton = QRadioButton("Exam", self)
        self.classRadioButton.setChecked(True)  # Default to "Class"

        # Group the radio buttons to make them mutually exclusive
        self.scheduleTypeGroup = QButtonGroup(self)
        self.scheduleTypeGroup.addButton(self.classRadioButton)
        self.scheduleTypeGroup.addButton(self.examRadioButton)

        # Layout for the dialog
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Class Code:"))
        layout.addWidget(self.classCodeInput)
        layout.addWidget(QLabel("Time:"))
        layout.addWidget(self.timeInput)
        layout.addWidget(QLabel("Day:"))
        layout.addWidget(self.dayInput)
        layout.addWidget(QLabel("Room:"))
        layout.addWidget(self.roomInput)

        # Add radio buttons to layout
        layout.addWidget(QLabel("Schedule Type:"))
        layout.addWidget(self.classRadioButton)
        layout.addWidget(self.examRadioButton)

        # Create buttons
        self.okButton = QPushButton("Save", self)
        self.cancelButton = QPushButton("Cancel", self)
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        # Add buttons to layout
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout.addLayout(buttonLayout)

        self.setLayout(layout)

    def get_schedule(self):
        schedule_type = "Class" if self.classRadioButton.isChecked() else "Exam"
        return [
            self.classCodeInput.text(),
            self.timeInput.text(),
            self.dayInput.text(),
            self.roomInput.text(),
            schedule_type
        ]

class ViewScheduleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Schedule Type")

        # Radio buttons for schedule type
        self.classRadioButton = QRadioButton("Class", self)
        self.examRadioButton = QRadioButton("Exam", self)
        self.classRadioButton.setChecked(True)  # Default to "Class"

        # Group the radio buttons to make them mutually exclusive
        self.scheduleTypeGroup = QButtonGroup(self)
        self.scheduleTypeGroup.addButton(self.classRadioButton)
        self.scheduleTypeGroup.addButton(self.examRadioButton)

        # Layout for the dialog
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Select the type of schedule to view:"))
        layout.addWidget(self.classRadioButton)
        layout.addWidget(self.examRadioButton)

        # Create buttons
        self.okButton = QPushButton("OK", self)
        self.cancelButton = QPushButton("Cancel", self)
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        # Add buttons to layout
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout.addLayout(buttonLayout)

        self.setLayout(layout)

    def get_selected_schedule_type(self):
        return "Class" if self.classRadioButton.isChecked() else "Exam"

class UpdateScheduleDialog(QDialog):
    def __init__(self, schedule_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Schedule")

        # Unpack schedule data
        self.class_code, self.time, self.day, self.room, self.schedule_type = schedule_data

        # Inputs for schedule details
        self.classCodeInput = QLineEdit(self)
        self.classCodeInput.setText(self.class_code)
        self.timeInput = QLineEdit(self)
        self.timeInput.setText(self.time)
        self.dayInput = QLineEdit(self)
        self.dayInput.setText(self.day)
        self.roomInput = QLineEdit(self)
        self.roomInput.setText(self.room)

        # Radio buttons for schedule type
        self.classRadioButton = QRadioButton("Class", self)
        self.examRadioButton = QRadioButton("Exam", self)
        if self.schedule_type == "Class":
            self.classRadioButton.setChecked(True)
        else:
            self.examRadioButton.setChecked(True)

        # Group the radio buttons
        self.scheduleTypeGroup = QButtonGroup(self)
        self.scheduleTypeGroup.addButton(self.classRadioButton)
        self.scheduleTypeGroup.addButton(self.examRadioButton)

        # Layout for the dialog
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Class Code:"))
        layout.addWidget(self.classCodeInput)
        layout.addWidget(QLabel("Time:"))
        layout.addWidget(self.timeInput)
        layout.addWidget(QLabel("Day:"))
        layout.addWidget(self.dayInput)
        layout.addWidget(QLabel("Room:"))
        layout.addWidget(self.roomInput)

        # Add radio buttons to layout
        layout.addWidget(QLabel("Schedule Type:"))
        layout.addWidget(self.classRadioButton)
        layout.addWidget(self.examRadioButton)

        # Create buttons
        self.okButton = QPushButton("Save", self)
        self.cancelButton = QPushButton("Cancel", self)
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        # Add buttons to layout
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout.addLayout(buttonLayout)

        self.setLayout(layout)

    def get_updated_schedule(self):
        schedule_type = "Class" if self.classRadioButton.isChecked() else "Exam"
        return [
            self.classCodeInput.text(),
            self.timeInput.text(),
            self.dayInput.text(),
            self.roomInput.text(),
            schedule_type
        ]

app = QApplication(sys.argv)
login = LoginPage()
if login.exec() == QDialog.DialogCode.Accepted:
    window = main(login.logged_in_username)
    window.show()
    sys.exit(app.exec())
