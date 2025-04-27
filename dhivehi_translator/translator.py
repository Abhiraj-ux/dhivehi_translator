from google.cloud import translate_v2 as translate
import os
from bs4 import BeautifulSoup

def translate_text(text, source_lang='auto', target_lang='en'):
    """
    Translate text between languages using Google Cloud Translation API.
    
    Args:
        text (str): Text to translate
        source_lang (str): Source language code (default: 'auto' for auto-detection)
        target_lang (str): Target language code (default: 'en' for English)
        
    Returns:
        str: Translated text
    """
    try:
        # Check if source and target languages are the same
        if source_lang == target_lang and source_lang != 'auto':
            return text  # Return the original text without translation
        
        # Create a client
        translate_client = translate.Client()
        
        # The source language can be explicitly specified or auto-detected
        if source_lang == 'auto':
            # Perform the translation
            result = translate_client.translate(
                text,
                target_language=target_lang
            )
        else:
            # Perform the translation with specified source language
            result = translate_client.translate(
                text,
                target_language=target_lang,
                source_language=source_lang
            )
        
        return result['translatedText']
    except Exception as e:
        return f"Translation error: {str(e)}"

def translate_content(content, source_lang='auto', target_lang='en'):
    """
    Translate a dictionary of content (title and paragraphs).
    
    Args:
        content (dict): Dictionary containing title and paragraphs
        source_lang (str): Source language code (default: 'auto' for auto-detection)
        target_lang (str): Target language code (default: 'en' for English)
        
    Returns:
        dict: Dictionary with translated title and paragraphs
    """
    if 'error' in content:
        return content
    
    translated_content = {
        'original_title': content['title'],
        'translated_title': translate_text(content['title'], source_lang, target_lang),
        'paragraphs': []
    }
    
    for paragraph in content['paragraphs']:
        translated_content['paragraphs'].append({
            'original': paragraph,
            'translated': translate_text(paragraph, source_lang, target_lang)
        })
    
    # If HTML content is present, translate HTML elements
    if 'html_elements' in content:
        translated_html = content['html']
        soup = BeautifulSoup(translated_html, 'html.parser')
        
        # Translate each HTML element
        translated_elements = []
        for element in content['html_elements']:
            translated_text = translate_text(element['text'], source_lang, target_lang)
            
            # Find the element in the soup by its ID
            html_element = soup.find(attrs={"data-translate-id": element['id']})
            if html_element:
                html_element.string = translated_text
            
            translated_elements.append({
                'id': element['id'],
                'original': element['text'],
                'translated': translated_text,
                'tag': element['tag']
            })
        
        translated_content['translated_html'] = str(soup)
        translated_content['translated_elements'] = translated_elements
    
    return translated_content