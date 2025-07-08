# PLUS Product Scraper

Een schaalbare scraper voor het verzamelen van productinformatie van PLUS.nl, inclusief voedingswaarden.

## Functionaliteiten

- **Sitemap Crawler**: Parset sitemap van PLUS.nl om alle product-URL's te verzamelen
- **Product Scraper**: Haalt gedetailleerde productinformatie op via de PLUS API
- **JSON Database**: Opslag van gegevens met TinyDB voor eenvoudige zoekopdrachten
- **Proxy Rotatie**: Ondersteunt meerdere proxy-oplossingen voor schaalbaarheid
- **Foutafhandeling**: Exponentiële backoff en retry-mechanismen

## Installatie

1. Clone de repository of download de broncode.
2. Maak een virtuele Python-omgeving aan (aanbevolen).
3. Installeer de benodigde packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuratie

Pas het `.env` bestand aan met de juiste instellingen. Zie `.env.example` voor een template.

## Gebruik

De scraper heeft verschillende opties:

- **`--sitemap`**: Analyseer en cache de sitemap.
- **`--scrape`**: Scrape productdetails van verzamelde URL's.
- **`--all`**: Voer de volledige pipeline uit.
- **`--sku <ID>`**: Scrape een specifiek product.
- **`--limit <N>`**: Beperk het aantal producten.

## Projectstructuur

```
scraper/
├── main.py           # Hoofdprogramma
├── sitemap_parser.py # Sitemap verwerking
├── product_scraper.py # Product scraping
├── database.py       # TinyDB database beheer
├── proxy_manager.py  # Proxy rotatie
├── cookie_manager.py # Cookie beheer
├── utils.py          # Hulpfuncties
├── requirements.txt  # Package vereisten
├── .env.example      # Configuratie template
└── data/             # Gegevensopslag
```

## Licentie

Dit project is beschikbaar onder de MIT-licentie.

## Disclaimer

Deze scraper is alleen voor educatieve doeleinden. Gebruik volgens de gebruiksvoorwaarden van de website.
