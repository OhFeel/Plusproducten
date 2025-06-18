/**
 * main.js - JavaScript for PLUS Product Analyzer
 */

// Set current date in footer
document.getElementById('current-date').textContent = new Date().toLocaleDateString('nl-NL', {
    year: 'numeric', 
    month: 'long', 
    day: 'numeric'
});

// Load data and update all charts
document.addEventListener('DOMContentLoaded', function() {
    // Load general insights
    fetchInsights();
    
    // Load charts
    fetchPriceDistribution();
    fetchBrandDistribution();
    fetchProteinComparison();
    fetchWordcloud();
});

/**
 * Fetch general insights
 */
function fetchInsights() {
    fetch('/api/insights')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                // Show no-data message if there are no products
                if (data.error.includes("No products found")) {
                    document.getElementById('no-data-message').style.display = 'block';
                }
                showError(data.error);
                return;
            }
            
            // Update summary stats
            document.getElementById('product-count').textContent = data.total_products + ' producten';
            document.getElementById('total-products').textContent = data.total_products;
            document.getElementById('total-brands').textContent = data.total_brands;
            document.getElementById('avg-price').textContent = data.avg_price.toFixed(2);
            document.getElementById('min-price').textContent = data.price_range[0].toFixed(2);
            document.getElementById('max-price').textContent = data.price_range[1].toFixed(2);
            
            // Fill in protein products table
            if (data.best_protein_sources) {
                const tbody = document.getElementById('best-protein-tbody');
                tbody.innerHTML = '';
                
                data.best_protein_sources.forEach(product => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${product.name}</td>
                        <td>${product.protein_per_100g.toFixed(1)}</td>
                        <td>€${product.price.toFixed(2)}</td>
                    `;
                    tbody.appendChild(row);
                });
            }
            
            // Fill in protein value products table
            if (data.best_protein_value) {
                const tbody = document.getElementById('best-protein-value-tbody');
                tbody.innerHTML = '';
                
                data.best_protein_value.forEach(product => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${product.name}</td>
                        <td>${product.protein_per_price.toFixed(2)}</td>
                        <td>${product.protein_per_100g.toFixed(1)}</td>
                        <td>€${product.price.toFixed(2)}</td>
                    `;
                    tbody.appendChild(row);
                });
            }
            
            // Fill in cheapest alcohol table
            if (data.cheapest_alcohol) {
                const tbody = document.getElementById('cheapest-alcohol-tbody');
                tbody.innerHTML = '';
                
                data.cheapest_alcohol.forEach(product => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${product.name}</td>
                        <td>€${product.price.toFixed(2)}</td>
                    `;
                    tbody.appendChild(row);
                });
            }
        })
        .catch(error => {
            console.error('Error fetching insights:', error);
            showError('Er is een probleem opgetreden bij het laden van de inzichten.');
        });
}

/**
 * Fetch price distribution
 */
function fetchPriceDistribution() {
    fetch('/api/price_distribution')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('price-distribution').innerHTML = 
                    `<div class="alert alert-warning">Geen prijsgegevens beschikbaar</div>`;
                return;
            }
            
            const chartData = JSON.parse(data.chart);
            Plotly.newPlot('price-distribution', chartData.data, chartData.layout);
        })
        .catch(error => {
            console.error('Error fetching price distribution:', error);
            document.getElementById('price-distribution').innerHTML = 
                `<div class="alert alert-danger">Fout bij laden van prijsverdeling</div>`;
        });
}

/**
 * Fetch brand distribution
 */
function fetchBrandDistribution() {
    fetch('/api/brand_distribution')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('brand-distribution').innerHTML = 
                    `<div class="alert alert-warning">Geen merkinformatie beschikbaar</div>`;
                return;
            }
            
            const chartData = JSON.parse(data.chart);
            Plotly.newPlot('brand-distribution', chartData.data, chartData.layout);
        })
        .catch(error => {
            console.error('Error fetching brand distribution:', error);
            document.getElementById('brand-distribution').innerHTML = 
                `<div class="alert alert-danger">Fout bij laden van merkgegevens</div>`;
        });
}

/**
 * Fetch protein comparison
 */
function fetchProteinComparison() {
    fetch('/api/protein_comparison')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('protein-comparison').innerHTML = 
                    `<div class="alert alert-warning">Geen eiwitgegevens beschikbaar</div>`;
                return;
            }
            
            const chartData = JSON.parse(data.chart);
            Plotly.newPlot('protein-comparison', chartData.data, chartData.layout);
        })
        .catch(error => {
            console.error('Error fetching protein comparison:', error);
            document.getElementById('protein-comparison').innerHTML = 
                `<div class="alert alert-danger">Fout bij laden van eiwitgegevens</div>`;
        });
}

/**
 * Fetch ingredients wordcloud
 */
function fetchWordcloud() {
    fetch('/api/wordcloud')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('ingredients-wordcloud').innerHTML = 
                    `<div class="alert alert-warning">Geen ingrediëntgegevens beschikbaar</div>`;
                return;
            }
            
            // Display the image from base64
            document.getElementById('ingredients-wordcloud').innerHTML = 
                `<img src="${data.image}" class="img-fluid" alt="Ingredients Word Cloud">`;
        })
        .catch(error => {
            console.error('Error fetching wordcloud:', error);
            document.getElementById('ingredients-wordcloud').innerHTML = 
                `<div class="alert alert-danger">Fout bij het genereren van de wordcloud</div>`;
        });
}

/**
 * Show error message
 */
function showError(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show mt-3';
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.querySelector('main').prepend(alertDiv);
}
