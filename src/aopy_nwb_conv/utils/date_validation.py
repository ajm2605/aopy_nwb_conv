import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from aopy_nwb_conv.utils.cache import (
    find_file_ext, 
    get_cached_files,
    _cached_files,
    _cache_loaded,
    cache_files_by_extension,
    get_temp_cache_path, 
    load_cache_pickle, 
    save_cache_pickle
)

from aopy_nwb_conv.utils.config import Config

def define_date_regex(date_format: str) -> re.Pattern:
    """Define regex pattern based on date format."""
    if date_format == "%Y-%m-%d":
        pattern = r'\d{4}-\d{2}-\d{2}'
    elif date_format == "%Y%m%d":
        pattern = r'\d{8}'
    elif date_format == "%m-%d-%Y":
        pattern = r'\d{2}-\d{2}-\d{4}'
    elif date_format == "%d_%m_%Y":
        pattern = r'\d{2}_\d{2}_\d{4}'
    else:
        raise ValueError(f"Unsupported date format: {date_format}")

    return re.compile(pattern)

def extract_date_from_string(file_name: str, date_regex) -> datetime:
    """Extract date from string based on given format."""

    match = date_regex.search(file_name)
    if match:
        date_str = match.group()
        return datetime.strptime(date_str, date_format)
    else:
        return None


def get_valid_preprocessed_dates(preprocessed_path, subject_id: str):
    """Get valid dates for a given subject."""
    date_format = Config().get_date_format()
    date_regex = define_date_regex(date_format)

    file_paths = get_cached_files(preprocessed_path, extension="hdf")

    files_with_dates = []
    for path in file_paths:
        file_name = Path(path).name
        extracted_date = extract_date_from_string(file_name, date_regex)
        if extracted_date:
            files_with_dates.append((path, extracted_date))
    return files_with_dates
