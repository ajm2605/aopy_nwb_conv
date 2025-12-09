# Package Components Specification

## 1. Core Architecture

### DataLocator
- Traverses folder structure to identify relevant HDF5 files for a session/day
- Parses folder hierarchy to extract metadata (subject ID, date, session info)
- Returns organized file manifest with metadata annotations
- Handles both single-session and full-day batch modes

### MetadataExtractor
- Extracts subject information from folder structure/filenames
- Parses electrode configuration data
- Extracts experimental protocol/task metadata
- Validates required metadata fields are present
- Outputs standardized metadata dictionary for NWB construction

### HDF5Reader
- Loads data from different HDF5 file types (neural, kinematic, eye tracking, task)
- Handles lazy loading for large files (100GB+)
- Provides unified interface despite varying HDF5 internal structures
- Manages memory efficiently with chunked reading

### NWBBuilder
- Constructs NWB file structure with proper hierarchy
- Creates NWBFile object with session metadata
- Populates device and electrode group information
- Adds processing modules for different data types

### DataConverter (multiple specialized converters)
- **ElectrophysiologyConverter**: Maps spike times, LFP, broadband to ElectricalSeries
- **KinematicConverter**: Maps hand position to SpatialSeries
- **EyeTrackingConverter**: Maps eye data to SpatialSeries
- **BehavioralConverter**: Maps task variables to TimeSeries/behavioral modules
- Each handles unit conversions and ensures NWB compliance

### TimeAlignmentValidator
- Verifies timing consistency across data streams (since your HDF5 already has resolved timing)
- Checks for gaps or misalignments
- Logs any timing warnings for user review

### NWBWriter
- Writes populated NWB object to disk
- Handles compression settings
- Manages iterative writing for large datasets to avoid memory issues
- Provides progress tracking for long conversions

---

## 2. Utility Components

### ConfigManager
- Loads conversion configuration (file paths, naming conventions, NWB parameters)
- Allows user customization without code changes
- Stores mapping rules (e.g., which HDF5 field → which NWB field)

### Logger
- Tracks conversion progress
- Records warnings/errors
- Generates conversion summary report

### BatchProcessor
- Orchestrates conversion of multiple sessions
- Handles parallelization if needed
- Aggregates logs across batch

---

## 3. Entry Points

### `convert_session()`
- Main function for single session conversion
- **Input**: session folder path or date/subject identifiers
- **Output**: NWB file path

### `convert_day()`
- Converts all sessions from a single day into one or multiple NWB files
- Handles decision logic for single vs. multi-file output

### `convert_batch()`
- Processes multiple days/sessions from a list
- Generates batch report

---

## 4. Future Extension Points

### BinaryReader (placeholder for Phase 2)
- Will replace HDF5Reader for raw binary processing
- Will handle timing synchronization logic

### Validator (placeholder)
- NWB file validation against schema
- Data integrity checks (value ranges, completeness)

---

## 5. Suggested Project Structure

```
nwb_converter/
├── core/
│   ├── data_locator.py
│   ├── metadata_extractor.py
│   ├── hdf5_reader.py
│   ├── nwb_builder.py
│   └── nwb_writer.py
├── converters/
│   ├── base_converter.py
│   ├── electrophysiology.py
│   ├── kinematics.py
│   ├── eye_tracking.py
│   └── behavioral.py
├── utils/
│   ├── config.py
│   ├── logger.py
│   └── time_alignment.py
├── batch/
│   └── batch_processor.py
├── api.py  # (convert_session, convert_day, convert_batch)
└── config/
    └── default_config.yaml
```

---

## 6. Key Design Decisions to Consider

- **Single file per day vs. per session**: Will sessions from the same day be analyzed together? Single file is cleaner but larger.
- **Memory management**: With 100GB files, you'll need chunked reading/writing. PyNWB supports iterative writes.
- **Error handling**: Should a failed session stop the batch, or skip and continue?
- **Incremental conversion**: Can you convert existing HDF5→NWB while simultaneously working toward binary→NWB, or full replacement?