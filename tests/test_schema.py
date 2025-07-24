import json
from pathlib import Path
from jsonschema import validate

SCHEMA_PATH = Path('questions/schema.json')

def test_sample_schema():
    with SCHEMA_PATH.open() as f:
        schema = json.load(f)
    item_schema = schema['properties']['questions']['items']
    sample = {
        'text': 'Sample?',
        'options': ['a', 'b'],
        'correct_index': 0,
        'category': '論理',
        'difficulty': 'easy',
        'irt': {'a': 1.0, 'b': 0.0}
    }
    validate(sample, item_schema)
