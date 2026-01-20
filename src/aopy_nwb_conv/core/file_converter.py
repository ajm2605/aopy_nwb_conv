from aopy_nwb_conv.utils.config import Config

#What is it that I want ot accomplish here? What is the minimum that I want? I want to give a function a teid for 
#a session and get back an NWB file. I'm fine with it being built from the preprocessed files.


def parse_preproc_filename_substrings(filepath):
    substring_list = ['broadband', 'lfp', 'ap', 'exp', 'spike', 'eye']
    matches = [sub for sub in substring_list if sub in filepath.name]

    print(matches)
    assert len(matches)==1

    return(matches[0])

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
