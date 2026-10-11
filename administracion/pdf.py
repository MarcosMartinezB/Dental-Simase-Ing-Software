from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

VERDE = colors.HexColor('#17574f')
MENTA = colors.HexColor('#e6f4f0')
BORDE = colors.HexColor('#cfe5df')


def generar_pdf(desde, hasta, resumen, generado_por=''):
    """Devuelve los bytes de un PDF con el reporte de gestión."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, title='Reporte de gestion - Dental Simase',
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm)
    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle('titulo', parent=estilos['Title'], textColor=VERDE)

    filas = [['Indicador', 'Valor']] + [[etiqueta, str(valor)] for etiqueta, valor in resumen]
    tabla = Table(filas, colWidths=[11 * cm, 6 * cm], repeatRows=1)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), VERDE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, MENTA]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDE),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    elementos = [
        Paragraph('Clínica Dental Simase', titulo),
        Paragraph('Reporte de gestión', estilos['Heading2']),
        Paragraph(f'Período: {desde:%d/%m/%Y} al {hasta:%d/%m/%Y}', estilos['Normal']),
        Spacer(1, 14), tabla, Spacer(1, 14),
    ]
    if generado_por:
        elementos.append(Paragraph(f'Generado por: {generado_por}', estilos['Italic']))
    doc.build(elementos)
    return buffer.getvalue()
