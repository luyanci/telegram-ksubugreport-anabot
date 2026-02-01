import os
import json
import logging

logger = logging.getLogger(__name__)

langs = {}

for file in os.listdir('locale'):
    if file.endswith('.json'):
        lang_code = file[:-5]
        with open(os.path.join('locale', file), 'r', encoding='utf-8') as f:
            try:
                langs[lang_code] = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from {file}: {e}")