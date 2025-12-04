"""
Train all ML models at once
"""

import os
import sys
import pickle
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

print("="*70)
print("🚀 TRAINING ALL ML MODELS FOR SMART TRAVEL SYSTEM")
print("="*70)

# ============================================================================
# MODEL 1: PACKAGE SCORER
# ============================================================================
def train_package_scorer():
    """Train XGBoost model for package scoring"""
    
    print("\n" + "="*70)
    print("📊 MODEL 1: PACKAGE SCORER")
    print("="*70)
    
    print("\n📊 Generating training data...")
    np.random.seed(42)
    
    data = []
    for _ in range(2000):
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
        
        style = np.random.choice(['budget', 'moderate', 'luxury'], p=[0.3, 0.5, 0.2])
        style_budget = 1 if style == 'budget' else 0
        style_moderate = 1 if style == 'moderate' else 0
        style_luxury = 1 if style == 'luxury' else 0
        
        destination_hash = np.random.uniform(0, 1)
        completeness = (has_flight + has_hotel + (1 if num_activities > 0 else 0)) / 3
        
        # Generate target score
        if 0.85 <= budget_util <= 0.95:
            value_component = 100
        elif 0.70 <= budget_util < 0.85:
            value_component = 85
        else:
            value_component = max(50, 100 - abs(90 - budget_util * 100))
        
        convenience_component = 60
        if has_flight:
            convenience_component += 20
        if has_hotel:
            convenience_component += 20
        convenience_component = min(convenience_component, 100)
        
        experience_component = 50 + min(num_activities * 5, 30)
        if hotel_ratio > 0.3:
            experience_component += 20
        experience_component = min(experience_component, 100)
        
        target_score = (
            value_component * 0.30 +
            convenience_component * 0.25 +
            experience_component * 0.45
        ) + np.random.normal(0, 3)
        
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
    
    df = pd.DataFrame(data, columns=columns)
    print(f"✅ Generated {len(df)} training samples")
    
    X = df.drop('score', axis=1)
    y = df['score']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"   Training set: {len(X_train)} samples")
    print(f"   Test set: {len(X_test)} samples")
    
    print("\n🤖 Training XGBoost model...")
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
    
    y_pred_test = model.predict(X_test)
    test_mse = mean_squared_error(y_test, y_pred_test)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    test_r2 = r2_score(y_test, y_pred_test)
    
    print(f"\n📈 Model Performance:")
    print(f"   MSE:  {test_mse:.2f}")
    print(f"   MAE:  {test_mae:.2f}")
    print(f"   R²:   {test_r2:.4f}")
    
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    model_path = os.path.join(models_dir, 'package_scorer.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"\n💾 Model saved to: {model_path}")
    return model

# ============================================================================
# MODEL 2: BUDGET ALLOCATOR (XGBOOST)
# ============================================================================
def train_budget_allocator():
    """Train XGBoost models for budget allocation"""
    
    print("\n" + "="*70)
    print("💰 MODEL 2: BUDGET ALLOCATOR")
    print("="*70)
    
    print("\n📊 Generating training data...")
    np.random.seed(42)
    
    # Generate 5000 synthetic travel budget allocations
    data = []
    destinations = ['Bangkok', 'Paris', 'New York', 'Tokyo', 'London', 
                   'Dubai', 'Rome', 'Barcelona', 'Singapore', 'Bali']
    
    for _ in range(5000):
        # Trip characteristics
        destination = np.random.choice(destinations)
        duration = np.random.randint(3, 15)
        total_budget = np.random.uniform(500, 10000)
        travelers = np.random.randint(1, 5)
        
        # Determine travel style based on budget per day
        budget_per_day = total_budget / duration
        if budget_per_day < 100:
            style = 'budget'
            base_alloc = {'accommodation': 0.35, 'transportation': 0.30, 
                         'food': 0.20, 'activities': 0.10, 'miscellaneous': 0.05}
        elif budget_per_day < 300:
            style = 'moderate'
            base_alloc = {'accommodation': 0.40, 'transportation': 0.25, 
                         'food': 0.18, 'activities': 0.12, 'miscellaneous': 0.05}
        else:
            style = 'luxury'
            base_alloc = {'accommodation': 0.45, 'transportation': 0.20, 
                         'food': 0.15, 'activities': 0.15, 'miscellaneous': 0.05}
        
        # Add realistic variations
        alloc = base_alloc.copy()
        
        # Expensive destinations (Paris, London, New York)
        if destination in ['Paris', 'London', 'New York']:
            alloc['accommodation'] += 0.05
            alloc['food'] += 0.03
            alloc['activities'] -= 0.08
        
        # Budget destinations (Bangkok, Bali)
        elif destination in ['Bangkok', 'Bali']:
            alloc['accommodation'] -= 0.05
            alloc['activities'] += 0.05
        
        # Long trips
        if duration > 10:
            alloc['accommodation'] += 0.03
            alloc['transportation'] -= 0.03
        
        # Add noise
        for key in alloc:
            noise = np.random.uniform(-0.03, 0.03)
            alloc[key] = max(0.05, alloc[key] + noise)
        
        # Normalize to sum to 1.0
        total = sum(alloc.values())
        alloc = {k: v/total for k, v in alloc.items()}
        
        # Encode style
        style_budget = 1 if style == 'budget' else 0
        style_moderate = 1 if style == 'moderate' else 0
        style_luxury = 1 if style == 'luxury' else 0
        
        # Store features and targets
        data.append([
            duration, total_budget, travelers, budget_per_day,
            hash(destination) % 100 / 100,  # Simple destination encoding
            style_budget, style_moderate, style_luxury,
            alloc['accommodation'], alloc['transportation'],
            alloc['food'], alloc['activities'], alloc['miscellaneous']
        ])
    
    columns = [
        'duration', 'total_budget', 'travelers', 'budget_per_day',
        'destination_hash', 'style_budget', 'style_moderate', 'style_luxury',
        'accommodation_pct', 'transportation_pct', 'food_pct', 
        'activities_pct', 'miscellaneous_pct'
    ]
    
    df = pd.DataFrame(data, columns=columns)
    print(f"✅ Generated {len(df)} training samples")
    
    # Feature columns
    feature_cols = ['duration', 'total_budget', 'travelers', 'budget_per_day',
                   'destination_hash', 'style_budget', 'style_moderate', 'style_luxury']
    
    X = df[feature_cols]
    
    # Train separate model for each allocation category
    models = {}
    targets = ['accommodation_pct', 'transportation_pct', 'food_pct', 
              'activities_pct', 'miscellaneous_pct']
    
    for target in targets:
        print(f"\n🤖 Training model for {target}...")
        y = df[target]
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        model = xgb.XGBRegressor(
            objective='reg:squarederror',
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            verbosity=0
        )
        
        model.fit(X_train, y_train, verbose=False)
        
        y_pred_test = model.predict(X_test)
        test_r2 = r2_score(y_test, y_pred_test)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        
        print(f"   Test R²:  {test_r2:.4f}")
        print(f"   Test MAE: {test_mae:.4f} ({test_mae*100:.2f}%)")
        
        models[target] = model
    
    # Save models
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    model_data = {
        'models': models,
        'feature_cols': feature_cols
    }
    
    model_path = os.path.join(models_dir, 'budget_allocator.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
    
    print(f"\n💾 Models saved to: {model_path}")
    return models

# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    try:
        # Train package scorer
        scorer_model = train_package_scorer()
        
        # Train budget allocator
        allocator_model = train_budget_allocator()
        
        print("\n" + "="*70)
        print("🎉 ALL MODELS TRAINED SUCCESSFULLY!")
        print("="*70)
        print("\n✅ Package Scorer: READY (XGBoost)")
        print("✅ Budget Allocator: READY (XGBoost)")
        print("\nRestart your FastAPI server to use the trained models.")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
