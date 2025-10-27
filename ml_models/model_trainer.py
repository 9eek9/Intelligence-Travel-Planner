"""
Model Trainer
Trains a Random Forest model to predict budget allocations
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import json
from datetime import datetime
import os

class BudgetModelTrainer:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = []
        
        # Use absolute path - FIXED
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_path = os.path.join(project_root, 'ml_models', 'models') + '/'
        
    def prepare_features(self, df):
        """
        Prepare features for training
        Convert categorical variables to numbers
        """
        print("📊 Preparing features...")
        
        # Categorical columns to encode
        categorical_cols = ['destination', 'region', 'season', 'purpose', 'accommodation_type']
        
        # Create label encoders for categorical variables
        for col in categorical_cols:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                df[f'{col}_encoded'] = self.label_encoders[col].fit_transform(df[col])
            else:
                df[f'{col}_encoded'] = self.label_encoders[col].transform(df[col])
        
        # Select features for training
        feature_cols = [
            'duration', 'total_budget', 'travelers', 'budget_per_day',
            'budget_per_person', 'cost_index',
            'destination_encoded', 'region_encoded', 'season_encoded',
            'purpose_encoded', 'accommodation_type_encoded'
        ]
        
        self.feature_names = feature_cols
        X = df[feature_cols].values
        
        # Target variables (percentages we want to predict)
        y = df[[
            'accommodation_pct', 'transportation_pct', 'food_pct',
            'activities_pct', 'miscellaneous_pct'
        ]].values
        
        print(f"✅ Features prepared: {len(feature_cols)} input features")
        return X, y
    
    def train(self, data_path='ml_models/data/training_data.csv'):
        """
        Train the budget allocation model
        
        Args:
            data_path: Path to training data CSV
            
        Returns:
            Dictionary with training metrics
        """
        print("\n" + "="*50)
        print("🚀 STARTING MODEL TRAINING")
        print("="*50 + "\n")
        
        # Load training data
        print(f"📂 Loading training data from {data_path}...")
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Training data not found at {data_path}")
        
        df = pd.read_csv(data_path)
        print(f"✅ Loaded {len(df)} samples")
        
        # Prepare features
        X, y = self.prepare_features(df)
        
        # Split data into training and testing
        print("\n🔀 Splitting data (80% train, 20% test)...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        print(f"   Training samples: {len(X_train)}")
        print(f"   Testing samples: {len(X_test)}")
        
        # Scale features (normalize values)
        print("\n⚖️  Scaling features...")
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train the model
        print("\n🧠 Training Random Forest model...")
        print("   This may take 1-2 minutes...")
        
        self.model = RandomForestRegressor(
            n_estimators=200,        # Number of trees
            max_depth=15,           # Max tree depth
            min_samples_split=5,    # Min samples to split
            min_samples_leaf=2,     # Min samples in leaf
            random_state=42,
            n_jobs=-1,              # Use all CPU cores
            verbose=0
        )
        
        self.model.fit(X_train_scaled, y_train)
        print("✅ Model training complete!")
        
        # Evaluate the model
        print("\n📈 Evaluating model performance...")
        y_pred = self.model.predict(X_test_scaled)
        metrics = self._calculate_metrics(y_test, y_pred)
        
        # Save model and metadata
        print("\n💾 Saving model...")
        self._save_model(metrics)
        
        # Print results
        print("\n" + "="*50)
        print("✅ TRAINING COMPLETE")
        print("="*50)
        self._print_metrics(metrics)
        
        return metrics
    
    def _calculate_metrics(self, y_true, y_pred):
        """Calculate evaluation metrics for each category"""
        categories = ['accommodation', 'transportation', 'food', 'activities', 'miscellaneous']
        metrics = {}
        
        for i, category in enumerate(categories):
            mae = mean_absolute_error(y_true[:, i], y_pred[:, i])
            mse = mean_squared_error(y_true[:, i], y_pred[:, i])
            rmse = np.sqrt(mse)
            r2 = r2_score(y_true[:, i], y_pred[:, i])
            
            metrics[category] = {
                'mae': float(mae),
                'rmse': float(rmse),
                'r2': float(r2),
                'mae_percentage': float(mae * 100)  # Convert to percentage points
            }
        
        # Overall metrics
        metrics['overall'] = {
            'mae': float(mean_absolute_error(y_true, y_pred)),
            'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred))),
            'r2': float(r2_score(y_true, y_pred))
        }
        
        return metrics
    
    def _save_model(self, metrics):
        """Save model, scaler, and metadata to disk"""
        os.makedirs(self.model_path, exist_ok=True)
        
        # Save model components
        joblib.dump(self.model, f'{self.model_path}budget_model.pkl')
        joblib.dump(self.scaler, f'{self.model_path}scaler.pkl')
        joblib.dump(self.label_encoders, f'{self.model_path}label_encoders.pkl')
        
        # Save metadata
        metadata = {
            'trained_at': datetime.now().isoformat(),
            'feature_names': self.feature_names,
            'metrics': metrics,
            'model_type': 'RandomForestRegressor',
            'model_version': '1.0',
            'n_estimators': 200,
            'max_depth': 15
        }
        
        with open(f'{self.model_path}model_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=4)
        
        print(f"✅ Model saved to {self.model_path}")
    
    def _print_metrics(self, metrics):
        """Print evaluation metrics in readable format"""
        print("\n📊 MODEL PERFORMANCE METRICS")
        print("-" * 50)
        
        print("\n🎯 Per-Category Accuracy:")
        for category, values in metrics.items():
            if category != 'overall':
                print(f"\n   {category.upper()}:")
                print(f"      Error: ±{values['mae_percentage']:.2f} percentage points")
                print(f"      R² Score: {values['r2']:.4f} (closer to 1.0 is better)")
        
        print(f"\n🌟 OVERALL PERFORMANCE:")
        print(f"   Average Error: {metrics['overall']['mae']:.4f}")
        print(f"   R² Score: {metrics['overall']['r2']:.4f}")
        
        if metrics['overall']['r2'] > 0.8:
            print("\n✅ Excellent model performance!")
        elif metrics['overall']['r2'] > 0.6:
            print("\n👍 Good model performance")
        else:
            print("\n⚠️  Model may need improvement")


# Standalone usage
if __name__ == "__main__":
    trainer = BudgetModelTrainer()
    trainer.train()