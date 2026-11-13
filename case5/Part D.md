**Part D: Comparison Table**

All three models used the same train set and test set, so every number below comes from the same test set. F1, precision and recall are for the spam class 

|  | **TF-IDF** | **Word2Vec avg** | **BERT** |
|---|---|---|---|
| **Representation** | TF-IDF | Average of word2vec-google-news-300 word vectors | bert-base-uncased [CLS] embedding |
| **Dimensionality** | 7,702 | 300 | 768 |
| **Best k** | 1 | 3 (cosine, distance-weighted) | 5 |
| **Spam-class F1** | 0.9286 | 0.8372 | 0.9338 |
| **Test errors (FP / FN)** | 1 / 19 | 26 / 23 | 12 / 8 |
| **Key strengths** | Almost no false alarms (1 ham flagged, spam precision 0.9924). Picks up spam words directly: of the 130 spam it caught, 34 had “free” and 37 had “win/won/winner/prize”. | Small, dense vectors (300-d). | Best spam F1 and recall (0.9463), so it missed the least spam (8). Results barely change with k (CV spam F1 0.9367–0.9398 for all k). |
| **Key weaknesses** | Missed 19 spam (recall 0.8725), more than BERT, since it only matches exact words. Its one false positive shared words like “bloke” and “girl” with a spam message in training. | Lowest spam F1 and many errors on both sides. Averaging loses word order and negation, and words not in the vocabulary are just skipped (we only split on spaces). | More false alarms than TF-IDF (12 vs 1, spam precision 0.9216). Costly to build: the embeddings took 18.6 s even on a GPU. |
| **Runtime / compute cost** | Training 1.66 s, prediction 0.04 s. No pretrained model. | Training + prediction 2.96 s Needs a pretrained model. | Embedding 18.6 s on GPU, training 1.99 s, prediction 0.075 s. |

**Compare the models:**

As shown in the table above, we used spam F1 as the main measure because spam is only about 13% of the messages, so accuracy alone can look high even for a weak model. Based on this, BERT was the best model overall, with the highest spam F1 (0.9338). However, it was only slightly ahead of TF-IDF (0.9286), and both got the same test accuracy (0.9821). The real difference is the type of mistake. BERT missed only 8 spam messages compared with 19 for TF-IDF, but it flagged 12 ham messages as spam while TF-IDF flagged just 1. So if the goal is to catch as much spam as possible, BERT is the better choice, but if wrongly blocking a real message is more costly, TF-IDF is the safer option. TF-IDF is also much cheaper to run: it needs no pretrained model and its CV + fit took 1.66 s, while BERT's embeddings alone took 18.6 s even on a GPU. Word2Vec averaging was clearly the weakest, with the lowest spam F1 (0.8372) and the most errors on both sides (26 false positives and 23 false negatives), so we would not choose it for this task.
 
Overall, BERT was chosen as the best-performing model because it had the highest spam F1 and missed the fewest spam messages, even though its lead over TF-IDF was small.

