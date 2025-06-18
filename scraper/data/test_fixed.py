import json
import os
import re
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from wordcloud import WordCloud
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import plotly.express as px

def analyze_calorie_value(df):
    """Analyze calorie content and other metrics per euro spent"""
    # Calculate value metrics
    df['kcal_per_euro'] = df['nutrient_energie_kc'] / df['price']
    df['fat_per_euro'] = df['nutrient_vet'] / df['price']
    df['carbs_per_euro'] = df['nutrient_koolhydraten'] / df['price']
    df['protein_per_euro'] = df['nutrient_eiwitten'] / df['price']
    
    metrics = {
        'Calories': {'col': 'kcal_per_euro', 'unit': 'kcal'},
        'Fat': {'col': 'fat_per_euro', 'unit': 'g'},
        'Carbs': {'col': 'carbs_per_euro', 'unit': 'g'},
        'Protein': {'col': 'protein_per_euro', 'unit': 'g'}
    }
    
    top_products = {}
    for metric_name, info in metrics.items():
        col = info['col']
        unit = info['unit']
        valid_data = df[df[col].notna() & (df[col] > 0)]
        
        # Get top 20 products
        top = valid_data.nlargest(20, col)[['name', 'price', col]].round(2)
        top_products[metric_name] = top
        
        # Create visualization
        plt.figure(figsize=(15, 8))
        sns.barplot(data=top, x=col, y='name')
        plt.title(f'Top 20 Products by {metric_name} per Euro')
        plt.xlabel(f'{metric_name} ({unit}) per Euro')
        plt.tight_layout()
        plt.savefig(f'analysis/{metric_name.lower()}_value.png')
        plt.close()

    # Calculate overall value score
    max_values = {
        'kcal': df['kcal_per_euro'].max(),
        'fat': df['fat_per_euro'].max(),
        'carbs': df['carbs_per_euro'].max(),
        'protein': df['protein_per_euro'].max()
    }
    
    df['value_score'] = df.apply(lambda row: sum([
        row['kcal_per_euro'] / max_values['kcal'] if not pd.isna(row['kcal_per_euro']) else 0,
        row['fat_per_euro'] / max_values['fat'] if not pd.isna(row['fat_per_euro']) else 0,
        row['carbs_per_euro'] / max_values['carbs'] if not pd.isna(row['carbs_per_euro']) else 0,
        row['protein_per_euro'] / max_values['protein'] if not pd.isna(row['protein_per_euro']) else 0
    ]) / 4, axis=1)
    
    # Get top 20 overall value products
    best_value = df.nlargest(20, 'value_score')[
        ['name', 'price', 'value_score', 'kcal_per_euro', 'protein_per_euro', 'fat_per_euro', 'carbs_per_euro']
    ].round(2)
    
    # Calculate calories per euro by category
    category_stats = df.groupby('category').agg({
        'kcal_per_euro': ['mean', 'max'],
        'fat_per_euro': ['mean', 'max'],
        'carbs_per_euro': ['mean', 'max'],
        'protein_per_euro': ['mean', 'max']
    }).round(2)
    
    return top_products, best_value, category_stats

def load_products_to_df():
    """Load products from JSON and convert to DataFrame"""
    with open(Path(__file__).parent / "all_products.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
        products_list = data['products']
    
    df = pd.json_normalize(products_list)
    
    # Convert price to numeric
    df['price'] = pd.to_numeric(df['price'].str.replace('€', '').str.replace(',', '.'), errors='coerce')
    
    # Extract nutrients
    nutrient_names = ['energie kc', 'eiwitten', 'koolhydraten', 'suikers', 'vet', 'verzadigd vet', 'zout']
    
    for nutrient in nutrient_names:
        col_name = f'nutrient_{nutrient.replace(" ", "_")}'
        df[col_name] = df['nutrients'].apply(lambda x: extract_nutrient_value(x, nutrient))
        df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
    
    return df

def extract_nutrient_value(nutrients_list, nutrient_name):
    """Extract a specific nutrient value from the nutrients list"""
    if not isinstance(nutrients_list, list):
        return None
    
    for nutrient in nutrients_list:
        if isinstance(nutrient, dict) and nutrient.get('name', '').lower().startswith(nutrient_name.lower()):
            try:
                return float(nutrient.get('value', 0))
            except (ValueError, TypeError):
                return None
    return None

def main():
    print("Starting analysis...")
    # Create analysis directory if it doesn't exist
    Path('analysis').mkdir(exist_ok=True)
    
    # Load data
    print("Loading data...")
    df = load_products_to_df()
    print(f"Loaded {len(df)} products")
    
    # Run calorie value analysis
    print("Running calorie analysis...")
    value_products, best_value, category_value = analyze_calorie_value(df)
    
    print("\nTop Products by Calories per Euro:")
    print(value_products['Calories'])
    
    print("\nTop Products by Fat per Euro:")
    print(value_products['Fat'])
    
    print("\nTop Products by Carbs per Euro:")
    print(value_products['Carbs'])
    
    print("\nTop Products by Protein per Euro:")
    print(value_products['Protein'])
    
    print("\nBest Overall Value Products (Combined Nutrients):")
    print(best_value)
    
    print("\nNutrient Value by Category:")
    print(category_value)

if __name__ == "__main__":
    main()
