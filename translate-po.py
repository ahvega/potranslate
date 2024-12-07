# Script: translate-po.py
# Purpose: Translates untranslated entries in a PO file using DeepL API
# Dependencies: polib, deepl, python-dotenv, tqdm

import argparse
import os
from dotenv import load_dotenv  # type: ignore  # Handles environment variables
import polib  # Handles PO file operations
import deepl  # DeepL API client
from tqdm import tqdm  # Progress bar functionality

def main():
    """
    Main function that handles the PO file translation process.
    Workflow:
    1. Parse command line arguments
    2. Load DeepL API key from environment
    3. Read and parse PO file
    4. Translate untranslated entries
    5. Save translated file
    """
    # Set up command line argument parsing
    # Required: input_file - Path to the PO file to translate
    # Optional: target-lang - Target language code (defaults to ES for Spanish)
    parser = argparse.ArgumentParser(description='Translate PO file using DeepL API')
    parser.add_argument('input_file', help='Input PO file to translate')
    parser.add_argument('--target-lang', default='ES', 
                       help='Target language code (default: ES)')
    args = parser.parse_args()

    # Load API key from .env file
    # File should contain: DEEPL_API_KEY=your_api_key
    load_dotenv()
    api_key = os.getenv('DEEPL_API_KEY')
    
    if not api_key:
        print("Error: DEEPL_API_KEY not found in .env file")
        exit(1)

    # Initialize DeepL translator with API key
    # This will be used for all translation operations
    translator = deepl.Translator(api_key)

    # Load and parse the PO file
    # polib handles the complexities of PO file format
    try:
        po = polib.pofile(args.input_file)
    except Exception as e:
        print(f"Error loading PO file: {e}")
        exit(1)

    # Create output filename
    # Appends target language code to original filename
    # Example: messages.po -> messages_ES.po
    base_name = os.path.splitext(args.input_file)[0]
    output_file = f"{base_name}_{args.target_lang}.po"

    # Translate each untranslated entry
    # Uses tqdm to show progress bar during translation
    print(f"Translating to {args.target_lang}...")
    for entry in tqdm(po.untranslated_entries()):
        try:
            # Translate the source text (msgid)
            # preserve_formatting=True ensures HTML tags remain intact
            translation = translator.translate_text(
                entry.msgid,
                target_lang=args.target_lang,
                preserve_formatting=True
            )
            # Update the PO entry with translated text
            entry.msgstr = translation.text
        except Exception as e:
            # Log error and continue with next entry if translation fails
            print(f"\nError translating entry: {e}")
            print(f"Problematic text: {entry.msgid}")
            continue

    # Save the translated PO file
    # Creates new file with _ES suffix
    try:
        po.save(output_file)
        print(f"\nTranslation completed. Output saved to: {output_file}")
    except Exception as e:
        print(f"Error saving translated file: {e}")
        exit(1)

if __name__ == '__main__':
    main()