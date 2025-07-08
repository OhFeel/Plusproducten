# PLUS Product Scraper

Een schaalbare scraper voor het verzamelen van productinformatie van PLUS.nl, inclusief voedingswaarden.

## Functionaliteiten

- **Sitemap Crawler**: Parset sitemap van PLUS.nl om alle product-URL's te verzamelen
- **Product Scraper**: Haalt gedetailleerde productinformatie op via de PLUS API
- **JSON Database**: Opslag van gegevens met TinyDB voor eenvoudige zoekopdrachten
- **Proxy Rotatie**: Ondersteunt meerdere proxy-oplossingen voor schaalbaarheid
- **Foutafhandeling**: Exponentiële backoff en retry-mechanismen

## Installatie

1. Clone de repository of download de broncode

2. Maak een virtuele Python-omgeving aan (aanbevolen):

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

3. Installeer de benodigde packages:

```powershell
pip install -r requirements.txt
```

## Configuratie

Pas het `.env` bestand aan met de juiste instellingen:

```
# .env file voor PLUS Scraper configuratie
# API keys en configuratie-instellingen

# Proxy configuratie
USE_PROXY=false
PROXY_TYPE=free  # free, scraperapi, smartproxy, aws
PROXY_API_KEY=your_proxy_api_key_here

# Cookie configuratie (see COOKIES.md for setup instructions)
COOKIE_COUNT=0              # Number of cookies
# Add cookies in format: COOKIE_NAME=value
# Example: COOKIE_SSLB=1

# Request configuratie
REQUEST_TIMEOUT=30
MAX_RETRIES=3
BACKOFF_FACTOR=2

# Scraping configuratie
MAX_CONCURRENT_REQUESTS=5
REQUEST_DELAY=1

# PLUS specifieke instellingen
PLUS_CSRF_TOKEN=your_csrf_token_here  # Get this from browser dev tools
```

## Gebruik

De scraper heeft verschillende opties voor gebruik:

### Sitemap Verwerken

Analyseer en cache de sitemap om product-URL's te verzamelen:

```powershell
python main.py --sitemap
```

### Producten Scrapen

Scrape productdetails van eerder verzamelde URL's:

```powershell
python main.py --scrape
```

### Volledige Pipeline

Voer zowel sitemap-analyse als product-scraping uit:

```powershell
python main.py --all
```

Of eenvoudigweg:

```powershell
python main.py
```

### Specifieke SKU Scrapen

Voor het scrapen van een specifiek product:

```powershell
python main.py --sku 553975
```

### Overige Opties

```
--force-refresh    : Vernieuw de sitemap, negeer cache
--limit N          : Beperk tot N producten
--skip N           : Sla de eerste N producten over
--batch-size N     : Aantal producten om te verwerken per batch
--retry            : Verwerk items uit retry.json
--debug            : Toon debug logging
```

## Projectstructuur

```
scraper/
├── main.py           # Hoofdprogramma
├── sitemap_parser.py # Sitemap verwerking
├── product_scraper.py # Product scraping
├── database.py       # TinyDB database beheer
├── proxy_manager.py  # Proxy rotatie
├── cookie_manager.py # Cookie beheer voor API verzoeken
├── utils.py          # Hulpfuncties
├── test_cookies.py   # Hulpprogramma voor cookie-extractie
├── test_product_cookies.py # Test voor cookie API toegang
├── requirements.txt  # Package vereisten
├── .env              # Configuratie
├── data/             # Gegevensopslag
│   ├── db.json       # Database bestand
│   ├── cookies.json  # Cookie cache
│   └── products/     # Cache voor product JSON
└── logs/             # Logbestanden
```

## Proxy-providers

De scraper ondersteunt verschillende proxy-providers:

### Gratis Proxy's

- Free-proxy (PyPI package): haalt proxy's op van diverse gratis bronnen
- ProxyScrape: HTTP/SOCKS proxy's via JSON-API

### Betaalde Providers

- ScraperAPI: 40M IP's, slimme rotatie
- Smartproxy: residentiële & ISP proxy's

## Output Formaat

Producten worden opgeslagen in de TinyDB database met het volgende formaat:

```json
{
  "sku": "553975",
  "name": "PLUS Boerentrots BBQ worst tuinkruiden",
  "brand": "PLUS",
  "price": "3.99",
  "base_unit_price": "€14.25 per kilo",
  "image_url": "https://images.ctfassets.net/s0lodsnpsezb/553975_M/acdb12f4ec62c0695c99f6a3154861b6/553975.png",
  "ingredients": "81% Varkensvlees°, water, varkensvet°, ...",
  "allergens": "Tarwe, Soja, Selderij, Mosterd",
  "nutrients_base": {
    "unit": "gram",
    "value": 100
  },
  "nutrients": [
    {
      "name": "Energie KJ",
      "value": "1194.0",
      "unit": "kilojoule",
      "parent_code": ""
    },
    {
      "name": "Energie KC",
      "value": "288.0",
      "unit": "KC",
      "parent_code": ""
    },
    // Meer voedingswaarden...
  ],
  "extracted_at": "2025-04-25 12:15:30"
}
```

## Licentie

Dit project is beschikbaar onder de MIT-licentie.

## Disclaimer

Deze scraper is alleen voor educatieve doeleinden. Gebruik volgens de gebruiksvoorwaarden van de website.
