"""
Association rules (lift & confidence) for each sentiment group.

Reads the 'grouped by rating' sheet in fixed_data.xlsx. Each review is one
transaction whose items are its unique ngrams (1-, 2- and 3-grams). For every
pair of items A, B that co-occur in at least MIN_COUNT reviews of a group:

    support(A->B)    = count(A and B) / n_reviews
    confidence(A->B) = count(A and B) / count(A)
    lift(A->B)       = confidence(A->B) / (count(B) / n_reviews)

Pairs whose items share a word (e.g. 'great' and 'great quality') are skipped,
since they co-occur by construction.

Writes one sheet per group ('rules - negative', ...) back into fixed_data.xlsx.
"""

from collections import Counter
from itertools import combinations

from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

FILE = "../data/fixed_data.xlsx"
GROUPED_SHEET = "grouped by rating"

# group name -> (minimum number of reviews a pair must co-occur in, header colour)
GROUPS = {
    "Negative": (2, "C00000"),
    "Neutral": (2, "7F7F7F"),
    "Positive": (3, "2E7D32"),
}
MIN_CONFIDENCE = 0.0

OUT_COLUMNS = ["antecedent", "consequent", "antecedent_count", "consequent_count",
               "pair_count", "n_reviews", "support", "confidence", "lift"]


def read_groups(ws):
    """Split the 'grouped by rating' sheet back into {group: [ngrams strings]}."""
    groups = {name: [] for name in GROUPS}
    current, header = None, None
    for row in ws.iter_rows(values_only=True):
        first = row[0]
        if isinstance(first, str) and first.split()[0].title() in GROUPS:
            current, header = first.split()[0].title(), None
        elif current and header is None and first == "reviewer_id":
            header = list(row)
            ngrams_idx = header.index("ngrams")
        elif current and header and any(v is not None for v in row):
            groups[current].append(row[ngrams_idx])
    return groups


def to_transaction(ngrams):
    if not ngrams:
        return set()
    return {t.strip() for t in str(ngrams).split("|") if t.strip()}


def mine_rules(transactions, min_count, min_confidence=MIN_CONFIDENCE):
    n = len(transactions)
    item_counts = Counter(item for t in transactions for item in t)

    # Apriori pruning: only items frequent enough on their own can form a frequent pair
    frequent = {i for i, c in item_counts.items() if c >= min_count}
    pair_counts = Counter()
    for t in transactions:
        items = sorted(t & frequent)
        for a, b in combinations(items, 2):
            if set(a.split()) & set(b.split()):
                continue
            pair_counts[(a, b)] += 1

    rules = []
    for (a, b), ab in pair_counts.items():
        if ab < min_count:
            continue
        for x, y in ((a, b), (b, a)):
            confidence = ab / item_counts[x]
            if confidence < min_confidence:
                continue
            lift = confidence / (item_counts[y] / n)
            rules.append([x, y, item_counts[x], item_counts[y], ab, n,
                          round(ab / n, 4), round(confidence, 4), round(lift, 4)])

    rules.sort(key=lambda r: (-r[8], -r[7], -r[4], r[0], r[1]))
    return rules


def write_sheet(wb, name, rules, color):
    if name in wb.sheetnames:
        del wb[name]
    ws = wb.create_sheet(name)
    ws.append(OUT_COLUMNS)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=color)
    for r in rules:
        ws.append(r)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    for c, h in enumerate(OUT_COLUMNS, start=1):
        ws.column_dimensions[get_column_letter(c)].width = 28 if c <= 2 else 16


def main():
    wb = load_workbook(FILE)
    groups = read_groups(wb[GROUPED_SHEET])

    for name, (min_count, color) in GROUPS.items():
        transactions = [to_transaction(g) for g in groups[name]]
        rules = mine_rules(transactions, min_count)
        write_sheet(wb, f"rules - {name.lower()}", rules, color)
        print(f"{name}: {len(transactions)} reviews, {len(rules)} rules (min pair count {min_count})")

    wb.save(FILE)
    print(f"Saved to {FILE}")


if __name__ == "__main__":
    main()
