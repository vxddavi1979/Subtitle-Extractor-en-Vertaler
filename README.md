# Subtitle Extractor en Vertaler
Een Python-script om automatisch ondertitels uit videobestanden te extraheren, te vertalen van Engels naar Nederlands, en tekst voor slechthorenden te verwijderen.

## Functies
- Detecteert en extraheert automatisch Nederlandse ondertitels als deze aanwezig zijn
- Extraheert Engelse ondertitels en vertaalt deze naar het Nederlands
- Verwijdert tekst voor slechthorenden (beschrijvingen, geluidseffecten, personagennamen)
- Ondersteunt verschillende ondertitelformaten, inclusief ASS (Advanced SubStation Alpha)
- Gebruikt lokale LibreTranslate server voor vertalingen
- Slaat bestanden over die al Nederlandse ondertitels hebben
- **NIEUW**: Ondersteuning voor het selecteren en verwerken van meerdere mappen tegelijk
- Inclusief verbeterde GUI voor het selecteren van één of meerdere mappen

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
   In de GUI-modus krijg je een dialoogvenster waarin je meerdere mappen kunt toevoegen voor verwerking.

### Command-line opties
```
python subs.py [map1] [map2] ... [mapN] [opties]
```
Je kunt één of meerdere mappen opgeven als positional arguments.

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

Verwerk bestanden in meerdere mappen:
```
python subs.py C:\Mijn\Series C:\Films D:\Documentaires
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

## Multi-map selectie GUI
Met de nieuwe GUI voor het selecteren van meerdere mappen kun je:
1. Op "Map toevoegen" klikken om een map te selecteren en toe te voegen aan de lijst
2. Een map in de lijst selecteren en op "Verwijder geselecteerde" klikken om deze te verwijderen
3. Op "Klaar" klikken wanneer je alle gewenste mappen hebt geselecteerd
4. Het script zal dan alle videobestanden in alle geselecteerde mappen (inclusief submappen) verwerken

## Hoe het werkt
1. Het script zoekt naar video bestanden in alle opgegeven mappen en submappen
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
- **Probleem met multiple folder select**: Controleer of Tkinter correct is geïnstalleerd en of je een GUI-omgeving hebt

## Licentie
Vrij te gebruiken en aan te passen (MIT Licentie)

## Credits
- FFmpeg voor ondertitel extractie
- LibreTranslate voor open-source vertalingen
- Python en alle bijbehorende bibliotheken

## Bijdragen
Suggesties, verbeteringen en bugfixes zijn welkom via pull requests!
