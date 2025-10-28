"""
Train Budget Optimization Model
Run this script to train the ML model using synthetic data
"""

import sys
import os

# Get the project root directory (parent of scripts folder)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from ml_models.model_trainer import BudgetModelTrainer

def main():
    print("\n" + "="*60)
    print("🧠 TRAINING BUDGET OPTIMIZATION MODEL")
    print("="*60 + "\n")
    
    # Use absolute path from project root - FIXED
    data_path = os.path.join(PROJECT_ROOT, 'ml_models', 'data', 'training_data.csv')
    models_dir = os.path.join(PROJECT_ROOT, 'ml_models', 'models')
    
    print(f"📁 Looking for training data at: {data_path}")
    
    # Check if training data exists
    if not os.path.exists(data_path):
        print("❌ Error: Training data not found!")
        print("\n📁 Please generate data first by running:")
        print("   python scripts/generate_data.py\n")
        return
    
    # Create models directory
    os.makedirs(models_dir, exist_ok=True)
    print(f"📁 Models will be saved to: {models_dir}")
    
    # Train model
    trainer = BudgetModelTrainer()
    metrics = trainer.train(data_path)
    
    print("\n✅ Model training complete!")
    print(f"\n📁 Model files saved to: {models_dir}")
    print("   - budget_model.pkl")
    print("   - scaler.pkl")
    print("   - label_encoders.pkl")
    print("   - model_metadata.json")
    
    print("\n🚀 Next step: Integrate with your API")
    print("   The model is ready to make predictions!\n")

if __name__ == "__main__":
    main()