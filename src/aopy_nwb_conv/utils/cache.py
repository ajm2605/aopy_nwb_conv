from pathlib import Path
import re
from datetime import datetime
import pickle
import tempfile

from aopy_nwb_conv.utils.config import Config

def save_cache_pickle(cache, cache_path):
    """Save cache using pickle"""
    with open(cache_path, 'wb') as f:
        pickle.dump(cache, f, protocol=pickle.HIGHEST_PROTOCOL)

def load_cache_pickle(cache_path):
    """Load cache from pickle"""
    if not cache_path.exists():
        return {}
    try:
        with open(cache_path, 'rb') as f:
            return pickle.load(f)
    except (pickle.PickleError, EOFError, FileNotFoundError):
        return {}

def get_temp_cache_path(cache_name="file_date_cache.pkl"):
    """In /tmp - cleared on reboot"""
    cache_dir = Path(tempfile.gettempdir()) / 'aopy_nwb_conv_cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / cache_name