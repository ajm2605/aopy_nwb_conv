from pathlib import Path
import re
from datetime import datetime

def find_file_ext(directory: Path, extension: str = "hdf"):
    """Find and cache files with a specific extension in a directory."""
    directory = Path(directory)
    cached_files = []
    
    for file_path in directory.rglob(f'*.{extension}'):
        if file_path.is_file():
            cached_files.append(file_path)
    
    return cached_files


def cache_files_by_extension(directory: Path, extension: str = "hdf", cache_path: Path = None):
    """Cache files with a specific extension in a directory to a cache file."""

    directory = Path(directory)

    if cache_path is None:
        cache_path = get_temp_cache_path()
    #try: 
    
        #directory / f'file_cache_{extension}.pkl'
    
    cached_files = find_file_ext(directory, extension)
    
    with open(cache_path, 'wb') as f:
        pickle.dump(cached_files, f)
    
    return cached_files


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

def find_files_with_date(directory, date_format="%Y-%m-%d"):
    """
    Find all files that contain a date matching the specified format.
    
    Args:
        directory: Path to search
        date_format: Expected date format (default: YYYY-MM-DD)
    
    Returns:
        List of tuples: (file_path, extracted_date_string)
    """
    directory = Path(directory)
    results = []
    
    # Create regex pattern based on date format

    regex = define_date_regex(date_format)
    
    # Search all files recursively
    for file_path in directory.rglob('*'):
        if file_path.is_file():
            # Check if filename contains date pattern
            match = regex.search(file_path.name)
            if match:
                date_str = match.group()
                
                # Validate it's a real date
                try:
                    datetime.strptime(date_str, date_format)
                    results.append((file_path, date_str))
                except ValueError:
                    # Invalid date (e.g., 2023-13-45)
                    continue
    
    return results

def get_valid_preprocessed_dates(preprocessed_path, subject_id: str):
    """Get valid dates for a given subject."""
    date_format = Config().get_date_format()

    files_with_dates = find_files_with_date_parallel(preprocessed_path, date_format=date_format)
    
    return files_with_dates