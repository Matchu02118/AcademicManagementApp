import sys
import warnings
import sqlite3
from PyQt6.QtWidgets import *
from PyQt6 import uic
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from dialogBoxes import *

warnings.filterwarnings("ignore", category=DeprecationWarning)

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
        self.calendar.selectionChanged.connect(self.filterAssignments)
        self.assignmentList.itemClicked.connect(self.expandAssignment)
        

        
        # Load data
        self.loadNotes()
        self.loadAssignments()
        self.loadDefaultSchedule()    

    # Schedules Tab Functions
    def loadDefaultSchedule(self):
        try:
            conn = sqlite3.connect("db/database.db")  # Updated database path
            cursor = conn.cursor()
            cursor.execute("""
                SELECT class_code, time, day, room 
                FROM schedules 
                WHERE username = ? AND schedule_type = ?
            """, (self.username, "Class"))
            schedules = cursor.fetchall()
            conn.close()

            # Clear the table widget before populating
            self.scheduleTableWidget.setColumnCount(4)
            self.scheduleTableWidget.setHorizontalHeaderLabels(["Subject", "Time", "Day", "Room"])

            for i in range (4):
                    self.scheduleTableWidget.setColumnWidth(i, 175) 

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
            conn = sqlite3.connect("db/database.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT class_code, time, day, room 
                FROM schedules 
                WHERE username = ? AND schedule_type = ?
            """, (self.username, schedule_type))
            schedules = cursor.fetchall()
            conn.close()

            # Clear the table widget before populating
            self.scheduleTableWidget.setColumnCount(4)
            self.scheduleTableWidget.setHorizontalHeaderLabels(["Subject", "Time", "Day", "Room"])

            for i in range (4):
                    self.scheduleTableWidget.setColumnWidth(i, 175)

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
            conn = sqlite3.connect("db/database.db")  # Updated database path
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO schedules (username, class_code, time, day, room, schedule_type)
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
                conn = sqlite3.connect("db/database.db")  # Updated database path
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM schedules
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
                conn = sqlite3.connect("db/database.db")
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT class_code, time, day, room 
                    FROM schedules
                    WHERE username = ? AND schedule_type = ?
                """, (self.username, schedule_type))
                schedules = cursor.fetchall()
                conn.close()

                # Clear the table widget before populating
                self.scheduleTableWidget.setColumnCount(4)
                self.scheduleTableWidget.setHorizontalHeaderLabels(["Class Code", "Time", "Day", "Room"])

                # Adjust column widths
                for i in range (4):
                    self.scheduleTableWidget.setColumnWidth(i, 175)
                
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
            conn = sqlite3.connect("db/database.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT schedule_type 
                FROM schedules
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

            try:
                conn = sqlite3.connect("db/database.db")
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE schedules
                    SET class_code = ?, time = ?, day = ?, room = ?, schedule_type = ?
                    WHERE username = ? AND class_code = ? AND time = ? AND day = ? AND room = ?
                """, (*updated_schedule, self.username, class_code, time, day, room))
                conn.commit()
                conn.close()

                self.scheduleTableWidget.item(selected_row, 0).setText(updated_schedule[0])
                self.scheduleTableWidget.item(selected_row, 1).setText(updated_schedule[1])
                self.scheduleTableWidget.item(selected_row, 2).setText(updated_schedule[2])
                self.scheduleTableWidget.item(selected_row, 3).setText(updated_schedule[3])

                QMessageBox.information(self, "Success", "Schedule updated successfully.")
            except sqlite3.Error as e:
                QMessageBox.warning(self, "Error", f"Failed to update schedule: {e}")

    # Notes Tab Functions
    def loadNotes(self):
        try:
            conn = sqlite3.connect("db/database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, title FROM notes WHERE username = ?", (self.username,))
            notes = cursor.fetchall()
            conn.close()

            self.notesView.clear()
            for note_id, title in notes:
                item = QListWidgetItem(title)
                item.setData(1, note_id)
                self.notesView.addItem(item)
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Error", f"Failed to load notes: {e}")

    def addNote(self):
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
        try:
            conn = sqlite3.connect("db/database.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO notes (username, title, content)
                VALUES (?, ?, ?)
            """, (self.username, title, content))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    def displayNote(self, item):
        note_id = item.data(1)  # Retrieve the note ID from the item's data
        try:
            conn = sqlite3.connect("db/database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT title, content FROM notes WHERE id = ?", (note_id,))
            note = cursor.fetchone()
            conn.close()
            if note:
                title, content = note
                dialog = EditNoteDialog(note_id, title, content, self)
                result = dialog.exec()

                if result == QDialog.DialogCode.Accepted:
                    updated_title = dialog.titleLineEdit.text().strip()
                    updated_content = dialog.contentTextEdit.toPlainText().strip()
                    conn = sqlite3.connect("db/database.db")
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE notes
                        SET title = ?, content = ?
                        WHERE id = ?
                    """, (updated_title, updated_content, note_id))
                    conn.commit()
                    conn.close()

                    # Update the QListWidget item
                    item.setText(updated_title)
                    QMessageBox.information(self, "Success", "Note updated successfully.")

                elif result == 2:
                    conn = sqlite3.connect("db/database.db")
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
                    conn.commit()
                    conn.close()

                    self.notesView.takeItem(self.notesView.row(item))
                    QMessageBox.information(self, "Success", "Note deleted successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to retrieve the note content.")
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Error", f"Failed to fetch note content: {e}")

    def closeEvent(self, event):
        """Handle cleanup when the application exits."""
        super().closeEvent(event)

    def open_delete_note_dialog(self):
        QMessageBox.information(self, "Delete Note", "This feature is under construction. A popup dialog will be implemented here.")

    # Assignments Tab Functions
    def loadAssignments(self):
        try:
            conn = sqlite3.connect("db/database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT title, due, class_code FROM assignments WHERE username = ?", (self.username,))
            assignments = cursor.fetchall()
            conn.close()

            # Clear the table widget before populating
            self.assignmentList.setRowCount(0)
            self.assignmentList.setColumnCount(3)
            self.assignmentList.setHorizontalHeaderLabels(["Title", "Due Date", "Class Code"])

            for row_idx, (title, due, class_code) in enumerate(assignments):
                self.assignmentList.insertRow(row_idx)
                self.assignmentList.setItem(row_idx, 0, QTableWidgetItem(title))
                self.assignmentList.setItem(row_idx, 1, QTableWidgetItem(due))
                self.assignmentList.setItem(row_idx, 2, QTableWidgetItem(class_code))
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Error", f"Failed to load assignments: {e}")

    def addAssignment(self):
        dialog = AddAssignmentDialog(self)
        result = dialog.exec()
        conn = sqlite3.connect("db/database.db")
        cursor = conn.cursor()
        if result == QDialog.DialogCode.Accepted:
            assignment_data = dialog.assignment_input()
            cursor.execute("""
                INSERT INTO assignments (username, class_code, title, details, due)
                VALUES (?, ?, ?, ?, ?)
            """, (self.username, *assignment_data))
            conn.commit()
            conn.close()
            self.loadAssignments()
    
    def filterAssignments(self):
        selected_date = self.calendar.selectedDate().toString("MM-dd-yyyy")
        try:
            conn = sqlite3.connect("db/database.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT title, due, class_code 
                FROM assignments 
                WHERE username = ? AND due = ?
            """, (self.username, selected_date))
            assignments = cursor.fetchall()
            conn.close()

            # Clear the table widget before populating
            self.assignmentList.setRowCount(0)
            for row_idx, (title, due, class_code) in enumerate(assignments):
                self.assignmentList.insertRow(row_idx)
                self.assignmentList.setItem(row_idx, 0, QTableWidgetItem(title))
                self.assignmentList.setItem(row_idx, 1, QTableWidgetItem(due))
                self.assignmentList.setItem(row_idx, 2, QTableWidgetItem(class_code))
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Error", f"Failed to filter assignments: {e}")

    def expandAssignment(self):
        selected_row = self.assignmentList.currentRow()
        conn = sqlite3.connect("db/database.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, class_code, title, details 
            FROM assignments 
            WHERE username = ? AND title = ?
        """, (self.username, self.assignmentList.item(selected_row, 0).text()))
        assignment = cursor.fetchone()
        conn.close()
        if assignment:
            self.username, class_code, title, details = assignment
            dialog = SelectedAssignmentDialog(title, details, self.username, class_code, self)
            dialog.exec()
            self.loadAssignments()
        else:
            QMessageBox.warning(self, "Error", "Failed to retrieve assignment details.")
        
    # Budgets Tab Functions
    def load_budgets(self):
        pass
    
    def add_budget(self):
        pass

app = QApplication(sys.argv)
login = LoginPage("db/database.db")
if login.exec() == QDialog.DialogCode.Accepted:
    window = main(login.logged_in_username)
    window.show()
    sys.exit(app.exec())
