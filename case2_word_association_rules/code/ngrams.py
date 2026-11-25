from openpyxl import load_workbook

INPUT_FILE = "../data/wrong_data.xlsx"
OUTPUT_FILE = "../data/fixed_data.xlsx"
SHEET_NAME = "processed data"
SEP = " | "
N_VALUES = (1, 2, 3)


def make_ngrams(lemmas, n_values=N_VALUES):
    """Build 1-, 2- and 3-grams from a ' | '-separated lemma string."""
    if lemmas is None or str(lemmas).strip() == "":
        return ""
    tokens = [t.strip() for t in str(lemmas).split("|") if t.strip()]
    grams = []
    for n in n_values:
        for i in range(len(tokens) - n + 1):
            grams.append(" ".join(tokens[i:i + n]))
    return SEP.join(grams)


def main():
    wb = load_workbook(INPUT_FILE)
    ws = wb[SHEET_NAME]

    header = [cell.value for cell in ws[1]]
    lemmas_col = header.index("lemmas") + 1
    ngrams_col = header.index("ngrams") + 1

    for row in range(2, ws.max_row + 1):
        lemmas = ws.cell(row=row, column=lemmas_col).value
        ws.cell(row=row, column=ngrams_col).value = make_ngrams(lemmas)

    wb.save(OUTPUT_FILE)
    print(f"Saved corrected ngrams to {OUTPUT_FILE} ({ws.max_row - 1} rows)")


if __name__ == "__main__":
    main()
