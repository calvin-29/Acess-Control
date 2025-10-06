from PyQt5.QtWidgets import (
    QLabel, QMainWindow, QPushButton, QApplication, QFormLayout, QVBoxLayout, QHBoxLayout, 
    QWidget, QLineEdit, QMessageBox, QDialog, QFrame, QAction
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
import sys, datetime, sqlite3, os


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # --- Window Settings ---
        self.setWindowTitle("Access Control Management System")
        self.setGeometry(100, 100, 700, 500)  # x, y, width, height

        # Call setup functions
        self.create_database()   # create SQLite DB if not exists
        self.initUI()            # setup widgets/layout
        self.initStyle()         # apply custom styles

    # ------------------------------
    # Utility Functions
    # ------------------------------
    def get_current_time(self):
        """Set current system time into Time In field"""
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.timein.setText(current_time)

    def get_current_time2(self):
        """Set current system time into Time Out field"""
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.timeout.setText(current_time)

    def get_current_date(self):
        """Set current system date into date field"""
        current_time = datetime.datetime.now().strftime("%d/%m/%Y")
        self.date.setText(current_time)

    def create_database(self):
        """Create SQLite database and users table if not exists"""
        with sqlite3.connect("my_db.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                name TEXT,
                                address TEXT,
                                time_in TEXT,
                                time_out TEXT
                              )""")
            conn.commit()
    
    def update_record(entry, name):
        """Update a record of someone in the database"""
        with sqlite3.connect("my_db.db") as conn:
            cursor = conn.cursor()
            tab = f"UPDATE users SET time_out='{entry}' WHERE name = '{name}'"
            cursor.execute(tab)
            conn.commit()

    def save_record(self):
        """Save user input into database"""
        name = self.name.text().strip()
        address = self.address.text().strip()
        time_in = self.timein.text().strip()
        time_out = self.timeout.text().strip()

        # validation
        if not name or not address:
            QMessageBox.warning(self, "Error", "Please enter both Name and Address")
            return

        # insert into DB
        with sqlite3.connect("my_db.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, address, time_in, time_out) VALUES (?, ?, ?, ?)",
                           (name, address, time_in, time_out))
            conn.commit()

        QMessageBox.information(self, "Success", "Record saved successfully!")

        # clear input fields after save
        self.name.clear()
        self.address.clear()
        self.timein.clear()
        self.timeout.clear()
    
    def settings(self):
        app = QDialog()
        app.setWindowTitle("Access Setting")
        app.exec_()
    
    def menu_commands(self, commands: QAction):
        if commands.text().lower() == "Update Record":
            self.update_record(self.name.text())
        elif commands.text().lower() == "Save Record":
            self.save_record()
        else:
            self.settings()

    # ------------------------------
    # UI Setup
    # ------------------------------

    def initUI(self):
        """Initialize main window layout and widgets"""
        window = QWidget()
        vbox = QVBoxLayout()

        # --- TITLE + LOGO SECTION ---
        hbox = QHBoxLayout()
        self.title = QLabel("Access Control System")

        logo = QLabel()
        pixmap = QPixmap(
            os.path.join("images","logo.png")
        ).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo.setPixmap(pixmap)
        hbox.addWidget(logo, alignment=Qt.AlignLeft)

        hbox.addWidget(self.title, alignment=Qt.AlignCenter)
        vbox.addLayout(hbox)
        window.setLayout(vbox)

        # --- MENU SECTION ---
        menu = self.menuBar()
        file = menu.addMenu("File")
        save = QAction(QIcon(os.path.join("images", "save.png")), "Save Record", self)
        save.setShortcut("Ctrl+S")
        update = QAction(QIcon(os.path.join("images", "update.png")), "Update Record", self)
        update.setShortcut("Ctrl+U")
        file.addAction(save)
        file.addAction(update)
        file.addSeparator()
        file.addAction(QIcon(os.path.join("images", "logo.png")), "Settings")

        file.triggered.connect(self.menu_commands)

        self.form_frame = QFrame()
        self.form_frame.setObjectName("form_frame")

        # --- FORM SECTION ---
        form = QFormLayout()
        self.name = QLineEdit()
        self.address = QLineEdit()
        self.timein = QLineEdit()
        self.timeout = QLineEdit()
        self.date = QLineEdit()
        self.picture = QLabel()

        # Buttons for setting current time
        self.get_time_btn = QPushButton("⏱")
        self.get_time_btn2 = QPushButton("⏱")
        self.date_btn = QPushButton("⏱")

        self.get_time_btn.setToolTip("Get Current Time In")
        self.get_time_btn.setFixedWidth(40)
        self.get_time_btn.clicked.connect(self.get_current_time)

        self.get_time_btn2.setToolTip("Get Current Time Out")
        self.get_time_btn2.setFixedWidth(40)
        self.get_time_btn2.clicked.connect(self.get_current_time2)

        self.date_btn.setToolTip("Get Current Date")
        self.date_btn.setFixedWidth(40)
        self.date_btn.clicked.connect(self.get_current_date)

        # Set fields read-only for time values
        self.timein.setReadOnly(True)
        self.timeout.setReadOnly(True)
        self.date.setReadOnly(True)

        # set the label configurations
        picture_hbox = QHBoxLayout()
        self.picture.setPixmap(QPixmap(os.path.join("images","profile.jpg")).
                               scaled(100, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        picture_hbox.addWidget(self.picture, alignment=Qt.AlignCenter)

        # Layout for time-in row
        self.time_in_hbox = QHBoxLayout()
        self.time_in_hbox.addWidget(self.timein)
        self.time_in_hbox.addWidget(self.get_time_btn)

        # Layout for time-out row
        self.time_out_hbox = QHBoxLayout()
        self.time_out_hbox.addWidget(self.timeout)
        self.time_out_hbox.addWidget(self.get_time_btn2)
        
        # Layout for date row
        self.date_hbox = QHBoxLayout()
        self.date_hbox.addWidget(self.date)
        self.date_hbox.addWidget(self.date_btn)

        # Add input fields to form
        form.addRow(picture_hbox)
        form.addRow("Name:", self.name)
        form.addRow("Address:", self.address)
        form.addRow("Time in:", self.time_in_hbox)
        form.addRow("Time out:", self.time_out_hbox)
        form.addRow("Date:", self.date_hbox)

        self.form_frame.setLayout(form)
        vbox.addWidget(self.form_frame)

        vbox.setAlignment(Qt.AlignTop)
        self.setCentralWidget(window)

    def initStyle(self):
        """Apply stylesheet to the UI"""
        self.title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: white;
            letter-spacing: 2px;
            margin-bottom: 20px;
        """)
        self.picture.setStyleSheet("""
            margin: 15px 0;
        """)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2A2A2A;
            }
            QWidget {
                border-radius: 16px;
                margin: 2px;
            }
            QLabel {
                font-size: 17px;
                font-weight: 500;
                color: white;
            }
            QLineEdit {
                padding: 8px 12px;
                font-size: 16px;
                border: 1px solid #bdbdbd;
                border-radius: 8px;
                background: #f7f7f7;
            }
            QLineEdit:focus {
                border: 1.5px solid #0078d7;
                background: #fff;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border-radius: 8px;
                font-size: 16px;
                padding: 6px 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #005fa3;
            }
            QPushButton:pressed {
                background-color: #003e6b;
            }
            QMenu {
                background-color: #2e2e2e;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
            }
            QMenu::item {
                padding: 5px 15px;
                background-color: transparent;
                color: #ffffff;
            }
            QMenu::item:selected {
                background-color: #4a90d9;
                border-radius: 3px;
            }
            QMenu::separator {
                height: 1px;
                background-color: #555555;
                margin: 5px 0;
            }
            #form_frame {
                background-color: #2A2A2A;
                border: 0.5px solid white;
            }
            QMenuBar {
                font-size: 14px;
                color: white;
                background-color: black;
            }
            QMenuBar::item:selected {
                color: #2A2A2A
            }
        """)

# ------------------------------
# Main Entry Point
# ------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
