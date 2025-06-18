import os
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import requests
from io import BytesIO
from PIL import Image
import matplotlib.gridspec as gridspec
from pathlib import Path
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import re
import warnings
import math
import time
warnings.filterwarnings('ignore')

# Path to product data
PRODUCTS_DIR = Path('products')

def load_product_data():
    """Load all product data from JSON files."""
    products = []
    for filename in tqdm(list(PRODUCTS_DIR.glob('*.json')), desc="Loading products"):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                product = json.load(f)
                # Add the filename as reference
                product['file_id'] = filename.stem
                products.append(product)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"Error loading {filename}: {e}")
    
    print(f"Loaded {len(products)} products")
    return products

def clean_and_convert_data(products):
    """Clean and convert product data to correct types."""
    df = pd.DataFrame(products)
    
    # Convert price and base_unit_price to float
    for col in ['price', 'base_unit_price']:
        df[col] = df[col].astype(str).str.replace(',', '.').replace('', '0')
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Extract nutrients data
    df_with_nutrients = extract_nutrients(df)
    
    # Normalize the base_unit_price
    df_with_nutrients = normalize_base_unit_price(df_with_nutrients)
    
    return df_with_nutrients

def extract_nutrients(df):
    """Extract nutrient information from the product data."""
    # Initialize columns for each nutrient type
    nutrient_cols = {
        'Energie KC': 'calories',
        'Eiwitten': 'protein',
        'Koolhydraten': 'carbs',
        'Vet': 'fat',
        'Waarvan suikers': 'sugars',
        'Vezel': 'fiber',
        'Zout': 'salt',
        'Waarvan verzadigd vet': 'saturated_fat'
    }
    
    for col in nutrient_cols.values():
        df[col] = np.nan
    
    # Extract nutrient values
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Extracting nutrients"):
        nutrients = row.get('nutrients', [])
        if not nutrients:
            continue
            
        for nutrient in nutrients:
            name = nutrient.get('name', '')
            value_str = nutrient.get('value', '0')
            
            if name in nutrient_cols and value_str:
                try:
                    # Convert to float
                    value = float(str(value_str).replace(',', '.'))
                    df.at[idx, nutrient_cols[name]] = value
                except (ValueError, TypeError):
                    pass
    
    # Create additional metrics
    df['protein_per_euro'] = df['protein'] / df['price'].replace(0, np.nan)
    df['calories_per_euro'] = df['calories'] / df['price'].replace(0, np.nan)
    
    return df

def normalize_base_unit_price(df):
    """Normalize base unit price by interpreting the value correctly."""
    # If base_unit_price is significantly higher than price, it's likely per kg/liter
    # If they're similar, it's likely per piece
    df['unit_price_ratio'] = df['base_unit_price'] / df['price'].replace(0, np.nan)
    
    # Create a normalized price column
    df['normalized_price'] = df['price'].copy()
    
    # If ratio > 3, it's likely per kg/liter
    high_ratio = (df['unit_price_ratio'] > 3) & df['unit_price_ratio'].notna()
    df.loc[high_ratio, 'price_unit'] = 'per kg/liter'
    
    # Otherwise, it's likely per piece
    df.loc[~high_ratio, 'price_unit'] = 'per piece'
    
    return df

def download_image(url, max_retries=3):
    """Download image from URL with retries."""
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                # Validate image dimensions
                if img.width <= 0 or img.height <= 0:
                    raise ValueError("Invalid image dimensions")
                return img
            retries += 1
            time.sleep(1)  # Wait a bit before retrying
        except Exception as e:
            retries += 1
            if retries >= max_retries:
                print(f"Error downloading image {url}: {e}")
            time.sleep(1)  # Wait a bit before retrying
    return None

def download_all_images(df, sample_size=20):
    """Download images for products with a limited sample size."""
    # Limit the number of images to download to avoid timeouts
    if sample_size and len(df) > sample_size:
        sample_df = df.sample(sample_size)
    else:
        sample_df = df
    
    urls = sample_df['image_url'].tolist()
    
    images = {}
    for url in tqdm(urls, desc="Downloading images"):
        img = download_image(url)
        if img:
            images[url] = img
            
    return images

def create_top_calories_graph(df, images, top_n=15, save_fig=True):
    """Create graph showing products with the most calories."""
    plt.figure(figsize=(15, 12))
    
    # Filter data
    top_calories = df.dropna(subset=['calories']).sort_values('calories', ascending=False).head(top_n)
    
    # Create bar chart
    ax = sns.barplot(x='calories', y='name', data=top_calories, palette='YlOrRd')
      # Add images
    for i, (_, row) in enumerate(top_calories.iterrows()):
        if row['image_url'] in images:
            img = images[row['image_url']]
            img_height = 0.8
            # Add safety check to prevent zero dimensions
            if img.height > 0 and img.width > 0:
                new_width = max(1, int(img.width * img_height / img.height))
                new_height = max(1, int(img_height * 100))
                img = img.resize((new_width, new_height))
                im = OffsetImage(img, zoom=0.15)
                ab = AnnotationBbox(im, (row['calories'] + 20, i), 
                                  xybox=(row['calories'] + 50, i),
                                  frameon=False,
                                  xycoords='data',
                                  boxcoords="data",
                                  pad=0)
            ax.add_artist(ab)
    
    # Style the chart
    plt.title('Products with the Highest Calories (per 100g/ml)', fontsize=18)
    plt.xlabel('Calories (kcal per 100g/ml)', fontsize=14)
    plt.tight_layout()
    
    if save_fig:
        plt.savefig('top_calories_products.png', dpi=300, bbox_inches='tight')
    
    plt.close()

def create_protein_price_ratio_graph(df, images, top_n=15, save_fig=True):
    """Create graph showing the best protein/price ratio."""
    plt.figure(figsize=(15, 12))
    
    # Filter data
    best_protein_deal = df.dropna(subset=['protein_per_euro']).sort_values('protein_per_euro', ascending=False).head(top_n)
    
    # Create bar chart
    ax = sns.barplot(x='protein_per_euro', y='name', data=best_protein_deal, palette='viridis')
      # Add images
    for i, (_, row) in enumerate(best_protein_deal.iterrows()):
        if row['image_url'] in images:
            img = images[row['image_url']]
            img_height = 0.8
            # Add safety check to prevent zero dimensions
            if img.height > 0 and img.width > 0:
                new_width = max(1, int(img.width * img_height / img.height))
                new_height = max(1, int(img_height * 100))
                img = img.resize((new_width, new_height))
                im = OffsetImage(img, zoom=0.15)
                ab = AnnotationBbox(im, (row['protein_per_euro'] + 1, i), 
                                  xybox=(row['protein_per_euro'] + 2, i),
                                  frameon=False,
                                  xycoords='data',
                                  boxcoords="data",
                                  pad=0)
            ax.add_artist(ab)
    
    # Style the chart
    plt.title('Best Protein Value (Grams of Protein per Euro)', fontsize=18)
    plt.xlabel('Protein (g) per Euro', fontsize=14)
    plt.tight_layout()
    
    if save_fig:
        plt.savefig('best_protein_value.png', dpi=300, bbox_inches='tight')
    
    plt.close()

def create_nutrition_bubble_chart(df, images, save_fig=True):
    """Create bubble chart showing protein, carbs, fat content."""
    plt.figure(figsize=(16, 12))
    
    # Filter products with all required nutrients
    filtered_df = df.dropna(subset=['protein', 'carbs', 'fat', 'calories']).copy()
    
    # Select a sample of products for better visualization
    if len(filtered_df) > 50:
        sample_df = filtered_df.sample(50)
    else:
        sample_df = filtered_df
    
    # Create bubble chart
    plt.scatter(sample_df['carbs'], sample_df['fat'], s=sample_df['protein']*20, 
                alpha=0.6, c=sample_df['calories'], cmap='plasma')
    
    # Add hover annotations for products
    for _, row in sample_df.iterrows():
        plt.annotate(row['name'], 
                   (row['carbs'], row['fat']),
                   fontsize=8,
                   alpha=0.7)
    
    # Style the chart
    plt.title('Nutritional Composition of Products', fontsize=18)
    plt.xlabel('Carbohydrates (g per 100g/ml)', fontsize=14)
    plt.ylabel('Fat (g per 100g/ml)', fontsize=14)
    plt.colorbar(label='Calories (per 100g/ml)')
    plt.grid(alpha=0.3)
    plt.tight_layout()
    
    if save_fig:
        plt.savefig('nutrition_bubble_chart.png', dpi=300, bbox_inches='tight')
    
    plt.close()

def create_brand_comparison_chart(df, save_fig=True):
    """Create chart comparing brands by average calories and protein."""
    # Group by brand
    brand_stats = df.groupby('brand').agg({
        'calories': 'mean',
        'protein': 'mean',
        'price': 'mean',
        'name': 'count'
    }).reset_index()
    
    # Filter brands with at least 5 products
    brand_stats = brand_stats[brand_stats['name'] >= 5].sort_values('calories', ascending=False)
    
    if len(brand_stats) > 0:
        plt.figure(figsize=(14, 10))
        
        # Create a horizontal bar chart
        sns.set_color_codes("pastel")
        sns.barplot(x="calories", y="brand", data=brand_stats.head(15), 
                  label="Calories", color="r")
        
        # Add a second bar chart for protein
        sns.set_color_codes("muted")
        sns.barplot(x="protein", y="brand", data=brand_stats.head(15), 
                  label="Protein", color="b")
        
        # Add legend and labels
        plt.legend(ncol=2, loc="lower right", frameon=True)
        plt.title('Brand Comparison: Average Calories vs Protein Content', fontsize=18)
        plt.xlabel('Value per 100g/ml', fontsize=14)
        plt.tight_layout()
        
        if save_fig:
            plt.savefig('brand_comparison.png', dpi=300, bbox_inches='tight')
        
        plt.close()

def create_allergen_analysis_chart(df, save_fig=True):
    """Create chart showing most common allergens."""
    # Extract allergens from the allergens field
    allergens = []
    for allergen_str in df['allergens'].dropna():
        if allergen_str:
            # Split by common separators
            parts = re.split(r',|;|\s+', allergen_str)
            allergens.extend([a.strip() for a in parts if a.strip()])
    
    # Count allergens
    allergen_counts = pd.Series(allergens).value_counts().head(15)
    
    plt.figure(figsize=(14, 8))
    sns.barplot(x=allergen_counts.values, y=allergen_counts.index, palette='rocket')
    plt.title('Most Common Allergens in Products', fontsize=18)
    plt.xlabel('Number of Products', fontsize=14)
    plt.tight_layout()
    
    if save_fig:
        plt.savefig('common_allergens.png', dpi=300, bbox_inches='tight')
    
    plt.close()

def create_fat_protein_scatter(df, images, save_fig=True):
    """Create scatter plot of fat vs protein content with product types."""
    plt.figure(figsize=(16, 14))
    
    # Filter products with required nutrients
    filtered_df = df.dropna(subset=['fat', 'protein']).copy()
    
    # Create categories based on first word of product name
    filtered_df['category'] = filtered_df['name'].str.split().str[0]
    
    # Get the top categories
    top_categories = filtered_df['category'].value_counts().head(10).index
    
    # Filter for top categories and sample to avoid overcrowding
    plot_df = filtered_df[filtered_df['category'].isin(top_categories)]
    if len(plot_df) > 100:
        plot_df = plot_df.sample(100)
    
    # Create a scatter plot
    ax = sns.scatterplot(x='fat', y='protein', hue='category', 
                       data=plot_df, s=100, alpha=0.7)
      # Add product images for interesting data points
    high_protein = plot_df.sort_values('protein', ascending=False).head(5)
    high_fat = plot_df.sort_values('fat', ascending=False).head(5)
    # Use subset parameter to avoid unhashable type error with dictionaries in other columns
    interesting_products = pd.concat([high_protein, high_fat]).drop_duplicates(subset=['name', 'fat', 'protein'])
    for _, row in interesting_products.iterrows():
        if row['image_url'] in images:
            img = images[row['image_url']]
            img_height = 100
            # Add safety check to prevent zero dimensions
            if img.height > 0 and img.width > 0:
                img_width = max(1, int(img.width * img_height / img.height))
                img = img.resize((img_width, img_height))
                im = OffsetImage(img, zoom=0.15)
                ab = AnnotationBbox(im, (row['fat'], row['protein']), 
                                 xybox=(10, 10), 
                                 xycoords='data',
                                 boxcoords="offset points",
                                 pad=0.5,
                                 arrowprops=dict(arrowstyle="->"))
            ax.add_artist(ab)
    
    # Style the chart
    plt.title('Fat vs. Protein Content by Product Type', fontsize=18)
    plt.xlabel('Fat (g per 100g/ml)', fontsize=14)
    plt.ylabel('Protein (g per 100g/ml)', fontsize=14)
    plt.grid(alpha=0.3)
    plt.legend(title='Product Type')
    plt.tight_layout()
    
    if save_fig:
        plt.savefig('fat_protein_scatter.png', dpi=300, bbox_inches='tight')
    
    plt.close()

def create_sugar_content_by_category(df, save_fig=True):
    """Create bar chart showing average sugar content by product category."""
    # Extract category from product name (using first two words)
    df['category'] = df['name'].str.split().str[:2].str.join(' ')
    
    # Group by category and calculate average sugar
    sugar_by_category = df.groupby('category').agg({
        'sugars': 'mean',
        'name': 'count'
    }).reset_index()
    
    # Filter categories with at least 3 products and sugar data
    sugar_by_category = sugar_by_category[
        (sugar_by_category['name'] >= 3) & 
        sugar_by_category['sugars'].notna()
    ].sort_values('sugars', ascending=False)
    
    if len(sugar_by_category) > 0:
        plt.figure(figsize=(14, 10))
        
        # Create bar chart
        sns.barplot(x='sugars', y='category', data=sugar_by_category.head(15), 
                  palette='YlOrBr')
        
        # Style chart
        plt.title('Average Sugar Content by Product Category', fontsize=18)
        plt.xlabel('Sugar (g per 100g/ml)', fontsize=14)
        plt.tight_layout()
        
        if save_fig:
            plt.savefig('sugar_by_category.png', dpi=300, bbox_inches='tight')
        
        plt.close()

def create_price_distribution_chart(df, save_fig=True):
    """Create histogram of product prices."""
    plt.figure(figsize=(14, 8))
    
    # Filter out extreme values
    price_df = df[(df['price'] > 0) & (df['price'] < df['price'].quantile(0.95))]
    
    # Create histogram
    sns.histplot(price_df['price'], bins=50, kde=True)
    
    # Style chart
    plt.title('Product Price Distribution', fontsize=18)
    plt.xlabel('Price (€)', fontsize=14)
    plt.ylabel('Number of Products', fontsize=14)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    
    if save_fig:
        plt.savefig('price_distribution.png', dpi=300, bbox_inches='tight')
    
    plt.close()
    
def create_dashboard(df, images):
    """Create a dashboard of all charts."""
    # Define the layout
    fig = plt.figure(figsize=(20, 30))
    gs = gridspec.GridSpec(4, 2, figure=fig)
    
    # Top calories
    ax1 = fig.add_subplot(gs[0, 0])
    top_calories = df.dropna(subset=['calories']).sort_values('calories', ascending=False).head(10)
    sns.barplot(x='calories', y='name', data=top_calories, ax=ax1, palette='YlOrRd')
    ax1.set_title('Top 10 Highest Calorie Products', fontsize=16)
    ax1.set_xlabel('Calories (kcal per 100g/ml)', fontsize=12)
    ax1.set_ylabel('')
    
    # Best protein value
    ax2 = fig.add_subplot(gs[0, 1])
    best_protein = df.dropna(subset=['protein_per_euro']).sort_values('protein_per_euro', ascending=False).head(10)
    sns.barplot(x='protein_per_euro', y='name', data=best_protein, ax=ax2, palette='viridis')
    ax2.set_title('Top 10 Best Protein Value', fontsize=16)
    ax2.set_xlabel('Protein (g) per Euro', fontsize=12)
    ax2.set_ylabel('')
    
    # Nutrition bubble chart
    ax3 = fig.add_subplot(gs[1, :])
    filtered_df = df.dropna(subset=['protein', 'carbs', 'fat', 'calories']).sample(min(50, len(df)))
    scatter = ax3.scatter(filtered_df['carbs'], filtered_df['fat'], 
                        s=filtered_df['protein']*20, alpha=0.6, 
                        c=filtered_df['calories'], cmap='plasma')
    ax3.set_title('Nutritional Composition of Products', fontsize=16)
    ax3.set_xlabel('Carbohydrates (g per 100g/ml)', fontsize=12)
    ax3.set_ylabel('Fat (g per 100g/ml)', fontsize=12)
    plt.colorbar(scatter, ax=ax3, label='Calories')
    ax3.grid(alpha=0.3)
    
    # Brand comparison
    ax4 = fig.add_subplot(gs[2, 0])
    brand_stats = df.groupby('brand').agg({
        'calories': 'mean',
        'name': 'count'
    }).reset_index()
    brand_stats = brand_stats[brand_stats['name'] >= 5].sort_values('calories', ascending=False).head(10)
    sns.barplot(x="calories", y="brand", data=brand_stats, ax=ax4, palette='rocket')
    ax4.set_title('Top Brands by Average Calories', fontsize=16)
    ax4.set_xlabel('Average Calories (kcal per 100g/ml)', fontsize=12)
    
    # Allergen analysis
    ax5 = fig.add_subplot(gs[2, 1])
    allergens = []
    for allergen_str in df['allergens'].dropna():
        if allergen_str:
            parts = re.split(r',|;|\s+', allergen_str)
            allergens.extend([a.strip() for a in parts if a.strip()])
    allergen_counts = pd.Series(allergens).value_counts().head(10)
    sns.barplot(x=allergen_counts.values, y=allergen_counts.index, ax=ax5, palette='mako')
    ax5.set_title('Most Common Allergens', fontsize=16)
    ax5.set_xlabel('Number of Products', fontsize=12)
    
    # Sugar content by category
    ax6 = fig.add_subplot(gs[3, :])
    df['category'] = df['name'].str.split().str[:2].str.join(' ')
    sugar_by_category = df.groupby('category').agg({
        'sugars': 'mean',
        'name': 'count'
    }).reset_index()
    sugar_by_category = sugar_by_category[
        (sugar_by_category['name'] >= 3) & 
        sugar_by_category['sugars'].notna()
    ].sort_values('sugars', ascending=False).head(10)
    sns.barplot(x='sugars', y='category', data=sugar_by_category, ax=ax6, palette='YlOrBr')
    ax6.set_title('Top Categories by Average Sugar Content', fontsize=16)
    ax6.set_xlabel('Sugar (g per 100g/ml)', fontsize=12)
    
    plt.tight_layout()
    plt.savefig('product_analysis_dashboard.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    # Load product data
    products = load_product_data()
    
    # Clean and convert data
    df = clean_and_convert_data(products)
    
    # Print some statistics
    print(f"Total products: {len(df)}")
    print(f"Products with calorie information: {df['calories'].notna().sum()}")
    print(f"Products with protein information: {df['protein'].notna().sum()}")    # Download product images for top products
    print("Downloading product images...")
    # Get top products without using drop_duplicates which can fail with unhashable types
    # Use more products for interactive website
    calories_top = df.sort_values('calories', ascending=False).head(20)
    protein_per_euro_top = df.sort_values('protein_per_euro', ascending=False).head(20)
    protein_top = df.sort_values('protein', ascending=False).head(20)
    # Also add products with interesting nutritional profiles
    high_fat = df.sort_values('fat', ascending=False).head(10)
    high_carbs = df.sort_values('carbs', ascending=False).head(10)    # Combine dataframes and identify duplicates by file_id
    all_top = pd.concat([calories_top, protein_per_euro_top, protein_top, high_fat, high_carbs])
    # Make sure we're only using hashable types for drop_duplicates
    top_products = all_top.drop_duplicates(subset=['file_id'])
    
    images = download_all_images(top_products)
    print(f"Downloaded {len(images)} product images")
    
    # Create visualizations
    print("Creating visualizations...")
    create_top_calories_graph(df, images)
    create_protein_price_ratio_graph(df, images)
    create_nutrition_bubble_chart(df, images)
    create_brand_comparison_chart(df)
    create_allergen_analysis_chart(df)
    create_fat_protein_scatter(df, images)
    create_sugar_content_by_category(df)
    create_price_distribution_chart(df)
    create_dashboard(df, images)
    
    # Export data for further analysis
    df.to_csv('product_analysis_data.csv', index=False)
    
    print("Analysis complete! Check the output files in the current directory.")

if __name__ == "__main__":
    main()
