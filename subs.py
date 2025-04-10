#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import datetime
import subprocess
import tempfile
import time
import glob
import argparse
from pathlib import Path
import re

# Check for required libraries
try:
    import requests
except ImportError:
    print("De 'requests' bibliotheek is niet geïnstalleerd.")
    print("Installeer deze met: pip install requests")
    sys.exit(1)

def check_existing_nl_subtitle(video_file, force=False):
    """Check if a .nl.srt file already exists next to the video file"""
    if force:
        return False
        
    base_dir = os.path.dirname(video_file)
    video_name_without_ext = os.path.splitext(os.path.basename(video_file))[0]
    nl_srt_path = os.path.join(base_dir, f"{video_name_without_ext}.nl.srt")
    
    if os.path.exists(nl_srt_path):
        print(f"Nederlandse ondertitels ({os.path.basename(nl_srt_path)}) bestaan al, overslaan...")
        return True
    return False

def clean_subtitle_text(text):
    """Remove hearing impaired text from subtitle"""
    # Remove character names that end with a colon
    text = re.sub(r'^[A-Z][A-Z\s\.]+:', '', text)
    
    # Remove text between parentheses (sound descriptions)
    text = re.sub(r'\([^)]*\)', '', text)
    
    # Remove text between brackets
    text = re.sub(r'\[[^\]]*\]', '', text)
    
    # Remove text between < and > (often used for formatting)
    text = re.sub(r'<[^>]*>', '', text)
    
    # Remove text between { and } (sometimes used for comments)
    text = re.sub(r'\{[^}]*\}', '', text)
    
    # Remove lines that are all uppercase (often speaker indications)
    lines = text.split('\n')
    filtered_lines = []
    for line in lines:
        if not (line.strip() and line.strip() == line.strip().upper() and any(c.isalpha() for c in line)):
            filtered_lines.append(line)
    text = '\n'.join(filtered_lines)
    
    # Trim any leading/trailing whitespace
    text = text.strip()
    
    return text

def check_and_extract_dutch_subtitles(video_file, output_dir):
    """Check if Dutch subtitles exist in the video file and extract them if found"""
    base_name = os.path.basename(video_file)
    file_name_without_ext = os.path.splitext(base_name)[0]
    output_srt = os.path.join(output_dir, f"{file_name_without_ext}.nl.srt")
    
    try:
        # First, list all subtitle streams in the file
        print(f"Checking for Dutch subtitles in {base_name}...")
        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", 
               "-select_streams", "s", video_file]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Check for Dutch subtitle language tags
            dutch_identifiers = ["nld", "dut", "nl", "dutch", "nederlands"]
            has_dutch = any(dutch_id in result.stdout.lower() for dutch_id in dutch_identifiers)
            
            if has_dutch:
                print("Dutch subtitles found, extracting...")
                
                # Try different mappings for Dutch subtitles
                dutch_maps = [
                    "0:s:m:language:nld",
                    "0:s:m:language:dut", 
                    "0:s:m:language:nl",
                    "0:s:m:language:dutch",
                    "0:s:m:language:nederlands"
                ]
                
                for map_option in dutch_maps:
                    try:
                        cmd = ["ffmpeg", "-i", video_file, "-map", map_option, 
                               "-c:s", "srt", output_srt]
                        subprocess.run(cmd, capture_output=True, timeout=60)
                        
                        if os.path.exists(output_srt) and os.path.getsize(output_srt) > 0:
                            print(f"✓ Extracted Dutch subtitles from {base_name}")
                            return output_srt
                    except:
                        continue
                
                # If specific language mapping failed, try to find Dutch subtitles by checking all streams
                import json
                try:
                    data = json.loads(result.stdout)
                    for i, stream in enumerate(data.get('streams', [])):
                        if stream.get('tags', {}).get('language', '').lower() in dutch_identifiers:
                            print(f"Found Dutch subtitle at stream index {i}")
                            cmd = ["ffmpeg", "-i", video_file, "-map", f"0:{stream.get('index', i)}", 
                                   "-c:s", "srt", output_srt]
                            subprocess.run(cmd, capture_output=True, timeout=60)
                            
                            if os.path.exists(output_srt) and os.path.getsize(output_srt) > 0:
                                print(f"✓ Extracted Dutch subtitles from stream {i} in {base_name}")
                                return output_srt
                except json.JSONDecodeError:
                    print("Could not parse JSON response")
                
                print("× Could not extract Dutch subtitles despite finding them")
                return None
            else:
                print("No Dutch subtitles found in the file")
                return None
                
        except subprocess.TimeoutExpired:
            print("Timeout while checking for subtitle streams")
            return None
            
    except Exception as e:
        print(f"Error checking for Dutch subtitles: {e}")
        return None

def extract_subtitles(video_file, output_dir):
    """Extract embedded subtitles from video file"""
    base_name = os.path.basename(video_file)
    file_name_without_ext = os.path.splitext(base_name)[0]
    output_srt = os.path.join(output_dir, f"{file_name_without_ext}.eng.srt")
    
    try:
        # First, list all subtitle streams in the file
        print(f"Checking subtitle streams in {base_name}...")
        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", 
               "-select_streams", "s", video_file]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            print(f"Found subtitle information: {result.stdout[:300]}...")
            
            # Check for ASS subtitle format
            if "ass" in result.stdout.lower():
                print("ASS subtitle format detected. Using specialized extraction...")
                stream_index = 0
                
                # Try to find the stream index for the ASS subtitle
                import json
                try:
                    data = json.loads(result.stdout)
                    for i, stream in enumerate(data.get('streams', [])):
                        if stream.get('codec_name') == 'ass':
                            stream_index = stream.get('index', i)
                            print(f"Found ASS subtitle at stream index {stream_index}")
                            break
                except json.JSONDecodeError:
                    print("Could not parse JSON response, using default stream index 0")
                
                # Extract and convert ASS to SRT
                try:
                    print(f"Extracting ASS subtitle (stream {stream_index}) and converting to SRT...")
                    cmd = ["ffmpeg", "-i", video_file, "-map", f"0:{stream_index}", 
                           "-c:s", "srt", output_srt]
                    subprocess.run(cmd, capture_output=True, timeout=90)
                    
                    if os.path.exists(output_srt) and os.path.getsize(output_srt) > 0:
                        print(f"✓ Successfully extracted and converted ASS subtitle to SRT from {base_name}")
                        return output_srt
                except subprocess.TimeoutExpired:
                    print("Timeout while extracting ASS subtitle, trying alternative methods...")
        except subprocess.TimeoutExpired:
            print("Timeout while checking subtitle streams, continuing with extraction attempts...")
            result = subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")
        
        # Try with language tag first
        if "eng" in result.stdout.lower() or "english" in result.stdout.lower():
            print("English subtitles found, extracting...")
            
            # Try to extract English subtitles with timeout
            try:
                cmd = ["ffmpeg", "-i", video_file, "-map", "0:s:m:language:eng", 
                       "-c:s", "srt", output_srt]
                subprocess.run(cmd, capture_output=True, timeout=60)
                
                if os.path.exists(output_srt) and os.path.getsize(output_srt) > 0:
                    print(f"✓ Extracted English subtitles from {base_name}")
                    return output_srt
            except subprocess.TimeoutExpired:
                print("Timeout while extracting English subtitles, trying next method...")
        
        # Try the first subtitle stream with timeout and forced SRT conversion
        print("Trying first subtitle stream with SRT conversion...")
        first_srt = os.path.join(output_dir, f"{file_name_without_ext}.first.srt")
        try:
            cmd = ["ffmpeg", "-i", video_file, "-map", "0:s:0", 
                   "-c:s", "srt", first_srt]
            subprocess.run(cmd, capture_output=True, timeout=60)
            
            if os.path.exists(first_srt) and os.path.getsize(first_srt) > 0:
                print(f"✓ Extracted first subtitle stream from {base_name}")
                # Rename to expected output file
                shutil.move(first_srt, output_srt)
                return output_srt
        except subprocess.TimeoutExpired:
            print("Timeout while extracting first subtitle stream, trying next method...")
        
        # If we still haven't found subtitles, try a more direct approach
        print("Trying direct subtitle extraction...")
        try:
            # This approach uses the -c:s srt option which forces conversion to SRT format
            cmd = ["ffmpeg", "-i", video_file, "-map", "0:s", "-c:s", "srt", output_srt]
            subprocess.run(cmd, capture_output=True, timeout=120)
            
            if os.path.exists(output_srt) and os.path.getsize(output_srt) > 0:
                print(f"✓ Extracted subtitles using direct method from {base_name}")
                return output_srt
        except subprocess.TimeoutExpired:
            print("Timeout during direct subtitle extraction")
        
        # If all methods fail, try one last extraction attempt
        print("Trying final extraction attempt with simplified options...")
        try:
            # Simplest extraction that might work
            cmd = ["ffmpeg", "-i", video_file, "-c:s", "srt", output_srt]
            subprocess.run(cmd, capture_output=True, timeout=180)
            
            if os.path.exists(output_srt) and os.path.getsize(output_srt) > 0:
                print(f"✓ Extracted subtitles using simplified method from {base_name}")
                return output_srt
        except subprocess.TimeoutExpired:
            print("Timeout during simplified subtitle extraction")
            
        # If nothing worked after all attempts
        print(f"× No suitable subtitles could be extracted from {base_name}")
        return None
        
    except Exception as e:
        print(f"Error extracting subtitles: {e}")
        return None

def translate_subtitle_file(srt_file, target_language="nl", use_libre=True, libre_url="http://localhost:5000", clean_hi=True):
    """Translate a subtitle file from English to target language"""
    if not srt_file or not os.path.exists(srt_file):
        return None
    
    # Get the base name and create the output file name
    base_dir = os.path.dirname(srt_file)
    base_name = os.path.basename(srt_file)
    file_name_without_ext = os.path.splitext(base_name)[0].replace(".eng", "")
    output_file = os.path.join(base_dir, f"{file_name_without_ext}.{target_language}.srt")
    
    try:
        # Read subtitle file
        with open(srt_file, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        # Split into subtitle blocks (each block has index, timestamp, and text)
        subtitle_blocks = re.split(r'\n\s*\n', content.strip())
        translated_blocks = []
        
        print(f"Translating {os.path.basename(srt_file)} to Dutch...")
        
        # Setup translator based on choice
        if use_libre:
            print(f"Using LibreTranslate at {libre_url}")
            import requests
            translate_url = f"{libre_url}/translate"
            
            # Function to translate text using LibreTranslate
            def libre_translate(text):
                if not text or text.strip() == "":
                    return text
                
                try:
                    payload = {
                        "q": text,
                        "source": "en",
                        "target": target_language,
                        "format": "text"
                    }
                    
                    response = requests.post(translate_url, json=payload, timeout=10)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if "translatedText" in result:
                            return result["translatedText"]
                    
                    print(f"LibreTranslate error: {response.status_code}, {response.text[:100]}")
                    return text  # Return original text on error
                    
                except Exception as e:
                    print(f"Error using LibreTranslate: {e}")
                    return text  # Return original text on error
            
            translate_function = libre_translate
        else:
            # Use deep_translator as fallback
            try:
                from deep_translator import GoogleTranslator
                translator = GoogleTranslator(source='en', target=target_language)
                
                def google_translate(text):
                    if not text or text.strip() == "":
                        return text
                    
                    try:
                        # Translate text in smaller chunks if needed (API limit)
                        if len(text) > 5000:
                            chunks = [text[i:i+5000] for i in range(0, len(text), 5000)]
                            translated_chunks = []
                            for chunk in chunks:
                                translated_chunk = translator.translate(chunk)
                                translated_chunks.append(translated_chunk)
                            return ' '.join(translated_chunks)
                        else:
                            return translator.translate(text)
                    except Exception as e:
                        print(f"Error during translation: {e}. Using original text.")
                        return text
                
                translate_function = google_translate
            except ImportError:
                print("deep_translator not available, falling back to English")
                # Just return original text if no translation is available
                translate_function = lambda x: x
        
        # Process each subtitle block
        for block in subtitle_blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                # Skip invalid blocks
                continue
                
            index = lines[0]
            timestamp = lines[1]
            text = '\n'.join(lines[2:])
            
            # Clean hearing impaired text if requested
            if clean_hi:
                text = clean_subtitle_text(text)
                # Skip blocks that are now empty
                if not text.strip():
                    continue
            
            # Translate only the text part
            translated_text = translate_function(text)
            
            # Build the translated block
            translated_block = f"{index}\n{timestamp}\n{translated_text}"
            translated_blocks.append(translated_block)
        
        # Write translated content to the new file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(translated_blocks))
        
        print(f"✓ Created Dutch subtitles: {os.path.basename(output_file)}")
        return output_file
    
    except Exception as e:
        print(f"Error translating subtitles: {e}")
        return None

def find_media_files(directories, age_in_hours=None):
    """Find all video files in the directories"""
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.m4v']
    
    # Ensure directories is a list
    if isinstance(directories, str):
        directories = [directories]
    
    # Find all video files in the directories and subdirectories
    found_files = []
    
    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in video_extensions):
                    file_path = os.path.join(root, file)
                    
                    # If age_in_hours is None or 0, include all files regardless of age
                    if age_in_hours is None or age_in_hours == 0:
                        found_files.append(file_path)
                    else:
                        # Calculate the cutoff time
                        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=age_in_hours)
                        cutoff_timestamp = cutoff_time.timestamp()
                        
                        file_mtime = os.path.getmtime(file_path)
                        # Check if the file was modified within the cutoff period
                        if file_mtime >= cutoff_timestamp:
                            found_files.append(file_path)
    
    return found_files

def select_directories_dialog():
    """Open a directory selection dialog that allows multiple selections"""
    try:
        import tkinter as tk
        from tkinter import filedialog
        import tkinter.messagebox as messagebox
        
        selected_dirs = []
        
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Create a custom dialog for multiple directory selection
        selection_window = tk.Toplevel(root)
        selection_window.title("Selecteer mappen voor video bestanden")
        selection_window.geometry("500x400")
        selection_window.minsize(500, 400)
        
        # Frame to hold the list and buttons
        main_frame = tk.Frame(selection_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Label
        label = tk.Label(main_frame, text="Geselecteerde mappen:")
        label.pack(anchor=tk.W, pady=(0, 5))
        
        # Listbox to show selected directories
        listbox_frame = tk.Frame(main_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(listbox_frame, selectmode=tk.SINGLE, yscrollcommand=scrollbar.set)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=listbox.yview)
        
        # Button frame
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        def add_directory():
            directory = filedialog.askdirectory(title="Selecteer een map")
            if directory:
                # Don't add duplicates
                if directory not in selected_dirs:
                    selected_dirs.append(directory)
                    listbox.insert(tk.END, directory)
        
        def remove_directory():
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                listbox.delete(index)
                selected_dirs.pop(index)
        
        def done():
            if not selected_dirs:
                messagebox.showwarning("Waarschuwing", "Je hebt geen mappen geselecteerd!")
            else:
                selection_window.destroy()
                root.quit()
        
        # Add buttons
        add_button = tk.Button(button_frame, text="Map toevoegen", command=add_directory)
        add_button.pack(side=tk.LEFT, padx=5)
        
        remove_button = tk.Button(button_frame, text="Verwijder geselecteerde", command=remove_directory)
        remove_button.pack(side=tk.LEFT, padx=5)
        
        done_button = tk.Button(button_frame, text="Klaar", command=done)
        done_button.pack(side=tk.RIGHT, padx=5)
        
        # Start the main loop
        selection_window.protocol("WM_DELETE_WINDOW", done)  # Handle window close
        root.mainloop()
        
        if selected_dirs:
            return selected_dirs
        else:
            print("Geen mappen geselecteerd.")
            return None
    except ImportError:
        print("Tkinter is niet beschikbaar. Geef de mappen op via de command line.")
        return None

def process_dutch_subtitles(dutch_srt, target_file, clean_hi=True):
    """Process existing Dutch subtitles (clean if requested)"""
    if clean_hi:
        print("Cleaning Dutch subtitles...")
        # Read the subtitles
        with open(dutch_srt, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        # Split into subtitle blocks
        subtitle_blocks = re.split(r'\n\s*\n', content.strip())
        cleaned_blocks = []
        
        # Process each subtitle block
        for block in subtitle_blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                # Skip invalid blocks
                continue
                
            index = lines[0]
            timestamp = lines[1]
            text = '\n'.join(lines[2:])
            
            # Clean hearing impaired text
            text = clean_subtitle_text(text)
            # Skip blocks that are now empty
            if not text.strip():
                continue
            
            # Build the cleaned block
            cleaned_block = f"{index}\n{timestamp}\n{text}"
            cleaned_blocks.append(cleaned_block)
        
        # Write cleaned content to the target file
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(cleaned_blocks))
        
        print(f"✓ Saved cleaned Dutch subtitles: {os.path.basename(target_file)}")
    else:
        # Just copy the file
        shutil.copy2(dutch_srt, target_file)
        print(f"✓ Saved Dutch subtitles: {os.path.basename(target_file)}")
    
    return target_file

def main():
    parser = argparse.ArgumentParser(description='Extract and translate subtitles from media files')
    parser.add_argument('directories', nargs='*', default=None, help='Directories to scan for media files (optional)')
    parser.add_argument('--hours', type=int, default=None, 
                       help='Process files modified in the last N hours (0 or None for all files)')
    parser.add_argument('--all', action='store_true',
                       help='Process all files regardless of modification time')
    parser.add_argument('--temp', help='Temporary directory to store extracted subtitles')
    parser.add_argument('--single', help='Process a single file instead of scanning a directory')
    parser.add_argument('--libre', action='store_true', default=True,
                      help='Use LibreTranslate instead of Google Translate (default: True)')
    parser.add_argument('--libre-url', default='http://localhost:5000',
                      help='URL for LibreTranslate server (default: http://localhost:5000)')
    parser.add_argument('--no-clean', action='store_false', dest='clean_hi', default=True,
                      help='Do not remove hearing impaired text (descriptions, speaker names, etc.)')
    parser.add_argument('--force', action='store_true', default=False,
                      help='Process files even if .nl.srt already exists (default: False)')
    
    args = parser.parse_args()
    
    # Handle single file mode
    if args.single:
        if os.path.isfile(args.single):
            # Create temporary directory if not specified
            temp_dir = args.temp if args.temp else tempfile.mkdtemp()
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
                
            print(f"Processing single file: {os.path.basename(args.single)}")
            
            # First, check if Dutch subtitle file already exists next to the video file
            if check_existing_nl_subtitle(args.single, args.force):
                print("Bestaande Nederlandse ondertitels gevonden, geen actie nodig.")
                return 0
            
            # First, check if Dutch subtitles already exist in the file
            dutch_srt = check_and_extract_dutch_subtitles(args.single, temp_dir)
            
            if dutch_srt:
                # If Dutch subtitles were found, copy them directly to the target location
                target_dir = os.path.dirname(args.single)
                video_name_without_ext = os.path.splitext(os.path.basename(args.single))[0]
                target_file = os.path.join(target_dir, f"{video_name_without_ext}.nl.srt")
                
                process_dutch_subtitles(dutch_srt, target_file, args.clean_hi)
                
                # Clean up
                if not args.temp:
                    shutil.rmtree(temp_dir)
                    
                return 0
            
            # If no Dutch subtitles, extract English ones and translate
            extracted_srt = extract_subtitles(args.single, temp_dir)
            
            if extracted_srt:
                # Translate subtitles
                translated_srt = translate_subtitle_file(
                    extracted_srt, 
                    target_language="nl",
                    use_libre=args.libre,
                    libre_url=args.libre_url,
                    clean_hi=args.clean_hi
                )
                
                if translated_srt:
                    # Move the translated subtitle to media file location
                    target_dir = os.path.dirname(args.single)
                    video_name_without_ext = os.path.splitext(os.path.basename(args.single))[0]
                    target_file = os.path.join(target_dir, f"{video_name_without_ext}.nl.srt")
                    
                    shutil.copy2(translated_srt, target_file)
                    print(f"✓ Saved Dutch subtitles next to video: {os.path.basename(target_file)}")
                    
            # Clean up
            if not args.temp:
                shutil.rmtree(temp_dir)
                
            return 0
        else:
            print(f"Error: File '{args.single}' does not exist.")
            return 1
    
    # If no directories are provided in the command line, open the multi-directory selection dialog
    selected_directories = args.directories
    if not selected_directories:
        print("Geen mappen opgegeven, openen van mapkeuze dialoog...")
        selected_directories = select_directories_dialog()
        if not selected_directories:
            print("Geen mappen geselecteerd. Beëindiging.")
            return 1
    
    # Verify the input directories exist
    valid_directories = []
    for directory in selected_directories:
        if os.path.isdir(directory):
            valid_directories.append(directory)
        else:
            print(f"Waarschuwing: Map '{directory}' bestaat niet en wordt overgeslagen.")
    
    if not valid_directories:
        print("Geen geldige mappen opgegeven. Beëindiging.")
        return 1
    
    # Create temporary directory if not specified
    temp_dir = args.temp if args.temp else tempfile.mkdtemp()
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    # Override hours if --all flag is used
    if args.all:
        args.hours = None
    
    time_message = "all files" if args.hours is None or args.hours == 0 else f"files modified in the last {args.hours} hours"
    print(f"Scanning for media files ({time_message}) in {len(valid_directories)} directories...")
    media_files = find_media_files(valid_directories, args.hours)
    
    if not media_files:
        no_files_message = "No media files found"
        if args.hours is not None and args.hours > 0:
            no_files_message += f" modified in the last {args.hours} hours"
        no_files_message += " in the selected directories."
        print(no_files_message)
        
        # Suggest using --all flag if time-based search found nothing
        if args.hours is not None and args.hours > 0:
            print("Tip: Use --all flag to process all files regardless of modification time")
        
        return 0
    
    print(f"Found {len(media_files)} media files.")
    
    processed_count = 0
    
    for media_file in media_files:
        print(f"\nProcessing: {os.path.basename(media_file)}")
        
        # Check if Dutch subtitle file already exists next to the video file
        if check_existing_nl_subtitle(media_file, args.force):
            continue
        
        # First, check if Dutch subtitles already exist in the file
        dutch_srt = check_and_extract_dutch_subtitles(media_file, temp_dir)
        
        if dutch_srt:
            # If Dutch subtitles were found, copy them directly to the target location
            target_dir = os.path.dirname(media_file)
            video_name_without_ext = os.path.splitext(os.path.basename(media_file))[0]
            target_file = os.path.join(target_dir, f"{video_name_without_ext}.nl.srt")
            
            process_dutch_subtitles(dutch_srt, target_file, args.clean_hi)
            processed_count += 1
            continue
            
        # If no Dutch subtitles, extract English ones and translate
        extracted_srt = extract_subtitles(media_file, temp_dir)
        
        if extracted_srt:
            # Translate subtitles
            translated_srt = translate_subtitle_file(
                extracted_srt, 
                target_language="nl",
                use_libre=args.libre,
                libre_url=args.libre_url,
                clean_hi=args.clean_hi
            )
            
            if translated_srt:
                # Move the translated subtitle to media file location
                target_dir = os.path.dirname(media_file)
                video_name_without_ext = os.path.splitext(os.path.basename(media_file))[0]
                target_file = os.path.join(target_dir, f"{video_name_without_ext}.nl.srt")
                
                shutil.copy2(translated_srt, target_file)
                print(f"✓ Saved Dutch subtitles next to video: {os.path.basename(target_file)}")
                processed_count += 1
    
    # Clean up
    if not args.temp:
        shutil.rmtree(temp_dir)
    
    print(f"\nSummary: Processed {processed_count} out of {len(media_files)} files.")
    return 0

if __name__ == "__main__":
    sys.exit(main())