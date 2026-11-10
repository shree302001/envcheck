"""Make the in-repo package importable without installing it."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))
