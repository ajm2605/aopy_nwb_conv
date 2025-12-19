import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from aopy_nwb_conv.utils.cache import (
    get_cached_files,
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

def extract_date_from_string(
    file_name: str,
    date_regex,
    date_format: str="%Y%m%d") -> datetime:
    """
    Extract date from a filename using a regular expression pattern.

    Args:
        file_name: The filename or path to search for a date string
        date_regex: Compiled regular expression pattern to match the date string
        date_format: Format string for parsing the matched date (default: "%Y%m%d")
                    Common formats:
                    - "%Y%m%d" for YYYYMMDD (e.g., 20231215)
                    - "%Y-%m-%d" for YYYY-MM-DD (e.g., 2023-12-15)
                    - "%m/%d/%Y" for MM/DD/YYYY (e.g., 12/15/2023)

    Returns:
        datetime: Parsed datetime object if a valid date is found
        None: If no date pattern is matched or parsing fails

    Examples:
        >>> import re
        >>> pattern = re.compile(r'\\d{8}')
        >>> extract_date_from_string("subject123_20231215.hdf", pattern)
        datetime.datetime(2023, 12, 15, 0, 0)

        >>> pattern = re.compile(r'\\d{4}-\\d{2}-\\d{2}')
        >>> extract_date_from_string("data_2023-12-15.csv", pattern, "%Y-%m-%d")
        datetime.datetime(2023, 12, 15, 0, 0)
    """
    print('Using hte normal extract_date_from_string function')
    match = date_regex.search(file_name)
    if match:
        date_str = match.group()
        return datetime.strptime(date_str, date_format)
    else:
        return None


def get_valid_preprocessed_dates(
    preprocessed_path,
    subject_id: str,
    max: Optional[int] = None,
    force_refresh: bool = False):
    """Get valid dates for a given subject."""
    date_format = Config().get_date_format()
    date_regex = define_date_regex(date_format)

    file_paths = get_cached_files(
        preprocessed_path,
        extension="hdf",
        max=max,
        force_refresh=force_refresh)

    files_with_dates = []
    for path in file_paths:
        file_name = Path(path).name
        extracted_date = extract_date_from_string(file_name, date_regex, date_format)
        if extracted_date:
            files_with_dates.append((path, extracted_date))
    return files_with_dates
