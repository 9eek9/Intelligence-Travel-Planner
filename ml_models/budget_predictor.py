"""
Budget Predictor
Uses trained ML model to predict budget allocations for new trips
"""

import joblib
import numpy as np
import os

class BudgetPredictor:
    def __init__(self):
        """Load trained model and preprocessors"""
        # Try multiple possible paths
        possible_paths = [
            'ml_models/models/',
            os.path.join(os.path.dirname(__file__), 'models/'),
            os.path.join(os.path.dirname(__file__), '..', 'ml_models', 'models/')
        ]
        
        model_path = None
        for path in possible_paths:
            if os.path.exists(os.path.join(path, 'budget_model.pkl')):
                model_path = path
                break
        
        if model_path is None:
            raise FileNotFoundError(
                "Model not found. Please train the model first by running: "
                "python scripts/retrain_model.py"
            )
        
        # Load saved models
        self.model = joblib.load(os.path.join(model_path, 'budget_model.pkl'))
        self.scaler = joblib.load(os.path.join(model_path, 'scaler.pkl'))
        self.label_encoders = joblib.load(os.path.join(model_path, 'label_encoders.pkl'))
        
        print("✅ ML model loaded successfully")
        
        # Print what destinations the model knows (for debugging)
        if 'destination' in self.label_encoders:
            known_destinations = self.label_encoders['destination'].classes_
            print(f"   📍 Known destinations: {', '.join(known_destinations)}")
    
    def predict(self, X):
        """Make predictions on input data"""
        categorical_features = ['destination', 'region', 'season', 'purpose', 'accommodation_type']
        numerical_features = ['duration', 'total_budget', 'travelers']
        
        # Encode categorical features
        encoded_features = []
        
        for col in categorical_features:
            if col in self.label_encoders and col in X.columns:
                try:
                    # Get the value and encode it
                    value = X[col].iloc[0]
                    encoded = self.label_encoders[col].transform([value])
                    encoded_features.append(int(encoded[0]))
                except ValueError:
                    print(f"   ⚠️  Warning: Unknown {col} '{X[col].iloc[0]}', using default")
                    encoded_features.append(0)
        
        # Add numerical features
        for col in numerical_features:
            if col in X.columns:
                encoded_features.append(float(X[col].iloc[0]))
        
        # Convert to 2D array for prediction (shape: 1 x n_features)
        X_encoded = np.array(encoded_features).reshape(1, -1)
        
        # Scale features
        X_scaled = self.scaler.transform(X_encoded)
        
        # Make predictions
        predictions = self.model.predict(X_scaled)
        
        # Extract breakdown
        breakdown = {
            'accommodation': float(predictions[0][0]),
            'transportation': float(predictions[0][1]),
            'food': float(predictions[0][2]),
            'activities': float(predictions[0][3]),
            'miscellaneous': float(predictions[0][4])
        }
        
        total_budget = float(X['total_budget'].iloc[0])
        predicted_total = sum(breakdown.values())
        
        # Calculate confidence based on how close prediction is to actual budget
        confidence = 1.0 - min(abs(predicted_total - total_budget) / total_budget, 0.5)
        confidence = max(0.5, min(0.95, confidence))
        
        return {
            'breakdown': breakdown,
            'total_budget': total_budget,
            'confidence': confidence
        }
    
    def predict_with_amounts(self, features):
        """
        Predict both percentages and dollar amounts
        
        Args:
            features (dict): Same as predict()
            
        Returns:
            dict: Contains both percentages and amounts
        """
        percentages = self.predict(features)
        total_budget = features['total_budget']
        
        amounts = {
            category: round(total_budget * pct, 2)
            for category, pct in percentages.items()
        }
        
        return {
            'percentages': percentages,
            'amounts': amounts,
            'total_budget': total_budget
        }


# Test the predictor
if __name__ == "__main__":
    try:
        predictor = BudgetPredictor()
        
        # Test with sample input
        test_features = {
            'destination': 'Paris',
            'region': 'Europe',
            'duration': 7,
            'total_budget': 3000,
            'travelers': 2,
            'season': 'peak',
            'purpose': 'romantic',
            'accommodation_type': 'hotel'
        }
        
        result = predictor.predict_with_amounts(test_features)
        
        print("\n🧪 TEST PREDICTION")
        print(f"Destination: {test_features['destination']}")
        print(f"Budget: ${test_features['total_budget']}")
        print(f"Duration: {test_features['duration']} days")
        print("\nPredicted Allocation:")
        for category, amount in result['amounts'].items():
            pct = result['percentages'][category]
            print(f"  {category.capitalize()}: ${amount:.2f} ({pct*100:.1f}%)")
            
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")