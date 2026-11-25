"""
Clean the mojibake / encoding artifacts out of the 'review' column of the
three simple review Excel files (negetive.xlsx, neutral_CA.xlsx,
positive_CA.xlsx). Each of these has a single sheet with a normal header
row and a 'review' column.

See text_cleaning.py for what the "ï¿½ï¿½ï¿½..." garbage is and how it's
cleaned (and why the original character can't always be perfectly
recovered).

Requires: pandas, openpyxl, ftfy  (pip install pandas openpyxl ftfy)
"""

import pandas as pd
from text_cleaning import clean_text, has_mojibake

FILES = ["../data/negetive.xlsx", "../data/neutral_CA.xlsx", "../data/positive_CA.xlsx"]
REVIEW_COL = "review"


def clean_file(path):
    df = pd.read_excel(path)
    before = has_mojibake(df[REVIEW_COL])

    df[REVIEW_COL] = df[REVIEW_COL].apply(clean_text)

    after = has_mojibake(df[REVIEW_COL])
    print(f"{path}: fixed {before} row(s) with encoding artifacts "
          f"({after} remaining)")

    df.to_excel(path, index=False)


if __name__ == "__main__":
    for f in FILES:
        clean_file(f)
