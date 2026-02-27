import numpy as np
import tempfile
from pathlib import Path
from aopy_nwb_conv.utils.config import Config

def write_array_to_temp_binary(data: np.ndarray) -> Path:
    """
    Write a numpy array to a temporary binary file.
    
    Args:
        data: Numpy array to write to binary file
        
    Returns:
        Path: Path to the temporary binary file
        
    Example:
        >>> data = np.array([[1, 2, 3], [4, 5, 6]])
        >>> temp_file = write_array_to_temp_binary(data)
        >>> # Use with spikeinterface
        >>> recording = se.read_binary(temp_file, ...)
    """
    # Create a temporary file that won't be automatically deleted
    temp_file = tempfile.NamedTemporaryFile( 
        delete=False,
        dir=Config().get_paths()['data_root'] /'tmp',
        suffix='.bin')

    temp_path = Path(temp_file.name)
    temp_file.close()
    
    # Write the numpy array to the binary file
    data.tofile(temp_path)
    
    return temp_path