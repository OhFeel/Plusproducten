"""
run_scraper.py - Command line helper script for the PLUS scraper
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

def setup_env_from_cookies():
    """
    Vraag de gebruiker om cookies uit PowerShell en sla deze op in .env
    """
    print("Cookie Setup Wizard voor PLUS Scraper")
    print("=====================================")
    print("Voer het PowerShell commando in dat je hebt gekopieerd met cookies.")
    print("Bijvoorbeeld: $session.Cookies.Add((New-Object System.Net.Cookie(\"SSLB\", \"1\", \"/\", \".plus.nl\")))")
    print("Druk op ENTER zonder invoer om te voltooien\n")
    
    cookie_lines = []
    print("Plak nu alle cookie regels (eindig met een lege regel):")
    while True:
        line = input().strip()
        if not line:
            break
        if "$session.Cookies.Add" in line:
            cookie_lines.append(line)
    
    if not cookie_lines:
        print("Geen cookies ingevoerd. Wizard wordt afgesloten.")
        return
    
    from test_cookies import extract_cookies_from_powershell, save_cookies_to_env
    cookies = extract_cookies_from_powershell("\n".join(cookie_lines))
    save_cookies_to_env(cookies)
    
    print(f"✓ {len(cookies)} cookies opgeslagen in .env bestand")

def main():
    """
    Main entry point
    """
    parser = argparse.ArgumentParser(description="PLUS Scraper Helper")
    subparsers = parser.add_subparsers(dest='command', help='Commando')
    
    # Cookie setup command
    setup_parser = subparsers.add_parser('setup-cookies', help='Setup cookies voor PLUS API toegang')
    
    # Run scraper command
    run_parser = subparsers.add_parser('run', help='Voer de scraper uit')
    run_parser.add_argument('--sku', type=str, help='Specifieke SKU om te scrapen')
    run_parser.add_argument('--limit', type=int, help='Maximaal aantal producten')
    run_parser.add_argument('--debug', action='store_true', help='Debug mode')
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command == 'setup-cookies':
        setup_env_from_cookies()
    elif args.command == 'run':
        # Verzamel argumenten voor de scraper
        cmd_args = ["python", "main.py"]
        
        if args.sku:
            cmd_args.extend(["--sku", args.sku])
        else:
            cmd_args.append("--all")  # Default is full scrape
        
        if args.limit:
            cmd_args.extend(["--limit", str(args.limit)])
        
        if args.debug:
            cmd_args.append("--debug")
        
        # Voer de scraper uit
        print(f"Voer uit: {' '.join(cmd_args)}")
        os.execvp(sys.executable, cmd_args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
