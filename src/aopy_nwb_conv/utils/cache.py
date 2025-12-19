import pickle
import tempfile
from pathlib import Path
from typing import Optional, Union

from aopy_nwb_conv.utils.config import Config

_cached_files = {}
_cache_loaded = {}

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

def find_file_ext(directory: Path, extension: str, max: int = None):
    """Find all files with a specific extension"""
    directory = Path(directory)
    results = []

    # Remove leading dot if present
    extension = extension.lstrip('.')

    for file_path in directory.rglob(f'*.{extension}'):
        if file_path.is_file():
            results.append(str(file_path))

        if max is not None and len(results) >= max:
            break

    return results

def cache_files_by_extension(
    directory: Path,
    extension: str = "hdf",
    max: int = None,
    cache_path: Path = None,
    force_refresh: bool = False

):
    """
    Cache files with a specific extension in a directory.

    Args:
        directory: Directory to search
        extension: File extension to search for (without dot)
        cache_path: Optional custom cache path (if None, uses temp directory)
        force_refresh: If True, regenerate cache even if it exists

    Returns:
        List of file paths as strings
    """
    directory = Path(directory)
    extension = extension.lstrip('.')

    # Create cache key for this directory/extension combo
    cache_key = f"{directory}_{extension}"

    # Check if already loaded in memory this session
    if cache_key in _cached_files and not force_refresh:
        print(f"✓ Using in-memory cache ({len(_cached_files[cache_key])} files)")
        return _cached_files[cache_key]

    # Determine cache file path
    if cache_path is None:
        cache_path = get_temp_cache_path(f"file_cache_{extension}.pkl")
    else:
        cache_path = Path(cache_path)

    # Try to load from pickle file (persistent cache)
    if not force_refresh:
        cached_files = load_cache_pickle(cache_path)
        if cached_files:
            print(f"✓ Loaded {len(cached_files)} .{extension} files from disk cache")
            _cached_files[cache_key] = cached_files
            _cache_loaded[cache_key] = True
            return cached_files

    # Generate new cache by scanning directory
    print(f"⟳ Scanning for .{extension} files in {directory}...")
    cached_files = find_file_ext(directory, extension, max)

    # Save to disk (persistent)
    save_cache_pickle(cached_files, cache_path)

    # Save to memory (fast access this session)
    _cached_files[cache_key] = cached_files
    _cache_loaded[cache_key] = True

    print(f"✓ Cached {len(cached_files)} .{extension} files")

    return cached_files


def get_cached_files(directory: Optional[Union[Path, str]] = None, extension: str = "hdf", max = None, force_refresh: bool = False):
    """
    Get cached files (loads if not already cached).

    Args:
        directory: Directory to search. If None, uses config path based on extension.
        extension: File extension to search for (default: "hdf")

    Returns:
        List of file paths as strings

    Examples:
        # Use config path for HDF files
        hdf_files = get_cached_files(extension="hdf")

        # Use config path for NWB files
        nwb_files = get_cached_files(extension="nwb")

        # Use custom path
        hdf_files = get_cached_files("/custom/path", "hdf")
    """
    if directory is None:
        config = Config()
        paths = config.get_paths()

        # Map extensions to config keys
        if extension == 'hdf':
            directory = paths['monkey_preprocessing']
        elif extension == 'nwb':
            directory = paths['nwb_output']
        else:
            raise ValueError(
                f"No default config path for extension '{extension}'. "
                f"Supported extensions: 'hdf', 'nwb'. "
                f"Please provide directory explicitly."
            )

        print(f"Using config path for .{extension}: {directory}")

    return cache_files_by_extension(directory, extension, max=max, force_refresh=force_refresh)


def clear_cache(extension: str = None):
    """
    Clear the in-memory cache.

    Args:
        extension: If provided, only clear cache for this extension.
                  If None, clear all caches.
    """
    global _cached_files, _cache_loaded

    if extension:
        # Clear specific extension
        keys_to_remove = [k for k in _cached_files.keys() if k.endswith(f"_{extension}")]
        for key in keys_to_remove:
            _cached_files.pop(key, None)
            _cache_loaded.pop(key, None)
        print(f"Cleared cache for .{extension} files")
    else:
        # Clear all
        _cached_files.clear()
        _cache_loaded.clear()
        print("Cleared all caches")
