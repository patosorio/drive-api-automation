import pandas as pd
from openpyxl import load_workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle


def load_excel_data(path):
    """Load Excel sheet into a pandas DataFrame."""
    wb = load_workbook(path, data_only=True)
    sheet = wb.active
    data = sheet.values
    columns = next(data)
    return pd.DataFrame(data, columns=columns)


def dataframe_to_paginated_pdf(
        df,
        output_path,
        margin=0.5 * inch,
        row_height=12,
):
    """Render a DataFrame into a paginated PDF formatted to A4 width."""
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    table_width = width - 2 * margin
    data = [df.columns.tolist()] + df.values.tolist()
    rows_per_page = int((height - 2 * margin) / row_height)

    for page_start in range(0, len(data), rows_per_page):
        page_data = data[page_start:page_start + rows_per_page]
        table = Table(page_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        table._argW = [table_width / len(df.columns)] * len(df.columns)
        table.wrapOn(c, width, height)
        table.drawOn(c, margin, height - margin - row_height * len(page_data))
        c.showPage()

    c.save()


if __name__ == '__main__':
    input_excel = (
        'conversion_xlsx_to_pdf/test-template/'
        'account-cancel-withdraw-2.xlsx'
    )
    output_pdf = 'conversion_xlsx_to_pdf/account-cancel-withdraw-2.pdf'

    df = load_excel_data(input_excel)
    dataframe_to_paginated_pdf(df, output_pdf)
