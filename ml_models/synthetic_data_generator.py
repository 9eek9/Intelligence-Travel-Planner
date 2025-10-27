"""
Synthetic Data Generator
Generates realistic training data based on travel industry standards
since we don't have real user data yet.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

class SyntheticDataGenerator:
    def __init__(self):
        # Industry standard budget distributions for different traveler types
        self.budget_templates = {
            'budget': {
                'accommodation': 0.35,
                'transportation': 0.30,
                'food': 0.20,
                'activities': 0.10,
                'miscellaneous': 0.05
            },
            'moderate': {
                'accommodation': 0.40,
                'transportation': 0.25,
                'food': 0.18,
                'activities': 0.12,
                'miscellaneous': 0.05
            },
            'luxury': {
                'accommodation': 0.45,
                'transportation': 0.20,
                'food': 0.15,
                'activities': 0.15,
                'miscellaneous': 0.05
            }
        }
        
        # Popular destinations with cost characteristics
        self.destinations = {
            'Paris': {'cost_index': 1.2, 'type': 'expensive', 'region': 'Europe'},
            'Bangkok': {'cost_index': 0.6, 'type': 'budget', 'region': 'Asia'},
            'New York': {'cost_index': 1.5, 'type': 'expensive', 'region': 'North America'},
            'Bali': {'cost_index': 0.7, 'type': 'budget', 'region': 'Asia'},
            'Dubai': {'cost_index': 1.3, 'type': 'luxury', 'region': 'Middle East'},
            'London': {'cost_index': 1.4, 'type': 'expensive', 'region': 'Europe'},
            'Mexico City': {'cost_index': 0.8, 'type': 'moderate', 'region': 'Latin America'},
            'Tokyo': {'cost_index': 1.1, 'type': 'moderate', 'region': 'Asia'},
            'Barcelona': {'cost_index': 1.0, 'type': 'moderate', 'region': 'Europe'},
            'Istanbul': {'cost_index': 0.7, 'type': 'budget', 'region': 'Middle East'},
            'Rome': {'cost_index': 1.1, 'type': 'moderate', 'region': 'Europe'},
            'Singapore': {'cost_index': 1.3, 'type': 'expensive', 'region': 'Asia'},
            'Lisbon': {'cost_index': 0.9, 'type': 'moderate', 'region': 'Europe'},
            'Prague': {'cost_index': 0.8, 'type': 'budget', 'region': 'Europe'},
            'Sydney': {'cost_index': 1.2, 'type': 'expensive', 'region': 'Oceania'}
        }
        
        self.travel_purposes = ['leisure', 'business', 'family', 'adventure', 'romantic']
        self.accommodation_types = ['hotel', 'hostel', 'airbnb', 'resort', 'apartment']
        
    def generate_training_data(self, n_samples=10000):
        """
        Generate synthetic training data
        
        Args:
            n_samples: Number of samples to generate
            
        Returns:
            DataFrame with training data
        """
        print(f"Generating {n_samples} synthetic samples...")
        data = []
        
        for i in range(n_samples):
            if (i + 1) % 1000 == 0:
                print(f"  Generated {i + 1}/{n_samples} samples...")
            
            # Generate random trip characteristics
            destination = np.random.choice(list(self.destinations.keys()))
            duration = np.random.randint(3, 15)
            total_budget = np.random.uniform(500, 10000)
            travelers = np.random.randint(1, 5)
            season = np.random.choice(['peak', 'off_peak', 'shoulder'], p=[0.3, 0.4, 0.3])
            purpose = np.random.choice(self.travel_purposes)
            accommodation_type = np.random.choice(self.accommodation_types)
            
            # Determine budget category
            budget_per_day_per_person = total_budget / (duration * travelers)
            if budget_per_day_per_person < 80:
                category = 'budget'
            elif budget_per_day_per_person < 250:
                category = 'moderate'
            else:
                category = 'luxury'
            
            # Get base distribution
            distribution = self.budget_templates[category].copy()
            
            # Apply realistic adjustments
            distribution = self._apply_adjustments(
                distribution, 
                destination, 
                duration, 
                season, 
                purpose,
                accommodation_type,
                travelers
            )
            
            # Normalize to ensure sum = 1.0
            total_pct = sum(distribution.values())
            distribution = {k: v/total_pct for k, v in distribution.items()}
            
            # Create data record
            data.append({
                # Input features
                'destination': destination,
                'region': self.destinations[destination]['region'],
                'duration': duration,
                'total_budget': total_budget,
                'travelers': travelers,
                'budget_per_day': total_budget / duration,
                'budget_per_person': total_budget / travelers,
                'season': season,
                'purpose': purpose,
                'accommodation_type': accommodation_type,
                'cost_index': self.destinations[destination]['cost_index'],
                
                # Target variables (percentages)
                'accommodation_pct': distribution['accommodation'],
                'transportation_pct': distribution['transportation'],
                'food_pct': distribution['food'],
                'activities_pct': distribution['activities'],
                'miscellaneous_pct': distribution['miscellaneous'],
                
                # Absolute amounts (for reference)
                'accommodation_amt': total_budget * distribution['accommodation'],
                'transportation_amt': total_budget * distribution['transportation'],
                'food_amt': total_budget * distribution['food'],
                'activities_amt': total_budget * distribution['activities'],
                'miscellaneous_amt': total_budget * distribution['miscellaneous']
            })
        
        df = pd.DataFrame(data)
        print(f"✅ Generated {len(df)} samples successfully")
        return df
    
    def _apply_adjustments(self, distribution, destination, duration, season, 
                          purpose, accommodation_type, travelers):
        """
        Apply realistic adjustments based on various factors
        This simulates how real travelers allocate their budgets
        """
        
        # 1. Destination cost adjustment
        cost_factor = self.destinations[destination]['cost_index']
        if cost_factor > 1.2:  # Expensive destination
            distribution['accommodation'] += 0.05
            distribution['food'] += 0.03
            distribution['activities'] -= 0.08
        
        # 2. Duration adjustment
        if duration < 5:  # Short trip - more transport proportion
            distribution['transportation'] += 0.05
            distribution['accommodation'] -= 0.05
        elif duration > 10:  # Long trip - more accommodation
            distribution['accommodation'] += 0.05
            distribution['miscellaneous'] += 0.02
            distribution['transportation'] -= 0.07
        
        # 3. Season adjustment
        if season == 'peak':  # Peak season - higher costs
            distribution['accommodation'] += 0.05
            distribution['transportation'] += 0.03
            distribution['food'] -= 0.05
            distribution['miscellaneous'] -= 0.03
        
        # 4. Purpose adjustment
        if purpose == 'business':
            distribution['accommodation'] += 0.08
            distribution['food'] += 0.05
            distribution['activities'] -= 0.13
        elif purpose == 'adventure':
            distribution['activities'] += 0.10
            distribution['accommodation'] -= 0.05
            distribution['food'] -= 0.05
        elif purpose == 'romantic':
            distribution['accommodation'] += 0.05
            distribution['food'] += 0.05
            distribution['activities'] -= 0.10
        elif purpose == 'family':
            distribution['activities'] += 0.05
            distribution['food'] += 0.05
            distribution['accommodation'] -= 0.10
        
        # 5. Accommodation type adjustment
        if accommodation_type == 'hostel':
            distribution['accommodation'] -= 0.10
            distribution['activities'] += 0.10
        elif accommodation_type == 'resort':
            distribution['accommodation'] += 0.10
            distribution['activities'] -= 0.05
            distribution['transportation'] -= 0.05
        elif accommodation_type == 'airbnb':
            distribution['accommodation'] -= 0.03
            distribution['food'] += 0.03
        
        # 6. Group size adjustment
        if travelers > 3:
            distribution['accommodation'] += 0.05
            distribution['food'] += 0.03
            distribution['transportation'] -= 0.08
        
        # Add random noise (±5%) for variety
        for key in distribution:
            noise = np.random.uniform(-0.05, 0.05) * distribution[key]
            distribution[key] = max(0.05, distribution[key] + noise)
        
        return distribution
    
    def save_to_csv(self, df, filename='training_data.csv'):
        """Save generated data to CSV file"""
        # If filename is just a name, put it in ml_models/data/
        # If it's an absolute path, use it directly
        if os.path.isabs(filename):
            filepath = filename
        else:
            filepath = f'ml_models/data/{filename}'
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        df.to_csv(filepath, index=False)
        print(f"💾 Saved to {filepath}")
        
    def print_statistics(self, df):
        """Print dataset statistics"""
        print("\n" + "="*50)
        print("📊 DATASET STATISTICS")
        print("="*50)
        print(f"\n📝 Total samples: {len(df)}")
        print(f"\n💰 Budget range: ${df['total_budget'].min():.2f} - ${df['total_budget'].max():.2f}")
        print(f"   Average budget: ${df['total_budget'].mean():.2f}")
        
        print(f"\n🌍 Destination distribution:")
        print(df['destination'].value_counts().head(10))
        
        print(f"\n📅 Duration range: {df['duration'].min()} - {df['duration'].max()} days")
        print(f"   Average: {df['duration'].mean():.1f} days")
        
        print(f"\n👥 Travelers range: {df['travelers'].min()} - {df['travelers'].max()}")
        print(f"   Average: {df['travelers'].mean():.1f}")
        
        print(f"\n💵 Average Budget Allocations:")
        print(f"   🏨 Accommodation: {df['accommodation_pct'].mean()*100:.1f}%")
        print(f"   ✈️  Transportation: {df['transportation_pct'].mean()*100:.1f}%")
        print(f"   🍽️  Food: {df['food_pct'].mean()*100:.1f}%")
        print(f"   🎭 Activities: {df['activities_pct'].mean()*100:.1f}%")
        print(f"   💼 Miscellaneous: {df['miscellaneous_pct'].mean()*100:.1f}%")
        print("="*50 + "\n")


# Standalone usage
if __name__ == "__main__":
    generator = SyntheticDataGenerator()
    df = generator.generate_training_data(n_samples=10000)
    generator.save_to_csv(df)
    generator.print_statistics(df)