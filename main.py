import sys
import sqlite3
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QHeaderView, QListWidgetItem, QDialog, QLineEdit, QPushButton, QVBoxLayout, QWidget, QMessageBox, QLabel, QHBoxLayout, QRadioButton, QButtonGroup, QTextEdit, QSizePolicy, QCheckBox
from PyQt6 import uic
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt  # Add this import
from dialogBoxes import ScheduleInputDialog, ViewScheduleDialog, UpdateScheduleDialog, NoteInputDialog, LoginPage, RegisterPage, EditNoteDialog, AddAssignmentDialog

class main(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username

        uic.loadUi("UI/window.ui", self)

        self.tabs.setCurrentIndex(0)
        
        # Schedule Tab buttons
        self.addSchedButton.clicked.connect(self.addSchedule)
        self.removeSchedButton.clicked.connect(self.deleteSchedule)
        self.viewSchedButton.clicked.connect(self.viewSchedule)
        self.updateSchedButton.clicked.connect(self.updateSchedule)

        # Note Tab buttons
        self.addNoteButton.clicked.connect(self.addNote)
        self.notesView.itemClicked.connect(self.displayNote)
        
        # Assignment Tab buttons
        self.addAssignmentButton.clicked.connect(self.addAssignment)

        # Initialize notes database
        self.init_notes_db()
        self.loadNotes()
        
        # Initialize assignments database
        self.init_assignments_db()
        self.loadAssignments()

        # Load "Class" schedules by default
        self.loadDefaultSchedule()

    # Schedules Tab Functions
    def loadDefaultSchedule(self):
        try:
            conn = sqlite3.connect("database/schedules.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT class_code, time, day, room 
                FROM schedule 
                WHERE username = ? AND schedule_type = ?
            """, (self.username, "Class"))
            schedules = cursor.fetchall()
            conn.close()

            # Clear the table widget before populating
            self.scheduleTableWidget.setColumnCount(4)
            self.scheduleTableWidget.setHorizontalHeaderLabels(["Class Code", "Time", "Day", "Room"])

            self.scheduleTableWidget.setColumnWidth(1, 150) 

            header_font = QFont()
            header_font.setBold(True)
            for i in range(4):
                self.scheduleTableWidget.horizontalHeaderItem(i).setFont(header_font)

            # Populate the table with schedule data
            self.scheduleTableWidget.setRowCount(0)
            for row_idx, schedule in enumerate(schedules):
                self.scheduleTableWidget.insertRow(row_idx)
                for col_idx, value in enumerate(schedule):
                    self.scheduleTableWidget.setItem(row_idx, col_idx, QTableWidgetItem(value))

        except sqlite3.Error as e:
            QMessageBox.warning(self, "Error", f"Failed to load default schedule: {e}")

    def addSchedule(self):
        dialog = ScheduleInputDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            schedule_data = dialog.get_schedule()
            if self.save_schedule(schedule_data):
                QMessageBox.information(self, "Success", "Schedule added successfully.")
                self.loadScheduleByType(schedule_data[-1])
            else:
                QMessageBox.warning(self, "Error", "Failed to add schedule. Please try again.")

    def loadScheduleByType(self, schedule_type):
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
            self.scheduleTableWidget.setHorizontalHeaderLabels(["Class Code", "Time", "Day", "Room"])

            self.scheduleTableWidget.setColumnWidth(1, 150)

            header_font = QFont()
            header_font.setBold(True)
            for i in range(4):
                self.scheduleTableWidget.horizontalHeaderItem(i).setFont(header_font)

            # Populate the table with schedule data
            self.scheduleTableWidget.setRowCount(0)
            for row_idx, schedule in enumerate(schedules):
                self.scheduleTableWidget.insertRow(row_idx)
                for col_idx, value in enumerate(schedule):
                    self.scheduleTableWidget.setItem(row_idx, col_idx, QTableWidgetItem(value))

            if not schedules:
                QMessageBox.information(self, "No Schedule", f"No {schedule_type} schedules found.")
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Error", f"Failed to fetch schedules: {e}")

    def save_schedule(self, schedule_data):
        try:
            conn = sqlite3.connect("database/schedules.db")
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
                self.scheduleTableWidget.setHorizontalHeaderLabels(["Class Code", "Time", "Day", "Room"])

                # Adjust column widths
                self.scheduleTableWidget.setColumnWidth(1, 150)

                header_font = QFont()
                header_font.setBold(True)
                for i in range(4):
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

    # Notes Tab Functions
    def init_notes_db(self):
        """Initialize the notes database."""
        self.notes_conn = sqlite3.connect("database/notes.db")
        cursor = self.notes_conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY (username) REFERENCES users (username)
            )
        """)
        self.notes_conn.commit()

    def loadNotes(self):
        """Load notes from the database into the QListWidget."""
        try:
            cursor = self.notes_conn.cursor()
            cursor.execute("SELECT id, title FROM notes WHERE username = ?", (self.username,))
            notes = cursor.fetchall()

            self.notesView.clear()
            for note_id, title in notes:
                item = QListWidgetItem(title)
                item.setData(1, note_id)  # Store the note ID in the item's data
                self.notesView.addItem(item)
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Error", f"Failed to load notes: {e}")

    def addNote(self):
        """Open the dialog to add a new note."""
        dialog = NoteInputDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title, content = dialog.get_note()
            if title and content:
                if self.saveNoteToDB(title, content):
                    QMessageBox.information(self, "Success", "Note added successfully.")
                    self.loadNotes()
                else:
                    QMessageBox.warning(self, "Error", "Failed to add note. Please try again.")
            else:
                QMessageBox.warning(self, "Invalid Input", "Both title and content are required.")

    def saveNoteToDB(self, title, content):
        """Save a new note to the database."""
        try:
            cursor = self.notes_conn.cursor()
            cursor.execute("""
                INSERT INTO notes (username, title, content)
                VALUES (?, ?, ?)
            """, (self.username, title, content))
            self.notes_conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    def displayNote(self, item):
        """Display the selected note's content in an editable dialog."""
        note_id = item.data(1)  # Retrieve the note ID from the item's data
        try:
            cursor = self.notes_conn.cursor()
            cursor.execute("SELECT title, content FROM notes WHERE id = ?", (note_id,))
            note = cursor.fetchone()
            if note:
                title, content = note

                # Open the EditNoteDialog
                dialog = EditNoteDialog(note_id, title, content, self)
                result = dialog.exec()

                if result == QDialog.DialogCode.Accepted:
                    # Save the updated note
                    updated_title = dialog.titleLineEdit.text().strip()
                    updated_content = dialog.contentTextEdit.toPlainText().strip()
                    cursor.execute("""
                        UPDATE notes
                        SET title = ?, content = ?
                        WHERE id = ?
                    """, (updated_title, updated_content, note_id))
                    self.notes_conn.commit()

                    # Update the QListWidget item
                    item.setText(updated_title)
                    QMessageBox.information(self, "Success", "Note updated successfully.")

                elif result == 2:  # Custom code for deletion
                    # Delete the note
                    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
                    self.notes_conn.commit()

                    # Remove the note from the QListWidget
                    self.notesView.takeItem(self.notesView.row(item))
                    QMessageBox.information(self, "Success", "Note deleted successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to retrieve the note content.")
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Error", f"Failed to fetch note content: {e}")

    def closeEvent(self, event):
        """Close the notes database connection when the application exits."""
        self.notes_conn.close()
        self.assignments_conn.close()
        super().closeEvent(event)

    def open_delete_note_dialog(self):
        QMessageBox.information(self, "Delete Note", "This feature is under construction. A popup dialog will be implemented here.")

    # Assignments Tab Functions
    def init_assignments_db(self):
        """Initialize the assignments database."""
        self.assignments_conn = sqlite3.connect("database/assignments.db")
        cursor = self.assignments_conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                subject TEXT NOT NULL,
                title TEXT NOT NULL,
                details TEXT NOT NULL,
                due TEXT NOT NULL,
                class_code TEXT NOT NULL,
                FOREIGN KEY (username) REFERENCES users (username)
            )
        """)
        self.assignments_conn.commit()

    def loadAssignments(self):
        """Load assignments from the database into the QTableWidget."""
        try:
            cursor = self.assignments_conn.cursor()
            cursor.execute("SELECT id, title, details, due, class_code FROM assignments WHERE username = ?", (self.username,))
            assignments = cursor.fetchall()

            # Clear the table widget before populating
            self.assignmentList.setRowCount(0)
            self.assignmentList.setColumnCount(4)
            self.assignmentList.setHorizontalHeaderLabels(["Title", "Details", "Due Date", "Class Code"])

            for row_idx, (assignment_id, title, details, due, class_code) in enumerate(assignments):
                self.assignmentList.insertRow(row_idx)
                self.assignmentList.setItem(row_idx, 0, QTableWidgetItem(title))
                self.assignmentList.setItem(row_idx, 1, QTableWidgetItem(details))
                self.assignmentList.setItem(row_idx, 2, QTableWidgetItem(due))
                self.assignmentList.setItem(row_idx, 3, QTableWidgetItem(class_code))
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Error", f"Failed to load assignments: {e}")

    def addAssignment(self):
        """Open the dialog to add a new assignment."""
        dialog = AddAssignmentDialog(self.username, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.loadAssignments()

    def removeAssignment(self):
        """Remove the selected assignment from the QTableWidget and database."""
        selected_row = self.assignmentTableWidget.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select an assignment to delete.")
            return

        title_item = self.assignmentTableWidget.item(selected_row, 0)
        if not title_item:
            QMessageBox.warning(self, "Error", "Failed to retrieve the selected assignment.")
            return

        title = title_item.text()

        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the assignment '{title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                cursor = self.assignments_conn.cursor()
                cursor.execute("DELETE FROM assignments WHERE username = ? AND title = ?", (self.username, title))
                self.assignments_conn.commit()

                # Remove the row from the table widget
                self.assignmentTableWidget.removeRow(selected_row)

                QMessageBox.information(self, "Success", "Assignment deleted successfully.")
            except sqlite3.Error as e:
                QMessageBox.warning(self, "Error", f"Failed to delete assignment: {e}")

    # Budgets Tab Functions
    # Placeholder for future implementation
    # Add functions related to Budgets here

    # Settings Tab Functions
    # Placeholder for future implementation
    # Add functions related to Settings here

app = QApplication(sys.argv)
login = LoginPage()
if login.exec() == QDialog.DialogCode.Accepted:
    window = main(login.logged_in_username)
    window.show()
    sys.exit(app.exec())
