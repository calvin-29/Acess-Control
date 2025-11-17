from reportlab.lib.pagesizes import A3
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch
from io import BytesIO
from PIL import Image as PILImage
import sys
import ast

file_path = sys.argv[1]
info = ast.literal_eval(sys.argv[2])

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