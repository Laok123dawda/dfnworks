# README

For information on how to get dfnWorks up and running, please see the document dfnWorks.pdf, in this directory.

## Native build from github repository

This document contains instructions for setting up dfnWorks natively on your
machine. To setup dfnWorks using Docker instead, see the next section.

### Clone the dnfWorks repository

    $ git clone https://github.com/lanl/dfnWorks.git

### Fix paths in test directory 

Fix the pathnames in files throughout pydfnworks. This can be done automatically by running the script ``fix_paths.py``:

    $ cd dfnWorks/pydfnworks/bin/
    $ python fix_paths.py 

Set the LagriT, PETSC, PFLOTRAN, Python, and FEHM paths 

**Before executing dfnWorks,** the following paths must be set:

- dfnWorks_PATH: the dfnWorks repository folder
- PETSC_DIR and PETSC_ARCH: PETSC environmental variables
- PFLOTRAN_EXE:  Path to PFLOTRAN executable 
- PYTHON_EXE:  Path to python executable 
- LAGRIT_EXE:  Path to LaGriT executable 

    $ vi dfnWorks/pydfnworks/pydfnworks/paths.py

For example:
    
    os.environ['dfnWorks_PATH'] = '/home/<username>/dfnWorks/'    

Alternatively, you can create a ``.dfnworksrc`` file in your home directory with the following format

    {
        "dfnworks_PATH": "<your-home-directory>/src/dfnworks-main/",
        "PETSC_DIR": "<your-home-directory>/src/petsc",
        "PETSC_ARCH": "arch-darwin-c-debug",
        "PFLOTRAN_EXE": "<your-home-directory>/src/pflotran/src/pflotran/pflotran",
        "PYTHON_EXE": "<your-home-directory>/anaconda3/bin/python",
        "LAGRIT_EXE": "<your-home-directory>/bin/lagrit",
        "FEHM_EXE": "<your-home-directory>//src/xfehm_v3.3.1"
    }


## Installing pydfnworks

Go up into the pydfnworks sub-directory:
    
    $ cd dfnWorks/pydfnworks/

Complie The pydfnWorks Package:
    
    $ python setup.py bdist_wheel

Install on Your Local Machine:
    
    $ python -m pip install dist/pydfnworks-2.6-py3-none-any.whl

**Note: the python version in dist/ needs to be consistent with the current release**

## Installation Requirements for Native Build
Tools that you will need to run the dfnWorks work flow are described in 
this section. VisIt and ParaView, which enable visualization of desired 
quantities on the DFNs, are optional, but at least one of them is highly 
recommended for visualization. CMake is also optional but allows faster IO 
processing using C++. 

### Operating Systems

dfnWorks currently runs on Macs and Unix machine running Ubuntu. 

### Python 

pydfnworks uses Python 3. We recommend using 
the Anaconda 3 distribution of Python, available at https://www.continuum.io/. 
pydfnworks requires the following python modules: ``numpy``, ``h5py``, ``scipy``, ``matplotlib``,  ``multiprocessing``, ``argparse``, ``shutil``, ``os``, ``sys``, ``networkx``, ``subprocess``, ``glob``, ``networkx``, ``fpdf``, and ``re``.


### LaGriT

The LaGriT meshing toolbox is used to create a high resolution computational 
mesh representation of the DFN in parallel. An algorithm for conforming 
Delaunay triangulation is implemented so that fracture intersections are 
coincident with triangle edges in the mesh and Voronoi control volumes are 
suitable for finite volume flow solvers such as FEHM and PFLOTRAN.

https://lagrit.lanl.gov

### PFLOTRAN
PFLOTRAN  is a massively parallel subsurface flow and reactive transport 
code. PFLOTRAN solves a system of partial differential equations for 
multiphase, multicomponent and multi-scale reactive flow and transport in 
porous media. The code is designed to run on leadership-class supercomputers 
as well as workstations and laptops.

http://pflotran.org

### FEHM
FEHM is a subsurface multiphase flow code developed at Los Alamos National 
Laboratory.

https://fehm.lanl.gov

### Paraview

Paraview_ is a parallel, open-source visualisation software. PFLOTRAN can 
output in ``.xmf`` and ``.vtk`` format. These can be imported in Paraview 
for visualization. While not required for running dfnWorks, Paraview is
very helpful for visualizing dfnWorks simulations.

Instructions for downloading and installing Paraview_ can be found at 
http://www.paraview.org/download/ 

