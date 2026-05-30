import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pickle
import os

def train():
    # Load combined dataset of both original and newer job postings
    df = pd.read_csv("data/combined_job_postings.csv")

    X = df["text"]
    y = df["is_fake"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    pipeline = Pipeline([
        ("vectorizer", TfidfVectorizer(
            stop_words="english",
            max_features=5000,
            ngram_range=(1, 1)
        )),
        ("classifier", LogisticRegression(
            max_iter=1000,
            C=0.1,
            class_weight="balanced"
        ))
    ])

    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)
    print(classification_report(y_test, predictions))

    os.makedirs("model", exist_ok=True)
    with open("model/model.pkl", "wb") as f:
        pickle.dump(pipeline, f)

    print("Model trained and saved successfully.")

if __name__ == "__main__":
    train()

