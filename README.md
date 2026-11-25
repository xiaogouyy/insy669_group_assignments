# INSY 669/670 Text Analytics: Group Case Assignments

Each case folder uses the same layout:

| Folder | Contents |
|---|---|
| `code/` | Python scripts and Jupyter notebooks |
| `data/` | Input datasets and intermediate data files |
| `results/` | Outputs produced by the code (scores, predictions, charts, tables) |
| `docs/` | Assignment brief and submitted report |

Code reads from `../data/` and writes to `../results/`, so run scripts and notebooks from inside their `code/` folder.

## Cases

| Case | Folder | Main task |
|---|---|---|
| 1 | `case1_text_mining_retail_reviews` | Collect and clean TeePublic reviews (US vs Canada), then compare word frequencies by sentiment |
| 2 | `case2_word_association_rules` | Group reviews by star rating and mine word association rules (support, confidence, lift) |
| 3 | `case3_sentiment_star_rating_regression` | Score sentiment with VADER, SentiStrength and KNN, then regress star rating on the three scores |
| 4 | `case4_lda_topic_knn_classifier` | Find topics with LDA, label one review category, then build and evaluate a KNN classifier |
| 5 | `case5_spam_detection_tfidf_bert_knn` | Classify SMS spam: TF-IDF + KNN (A), Part B model, BERT embeddings + KNN (C), comparison (D), error analysis (E), optional challenge |
