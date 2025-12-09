# README Structure for NWB Converter Project

# AOlab HDF5 to NWB Converter

A Python package for converting AOlab's proprietary HDF5 neurophysiology data to the Neurodata Without Borders (NWB) format.

## Overview

This converter enables AOlab members to transform their preprocessed experimental data into NWB format, facilitating:
- Use of open-source analysis tools (pynapple, NWBWidgets, etc.)
- Seamless data sharing with external collaborators
- Future-proof analysis pipelines portable across datasets
- Alignment with open science best practices

**Current Status**: Phase 1 - Converting preprocessed HDF5 files  
**Future**: Phase 2 - Direct conversion from raw binary acquisition files

## Features

- **Simple API**: Convert sessions with a single function call
- **Batch Processing**: Convert multiple sessions or entire days efficiently
- **Memory Efficient**: Handles large files (100GB+) with chunked reading/writing
- **Comprehensive Logging**: Track conversion progress and troubleshoot issues
- **Data Validation**: Automatic checks for timing consistency and data integrity
- **NWB Compliant**: Generates valid NWB 2.x files compatible with the entire NWB ecosystem

## Roadmap

### Phase 1 (Current)
- 🚧 Convert preprocessed HDF5 files
- 🚧 Support all major data modalities
- 🚧 Batch processing capabilities
- 🚧 Comprehensive documentation
- 🚧 Example notebooks

### Phase 2 (Future)
- ⬜ Direct binary file conversion
- ⬜ Real-time preprocessing pipeline
- ⬜ GUI for non-programmers
- ⬜ DANDI archive integration
- ⬜ Automated quality control

## First-Time Setup

### 1. Create your local configuration
```bash
# Copy the template
cp config/config.template.yaml config/config.yaml

# Edit with your paths
nano config/config.yaml  # or vim, code, etc.
```

Edit `config/config.yaml`:
```yaml
data:
  data_root: "/mnt/server/lab_data"  # Your mounted server path
  output_root: "/mnt/server/nwb_output"

logging:
  level: "INFO"
  log_dir: "logs"
```

### 2. Verify setup
```python
from aopy_nwb_conv.utils.config import get_config

config = get_config()
print(f"Data root: {config.data_root}")
```

## Usage

Now your code automatically uses the configured path:
```python
# No need to specify path!
from aopy_nwb_conv.core.data_locator import DataLocator

locator = DataLocator()  # Uses config.yaml
session = locator.locate_session("MonkeyA", "2024-03-15", "session_001")
```

Or override if needed:
```python
locator = DataLocator(data_root="/different/path")
```
<!-- 
## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Install from PyPI (when published)
```bash
pip install nwb-aolab-converter
```

### Install from source
```bash
git clone https://github.com/aolab/nwb-converter.git
cd nwb-converter
pip install -e .
```

### Dependencies
Key dependencies (automatically installed):
- pynwb >= 2.5.0
- h5py >= 3.8.0
- numpy >= 1.24.0
- pyyaml >= 6.0

## Quick Start

### Convert a Single Session

```python
from nwb_converter import convert_session

# Convert one session
nwb_file = convert_session(
    session_path="/data/MonkeyA/2024-03-15/session_001/",
    output_dir="/data/nwb_files/"
)

print(f"Conversion complete: {nwb_file}")
```

### Convert Multiple Sessions

```python
from nwb_converter import convert_batch

# Convert a batch of sessions
sessions = [
    "/data/MonkeyA/2024-03-15/session_001/",
    "/data/MonkeyA/2024-03-16/session_001/",
    "/data/MonkeyB/2024-03-15/session_001/"
]

convert_batch(
    session_list=sessions,
    output_dir="/data/nwb_files/",
    parallel=True
)
```

### Convert All Sessions from a Day

```python
from nwb_converter import convert_day

# Convert all sessions from one day
convert_day(
    day_path="/data/MonkeyA/2024-03-15/",
    output_dir="/data/nwb_files/"
)
```

## Data Requirements

### Folder Structure
Your data should be organized as:
```
data/
└── SubjectID/
    └── YYYY-MM-DD/
        └── session_XXX/
            ├── neural_data.h5
            ├── kinematics.h5
            ├── eyetracking.h5
            └── task_events.h5
```

### Supported Data Types
- **Electrophysiology**: Spike times, LFP, broadband signals
- **Kinematics**: Hand position, velocity (3D)
- **Eye Tracking**: Gaze coordinates (x, y)
- **Behavioral**: Task events, trial markers, state variables

## Configuration

### Using Default Settings
Most users can use the default configuration without modification:

```python
convert_session(session_path="/data/MonkeyA/2024-03-15/session_001/")
```

### Custom Configuration
Create a custom config file for advanced options:

```python
from nwb_converter import convert_session

convert_session(
    session_path="/data/MonkeyA/2024-03-15/session_001/",
    config_file="/path/to/custom_config.yaml"
)
```

Example `custom_config.yaml`:
```yaml
# NWB file settings
nwb:
  experimenter: "John Doe"
  lab: "AOlab"
  institution: "University Name"
  
# Compression settings
compression:
  enabled: true
  algorithm: "gzip"
  level: 4

# Data mapping
field_mapping:
  neural:
    spike_times: "sorted_units/timestamps"
    lfp: "continuous/lfp_data"
```

## Working with Converted Data

### Loading NWB Files

```python
import pynwb

# Read NWB file
with pynwb.NWBHDF5IO('session_001.nwb', 'r') as io:
    nwbfile = io.read()
    
    # Access spike times
    units = nwbfile.units
    spike_times = units['spike_times'][0]
    
    # Access kinematics
    position = nwbfile.processing['behavior']['position']
```

### Using with Analysis Tools

#### Pynapple Example
```python
import pynapple as nap

# Load data
data = nap.load_file('session_001.nwb')

# Access neural data
units = data['units']

# Compute tuning curves
tuning = nap.compute_1d_tuning_curves(
    units, 
    feature=position, 
    nb_bins=20
)
```

#### NWBWidgets Visualization
```python
from nwbwidgets import nwb2widget

# Interactive visualization
nwb2widget('session_001.nwb')
```

## Examples

See the [`examples/`](examples/) directory for detailed notebooks:

- **[01_basic_conversion.ipynb](examples/01_basic_conversion.ipynb)**: Simple single-session conversion
- **[02_batch_conversion.ipynb](examples/02_batch_conversion.ipynb)**: Converting multiple sessions
- **[03_custom_config.ipynb](examples/03_custom_config.ipynb)**: Using custom configurations
- **[04_working_with_nwb.ipynb](examples/04_working_with_nwb.ipynb)**: Analyzing converted data
- **[05_visualization.ipynb](examples/05_visualization.ipynb)**: Visualizing NWB data

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: HDF5 file not found`
```
Solution: Verify your folder structure matches the expected format.
Check that all required HDF5 files are present in the session folder.
```

**Issue**: `MemoryError during conversion`
```
Solution: Reduce chunk size in config or increase available RAM.
Try converting sessions one at a time instead of in batch.
```

**Issue**: `Timing validation warnings`
```
Solution: Review the conversion log for specific timing misalignments.
These are typically non-critical but should be documented.
```

### Validation

Validate your converted NWB files:

```python
from nwb_converter.utils import validate_nwb_file

# Check if file is valid
is_valid, messages = validate_nwb_file('session_001.nwb')

if is_valid:
    print("✓ NWB file is valid")
else:
    print("Issues found:")
    for msg in messages:
        print(f"  - {msg}")
```

### Logs

Conversion logs are saved to:
```
output_dir/logs/conversion_YYYYMMDD_HHMMSS.log
```

Check logs for detailed error messages and warnings.

## Documentation

Full documentation is available at: [https://aolab-nwb-converter.readthedocs.io](https://aolab-nwb-converter.readthedocs.io)

- [User Guide](docs/user_guide.md)
- [API Reference](docs/api_reference.md)
- [Configuration Options](docs/configuration.md)
- [Data Mapping](docs/data_mapping.md)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/aolab/nwb-converter.git
cd nwb-converter

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/
```

## Support

- **Issues**: Report bugs or request features on [GitHub Issues](https://github.com/aolab/nwb-converter/issues)
- **Questions**: Ask questions on [GitHub Discussions](https://github.com/aolab/nwb-converter/discussions)
- **Lab Contact**: [your-email@institution.edu](mailto:your-email@institution.edu)

## Citation

If you use this converter in your research, please cite:

```bibtex
@software{aolab_nwb_converter,
  author = {Your Name and AOlab Contributors},
  title = {AOlab HDF5 to NWB Converter},
  year = {2024},
  url = {https://github.com/aolab/nwb-converter}
}
```

Also cite the NWB format:
```bibtex
@article{ruebel2022neurodata,
  title={The Neurodata Without Borders ecosystem for neurophysiological data science},
  author={R{\"u}bel, Oliver and Tritt, Andrew and Ly, Ryan and others},
  journal={eLife},
  volume={11},
  pages={e78362},
  year={2022}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- NWB development team for creating the standard
- PyNWB developers for the excellent Python API
- AOlab members for testing and feedback
- [Any funding sources]

---

**Questions?** Open an issue or contact the development team!
```