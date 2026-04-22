from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


def evaluate_model(y_true, y_pred):
    return {
        "accuracy": round(accuracy_score(y_true, y_pred), 3),
        "precision": round(precision_score(y_true, y_pred, average="weighted", zero_division=0), 3),
        "recall": round(recall_score(y_true, y_pred, average="weighted", zero_division=0), 3),
        "f1_score": round(f1_score(y_true, y_pred, average="weighted", zero_division=0), 3)
    }