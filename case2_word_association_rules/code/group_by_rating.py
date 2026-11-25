from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

FILE = "../data/fixed_data.xlsx"
SOURCE_SHEET = "processed data"
TARGET_SHEET = "grouped by rating"
GAP_ROWS = 2

# (group name, ratings, title bar colour, row tint colour)
GROUPS = [
    ("Negative", {1, 2}, "C00000", "FDE9E7"),
    ("Neutral", {3}, "7F7F7F", "F2F2F2"),
    ("Positive", {4, 5}, "2E7D32", "E8F5E9"),
]

thin = Side(style="thin", color="BFBFBF")
border = Border(left=thin, right=thin, top=thin, bottom=thin)


def main():
    wb = load_workbook(FILE)
    src = wb[SOURCE_SHEET]

    header = [cell.value for cell in src[1]]
    label_idx = header.index("review-label")
    rows = [r for r in src.iter_rows(min_row=2, values_only=True) if any(v is not None for v in r)]

    if TARGET_SHEET in wb.sheetnames:
        del wb[TARGET_SHEET]
    ws = wb.create_sheet(TARGET_SHEET)
    n_cols = len(header)

    r = 1
    for name, ratings, title_color, tint_color in GROUPS:
        group_rows = [row for row in rows if row[label_idx] in ratings]
        rating_text = "/".join(str(x) for x in sorted(ratings))

        # Title bar
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=n_cols)
        title = ws.cell(row=r, column=1, value=f"{name.upper()}  (rating {rating_text})  -  {len(group_rows)} reviews")
        title.font = Font(bold=True, size=14, color="FFFFFF")
        title.fill = PatternFill("solid", fgColor=title_color)
        title.alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[r].height = 24
        r += 1

        # Column headers
        for c, h in enumerate(header, start=1):
            cell = ws.cell(row=r, column=c, value=h)
            cell.font = Font(bold=True, color=title_color)
            cell.fill = PatternFill("solid", fgColor=tint_color)
            cell.border = Border(left=thin, right=thin, top=thin, bottom=Side(style="medium", color=title_color))
        r += 1

        # Data rows
        tint = PatternFill("solid", fgColor=tint_color)
        for row in group_rows:
            for c, v in enumerate(row, start=1):
                cell = ws.cell(row=r, column=c, value=v)
                cell.fill = tint
                cell.border = border
            r += 1

        r += GAP_ROWS

    # Column widths: wider for text columns
    wide = {"title": 30, "review": 50, "cleaned": 50, "tokens": 50,
            "filtered": 50, "lemmas": 50, "ngrams": 80}
    for c, h in enumerate(header, start=1):
        ws.column_dimensions[get_column_letter(c)].width = wide.get(h, 14)

    wb.save(FILE)
    print(f"Wrote sheet '{TARGET_SHEET}' to {FILE}")


if __name__ == "__main__":
    main()
