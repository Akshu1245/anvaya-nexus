"""
Vercel Python serverless entry point.
Wraps the Flask app for the Vercel Python runtime.
"""
import sys
import os

# Add the project root to the path so 'backend' package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.anvaya import create_app

# Vercel looks for a variable named `app` (WSGI callable)
app = create_app()

# Required by Vercel Python runtime
handler = app
