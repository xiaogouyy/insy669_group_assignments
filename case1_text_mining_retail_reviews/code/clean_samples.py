"""
Clean the mojibake / encoding artifacts out of 'Review for CA_sample.xlsx'
and 'Review for US_sample.xlsx'.

These two files are more complex than the simple review files handled by
cleaning.py:

  * 'Review for CA_sample.xlsx' has one sheet ('Random Sample') with a
    normal header row, a 'title' column and a 'review' column - both can
    contain the garbled text.

  * 'Review for US_sample.xlsx' has 8 sheets:
      - 'US Random Sample' and 'CA Random Sample' have a normal header row
        (with 'title'/'review' columns, plus a couple of extra/blank
        columns that are left untouched).
      - 'US Positive', 'US Negative', 'US Neutral', 'CA Positive',
        'CA Negative', 'CA Neutral' have NO header row at all - the data
        starts on row 1. 'title' is column index 7 and 'review' is column
        index 8 in these. They must be read/written with header=None,
        otherwise pandas mistakes the first data row for a header and it
        gets silently dropped.

See text_cleaning.py for what the "ï¿½ï¿½ï¿½..." garbage is and how it's
cleaned (and why the original character can't always be perfectly
recovered).

Requires: pandas, openpyxl, ftfy  (pip install pandas openpyxl ftfy)
"""

import pandas as pd
from text_cleaning import clean_text, has_mojibake

CA_SAMPLE_FILE = "../data/Review for CA_sample.xlsx"
US_SAMPLE_FILE = "../data/Review for US_sample.xlsx"

# Sheets in Review for US_sample.xlsx that have a real header row.
HEADERED_SHEETS = {"US Random Sample", "CA Random Sample"}

# Column positions (0-based) of 'title' and 'review' in the headerless sheets.
TITLE_COL_IDX = 7
REVIEW_COL_IDX = 8


def clean_ca_sample():
    df = pd.read_excel(CA_SAMPLE_FILE, sheet_name="Random Sample")

    before = has_mojibake(df["title"]) + has_mojibake(df["review"])
    df["title"] = df["title"].apply(clean_text)
    df["review"] = df["review"].apply(clean_text)
    after = has_mojibake(df["title"]) + has_mojibake(df["review"])

    print(f"{CA_SAMPLE_FILE}: fixed {before} cell(s) with encoding "
          f"artifacts ({after} remaining)")

    df.to_excel(CA_SAMPLE_FILE, sheet_name="Random Sample", index=False)


def clean_us_sample():
    xl = pd.ExcelFile(US_SAMPLE_FILE)
    sheets = {}
    total_before = 0
    total_after = 0

    for name in xl.sheet_names:
        if name in HEADERED_SHEETS:
            df = xl.parse(name, header=0)
            before = has_mojibake(df["title"]) + has_mojibake(df["review"])
            df["title"] = df["title"].apply(clean_text)
            df["review"] = df["review"].apply(clean_text)
            after = has_mojibake(df["title"]) + has_mojibake(df["review"])
        else:
            df = xl.parse(name, header=None)
            before = (has_mojibake(df[TITLE_COL_IDX])
                      + has_mojibake(df[REVIEW_COL_IDX]))
            df[TITLE_COL_IDX] = df[TITLE_COL_IDX].apply(clean_text)
            df[REVIEW_COL_IDX] = df[REVIEW_COL_IDX].apply(clean_text)
            after = (has_mojibake(df[TITLE_COL_IDX])
                     + has_mojibake(df[REVIEW_COL_IDX]))

        print(f"{US_SAMPLE_FILE} [{name}]: fixed {before} cell(s) with "
              f"encoding artifacts ({after} remaining)")
        total_before += before
        total_after += after
        sheets[name] = df

    with pd.ExcelWriter(US_SAMPLE_FILE, engine="openpyxl") as writer:
        for name in xl.sheet_names:
            has_header = name in HEADERED_SHEETS
            sheets[name].to_excel(writer, sheet_name=name, index=False,
                                   header=has_header)

    print(f"{US_SAMPLE_FILE}: total fixed {total_before} cell(s) "
          f"({total_after} remaining)")


if __name__ == "__main__":
    clean_ca_sample()
    clean_us_sample()
