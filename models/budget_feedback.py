"""
Budget Feedback Model
Stores ML predictions and actual user spending for future model improvement
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base  # Adjust this import based on your database.py location

class BudgetFeedback(Base):
    """
    Stores budget predictions and actual spending
    Used to collect real data for model retraining
    """
    __tablename__ = 'budget_feedback'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Trip details (input features)
    destination = Column(String(100), nullable=False)
    region = Column(String(50))
    duration = Column(Integer, nullable=False)
    total_budget = Column(Float, nullable=False)
    travelers = Column(Integer, default=1)
    season = Column(String(20))
    purpose = Column(String(50))
    accommodation_type = Column(String(50))
    cost_index = Column(Float, default=1.0)
    
    # Suggested allocation (what we predicted)
    suggested_accommodation_pct = Column(Float)
    suggested_transportation_pct = Column(Float)
    suggested_food_pct = Column(Float)
    suggested_activities_pct = Column(Float)
    suggested_miscellaneous_pct = Column(Float)
    
    # Actual spending (collected after trip - optional)
    actual_accommodation_amt = Column(Float, nullable=True)
    actual_transportation_amt = Column(Float, nullable=True)
    actual_food_amt = Column(Float, nullable=True)
    actual_activities_amt = Column(Float, nullable=True)
    actual_miscellaneous_amt = Column(Float, nullable=True)
    
    # User feedback
    user_rating = Column(Integer, nullable=True)  # 1-5 stars
    was_helpful = Column(Boolean, nullable=True)
    comments = Column(Text, nullable=True)
    
    # Metadata
    prediction_method = Column(String(20))  # 'ml' or 'rule_based'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to user (uncomment if you have User model)
    # user = relationship('User', back_populates='budget_feedbacks')
    
    def to_dict(self):
        """Convert to dictionary for JSON response"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'destination': self.destination,
            'duration': self.duration,
            'total_budget': self.total_budget,
            'travelers': self.travelers,
            'suggested_allocation': {
                'accommodation': self.suggested_accommodation_pct,
                'transportation': self.suggested_transportation_pct,
                'food': self.suggested_food_pct,
                'activities': self.suggested_activities_pct,
                'miscellaneous': self.suggested_miscellaneous_pct
            },
            'actual_spending': {
                'accommodation': self.actual_accommodation_amt,
                'transportation': self.actual_transportation_amt,
                'food': self.actual_food_amt,
                'activities': self.actual_activities_amt,
                'miscellaneous': self.actual_miscellaneous_amt
            } if self.actual_accommodation_amt else None,
            'user_feedback': {
                'rating': self.user_rating,
                'was_helpful': self.was_helpful,
                'comments': self.comments
            } if self.user_rating else None,
            'prediction_method': self.prediction_method,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<BudgetFeedback {self.id} - {self.destination} - ${self.total_budget}>'