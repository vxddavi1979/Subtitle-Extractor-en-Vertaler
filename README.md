# Subtitle Extractor en Vertaler

Een Python-script om automatisch ondertitels uit videobestanden te extraheren, te vertalen van Engels naar Nederlands, en tekst voor slechthorenden te verwijderen.

## Functies

- Detecteert en extraheert automatisch Nederlandse ondertitels als deze aanwezig zijn
- Extraheert Engelse ondertitels en vertaalt deze naar het Nederlands
- Verwijdert tekst voor slechthorenden (beschrijvingen, geluidseffecten, personagennamen)
- Ondersteunt verschillende ondertitelformaten, inclusief ASS (Advanced SubStation Alpha)
- Gebruikt lokale LibreTranslate server voor vertalingen
- Slaat bestanden over die al Nederlandse ondertitels hebben
- Inclusief GUI voor het selecteren van mappen

## Vereisten

### Software

- Python 3.6 of hoger
- FFmpeg (voor het extraheren van ondertitels)
- LibreTranslate (lokale vertaalserver)

### Python-modules

```
pip install requests
pip install tkinter  # Meestal standaard aanwezig in Python
```

Optioneel (als fallback voor LibreTranslate):
```
pip install deep-translator
```

## Installatie

1. Installeer FFmpeg:
   - **Windows**: Download van [ffmpeg.org](https://ffmpeg.org/download.html) en voeg toe aan PATH
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg` of equivalent voor je distributie

2. Installeer LibreTranslate:
   - Met Docker: `docker run -ti --rm -p 5000:5000 libretranslate/libretranslate`
   - Of volg de instructies op [LibreTranslate GitHub](https://github.com/LibreTranslate/LibreTranslate)

3. Download het script of kloon de repository

## Gebruik

### Basis gebruik

1. Start LibreTranslate server op poort 5000 (standaard)
2. Voer het script uit zonder parameters voor GUI modus:
   ```
   python subs.py
   ```

### Command-line opties

```
python subs.py [map] [opties]
```

Opties:
- `--single BESTAND`: Verwerk één bestand in plaats van een hele map
- `--all`: Verwerk alle bestanden ongeacht ouderdom
- `--hours N`: Verwerk alleen bestanden gewijzigd in de afgelopen N uur
- `--force`: Verwerk ook bestanden die al een .nl.srt hebben
- `--no-clean`: Verwijder geen tekst voor slechthorenden
- `--libre-url URL`: Aangepaste URL voor LibreTranslate (standaard: http://localhost:5000)
- `--temp MAP`: Aangepaste map voor tijdelijke bestanden

### Voorbeelden

Verwerk alle bestanden in een map:
```
python subs.py C:\Mijn\Series
```

Verwerk één bestand:
```
python subs.py --single "C:\Mijn\Series\Aflevering.mkv"
```

Verwerk bestanden van de afgelopen week:
```
python subs.py --hours 168
```

Forceer herverwerking:
```
python subs.py --force
```

## Hoe het werkt

1. Het script zoekt naar video bestanden in de opgegeven map
2. Voor elk bestand:
   - Controleert of er al een .nl.srt bestand is (slaat over tenzij --force gebruikt wordt)
   - Controleert of het bestand Nederlandse ondertitels bevat en extraheert deze indien aanwezig
   - Als er geen Nederlandse ondertitels zijn, extraheert het de Engelse ondertitels
   - Vertaalt Engelse ondertitels naar het Nederlands via LibreTranslate
   - Verwijdert tekst voor slechthorenden (personagenamen, geluidseffecten, etc.)
   - Slaat het resultaat op als [videobestandsnaam].nl.srt naast het videobestand

## Probleemoplossing

- **FFmpeg niet gevonden**: Zorg dat FFmpeg in je PATH staat of specificeer het volledige pad in het script
- **LibreTranslate niet beschikbaar**: Controleer of de LibreTranslate server draait op http://localhost:5000
- **Vertaling werkt niet**: Controleer de logs van LibreTranslate en zorg dat het taalmodel correct is geladen

## Licentie

Vrij te gebruiken en aan te passen (MIT Licentie)

## Credits

- FFmpeg voor ondertitel extractie
- LibreTranslate voor open-source vertalingen
- Python en alle bijbehorende bibliotheken

## Bijdragen

Suggesties, verbeteringen en bugfixes zijn welkom via pull requests!
