import argparse
import csv
import html
import json
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook


STOPWORDS = set("""a an the and or but if while as at by for from in into of on onto to with
about above after against along among around before below beneath beside between
beyond during except inside near off out outside over past per since than through
throughout till toward towards under underneath until up upon via within
i me my mine myself we us our ours ourselves you your yours yourself yourselves
he him his himself she her hers herself it its itself they them their theirs
themselves this that these those what which who whom whose
am is are was were be been being have has had having do does did doing
can could may might must shall should will would
here there where when why how then once now
all any both each either few many more most much other others some such
only own same so too also really just still even ever already yet
it's that's there's here's what's who's i'd you'd he'd she'd we'd they'd
""".split())
NEGATIONS = {'no', 'not', 'never', 'nor', 'neither', 'without'}
STOPWORDS.difference_update(NEGATIONS)

TOKEN_RE = re.compile(r"[^\W_]+(?:'[^\W_]+)*", re.UNICODE)
URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.I)
HTML_TAG_RE = re.compile(r"</?[A-Za-z][^>]*>")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r'(?<!\w)(?:\+?1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\d)')


def read_sheet(path):
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = wb['Data'] if 'Data' in wb.sheetnames else wb.active
        rows = sheet.iter_rows(values_only=True)
        headers = next(rows)
        return [dict(zip(headers, row)) for row in rows if any(v is not None for v in row)]
    finally:
        wb.close()


def id_string(value):
    if isinstance(value, (int, float)) and float(value).is_integer():
        return str(int(value))
    return str(value).strip()


def metadata_value(value):
    if value is None:
        return ''
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def clean_tokens(text):
    text = unicodedata.normalize('NFC', str(text))
    text = html.unescape(text).translate(str.maketrans({'’': "'", '‘': "'"}))
    text = URL_RE.sub(' ', text)
    text = HTML_TAG_RE.sub(' ', text)
    text = EMAIL_RE.sub(' ', text)
    text = PHONE_RE.sub(' ', text)
    text = text.lower()

    for source, replacement in [("won't", 'will not'), ("can't", 'can not'),
                                ("shan't", 'shall not'), ("ain't", 'is not'),
                                ('cannot', 'can not')]:
        text = re.sub(r'\b' + re.escape(source) + r'\b', replacement, text)
    text = re.sub(r"\b([a-z]+)n't\b", r'\1 not', text)
    text = re.sub(r"\bi'm\b", 'i am', text)
    text = re.sub(r"\b(you|we|they)'re\b", r'\1 are', text)
    text = re.sub(r"\b(i|you|we|they)'ve\b", r'\1 have', text)
    text = re.sub(r"\b(i|you|he|she|it|we|they)'ll\b", r'\1 will', text)

    return TOKEN_RE.findall(text)


def prepare(case3_path, source_path, output_path):
    case3_rows = read_sheet(case3_path)
    source_rows = read_sheet(source_path)
    source_by_id = {id_string(r['reviewer_id']): r for r in source_rows}
    if len(source_by_id) != len(source_rows):
        raise ValueError('Source IDs are not unique; cannot safely attach metadata.')

    prepared = []
    for row in case3_rows:
        review_id = id_string(row['reviewer_id'])
        if review_id not in source_by_id:
            raise ValueError('Case 3 ID missing from source: ' + review_id)
        original = source_by_id[review_id]
        rating = row['star_rating']
        if not isinstance(rating, (int, float)) or int(rating) != rating or not 1 <= rating <= 5:
            raise ValueError('Invalid star rating at ID ' + review_id)
        if int(rating) != int(original['review-label']):
            raise ValueError('Case 3/source star ratings disagree at ID ' + review_id)
        text = row.get('review_text')
        if not isinstance(text, str) or not text.strip():
            raise ValueError('Empty Case 3 review text at ID ' + review_id)

        has_body = original.get('review') is not None and bool(str(original['review']).strip())
        tokens = clean_tokens(text)
        topic_tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1 and not t.isdigit()]
        if not tokens or not topic_tokens:
            raise ValueError('Cleaning produced an empty document at ID ' + review_id)

        record = {'reviewer_id': review_id}
        for name in ['store_location', 'latitude', 'longitude', 'date', 'month', 'year', 'title']:
            value = metadata_value(original.get(name))
            if name == 'title' and isinstance(value, str):
                value = PHONE_RE.sub('[contact number removed]', value)
            record[name] = value
        record.update({
            'review_text': text,
            'star_rating': int(rating),
            'clean_text': ' '.join(tokens),
            'topic_tokens': json.dumps(topic_tokens, ensure_ascii=False),
            'text_source': 'review_body' if has_body else 'title_only',
        })
        prepared.append(record)

    ids = [r['reviewer_id'] for r in prepared]
    if len(ids) != len(set(ids)):
        raise ValueError('Case 3 IDs are not unique.')
    if {r['reviewer_id'] for r in prepared} != set(source_by_id):
        raise ValueError('Source and Case 3 row coverage differs; resolve before exporting.')

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(prepared[0]))
        writer.writeheader()
        writer.writerows(prepared)

    return prepared


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--case3', type=Path, default=Path('Case3_Data_Simple.xlsx'))
    parser.add_argument('--source', type=Path, default=Path('INSY669 Dataset.xlsx'))
    parser.add_argument('--output', type=Path, default=Path('Case4_MemberA_Cleaned_TeePublic.csv'))
    args = parser.parse_args()
    prepare(args.case3, args.source, args.output)
