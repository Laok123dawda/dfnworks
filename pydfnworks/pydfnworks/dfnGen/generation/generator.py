import os
import sys
import numpy as np
import shutil
from time import time
import subprocess


def dfn_gen(self, output=True, visual_mode=None):
    ''' Wrapper script the runs the dfnGen workflow:    
        1) make_working_directory: Create a directory with name of job
        2) check_input: Check input parameters and create a clean version of the input file
        3) create_network: Create network. DFNGEN v2.0 is called and creates the network
        4) output_report: Generate a PDF summary of the DFN generation
        5) mesh_network: calls module dfnGen_meshing and runs LaGriT to mesh the DFN

    Parameters
    ----------
        self : object
            DFN Class object
        output : bool
            If True, output pdf will be created. If False, no pdf is made 
        visual_mode : None
            If the user wants to run in a different meshing mode from what is in params.txt, set visual_mode = True/False on command line to override meshing mode

    Returns
    -------
        None

    Notes
    -----
        Details of each portion of the routine are in those sections

    '''
    # Create Working directory
    self.make_working_directory()
    # Check input file
    self.check_input()
    # Create network
    self.create_network()
    if output:
        self.output_report()
    # Mesh Network
    self.mesh_network(visual_mode=visual_mode)
    print('=' * 80)
    print('dfnGen Complete')
    print('=' * 80)


def make_working_directory(self, delete=False):
    ''' Make working directory for dfnWorks Simulation

    Parameters
    ----------
        self : object
            DFN Class object

    Returns
    -------
        None

    Notes
    -----
    If directory already exists, user is prompted if they want to overwrite and proceed. If not, program exits. 
    '''

    if not delete:
        try:
            os.mkdir(self.jobname)
        except OSError:
            if os.path.isdir(self.jobname):
                print('\nFolder ', self.jobname, ' exists')
                keep = input('Do you want to delete it? [yes/no] \n')
                if keep == 'yes' or keep == 'y':
                    print('Deleting', self.jobname)
                    shutil.rmtree(self.jobname)
                    print('Creating', self.jobname)
                    os.mkdir(self.jobname)
                elif keep == 'no' or 'n':
                    error = "Not deleting folder. Exiting Program\n"
                    sys.stderr.write(error)
                    sys.exit(1)
                else:
                    error = "Unknown Response. Exiting Program\n"
                    sys.stderr.write(error)
                    sys.exit(1)
            else:
                error = f"Unable to create working directory {self.jobname}\n. Please check the provided path.\nExiting\n"
                sys.stderr.write(error)
                sys.exit(1)
    else:
        if not os.path.isdir(self.jobname):
            os.mkdir(self.jobname)
        else:
            try:
                shutil.rmtree(self.jobname)
                print('--> Creating ', self.jobname)
                os.mkdir(self.jobname)
            except:
                error = "ERROR deleting and creating directory.\nExiting\n"
                sys.stderr.write(error)
                sys.exit(1)

    os.mkdir(self.jobname + '/radii')
    os.mkdir(self.jobname + '/intersections')
    os.mkdir(self.jobname + '/polys')
    os.chdir(self.jobname)

    print(f"Current directory is now: {os.getcwd()}")
    print(f"Jobname is {self.jobname}")


def create_network(self):
    ''' Execute dfnGen

    Parameters
    ----------
        self : object
            DFN Class 

    Returns
    -------
        None

    Notes
    -----
    After generation is complete, this script checks whether the generation of the fracture network failed or succeeded based on the existence of the file params.txt. 
    '''
    print('--> Running DFNGEN')
    # copy input file into job folder
    cmd = os.environ[
        'DFNGEN_EXE'] + ' ' + self.local_dfnGen_file[:
                                                     -4] + '_clean.dat' + ' ' + self.jobname

    print("Running %s" % cmd)
    subprocess.call(cmd, shell=True)

    if os.path.isfile("params.txt") is False:
        error = "ERROR! Generation Failed\nExiting Program.\n"
        sys.stderr.write(error)
        sys.exit(1)
    else:
        self.gather_output()
        print('-' * 80)
        print("Generation Succeeded")
        print('-' * 80)


def parse_params_file(self,quiet=False):
    """ Reads params.txt file from DFNGen and parses information

    Parameters
    ---------
        quiet : bool
            If True details are not printed to screen, if False they area 

    Returns
    -------
        num_poly: int
            Number of Polygons
        h: float 
            Meshing length scale h
        dudded_points: int 
            Expected number of dudded points in Filter (LaGriT)
        visual_mode : bool
            If True, reduced_mesh.inp is created (not suitable for flow and transport), if False, full_mesh.inp is created  
        domain: dict
             x,y,z domain sizes 
    
    Notes
    -----
        None
    """
    if not quiet:
        print("\n--> Parsing  params.txt")
    fparams = open('params.txt', 'r')
    # Line 1 is the number of polygons
    self.num_frac = int(fparams.readline())
    #Line 2 is the h scale
    self.h = float(fparams.readline())
    # Line 3 is the visualization mode: '1' is True, '0' is False.
    self.visual_mode = int(fparams.readline())
    # line 4 dudded points
    self.dudded_points = int(fparams.readline())

    # Dict domain contains the length of the domain in x,y, and z
    self.domain = {'x': 0, 'y': 0, 'z': 0}
    #Line 5 is the x domain length
    self.domain['x'] = (float(fparams.readline()))

    #Line 5 is the x domain length
    self.domain['y'] = (float(fparams.readline()))

    #Line 5 is the x domain length
    self.domain['z'] = (float(fparams.readline()))
    fparams.close()

    if not quiet:
        print("--> Number of Polygons: %d" % self.num_frac)
        print("--> H_SCALE %f" % self.h)
        if self.visual_mode > 0:
            self.visual_mode = True
            print("--> Visual mode is on")
        else:
            self.visual_mode = False
            print("--> Visual mode is off")
        print(f"--> Expected Number of dudded points: {self.dudded_points}")
        print(f"--> X Domain Size {self.domain['x']} m")
        print(f"--> Y Domain Size {self.domain['y']} m")
        print(f"--> Z Domain Size {self.domain['z']} m")
        print("--> Parsing params.txt complete\n")

def gather_output(self):
    
    """ Reads in information about fractures and add them to the DFN object. Information is taken from radii.dat, translations.dat, normal_vectors.dat, and surface_area_Final.dat files. Information for each fracture is stored in a dictionary created by create_fracture_dictionary() that includes the fracture id, radius, normal vector, center, family number, surface area, and if the fracture was removed due to being isolated 

    Parameters
    -----------
        None

    Returns
    --------
        fractuers : list
            List of fracture dictionaries with information.
    Notes
    ------
        Both fractures in the final network and those removed due to being isolated are included in the list. 

    """
    print("--> Parsing dfnWorks output and adding to object")
    self.parse_params_file(quiet = False)

    ## load radii
    data = np.genfromtxt('radii_Final.dat', skip_header = 2)
    ## populate radius array
    self.radii = np.zeros((self.num_frac,3))
    # First Column is x, second is y, 3rd is max
    self.radii[:,:2] = data[:,:2]
    for i in range(self.num_frac):
        self.radii[i,2] = max(self.radii[i,0], self.radii[i,1])

    # gather fracture families
    self.families = data[:,2].astype(int)

    ## load surface area
    self.surface_area = np.genfromtxt('surface_area_Final.dat', skip_header = 1)
    ## load normal vectors
    self.normal_vectors = np.genfromtxt('normal_vectors.dat')
    # Get fracture centers
    centers = []
    with open('translations.dat', "r") as fp:
        fp.readline()  # header
        for i, line in enumerate(fp.readlines()):
            if "R" not in line:
                line = line.split()
                centers.append([float(line[0]), float(line[0]), float(line[2])])
    self.centers = np.array(centers)

    # Grab Polygon information
    self.poly_info = np.genfromtxt('poly_info.dat')

    ## create holder arrays for b, k, and T
    self.aperture = np.array(self.num_frac)
    self.perm = np.array(self.num_frac)
    self.transmissivity = np.array(self.num_frac)

    # gather indexes for fracture families
    self.family = []
    ## get number of families
    num_families = int(max(self.families))
    for i in range(1, num_families+1):
        idx = np.where(self.families == i)
        self.family.append(idx) 
