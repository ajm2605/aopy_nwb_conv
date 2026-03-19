from aopy_nwb_conv.utils.config import Config
from aopy_nwb_conv.utils.date_validation import default_extract_date_from_string
from aopy_nwb_conv.utils.file_utils import write_array_to_temp_binary
from pathlib import Path
from typing import Dict, List
from aopy.data.bmi3d import load_ecube_metadata
from aopy.data.base import load_preproc_broadband_data, load_preproc_lfp_data, load_preproc_eye_data
import numpy as np
from datetime import datetime
import os

import spikeinterface.extractors as se
from neuroconv.tools import spikeinterface as nwb_si
import aopy
from pynwb import NWBFile, NWBHDF5IO
from pynwb.behavior import SpatialSeries, Position
from aopy.data.bmi3d import get_kinematics
#(preproc_dir, subject, te_id, date, cached=True)
#from aopy.data.bmi3d import load_ecube_metadata
#What is it that I want ot accomplish here? What is the minimum that I want? I want to give a function a teid for 
#a session and get back an NWB file. I'm fine with it being built from the preprocessed files.

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
#def get_probe_info(probe_id):
#    probe_paths = Config().get('')
    
def get_probe_info(entry):
    if entry.subject=='churro':
        return 'churro_fma'
    elif entry.subject=='beignet':
        return 'beignet_ecog'
    else:
        raise NotImplementedError("Only churro, beignet probes are implemented currently")

def add_spatial_series_to_nwbfile(nwbfile, spatial_series):
    # Check if behavior module exists
    if 'behavior' in nwbfile.processing:
        behavior_module = nwbfile.processing['behavior']
        # Check if Position container exists within behavior module
        if 'Position' in behavior_module.data_interfaces:
            position = behavior_module.data_interfaces['Position']
            position.add_spatial_series(spatial_series)
        else:
            # Position doesn't exist, create it
            position = Position(spatial_series=spatial_series)
            behavior_module.add(position)
    else:
        # Behavior module doesn't exist, create it
        behavior_module = nwbfile.create_processing_module(
            name='behavior',
            description='Behavioral data'
        )
        position = Position(spatial_series=spatial_series)
        behavior_module.add(position)

def add_aopy_eye_to_nwbfile(nwbfile, entry):
    eye_data, eye_metadata = load_preproc_eye_data(Config().get_paths()['monkey_preprocessed'], entry.subject, entry.id, entry.date)
    ts = np.arange(eye_data['raw_data'].shape[0]) / eye_metadata['samplerate']

    
    #position_data = np.random.rand(1000, 2)  # Replace with your actual data
    #timestamps = np.linspace(0, 100, 1000)   # Replace with your actual timestamps

    spatial_series = SpatialSeries(
        name='eye_position',  # or whatever name you want
        description='Position of eye in arena',
        data=eye_data['raw_data'][:, :2],  # shape should be (n_samples, 2) for x and y
        timestamps=ts,
        reference_frame='???',
        unit='cm?? V?'  # or 'pixels', 'cm', etc.
    )
    add_spatial_series_to_nwbfile(nwbfile, spatial_series)
    
def add_aopy_kin_to_nwbfile(nwbfile, entry, datatype='cursor'):
    
    kin_data = get_kinematics(Config().get_paths()['monkey_preprocessed'], entry.subject, entry.id, entry.date, 1000, datatype='cursor')
    kin_out = kin_data[0]

    print(datatype)
    print(kin_data[0].shape)
    ts = np.arange(np.shape(kin_data[0])[0]) / kin_data[1]

    
    #position_data = np.random.rand(1000, 2)  # Replace with your actual data
    #timestamps = np.linspace(0, 100, 1000)   # Replace with your actual timestamps

    spatial_series = SpatialSeries(
        name=datatype,  # or whatever name you want
        description= datatype,
        data=kin_out,  # shape should be (n_samples, 2) for x and y
        timestamps=ts,
        reference_frame='???',
        unit='cm'  # or 'pixels', 'cm', etc.
    )
    add_spatial_series_to_nwbfile(nwbfile, spatial_series)

def add_aopy_ephys_to_nwbfile(nwbfile, entry, prb, datatype='broadband'):
    #Load broadband data

    [_, exp_metadata] = aopy.data.base.load_preproc_exp_data(Config().get_paths()['monkey_preprocessed'], entry.subject, entry.id, entry.date) 
    if datatype=='broadband':
        [data, metadata] = load_preproc_broadband_data(Config().get_paths()['monkey_preprocessed'], entry.subject, entry.id, entry.date)
        sampling_frequency = metadata['samplerate']
    elif datatype=='lfp':
        [data, metadata] = load_preproc_lfp_data(Config().get_paths()['monkey_preprocessed'], entry.subject, entry.id, entry.date)
        sampling_frequency = metadata['lfp_samplerate']
        print(f"Loaded LFP data with shape {data.shape} and sampling frequency {sampling_frequency}")
    elif datatype=='ap':
        [data, metadata] = load_preproc_ap_data(Config().get_paths()['monkey_preprocessed'], entry.subject, entry.id, entry.date)
        sampling_frequency = metadata['ap_samplerate']
    else:
        raise ValueError(f"Datatype {datatype} not recognized for ephys data loading")

    #if entry

    if exp_metadata['drmap_drive_type']=='ECoG244':
        #Ecog data, lets correctly remap acq channels
        elec_pos, acq_ch, elecs = aopy.data.load_chmap(drive_type='ECoG244')
        data = data[:, acq_ch-1]

    #Loading relevant info to make a spikeinterface recording
    
    num_channels = np.shape(data)[1]#
    dtype=data.dtype
    volts_per_bit = metadata['voltsperbit']

    data = data * volts_per_bit
    #write out broadband to a temp binary file
    tmp_bin = write_array_to_temp_binary(data)
    
    #Load broadband into spikeinterface recording
    try:
        recording = se.read_binary(
            tmp_bin, 
            sampling_frequency=sampling_frequency, 
            dtype=dtype, 
            num_channels=num_channels, 
            gain_to_uV=volts_per_bit,
        )

        #Set probe info and recording properties
        recording = recording.set_probegroup(prb)
        #recording.set_channel_gains(volts_per_bit)
        #recording.set_channel_offsets(0)

        #Now add the recording to the NWB file
        if 'experimenter' in exp_metadata.keys():
            experimenter = exp_metadata['experimenter']
        else:
            experimenter = 'Unknown'

        recording_metadata = {
            'Ecephys': {
                'ElectricalSeries': {
                    'name': experimenter,
                    'description': f"{datatype} data recorded from the Ecube System"
                }
            }
        }

        nwb_si.add_recording_to_nwbfile(
            recording=recording,
            nwbfile=nwbfile,
            metadata=recording_metadata,
            write_as='raw',
        )
    finally:
        os.remove(tmp_bin)

def convert_aopy_to_nwb(entry, ephys_datatype='lfp', overwrite=False,output_path=None, preproc=True):   

    assert preproc==True, "Only preprocessed conversion is implemented currently"
    
    sources = entry.get_preprocessed_sources()
    assert ephys_datatype in sources, f"Requested ephys datatype {ephys_datatype} not found in preprocessed sources for this session"

    preproc_dir = Config().get_paths()['monkey_preprocessed']
    #Generate correct output path  
    if output_path is None:
        config = Config()
        assert config is not None, "Config could not be loaded"
        output_path = config.get_paths()['data_output']
        
    output_path.mkdir(parents=True, exist_ok=True)
    output_path = output_path / f"{entry.subject}_{entry.id}.nwb"
    
    if output_path.exists() and not overwrite:
        print(f"Skipping conversion for {entry.subject}_{entry.id} because output file exists and overwrite is False")
        return output_path
    #Before we can make an empty file, we need a few things:
    #1. Probe info
    probe_id = get_probe_info(entry)
    prb = config.get_probes()[probe_id]
    
    #Load Experiment data
    exp_data, exp_metadata = aopy.data.load_preproc_exp_data(preproc_dir, entry.subject, entry.id, entry.date)
    
    session_start_time = datetime.strptime(exp_metadata['date'], '%Y-%m-%d %H:%M:%S.%f')


    #Create empty NWB file:
    nwbfile = NWBFile(
        session_description=entry.task_name,  # required
        identifier=str(entry.id),  # required
        session_start_time=session_start_time,  # required
        experimenter=[
            "Pull form HDF File",
        ],  # optional
        lab="Orsborn Lab",  # optional
        institution="University of Washington",  # optional
        experiment_description=entry.task_name,  # optional
    )
    

    add_aopy_ephys_to_nwbfile(nwbfile, entry, prb, datatype=ephys_datatype)
    if 'eye' in sources:
        add_aopy_eye_to_nwbfile(nwbfile, entry)
    if 'cursor_interp' in exp_data.keys():
        add_aopy_kin_to_nwbfile(nwbfile, entry, datatype='cursor')
    if 'hand_interp' in exp_data.keys():
        add_aopy_kin_to_nwbfile(nwbfile, entry, datatype='hand')

    if entry.task_name=='manual control':
        df = aopy.data.bmi3d.tabulate_behavior_data_center_out(Config().get_paths()['monkey_preprocessed'], [entry.subject], [entry.id], [entry.date])

        for r in df.itertuples():
            nwbfile.add_trial(r.prev_trial_end_time, r.trial_end_time)

        for col in df.columns:
            if df[col].dtype != object:
                nwbfile.add_trial_column(col, col, df[col].values)

    print('made it this far')
    with NWBHDF5IO(output_path, "w") as io:
        io.write(nwbfile)


    #nwb_si.write_recording_to_nwbfile(recording=recording, nwbfile_path=output_path, metadata=metadata )
    return output_path
    #3. Num channels
    #4. dtype
    #5. Metadata stuff

    
    #First, lets create the empty NWB file

    #Lets start with the ecube raw data
    #Now, lets figure out where all the data is:
    

