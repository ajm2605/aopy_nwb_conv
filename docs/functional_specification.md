# Functional Specification: HDF5 to NWB Converter for AOlab

## 1. Background

### The Problem
The AOlab currently uses a proprietary processed data file structure with custom code for data manipulation and analysis. This approach presents several limitations:

- **Limited interoperability**: Proprietary formats restrict the ability to use existing open-source analysis tools and visualization software
- **Collaboration barriers**: Sharing data with external collaborators requires them to adopt lab-specific code and data structures
- **Future-proofing concerns**: Analysis pipelines developed for proprietary formats may not be portable to new data collection systems or other laboratory environments
- **Reinventing the wheel**: Time spent maintaining custom analysis code could be better spent on scientific questions

### The Solution
Transition to the Neurodata Without Borders (NWB) format—an open-source, community-driven standard for neurophysiology data. This conversion will:

- Enable use of the rich ecosystem of NWB-compatible analysis tools (e.g., pynapple, NWBWidgets, DANDI)
- Facilitate seamless data sharing with collaborators across institutions
- Create analysis pipelines that are portable across different datasets and acquisition systems
- Align the lab with best practices in open science and data standardization

### Project Scope
**Phase 1** (current): Convert already-preprocessed HDF5 files (time-aligned and filtered data) to NWB format

**Phase 2** (future): Extend the converter to work directly with raw binary files from acquisition systems, handling timing synchronization and preprocessing within the NWB pipeline

---

## 2. User Profile

### Primary Users
Members of the AOlab who need to convert their experimental data to NWB format for analysis or sharing.

### User Knowledge and Skills

**Domain Expertise:**
- Expert knowledge of their own experimental data (neural recordings, behavioral tasks, kinematic tracking)
- Familiar with the lab's current data organization and folder structure
- Understands the meaning of data streams (spike times, LFP, hand kinematics, eye tracking)

**Computing Skills:**
- Can navigate file systems and organize data folders
- Can run Python scripts from the command line or Jupyter notebooks
- Can install Python packages (e.g., `pip install`, managing virtual environments)
- May or may not have programming experience beyond running existing scripts

**NWB Knowledge:**
- **Little to no familiarity** with the NWB data specification
- May not understand NWB concepts like ElectricalSeries, SpatialSeries, or processing modules
- Should not need to read NWB documentation to successfully convert their data

### Design Implications
The converter must:
- Provide a simple, minimal API (e.g., `convert_session(data_path)`)
- Include comprehensive documentation with step-by-step examples
- Offer informative error messages and warnings
- Provide validation feedback to confirm successful conversion
- Include demonstration notebooks showing how to work with the resulting NWB files using popular tools (pynapple, NWBWidgets, etc.)

---

## 3. Data Sources

### Current Data Structure (Phase 1)

**Format:** HDF5 files containing preprocessed neurophysiology data

**Organization:**
- Data organized in a hierarchical folder structure: `subject/date/session/`
- Each session contains multiple HDF5 files for different data modalities:
  - Neural data (spike times, LFP, broadband signals)
  - Kinematic data (hand position, velocity)
  - Eye tracking data (gaze position)
  - Task/behavioral data (trial events, task variables)

**Data Characteristics:**
- Files can be very large (100GB+ for long sessions with many channels)
- Timing information is already synchronized across data streams within HDF5 files
- Metadata (subject ID, session date, electrode configuration) is embedded in folder names and file structures

**Data Streams:**
- **Electrophysiology**: Spike times (sorted units), LFP (local field potentials), broadband signals
- **Kinematics**: Hand position in 3D space, sampled at ~100-500 Hz
- **Eye tracking**: Gaze coordinates (x, y), sampled at ~240-1000 Hz
- **Behavioral**: Task events, trial markers, behavioral state variables

### Future Data Structure (Phase 2)

**Format:** Raw binary files from acquisition systems (e.g., Blackrock, Plexon)

**Challenges:**
- Timing synchronization across multiple acquisition devices
- Data requires preprocessing (filtering, spike sorting) before analysis
- Larger file sizes and different internal structures

---

## 4. Use Cases

### Use Case 1: Converting Data for Analysis with Open-Source Tools

**Objective:** A lab member wants to analyze neural population dynamics during a reaching task using the pynapple package, which requires NWB-formatted data.

**User Scenario:**
Dr. Smith has collected three recording sessions from a monkey performing a center-out reaching task. She wants to use pynapple's tuning curve analysis and decoding functions, which expect NWB files as input.

**Expected Interactions:**

1. **Setup:**
   - User installs the converter package: `pip install nwb-aolab-converter`
   - User confirms their data is organized in the standard folder structure

2. **Configure conversion (optional):**
   - User reviews default configuration to ensure proper mapping of data fields
   - For most users, default settings will work without modification

3. **Run conversion:**
   ```python
   from nwb_converter import convert_session
   
   # Convert a single session
   nwb_file = convert_session(
       session_path="/data/MonkeyA/2024-03-15/session_001/",
       output_dir="/data/nwb_files/"
   )
   ```

4. **Verify conversion:**
   - Converter prints summary: "✓ Converted 192 neurons, 3.5 hours of LFP, 12,450 kinematic samples"
   - User receives path to output NWB file
   - Conversion log saved for troubleshooting

5. **Use converted data:**
   ```python
   import pynapple as nap
   import nwbwidgets
   
   # Load NWB file
   data = nap.load_file(nwb_file)
   
   # Access spike times
   spike_times = data['units']
   
   # Perform analysis
   tuning_curves = nap.compute_1d_tuning_curves(...)
   ```

**Expected Outcome:**
- User has a valid NWB file containing all neural and behavioral data
- Analysis proceeds seamlessly with pynapple without format conversion errors
- User can visualize data using NWBWidgets or other NWB-compatible tools

---

### Use Case 2: Batch Converting Historical Data for Collaboration

**Objective:** A postdoc needs to share two years of archived experimental data with a collaborator at another institution who uses NWB-based analysis pipelines.

**User Scenario:**
Dr. Johnson is collaborating with a lab that studies motor cortex dynamics. The external collaborator's analysis pipeline expects NWB format. Dr. Johnson needs to convert 45 recording sessions spanning 15 experimental days.

**Expected Interactions:**

1. **Identify data to convert:**
   - User creates a list of sessions or specifies a date range:
   ```python
   from nwb_converter import convert_batch
   
   sessions = [
       "/data/MonkeyB/2023-01-10/",
       "/data/MonkeyB/2023-01-11/",
       # ... or read from file
   ]
   ```

2. **Configure batch conversion:**
   ```python
   # Convert multiple days
   convert_batch(
       session_list=sessions,
       output_dir="/data/shared_nwb/",
       parallel=True,  # Speed up with parallel processing
       skip_errors=True  # Continue if individual sessions fail
   )
   ```

3. **Monitor progress:**
   - Converter displays progress bar: "Converting session 12/45..."
   - Warnings logged for any issues (e.g., missing metadata fields)
   - Conversion continues even if individual sessions encounter errors

4. **Review batch report:**
   - Converter generates summary report:
     - 43/45 sessions converted successfully
     - 2 sessions failed (logged with error details)
     - Total data: 850GB processed in 2.5 hours
   - User reviews log file to identify and fix failed sessions

5. **Validate and share:**
   - User runs validation script to check NWB file integrity:
   ```python
   from nwb_converter.utils import validate_nwb_files
   
   validate_nwb_files("/data/shared_nwb/")
   ```
   - User uploads validated NWB files to shared storage or DANDI archive
   - Collaborator downloads and immediately begins analysis with their existing tools

**Expected Outcome:**
- All historical sessions converted to standardized NWB format
- Collaborator can access data without learning proprietary lab formats
- Failed conversions clearly documented for user follow-up
- Data sharing facilitates cross-lab analysis and publication

---

## 5. Success Criteria

The converter will be considered successful when:

1. **Ease of use**: Lab members with minimal Python experience can convert their data in under 10 minutes
2. **Reliability**: >95% of sessions convert successfully without manual intervention
3. **Data fidelity**: All critical data streams and metadata are preserved in the conversion
4. **Adoption**: At least 50% of new analyses use NWB files instead of proprietary formats within 6 months
5. **External sharing**: At least 3 datasets successfully shared with external collaborators using NWB format

---

## 6. Future Enhancements

- **Interactive GUI**: Web-based interface for users uncomfortable with command-line tools
- **Automatic validation**: Integration with NWB Inspector for automated file validation
- **DANDI upload**: Direct upload to DANDI archive for public data sharing
- **Phase 2 implementation**: Direct conversion from raw binary acquisition files