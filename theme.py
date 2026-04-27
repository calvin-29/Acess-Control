# ------------------------------
# Themes
# ------------------------------
def set_light_theme(app):
    app.title.setStyleSheet("font-size:20px;font-weight:700;color:#222;letter-spacing:1px;")
    app.setStyleSheet("""
        QMainWindow,QDialog{background-color:rgb(235, 235, 200);}
        QLabel{font-size:14px;color:#222;}
        QLineEdit, QTextEdit{
            padding:8px 10px;font-size:14px;border:1px solid #bdbdbd;
            border-radius:6px;background:white;color:black;
        }
        QPushButton{
            background-color:#0078d7;color:white;
            border-radius:8px;font-size:14px;padding:6px 10px;
        }
        QPushButton:disabled{background-color:#949494;}
        QPushButton:hover{background-color:#005fa3;}
        QMenuBar, QMenu{background-color:#e9f2ff;color:#1E2832;font-size:13px}
        QMenuBar::item::selected, QMenu::item::selected{background-color:#e9e7df;color:#1E2912;}
        QComboBox{background-color:#0078d7;color:white;font-size:13px}
        #form_frame, QListWidget{
            background-color:#ffffff;border-radius:10px;
            padding:16px;border:1px solid #e1e1e1;
        }
        QListWidget{background-color:grey}
        QListWidget::item{color: black;font-family:"Ink Free"}
    """)

def set_dark_theme(app):
    app.title.setStyleSheet("font-size:20px;font-weight:700;color:white;letter-spacing:1px;")
    app.setStyleSheet("""
        QMainWindow,QDialog{background-color:rgb(20, 20, 50);}
        QLabel{
            font-size:16px;font-weight:400;font-family:"Segoe UI";
            color:white;margin:0px 0px 5px 0px
        }
        QLineEdit, QTextEdit{
            padding:8px 10px;font-size:16px;border:1px solid #555;
            border-radius:6px;background:rgb(20, 20, 40);
            color:white;margin:0px 0px 5px 0px
        }
        QPushButton{
            background-color:#0078d7;color:white;
            border-radius:8px;font-size:14px;padding:6px 10px;
        }
        QPushButton:disabled{background-color:#949494;}
        QPushButton:hover{background-color:#005fa3;}
        QMenuBar, QMenu{background-color:#1E2832;color:#C8E1FA;font-size:15px}
        QMenuBar::item::selected, QMenu::item::selected{background-color:#1E2842;color:#C8E1EA}
        QComboBox{background-color:#0078d7;color:white;font-size:13px}
        #form_frame, QListWidget{
            background-color:rgb(20, 20, 45);
            border-radius:10px;padding:16px;
            border:1px solid #333;
        }
        QListWidget::item{color: white;font-family:"Ink Free"}
    """)

