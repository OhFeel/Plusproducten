# PLUS Product Analyzer

Deze tool analyseert de gescrapte producten van PLUS.nl en biedt inzicht in de data.

## Vereisten

- Python 3.8 of hoger
- Alle packages in `requirements_analysis.txt`

## Installatie

1. Zorg ervoor dat je de scraper al hebt gebruikt om productgegevens te verzamelen
2. Installeer extra vereisten voor de analyse:

```powershell
pip install -r requirements_analysis.txt
```

## Gebruik

Run de analyseweb-app met de helper script:

```powershell
python start_analysis.py
```

Dit zal:
1. Controleren of er productgegevens beschikbaar zijn
2. Een TinyDB database maken vanuit de individuele product JSON bestanden
3. Alle benodigde packages installeren
4. De productgegevens voorverwerken voor analyse
5. Een webserver starten op poort 5000
6. Een webbrowser openen met het dashboard

Je kunt ook direct de analyse app starten met:

```powershell
python run_analysis.py
```

### Opties

- `--port PORT`: Gebruik een andere poort (standaard: 5000)
- `--no-browser`: Start de server zonder een browser te openen
- `--preprocess`: Voer alleen de voorverwerking uit zonder de webserver te starten

## Functionaliteiten

De analyse omvat:

- **Algemene statistieken**: Totaal aantal producten, merken, prijsbereik
- **Prijsverdeling**: Histogram van productprijzen
- **Merkanalyse**: Producttelling per merk
- **Eiwitanalyse**: 
  - Producten met het meeste eiwit per 100g
  - Beste eiwit/prijs-verhouding
- **Alcoholische producten**: De goedkoopste alcoholische dranken
- **Ingrediëntenanalyse**: Wordcloud van meest voorkomende ingrediënten
