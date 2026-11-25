import re
import string
import pandas as pd
from typing import List, Tuple
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag, ngrams
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, classification_report, confusion_matrix)

import nltk
nltk.download(['punkt', 'punkt_tab', 'stopwords', 'wordnet',
               'averaged_perceptron_tagger', 'averaged_perceptron_tagger_eng'],
              quiet=True)

# 1. Preprocess
class ReviewTextPipeline:
    def __init__(self):
        self.stop_words = set(stopwords.words("english")) - {
            "no", "not", "nor", "never", "none", "cannot",
            "n't", "isn't", "wasn't", "don't", "doesn't",
            "didn't", "won't", "wouldn't", "shouldn't"
        }
        self.lemmatizer = WordNetLemmatizer()

    def clean(self, text: str) -> str:
        text = str(text).lower()
        text = re.sub(r"[^a-z\s']", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        return [t for t in tokens
                if t not in self.stop_words
                and t not in string.punctuation
                and len(t) > 1]

    def lemmatize(self, tokens: List[str]) -> List[str]:
        def get_wordnet_pos(tag):
            if tag.startswith('J'): return wordnet.ADJ
            if tag.startswith('V'): return wordnet.VERB
            if tag.startswith('N'): return wordnet.NOUN
            if tag.startswith('R'): return wordnet.ADV
            return wordnet.NOUN
        tagged = pos_tag(tokens)
        return [self.lemmatizer.lemmatize(w, get_wordnet_pos(t)) for w, t in tagged]

    def generate_ngrams(self, tokens: List[str],
                        n_range: Tuple[int, int] = (1, 3)) -> List[str]:
        return [" ".join(g)
                for n in range(n_range[0], n_range[1] + 1)
                for g in ngrams(tokens, n)]

    def process(self, text: str, n_range: Tuple[int, int] = (1, 3)):
        cleaned  = self.clean(text)
        tokens   = word_tokenize(cleaned)
        filtered = self.remove_stopwords(tokens)
        lemmas   = self.lemmatize(filtered)
        grams    = self.generate_ngrams(lemmas, n_range)
        return cleaned, tokens, filtered, lemmas, grams

    def preprocess_for_tfidf(self, text: str) -> str:
        """Return lemmatized string ready for TF-IDF."""
        _, _, _, lemmas, _ = self.process(text, n_range=(1, 1))
        return " ".join(lemmas)


# 2. Load Excel data
df = pd.read_excel("../data/Case3_Data1.xlsx", sheet_name="Data")

print(f"Loaded {len(df)} rows")
print(f"Columns: {list(df.columns)}")
print(f"\nRating distribution:\n{df['star_rating'].value_counts().sort_index()}\n")

df['review_text'] = df['review_text'].fillna("")


# 3. Build binary sentiment label
# 4-5 stars → positive (+1); 3 stars → neutral (0); 1-2 stars → negative (-1)
def rating_to_sentiment(r):
    if r >= 4:  return 1
    if r == 3:  return 0
    return -1

df['sentiment'] = df['star_rating'].apply(rating_to_sentiment)

print("3-class label distribution:")
counts = df['sentiment'].value_counts().sort_index()
labels = {-1: 'negative', 0: 'neutral', 1: 'positive'}
for k, v in counts.items():
    print(f"  {labels[k]:>8} ({k:+d}): {v} rows  ({v/len(df)*100:.1f}%)")
print()


# 4. Preprocess every review
pipeline = ReviewTextPipeline()

print("Preprocessing reviews...")
df['processed'] = df['review_text'].apply(pipeline.preprocess_for_tfidf)

# sanity check on one row
print(f"\nExample:")
print(f"  Original : {df.iloc[0]['review_text'][:80]}...")
print(f"  Processed: {df.iloc[0]['processed'][:80]}...\n")


# 5. TF-IDF representation
vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),       # unigrams + bigrams (trigrams sparsify small data)
    min_df=2,                 # ignore terms appearing in <2 reviews
    max_df=0.9,               # ignore terms in >90% of reviews
    sublinear_tf=True,
)

X = vectorizer.fit_transform(df['processed'])
y = df['sentiment'].values

print(f"TF-IDF matrix: {X.shape[0]} reviews × {X.shape[1]} features\n")


# 6. Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)


# 7. Train KNN
knn = KNeighborsClassifier(n_neighbors=7, metric='cosine', weights='distance', n_jobs=-1)
knn.fit(X_train, y_train)


# 8. Evaluate
y_pred = knn.predict(X_test)

print("=" * 55)
print("KNN 3-CLASS SENTIMENT — RESULTS")
print("=" * 55)
print(f"Accuracy        : {accuracy_score(y_test, y_pred):.4f}")
print(f"Macro Precision : {precision_score(y_test, y_pred, average='macro'):.4f}")
print(f"Macro Recall    : {recall_score(y_test, y_pred, average='macro'):.4f}")
print(f"Macro F1        : {f1_score(y_test, y_pred, average='macro'):.4f}")
print(f"Weighted F1     : {f1_score(y_test, y_pred, average='weighted'):.4f}")

print(f"\nClassification report:")
print(classification_report(
    y_test, y_pred,
    labels=[-1, 0, 1],
    target_names=['negative', 'neutral', 'positive'],
    zero_division=0,
))

print(f"Confusion matrix (rows=true, cols=pred):")
print(f"  order: [-1, 0, +1]")
print(confusion_matrix(y_test, y_pred, labels=[-1, 0, 1]))


# 9. Cross-validation
cv_scores = cross_val_score(knn, X, y, cv=5, scoring='f1_macro')
print(f"\n5-fold CV F1: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")


# 10. Score on FULL dataset & write output
df['predicted_sentiment']  = knn.predict(X)
proba = knn.predict_proba(X)
df['prob_negative'] = proba[:, list(knn.classes_).index(-1)]
df['prob_neutral']  = proba[:, list(knn.classes_).index(0)]
df['prob_positive'] = proba[:, list(knn.classes_).index(1)]

# human-readable class label
label_map = {-1: 'negative', 0: 'neutral', 1: 'positive'}
df['predicted_label'] = df['predicted_sentiment'].map(label_map)

df.to_csv("../results/Case3_sentiment_predictions.csv", index=False, encoding="utf-8-sig")