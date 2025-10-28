#!/usr/bin/env python3
"""
Retrain the ML Budget Prediction Model
Uses the existing working train_model.py approach
"""

import sys
import os
import pandas as pd
import numpy as np

# Add paths
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, '..'))

print("="*70)
print("🔄 RETRAINING ML BUDGET MODEL")
print("="*70)

# Step 1: Generate training data
print("\n📊 Step 1: Generating training data...")
np.random.seed(42)

destinations = ['BKK', 'NYC', 'LAX', 'MIA', 'LAS', 'LON', 'PAR', 'TYO', 'SYD', 'DXB']
regions = ['Asia', 'North America', 'Europe', 'Oceania', 'Middle East']
seasons = ['peak', 'off_peak', 'shoulder']
purposes = ['leisure', 'business', 'family', 'adventure', 'romantic']
acc_types = ['hotel', 'hostel', 'airbnb', 'resort', 'apartment']

data = {
    'destination': np.random.choice(destinations, 2000),
    'duration': np.random.randint(1, 15, 2000),
    'total_budget': np.random.randint(500, 10000, 2000),
    'travelers': np.random.randint(1, 6, 2000),
    'region': np.random.choice(regions, 2000),
    'season': np.random.choice(seasons, 2000),
    'purpose': np.random.choice(purposes, 2000),
    'accommodation_type': np.random.choice(acc_types, 2000)
}

df = pd.DataFrame(data)

# Generate target columns (budget breakdown)
# Use realistic percentages based on travel patterns
for i in range(len(df)):
    budget = df.loc[i, 'total_budget']
    
    # Base percentages
    acc_pct = np.random.uniform(0.25, 0.45)
    trans_pct = np.random.uniform(0.15, 0.35)
    food_pct = np.random.uniform(0.15, 0.25)
    act_pct = np.random.uniform(0.10, 0.20)
    misc_pct = np.random.uniform(0.03, 0.10)
    
    # Normalize to sum to budget
    total_pct = acc_pct + trans_pct + food_pct + act_pct + misc_pct
    acc_pct /= total_pct
    trans_pct /= total_pct
    food_pct /= total_pct
    act_pct /= total_pct
    misc_pct /= total_pct
    
    df.loc[i, 'accommodation'] = round(budget * acc_pct, 2)
    df.loc[i, 'transportation'] = round(budget * trans_pct, 2)
    df.loc[i, 'food'] = round(budget * food_pct, 2)
    df.loc[i, 'activities'] = round(budget * act_pct, 2)
    df.loc[i, 'miscellaneous'] = round(budget * misc_pct, 2)

data_path = os.path.join(project_root, '..', 'ml_models', 'data', 'training_data.csv')
os.makedirs(os.path.dirname(data_path), exist_ok=True)
df.to_csv(data_path, index=False)
print(f"   ✅ Generated {len(df)} samples")
print(f"   📁 Saved to: {data_path}")
print(f"   📋 Columns: {list(df.columns)}")

# Step 2: Train model directly
print("\n🤖 Step 2: Training model...")

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

# Load data
df = pd.read_csv(data_path)

# Define features
categorical_features = ['destination', 'region', 'season', 'purpose', 'accommodation_type']
numerical_features = ['duration', 'total_budget', 'travelers']
target_features = ['accommodation', 'transportation', 'food', 'activities', 'miscellaneous']

# Encode categorical features
label_encoders = {}
for col in categorical_features:
    le = LabelEncoder()
    df[col + '_encoded'] = le.fit_transform(df[col])
    label_encoders[col] = le

# Prepare X and y
feature_cols = [col + '_encoded' for col in categorical_features] + numerical_features
X = df[feature_cols]
y = df[target_features]

print(f"   📊 Training shape: X={X.shape}, y={y.shape}")

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train model
print("   🔄 Training Random Forest...")
model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
model.fit(X_train_scaled, y_train)

# Evaluate
y_pred = model.predict(X_test_scaled)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"\n📈 Training Results:")
print(f"   Mean Absolute Error: ${mae:.2f}")
print(f"   R² Score: {r2:.3f}")

# Save model
model_path = os.path.join(project_root, '..', 'ml_models', 'models')
os.makedirs(model_path, exist_ok=True)

joblib.dump(model, os.path.join(model_path, 'budget_model.pkl'))
joblib.dump(scaler, os.path.join(model_path, 'scaler.pkl'))
joblib.dump(label_encoders, os.path.join(model_path, 'label_encoders.pkl'))

print(f"\n💾 Model saved to: {model_path}")

# Step 3: Test model
print("\n🧪 Step 3: Testing model...")
try:
    from ml_models.budget_predictor import BudgetPredictor
    
    # Force reload to get new model
    import importlib
    import ml_models.budget_predictor as bp
    importlib.reload(bp)
    
    predictor = bp.BudgetPredictor()
    
    test_cases = [
        {
            'destination': 'BKK',
            'duration': 5,
            'total_budget': 3000,
            'travelers': 2,
            'region': 'Asia',
            'season': 'off_peak',
            'purpose': 'leisure',
            'accommodation_type': 'hotel'
        },
        {
            'destination': 'NYC',
            'duration': 3,
            'total_budget': 2000,
            'travelers': 1,
            'region': 'North America',
            'season': 'peak',
            'purpose': 'business',
            'accommodation_type': 'hotel'
        }
    ]
    
    print("\n🎯 Test Predictions:")
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   Test {i}: {test_case['destination']} - ${test_case['total_budget']}")
        test_df = pd.DataFrame([test_case])
        
        try:
            result = predictor.predict(test_df)
            print(f"      ✅ Success!")
            print(f"      Accommodation: ${result['breakdown']['accommodation']:.2f}")
            print(f"      Transportation: ${result['breakdown']['transportation']:.2f}")
            print(f"      Food: ${result['breakdown']['food']:.2f}")
            print(f"      Activities: ${result['breakdown']['activities']:.2f}")
            print(f"      Miscellaneous: ${result['breakdown']['miscellaneous']:.2f}")
            print(f"      Confidence: {result['confidence']:.1%}")
        except Exception as e:
            print(f"      ❌ Failed: {e}")
            import traceback
            traceback.print_exc()

except Exception as e:
    print(f"   ⚠️  Could not test model: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("✅ MODEL RETRAINING COMPLETE!")
print("="*70)
print("\n💡 Next steps:")
print("   1. Restart your FastAPI server: uvicorn app:app --reload")
print("   2. Test the /budget/predict-budget endpoint")
print("   3. ML predictions should now work!\n")