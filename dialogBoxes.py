from PyQt6.QtWidgets import *
from PyQt6.QtWidgets import *
from PyQt6 import uic
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import sqlite3
import sys

class LoginPage(QDialog):
    def __init__(self, user_db_path):
        super().__init__()
        uic.loadUi("UI/login.ui", self)
        self.login_button.clicked.connect(self.login)
        self.create_account_button.clicked.connect(self.registerPage)
        self.logged_in_username = None
        self.conn = sqlite3.connect(user_db_path)  # Initialize the database connection

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
        register_dialog = RegisterPage(self.conn, self)  # Pass the connection to RegisterPage
        register_dialog.exec()

    def validate_credentials(self, username, password):
        cursor = self.conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        return result is not None and result[0] == password

    def closeEvent(self, event):
        self.conn.close()  # Close the database connection
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
        self.classCodeLabel = QLabel("Subject:")
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
        self.classCodeLabel = QLabel("Subject:")
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
        self.setMaximumSize(800, 640)
        self.setMinimumSize(800, 640)

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
        current_text = self.noteInput.toPlainText()
        cursor = self.noteInput.textCursor()
        cursor_position = cursor.position()

        # Only update the text if it has changed
        if self.noteInput.toPlainText() != current_text:
            self.noteInput.blockSignals(True)  # Prevent recursive signal triggering
            self.noteInput.setPlainText(current_text)  # Set the plain text back
            self.noteInput.blockSignals(False)  # Re-enable signals

        # Restore the cursor position
        cursor.setPosition(cursor_position)
        self.noteInput.setTextCursor(cursor)
        
    def get_note(self):
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
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("ui/assignment.ui", self)
        self.load_subjects()
        self.setWindowTitle("Add Assignment")
        
    def assignment_input(self):
        subjectName = self.classCodes.currentText()
        assignmentTitle = self.title.text()
        assignmentDetails = self.details.toPlainText()
        dueDate = self.dueDate.selectedDate().toString("MM-dd-yyyy")
        return subjectName, assignmentTitle, assignmentDetails, dueDate

    def load_subjects(self):
        conn = sqlite3.connect("db/database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT class_code FROM schedules")
        subjects = cursor.fetchall()
        for subject in subjects:
            self.classCodes.addItem(subject[0])
        conn.close()
        
class SelectedAssignmentDialog(QDialog):
    def __init__(self, title, details, logged_in_username, class_code, parent=None):
        super().__init__(parent)
        uic.loadUi("ui/assignment_details.ui", self)
        self.assignmentTitle = title
        self.assignmentDetails = details
        self.username = logged_in_username
        self.subject = class_code
        
        self.title.setText(self.assignmentTitle)
        self.details.setText(self.assignmentDetails)
        self.setWindowTitle(self.assignmentTitle)
        
        # Buttons
        self.doneBtn.clicked.connect(self.marked_done)
        self.deleteBtn.clicked.connect(self.delete_assignment)
        
    def marked_done(self):
        conn = sqlite3.connect("db/database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO markedDone (username, class_code, assignment_title) VALUES (?, ?, ?)",
                        (self.username, self.subject, self.assignmentTitle))
        cursor.execute("DELETE FROM assignments WHERE class_code = ? AND title = ?",
                        (self.subject, self.assignmentTitle))
        conn.commit()
        conn.close()
        self.accept()
    
    def delete_assignment(self):
        conn = sqlite3.connect("db/database.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM assignments WHERE class_code = ? AND title = ?",
                        (self.subject, self.assignmentTitle))
        conn.commit()
        conn.close()
        self.accept()
        
        
"""# Test area
app = QApplication(sys.argv)
test = ScheduleInputDialog() # Renmae this to the appropriate dialog you want to test
test.show()
sys.exit(app.exec())"""
