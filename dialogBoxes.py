from PyQt6.QtWidgets import (
    QDialog, QLineEdit, QVBoxLayout, QLabel, QRadioButton, QButtonGroup, QPushButton, QHBoxLayout, QTextEdit, QSizePolicy, QDateEdit, QComboBox
)
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6 import uic
from PyQt6.QtGui import QTextCursor
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QDate
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
        with open("styles/scheduleDialogs/scheduleInput.qss", "r") as file:
            qss= file.read()
            
        self.setStyleSheet(qss)
        self.resize(400, 300)
        
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

        # Labels for inputs
        self.classCodeLabel = QLabel("Class Code:")
        self.timeLabel = QLabel("Time:")
        self.dayLabel = QLabel("Day:")
        self.roomLabel = QLabel("Room:")
        self.scheduleTypeLabel = QLabel("Schedule Type:")

        # Layout for the dialog
        layout = QVBoxLayout()
        layout.addWidget(self.classCodeLabel)
        layout.addWidget(self.classCodeInput)
        layout.addWidget(self.timeLabel)
        layout.addWidget(self.timeInput)
        layout.addWidget(self.dayLabel)
        layout.addWidget(self.dayInput)
        layout.addWidget(self.roomLabel)
        layout.addWidget(self.roomInput)

        # Add radio buttons to layout
        layout.addWidget(self.scheduleTypeLabel)
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
        self.layout().setAlignment(self.scheduleTypeLabel, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        
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
        with open("styles/scheduleDialogs/scheduleInput.qss", "r") as file:
            qss= file.read()
            
        self.setStyleSheet(qss)
        self.resize(400, 300)
        
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
        self.classCodeLabel = QLabel("Class Code:")
        self.timeLabel = QLabel("Time:")
        self.dayLabel = QLabel("Day:")
        self.roomLabel = QLabel("Room:")
        self.scheduleTypeLabel = QLabel("Schedule Type:")

        # Layout for the dialog
        layout = QVBoxLayout()
        layout.addWidget(self.classCodeLabel)
        layout.addWidget(self.classCodeInput)
        layout.addWidget(self.timeLabel)
        layout.addWidget(self.timeInput)
        layout.addWidget(self.dayLabel)
        layout.addWidget(self.dayInput)
        layout.addWidget(self.roomLabel)
        layout.addWidget(self.roomInput)

        # Add radio buttons to layout
        layout.addWidget(self.scheduleTypeLabel)
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
        self.layout().setAlignment(self.scheduleTypeLabel, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        
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
        self.resize(800, 640)

        with open("styles/noteDialogs/noteInput.qss", "r") as file:
            qss= file.read()
        
        self.setStyleSheet(qss)
        
        self.noteTitle = QLineEdit(self)
        self.noteInput = QTextEdit(self)
        self.noteInput.setMinimumSize(320, 240)

        # Enable undo/redo functionality
        self.noteInput.setUndoRedoEnabled(True)

        # Connect the textChanged signal to enforce plain text
        self.noteInput.textChanged.connect(self.convertToPlainText)

        self.noteTitleLabel = QLabel("Note Title:")
        self.noteInputLabel = QLabel("Enter your note:")

        # Layout for the dialog
        layout = QVBoxLayout()
        layout.addWidget(self.noteTitleLabel)
        layout.addWidget(self.noteTitle)
        layout.addWidget(self.noteInputLabel)
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
        self.layout().setAlignment(self.noteTitleLabel, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.layout().setAlignment(self.noteInputLabel, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

    def convertToPlainText(self):
        """Convert the content of the QTextEdit to plain text."""
        cursor = self.noteInput.textCursor()
        text = self.noteInput.toPlainText()  
        self.noteInput.blockSignals(True)
        self.noteInput.setPlainText(text)
        self.noteInput.blockSignals(False) 
        cursor.setPosition(cursor.position()) 
        self.noteInput.setTextCursor(cursor)

    def get_note(self):
        """Return the note title and content."""
        return self.noteTitle.text(), self.noteInput.toPlainText()

class EditNoteDialog(QDialog):
    def __init__(self, note_id, title, content, parent=None):
        super().__init__(parent)
        self.note_id = note_id
        self.setWindowTitle("Note")
        self.resize(800, 640)

        with open("styles/noteDialogs/noteInput.qss", "r") as file:
            qss= file.read()
        
        self.setStyleSheet(qss)
        
        # Layout
        layout = QVBoxLayout(self)
        
        # Title Section
        self.titleLineEdit = QLineEdit(self)
        self.titleLineEdit.setText(title)
        layout.addWidget(self.titleLineEdit)

        # Content Section
        self.contentTextEdit = QTextEdit(self)
        self.contentTextEdit.setPlainText(content)

        # Enable undo/redo functionality
        self.contentTextEdit.setUndoRedoEnabled(True)

        layout.addWidget(self.contentTextEdit)

        self.contentTextEdit.textChanged.connect(self.convertToPlainText)

        # Buttons
        self.saveButton = QPushButton("Save", self)
        self.saveButton.clicked.connect(self.saveNote)
        layout.addWidget(self.saveButton)

        self.deleteButton = QPushButton("Delete", self)
        self.deleteButton.clicked.connect(self.deleteNote)
        layout.addWidget(self.deleteButton)

        self.setLayout(layout)

    def convertToPlainText(self):
        """Convert the content of the QTextEdit to plain text."""
        cursor = self.contentTextEdit.textCursor()
        cursor_position = cursor.position()  # Save the current cursor position
        text = self.contentTextEdit.toPlainText()
        self.contentTextEdit.blockSignals(True)  # Prevent recursive signal triggering
        self.contentTextEdit.setPlainText(text)  # Set the plain text back
        self.contentTextEdit.blockSignals(False)  # Re-enable signals
        cursor.setPosition(cursor_position)  # Restore the cursor position
        self.contentTextEdit.setTextCursor(cursor)

    def saveNote(self):
        """Save the updated note."""
        title = self.titleLineEdit.text().strip()
        content = self.contentTextEdit.toPlainText().strip()
        if not title or not content:
            QMessageBox.warning(self, "Invalid Input", "Both title and content are required.")
            return
        self.accept()  # Close the dialog and return success

    def deleteNote(self):
        """Delete the note."""
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this note?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.done(2)  # Return a custom code for deletion
            
class AddAssignmentDialog(QDialog):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Assignment")
        with open("styles/assignmentDialogs/assignmentInput.qss", "r") as file:
            qss = file.read()
        self.setStyleSheet(qss)

        self.username = username

        # Removed subjectName
        self.assignmentName = QLineEdit(self)
        self.assignmentDetails = QTextEdit(self)
        self.dueDate = QDateEdit(self)
        self.dueDate.setCalendarPopup(True)
        self.dueDate.setDate(QDate.currentDate())  # Set to the current date

        # Dropdown for class codes and schedule types
        self.classDropdown = QComboBox(self)
        self.load_class_codes()

        # Layout
        layout = QVBoxLayout()
        # Removed subjectName label and input
        layout.addWidget(QLabel("Assignment Title:"))
        layout.addWidget(self.assignmentName)
        layout.addWidget(QLabel("Assignment Details:"))
        layout.addWidget(self.assignmentDetails)
        layout.addWidget(QLabel("Due Date:"))
        layout.addWidget(self.dueDate)
        layout.addWidget(QLabel("Class Code and Type:"))
        layout.addWidget(self.classDropdown)

        # Buttons
        self.okButton = QPushButton("Save", self)
        self.cancelButton = QPushButton("Cancel", self)
        self.okButton.clicked.connect(self.save_assignment)
        self.cancelButton.clicked.connect(self.reject)

        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout.addLayout(buttonLayout)

        self.setLayout(layout)

    def load_class_codes(self):
        """Load class codes and schedule types from schedules.db."""
        try:
            conn = sqlite3.connect("database/schedules.db")
            cursor = conn.cursor()
            cursor.execute("SELECT class_code, schedule_type FROM schedule WHERE username = ?", (self.username,))
            for class_code, schedule_type in cursor.fetchall():
                self.classDropdown.addItem(f"{class_code} ({schedule_type})")
            conn.close()
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Error", f"Failed to load class codes: {e}")

    def save_assignment(self):
        """Save the assignment to the database."""
        # Removed subjectName from the save logic
        title = self.assignmentName.text().strip()
        details = self.assignmentDetails.toPlainText().strip()
        due_date = self.dueDate.date().toString("yyyy-MM-dd")
        class_code = self.classDropdown.currentText().split(" ")[0]

        if not title or not details:
            QMessageBox.warning(self, "Invalid Input", "All fields are required.")
            return

        try:
            conn = sqlite3.connect("database/assignments.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO assignments (username, title, class_code, details, due)
                VALUES (?, ?, ?, ?, ?)
            """, (self.username, title, details, due_date, class_code))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Success", "Assignment added successfully.")
            self.accept()
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Error", f"Failed to save assignment: {e}")