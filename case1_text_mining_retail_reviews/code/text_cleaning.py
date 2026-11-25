"""
Shared text-cleaning helper for the review Excel files.

See cleaning.py for a full explanation of what the "ï¿½ï¿½ï¿½..." garbage is
and why it can't be perfectly recovered. clean_text() below implements that
same fix so every script in this project cleans text the same way.

Requires: ftfy  (pip install ftfy)
"""

import re
import pandas as pd
import ftfy

# One or more repeats of the mojibake unit -> a single real "�"
MOJIBAKE_UNIT = re.compile(r"(?:ï¿½)+")

# A lone "�" sitting between two letters is almost always a mangled
# apostrophe in a contraction (it's, can't, haven't, ...)
REPLACEMENT_BETWEEN_LETTERS = re.compile(r"(?<=[A-Za-z])�+(?=[A-Za-z])")


def clean_text(text):
    """Clean mojibake / encoding artifacts out of a single text value."""
    if pd.isna(text):
        return text

    text = str(text)

    # Step 1: collapse the "ï¿½ï¿½ï¿½..." garbage into the real replacement char
    text = MOJIBAKE_UNIT.sub("�", text)

    # Step 2: let ftfy fix any other/ordinary mojibake it recognizes
    text = ftfy.fix_text(text)

    # ftfy may have left behind more "ï¿½" runs (from re-fixing) - collapse again
    text = MOJIBAKE_UNIT.sub("�", text)

    # Step 3: turn unrecoverable replacement chars into something readable
    text = REPLACEMENT_BETWEEN_LETTERS.sub("'", text)   # it's, can't, haven't
    text = text.replace("�", " ")                   # anything left -> space

    # Step 4: tidy up whitespace created by the substitutions
    text = re.sub(r"\s+", " ", text).strip()

    return text


def has_mojibake(series):
    """Count how many values in a pandas Series still contain mojibake."""
    return series.astype(str).str.contains("ï¿½|�", na=False).sum()
