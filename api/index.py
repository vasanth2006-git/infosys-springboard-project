import sys
import os

# Ensure the root directory of the project is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Expose the FastAPI application object for Vercel Serverless Function runtime
from main import app
