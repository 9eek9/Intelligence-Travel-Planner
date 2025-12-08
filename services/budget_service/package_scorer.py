"""
ML-based Package Quality Scorer using XGBoost
Scores travel packages based on value, convenience, and experience
"""

from typing import Dict, Any
import numpy as np
import xgboost as xgb
import os

class PackageScorer:
    """Score packages using XGBoost ML model"""
    
    def __init__(self):
        """Load pre-trained model"""
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the pre-trained XGBoost model"""
        # Try .json first (XGBoost native format)
        model_path = os.path.join(os.path.dirname(__file__), "models", "package_quality_model.json")
        
        if os.path.exists(model_path):
            try:
                self.model = xgb.Booster()
                self.model.load_model(model_path)
                print(f"Loaded XGBoost model from {model_path}")
                return
            except Exception as e:
                print(f"Failed to load .json model: {e}")
        
        # Try .pkl as fallback
        pkl_path = os.path.join(os.path.dirname(__file__), "models", "package_scorer.pkl")
        if os.path.exists(pkl_path):
            try:
                import pickle
                with open(pkl_path, 'rb') as f:
                    self.model = pickle.load(f)
                print(f"Loaded pickled model from {pkl_path}")
                return
            except Exception as e:
                print(f"Failed to load .pkl model: {e}")
        
        print(f"No model file found. Checked:")
        print(f"   - {model_path}")
        print(f"   - {pkl_path}")
        print(f"   Please run 'python train_model.py' to create the model.")
        self.model = None
    
    def score_package(
        self, 
        package: Dict[str, Any],
        user_preferences: Dict[str, Any],
        destination: str
    ) -> Dict[str, Any]:
        """Score a package using ML model only"""
        
        if self.model is None:
            raise Exception("ML model not available. Please train and save the model first.")
        
        return self._ml_score(package, user_preferences, destination)
    
    def _ml_score(self, package: Dict, preferences: Dict, destination: str) -> Dict:
        """Score using XGBoost ML model"""
        
        # Calculate component scores FIRST (these are rule-based and transparent)
        value_score = self._calculate_value_score(package, preferences)
        convenience_score = self._calculate_convenience_score(package)
        experience_score = self._calculate_experience_score(package)
        
        # Calculate overall score as weighted average of components
        # This makes scoring more transparent and predictable
        overall_score = value_score + convenience_score + experience_score
        
        # Optional: Use ML model as adjustment factor
        # Extract features
        features = self._extract_features(package, preferences, destination)
        features_array = np.array([features], dtype=np.float32)
        
        try:
            ml_prediction = float(self.model.predict(features_array)[0])
            # Use ML as a small adjustment (+/- 5 points) to the rule-based score
            ml_adjustment = (ml_prediction - overall_score) * 0.2  # 20% weight to ML
            overall_score = max(0, min(100, overall_score + ml_adjustment))
        except Exception as e:
            print(f"ML prediction failed, using rule-based score only: {e}")
        
        # Generate insights
        insights = self._generate_ml_insights(
            overall_score, value_score, convenience_score, experience_score, package
        )
        
        return {
            "overall_score": round(overall_score, 1),
            "value_score": round(value_score, 1),
            "convenience_score": round(convenience_score, 1),
            "experience_score": round(experience_score, 1),
            "insights": insights,
            "model_used": "Rule-based + XGBoost adjustment",
            "score_explanation": {
                "budget_efficiency": f"How well the package uses your ${preferences.get('budget', 0)} budget (optimal: 85-95%)",
                "travel_comfort": "Quality of flights (direct vs layovers) and hotel amenities",
                "activity_richness": f"Number and variety of activities included ({len(package.get('activities', {}).get('details', []))} activities)"
            }
        }
    
    def _extract_features(self, package: Dict, preferences: Dict, destination: str) -> list:
        """Extract 15 numerical features matching the training data"""
        
        # Get values safely
        total = package.get("total", 0)
        budget = preferences.get("budget", 0)
        flight_price = package.get("flight", {}).get("price", 0) if package.get("flight") else 0
        hotel_price = package.get("hotel", {}).get("price", 0) if package.get("hotel") else 0
        
        # Handle meals and transit structures
        meals_cost = 0
        if isinstance(package.get("meals"), dict):
            meals_cost = package["meals"].get("total", 0)
        else:
            meals_cost = package.get("meals", 0)
        
        transit_cost = 0
        if isinstance(package.get("transit"), dict):
            transit_cost = package["transit"].get("total", 0)
        else:
            transit_cost = package.get("transit", 0)
        
        activities_cost = package.get("activities", {}).get("total", 0)
        num_activities = len(package.get("activities", {}).get("details", []))
        
        # Calculate ratios and utilization
        if total > 0:
            flight_ratio = flight_price / total
            hotel_ratio = hotel_price / total
            activities_ratio = activities_cost / total
            meals_ratio = meals_cost / total
            transit_ratio = transit_cost / total
        else:
            flight_ratio = hotel_ratio = activities_ratio = meals_ratio = transit_ratio = 0
        
        if budget > 0:
            budget_util = total / budget
            budget_remaining = (budget - total) / budget
        else:
            budget_util = 0
            budget_remaining = 0
        
        # Travel style (one-hot encoded)
        travel_style = preferences.get("travel_style", "moderate").lower()
        style_budget = 1 if travel_style == "budget" else 0
        style_moderate = 1 if travel_style == "moderate" else 0
        style_luxury = 1 if travel_style == "luxury" else 0
        
        # Destination hash (simple encoding)
        destination_hash = hash(destination) % 100 / 100.0
        
        # Completeness: has flight + hotel + activities
        has_flight = 1 if package.get("flight") else 0
        has_hotel = 1 if package.get("hotel") else 0
        has_activities = 1 if num_activities > 0 else 0
        completeness = (has_flight + has_hotel + has_activities) / 3.0
        
        # Feature vector matching training (15 features)
        features = [
            budget_util,         # 0: Budget utilization (0-1)
            budget_remaining,    # 1: Budget remaining ratio
            has_flight,          # 2: Has flight (0 or 1)
            flight_ratio,        # 3: Flight cost ratio
            has_hotel,           # 4: Has hotel (0 or 1)
            hotel_ratio,         # 5: Hotel cost ratio
            num_activities,      # 6: Number of activities
            activities_ratio,    # 7: Activities cost ratio
            meals_ratio,         # 8: Meals cost ratio
            transit_ratio,       # 9: Transit cost ratio
            style_budget,        # 10: Budget style (0 or 1)
            style_moderate,      # 11: Moderate style (0 or 1)
            style_luxury,        # 12: Luxury style (0 or 1)
            destination_hash,    # 13: Destination encoding (0-1)
            completeness         # 14: Package completeness (0-1)
        ]
        
        return features
    
    def _calculate_value_score(self, package, preferences):
        """Calculate value score based on budget utilization"""
        budget = preferences.get("budget", 0)
        budget_remaining = package.get("budgetRemaining", 0)
        
        if budget <= 0:
            return 20  # Invalid budget
        
        budget_used_ratio = (budget - budget_remaining) / budget
        
        # Scoring logic (ordered from best to worst):
        if 0.85 <= budget_used_ratio <= 0.95:
            return 40  # Perfect usage (85-95% - sweet spot)
        elif 0.95 < budget_used_ratio <= 1.0:
            return 37  # ← Changed from 32 to 37 (still good, small penalty)
        elif 0.75 <= budget_used_ratio < 0.85:
            return 35  # Good usage (75-85%)
        elif 0.65 <= budget_used_ratio < 0.75:
            return 28  # Decent usage (65-75%)
        elif budget_used_ratio > 1.0:
            return 15  # Over budget (penalize heavily)
        elif 0.50 <= budget_used_ratio < 0.65:
            return 25  # Moderate usage (50-65%)
        else:
            return 20  # Low usage (under 50% - not optimizing budget)
    
    def _calculate_convenience_score(self, package):
        """Calculate convenience score based on flight and hotel"""
        score = 0
        
        # Flight convenience (15 points)
        if package.get("flight"):
            itineraries = package["flight"].get("itineraries", [])
            total_stops = sum(
                sum(seg.get("stops", 0) for seg in itin.get("segments", []))
                for itin in itineraries
            )
            if total_stops == 0:
                score += 15
            elif total_stops <= 2:
                score += 10
            else:
                score += 5
        
        # Hotel quality (15 points)
        if package.get("hotel"):
            hotel = package["hotel"]
            room_desc = hotel.get("room_description", "").lower()
            
            # Check amenities
            amenities = ["wifi", "breakfast", "pool", "gym", "spa", "suite", "deluxe"]
            amenity_count = sum(1 for amenity in amenities if amenity in room_desc)
            score += min(amenity_count * 2, 15)
        
        return min(score, 30)
    
    def _calculate_experience_score(self, package):
        """Calculate experience score based on activities"""
        activities_count = len(package.get("activities", {}).get("details", []))
        
        if activities_count >= 5:
            return 30
        elif activities_count >= 3:
            return 25
        elif activities_count >= 2:
            return 18
        elif activities_count >= 1:
            return 12
        else:
            return 5
    
    def _generate_ml_insights(self, overall_score, value_score, convenience_score, experience_score, package):
        """Generate insights based on ML predictions"""
        
        insights = []
        
        # Overall assessment
        if overall_score >= 80:
            insights.append("Exceptional package quality")
        elif overall_score >= 70:
            insights.append("Excellent value package")
        elif overall_score >= 60:
            insights.append("Good package option")
        else:
            insights.append("Basic package")
        
        # Value insights
        if value_score >= 35:
            insights.append("Optimal budget usage")
        elif value_score >= 25:
            insights.append("Budget-friendly")
        
        # Convenience insights
        hotel = package.get("hotel", {})
        if hotel:
            room_desc = hotel.get("room_description", "").lower()
            if "deluxe" in room_desc or "suite" in room_desc:
                insights.append("Premium accommodation")
            if "wifi" in room_desc:
                insights.append("WiFi included")
        
        flight = package.get("flight", {})
        if flight:
            itineraries = flight.get("itineraries", [])
            total_stops = sum(
                sum(seg.get("stops", 0) for seg in itin.get("segments", []))
                for itin in itineraries
            )
            if total_stops == 0:
                insights.append("Direct flights")
            elif total_stops <= 2:
                insights.append("Few layovers")
        
        # Experience insights
        activities_count = len(package.get("activities", {}).get("details", []))
        if activities_count >= 5:
            insights.append(f"Rich activities ({activities_count} included)")
        elif activities_count >= 3:
            insights.append(f"Good activities ({activities_count} included)")
        
        return " • ".join(insights)


# Global scorer instance
_scorer = None

def score_package(package, user_preferences, destination):
    """
    Score a travel package using ML model
    
    Args:
        package: Package dictionary with flight, hotel, activities, etc.
        user_preferences: User preferences including budget, travel_style
        destination: Destination city name
    
    Returns:
        Dictionary with scores and insights
    """
    global _scorer
    
    if _scorer is None:
        _scorer = PackageScorer()
    
    try:
        return _scorer.score_package(package, user_preferences, destination)
    except Exception as e:
        print(f"ML scoring failed: {e}")
        # If ML fails, raise the error instead of falling back
        raise Exception(f"ML model required but failed: {str(e)}")
