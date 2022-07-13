# CoreMS Portal

![CoreMS Logo](web/app/static/images/CoreMS.COLOR.png)  

*CoreMS Portal* is a full-stack solution for mass spectrometry data processing of small molecule analysis. Currently, there are two workflows: molecular formulae assignment of ultra-high-resolution analysis of complex mixtures and GC-MS-based metabolomics analysis. LC-MS-based metabolomics workflows are presently under development.


## Current Version

### `3.9.7.beta`

### Services:

- PostgreSQL (Web and Data storage)
- Redis (Task queues storage) 
- Flask and Celery ( Web framework and Task queues Client)
- Celery (Task queues runner)

### Data input formats

- ANDI NetCDF for GC-MS (.cdf)
- Mass List (centroid mode) (.txt)
- Mass List (Profile mode) (.txt)
- Thermo raw format (.raw)
- Bruker D format (.d)

### Data output formats

- Text Files (.csv, tab separated .txt, etc)
- JSON for workflow metadata

## Local Deployment using docker-compose

- To start download or git clone this repository :D

- [install docker for desktop](https://hub.docker.com/?overlay=onboarding)

  There are two main way to start a local deployment, building from source, our using the images from docker hub.
   
 - To start from source, open a terminal and cd into the root project directory. 

 - To start from the pre built images, open the terminal and cd into CoreMS-Portal directory
 
   then: ( this command will build and pull the images, create the containers, volumes and network)
     
     ```bash

     docker-compose up
   
     ```

- After the first deployment, we need to start migration and create all the database tables. Open the terminal, cd into the root directory:

    ```bash
    make init-db

    ```

- To take all the services down and remove all the volumes:
    
    ```bash
    docker-compose down -v

    ```

## Kubernetes 

If you don't have kompose installed: [install kompose](https://kompose.io/installation/)

- Build from source:

    ```bash
    kompose convert -f docker-compose.yml -o ./kubernetes
	kubectl create -f ./kubernetes
    
    ```
    