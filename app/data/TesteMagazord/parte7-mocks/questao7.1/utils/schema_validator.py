import json
from jsonschema import validate

def validate_product_schema(instance, schema_path: str):
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    validate(instance=instance, schema=schema)
    return True