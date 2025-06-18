import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from flask import Flask, send_from_directory
import base64
from pathlib import Path
import numpy as np

# Path to product data
PRODUCTS_DIR = Path('products')
IMAGES_DIR = Path('static/images')
CACHE_DIR = Path('static/cache')

# Create necessary directories
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Initialize the Flask app
server = Flask(__name__, static_folder='static')
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[dbc.themes.BOOTSTRAP, 'https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap'],
    title='PLUS Products Analysis',
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

# Load the product data
print("Loading product data...")
df = pd.read_csv('product_analysis_data.csv')

# Process the data for display
def prepare_data():
    # Create a dictionary of products keyed by product ID for quick lookup
    products_dict = {}
    
    print(f"Total products: {len(df)}")
    
    for _, row in df.iterrows():
        try:
            product_id = row['file_id']
            if product_id and isinstance(product_id, str):
                products_dict[product_id] = row.to_dict()
        except Exception as e:
            print(f"Error processing row: {e}")
    
    print(f"Products dictionary prepared with {len(products_dict)} items")
    return products_dict

# Get product details by ID
def get_product_details(product_id):
    # Load product data from the JSON file
    try:
        with open(PRODUCTS_DIR / f"{product_id}.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading product {product_id}: {e}")
        return None

# Create interactive visualizations
def create_top_calories_graph():
    top_calories = df.dropna(subset=['calories']).sort_values('calories', ascending=False).head(15)
    fig = px.bar(
        top_calories, 
        x='calories', 
        y='name',
        color='calories',
        color_continuous_scale='Reds',
        title='Products with Highest Calories (per 100g/ml)',
        labels={'calories': 'Calories (kcal)', 'name': 'Product'},
        hover_data=['brand', 'price', 'calories', 'protein', 'fat', 'carbs', 'image_url', 'file_id'],
        custom_data=['file_id']  # Include file_id for click events
    )
    
    # Add custom hover template with image preview if available
    hover_template = '''
    <div class="custom-tooltip">
        <img src="%{customdata[6]}" onerror="this.style.display='none'" style="max-width:100px; max-height:100px;">
        <b>%{y}</b><br>
        Brand: %{customdata[0]}<br>
        Price: €%{customdata[1]:.2f}<br>
        Calories: %{x:.1f} kcal<br>
        Protein: %{customdata[2]:.1f}g<br>
        Fat: %{customdata[3]:.1f}g<br>
        Carbs: %{customdata[4]:.1f}g<br>
        <i>Click for more details</i>
    </div>
    '''
    
    fig.update_traces(hovertemplate=hover_template)
    
    # Style the graph
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_family='Montserrat',
        height=600
    )
    
    return fig

def create_protein_price_ratio_graph():
    # Filter products with price and protein info
    protein_price_df = df.dropna(subset=['protein', 'price']).copy()
    
    # Calculate protein per euro if not already in the dataframe
    if 'protein_per_euro' not in protein_price_df.columns:
        # Use price directly if price_per_kg_or_l not available
        protein_price_df['protein_per_euro'] = protein_price_df['protein'] / protein_price_df['price'] * 100
    
    # Get top 15 products by protein per euro
    best_protein_deal = protein_price_df.sort_values('protein_per_euro', ascending=False).head(15)
    
    fig = px.bar(
        best_protein_deal, 
        x='protein_per_euro', 
        y='name',
        color='protein_per_euro',
        color_continuous_scale='Greens',
        title='Best Value Protein Sources (g protein per €)',
        labels={'protein_per_euro': 'Protein (g) per €', 'name': 'Product'},
        hover_data=['brand', 'price', 'protein', 'calories', 'image_url', 'file_id'],
        custom_data=['file_id']  # Include file_id for click events
    )
    
    # Add custom hover template with image preview
    hover_template = '''
    <div class="custom-tooltip">
        <img src="%{customdata[4]}" onerror="this.style.display='none'" style="max-width:100px; max-height:100px;">
        <b>%{y}</b><br>
        Brand: %{customdata[0]}<br>
        Price: €%{customdata[1]:.2f}<br>
        Protein: %{customdata[2]:.1f}g<br>
        Calories: %{customdata[3]:.1f} kcal<br>
        Value: %{x:.1f}g protein/€<br>
        <i>Click for more details</i>
    </div>
    '''
    
    fig.update_traces(hovertemplate=hover_template)
    
    # Style the graph
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_family='Montserrat',
        height=600
    )
    
    return fig

def create_nutrition_bubble_chart():
    # Filter out products with missing nutrient data
    nutrition_df = df.dropna(subset=['carbs', 'fat', 'protein']).copy()
    
    # Get a range of products with different nutritional profiles, sample with replacement if needed
    if len(nutrition_df) >= 100:
        # Random sample of 100 products for better visibility
        chart_data = nutrition_df.sample(100)
    else:
        chart_data = nutrition_df
    
    fig = px.scatter(
        chart_data,
        x='carbs',
        y='fat',
        size='protein',
        color='calories',
        color_continuous_scale='Viridis',
        size_max=40,
        hover_name='name',
        title='Nutritional Composition (Carbs vs Fat, size represents Protein)',
        labels={
            'carbs': 'Carbs (g per 100g/ml)',
            'fat': 'Fat (g per 100g/ml)',
            'protein': 'Protein (g)',
            'calories': 'Calories (kcal)'
        },
        hover_data=['brand', 'price', 'image_url', 'protein', 'file_id'],
        custom_data=['file_id']  # Include file_id for click events
    )
    
    # Style the graph
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_family='Montserrat',
        height=600
    )
    
    return fig

def create_brand_comparison_chart():
    # Get brands with at least 5 products
    brand_counts = df['brand'].value_counts()
    popular_brands = brand_counts[brand_counts >= 5].index.tolist()
    
    # Filter for popular brands and calculate average nutritional values
    brand_df = df[df['brand'].isin(popular_brands)].copy()
    brand_summary = brand_df.groupby('brand').agg({
        'calories': 'mean',
        'protein': 'mean',
        'fat': 'mean',
        'carbs': 'mean',
        'name': 'count'
    }).reset_index().rename(columns={'name': 'product_count'})
    
    brand_summary = brand_summary.sort_values('calories', ascending=False).head(15)
    
    fig = px.scatter(
        brand_summary,
        x='calories',
        y='protein',
        size='product_count',
        color='brand',
        hover_name='brand',
        title='Brand Comparison: Average Calories and Protein',
        labels={
            'calories': 'Avg. Calories (kcal per 100g/ml)',
            'protein': 'Avg. Protein (g per 100g/ml)',
            'product_count': 'Number of Products'
        },
        size_max=40
    )
    
    # Style the graph
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_family='Montserrat',
        height=600
    )
    
    return fig

def create_allergen_analysis_chart():
    # Count allergens
    allergen_counts = {}
    
    for allergen in df['allergens'].dropna():
        if isinstance(allergen, str):
            allergens = [a.strip() for a in allergen.split(',')]
            for a in allergens:
                if a and len(a) > 2:  # Filter out empty or very short entries
                    allergen_counts[a] = allergen_counts.get(a, 0) + 1
    
    # Convert to dataframe
    allergen_df = pd.DataFrame([
        {'allergen': allergen, 'count': count}
        for allergen, count in allergen_counts.items()
    ])
    
    if not allergen_df.empty:
        # Get top allergens
        top_allergens = allergen_df.sort_values('count', ascending=False).head(10)
        
        fig = px.bar(
            top_allergens,
            x='count',
            y='allergen',
            orientation='h',
            color='count',
            color_continuous_scale='Reds',
            title='Most Common Allergens',
            labels={'count': 'Number of Products', 'allergen': 'Allergen'}
        )
        
        # Style the graph
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_family='Montserrat',
            height=600,
            yaxis={'categoryorder': 'total ascending'}
        )
        
        return fig
    else:
        # Return an empty figure if no data
        return go.Figure()

def create_fat_protein_scatter():
    # Filter out products with missing data
    plot_df = df.dropna(subset=['fat', 'protein']).copy()
    
    # Create categories for the color coding
    plot_df['protein_to_fat_ratio'] = np.where(
        plot_df['fat'] > 0,
        plot_df['protein'] / plot_df['fat'],
        plot_df['protein']  # Avoid division by zero
    )
    
    # Create category based on the ratio
    conditions = [
        (plot_df['protein_to_fat_ratio'] < 0.5),
        (plot_df['protein_to_fat_ratio'] >= 0.5) & (plot_df['protein_to_fat_ratio'] < 1),
        (plot_df['protein_to_fat_ratio'] >= 1) & (plot_df['protein_to_fat_ratio'] < 2),
        (plot_df['protein_to_fat_ratio'] >= 2)
    ]
    
    values = ['High Fat', 'More Fat than Protein', 'More Protein than Fat', 'High Protein']
    plot_df['category'] = np.select(conditions, values, default='Unknown')
    
    fig = px.scatter(
        plot_df,
        x='fat',
        y='protein',
        color='category',
        color_discrete_map={
            'High Fat': '#fc8d59',
            'More Fat than Protein': '#ffffbf',
            'More Protein than Fat': '#91cf60',
            'High Protein': '#1a9850'
        },
        hover_name='name',
        title='Fat vs Protein Content',
        labels={
            'fat': 'Fat (g per 100g/ml)',
            'protein': 'Protein (g per 100g/ml)',
            'category': 'Category'
        },
        hover_data=['brand', 'calories', 'carbs', 'image_url', 'file_id'],
        custom_data=['file_id']  # Include file_id for click events
    )
    
    # Add diagonal lines to show the ratio boundaries
    max_val = max(plot_df['fat'].max(), plot_df['protein'].max()) + 5
    
    fig.add_shape(
        type="line",
        x0=0, y0=0,
        x1=max_val, y1=max_val * 0.5,
        line=dict(color="gray", dash="dot"),
        name="Fat:Protein = 2:1"
    )
    
    fig.add_shape(
        type="line",
        x0=0, y0=0,
        x1=max_val, y1=max_val,
        line=dict(color="gray", dash="dot"),
        name="Fat:Protein = 1:1"
    )
    
    fig.add_shape(
        type="line",
        x0=0, y0=0,
        x1=max_val, y1=max_val * 2,
        line=dict(color="gray", dash="dot"),
        name="Fat:Protein = 1:2"
    )
    
    # Style the graph
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_family='Montserrat',
        height=600,
        legend_title_text='Protein to Fat Ratio'
    )
    
    return fig

def create_sugar_content_by_category():
    # Get average sugar content by category
    sugar_by_category = df.groupby('category').agg({
        'sugars': 'mean',
        'name': 'count'
    }).reset_index()
    
    # Filter for categories with at least 3 products and valid sugar data
    sugar_by_category = sugar_by_category[
        (sugar_by_category['name'] >= 3) & 
        sugar_by_category['sugars'].notna()
    ].sort_values('sugars', ascending=False).head(10)
    
    fig = px.bar(
        sugar_by_category,
        x='sugars',
        y='category',
        orientation='h',
        color='sugars',
        color_continuous_scale='YlOrBr',
        title='Top Categories by Average Sugar Content',
        labels={'sugars': 'Sugar (g per 100g/ml)', 'category': 'Product Category'}
    )
    
    # Style the graph
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_family='Montserrat',
        height=600
    )
    
    return fig

def create_price_distribution_chart():
    # Filter out extreme outliers for better visualization
    price_df = df[(df['price'] > 0) & (df['price'] < df['price'].quantile(0.99))].copy()
    
    fig = px.histogram(
        price_df,
        x='price',
        nbins=30,
        color_discrete_sequence=['#636EFA'],
        title='Price Distribution of Products',
        labels={'price': 'Price (€)', 'count': 'Number of Products'}
    )
    
    # Add a rug plot at the bottom
    fig.add_trace(
        go.Scatter(
            x=price_df['price'],
            y=[0] * len(price_df),
            mode='markers',
            marker=dict(
                color='rgba(99, 110, 250, 0.5)',
                size=4,
                line=dict(width=0)
            ),
            hoverinfo='none',
            showlegend=False
        )
    )
    
    # Add median line
    median_price = price_df['price'].median()
    fig.add_vline(x=median_price, line_dash='dash', line_color='red', annotation_text=f"Median: €{median_price:.2f}")
    
    # Style the graph
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_family='Montserrat',
        height=500,
        bargap=0.2
    )
    
    return fig

def create_category_breakdown():
    # Count products per category
    category_counts = df['category'].value_counts().reset_index()
    category_counts.columns = ['category', 'count']
    
    # Get the top 10 categories
    top_categories = category_counts.head(10)
    
    fig = px.pie(
        top_categories,
        values='count',
        names='category',
        title='Product Distribution by Category',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    # Style the graph
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_family='Montserrat',
        height=550
    )
    
    return fig

def create_protein_source_comparison():
    # Filter products with protein data
    protein_df = df.dropna(subset=['protein']).copy()
    
    # Create a categorical column for protein source
    protein_df['protein_source'] = 'Other'
    
    # Define protein sources by keywords in the name
    protein_sources = {
        'Dairy': ['melk', 'kaas', 'yoghurt', 'kwark', 'vla', 'roomkaas', 'creme fraiche'],
        'Meat': ['vlees', 'kip', 'rund', 'ham', 'worst', 'bacon', 'spek', 'filet', 'gehakt'],
        'Fish': ['vis', 'zalm', 'tonijn', 'haring', 'kabeljauw'],
        'Plant-based': ['vega', 'soja', 'tofu', 'boon', 'peulvrucht', 'linzen', 'noten', 'pinda']
    }
    
    for source, keywords in protein_sources.items():
        mask = protein_df['name'].str.lower().apply(lambda x: any(keyword in str(x).lower() for keyword in keywords))
        protein_df.loc[mask, 'protein_source'] = source
    
    # Calculate average protein and price per protein source
    source_summary = protein_df.groupby('protein_source').agg({
        'protein': 'mean',
        'price': 'mean',
        'calories': 'mean',
        'name': 'count'
    }).reset_index().rename(columns={'name': 'product_count'})
    
    # Calculate protein per euro
    source_summary['protein_per_euro'] = source_summary['protein'] / source_summary['price'] * 100
    
    # Sort by protein content
    source_summary = source_summary.sort_values('protein', ascending=False)
    
    fig = px.bar(
        source_summary,
        x='protein_source',
        y='protein',
        color='protein_per_euro',
        color_continuous_scale='Viridis',
        title='Average Protein Content by Source',
        labels={
            'protein_source': 'Protein Source',
            'protein': 'Protein (g per 100g/ml)',
            'protein_per_euro': 'Protein (g) per €'
        },
        hover_data=['calories', 'price', 'product_count']
    )
    
    # Add custom hover template
    fig.update_traces(
        hovertemplate='<b>%{x}</b><br>Protein: %{y:.1f}g<br>Calories: %{customdata[0]:.1f} kcal<br>Price: €%{customdata[1]:.2f}<br>Products: %{customdata[2]}<br>Protein per €: %{marker.color:.1f}g'
    )
    
    # Add a secondary y-axis for price
    fig.add_trace(
        go.Scatter(
            x=source_summary['protein_source'],
            y=source_summary['price'],
            mode='markers',
            marker=dict(
                symbol='diamond',
                size=10,
                color='red'
            ),
            name='Average Price (€)',
            yaxis='y2'
        )
    )
    
    # Style the graph
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_family='Montserrat',
        height=550,
        yaxis2=dict(
            title='Price (€)',
            overlaying='y',
            side='right'
        )
    )
    
    return fig

# Products table for detailed investigation
def create_products_table():
    if len(df) > 1000:
        # Sample 1000 rows for performance
        table_data = df.sample(1000)
    else:
        table_data = df.copy()
    
    # Select relevant columns
    cols = ['name', 'brand', 'price', 'calories', 'protein', 'carbs', 'fat', 'sugars', 'file_id']
    table_data = table_data[cols].dropna(subset=['name'])
    
    return table_data.to_dict('records')

# Define the app layout
products_dict = prepare_data()

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Img(src='/static/logo.png', 
                         style={'height': '80px', 'margin-right': '20px'}),
                html.H1("PLUS Product Analyzer", 
                        style={'display': 'inline-block', 'vertical-align': 'middle'})
            ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '20px'}),
            html.H4("Interactive Nutritional Analysis Dashboard", 
                    className="text-muted"),
            html.Hr(),
            
            # Introduction
            dbc.Card(
                dbc.CardBody([
                    html.H4("About This Dashboard", className="card-title"),
                    html.P(
                        "This interactive dashboard analyzes product data from PLUS supermarket to provide "
                        "insights into nutritional content, price comparison, and more. Hover over any data point "
                        "to see detailed product information.",
                        className="card-text"
                    ),
                    dbc.Button("View Source Code", color="primary", outline=True, href="#", className="mt-2"),
                ]),
                className="mb-4"
            ),
            
            # Product Statistics Summary
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        html.H5("Products Analyzed", className="card-title text-center mb-0"),
                        html.H2(f"{len(df):,}", className="text-center text-primary")
                    ], body=True)
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        html.H5("Average Price", className="card-title text-center mb-0"),
                        html.H2(f"€{df['price'].mean():.2f}", className="text-center text-success")
                    ], body=True)
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        html.H5("Average Calories", className="card-title text-center mb-0"),
                        html.H2(f"{df['calories'].mean():.0f} kcal", className="text-center text-danger")
                    ], body=True)
                ], width=4),
            ], className="mb-4"),
            
            # Main navigation menu
            dbc.Card([
                dbc.CardHeader("Explore Analytics"),
                dbc.CardBody([
                    dbc.Nav(
                        [
                            dbc.NavItem(dbc.NavLink("Top Calorie Products", href="#calories", active=True, id="calories-link")),
                            dbc.NavItem(dbc.NavLink("Best Protein Value", href="#protein", id="protein-link")),
                            dbc.NavItem(dbc.NavLink("Nutritional Composition", href="#nutrition", id="nutrition-link")),
                            dbc.NavItem(dbc.NavLink("Brand Comparison", href="#brands", id="brands-link")),                            dbc.NavItem(dbc.NavLink("Protein Sources", href="#protein-sources", id="protein-sources-link")),                            dbc.NavItem(dbc.NavLink("Sugar Content", href="#sugar", id="sugar-link")),
                            dbc.NavItem(dbc.NavLink("Product Gallery", href="#gallery", id="gallery-link")),
                            dbc.NavItem(dbc.NavLink("Product Comparison", href="#comparison", id="comparison-link")),
                            dbc.NavItem(dbc.NavLink("Product Search", href="#search", id="search-link")),
                        ],
                        pills=True,
                        vertical=True
                    ),
                ]),
            ], className="mb-4"),
            
            # Legend/Guide
            dbc.Card([
                dbc.CardHeader("Guide"),
                dbc.CardBody([
                    html.P("🔍 Hover over data points to see product details"),
                    html.P("📊 Click and drag on charts to zoom in"),
                    html.P("🔄 Double-click to reset the view"),
                    html.P("📱 All charts are mobile-friendly")
                ]),
            ]),
            
        ], md=3, className="sidebar"),
        
        dbc.Col([
            # Main content area
            html.Div(id="main-content", children=[
                # First section: Top Calories
                html.Div([
                    html.H3("Top Calorie Products", id="calories"),
                    html.P("These products contain the highest number of calories per 100g/ml"),
                    dcc.Graph(
                        id="top-calories-graph",
                        figure=create_top_calories_graph(),
                        config={'responsive': True}
                    ),
                ], className="mb-5"),
                
                # Second section: Protein Value
                html.Div([
                    html.H3("Best Protein Value", id="protein"),
                    html.P("Products offering the most protein per euro spent"),
                    dcc.Graph(
                        id="protein-price-graph",
                        figure=create_protein_price_ratio_graph(),
                        config={'responsive': True}
                    ),
                ], className="mb-5"),
                
                # Third section: Nutritional Composition
                html.Div([
                    html.H3("Nutritional Composition", id="nutrition"),
                    html.P("Explore the relationship between carbohydrates, fat, and protein"),
                    dcc.Graph(
                        id="nutrition-bubble-chart",
                        figure=create_nutrition_bubble_chart(),
                        config={'responsive': True}
                    ),
                ], className="mb-5"),
                
                # Fourth section: Brand Comparison
                html.Div([
                    html.H3("Brand Comparison", id="brands"),
                    html.P("Compare different brands based on average calorie and protein content"),
                    dcc.Graph(
                        id="brand-comparison-chart",
                        figure=create_brand_comparison_chart(),
                        config={'responsive': True}
                    ),
                ], className="mb-5"),
                
                # Additional sections
                html.Div([
                    html.H3("Protein Source Comparison", id="protein-sources"),
                    html.P("Compare protein content across different food sources"),
                    dcc.Graph(
                        id="protein-source-comparison",
                        figure=create_protein_source_comparison(),
                        config={'responsive': True}
                    ),
                ], className="mb-5"),
                
                # Two column layout for smaller charts
                dbc.Row([
                    dbc.Col([
                        html.H3("Common Allergens"),
                        html.P("Most frequently listed allergens in products"),
                        dcc.Graph(
                            id="allergen-analysis-chart",
                            figure=create_allergen_analysis_chart(),
                            config={'responsive': True}
                        ),
                    ], md=6),
                    dbc.Col([
                        html.H3("Category Breakdown"),
                        html.P("Distribution of products by category"),
                        dcc.Graph(
                            id="category-breakdown-chart",
                            figure=create_category_breakdown(),
                            config={'responsive': True}
                        ),
                    ], md=6),
                ], className="mb-5"),
                
                # Additional charts
                dbc.Row([
                    dbc.Col([
                        html.H3("Fat vs Protein Analysis"),
                        html.P("Relationship between fat and protein content"),
                        dcc.Graph(
                            id="fat-protein-scatter",
                            figure=create_fat_protein_scatter(),
                            config={'responsive': True}
                        ),
                    ], md=6),
                    dbc.Col([
                        html.H3("Sugar Content by Category", id="sugar"),
                        html.P("Product categories with the highest average sugar content"),
                        dcc.Graph(
                            id="sugar-content-chart",
                            figure=create_sugar_content_by_category(),
                            config={'responsive': True}
                        ),
                    ], md=6),
                ], className="mb-5"),
                
                html.Div([
                    html.H3("Price Distribution"),
                    html.P("Distribution of product prices"),
                    dcc.Graph(
                        id="price-distribution-chart",
                        figure=create_price_distribution_chart(),
                        config={'responsive': True}
                    ),
                ], className="mb-5"),
                  # Product Gallery Section
                html.Div([
                    html.H3("Product Gallery", id="gallery"),
                    html.P("Visual showcase of products with their images"),
                    html.Div([
                        dbc.Card([
                            dbc.CardHeader("Filter Gallery"),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Sort by:"),
                                        dbc.Select(
                                            id="gallery-sort",
                                            options=[
                                                {"label": "Highest Calories", "value": "calories-desc"},
                                                {"label": "Highest Protein", "value": "protein-desc"},
                                                {"label": "Best Protein Value", "value": "protein_per_euro-desc"},
                                                {"label": "Lowest Price", "value": "price-asc"},
                                                {"label": "Highest Fat", "value": "fat-desc"}
                                            ],
                                            value="calories-desc"
                                        ),
                                    ], md=4),
                                    dbc.Col([
                                        html.Label("Category:"),
                                        dbc.Select(
                                            id="gallery-category",
                                            options=[{"label": "All Categories", "value": "all"}],
                                            value="all"
                                        ),
                                    ], md=4),
                                    dbc.Col([
                                        html.Label("Items to show:"),
                                        dbc.Select(
                                            id="gallery-limit",
                                            options=[
                                                {"label": "10 items", "value": "10"},
                                                {"label": "20 items", "value": "20"},
                                                {"label": "30 items", "value": "30"}
                                            ],
                                            value="20"
                                        ),
                                    ], md=4)
                                ])
                            ])
                        ], className="mb-3"),
                        html.Div(id="product-gallery", className="product-gallery mb-4")
                    ])
                ], className="mb-5"),
                  # Product Comparison Tool
                html.Div([
                    html.H3("Product Comparison Tool", id="comparison"),
                    html.P("Compare nutritional values between different products"),
                    dbc.Card([
                        dbc.CardHeader("Select Products to Compare"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Product 1:"),
                                    dcc.Dropdown(
                                        id="comparison-product-1",
                                        options=[],
                                        placeholder="Type to search for a product...",
                                        value=None
                                    ),
                                ], md=6),
                                dbc.Col([
                                    html.Label("Product 2:"),
                                    dcc.Dropdown(
                                        id="comparison-product-2",
                                        options=[],
                                        placeholder="Type to search for a product...",
                                        value=None
                                    ),
                                ], md=6),
                            ]),
                            html.Div([
                                dbc.Button("Compare Products", 
                                          id="compare-button", 
                                          color="primary", 
                                          className="mt-3"),
                                dbc.Button("Reset Comparison", 
                                          id="reset-comparison-button", 
                                          color="secondary", 
                                          className="mt-3 ms-2"),
                            ]),
                        ])
                    ], className="mb-4"),
                    html.Div(id="comparison-results")
                ], className="mb-5"),

                # Product search section
                html.Div([
                    html.H3("Product Search", id="search"),
                    html.P("Search for specific products in the database"),
                    dbc.InputGroup([
                        dbc.Input(id="search-input", placeholder="Enter product name, brand, or ingredients...", type="text"),
                        dbc.InputGroupText(html.I(className="fas fa-search")),
                    ], className="mb-3"),
                    html.Div(id="search-results")
                ], className="mb-5"),
            ]),
        ], md=9),
    ]),
      # Footer
    html.Footer([
        html.Hr(),
        html.P([
            "© 2025 PLUS Product Analyzer Dashboard | Created with ",
            html.A("Dash", href="https://plotly.com/dash/", target="_blank"),
            " | Product data from PLUS supermarket"
        ], className="text-center text-muted"),
    ]),
    
    # Product details modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="product-modal-title")),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col([
                    html.Img(id="product-modal-image", className="img-fluid mb-3", style={"max-height": "200px"})
                ], width=4),
                dbc.Col([
                    html.H5("Nutritional Information", className="mb-3"),
                    html.Div(id="product-modal-nutrition"),
                ], width=8),
            ]),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.H5("Ingredients"),
                    html.P(id="product-modal-ingredients", className="small"),
                ]),
            ]),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.H5("Allergens"),
                    html.P(id="product-modal-allergens"),
                ], width=6),
                dbc.Col([
                    html.H5("Price Information"),
                    html.P(id="product-modal-price"),
                ], width=6),
            ]),
        ]),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-product-modal", className="ms-auto", n_clicks=0)
        ),
    ], id="product-details-modal", size="lg"),
], fluid=True, className="dbc", style={'font-family': 'Montserrat, sans-serif'})

# Define callback for search functionality
@app.callback(
    Output("search-results", "children"),
    Input("search-input", "value")
)
def update_search_results(search_term):
    if not search_term or len(search_term) < 3:
        return html.P("Enter at least 3 characters to search", className="text-muted")
    
    # Search in product names and brands
    search_term = search_term.lower()
    
    # Filter dataframe for matching products
    matching_df = df[
        df['name'].str.lower().str.contains(search_term, na=False) |
        df['brand'].str.lower().str.contains(search_term, na=False) |
        df['ingredients'].str.lower().str.contains(search_term, na=False)
    ].head(20)  # Limit to 20 results
    
    if len(matching_df) == 0:
        return html.P("No products found matching your search", className="text-muted")
    
    # Create cards for each product
    product_cards = []
    
    for _, product in matching_df.iterrows():
        # Create a card for each product
        card_content = [
            dbc.CardHeader(product['name']),
            dbc.CardBody([
                html.H5(product['brand'], className="card-title"),
                html.P([
                    f"Price: €{product['price']:.2f}",
                    html.Br(),
                    f"Calories: {product['calories']:.0f} kcal per 100g/ml",
                    html.Br(),
                    f"Protein: {product['protein']:.1f}g | Fat: {product['fat']:.1f}g | Carbs: {product['carbs']:.1f}g"
                ], className="card-text"),
                dbc.Button(
                    "Product Details",
                    id={"type": "product-button", "index": product['file_id']},
                    color="primary",
                    size="sm",
                    className="mt-2"
                ),
            ]),
        ]
        
        # Add product image if available
        if pd.notna(product['image_url']):
            card_img = html.Img(
                src=product['image_url'],
                className="card-img-top p-3",
                style={"height": "150px", "object-fit": "contain"}
            )
            card_content.insert(1, card_img)
        
        product_cards.append(
            dbc.Col(
                dbc.Card(card_content, className="h-100 product-card"),
                lg=4, md=6, className="mb-4"
            )
        )
    
    # Arrange cards in rows
    card_rows = []
    for i in range(0, len(product_cards), 3):
        row = dbc.Row(product_cards[i:i+3], className="mb-4")
        card_rows.append(row)
    
    return card_rows

# Callback to update the gallery section
@app.callback(
    Output("product-gallery", "children"),
    [
        Input("gallery-sort", "value"),
        Input("gallery-category", "value"),
        Input("gallery-limit", "value"),
    ]
)
def update_product_gallery(sort_by, category, limit):
    # Parse sorting options
    if sort_by:
        col, direction = sort_by.split('-')
        ascending = direction == 'asc'
    else:
        col, ascending = 'calories', False  # Default to calories descending
    
    # Filter by category if needed
    if category and category != "all":
        filtered_df = df[df['category'] == category]
    else:
        filtered_df = df
    
    # Filter products with images and necessary data
    filtered_df = filtered_df.dropna(subset=[col, 'name', 'brand'])
    filtered_df = filtered_df[filtered_df['image_url'].notna()]
    
    # Sort and limit
    try:
        limit_val = int(limit) if limit else 20
        sorted_df = filtered_df.sort_values(by=col, ascending=ascending).head(limit_val)
    except Exception as e:
        print(f"Error sorting products: {e}")
        sorted_df = filtered_df.head(20)
    
    # Create gallery items
    gallery_items = []
    
    for _, product in sorted_df.iterrows():
        try:
            # Get product data
            name = product['name']
            brand = product['brand'] if pd.notna(product['brand']) else ""
            price = product['price'] if pd.notna(product['price']) else 0.0
            image_url = product['image_url']
            metric_value = product[col] if pd.notna(product[col]) else 0
            metric_label = {
                'calories': 'calories',
                'protein': 'g protein',
                'fat': 'g fat',
                'carbs': 'g carbs',
                'price': '€',
                'protein_per_euro': 'g protein/€'
            }.get(col, '')
            
            # Create gallery item
            gallery_item = dbc.Card([
                html.Img(src=image_url, className="card-img-top p-3", 
                         style={"height": "200px", "object-fit": "contain"}),
                dbc.CardBody([
                    html.H6(f"{name}", className="card-title text-truncate", 
                            title=name, style={"font-size": "0.9rem"}),
                    html.P([
                        html.Span(f"{brand}", className="text-muted"),
                        html.Br(),
                        f"€{price:.2f} | ", 
                        html.Strong(f"{metric_value:.1f} {metric_label}")
                    ], className="card-text small"),
                    dbc.Button(
                        "Details",
                        id={"type": "gallery-product-btn", "index": product['file_id']},
                        color="primary",
                        size="sm",
                        className="w-100"
                    ),
                ]),
            ], className="product-gallery-item")
            
            gallery_items.append(gallery_item)
            
        except Exception as e:
            print(f"Error creating gallery item: {e}")
            continue
    
    if not gallery_items:
        return html.P("No products with images found matching your criteria.", className="text-muted")
    
    return gallery_items

# Callback to populate category dropdown
@app.callback(
    Output("gallery-category", "options"),
    Input("gallery-sort", "value")  # This is just a trigger, we don't actually use the value
)
def update_category_options(_):
    # Get all categories that have at least one product
    categories = df['category'].dropna().unique()
    options = [{"label": "All Categories", "value": "all"}]
    options.extend([{"label": cat, "value": cat} for cat in sorted(categories) if cat])
    return options

# Callback for opening the product details modal
@app.callback(
    [
        Output("product-details-modal", "is_open"),
        Output("product-modal-title", "children"),
        Output("product-modal-image", "src"),
        Output("product-modal-nutrition", "children"),
        Output("product-modal-ingredients", "children"),
        Output("product-modal-allergens", "children"),
        Output("product-modal-price", "children"),
    ],
    [
        Input({"type": "product-button", "index": dash.dependencies.ALL}, "n_clicks"),
        Input({"type": "gallery-product-btn", "index": dash.dependencies.ALL}, "n_clicks"),
        Input("close-product-modal", "n_clicks"),
        Input("top-calories-graph", "clickData"),
        Input("protein-price-graph", "clickData"),
        Input("nutrition-bubble-chart", "clickData"),
        Input("fat-protein-scatter", "clickData")
    ],
    [dash.dependencies.State("product-details-modal", "is_open")]
)
def toggle_product_modal(product_clicks, gallery_clicks, close_clicks, calories_click, protein_click, nutrition_click, fat_protein_click, is_open):
    ctx = dash.callback_context
    
    # Default return values
    default_return = (
        False,
        "",
        "",
        "No nutritional information available.",
        "No ingredients information available.",
        "No allergen information available.",
        "No price information available."
    )
    
    if not ctx.triggered:
        return default_return
    
    # Get the id of the component that triggered the callback
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    trigger_prop = ctx.triggered[0]["prop_id"].split(".")[1]
    
    # Close button was clicked
    if trigger_id == "close-product-modal":
        return False, "", "", "", "", "", ""
    
    # Handle clicks on charts
    product_id = None
    
    # Check if a chart was clicked
    if trigger_prop == "clickData":
        click_data = None
        
        if trigger_id == "top-calories-graph" and calories_click:
            click_data = calories_click
        elif trigger_id == "protein-price-graph" and protein_click:
            click_data = protein_click
        elif trigger_id == "nutrition-bubble-chart" and nutrition_click:
            click_data = nutrition_click
        elif trigger_id == "fat-protein-scatter" and fat_protein_click:
            click_data = fat_protein_click
            
        # Extract product ID from click data if available
        if click_data and "points" in click_data and len(click_data["points"]) > 0:
            point = click_data["points"][0]
            if "customdata" in point and len(point["customdata"]) > 0:
                product_id = point["customdata"][0]    # A product button was clicked - either from search results or gallery
    elif trigger_id.startswith("{"):
        try:
            button_id = json.loads(trigger_id)
            if button_id["type"] == "product-button" or button_id["type"] == "gallery-product-btn":
                product_id = button_id["index"]
        except Exception as e:
            print(f"Error parsing button ID: {e}")
            pass
            
            # Get the product from the dataframe
            product_row = df[df['file_id'] == product_id].iloc[0]
            
            # Get the product details
            name = product_row['name']
            brand = product_row['brand']
            image_url = product_row['image_url'] if pd.notna(product_row['image_url']) else ""
            
            # Prepare nutrition information as a table
            nutrition_rows = []
            
            if pd.notna(product_row['calories']):
                nutrition_rows.append(html.Tr([
                    html.Td("Calories"),
                    html.Td(f"{product_row['calories']:.1f} kcal")
                ]))
            
            if pd.notna(product_row['protein']):
                nutrition_rows.append(html.Tr([
                    html.Td("Protein"),
                    html.Td(f"{product_row['protein']:.1f} g")
                ]))
            
            if pd.notna(product_row['fat']):
                nutrition_rows.append(html.Tr([
                    html.Td("Fat"),
                    html.Td(f"{product_row['fat']:.1f} g")
                ]))
                
            if pd.notna(product_row['carbs']):
                nutrition_rows.append(html.Tr([
                    html.Td("Carbohydrates"),
                    html.Td(f"{product_row['carbs']:.1f} g")
                ]))
                
            if pd.notna(product_row['sugars']):
                nutrition_rows.append(html.Tr([
                    html.Td("- of which Sugars"),
                    html.Td(f"{product_row['sugars']:.1f} g")
                ]))
                
            if pd.notna(product_row['salt']):
                nutrition_rows.append(html.Tr([
                    html.Td("Salt"),
                    html.Td(f"{product_row['salt']:.2f} g")
                ]))
            
            # Create nutrition table
            nutrition_table = dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Nutrient"), 
                    html.Th("Per 100g/ml")
                ])),
                html.Tbody(nutrition_rows)
            ], bordered=False, size="sm", striped=True)
            
            # Prepare ingredients
            ingredients = product_row['ingredients'] if pd.notna(product_row['ingredients']) else "No ingredients listed"
            
            # Prepare allergens
            allergens = product_row['allergens'] if pd.notna(product_row['allergens']) else "No allergens listed"
            
            # Prepare price information
            price_info = [
                f"Price: €{product_row['price']:.2f}",
                html.Br(),
            ]
            
            if pd.notna(product_row['price_per_kg_or_l']):
                price_info.extend([
                    f"Unit price: €{product_row['price_per_kg_or_l']:.2f} per kg/L",
                    html.Br()
                ])
            
            # Return product details
            return (
                True,
                f"{name} ({brand})",
                image_url,
                nutrition_table,
                ingredients,
                allergens,
                price_info
            )
        except Exception as e:
            print(f"Error displaying product details: {e}")
            return default_return
    
    return default_return

# Callback to populate product comparison dropdowns
@app.callback(
    [
        Output("comparison-product-1", "options"),
        Output("comparison-product-2", "options")
    ],
    [
        Input("comparison-product-1", "search_value"),
        Input("comparison-product-2", "search_value")
    ]
)
def update_comparison_options(search_value_1, search_value_2):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    search_value = search_value_1 if triggered_id == "comparison-product-1" else search_value_2
    
    if not search_value or len(search_value) < 3:
        return [[{"label": "Type at least 3 characters...", "value": "placeholder", "disabled": True}],
                [{"label": "Type at least 3 characters...", "value": "placeholder", "disabled": True}]]
    
    search_value = search_value.lower()
    matching_products = df[
        df['name'].str.lower().str.contains(search_value, na=False) |
        df['brand'].str.lower().str.contains(search_value, na=False)
    ]
    
    # Prepare options with both name and brand
    options = [
        {
            "label": f"{row['name']} ({row['brand']})",
            "value": row['file_id']
        }
        for _, row in matching_products.head(50).iterrows()
        if pd.notna(row['name']) and pd.notna(row['file_id'])
    ]
    
    if not options:
        options = [{"label": "No products found", "value": "placeholder", "disabled": True}]
        
    # Return the same options for both dropdowns
    return options, options

# Callback to show the comparison results
@app.callback(
    Output("comparison-results", "children"),
    [
        Input("compare-button", "n_clicks"),
        Input("reset-comparison-button", "n_clicks")
    ],
    [
        dash.dependencies.State("comparison-product-1", "value"),
        dash.dependencies.State("comparison-product-2", "value")
    ]
)
def display_comparison(compare_clicks, reset_clicks, product_id_1, product_id_2):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    # Handle reset button
    if triggered_id == "reset-comparison-button":
        return html.P("Select products above to compare", className="text-muted mt-3")
    
    # Check if both products are selected
    if not product_id_1 or not product_id_2 or product_id_1 == "placeholder" or product_id_2 == "placeholder":
        return html.P("Please select two products to compare", className="text-muted mt-3")
    
    # Get product data
    try:
        product1 = df[df['file_id'] == product_id_1].iloc[0].to_dict()
        product2 = df[df['file_id'] == product_id_2].iloc[0].to_dict()
        
        # Create comparison table
        comparison_rows = []
        
        # Add rows for product details
        comparison_rows.append(
            html.Tr([
                html.Th("Product"),
                html.Td(html.Strong(product1['name'])),
                html.Td(html.Strong(product2['name'])),
            ])
        )
        
        comparison_rows.append(
            html.Tr([
                html.Th("Brand"),
                html.Td(product1['brand'] if pd.notna(product1['brand']) else "-"),
                html.Td(product2['brand'] if pd.notna(product2['brand']) else "-"),
            ])
        )
        
        comparison_rows.append(
            html.Tr([
                html.Th("Price"),
                html.Td(f"€{product1['price']:.2f}" if pd.notna(product1['price']) else "-"),
                html.Td(f"€{product2['price']:.2f}" if pd.notna(product2['price']) else "-"),
            ])
        )
        
        # Nutritional comparisons with color-coding for differences
        nutrients = [
            ('calories', 'Calories (kcal)'), 
            ('protein', 'Protein (g)'), 
            ('fat', 'Fat (g)'), 
            ('carbs', 'Carbs (g)'), 
            ('sugars', 'Sugars (g)'), 
            ('salt', 'Salt (g)')
        ]
        
        for nutrient_code, nutrient_name in nutrients:
            # Skip if both products don't have this nutrient data
            if (pd.isna(product1.get(nutrient_code)) or product1.get(nutrient_code) is None) and \
               (pd.isna(product2.get(nutrient_code)) or product2.get(nutrient_code) is None):
                continue
            
            val1 = product1.get(nutrient_code, None) if pd.notna(product1.get(nutrient_code)) else "-"
            val2 = product2.get(nutrient_code, None) if pd.notna(product2.get(nutrient_code)) else "-"
            
            # Determine which value is better (lower is better except for protein)
            better_is_higher = nutrient_code == 'protein'
            
            # Only compare if both are numbers
            style1 = {}
            style2 = {}
            
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                if better_is_higher:
                    if val1 > val2 * 1.1:  # 10% better
                        style1 = {"backgroundColor": "#d4edda", "fontWeight": "bold"}  # Green
                    elif val2 > val1 * 1.1:
                        style2 = {"backgroundColor": "#d4edda", "fontWeight": "bold"}
                else:
                    if val1 * 1.1 < val2:  # 10% better
                        style1 = {"backgroundColor": "#d4edda", "fontWeight": "bold"}
                    elif val2 * 1.1 < val1:
                        style2 = {"backgroundColor": "#d4edda", "fontWeight": "bold"}
            
            # Format numeric values
            if isinstance(val1, (int, float)):
                val1 = f"{val1:.1f}"
            if isinstance(val2, (int, float)):
                val2 = f"{val2:.1f}"
            
            comparison_rows.append(
                html.Tr([
                    html.Th(nutrient_name),
                    html.Td(val1, style=style1),
                    html.Td(val2, style=style2),
                ])
            )
        
        # Create the comparison table
        comparison_table = dbc.Table(
            [html.Tbody(comparison_rows)],
            bordered=True,
            striped=True,
            hover=True,
            responsive=True,
            className="comparison-table"
        )
        
        # Get product images
        img1 = html.Img(
            src=product1['image_url'] if pd.notna(product1['image_url']) else "",
            className="img-fluid",
            style={"maxHeight": "150px", "objectFit": "contain"}
        ) if pd.notna(product1.get('image_url')) else html.Div("No image available")
        
        img2 = html.Img(
            src=product2['image_url'] if pd.notna(product2['image_url']) else "",
            className="img-fluid",
            style={"maxHeight": "150px", "objectFit": "contain"}
        ) if pd.notna(product2.get('image_url')) else html.Div("No image available")
        
        # Create a radar chart for the comparison
        radar_data = []
        
        # Define nutrients for radar chart
        radar_nutrients = ['calories', 'protein', 'fat', 'carbs', 'sugars']
        
        # Normalize each nutrient to a 0-10 scale
        # Higher is better for protein, lower is better for others
        max_vals = {
            'calories': 500,  # Assuming most products are below 500 kcal
            'protein': 30,    # Assuming most products are below 30g protein
            'fat': 40,        # Assuming most products are below 40g fat
            'carbs': 60,      # Assuming most products are below 60g carbs
            'sugars': 30      # Assuming most products are below 30g sugars
        }
        
        # Prepare data for radar chart
        for product, name, color in [(product1, product1['name'], '#007bff'), 
                                     (product2, product2['name'], '#28a745')]:
            # Calculate normalized values (0-10 scale)
            values = []
            for nutrient in radar_nutrients:
                if pd.notna(product.get(nutrient)) and product.get(nutrient) is not None:
                    if nutrient == 'protein':
                        # For protein, higher is better
                        val = min(10, (product[nutrient] / max_vals[nutrient]) * 10)
                    else:
                        # For others, lower is better
                        val = max(0, 10 - (product[nutrient] / max_vals[nutrient]) * 10)
                    values.append(val)
                else:
                    values.append(0)
            
            radar_data.append(
                go.Scatterpolar(
                    r=values,
                    theta=[n.capitalize() for n in radar_nutrients],
                    fill='toself',
                    name=name,
                    line_color=color
                )
            )
        
        # Create radar chart
        radar_layout = go.Layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )
            ),
            showlegend=True,
            title="Nutritional Comparison (Higher is Better)"
        )
        
        radar_fig = go.Figure(data=radar_data, layout=radar_layout)
        radar_chart = dcc.Graph(figure=radar_fig, config={'responsive': True})
        
        # Return the complete comparison
        return html.Div([
            dbc.Card([
                dbc.CardHeader("Nutritional Comparison"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.H5("Product Images", className="mb-3"),
                                dbc.Row([
                                    dbc.Col(img1, className="text-center"),
                                    dbc.Col(img2, className="text-center")
                                ])
                            ], className="mb-4")
                        ], md=12),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.H5("Detailed Comparison", className="mb-3"),
                            comparison_table,
                            html.Div(className="text-muted mt-2", children=[
                                html.Small("Highlighted values indicate a significantly better nutritional profile for that metric.")
                            ])
                        ], md=6),
                        dbc.Col([
                            html.H5("Nutritional Profile", className="mb-3"),
                            radar_chart
                        ], md=6)
                    ])
                ])
            ])
        ])
    
    except Exception as e:
        print(f"Error creating comparison: {e}")
        return html.Div([
            html.P(f"Error creating comparison: {e}", className="text-danger"),
            html.P("Please try selecting different products.")
        ])

# Run the server
if __name__ == '__main__':
    app.run_server(debug=True)
