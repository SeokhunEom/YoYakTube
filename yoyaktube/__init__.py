"""YoYakTube internal package."""

# Import core modules that don't require streamlit
from . import constants, i18n, config, utils, transcript, llm

# Conditionally import streamlit-dependent modules
try:
    from . import state, ui
    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False

"""YoYakTube package.

Modularized components for readability, maintainability, and extensibility.
"""

__all__ = []
