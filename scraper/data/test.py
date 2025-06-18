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
from sklearn.manifold import TSNE
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

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

def combine_json_files():
    # Get the current directory where the script is located
    current_dir = Path(__file__).parent
    products_dir = current_dir / "products"
    output_file = current_dir / "all_products.json"
    
    # List to store all products
    all_products = []
    
    # Read all JSON files from the products directory
    for file_path in products_dir.glob("*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                product = json.load(file)
                # Add the filename as a field
                product['filename'] = file_path.name
                all_products.append(product)
        except json.JSONDecodeError as e:
            print(f"Error reading {file_path}: {e}")
        except Exception as e:
            print(f"Unexpected error with {file_path}: {e}")
    
    # Sort products by name to ensure consistent ordering
    all_products.sort(key=lambda x: x.get('name', ''))
    
    # Write combined data to output file
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump({
                'products': all_products,
                'total_products': len(all_products)
            }, file, indent=2, ensure_ascii=False)
        print(f"Successfully combined {len(all_products)} products into {output_file}")
        return all_products
    except Exception as e:
        print(f"Error writing output file: {e}")
        return None

def load_products_to_df(products_list=None):
    """Convert products list to pandas DataFrame with proper data types"""
    if products_list is None:
        # Load from saved JSON if no list provided
        with open(Path(__file__).parent / "all_products.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
            products_list = data['products']
    
    df = pd.json_normalize(products_list)
    
    # Convert price to numeric
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'].str.replace('€', '').str.replace(',', '.'), errors='coerce')
    
    if 'base_unit_price' in df.columns:
        df['base_unit_price'] = pd.to_numeric(df['base_unit_price'].str.replace('€', '').str.replace(',', '.'), errors='coerce')
    
    # Extract nutrients
    nutrient_names = ['energie kc', 'eiwitten', 'koolhydraten', 'suikers', 'vet', 'verzadigd vet', 'zout']
    
    for nutrient in nutrient_names:
        col_name = f'nutrient_{nutrient.replace(" ", "_")}'
        df[col_name] = df['nutrients'].apply(lambda x: extract_nutrient_value(x, nutrient))
        # Convert to numeric explicitly
        df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
    
    # Convert extracted_at to datetime
    if 'extracted_at' in df.columns:
        df['extracted_at'] = pd.to_datetime(df['extracted_at'])
    
    # Convert allergens and ingredients to lists if they're strings
    if 'allergens' in df.columns:
        df['allergens'] = df['allergens'].apply(lambda x: x.split(',') if isinstance(x, str) and x else [])
    
    if 'ingredients' in df.columns:
        df['ingredients'] = df['ingredients'].apply(lambda x: x.split('\n') if isinstance(x, str) and x else [])
    
    return df

def analyze_protein_per_euro(df):
    """Analyze protein content per euro spent"""
    # Use base_unit_price instead of price for standardized comparison (per kg/L)
    df['protein_per_euro'] = df['nutrient_eiwitten'] / df['base_unit_price']
    # Filter out rows where protein_per_euro is NaN or infinite
    df_protein = df[df['protein_per_euro'].notna() & (df['protein_per_euro'] > 0)]
    top_protein = df_protein.nlargest(20, 'protein_per_euro')[
        ['name', 'price', 'base_unit_price', 'nutrient_eiwitten', 'protein_per_euro']
    ].round(2)
    
    # Create bar plot
    plt.figure(figsize=(15, 8))
    sns.barplot(data=top_protein, x='protein_per_euro', y='name')
    plt.title('Top 20 Protein Sources (g/€)')
    plt.xlabel('Protein (g) per Euro')
    plt.tight_layout()
    plt.savefig('analysis/protein_per_euro.png')
    plt.close()
    
    return top_protein

def analyze_price_distribution(df):
    """Create histogram of product prices"""
    plt.figure(figsize=(12, 6))
    sns.histplot(data=df[df['price'] < df['price'].quantile(0.95)], x='price', bins=50)
    plt.title('Distribution of Product Prices (excluding top 5% outliers)')
    plt.xlabel('Price (€)')
    plt.ylabel('Count')
    plt.tight_layout()
    plt.savefig('analysis/price_distribution.png')
    plt.close()
    
    return df['price'].describe()

def analyze_ingredients(df):
    """Analyze most common ingredients and create wordcloud"""
    # Flatten ingredients lists and clean them
    all_ingredients = []
    for ingredients in df['ingredients'].dropna():
        if isinstance(ingredients, list):
            # Clean and split ingredients
            for ingredient in ingredients:
                # Split on commas and clean each part
                parts = [part.strip().lower() for part in ingredient.split(',')]
                all_ingredients.extend(parts)
    
    # Remove common words and short strings
    stop_words = {'bevat', 'kan', 'bevatten', 'en', 'of', 'het', 'de', 'een', 'met'}
    ingredient_freq = Counter(word for word in all_ingredients 
                            if len(word) > 2 and word not in stop_words)
    
    # Create wordcloud
    wordcloud = WordCloud(width=1600, height=800, background_color='white', 
                         max_words=100, collocations=False).generate_from_frequencies(ingredient_freq)
    
    plt.figure(figsize=(20, 10))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.tight_layout(pad=0)
    plt.savefig('analysis/ingredients_wordcloud.png')
    plt.close()
    
    return pd.DataFrame(ingredient_freq.most_common(30), columns=['Ingredient', 'Frequency'])

def analyze_allergens(df):
    """Analyze allergen distribution"""
    allergen_counts = Counter()
    for allergens in df['allergens'].dropna():
        if isinstance(allergens, list):
            allergen_counts.update([a.strip() for a in allergens])
    
    allergen_df = pd.DataFrame(allergen_counts.most_common(), columns=['Allergen', 'Count'])
    
    # Plot top 15 allergens
    plt.figure(figsize=(12, 6))
    sns.barplot(data=allergen_df.head(15), x='Count', y='Allergen')
    plt.title('Top 15 Most Common Allergens')
    plt.tight_layout()
    plt.savefig('analysis/allergen_distribution.png')
    plt.close()
    
    return allergen_df

def analyze_brands(df):
    """Compare brands on average price and nutrients"""
    # Only include brands with at least 5 products
    brand_counts = df['brand'].value_counts()
    valid_brands = brand_counts[brand_counts >= 5].index
    
    brand_stats = df[df['brand'].isin(valid_brands)].groupby('brand').agg({
        'price': 'mean',
        'base_unit_price': 'mean',
        'nutrient_eiwitten': 'mean',
        'nutrient_suikers': 'mean',
        'nutrient_vet': 'mean'
    }).round(2)
    
    # Create comparative visualizations
    metrics = ['price', 'nutrient_eiwitten', 'nutrient_suikers', 'nutrient_vet']
    fig, axes = plt.subplots(2, 2, figsize=(20, 15))
    
    for i, (metric, ax) in enumerate(zip(metrics, axes.flat)):
        data = brand_stats.sort_values(metric, ascending=False).head(10).reset_index()
        sns.barplot(data=data, x=metric, y='brand', ax=ax)
        ax.set_title(f'Top 10 Brands by {metric}')
    
    plt.tight_layout()
    plt.savefig('analysis/brand_comparison.png')
    plt.close()
    
    return brand_stats.sort_values('price', ascending=False)

def find_extreme_products(df):
    """Find products with extreme values (above 95th percentile)"""
    metrics = ['nutrient_suikers', 'nutrient_zout', 'nutrient_vet']
    extreme_products = {}
    
    fig, axes = plt.subplots(len(metrics), 1, figsize=(15, 5*len(metrics)))
    
    for i, metric in enumerate(metrics):
        # Calculate threshold excluding NaN values
        metric_data = df[metric].dropna()
        threshold = metric_data.quantile(0.95)
        extreme = df[df[metric] > threshold][['name', metric, 'price', 'base_unit_price']].sort_values(metric, ascending=False)
        extreme_products[metric] = extreme
        
        # Create boxplot for non-null values
        sns.boxplot(data=metric_data, ax=axes[i])
        axes[i].set_title(f'Distribution of {metric} (g/100g) with outliers')
    
    plt.tight_layout()
    plt.savefig('analysis/extreme_values.png')
    plt.close()
    
    return extreme_products

def cluster_products(df):
    """Perform PCA and t-SNE on product nutrients"""
    # Select numeric nutrient columns
    nutrient_cols = ['nutrient_eiwitten', 'nutrient_koolhydraten', 'nutrient_vet', 'nutrient_zout']
    X = df[nutrient_cols].dropna()
    
    if len(X) < 10:  # Not enough data points
        return None
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # PCA
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    # Create PCA plot
    pca_df = pd.DataFrame(X_pca, columns=['PC1', 'PC2'])
    pca_df['name'] = df.loc[X.index, 'name']
    pca_df['brand'] = df.loc[X.index, 'brand']
    
    fig = px.scatter(pca_df, x='PC1', y='PC2', 
                    hover_data=['name', 'brand'],
                    title='Product Clustering using PCA')
    fig.write_html('analysis/pca_clustering.html')
    
    # Calculate explained variance
    explained_variance = pd.DataFrame({
        'component': ['PC1', 'PC2'],
        'explained_variance_ratio': pca.explained_variance_ratio_
    })
    
    return explained_variance

def analyze_price_trends(df):
    """Analyze price changes over time for products"""
    if 'extracted_at' not in df.columns:
        return None
        
    # Group by product and date to get price history
    price_history = df.groupby(['name', pd.Grouper(key='extracted_at', freq='D')])['price'].mean().reset_index()
    
    # Find products with significant price changes
    price_changes = price_history.groupby('name').agg({
        'price': ['min', 'max', 'std']
    }).round(2)
    
    price_changes.columns = ['min_price', 'max_price', 'price_std']
    price_changes['price_range'] = price_changes['max_price'] - price_changes['min_price']
    price_changes['price_change_pct'] = ((price_changes['max_price'] - price_changes['min_price']) / 
                                       price_changes['min_price'] * 100).round(1)
    
    # Plot price trends for top 10 products with highest price range
    top_products = price_changes.nlargest(10, 'price_range').index
    plt.figure(figsize=(15, 8))
    
    for product in top_products:
        product_data = price_history[price_history['name'] == product]
        plt.plot(product_data['extracted_at'], product_data['price'], label=product)
    
    plt.title('Price Trends for Products with Largest Price Changes')
    plt.xlabel('Date')
    plt.ylabel('Price (€)')
    plt.xticks(rotation=45)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('analysis/price_trends.png', bbox_inches='tight')
    plt.close()
    
    return price_changes.sort_values('price_range', ascending=False)

def analyze_alcohol_details(df):
    """Detailed analysis of alcoholic beverages"""
    # Convert percentage_alcohol to numeric, handling any formatting issues
    df['alcohol_pct'] = pd.to_numeric(df['percentage_alcohol'].str.replace('%', '').str.replace(',', '.'), errors='coerce')
    
    # For alcoholic beverages, we'll use the actual alcohol content per liter instead of base_unit_price
    # because alcohol is measured differently than regular nutrients.
    # We'll calculate the alcohol content per liter from the percentage and then per euro
    
    # First, calculate alcohol content per liter (10ml alcohol per 100ml of 10% drink)
    df['alcohol_per_liter'] = df['alcohol_pct'] * 10  # ml of pure alcohol per liter
    
    # Calculate alcohol ml per euro based on base_unit_price (for standardized comparison)
    df['alcohol_ml_per_euro'] = df['alcohol_per_liter'] / df['base_unit_price']
    
    # For the actual alcohol content in the package, we also need volume
    # Extract volume from name using regex (looking for patterns like 750ml, 70cl, etc.)
    df['volume_ml'] = df['name'].str.extract(r'(\d+)\s*(?:ml|cl|liter|l)', flags=re.IGNORECASE).astype(float)
    df.loc[df['name'].str.contains('cl', case=False, na=False), 'volume_ml'] *= 10  # Convert cl to ml
    df.loc[df['name'].str.contains('liter|l\s|l$', case=False, na=False), 'volume_ml'] *= 1000  # Convert L to ml
    
    # Set default volume for beers and wines if not specified
    df.loc[(df['alcohol_pct'] <= 15) & (df['volume_ml'].isna()), 'volume_ml'] = 330  # Standard beer bottle
    df.loc[(df['alcohol_pct'] > 15) & (df['alcohol_pct'] <= 25) & (df['volume_ml'].isna()), 'volume_ml'] = 750  # Wine bottle
    df.loc[(df['alcohol_pct'] > 25) & (df['volume_ml'].isna()), 'volume_ml'] = 700  # Spirit bottle
    
    # Calculate total alcohol in package
    df['total_alcohol_ml'] = df['volume_ml'] * df['alcohol_pct'] / 100
    
    # Categorize alcoholic beverages
    def categorize_alcohol(row):
        if pd.isna(row['alcohol_pct']):
            return 'Non-Alcoholic'
        elif row['alcohol_pct'] <= 7:
            return 'Beer'
        elif row['alcohol_pct'] <= 15:
            return 'Wine'
        elif row['alcohol_pct'] <= 25:
            return 'Liqueur'
        else:
            return 'Spirits'
    
    df['alcohol_category'] = df.apply(categorize_alcohol, axis=1)
    
    # Analysis by category
    category_stats = df[df['alcohol_category'] != 'Non-Alcoholic'].groupby('alcohol_category').agg({
        'price': ['mean', 'min', 'max', 'count'],
        'alcohol_pct': ['mean', 'min', 'max'],
        'alcohol_ml_per_euro': ['mean', 'max'],
        'total_alcohol_ml': ['mean']
    }).round(2)
    
    # Best value analysis by category
    best_value = {}
    for category in df['alcohol_category'].unique():
        if category != 'Non-Alcoholic':
            category_df = df[df['alcohol_category'] == category]            
            best_value[category] = category_df.nlargest(5, 'alcohol_ml_per_euro')[
                ['name', 'price', 'base_unit_price', 'alcohol_pct', 'volume_ml', 'alcohol_ml_per_euro']
            ]
    
    # Visualization: Price vs Alcohol Content
    plt.figure(figsize=(12, 8))
    sns.scatterplot(data=df[df['alcohol_category'] != 'Non-Alcoholic'], 
                   x='alcohol_pct', y='price', hue='alcohol_category', alpha=0.6)
    plt.title('Price vs Alcohol Percentage by Category')
    plt.xlabel('Alcohol Percentage')
    plt.ylabel('Price (€)')
    plt.tight_layout()
    plt.savefig('analysis/alcohol_price_correlation.png')
    plt.close()
    
    # Visualization: Value by Category
    plt.figure(figsize=(10, 6))
    category_means = df[df['alcohol_category'] != 'Non-Alcoholic'].groupby('alcohol_category')['alcohol_ml_per_euro'].mean()
    sns.barplot(x=category_means.index, y=category_means.values)
    plt.title('Average Alcohol (ml) per Euro by Category')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('analysis/alcohol_value_by_category.png')
    plt.close()
    
    return category_stats, best_value

def analyze_alcohol_efficiency(df):
    """Analyze alcohol content per euro spent"""
    # Convert percentage_alcohol to numeric, handling any formatting issues
    df['alcohol_pct'] = pd.to_numeric(df['percentage_alcohol'].str.replace('%', '').str.replace(',', '.'), errors='coerce')
    
    # Calculate alcohol content in ml per euro using base_unit_price for standardized comparison
    df['alcohol_ml_per_euro'] = (df['alcohol_pct'] / 100) * 1000 / df['base_unit_price']  # ml of alcohol per euro
    
    # Filter valid entries
    df_alcohol = df[df['alcohol_ml_per_euro'].notna() & (df['alcohol_ml_per_euro'] > 0)]
    
    # Get top 20 most efficient alcohol sources
    top_alcohol = df_alcohol.nlargest(20, 'alcohol_ml_per_euro')[
        ['name', 'price', 'base_unit_price', 'alcohol_pct', 'alcohol_ml_per_euro']
    ].round(2)
    
    # Create visualization
    plt.figure(figsize=(15, 8))
    sns.barplot(data=top_alcohol, x='alcohol_ml_per_euro', y='name')
    plt.title('Top 20 Most Cost-Effective Alcoholic Beverages')
    plt.xlabel('Pure Alcohol (ml) per Euro')
    plt.tight_layout()
    plt.savefig('analysis/alcohol_efficiency.png')
    plt.close()
    
    # Additional alcohol statistics
    alcohol_stats = {
        'total_alcoholic_products': len(df[df['alcohol_pct'].notna() & (df['alcohol_pct'] > 0)]),
        'avg_alcohol_percentage': df['alcohol_pct'].mean(),
        'max_alcohol_percentage': df[['name', 'alcohol_pct']].nlargest(1, 'alcohol_pct'),
        'price_range': df[df['alcohol_pct'].notna()]['price'].describe()
    }
    
    return top_alcohol, alcohol_stats

def analyze_product_categories(df):
    """Analyze products by inferring categories from names"""
    # Define category keywords
    categories = {
        'Alcohol': ['jenever', 'whisky', 'vodka', 'wijn', 'bier', 'rum'],
        'Zuivel': ['kaas', 'melk', 'yoghurt', 'kwark', 'roomboter', 'room'],
        'Vlees': ['worst', 'ham', 'vlees', 'kipfilet', 'gehakt'],
        'Groente': ['sla', 'tomaat', 'komkommer', 'paprika', 'ui'],
        'Fruit': ['appel', 'peer', 'banaan', 'sinaasappel', 'mandarijn'],
        'Drank': ['water', 'sap', 'frisdrank', 'limonade'],
        'Snacks': ['chips', 'koek', 'snoep', 'chocolade', 'noten']
    }
    
    # Categorize products
    def categorize_product(name):
        name = name.lower()
        for category, keywords in categories.items():
            if any(keyword in name for keyword in keywords):
                return category
        return 'Overig'
    
    df['category'] = df['name'].apply(categorize_product)
    
    # Calculate statistics per category
    category_stats = df.groupby('category').agg({
        'price': ['count', 'mean', 'min', 'max'],
        'nutrient_eiwitten': 'mean',
        'nutrient_vet': 'mean',
        'nutrient_suikers': 'mean'
    }).round(2)
    
    # Create visualization
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df, x='category', y='price')
    plt.title('Average Price by Product Category')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('analysis/category_prices.png')
    plt.close()
    
    return category_stats

def analyze_nutritional_correlations(df):
    """Analyze correlations between nutritional values"""
    # Select relevant columns
    nutrient_cols = [col for col in df.columns if col.startswith('nutrient_')]
    
    # Calculate correlation matrix
    corr_matrix = df[nutrient_cols].corr()
    
    # Create heatmap
    plt.figure(figsize=(12, 10))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
    plt.title('Nutrient Correlations')
    plt.tight_layout()
    plt.savefig('analysis/nutrient_correlations.png')
    plt.close()
    
    return corr_matrix

def analyze_calorie_value(df):
    """Analyze calorie content and other metrics per euro spent"""
    # Calculate value metrics using base_unit_price for standardized comparison (per kg/L)
    df['kcal_per_euro'] = df['nutrient_energie_kc'] / df['base_unit_price']
    df['fat_per_euro'] = df['nutrient_vet'] / df['base_unit_price']
    df['carbs_per_euro'] = df['nutrient_koolhydraten'] / df['base_unit_price']
    df['protein_per_euro'] = df['nutrient_eiwitten'] / df['base_unit_price']
    
    # Get top value products for each metric
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
        top = valid_data.nlargest(20, col)[['name', 'price', 'base_unit_price', col]].round(2)
        top_products[metric_name] = top
        
        # Create visualization
        plt.figure(figsize=(15, 8))
        sns.barplot(data=top, x=col, y='name')
        plt.title(f'Top 20 Products by {metric_name} per Euro')
        plt.xlabel(f'{metric_name} ({unit}) per Euro')
        plt.tight_layout()
        plt.savefig(f'analysis/{metric_name.lower()}_value.png')
        plt.close()
    
    # Calculate overall value score (normalized sum of all metrics)
    df['value_score'] = (
        df['kcal_per_euro'] / df['kcal_per_euro'].max() +
        df['fat_per_euro'] / df['fat_per_euro'].max() +
        df['carbs_per_euro'] / df['carbs_per_euro'].max() +
        df['protein_per_euro'] / df['protein_per_euro'].max()
    ) / 4
      # Get top 20 overall value products
    best_value = df.nlargest(20, 'value_score')[['name', 'price', 'base_unit_price', 'value_score', 'kcal_per_euro', 'protein_per_euro', 'fat_per_euro', 'carbs_per_euro']].round(2)
    
    # Calculate calories per euro by category
    category_stats = df.groupby('category').agg({
        'kcal_per_euro': ['mean', 'max'],
        'fat_per_euro': ['mean', 'max'],
        'carbs_per_euro': ['mean', 'max'],
        'protein_per_euro': ['mean', 'max']
    }).round(2)
    
    return top_products, best_value, category_stats

def main():
    # Create analysis directory if it doesn't exist
    Path('analysis').mkdir(exist_ok=True)
    
    # Combine JSON files and load into DataFrame
    products = combine_json_files()
    if products:
        df = load_products_to_df(products)
        
        # Run analyses
        print("\nRunning analyses...")
        
        protein_analysis = analyze_protein_per_euro(df)
        print("\nTop protein sources per euro:")
        print(protein_analysis)
        
        price_stats = analyze_price_distribution(df)
        print("\nPrice distribution statistics:")
        print(price_stats)
        
        ingredient_freq = analyze_ingredients(df)
        print("\nMost common ingredients:")
        print(ingredient_freq)
        
        allergen_dist = analyze_allergens(df)
        print("\nAllergen distribution:")
        print(allergen_dist)
        
        brand_comparison = analyze_brands(df)
        print("\nBrand comparison:")
        print(brand_comparison)
        
        extreme_products = find_extreme_products(df)
        print("\nProducts with extreme nutrient values:")
        for metric, products in extreme_products.items():
            print(f"\n{metric}:")
            print(products.head())
        
        clusters = cluster_products(df)
        if clusters is not None:
            print("\nPCA Explained Variance Ratios:")
            print(clusters)
        
        price_trends = analyze_price_trends(df)
        if price_trends is not None:
            print("\nProducts with largest price changes:")
            print(price_trends.head(10))
          # Basic alcohol analysis
        alcohol_results, alcohol_stats = analyze_alcohol_efficiency(df)
        print("\nMost cost-effective alcoholic beverages:")
        print(alcohol_results)
        print("\nAlcohol statistics:")
        print(f"Total alcoholic products: {alcohol_stats['total_alcoholic_products']}")
        print(f"Average alcohol percentage: {alcohol_stats['avg_alcohol_percentage']:.1f}%")
        print("\nStrongest alcoholic product:")
        print(alcohol_stats['max_alcohol_percentage'])
        
        # Detailed alcohol analysis
        category_stats, best_value = analyze_alcohol_details(df)
        print("\nAlcohol Category Statistics:")
        print(category_stats)
        print("\nBest Value Products by Category:")
        for category, products in best_value.items():
            print(f"\n{category}:")
            print(products)
        
        category_stats = analyze_product_categories(df)
        print("\nProduct category statistics:")
        print(category_stats)
        
        nutrient_corr = analyze_nutritional_correlations(df)
        print("\nNutritional value correlations:")
        print(nutrient_corr)
        
        # New calorie and value analysis
        value_products, best_value, category_value = analyze_calorie_value(df)
        
        print("\nTop Products by Calories per Euro:")
        print(value_products['Calories'])
        
        print("\nTop Products by Fat per Euro:")
        print(value_products['Fat'])
        
        print("\nTop Products by Carbs per Euro:")
        print(value_products['Carbs'])
        
        print("\nBest Overall Value Products (Combined Nutrients):")
        print(best_value)
        
        print("\nNutrient Value by Category:")
        print(category_value)

if __name__ == "__main__":
    main()