# train_detector.py
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# 1. Load your assembled training data
print("Loading training_data.csv...")
try:
    df = pd.read_csv('training_data.csv')
except FileNotFoundError:
    print("Error: 'training_data.csv' not found. Please create it first by running the feature extractor on your labeled chats.")
    exit()

# 2. Define Features (X) and Target (y)
# The 'label' column is what we want to predict.
# All other columns are the features.
X = df.drop('label', axis=1)
y = df['label']

# 3. Split data for training and testing
# This lets us see how well the model performs on data it hasn't seen before.
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

# 4. Initialize and Train the LightGBM Model
print("Training the LightGBM detector model...")
# The parameters can be tuned, but the defaults are a great start.
model = lgb.LGBMClassifier(objective='binary', random_state=42)
model.fit(X_train, y_train)

# 5. Evaluate the Model's Performance
print("\n--- Model Evaluation ---")
predictions = model.predict(X_test)

print("Confusion Matrix:")
# A confusion matrix shows True Positives, False Positives, etc.
print(confusion_matrix(y_test, predictions))

print("\nClassification Report:")
# This report shows precision, recall, and f1-score.
# High precision for class '1' means fewer false alarms.
print(classification_report(y_test, predictions, target_names=['Benign (0)', 'Honeytrap (1)']))

# 6. Save the Final Model
print("\nSaving the trained model to 'honeytrap_detector.joblib'...")
joblib.dump(model, 'honeytrap_detector.joblib')
print("✅ Model training complete and saved!")