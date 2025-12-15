
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
import re
from datetime import datetime
import pickle
import tempfile

from aopy_nwb_conv.utils.config import Config

def data_locator():
    """Module for data location and management."""
    print('TODO: Implement data locator functionality.')
