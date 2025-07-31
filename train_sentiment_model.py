# train_sentiment_model.py
import pandas as pd
import joblib
import numpy as np # --- VIZ: Added for numerical operations
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay

# --- VIZ: Import visualization libraries ---
import matplotlib.pyplot as plt
import seaborn as sns


TRAINING_CSV = 'training_data.csv'
SENTIMENT_MODEL_PATH = 'sentiment_model.joblib'

# --- VIZ: Function to plot the confusion matrix ---
def plot_confusion_matrix(y_true, y_pred, class_names):
    """Plots a confusion matrix for the model's predictions."""
    print("\n--- Displaying Confusion Matrix ---")
    cm = confusion_matrix(y_true, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_names)
    
    sns.set_theme(style="white")
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.grid(False)
    disp.plot(ax=ax, cmap=plt.cm.Blues, colorbar=False)
    
    ax.set_title("Confusion Matrix: Sentiment Model", fontsize=16)
    ax.set_xlabel("Predicted Label", fontsize=12)
    ax.set_ylabel("True Label", fontsize=12)
    plt.show()

# --- VIZ: Function to plot the logistic regression decision boundary ---
def plot_decision_boundary(model, X_test, y_test):
    """Plots the decision boundary for a single-feature logistic regression model."""
    print("\n--- Displaying Model Decision Boundary ---")
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot the actual data points from the test set
    sns.stripplot(x=X_test.iloc[:, 0], y=y_test, ax=ax, palette="Set2", jitter=0.1, alpha=0.7, label='Actual Data')
    
    # Create a smooth range of values for the feature
    x_range = np.linspace(X_test.iloc[:, 0].min(), X_test.iloc[:, 0].max(), 300).reshape(-1, 1)
    
    # Get the model's predicted probability for that range
    y_proba = model.predict_proba(x_range)[:, 1]
    
    # Plot the model's decision curve
    ax.plot(x_range, y_proba, color='red', lw=2, label='Model Probability Curve')
    
    # Draw the 50% decision threshold
    ax.axhline(0.5, ls='--', color='black', label='Decision Boundary (0.5)')

    ax.set_title("Model Decision Boundary", fontsize=16)
    ax.set_xlabel(X_test.columns[0], fontsize=12)
    ax.set_ylabel("Probability of being a Honeytrap", fontsize=12)
    ax.legend()
    plt.show()


def main():
    """Trains a simple logistic regression model based only on the sentiment_escalation feature."""
    print(f"--- Training Sentiment Escalation Model ---")
    df = pd.read_csv(TRAINING_CSV)
    X = df[['sentiment_escalation']]
    y = df['label']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    
    model = LogisticRegression(random_state=42, class_weight='balanced')
    model.fit(X_train, y_train)

    print("\n--- Sentiment Model Evaluation ---")
    predictions = model.predict(X_test)
    class_names = ['Benign (0)', 'Honeytrap (1)']
    
    print(classification_report(y_test, predictions, target_names=class_names))

    # --- VIZ: Call the visualization functions ---
    plot_confusion_matrix(y_test, predictions, class_names)
    plot_decision_boundary(model, X_test, y_test)
    
    joblib.dump(model, SENTIMENT_MODEL_PATH)
    print(f"\n✅ New sentiment model saved to '{SENTIMENT_MODEL_PATH}'!")


if __name__ == "__main__":
    main()