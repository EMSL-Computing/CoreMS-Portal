
# CoreMS App  


**CoreMS-APP* is the app for running mass spectrometry data processing workflows for metabolomics and natural organic matter analysis  

## Current Version
  
###  `3.9.7.beta`

### Data input formats  

- ANDI NetCDF for GC-MS (.cdf)
- CoreMS self-containing Hierarchical Data Format (.hdf5)
- ChemStation Agilent (Ongoing)

### Data output formats

- Pandas data frame (can be saved using pickle, h5, etc)
- Text Files (.csv, tab separated .txt, etc)
- Microsoft Excel (xlsx)
- JSON for workflow metadata
- Self-containing Hierarchical Data Format (.hdf5) including raw data and ime-series data-point for processed data-sets with all associated metadata stored as json attributes

### Data structure types

- GC-MS

## Available features

### Signal Processing

- Baseline detection, subtraction, smoothing 
- Manual and automatic noise threshold calculation
- First and second derivatives peak picking methods
- Peak Area Calculation
- EIC Chromatogram deconvolution(TODO)

### Calibration

- Retention Index Linear XXX method 

### Compound Identification

- Automatic local (SQLite) or external (PostgreSQL) database check, generation, and search
- Automatic molecular match algorithm with all spectral similarity methods 

## CoreMS App Installation

- PyPi:     
```bash
pip3 install corems-app
```

- From source:
 ```bash
python3 setup.py install
```

## Usage
- Development server:
    
    Assuming you have python virtual environment at venv:
    The user database needs to be initiated for the first time use:
    
    ```bash
    make init-database
    ```
    
    ```bash
    make run-local
    ```
    
    Otherwise:
    ```bash
    flask run
    ```

- Then go to http://localhost:5000/gcms

- Remote trigger:

    Modify the tmp/MetamsFile.json and tmp/CoremsFile.json accordingly to your dataset and workflow parameters.
    Make sure to include the CoremsFile.json path inside the MetamsFile.json: "corems_json_path": "path_to_CoremsFile.json" 

    ```bash
    curl -X POST -H "Content-Type: application/json" --data @tmp/MetamsFile.json localhost:5000/gcms/remote-start-workflow
    ```

## Docker 

A docker image serving the app.from gunicorn

If you don't have docker installed, the easiest way is to [install docker for desktop](https://hub.docker.com/?overlay=onboarding)

- Pull from Docker Registry:

    ```bash
    docker pull corilo/corems-app.latest
    
    ```

- Build the image from source:

    ```bash
    docker build -t corems-flask-app..
    ```
- Run Workflow from Container:

    $(app.dir) = dirpath for the app.installation 
    
    ```bash
    @docker run --rm -d -p 5000:5000  \
	-v $(app.dir):/app.corems-flask-app
    ```
