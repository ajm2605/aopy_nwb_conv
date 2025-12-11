
"""
Module for data location and management.
What do I want this to do? I want it to locate all relevant
data to a given session or a given day. I will need to 
specify 

config: 
    data dir: root data directories
    subject ID: to identify the subject
"""
from pathlib import Path

from aopy_nwb_conv.utils.config import Config

def get_valid_preprocessed_dates(preprocessed_path, subject_id: str):
    """Get valid dates for a given subject."""
    folders = [Path(f) for f in preprocessed_path.glob(subject_id) if f.is_dir()]
    return folders

def data_locator():
    """Module for data location and management."""
    print('TODO: Implement data locator functionality.')
