# Cookie Setup Guide

Om de PLUS API te benaderen, moet de scraper geldige cookies gebruiken. Deze gids legt uit hoe je cookies kunt instellen voor de scraper.

## Optie 1: Handmatig cookies verzamelen

1. Open een browser en ga naar [PLUS.nl](https://www.plus.nl)
2. Open de browser developer tools (F12 of rechtermuisklik -> Inspecteren)
3. Ga naar het Network tabblad
4. Laad een product pagina, bijvoorbeeld https://www.plus.nl/product/plus-boerentrots-bbq-worst-tuinkruiden-krimp-280-g-553975
5. Filter op "API" of "XHR" en zoek naar een request naar `DataActionGetProductDetailsAndAgeInfo`
6. Klik op dit request en kijk bij "Headers" -> "Request Headers" voor de Cookie waarde
7. Kopieer deze cookies en sla ze op in het `.env` bestand

## Optie 2: PowerShell cookie extractor gebruiken

De eenvoudigste methode is om de PowerShell cookie extractor te gebruiken:

1. Open PowerShell met administrator rechten
2. Voer de volgende commando's uit:

```powershell
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$session.UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
$session.Cookies.Add((New-Object System.Net.Cookie("SSLB", "1", "/", ".plus.nl")))
$session.Cookies.Add((New-Object System.Net.Cookie("plus_cookie_level", "3", "/", "www.plus.nl")))

# Meer cookies toevoegen indien nodig...

# Kopieer de uitvoer en plak het in test_cookies.py
```

3. Open het bestand `test_cookies.py` en plaats de PowerShell cookie regels in de `powershell_output` variabele
4. Voer het script uit: `python test_cookies.py`
5. De cookies worden automatisch naar het `.env` bestand geschreven

## Optie 3: De interactieve cookie setup wizard gebruiken

1. Voer het volgende commando uit:

```powershell
python run_scraper.py setup-cookies
```

2. Volg de instructies op het scherm om de cookie regels in te voeren
3. De cookies worden automatisch naar het `.env` bestand geschreven

## Cookies testen

Om te controleren of de cookies werken, kun je het volgende commando uitvoeren:

```powershell
python test_product_cookies.py --sku 553975 --debug
```

Als alles goed werkt, zie je een succesbericht en worden de productgegevens opgeslagen in `data/test/product_553975_cookie_test.json`.

## Probleemoplossing

Als je problemen ondervindt met cookies:

1. Zorg ervoor dat je cookies up-to-date zijn (cookies verlopen na verloop van tijd)
2. Controleer of je de juiste waarden hebt gekopieerd
3. Probeer opnieuw cookies te verzamelen via de browser
4. Voer het test script uit met debug optie om meer details te zien: `python test_product_cookies.py --debug`
