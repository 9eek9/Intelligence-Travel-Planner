"""
Generate Synthetic Training Data
Run this script to create fake but realistic training data
"""

import sys
import os

# Get the project root directory (parent of scripts folder)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from ml_models.synthetic_data_generator import SyntheticDataGenerator

def main():
    print("\n" + "="*60)
    print("🎲 GENERATING SYNTHETIC TRAINING DATA")
    print("="*60 + "\n")
    
    # Use absolute path from project root - FIXED
    data_dir = os.path.join(PROJECT_ROOT, 'ml_models', 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    print(f"📁 Data will be saved to: {data_dir}")
    
    # Generate data
    generator = SyntheticDataGenerator()
    df = generator.generate_training_data(n_samples=10000)
    
    # Save to CSV with absolute path - FIXED
    output_file = os.path.join(data_dir, 'training_data.csv')
    df.to_csv(output_file, index=False)
    print(f"💾 Saved to {output_file}")
    
    # Print statistics
    generator.print_statistics(df)
    
    print("✅ Data generation complete!")
    print("\n📁 Next step: Train the model by running:")
    print("   python scripts/train_model.py\n")

if __name__ == "__main__":
    main()