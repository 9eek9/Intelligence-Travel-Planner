"""
Data Collection Service
Manages collection of real user data for model improvement
"""

from models.budget_feedback import BudgetFeedback
from database.database import SessionLocal
import pandas as pd
import os

class DataCollectionService:
    """
    Handles saving predictions, actual spending, and user feedback
    Exports data for model retraining
    """
    
    @staticmethod
    def save_prediction(user_id, input_features, prediction, method='ml'):
        """
        Save a budget prediction when made
        
        Args:
            user_id: ID of the user making the request
            input_features: Dict with trip details
            prediction: Dict with predicted percentages
            method: 'ml' or 'rule_based'
            
        Returns:
            int: Feedback ID for future updates
        """
        try:
            feedback = BudgetFeedback(
                user_id=user_id,
                destination=input_features.get('destination'),
                region=input_features.get('region'),
                duration=input_features.get('duration'),
                total_budget=input_features.get('total_budget'),
                travelers=input_features.get('travelers', 1),
                season=input_features.get('season'),
                purpose=input_features.get('purpose'),
                accommodation_type=input_features.get('accommodation_type'),
                cost_index=input_features.get('cost_index', 1.0),
                suggested_accommodation_pct=prediction.get('accommodation'),
                suggested_transportation_pct=prediction.get('transportation'),
                suggested_food_pct=prediction.get('food'),
                suggested_activities_pct=prediction.get('activities'),
                suggested_miscellaneous_pct=prediction.get('miscellaneous'),
                prediction_method=method
            )
            
            db.session.add(feedback)
            db.session.commit()
            
            print(f"✅ Prediction saved (ID: {feedback.id})")
            return feedback.id
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error saving prediction: {e}")
            return None
    
    @staticmethod
    def update_actual_spending(feedback_id, actual_spending):
        """
        Update feedback with actual spending after trip
        
        Args:
            feedback_id: ID of the feedback record
            actual_spending: Dict with actual amounts spent
            
        Returns:
            bool: Success status
        """
        try:
            feedback = BudgetFeedback.query.get(feedback_id)
            if not feedback:
                print(f"❌ Feedback {feedback_id} not found")
                return False
            
            feedback.actual_accommodation_amt = actual_spending.get('accommodation')
            feedback.actual_transportation_amt = actual_spending.get('transportation')
            feedback.actual_food_amt = actual_spending.get('food')
            feedback.actual_activities_amt = actual_spending.get('activities')
            feedback.actual_miscellaneous_amt = actual_spending.get('miscellaneous')
            
            db.session.commit()
            print(f"✅ Actual spending updated for feedback {feedback_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error updating spending: {e}")
            return False
    
    @staticmethod
    def submit_user_feedback(feedback_id, rating, was_helpful, comments=None):
        """
        Collect user feedback on prediction quality
        
        Args:
            feedback_id: ID of the feedback record
            rating: 1-5 star rating
            was_helpful: Boolean
            comments: Optional text feedback
            
        Returns:
            bool: Success status
        """
        try:
            feedback = BudgetFeedback.query.get(feedback_id)
            if not feedback:
                print(f"❌ Feedback {feedback_id} not found")
                return False
            
            feedback.user_rating = rating
            feedback.was_helpful = was_helpful
            feedback.comments = comments
            
            db.session.commit()
            print(f"✅ User feedback submitted for {feedback_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error submitting feedback: {e}")
            return False
    
    @staticmethod
    def get_user_feedbacks(user_id, limit=10):
        """Get recent feedbacks for a user"""
        return BudgetFeedback.query.filter_by(user_id=user_id)\
            .order_by(BudgetFeedback.created_at.desc())\
            .limit(limit)\
            .all()
    
    @staticmethod
    def get_feedback_stats():
        """Get statistics about collected feedback"""
        total = BudgetFeedback.query.count()
        with_actual_spending = BudgetFeedback.query.filter(
            BudgetFeedback.actual_accommodation_amt.isnot(None)
        ).count()
        with_ratings = BudgetFeedback.query.filter(
            BudgetFeedback.user_rating.isnot(None)
        ).count()
        
        ml_predictions = BudgetFeedback.query.filter_by(prediction_method='ml').count()
        rule_predictions = BudgetFeedback.query.filter_by(prediction_method='rule_based').count()
        
        return {
            'total_predictions': total,
            'with_actual_spending': with_actual_spending,
            'with_user_ratings': with_ratings,
            'ml_predictions': ml_predictions,
            'rule_based_predictions': rule_predictions,
            'ready_for_retraining': with_actual_spending >= 100
        }
    
    @staticmethod
    def export_for_retraining(min_samples=100, output_path='ml_models/data/real_user_data.csv'):
        """
        Export real user data for model retraining
        
        Args:
            min_samples: Minimum samples needed
            output_path: Where to save the CSV
            
        Returns:
            DataFrame or None
        """
        # Only export completed feedback with actual spending
        feedbacks = BudgetFeedback.query.filter(
            BudgetFeedback.actual_accommodation_amt.isnot(None)
        ).all()
        
        if len(feedbacks) < min_samples:
            print(f"⚠️  Not enough samples for retraining.")
            print(f"   Have: {len(feedbacks)}, Need: {min_samples}")
            return None
        
        print(f"📊 Exporting {len(feedbacks)} real user samples...")
        
        data = []
        for fb in feedbacks:
            # Calculate total actual spending
            total_actual = (
                fb.actual_accommodation_amt + 
                fb.actual_transportation_amt + 
                fb.actual_food_amt + 
                fb.actual_activities_amt + 
                fb.actual_miscellaneous_amt
            )
            
            # Calculate actual percentages
            data.append({
                'destination': fb.destination,
                'region': fb.region,
                'duration': fb.duration,
                'total_budget': total_actual,
                'travelers': fb.travelers,
                'budget_per_day': total_actual / fb.duration,
                'budget_per_person': total_actual / fb.travelers,
                'season': fb.season,
                'purpose': fb.purpose,
                'accommodation_type': fb.accommodation_type,
                'cost_index': fb.cost_index,
                'accommodation_pct': fb.actual_accommodation_amt / total_actual,
                'transportation_pct': fb.actual_transportation_amt / total_actual,
                'food_pct': fb.actual_food_amt / total_actual,
                'activities_pct': fb.actual_activities_amt / total_actual,
                'miscellaneous_pct': fb.actual_miscellaneous_amt / total_actual,
                'user_rating': fb.user_rating
            })
        
        df = pd.DataFrame(data)
        
        # Save to CSV
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        
        print(f"✅ Exported {len(df)} samples to {output_path}")
        print("   Ready for model retraining!")
        
        return df