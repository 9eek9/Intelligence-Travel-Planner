"""
Train XGBoost model for budget allocation using synthetic data
"""

import sys
import os

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from ml_models.synthetic_data_generator import SyntheticDataGenerator
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
import pickle
import numpy as np

def train_budget_allocation_model():
    """Train XGBoost model to predict optimal budget allocation"""
    
    print("="*60)
    print("TRAINING BUDGET ALLOCATION MODEL WITH YOUR DATA")
    print("="*60)
    
    # Generate data using your sophisticated generator
    print("\nGenerating training data...")
    generator = SyntheticDataGenerator()
    df = generator.generate_training_data(n_samples=10000)
    
    # Show statistics
    generator.print_statistics(df)
    
    # Prepare features
    print("Preparing features...")
    
    # Encode categorical variables
    le_destination = LabelEncoder()
    le_region = LabelEncoder()
    le_season = LabelEncoder()
    le_purpose = LabelEncoder()
    le_accommodation = LabelEncoder()
    
    df['destination_encoded'] = le_destination.fit_transform(df['destination'])
    df['region_encoded'] = le_region.fit_transform(df['region'])
    df['season_encoded'] = le_season.fit_transform(df['season'])
    df['purpose_encoded'] = le_purpose.fit_transform(df['purpose'])
    df['accommodation_encoded'] = le_accommodation.fit_transform(df['accommodation_type'])
    
    # Feature columns
    feature_cols = [
        'duration', 'total_budget', 'travelers', 'budget_per_day', 
        'budget_per_person', 'cost_index', 'destination_encoded',
        'region_encoded', 'season_encoded', 'purpose_encoded', 
        'accommodation_encoded'
    ]
    
    X = df[feature_cols]
    
    # Train separate models for each budget category
    models = {}
    encoders = {
        'destination': le_destination,
        'region': le_region,
        'season': le_season,
        'purpose': le_purpose,
        'accommodation': le_accommodation
    }
    
    for target in ['accommodation_pct', 'transportation_pct', 'food_pct', 
                   'activities_pct', 'miscellaneous_pct']:
        
        print(f"\nTraining model for {target}...")
        y = df[target]
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        model = xgb.XGBRegressor(
            objective='reg:squarederror',
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )
        
        model.fit(X_train, y_train, verbose=False)
        
        # Evaluate
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
        
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        test_mae = np.mean(np.abs(y_test - y_pred_test))
        
        print(f"   Train R²: {train_r2:.4f}")
        print(f"   Test R²:  {test_r2:.4f}")
        print(f"   Test MAE: {test_mae:.4f} ({test_mae*100:.2f}%)")
        
        models[target] = model
    
    # Save models
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    model_data = {
        'models': models,
        'encoders': encoders,
        'feature_cols': feature_cols
    }
    
    model_path = os.path.join(models_dir, 'budget_allocator.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
    
    print(f"\nModels saved to: {model_path}")
    print("="*60)
    print("TRAINING COMPLETE!")
    print("="*60)
    
    return models, encoders

if __name__ == "__main__":
    train_budget_allocation_model()
