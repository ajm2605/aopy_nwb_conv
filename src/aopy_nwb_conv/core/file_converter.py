from aopy_nwb_conv.utils.config import Config
from pathlib import Path
from typing import Dict, List
from aopy.data.bmi3d import load_ecube_metadata
from aopy.data.base import load_preproc_broadband_data
#(preproc_dir, subject, te_id, date, cached=True)
#from aopy.data.bmi3d import load_ecube_metadata
#What is it that I want ot accomplish here? What is the minimum that I want? I want to give a function a teid for 
#a session and get back an NWB file. I'm fine with it being built from the preprocessed files.

@lru_cache(maxsize=2)
def load_hdf_data(file_path, data_name, data_group="/"):
    '''
    Clear cache when needed
    load_hdf_data.cache_clear()
    
    Load data from an hdf file as a numpy array (cached)

    Args:
        file_path (str or Path): full path to the hdf file
        data_name (str): table to load
        data_group (str, optional): from which group to load data
    
    Returns:
        ndarray: numpy array of data from hdf
    '''
    with h5py.File(str(file_path), 'r') as hdf:
        full_data_name = os.path.join(data_group, data_name).replace("\\", "/")
        
        if full_data_name not in hdf:
            raise ValueError(f'{full_data_name} not found in file {file_path}')
        
        _, data = _load_hdf_dataset(hdf[full_data_name], data_name)
    
    return np.array(data)



def parse_preproc_filename_substrings(filepath):
    substring_list = ['broadband', 'lfp', 'ap', 'exp', 'spike', 'eye']
    matches = [sub for sub in substring_list if sub in filepath.name]

    print(matches)
    assert len(matches)==1

    return(matches[0])


def parse_ecube_raw_files(folder_path: str) -> Dict[str, List[str]]:
    """Categorize files in a folder based on their filenames.
    
    Args:
        folder_path: Path to the folder containing files to categorize
        
    Returns:
        Dictionary with categories as keys and lists of full file paths as values.
        Categories: 'Analog', 'Digital', 'Headstone', 'Settings'
    """
    folder = Path(folder_path)
    
    # Initialize result dictionary
    categories = {
        'Analog': [],
        'Digital': [],
        'Headstage': [],
    }
    
    # Get all files in the folder
    for file_path in folder.iterdir():
        if file_path.is_file():
            filename = file_path.name.lower()
            full_path = str(file_path)
            
            # Check for Settings first (since it can contain other substrings)
            if 'settings' in filename:
                #categories['Settings'].append(full_path)
                continue
            # Then check other categories
            if 'analog' in filename:
                categories['Analog'].append(full_path)
            elif 'digital' in filename:
                categories['Digital'].append(full_path)
            elif 'headstage' in filename:
                categories['Headstage'].append(full_path)
    
    return categories


def raw_ecube_filepath_metadata(te_id):

    config = Config()
    assert config is not None, "Config could not be loaded"
    raw_root = config.get_paths()['monkey_raw'] / 'ecube'
    session_file = list(raw_root.glob(f"*{te_id}*"))
    print(session_file)
    if len(session_file)==0:
        raise FileNotFoundError(f"No raw ecube session found for TE ID {te_id}")
    elif len(session_file)>1:
        raise ValueError(f"Multiple raw ecube sessions found for TE ID {te_id}: {session_file}")
    
    parsed_paths =  parse_ecube_raw_files(session_file[0])
    
        # Build metadata dictionary for each category
    metadata = {}
    for key in parsed_paths.keys():
        metadata_dict = load_ecube_metadata(session_file[0], key)
        metadata_dict['file_paths'] = parsed_paths[key]  # Add the file paths
        metadata[key] = metadata_dict

    return(metadata)

def preproc_find_session_file_paths(subject, te_id):
    """This takes in a path that goes to a single session and
    returns a datastruct with the sorted paths of all binary/raw files"""

    config = Config()
    print(config)
    assert config is not None, "Config could not be loaded"
    preprocessed_path = config.get_paths()['monkey_preprocessed'] / subject
    session_file_paths = list(preprocessed_path.glob(f"*{te_id}*.hdf"))

    path_types = [parse_preproc_filename_substrings(file_path) for file_path in session_file_paths]
    session_file_paths_dict = dict(zip(path_types, session_file_paths))
    return(session_file_paths_dict)

def preproc_convert(subject, te_id):

    filepaths = find_session_file_paths(subject, te_id)
    
    #What do I need to make this happen?



#def convert_ecube_raw(te_id, output_path=None):
def get_probe_info(probe_id):
    probe_paths = Config().get('')
    


def convert_aopy_to_nwb(subject, te_id, probe_id, output_path, preproc=True):   

    #Generate correct output path  
    if output_path is None:
        config = Config()
        assert config is not None, "Config could not be loaded"
        output_path = config.get_paths()['data_output']
        
    output_path.mkdir(parents=True, exist_ok=True)
    output_path = output_path / f"{te_id}.nwb"
    
    #Before we can make an empty file, we need a few things:
    #1. Probe info
    prb = self.config.get_probes()[probe_id]
    
    #2. Sampling_frequency
    if preproc:
        filepaths = preproc_find_session_file_paths(subject, te_id)
    else:
        filepaths = raw_ecube_filepath_metadata(te_id)
    
    #3. Num channels
    #4. dtype
    #5. Metadata stuff

    
    #First, lets create the empty NWB file

    #Lets start with the ecube raw data
    #Now, lets figure out where all the data is:
    

