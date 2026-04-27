from PyQt5.QtWidgets import (
    QLabel, QMainWindow, QPushButton, QApplication, QFormLayout, QVBoxLayout,
    QHBoxLayout, QWidget, QLineEdit, QMessageBox, QDialog, QAction,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplashScreen
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont, QIcon
from theme import set_dark_theme, set_light_theme
from admin import AdminLogin, AdminManager
from ui import UI
from export import run_threaded_export
from camera import Camera
import sys
import datetime
import sqlite3
import os
import cv2
import json

def list_available_cameras(max_index_to_check=10):
    available_cameras = []
    for i in range(max_index_to_check):
        api = cv2.CAP_DSHOW if sys.platform.startswith("win") else 0
        cap = cv2.VideoCapture(i, api)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras

def get_appdata_dir():
    APP_NAME = "Visitor_Log"
    if sys.platform.startswith("win"):
        local = os.getenv("APPDATA")
        if local:
            base = os.path.join(local, APP_NAME)
        else:
            base = os.path.join(os.path.expanduser("~"), f".{APP_NAME.lower()}")
    else:
        xdg = os.getenv("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
        base = os.path.join(xdg, APP_NAME)
    os.makedirs(base, exist_ok=True)
    return base

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.dark_mode = True
        self.setWindowTitle("Visitor Login")

        appdata = get_appdata_dir()
        self.db_path = os.path.join(appdata, "data.db")
        self.config = os.path.join(appdata, "config.json")
        self.config_data = {
            "dark_mode": True,
            "camera": 0
        }

        try:
            if not os.path.exists(self.config):
                with open(self.config, "w") as f:
                    json.dump(self.config_data, f)
            else:
                with open(self.config, "r") as f:
                    self.config_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Loading Error", str(e))

        icon_path = self.get_resources("images", "logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.create_database()

        self.admin = False

        pixmap = QPixmap(icon_path)
        pixmap = pixmap.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        splash = QSplashScreen(pixmap)
        splash.show()

        cameras = list_available_cameras()

        self.ui = UI(self, cameras)
        self.ui.initUI()

        self.camera = Camera(self, cameras)
        self.current_camera_index = 0

        if self.config_data["dark_mode"]:
            set_dark_theme(self)
        else:
            set_light_theme(self)

        self.show()        
        self.setWindowState(Qt.WindowMaximized)
        splash.finish(self)

    # ------------------------------
    # Database and Utility
    # ------------------------------
    def create_database(self):
        try:
            with self.get_resources("db", self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tag TEXT,
                        name TEXT,
                        address TEXT,
                        phone TEXT,
                        purpose TEXT,
                        who TEXT,
                        time_in TEXT,
                        time_out TEXT,
                        date TEXT,
                        picture BLOB
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS admins (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT
                    )
                """)
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to create database:\n{e}")
    
    def check_admin(self):
        try:
            with self.get_resources("db", self.db_path) as conn:
                cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM admins")
            count = cursor.fetchone()[0]
            if count == 0:
                dialog = QMessageBox.question(self, "No admin", "No admin is detected. \nWould you like to add one",
                                    QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
                if dialog == QMessageBox.StandardButton.Yes:
                    admin = AdminManager(self)
                    admin.add_admin()
                    self.admin = True
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to create database:\n{e}")

    def get_current_time(self):
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.timeout.setText(current_time)
        self.statusBar().showMessage("Time updated", 2000)

    def get_current_date(self):
        current_date = datetime.datetime.now().strftime("%d/%m/%Y")
        self.date.setText(current_date)
        self.statusBar().showMessage("Date updated", 2000)
    
    def save(self):
        try:
            with open(self.config, "w") as f:
                json.dump(self.config_data, f)
        except Exception as e:
            QMessageBox.critical(self, "Saving Error", str(e))

    def toggle_theme(self):
        if self.dark_mode:
            self.dark_mode = False
            set_light_theme()
        else:
            self.dark_mode = True
            set_dark_theme()
        self.config_data["dark_mode"] = self.dark_mode
        self.save()

    def save_record(self):
        tag = self.tag.text().strip()
        name = self.name.text().strip()
        address = self.address.text().strip()
        phone = self.phone.text().strip()
        time_in = datetime.datetime.now().strftime("%H:%M:%S")
        purpose = self.purpose.toPlainText().strip()
        who = self.who_to_meet.text().strip()
        time_out = self.timeout.text().strip()
        date = self.date.text().strip()

        if not name or not address or not date or not purpose or not phone or not who:
            QMessageBox.warning(self, "Error", "Please fill all required fields.")
            return

        if len(phone) != 11 or not phone.isnumeric():
            QMessageBox.warning(self, "Error", "Phone number is invalid")
            return

        profile_path = self.get_resources("images", "temp.jpg")
        picture_data = None
        if os.path.exists(profile_path):
            with open(profile_path, "rb") as f:
                picture_data = f.read()
        
        normalized_tag = tag.rjust(3, '0') if tag else None
        
        with self.get_resources("db", self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT tag, name FROM users WHERE date=?', (date,))
            r = cursor.fetchall()
            if r:
                tags = [i[0] for i in r]
                names = [j[1] for j in r]
                # if tag has been registered today and it is not someone recorded today
                if normalized_tag in tags and name not in names:
                    QMessageBox.critical(self, "DB Error", f"Tag has been registered today")
                    return

        try:
            with self.get_resources("db", self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE date=? AND tag=?", (date, tag))
                record = cursor.fetchone()

                if record:
                    reply = QMessageBox.question(self, "Confirm", f"Update profile for {name}?",
                                                QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        cursor.execute(
                            """UPDATE users SET name=?, address=?, phone=?, time_out=?, purpose=?, who=?, picture=?
                            WHERE tag=? AND date=?""", 
                            (name, address, phone, time_out, purpose, who, picture_data, tag, date)
                        )
                    else:
                        return
                else:
                    cursor.execute(
                        """INSERT INTO users (tag, name, address, phone, time_in, purpose, who, time_out, date, picture) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (normalized_tag, name, address, phone, time_in, purpose, who, time_out, date, picture_data)
                    )
                conn.commit()
            self.clear()
            self.ui.dashboard()
            QMessageBox.information(self, "Success", "Record saved successfully!")
            self.statusBar().showMessage("Record saved", 3000)
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "DB Error", f"Tag '{tag}' has already been used")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "DB Error", f"Failed to save record:\n{e}")

    def clear(self):
        self.tag.clear()
        self.name.clear()
        self.address.clear()
        self.phone.clear()
        self.purpose.clear()
        self.who_to_meet.clear()
        self.timeout.clear()
        self.date.clear()

        profile_path = self.get_resources("images", "profile.jpg")
        temp_image = self.get_resources("images", "temp.jpg")

        if os.path.exists(profile_path):
            pixmap = QPixmap(profile_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.picture.setPixmap(pixmap)
        else:
            self.picture.clear()

        if os.path.exists(temp_image):
            try:
                os.remove(temp_image)
            except FileNotFoundError as e:
                pass

    def closeEvent(self, a0):
        self.clear()

    def load_record(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Load Record")
        layout = QFormLayout(dialog)
        tag_input = QLineEdit()
        tag_input.setPlaceholderText("Enter Tag")
        layout.addRow("Tag:", tag_input)
        submit = QPushButton("Submit")
        layout.addRow(submit)

        def load():
            tag = tag_input.text().strip()
            date = datetime.datetime.now().strftime("%d/%m/%Y")
            if not tag:
                QMessageBox.warning(dialog, "Error", "Please enter a tag.")
                return

            normalized = tag.rjust(3, '0')
            try:
                with self.get_resources("db", self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM users WHERE tag=? AND date=?", (normalized, date))
                    record = cursor.fetchone()
                    if record:
                        self.ui.form(True)
                        self.tag.setText(str(record[1] or ""))
                        self.name.setText(str(record[2] or ""))
                        self.address.setText(str(record[3] or ""))
                        self.phone.setText(str(record[4] or ""))
                        self.purpose.setText(str(record[5] or ""))
                        self.who_to_meet.setText(str(record[6] or ""))
                        self.timeout.setText(str(record[8] or ""))
                        self.date.setText(str(record[9] or ""))
                        self.ui.get_time_btn2.setEnabled(False if record[8] else True)
                        if record[10]:
                            pixmap = QPixmap()
                            pixmap.loadFromData(record[10])
                            self.picture.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                            with open(self.get_resources("images", "temp.jpg"), 'wb') as f_:
                                f_.write(record[10])
                        else:
                            path = self.get_resources("images", "profile.jpg")
                            if os.path.exists(path):
                                self.picture.setPixmap(QPixmap(path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    else:
                        self.ui.form()
                        QMessageBox.warning(dialog, "Not Found", f"No record found for tag: {tag}")
                self.ui.change(1)
            except sqlite3.Error as e:
                QMessageBox.critical(dialog, "DB Error", f"Failed to load record:\n{e}")
            dialog.close()

        submit.clicked.connect(load)
        dialog.exec_()

    def view(self):
        self.check_admin()
        if self.admin:
            dialog = QMainWindow(self)
            dialog.setWindowTitle("View Logs")
            dialog.resize(self.width()-30, self.height()-30)

            menu = dialog.menuBar()
            file = menu.addMenu("File")
            export = file.addMenu("Export")
            export.addAction("Export to csv").triggered.connect(lambda: run_threaded_export(self, "csv"))
            export.addAction("Export to html").triggered.connect(lambda: run_threaded_export(self, "html"))
            export.addAction("Export to pdf").triggered.connect(lambda: run_threaded_export(self, "pdf"))

            win = QWidget()
            vbox = QVBoxLayout()

            search_box = QHBoxLayout()
            search_label = QLabel("🔍 Search:")
            search_input = QLineEdit()
            search_input.setPlaceholderText("Type to search by tag, name, address, or date...")
            search_box.addWidget(search_label)
            search_box.addWidget(search_input)
            vbox.addLayout(search_box)

            table = QTableWidget()
            with self.get_resources("db", self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT tag, name, address, phone, purpose, who, time_in, time_out, date FROM users ORDER BY date DESC, time_in DESC")
                info = cursor.fetchall()

                rows, columns = len(info), 9
                table.setRowCount(rows)
                table.setColumnCount(columns)
                table.setStyleSheet("background-color: rgb(200, 200, 200);")
                for row_idx, row_val in enumerate(info):
                    for col_idx, cell in enumerate(row_val):
                        text = "" if cell is None else str(cell)
                        item = QTableWidgetItem(text)
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setFont(QFont("Consolas", 10))
                        table.setItem(row_idx, col_idx, item)

                table.setHorizontalHeaderLabels(["Tag", "Name", "Address", "Phone Number", "Purpose", "Who to meet", "Time In",  "Time Out", "Date"])
                header = table.horizontalHeader()
                header.setSectionResizeMode(QHeaderView.Stretch)

            vbox.addWidget(table)
            win.setLayout(vbox)
            dialog.setCentralWidget(win)

            def filter_table():
                filter_text = search_input.text().strip().lower()
                for row in range(table.rowCount()):
                    match = False
                    for col in range(table.columnCount()):
                        item = table.item(row, col)
                        if item and filter_text in item.text().lower():
                            match = True
                            break
                    table.setRowHidden(row, not match)

            search_input.textChanged.connect(filter_table)
            dialog.show()
        else:
            QMessageBox.information(self, "Not admin", "You are not the admin")

    def settings(self):
        admin = AdminLogin(self)
        if admin.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Access Granted", "Welcome, Admin!")
            self.admin = True
            self.statusBar().showMessage("Signed in as admin", 3000)
        else:
            QMessageBox.warning(self, "Access Denied", "Invalid credentials.")

    def open_admin_manager(self):
        if not self.admin:
            QMessageBox.information(self, "Not admin", "You must sign in first.")
            return
        mgr = AdminManager(self)
        mgr.exec_()

    def menu_commands(self, command: QAction):
        text = command.text()
        if text == "Load Record":
            self.load_record()
        elif text == "Save Record":
            self.save_record()
        elif text == "New Record":
            self.clear()
            self.ui.form()
            self.ui.change(1)
        elif text == "Toggle Theme":
            self.toggle_theme()
        elif text == "View Table":
            self.view()
        elif text == "Reset All":
            self.clear()
            self.ui.form()
            self.ui.change(1)
        elif text == "Clear Date":
            self.date.clear()
        elif text == "Sign In / Admin Manager":
            self.check_admin()
            if self.admin:
                self.open_admin_manager()
            else:
                self.settings()
        elif text == "Logout":
            self.check_admin()
            if self.admin:
                self.admin = False
                QMessageBox.information(self, "Logged out", "You have logged out successfully.")
                self.statusBar().showMessage("Signed out", 3000)
            else:
                QMessageBox.information(self, "Info", "You are not logged in.")
        else:
            self.settings()
    
    def toolbtnpressed(self, a, stack, list_):
        if a.text() == "Save":
            self.save_record()
        elif a.text() == "Load":
            self.load_record()
        elif a.text() == "Register":
            stack.setCurrentIndex(1)
            list_.setCurrentRow(1)
        elif a.text() == "Export":
            self.check_admin()
            if self.admin:
                export = QDialog(self)
                export.setWindowTitle("Export Data")
                export.setMinimumSize(300, 100)
                hbox = QHBoxLayout()
                for i in ["CSV", "HTML", "PDF"]:
                    btn = QPushButton(i)
                    btn.clicked.connect(lambda e, val=i: run_threaded_export(self, val.lower()))
                    hbox.addWidget(btn)
                hbox.setSpacing(10)
                export.setLayout(hbox)
                export.exec_()
            else:
                msgbox = QMessageBox(self)
                msgbox.setWindowTitle("Sign In")
                msgbox.setText("You are not currently the admin. \nWould you like to sign in?")
                yes_btn = msgbox.addButton("Yes", QMessageBox.ActionRole)
                no_btn = msgbox.addButton("No", QMessageBox.ActionRole)

                yes_btn.clicked.connect(lambda: self.settings())
                no_btn.clicked.connect(lambda: msgbox.close())
                msgbox.exec_()
        elif a.text() == "Sign In":
            self.settings()
        else:
            self.open_admin_manager()
    
    @staticmethod
    def get_resources(type_of, path):
        if type_of == "db":
            return sqlite3.connect(path)
        elif type_of == "images":
            return os.path.join(os.path.dirname(__file__), type_of, path)

# ------------------------------
# Run App
# ------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set global readable font
    app.setFont(QFont("Segoe UI", 11))

    MainWindow()
    
    sys.exit(app.exec_())