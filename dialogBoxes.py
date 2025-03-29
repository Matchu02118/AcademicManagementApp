from PyQt6.QtWidgets import (
    QDialog, QLineEdit, QVBoxLayout, QLabel, QRadioButton, QButtonGroup, QPushButton, QHBoxLayout, QTextEdit, QSizePolicy
)
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6 import uic
import sqlite3

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
        self.conn = sqlite3.connect("database/user_accounts.db")
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

class NoteInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter a Note:")

        self.noteTitle = QLineEdit(self)
        self.noteInput = QTextEdit(self)
        self.noteInput.setMinimumSize(320, 240)   

        # Layout for the dialog
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Note Title:"))
        layout.addWidget(self.noteTitle)
        layout.addWidget(QLabel("Enter your note:"))
        layout.addWidget(self.noteInput)

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
        
        self.noteInput.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def get_note(self):
        """Return the note title and content."""
        return self.noteTitle.text(), self.noteInput.toPlainText()
