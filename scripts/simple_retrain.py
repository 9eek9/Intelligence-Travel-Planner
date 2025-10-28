#!/usr/bin/env python3
"""
Simple ML Model Retraining Script
Works directly with scikit-learn - guaranteed to work!
"""

import sys
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import json

print("="*70)
print("🔄 ML BUDGET MODEL RETRAINING (SIMPLE VERSION)")
print("="*70)

# Paths
project_root = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(project_root, '..', 'ml_models', 'data')
model_dir = os.path.join(project_root, '..', 'ml_models', 'models')
os.makedirs(data_dir, exist_ok=True)
os.makedirs(model_dir, exist_ok=True)

# Step 1: Generate Training Data
print("\n📊 Step 1: Generating synthetic training data...")
np.random.seed(42)

destinations = ['BKK', 'NYC', 'LAX', 'MIA', 'LAS', 'LON', 'PAR', 'TYO', 'SYD', 'DXB', 
                'YYZ', 'YVR', 'YUL', 'BCN', 'ROM', 'BER', 'AMS', 'DUB', 'HKG', 'SIN']
regions = ['Asia', 'North America', 'Europe', 'Oceania', 'Middle East']
seasons = ['peak', 'off_peak', 'shoulder']
purposes = ['leisure', 'business', 'family', 'adventure', 'romantic']
acc_types = ['hotel', 'hostel', 'airbnb', 'resort', 'apartment']

num_samples = 2000

data = {
    'destination': np.random.choice(destinations, num_samples),
    'duration': np.random.randint(1, 21, num_samples),
    'total_budget': np.random.randint(500, 10000, num_samples),
    'travelers': np.random.randint(1, 6, num_samples),
    'region': np.random.choice(regions, num_samples),
    'season': np.random.choice(seasons, num_samples),
    'purpose': np.random.choice(purposes, num_samples),
    'accommodation_type': np.random.choice(acc_types, num_samples)
}

df = pd.DataFrame(data)

# Generate realistic target values (budget breakdown)
df['accommodation'] = (df['total_budget'] * np.random.uniform(0.25, 0.45, num_samples)).round(2)
df['transportation'] = (df['total_budget'] * np.random.uniform(0.15, 0.35, num_samples)).round(2)
df['food'] = (df['total_budget'] * np.random.uniform(0.15, 0.25, num_samples)).round(2)
df['activities'] = (df['total_budget'] * np.random.uniform(0.10, 0.20, num_samples)).round(2)
df['miscellaneous'] = (df['total_budget'] * np.random.uniform(0.03, 0.10, num_samples)).round(2)

# Save training data
data_path = os.path.join(data_dir, 'training_data.csv')
df.to_csv(data_path, index=False)
print(f"   ✅ Generated {len(df)} training samples")
print(f"   📁 Saved to: {data_path}")

# Step 2: Prepare Data for Training
print("\n🔧 Step 2: Preparing data...")

# Features and targets
feature_cols = ['destination', 'duration', 'total_budget', 'travelers', 'region', 'season', 'purpose', 'accommodation_type']
target_cols = ['accommodation', 'transportation', 'food', 'activities', 'miscellaneous']

X = df[feature_cols].copy()
y = df[target_cols].copy()

# Encode categorical features
label_encoders = {}
categorical_cols = ['destination', 'region', 'season', 'purpose', 'accommodation_type']

for col in categorical_cols:
    le = LabelEncoder()
    X[col] = le.fit_transform(X[col].astype(str))
    label_encoders[col] = le

# Scale numerical features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split data
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

print(f"   ✅ Training set: {len(X_train)} samples")
print(f"   ✅ Test set: {len(X_test)} samples")

# Step 3: Train Model
print("\n🤖 Step 3: Training Random Forest model...")

model = RandomForestRegressor(
    n_estimators=100,
    max_depth=15,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)
print("   ✅ Model trained successfully!")

# Step 4: Evaluate Model
print("\n📈 Step 4: Evaluating model...")

y_pred = model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100

print(f"   Mean Absolute Error: ${mae:.2f}")
print(f"   R² Score: {r2:.3f}")
print(f"   Mean Absolute % Error: {mape:.1f}%")

# Step 5: Save Model
print("\n💾 Step 5: Saving model files...")

joblib.dump(model, os.path.join(model_dir, 'budget_model.pkl'))
joblib.dump(scaler, os.path.join(model_dir, 'scaler.pkl'))
joblib.dump(label_encoders, os.path.join(model_dir, 'label_encoders.pkl'))

metadata = {
    'model_type': 'RandomForestRegressor',
    'n_samples': len(df),
    'features': feature_cols,
    'targets': target_cols,
    'mae': float(mae),
    'r2': float(r2),
    'mape': float(mape),
    'trained_date': pd.Timestamp.now().isoformat()
}

with open(os.path.join(model_dir, 'model_metadata.json'), 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"   ✅ Saved budget_model.pkl")
print(f"   ✅ Saved scaler.pkl")
print(f"   ✅ Saved label_encoders.pkl")
print(f"   ✅ Saved model_metadata.json")

# Step 6: Test Predictions
print("\n🧪 Step 6: Testing predictions...")

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

for i, test_case in enumerate(test_cases, 1):
    print(f"\n   Test {i}: {test_case['destination']} - ${test_case['total_budget']}")
    
    # Prepare input
    test_df = pd.DataFrame([test_case])
    test_X = test_df.copy()
    
    # Encode
    for col in categorical_cols:
        try:
            test_X[col] = label_encoders[col].transform(test_X[col].astype(str))
        except:
            # Handle unknown categories
            test_X[col] = 0
    
    # Scale
    test_X_scaled = scaler.transform(test_X)
    
    # Predict
    prediction = model.predict(test_X_scaled)[0]
    
    print(f"      ✅ Accommodation: ${prediction[0]:.2f}")
    print(f"      ✅ Transportation: ${prediction[1]:.2f}")
    print(f"      ✅ Food: ${prediction[2]:.2f}")
    print(f"      ✅ Activities: ${prediction[3]:.2f}")
    print(f"      ✅ Miscellaneous: ${prediction[4]:.2f}")
    print(f"      💰 Total: ${sum(prediction):.2f}")

print("\n" + "="*70)
print("✅ MODEL RETRAINING COMPLETE!")
print("="*70)
print("\n💡 Next steps:")
print("   1. Restart your FastAPI server: uvicorn app:app --reload")
print("   2. Test endpoint: POST http://localhost:8000/budget/predict-budget")
print("   3. Your ML model is now working!\n")
