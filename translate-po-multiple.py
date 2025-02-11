# Script: translate-po-multiple.py
# Purpose: Translates untranslated entries in a PO file using multiple translation APIs
# Dependencies: polib, deepl, python-dotenv, tqdm, requests, openai, google-cloud-translate

import argparse
import os
import polib
from tqdm import tqdm
from dotenv import load_dotenv
import requests
import logging
import time
import json
from openai import OpenAI
from google.cloud import translate_v3

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def isolate_html_and_variables(text):
    """
    Isolates HTML tags and variables from a string.

    Args:
        text (str): The string to process.

    Returns:
        tuple: (cleaned_text, html_tags, variables)
    """
    import re
    html_tags = re.findall(r'<[^>]+>', text)
    variables = re.findall(r'%[sd]|{[0-9]+}', text)
    cleaned_text = re.sub(r'<[^>]+>', '{{HTML}}', text)
    cleaned_text = re.sub(r'%[sd]|{[0-9]+}', '{{VAR}}', cleaned_text)
    return cleaned_text, html_tags, variables

def reinsert_html_and_variables(text, html_tags, variables):
    """
    Re-inserts HTML tags and variables into a translated string.

    Args:
        text (str): The translated string.
        html_tags (list): List of HTML tags to re-insert.
        variables (list): List of variables to re-insert.

    Returns:
        str: The reconstructed string.
    """
    import re
    for tag in html_tags:
        text = re.sub(r'{{HTML}}', tag, text, count=1)
    for var in variables:
        text = re.sub(r'{{VAR}}', var, text, count=1)
    return text

def translate_string(text, target_lang='es', preserve_formatting=True, api='deepl'):
    """
    Translates a string while preserving HTML tags, variables, and code-like sections.

    Args:
        text (str): The string to translate.
        target_lang (str): Target language code (default: 'es').
        preserve_formatting (bool): Whether to preserve HTML/php syntax (default: True).
        api (str): Translation API to use ('deepl', 'deepseek', 'azure', 'google').

    Returns:
        str: The translated string.
    """
    if api == 'deepl':
        import deepl
        translator = deepl.Translator(os.getenv('DEEPL_API_KEY'))
        result = translator.translate_text(
            text,
            target_lang=target_lang,
            preserve_formatting=preserve_formatting
        )
        return result.text
    elif api == 'deepseek':
        # Initialize OpenAI client with DeepSeek's base URL
        client = OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com"
        )
        
        system_prompt = (
            "You are a professional translator. Your task is to translate text while preserving HTML tags, "
            "variables, and placeholders. Do not modify the structure of the text or any technical elements."
        )
        
        print(f"Translating: {text}")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Translate this text to {target_lang}: {text}"}
                    ],
                    temperature=1.3,  # Added recommended temperature for translations
                    stream=False
                )
                # Print raw response for debugging
                print(f"Raw API Response: {response}")
                return response.choices[0].message.content
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Failed after {max_retries} retries: {str(e)}")
                print(f"Retrying ({attempt + 1}/{max_retries})... Error: {str(e)}")
                time.sleep(2 ** attempt)
    elif api == 'azure':
        # Azure Translator logic
        pass
    elif api == 'google':
        try:
            client = translate_v3.TranslationServiceClient()
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
            if not project_id:
                raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is not set")
            
            parent = f"projects/{project_id}/locations/global"
            
            # Map language codes to Google's format if needed
            # Google uses ISO-639-1 language codes
            lang_mapping = {
                'es_ES': 'es',
                'en_US': 'en',
                'fr_FR': 'fr',
                # Add more mappings as needed
            }
            google_lang_code = lang_mapping.get(target_lang, target_lang.split('_')[0].lower())
            
            # Implement retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = client.translate_text(
                        contents=[text],
                        target_language_code=google_lang_code,
                        parent=parent,
                        mime_type="text/plain",  # Using plain text since we handle HTML tags separately
                        source_language_code="en"
                    )
                    
                    if response.translations:
                        translated_text = response.translations[0].translated_text
                        print(f"Translated: {text} -> {translated_text}")
                        return translated_text
                    else:
                        raise Exception("No translation returned from Google API")
                        
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise Exception(f"Failed after {max_retries} retries: {str(e)}")
                    print(f"Retrying ({attempt + 1}/{max_retries})... Error: {str(e)}")
                    time.sleep(2 ** attempt)
                    
        except Exception as e:
            logger.error(f"Google Translation error: {str(e)}")
            raise
    else:
        raise ValueError(f"Unsupported API: {api}")

    return text

def translate_bulk(strings, target_lang='es', api='deepseek'):
    """
    Translates a batch of strings using the DeepSeek Chat API.

    Args:
        strings (list): List of strings to translate.
        target_lang (str): Target language code (default: 'es').
        api (str): Translation API to use ('deepseek').

    Returns:
        list: List of translated strings.
    """
    headers = {
        'Authorization': f'Bearer {os.getenv("DEEPSEEK_API_KEY")}',
        'Content-Type': 'application/json'
    }
    prompt = (
        "You are a professional translator. Translate the following strings to {target_lang} while "
        "preserving HTML tags, variables, and placeholders. Do not modify the structure of the text. "
        "Here are the strings to translate:\n\n{text}"
    ).format(target_lang=target_lang, text='\n'.join(strings))
    data = {
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}]
    }
    response = requests.post(
        'https://api.deepseek.com/v1/chat/completions',
        headers=headers,
        json=data
    )
    if response.status_code == 200:
        translated_text = response.json()['choices'][0]['message']['content']
        return translated_text.split('\n')
    else:
        raise Exception(f"DeepSeek API Error: {response.status_code} - {response.text}")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Translate PO file using multiple translation APIs')
    parser.add_argument('input_file', help='Input PO file path')
    parser.add_argument('output_file', help='Output PO file path')
    parser.add_argument('--api', choices=['deepl', 'deepseek', 'azure', 'google'], default='deepl',
                      help='Translation API to use (default: deepl)')
    parser.add_argument('--target-lang', default='es',
                      help='Target language code (default: es)')
    args = parser.parse_args()

    # Load API keys from environment
    load_dotenv()

    # Read and parse PO file
    po = polib.pofile(args.input_file)
    
    # Get all untranslated entries
    untranslated = po.untranslated_entries()
    logger.info(f"Found {len(untranslated)} untranslated entries")
    
    # Process all untranslated entries
    for entry in tqdm(untranslated, desc="Translating"):
        try:
            entry.msgstr = translate_string(entry.msgid, args.target_lang, api=args.api)
            # Add a small delay to avoid hitting rate limits
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Error translating '{entry.msgid}': {str(e)}")
            continue

    # Save translated file
    po.save(args.output_file)
    logger.info(f"Translation complete. Saved to {args.output_file}")

if __name__ == '__main__':
    main()