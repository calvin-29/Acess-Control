from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

w, h = A4
c = canvas.Canvas("hello.pdf", pagesize=A4)
print(inch)
c.translate(inch, inch)
c.setFont("Consolas", 15)
c.setStrokeColorRGB(.4, .7, .5)
c.setFillColorRGB(0, 0, 0)
c.line(0, 0, 0, 1.7)
c.line(0, 0, inch, 0)

c.showPage()
c.save()
