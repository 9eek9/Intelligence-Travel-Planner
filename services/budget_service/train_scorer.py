"""
Training script for Package Scorer XGBoost model
Run this once to train and save the model
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import pickle
import os

def generate_synthetic_training_data(n_samples=2000):
    """
    Generate synthetic training data for package scoring
    In production, replace this with real user ratings and booking data
    """
    np.random.seed(42)
    
    data = []
    for _ in range(n_samples):
        # Generate realistic package features
        budget_util = np.random.uniform(0.5, 1.0)
        budget_remaining = 1.0 - budget_util
        has_flight = np.random.choice([0, 1], p=[0.2, 0.8])
        flight_ratio = np.random.uniform(0.3, 0.5) if has_flight else 0
        has_hotel = np.random.choice([0, 1], p=[0.1, 0.9])
        hotel_ratio = np.random.uniform(0.2, 0.4) if has_hotel else 0
        num_activities = np.random.randint(0, 10)
        activities_ratio = np.random.uniform(0.1, 0.3) if num_activities > 0 else 0
        meals_ratio = np.random.uniform(0.05, 0.15)
        transit_ratio = np.random.uniform(0.02, 0.08)
        
        # Travel style (one-hot encoded)
        style = np.random.choice(['budget', 'moderate', 'luxury'], p=[0.3, 0.5, 0.2])
        style_budget = 1 if style == 'budget' else 0
        style_moderate = 1 if style == 'moderate' else 0
        style_luxury = 1 if style == 'luxury' else 0
        
        destination_hash = np.random.uniform(0, 1)
        completeness = (has_flight + has_hotel + (1 if num_activities > 0 else 0)) / 3
        
        # Generate target score using realistic logic
        # Value component: optimal budget usage around 85-95%
        if 0.85 <= budget_util <= 0.95:
            value_component = 100
        elif 0.70 <= budget_util < 0.85:
            value_component = 85
        else:
            value_component = max(50, 100 - abs(90 - budget_util * 100))
        
        # Convenience: having flight + hotel + activities
        convenience_component = 60
        if has_flight:
            convenience_component += 20
        if has_hotel:
            convenience_component += 20
        convenience_component = min(convenience_component, 100)
        
        # Experience: more activities + better hotel = better experience
        experience_component = 50 + min(num_activities * 5, 30)
        if hotel_ratio > 0.3:
            experience_component += 20
        experience_component = min(experience_component, 100)
        
        # Weighted score with some realistic noise
        target_score = (
            value_component * 0.30 +
            convenience_component * 0.25 +
            experience_component * 0.45
        ) + np.random.normal(0, 3)  # Add slight noise
        
        target_score = np.clip(target_score, 0, 100)
        
        features = [
            budget_util, budget_remaining, has_flight, flight_ratio,
            has_hotel, hotel_ratio, num_activities, activities_ratio,
            meals_ratio, transit_ratio, style_budget, style_moderate,
            style_luxury, destination_hash, completeness
        ]
        
        data.append(features + [target_score])
    
    columns = [
        'budget_util', 'budget_remaining', 'has_flight', 'flight_ratio',
        'has_hotel', 'hotel_ratio', 'num_activities', 'activities_ratio',
        'meals_ratio', 'transit_ratio', 'style_budget', 'style_moderate',
        'style_luxury', 'destination_hash', 'completeness', 'score'
    ]
    
    return pd.DataFrame(data, columns=columns)

def train_xgboost_model():
    """Train XGBoost model for package scoring"""
    
    print("=" * 60)
    print("XGBOOST PACKAGE SCORER TRAINING")
    print("=" * 60)
    
    # Generate training data
    print("\nGenerating training data...")
    df = generate_synthetic_training_data(n_samples=2000)
    print(f"Generated {len(df)} training samples")
    
    # Split features and target
    X = df.drop('score', axis=1)
    y = df['score']
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"   Training set: {len(X_train)} samples")
    print(f"   Test set: {len(X_test)} samples")
    
    # Train XGBoost model
    print("\n Training XGBoost model...")
    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=0
    )
    
    model.fit(X_train, y_train, verbose=False)
    
    # Evaluate on test set
    print("\n Evaluating model performance...")
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    train_mse = mean_squared_error(y_train, y_pred_train)
    test_mse = mean_squared_error(y_test, y_pred_test)
    train_mae = mean_absolute_error(y_train, y_pred_train)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    
    print(f"\n   Training Metrics:")
    print(f"   - MSE:  {train_mse:.2f}")
    print(f"   - MAE:  {train_mae:.2f}")
    print(f"   - R²:   {train_r2:.4f}")
    
    print(f"\n   Test Metrics:")
    print(f"   - MSE:  {test_mse:.2f}")
    print(f"   - MAE:  {test_mae:.2f}")
    print(f"   - R²:   {test_r2:.4f}")
    
    # Feature importance
    print("\n Top 5 Most Important Features:")
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for idx, row in feature_importance.head(5).iterrows():
        print(f"   {row['feature']:20s}: {row['importance']:.4f}")
    
    # Save model
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    model_path = os.path.join(models_dir, 'package_scorer.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"\n Model saved to: {model_path}")
    print("=" * 60)
    print("RAINING COMPLETE!")
    print("=" * 60)
    
    return model

if __name__ == "__main__":
    train_xgboost_model()
