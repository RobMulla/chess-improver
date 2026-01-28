import os

import pytest
from jinja2 import Environment, FileSystemLoader


def test_templates_syntax():
    """
    Traverse the templates directory and try to parse every .html file
    using Jinja2 environment. This catches basic syntax errors.
    """
    templates_dir = os.path.join(os.path.dirname(__file__), "../src/web/templates")
    env = Environment(loader=FileSystemLoader(templates_dir))

    # List of known templates to check
    # Or generically walk the directory
    for root, _, files in os.walk(templates_dir):
        for file in files:
            if file.endswith(".html"):
                # Get relative path for template loader
                rel_path = os.path.relpath(os.path.join(root, file), templates_dir)
                print(f"Checking template: {rel_path}")
                try:
                    # Just loading the template forces parsing
                    env.get_template(rel_path)
                except Exception as e:
                    pytest.fail(f"Syntax error in template {rel_path}: {e}")
