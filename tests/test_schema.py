import json
import jsonschema


def test_sample_schema():
    schema = json.load(open('questions/schema.json'))
    sample = json.load(open('generated_questions/sample.json'))
    jsonschema.validate(sample, schema)
