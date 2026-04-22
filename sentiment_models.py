from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
from transformers import pipeline

vader_analyzer = SentimentIntensityAnalyzer()

print("Loading transformer model, please wait...")
transformer_pipeline = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english"
)
print("Transformer model loaded.")


def vader_sentiment(text):
    scores = vader_analyzer.polarity_scores(text)
    compound = scores["compound"]

    if compound >= 0.05:
        label = "Positive"
    elif compound <= -0.05:
        label = "Negative"
    else:
        label = "Neutral"

    return {"label": label, "score": round(compound, 4)}


def textblob_sentiment(text):
    polarity = TextBlob(text).sentiment.polarity

    if polarity > 0.05:
        label = "Positive"
    elif polarity < -0.05:
        label = "Negative"
    else:
        label = "Neutral"

    return {"label": label, "score": round(polarity, 4)}


def transformer_sentiment(text):
    try:
        result = transformer_pipeline(text[:512])[0]
        raw_label = result["label"].upper()
        score = round(result["score"], 4)

        if raw_label == "POSITIVE":
            label = "Positive"
        elif raw_label == "NEGATIVE":
            label = "Negative"
        else:
            label = "Neutral"

        return {"label": label, "score": score}
    except Exception:
        return {"label": "Neutral", "score": 0.0}