from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from reportlab.lib.pagesizes import A3
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch
from io import BytesIO
from PIL import Image as PILImage
import os
import sqlite3
import base64
import sys
import csv

def exports(self, type_of):
    QApplication.setOverrideCursor(Qt.WaitCursor)
    file_path = os.path.join(os.path.expanduser("~"), "Documents", f"access_records.{type_of}")
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "logo.png")

    with open(logo_path, "rb") as f:
        logo_content = f.read()

    try:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT tag, name, address, phone, purpose, who, time_in, time_out, date, picture FROM users")
            info = cursor.fetchall()
    except Exception as e:
        QMessageBox.critical(self, "Export Error", f"Failed to read records:\n{e}")
        return

    try:
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
                e.write('  <img src="data:image/jpeg;base64,{base64.b64encode(logo_content).decode("utf-8")}">')
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
                    img_data = base64.b64encode(picture).decode("utf-8")
                    img_tag = f'<img src="data:image/jpeg;base64,{img_data}"'
                    for val in row[:-1]:
                        e.write(f"    <td>{val or ''}</td>")
                    e.write(f"    <td>{img_tag}</td>")
                    e.write("  </tr>")
                e.write('</table>')
                e.write('</body>')
                e.write('</html>')
        elif type_of == "pdf":
            doc = SimpleDocTemplate(file_path, pagesize=A3)
            styles = getSampleStyleSheet()
            story = []

            title = Paragraph("<b>Access Control Records</b>", styles["Title"])
            story.append(title)
            story.append(Spacer(1, 0.3 * inch))

            # Header row (with picture column)
            data = [["Tag", "Name", "Address", "Phone Number", "Purpose", "Who to Meet", "Time In", "Time Out", "Date", "Picture"]]

            for row in info:
                tag, name, address, phone, purpose, who_to_meet, time_in, time_out, date, picture = row

                # Default placeholder if no image
                if picture:
                    try:
                        # Convert blob to image and scale down
                        pil_img = PILImage.open(BytesIO(picture))
                        pil_img.thumbnail((60, 60))
                        img_buffer = BytesIO()
                        pil_img.save(img_buffer, format="JPEG")
                        img_buffer.seek(0)
                        img = Image(img_buffer, width=0.8 * inch, height=0.8 * inch)
                    except Exception:
                        img = Paragraph("<font color='grey'>Error</font>", styles["BodyText"])
                else:
                    img = Paragraph("<font color='grey'>No Image</font>", styles["BodyText"])

                data.append([tag or "", name or "", address or "", phone or "", purpose or "",
                            who_to_meet or "", time_in or "", time_out or "", date or "", img])

            table = Table(data, repeatRows=1, colWidths=[0.6*inch, 1*inch, 1*inch, 1.3*inch,
                                                        0.8*inch, 0.8*inch, 0.8*inch, 0.9*inch])

            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0078d7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))

            story.append(table)
            doc.build(story)

        else:
            QMessageBox.warning(self, "Unknown type", f"Unknown export type: {type_of}")
            return

        QApplication.restoreOverrideCursor()

        msgbox = QMessageBox(self)
        msgbox.setWindowTitle("File saved successfully")
        msgbox.setText(f"File is saved at {file_path}")
        open_btn = msgbox.addButton("Show in folder", QMessageBox.ActionRole)
        ok_btn = msgbox.addButton(QMessageBox.Ok)

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
    except Exception as e:
        os.remove(file_path)
        QMessageBox.critical(self, "Export Error", f"Failed to export:\n{e}")
