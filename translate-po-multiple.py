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
import re
import hashlib
import pickle
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Dict, Optional
from openai import OpenAI
from google.cloud import translate_v3

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Compile regex patterns for better performance
HTML_TAG_PATTERN = re.compile(r'<[^>]+>')
VARIABLE_PATTERN = re.compile(r'%[sd]|{[0-9]+}')
HTML_PLACEHOLDER = '{{HTML}}'
VAR_PLACEHOLDER = '{{VAR}}'

# Cache directory
CACHE_DIR = Path('.translation_cache')
CACHE_DIR.mkdir(exist_ok=True)

def get_cache_key(text: str, target_lang: str, api: str) -> str:
    """Generate a unique cache key for a translation."""
    content = f"{text}|{target_lang}|{api}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def get_cached_translation(text: str, target_lang: str, api: str) -> Optional[str]:
    """Retrieve cached translation if available."""
    cache_key = get_cache_key(text, target_lang, api)
    cache_file = CACHE_DIR / f"{cache_key}.pkl"

    if cache_file.exists():
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return None
    return None

def save_to_cache(text: str, target_lang: str, api: str, translation: str):
    """Save translation to cache."""
    cache_key = get_cache_key(text, target_lang, api)
    cache_file = CACHE_DIR / f"{cache_key}.pkl"

    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(translation, f)
    except Exception as e:
        logger.warning(f"Failed to save to cache: {e}")

def isolate_html_and_variables(text: str) -> Tuple[str, List[str], List[str]]:
    """
    Isolates HTML tags and variables from a string using compiled regex patterns.

    Args:
        text (str): The string to process.

    Returns:
        tuple: (cleaned_text, html_tags, variables)
    """
    html_tags = HTML_TAG_PATTERN.findall(text)
    variables = VARIABLE_PATTERN.findall(text)
    cleaned_text = HTML_TAG_PATTERN.sub(HTML_PLACEHOLDER, text)
    cleaned_text = VARIABLE_PATTERN.sub(VAR_PLACEHOLDER, cleaned_text)
    return cleaned_text, html_tags, variables

def reinsert_html_and_variables(text: str, html_tags: List[str], variables: List[str]) -> str:
    """
    Re-inserts HTML tags and variables into a translated string.

    Args:
        text (str): The translated string.
        html_tags (list): List of HTML tags to re-insert.
        variables (list): List of variables to re-insert.

    Returns:
        str: The reconstructed string.
    """
    for tag in html_tags:
        text = text.replace(HTML_PLACEHOLDER, tag, 1)
    for var in variables:
        text = text.replace(VAR_PLACEHOLDER, var, 1)
    return text

def translate_string(text: str, target_lang: str = 'es', preserve_formatting: bool = True, api: str = 'deepl', use_cache: bool = True) -> str:
    """
    Translates a string while preserving HTML tags, variables, and code-like sections.

    Args:
        text (str): The string to translate.
        target_lang (str): Target language code (default: 'es').
        preserve_formatting (bool): Whether to preserve HTML/php syntax (default: True).
        api (str): Translation API to use ('deepl', 'deepseek', 'azure', 'google').
        use_cache (bool): Whether to use caching (default: True).

    Returns:
        str: The translated string.
    """
    # Check cache first
    if use_cache:
        cached = get_cached_translation(text, target_lang, api)
        if cached:
            logger.debug(f"Cache hit for: {text[:50]}...")
            return cached

    translated_text = None

    if api == 'deepl':
        import deepl
        translator = deepl.Translator(os.getenv('DEEPL_API_KEY'))
        result = translator.translate_text(
            text,
            target_lang=target_lang,
            preserve_formatting=preserve_formatting
        )
        translated_text = result.text
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
                translated_text = response.choices[0].message.content
                break
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
                        break
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

    # Save to cache before returning
    if translated_text and use_cache:
        save_to_cache(text, target_lang, api, translated_text)

    return translated_text if translated_text else text

def translate_batch(strings: List[str], target_lang: str = 'es', api: str = 'deepl', use_cache: bool = True) -> List[str]:
    """
    Translates a batch of strings using the specified API.

    Args:
        strings (list): List of strings to translate.
        target_lang (str): Target language code (default: 'es').
        api (str): Translation API to use ('deepl', 'deepseek', 'google').
        use_cache (bool): Whether to use caching (default: True).

    Returns:
        list: List of translated strings.
    """
    if api == 'deepl':
        import deepl
        translator = deepl.Translator(os.getenv('DEEPL_API_KEY'))

        # Separate cached and uncached strings
        results = [None] * len(strings)
        to_translate = []
        to_translate_indices = []

        for i, text in enumerate(strings):
            if use_cache:
                cached = get_cached_translation(text, target_lang, api)
                if cached:
                    results[i] = cached
                    continue
            to_translate.append(text)
            to_translate_indices.append(i)

        # Batch translate uncached strings
        if to_translate:
            try:
                translations = translator.translate_text(to_translate, target_lang=target_lang)
                for idx, translation in zip(to_translate_indices, translations):
                    translated = translation.text
                    results[idx] = translated
                    if use_cache:
                        save_to_cache(strings[idx], target_lang, api, translated)
            except Exception as e:
                logger.error(f"Batch translation error: {e}")
                # Fallback to individual translation
                for idx in to_translate_indices:
                    results[idx] = translate_string(strings[idx], target_lang, api=api, use_cache=use_cache)

        return results

    elif api == 'google':
        client = translate_v3.TranslationServiceClient()
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        parent = f"projects/{project_id}/locations/global"

        lang_mapping = {
            'es_ES': 'es', 'en_US': 'en', 'fr_FR': 'fr',
        }
        google_lang_code = lang_mapping.get(target_lang, target_lang.split('_')[0].lower())

        # Separate cached and uncached strings
        results = [None] * len(strings)
        to_translate = []
        to_translate_indices = []

        for i, text in enumerate(strings):
            if use_cache:
                cached = get_cached_translation(text, target_lang, api)
                if cached:
                    results[i] = cached
                    continue
            to_translate.append(text)
            to_translate_indices.append(i)

        # Batch translate (Google supports up to 100 items per request)
        if to_translate:
            batch_size = 100
            for batch_start in range(0, len(to_translate), batch_size):
                batch_end = min(batch_start + batch_size, len(to_translate))
                batch = to_translate[batch_start:batch_end]
                batch_indices = to_translate_indices[batch_start:batch_end]

                try:
                    response = client.translate_text(
                        contents=batch,
                        target_language_code=google_lang_code,
                        parent=parent,
                        mime_type="text/plain",
                        source_language_code="en"
                    )

                    for idx, translation in zip(batch_indices, response.translations):
                        translated = translation.translated_text
                        results[idx] = translated
                        if use_cache:
                            save_to_cache(strings[idx], target_lang, api, translated)
                except Exception as e:
                    logger.error(f"Batch translation error: {e}")
                    for idx in batch_indices:
                        results[idx] = translate_string(strings[idx], target_lang, api=api, use_cache=use_cache)

        return results

    else:
        # Fallback to individual translations for other APIs
        return [translate_string(s, target_lang, api=api, use_cache=use_cache) for s in strings]

def save_progress(output_file: str, translated_count: int):
    """Save translation progress to resume later."""
    progress_file = Path(output_file).with_suffix('.progress')
    try:
        with open(progress_file, 'w') as f:
            json.dump({'translated_count': translated_count}, f)
    except Exception as e:
        logger.warning(f"Failed to save progress: {e}")

def load_progress(output_file: str) -> int:
    """Load translation progress if available."""
    progress_file = Path(output_file).with_suffix('.progress')
    if progress_file.exists():
        try:
            with open(progress_file, 'r') as f:
                data = json.load(f)
                return data.get('translated_count', 0)
        except Exception as e:
            logger.warning(f"Failed to load progress: {e}")
    return 0

def translate_entry_wrapper(args_tuple):
    """Wrapper for parallel translation."""
    entry, target_lang, api, use_cache = args_tuple
    try:
        translation = translate_string(entry.msgid, target_lang, api=api, use_cache=use_cache)
        return (entry, translation, None)
    except Exception as e:
        return (entry, None, str(e))

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Translate PO file using multiple translation APIs')
    parser.add_argument('input_file', help='Input PO file path')
    parser.add_argument('output_file', help='Output PO file path')
    parser.add_argument('--api', choices=['deepl', 'deepseek', 'azure', 'google'], default='deepl',
                      help='Translation API to use (default: deepl)')
    parser.add_argument('--target-lang', default='es',
                      help='Target language code (default: es)')
    parser.add_argument('--batch-size', type=int, default=10,
                      help='Number of strings to translate in a batch (default: 10)')
    parser.add_argument('--parallel', type=int, default=1,
                      help='Number of parallel translation workers (default: 1)')
    parser.add_argument('--no-cache', action='store_true',
                      help='Disable translation caching')
    parser.add_argument('--resume', action='store_true',
                      help='Resume from previous progress')
    parser.add_argument('--delay', type=float, default=0.5,
                      help='Delay between translations in seconds (default: 0.5)')
    args = parser.parse_args()

    # Load API keys from environment
    load_dotenv()

    # Read and parse PO file
    po = polib.pofile(args.input_file)

    # Get all untranslated entries
    untranslated = po.untranslated_entries()
    logger.info(f"Found {len(untranslated)} untranslated entries")

    # Load progress if resuming
    start_index = 0
    if args.resume:
        start_index = load_progress(args.output_file)
        if start_index > 0:
            logger.info(f"Resuming from entry {start_index}")
            untranslated = untranslated[start_index:]

    use_cache = not args.no_cache

    # Use batch translation if batch_size > 1 and API supports it
    if args.batch_size > 1 and args.api in ['deepl', 'google']:
        logger.info(f"Using batch translation with batch size: {args.batch_size}")

        for batch_start in tqdm(range(0, len(untranslated), args.batch_size), desc="Translating batches"):
            batch_end = min(batch_start + args.batch_size, len(untranslated))
            batch = untranslated[batch_start:batch_end]

            try:
                msgids = [entry.msgid for entry in batch]
                translations = translate_batch(msgids, args.target_lang, api=args.api, use_cache=use_cache)

                for entry, translation in zip(batch, translations):
                    entry.msgstr = translation

                # Save progress periodically
                if (batch_start + args.batch_size) % 50 == 0:
                    po.save(args.output_file)
                    save_progress(args.output_file, start_index + batch_end)

                time.sleep(args.delay)

            except Exception as e:
                logger.error(f"Error in batch translation: {str(e)}")
                # Fallback to individual translation
                for entry in batch:
                    try:
                        entry.msgstr = translate_string(entry.msgid, args.target_lang, api=args.api, use_cache=use_cache)
                        time.sleep(args.delay)
                    except Exception as e2:
                        logger.error(f"Error translating '{entry.msgid}': {str(e2)}")
                        continue

    # Use parallel translation if parallel > 1
    elif args.parallel > 1:
        logger.info(f"Using {args.parallel} parallel workers")

        with ThreadPoolExecutor(max_workers=args.parallel) as executor:
            futures = []
            for entry in untranslated:
                future = executor.submit(translate_entry_wrapper, (entry, args.target_lang, args.api, use_cache))
                futures.append(future)

            completed = 0
            for future in tqdm(as_completed(futures), total=len(futures), desc="Translating"):
                entry, translation, error = future.result()
                if error:
                    logger.error(f"Error translating '{entry.msgid}': {error}")
                else:
                    entry.msgstr = translation

                completed += 1
                if completed % 50 == 0:
                    po.save(args.output_file)
                    save_progress(args.output_file, start_index + completed)

                time.sleep(args.delay / args.parallel)  # Adjust delay for parallel workers

    # Standard sequential translation
    else:
        for idx, entry in enumerate(tqdm(untranslated, desc="Translating")):
            try:
                entry.msgstr = translate_string(entry.msgid, args.target_lang, api=args.api, use_cache=use_cache)

                # Save progress periodically
                if (idx + 1) % 50 == 0:
                    po.save(args.output_file)
                    save_progress(args.output_file, start_index + idx + 1)

                time.sleep(args.delay)

            except Exception as e:
                logger.error(f"Error translating '{entry.msgid}': {str(e)}")
                continue

    # Save final translated file
    po.save(args.output_file)
    logger.info(f"Translation complete. Saved to {args.output_file}")

    # Clean up progress file
    progress_file = Path(args.output_file).with_suffix('.progress')
    if progress_file.exists():
        progress_file.unlink()

if __name__ == '__main__':
    main()