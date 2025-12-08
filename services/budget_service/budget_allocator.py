"""
ML-based Budget Allocation Service
Uses XGBoost trained on your synthetic data to suggest optimal budget splits
"""

import os
import pickle
from typing import Dict, Any

class BudgetAllocator:
    """Suggest optimal budget allocation using ML"""
    
    def __init__(self):
        """Load trained model"""
        self.model_data = self._load_model()
        self.use_ml = self.model_data is not None
        
    def _load_model(self):
        """Load trained XGBoost model"""
        model_path = os.path.join(os.path.dirname(__file__), 'models', 'budget_allocator.pkl')
        try:
            with open(model_path, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            print("Budget allocation model not found, using rules")
            return None
    
    def suggest_allocation(
        self,
        total_budget: float,
        destination: str,
        duration: int,
        travelers: int = 1,
        travel_style: str = "moderate"
    ) -> Dict[str, Any]:
        """
        Suggest optimal budget allocation
        
        Returns dict with percentage allocations for each category
        """
        
        if self.use_ml:
            return self._ml_suggestion(
                total_budget, destination, duration, travelers, travel_style
            )
        else:
            return self._rule_based_suggestion(travel_style)
    
    def _ml_suggestion(self, total_budget, destination, duration, travelers, travel_style):
        """Use trained XGBoost models"""
        
        models = self.model_data['models']
        encoders = self.model_data.get('encoders', {})
        
        try:
            # Encode style
            style_budget = 1 if travel_style == 'budget' else 0
            style_moderate = 1 if travel_style == 'moderate' else 0
            style_luxury = 1 if travel_style == 'luxury' else 0
            
            features = {
                'duration': duration,
                'total_budget': total_budget,
                'travelers': travelers,
                'budget_per_day': total_budget / duration,
                'destination_hash': hash(destination) % 100 / 100,  # Simple hash
                'style_budget': style_budget,
                'style_moderate': style_moderate,
                'style_luxury': style_luxury
            }
            
            # If encoders exist and destination is in classes, use encoding
            if encoders and 'destination' in encoders:
                if destination in encoders['destination'].classes_:
                    features['destination_encoded'] = encoders['destination'].transform([destination])[0]
                else:
                    features['destination_encoded'] = 0
            
            feature_array = [[
                features[col] for col in self.model_data['feature_cols']
            ]]
            
            # Predict percentages
            predictions = {}
            for target, model in models.items():
                pred = model.predict(feature_array)[0]
                predictions[target] = float(pred)
            
            # Normalize to ensure sum = 100%
            total = sum(predictions.values())
            predictions = {k: v/total for k, v in predictions.items()}
            
            # Calculate percentages (convert from ratio to percentage and round)
            flights_pct = round(predictions['transportation_pct'] * 100, 2)
            hotels_pct = round(predictions['accommodation_pct'] * 100, 2)
            activities_pct = round(predictions['activities_pct'] * 100, 2)
            meals_pct = round(predictions['food_pct'] * 100, 2)
            transit_pct = round(predictions['miscellaneous_pct'] * 100, 2)
            
            # Generate detailed reasoning
            reasoning_parts = [
                f"ML-optimized allocation for {destination} ({duration} days, {travelers} traveler{'s' if travelers > 1 else ''})",
            ]
            
            # Add style-specific reasoning
            if travel_style == "budget":
                reasoning_parts.append("Budget style: prioritizing affordable options")
            elif travel_style == "luxury":
                reasoning_parts.append("Luxury style: emphasizing premium experiences")
            else:
                reasoning_parts.append("Moderate style: balanced allocation")
            
            # Add destination-specific insights
            if hotels_pct > 42:
                reasoning_parts.append(f"Higher hotel allocation ({hotels_pct}%) for comfortable stays")
            
            if activities_pct > 12:
                reasoning_parts.append(f"Enhanced activities budget ({activities_pct}%) for richer experiences")
            
            reasoning = ". ".join(reasoning_parts) + "."
            
            return {
                "flights_percent": flights_pct,
                "hotels_percent": hotels_pct,
                "activities_percent": activities_pct,
                "meals_percent": meals_pct,
                "transit_percent": transit_pct,
                "reasoning": reasoning,
                "model_used": "XGBoost",
                "confidence": "high"
            }
            
        except Exception as e:
            print(f"ML prediction failed: {e}, using fallback")
            return self._rule_based_suggestion(travel_style)
    
    def _rule_based_suggestion(self, travel_style):
        """Fallback rule-based allocation"""
        
        allocations = {
            "budget": {"flights": 30, "hotels": 35, "activities": 10, "meals": 20, "transit": 5},
            "moderate": {"flights": 25, "hotels": 40, "activities": 12, "meals": 18, "transit": 5},
            "luxury": {"flights": 20, "hotels": 45, "activities": 15, "meals": 15, "transit": 5}
        }
        
        alloc = allocations.get(travel_style, allocations["moderate"])
        
        return {
            "flights_percent": alloc["flights"],
            "hotels_percent": alloc["hotels"],
            "activities_percent": alloc["activities"],
            "meals_percent": alloc["meals"],
            "transit_percent": alloc["transit"],
            "reasoning": f"Rule-based allocation for {travel_style} travel style",
            "model_used": "Rule-Based"
        }


def suggest_budget_allocation(total_budget, destination, days, travel_style):
    """Convenience function"""
    allocator = BudgetAllocator()
    return allocator.suggest_allocation(
        total_budget, destination, days, travelers=1, travel_style=travel_style
    )
