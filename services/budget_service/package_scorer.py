"""
ML-based Package Quality Scorer using XGBoost
Scores travel packages based on value, convenience, and experience
"""

from typing import Dict, Any
import numpy as np
import xgboost as xgb
import pickle
import os

class PackageScorer:
    """Score packages using XGBoost ML model"""
    
    def __init__(self):
        """Load pre-trained model or use rule-based fallback"""
        self.model = self._load_model()
        self.use_ml = self.model is not None
    
    def _load_model(self):
        """Load trained XGBoost model if available"""
        model_path = os.path.join(os.path.dirname(__file__), 'models', 'package_scorer.pkl')
        try:
            with open(model_path, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            print("No trained model found, using rule-based scoring")
            return None
    
    def score_package(
        self, 
        package: Dict[str, Any],
        user_preferences: Dict[str, Any],
        destination: str
    ) -> Dict[str, Any]:
        """Score a package using ML or rules"""
        
        if self.use_ml:
            return self._ml_score(package, user_preferences, destination)
        else:
            return self._rule_based_score(package, user_preferences, destination)
    
    def _ml_score(self, package: Dict, preferences: Dict, destination: str) -> Dict:
        """Score using trained XGBoost model"""
        
        # Extract features for ML model
        features = self._extract_features(package, preferences, destination)
        
        # Predict score (0-100)
        X = np.array([features])
        predicted_score = self.model.predict(X)[0]
        
        # Get feature importance for breakdown
        breakdown = self._calculate_breakdown_from_features(features)
        
        insights = self._generate_ml_insights(predicted_score, breakdown)
        
        return {
            "overall_score": round(float(predicted_score), 1),
            "value_score": round(breakdown["value"], 1),
            "convenience_score": round(breakdown["convenience"], 1),
            "experience_score": round(breakdown["experience"], 1),
            "insights": insights,
            "model_used": "XGBoost"
        }
    
    def _extract_features(self, package: Dict, preferences: Dict, destination: str) -> list:
        """Extract ML features from package"""
        
        budget = preferences.get("budget", 1000)
        travel_style = preferences.get("travel_style", "moderate")
        
        # Feature engineering (15 features)
        features = [
            # Budget features
            package["total"] / budget,  # Budget utilization ratio
            package.get("budgetRemaining", 0) / budget,  # Remaining ratio
            
            # Flight features
            1 if package.get("flight") else 0,  # Has flight
            package.get("flight", {}).get("price", 0) / package["total"],  # Flight cost ratio
            
            # Hotel features
            1 if package.get("hotel") else 0,  # Has hotel
            package.get("hotel", {}).get("total", 0) / package["total"],  # Hotel cost ratio
            
            # Activities features
            len(package.get("activities", {}).get("details", [])),  # Number of activities
            package.get("activities", {}).get("total", 0) / package["total"],  # Activities cost ratio
            
            # Meals & Transit
            package.get("meals", 0) / package["total"],  # Meals ratio
            package.get("transit", {}).get("total", 0) / package["total"],  # Transit ratio
            
            # Travel style encoding
            1 if travel_style == "budget" else 0,
            1 if travel_style == "moderate" else 0,
            1 if travel_style == "luxury" else 0,
            
            # Destination encoding (simplified - use proper encoding in production)
            hash(destination) % 100 / 100,  # Destination hash
            
            # Package completeness
            sum([
                1 if package.get("flight") else 0,
                1 if package.get("hotel") else 0,
                1 if package.get("activities", {}).get("total", 0) > 0 else 0
            ]) / 3  # Completeness ratio
        ]
        
        return features
    
    def _calculate_breakdown_from_features(self, features: list) -> Dict:
        """Estimate component scores from features"""
        budget_util = features[0]
        has_flight = features[2]
        has_hotel = features[4]
        num_activities = features[6]
        
        # Approximate breakdown (in production, train separate models)
        value = 50 + (50 * (1 - abs(0.9 - budget_util)))
        convenience = 60 + (20 if has_flight else 0) + (20 if has_hotel else 0)
        experience = 50 + min(num_activities * 10, 50)
        
        return {
            "value": value,
            "convenience": convenience,
            "experience": experience
        }
    
    def _rule_based_score(self, package: Dict, preferences: Dict, destination: str) -> Dict:
        """Fallback rule-based scoring (original implementation)"""
        
        # Value for money (30% weight)
        value_score = self._calculate_value_score(package, preferences)
        
        # Convenience (25% weight)
        convenience_score = self._calculate_convenience_score(package)
        
        # Experience quality (45% weight)
        experience_score = self._calculate_experience_score(package, destination)
        
        # Weighted overall score
        overall_score = (
            value_score * 0.30 +
            convenience_score * 0.25 +
            experience_score * 0.45
        )
        
        insights = self._generate_insights(value_score, convenience_score, experience_score)
        
        return {
            "overall_score": round(overall_score, 1),
            "value_score": round(value_score, 1),
            "convenience_score": round(convenience_score, 1),
            "experience_score": round(experience_score, 1),
            "insights": insights,
            "model_used": "Rule-Based"
        }
    
    def _calculate_value_score(self, package: Dict, preferences: Dict) -> float:
        """Calculate value for money (0-100)"""
        budget = preferences["budget"]
        total_cost = package["total"]
        
        # Score based on budget utilization
        utilization = (total_cost / budget) * 100
        
        if 85 <= utilization <= 95:  # Sweet spot
            return 100
        elif 70 <= utilization < 85:
            return 85
        elif 95 < utilization <= 100:
            return 75
        else:
            return max(50, 100 - abs(90 - utilization))
    
    def _calculate_convenience_score(self, package: Dict) -> float:
        """Calculate convenience score (0-100)"""
        score = 70  # Base score
        
        # Bonus for having all components
        if package.get("flight") and package.get("hotel"):
            score += 15
        
        # Bonus for activities included
        if package.get("activities", {}).get("total", 0) > 0:
            score += 15
        
        return min(score, 100)
    
    def _calculate_experience_score(self, package: Dict, destination: str) -> float:
        """Calculate expected experience quality (0-100)"""
        score = 60  # Base score
        
        # Hotel quality (if available)
        hotel = package.get("hotel")
        if hotel:
            hotel_price = hotel.get("total", 0)
            if hotel_price > 1000:
                score += 20
            elif hotel_price > 500:
                score += 15
            else:
                score += 10
        
        # Activities variety
        num_activities = len(package.get("activities", {}).get("details", []))
        score += min(num_activities * 2, 20)
        
        return min(score, 100)
    
    def _generate_insights(
        self, value: float, convenience: float, experience: float
    ) -> str:
        """Generate human-readable insights with reasoning"""
        reasons = []
        
        # Value reasoning
        if value > 90:
            reasons.append("excellent budget utilization (85-95% spent)")
        elif value > 75:
            reasons.append("good value for money")
        else:
            reasons.append("could optimize budget usage")
        
        # Convenience reasoning
        if convenience >= 100:
            reasons.append("complete package with all essentials")
        elif convenience >= 85:
            reasons.append("most components included")
        else:
            reasons.append("some components missing")
        
        # Experience reasoning
        if experience > 85:
            reasons.append("high-quality experiences")
        elif experience > 70:
            reasons.append("good mix of activities")
        else:
            reasons.append("basic experience level")
        
        return " • ".join(reasons).capitalize()
    
    def _generate_ml_insights(self, score: float, breakdown: Dict) -> str:
        """Generate insights from ML predictions with detailed reasoning"""
        if score >= 85:
            level = "Highly recommended"
        elif score >= 70:
            level = "Good choice"
        elif score >= 55:
            level = "Acceptable"
        else:
            level = "Consider alternatives"
        
        reasons = []
        if breakdown["value"] > 85:
            reasons.append("excellent value")
        if breakdown["convenience"] > 85:
            reasons.append("very convenient")
        if breakdown["experience"] > 80:
            reasons.append("great experiences")
        
        if reasons:
            return f"{level}: {', '.join(reasons)} (Score: {score:.0f}/100)"
        else:
            return f"{level} (Score: {score:.0f}/100)"


# Convenience function
def score_package(package: Dict, user_preferences: Dict, destination: str) -> Dict:
    scorer = PackageScorer()
    return scorer.score_package(package, user_preferences, destination)
