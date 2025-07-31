"""
A one-time script to train the honeytrap detector with visualizations,
early stopping, and a final save step.
"""
import pandas as pd
import joblib
import lightgbm as lgb
from sklearn.model_selection import StratifiedKFold, RandomizedSearchCV, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectKBest, f_classif
# --- VIZ: Import visualization libraries and metrics ---
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay

# --- Configuration ---
TRAINING_CSV = 'training_data.csv'
MODEL_OUTPUT_PATH = 'honeytrap_detector.joblib'

# --- VIZ: Function to plot the training (logloss) curve ---
def plot_training_history(model):
    """Plots the validation logloss during model training."""
    print("\n--- Displaying Training Learning Curve ---")
    try:
        sns.set_theme(style="whitegrid")
        ax = lgb.plot_metric(model, metric='logloss', figsize=(10, 6))
        ax.set_title("Model Training Curve (Validation LogLoss)", fontsize=16)
        ax.set_xlabel("Boosting Round (n_estimators)", fontsize=12)
        ax.set_ylabel("LogLoss", fontsize=12)
        plt.show()
    except Exception as e:
        print(f"Could not plot training history: {e}")

# --- VIZ: Function to plot the confusion matrix ---
def plot_confusion_matrix(y_true, y_pred, class_names):
    """Plots a confusion matrix for the model's predictions."""
    print("\n--- Displaying Confusion Matrix ---")
    try:
        cm = confusion_matrix(y_true, y_pred)
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_names)
        
        sns.set_theme(style="white")
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.grid(False) # Turn off grid for the matrix
        disp.plot(ax=ax, cmap=plt.cm.Blues, colorbar=False)
        
        ax.set_title("Confusion Matrix: Test Set Performance", fontsize=16)
        ax.set_xlabel("Predicted Label", fontsize=12)
        ax.set_ylabel("True Label", fontsize=12)
        plt.show()
    except Exception as e:
        print(f"Could not plot confusion matrix: {e}")

def main():
    print(f"--- Loading Data from '{TRAINING_CSV}' ---")
    try:
        df = pd.read_csv(TRAINING_CSV)
        if 'label' not in df.columns or len(df.index) < 50:
            print("Error: Not enough data for a 3-way split. Need at least 50 rows.")
            return

        X = df.drop('label', axis=1)
        y = df['label']
        feature_names_original = list(X.columns)
        
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val, y_train_val, test_size=0.25, random_state=42, stratify=y_train_val
        )
        
        # Note: Scaling is now done inside the pipeline
        
        lgbm = lgb.LGBMClassifier(objective='binary', random_state=42, is_unbalance=True)
        
        param_grid = {
            'feature_selection__k': range(8, len(feature_names_original) + 1),
            'model__learning_rate': [0.01, 0.05],
            'model__n_estimators': [200, 300, 500],
            'model__num_leaves': [20, 31, 40],
        }

        cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
        
        pipeline = Pipeline([
            ('feature_selection', SelectKBest(f_classif)),
            ('scaler', StandardScaler()),
            ('model', lgbm)
        ])
        
        random_search = RandomizedSearchCV(
            estimator=pipeline,
            param_distributions=param_grid,
            n_iter=10,
            scoring='f1_weighted',
            cv=cv, n_jobs=-1, verbose=1, random_state=42
        )

        print("\n--- Starting Randomized Hyperparameter Search ---")
        random_search.fit(X_train, y_train)
        
        print(f"\n🏆 Best Parameters Found: {random_search.best_params_}")
        
        best_pipeline = random_search.best_estimator_

        # To use early stopping for evaluation, we need to fit the best model manually
        print("\n--- Training model with best params and Early Stopping for evaluation ---")
        
        # Extract best params and create final model instance
        best_params = random_search.best_params_
        final_model = lgb.LGBMClassifier(
            objective='binary', random_state=42, is_unbalance=True,
            n_estimators=1000, # High n_estimators for early stopping
            learning_rate=best_params['model__learning_rate'],
            num_leaves=best_params['model__num_leaves'],
        )
        
        # Create a temporary pipeline for evaluation
        eval_pipeline = Pipeline([
            ('feature_selection', SelectKBest(f_classif, k=best_params['feature_selection__k'])),
            ('scaler', StandardScaler()),
        ])
        
        X_train_transformed = eval_pipeline.fit_transform(X_train, y_train)
        X_val_transformed = eval_pipeline.transform(X_val)

        final_model.fit(
            X_train_transformed, y_train,
            eval_set=[(X_val_transformed, y_val)],
            eval_metric='logloss',
            callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=True)]
        )
        
        plot_training_history(final_model)
        
        print("\n--- Final Model Evaluation on Hold-Out Test Set ---")
        X_test_transformed = eval_pipeline.transform(X_test)
        predictions = final_model.predict(X_test_transformed)
        class_names = ['Benign (0)', 'Honeytrap (1)']
        
        print(classification_report(y_test, predictions, target_names=class_names))
        
        plot_confusion_matrix(y_test, predictions, class_names)
        
        # --- ADDED: Retrain and Save Final Pipeline ---
        print("\n--- Retraining final pipeline on the entire dataset for deployment ---")
        # Use the best pipeline found by the search, which has all the correct steps and params
        final_pipeline_to_save = random_search.best_estimator_
        final_pipeline_to_save.fit(X, y)
        
        # Save the entire pipeline (selector, scaler, and model)
        joblib.dump(final_pipeline_to_save, MODEL_OUTPUT_PATH)
        print(f"\n✅ New OPTIMIZED pipeline saved to '{MODEL_OUTPUT_PATH}'!")

    except Exception as e:
        print(f"An error occurred during model training: {e}")

if __name__ == "__main__":
    main()