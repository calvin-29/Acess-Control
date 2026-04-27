from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QThread
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib import colors
import os
import io
import os
import sqlite3
import base64
import sys
import csv

def get_file_path(type_of):
    return os.path.join(os.path.expanduser("~"), "Documents", f"access_records.{type_of}")

class ExportWorker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, main_window, export_type):
        super().__init__()
        self.main_window = main_window
        self.export_type = export_type
        self.file_path = get_file_path(self.export_type)

    def run(self):
        try:
            export_file(self.main_window, self.export_type)
            self.finished.emit()
        except Exception as e:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
            self.error.emit(str(e))

def finish(app, file_path):
    msgbox = QMessageBox(app)
    msgbox.setWindowTitle("File saved successfully")
    msgbox.setText(f"File is saved at {file_path}")
    open_btn = msgbox.addButton("Show in folder", QMessageBox.ActionRole)
    msgbox.addButton(QMessageBox.Ok)

    def reveal():
        try:
            if sys.platform.startswith("win"):
                os.startfile(os.path.split(file_path)[0])
            elif sys.platform.startswith("darwin"):
                os.system(f'open "{os.path.split(file_path)[0]}"')
            else:
                os.system(f'xdg-open "{os.path.split(file_path)[0]}"')
        except Exception:
            pass

    open_btn.clicked.connect(reveal)
    msgbox.exec_()

def run_threaded_export(app, export_type):
    app.export_thread = QThread()
    app.worker = ExportWorker(app, export_type)

    app.worker.moveToThread(app.export_thread)

    app.export_thread.started.connect(app.worker.run)
    app.worker.finished.connect(app.export_thread.quit)
    app.worker.finished.connect(app.worker.deleteLater)
    app.export_thread.finished.connect(app.export_thread.deleteLater)
    
    app.worker.finished.connect(lambda: app.statusBar().showMessage("Export Complete!", 3000))
    app.worker.finished.connect(lambda: finish(app, get_file_path(export_type)))
    app.worker.error.connect(lambda err: QMessageBox.critical(app, "Export Error", err))

    app.export_thread.start()
    app.statusBar().showMessage(f"Exporting to {export_type.upper()}... Please wait.")

def export_file(app, type_of):
    file_path = get_file_path(type_of)

    QApplication.setOverrideCursor(Qt.WaitCursor)
    logo_path = app.get_resources("images", "logo.png")
    default_pic_path = app.get_resources("images", "profile.jpg")

    logo_content = ""
    with open(logo_path, "rb") as f:
        logo_content = f.read()
    
    default_pic_content = ""
    with open(default_pic_path, "rb") as f:
        default_pic_content = f.read()

    with app.get_resources("db", app.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT tag, name, address, phone, purpose, who, time_in, time_out, date, picture FROM users")
        info = cursor.fetchall()
    
    if type_of == "csv":
        with open(file_path, "w", encoding="utf-8", newline='') as e:
            writer = csv.writer(e)
            writer.writerow(["tag", "name", "address", "phone", "purpose", "who_to_meet",
                                "time_in", "time_out", "date"])
            for row in info:
                writer.writerow(row[1:-1])
    elif type_of == "html":
        with open(file_path, "w", encoding="utf-8") as e:
            e.write('<!DOCTYPE html>')
            e.write('<html lang="en">')
            e.write('<head>')
            e.write('<meta charset="UTF-8">')
            e.write('<title>Access Control Records</title>')
            e.write('<style>')
            e.write('  body{font-family:Verdana,Geneva,Tahoma,sans-serif; margin: 10px; background-color: #121212;}')
            e.write('  div{color: #ffffff; display: flex; padding: 20px; gap: 20px}')
            e.write('  th,td{border: 1px solid #ccc; padding: 8px; text-align: center;}')
            e.write('  th{color: white; background-color: black}')
            e.write('  table{width: 100%; background-color: white; border:1; cellpadding:5; cellspacing:0}')
            e.write('  th:nth-child(1){width: 5%;}')
            e.write('  th:nth-child(5){width: 15%;}')
            e.write('  th:nth-child(2), th:nth-child(3), th:nth-child(4), th:nth-child(6),')
            e.write('  th:nth-child(7), th:nth-child(8), th:nth-child(9), th:nth-child(10){width: 10%;}')
            e.write('  img {width: 80px; height: 80px; border-radius: 8px;}')
            e.write('  .data{height: 100px}')
            e.write('</style>')
            e.write('</head>')
            e.write('<body>')
            e.write('<div>')
            e.write(f'  <img src="data:image/jpeg;base64,{base64.b64encode(logo_content).decode("utf-8")}">')
            e.write('  <h2>Access Control Records</h2>')
            e.write('</div>')
            e.write('<table>')
            e.write('  <tr>')
            e.write('    <th>Tag</th>')
            e.write('    <th>Name</th>')
            e.write('    <th>Address</th>')
            e.write('    <th>Phone number</th>')
            e.write('    <th>Purpose</th>')
            e.write('    <th>Who to meet</th>')
            e.write('    <th>Time In</th>')
            e.write('    <th>Time Out</th>')
            e.write('    <th>Date</th>')
            e.write('    <th>Picture</th>')
            e.write('  </tr>')
            for row in info:
                e.write("  <tr>")
                data = row[-1] if row[-1] else default_pic_content
                img_data = base64.b64encode(data).decode("utf-8")
                img_tag = f'<img src="data:image/jpeg;base64,{img_data}"'
                for val in row[:-1]:
                    e.write(f"    <td>{val or ''}</td>")
                e.write(f"    <td>{img_tag}</td>")
                e.write("  </tr>")
            e.write('</table>')
            e.write('</body>')
            e.write('</html>')
    elif type_of == "pdf":
        doc = SimpleDocTemplate(file_path, pagesize=A4, title="Access Control Records")
        elements = []
        styles = getSampleStyleSheet()
        formatted_data = []

        styles.add(ParagraphStyle(name='TableHeader',
                                parent=styles['Normal'],
                                fontName='Helvetica-Bold',
                                fontSize=9,
                                textColor=colors.white))

        styles.add(ParagraphStyle(name='TableData',
                                parent=styles['Normal'],
                                fontName='Helvetica',
                                fontSize=7,
                                textColor=colors.black))

        header = ['Tag','Name','Address','Phone number','Purpose','Who to meet','Time In','Time Out','Date','Picture']
        formatted_data.append([Paragraph(h, styles['TableHeader']) for h in header])

        for row in info:
            new_row = []
            for item in row[:-1]:
                new_row.append(Paragraph(str(item), styles['TableData']))
            
            img_data = row[-1] if row[-1] else default_pic_content
            if isinstance(img_data, bytes):
                img_obj = Image(io.BytesIO(img_data), width=0.5*inch, height=0.5*inch)
                new_row.append(img_obj)
            else:
                new_row.append("None")
                
            formatted_data.append(new_row)

        def add_background(canvas: Canvas, doc):
            canvas.saveState()
            canvas.setFillColor(colors.black)
            canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
            
            logo_x, logo_y = 0.2 * inch, A4[1] - (0.75 * inch)
            logo_dim = .6*inch
            canvas.drawImage(logo_path, logo_x, logo_y, width=logo_dim, height=logo_dim, mask='auto')

            canvas.setFillColor(colors.white)
            canvas.setFont("Helvetica-Bold", 15)
            canvas.drawString(logo_x+logo_dim+15, logo_y+10, "Access Control Records")

            canvas.restoreState()

        colWidths = [.5*inch, .8*inch, .8*inch, .8*inch, 1.1*inch, .8*inch, .8*inch, .8*inch, .8*inch, .8*inch]
        table = Table(formatted_data, colWidths=colWidths)
        style = TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            ('BOX', (0, 0), (-1, 0), 1, colors.white),
            ('BACKGROUND', (0, 0), (-1, 0), colors.black),
            
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ])

        table.setStyle(style)
        elements.append(table)

        doc.build(elements, onFirstPage=add_background, onLaterPages=add_background)

    QApplication.restoreOverrideCursor()
