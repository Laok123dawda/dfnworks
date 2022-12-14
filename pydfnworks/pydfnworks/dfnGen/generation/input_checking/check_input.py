import os
import shutil
import sys

#pydfnworks modules
import pydfnworks.dfnGen.generation.input_checking.helper_functions as hf
from pydfnworks.dfnGen.generation.input_checking.parsing import parse_input
from pydfnworks.dfnGen.generation.input_checking.verifications import verify_params
from pydfnworks.dfnGen.generation.input_checking.write_input_file import dump_params


def check_input(self):
    """ Checks input file for DFNGen to make sure all necessary parameters are defined. Then writes out a "clean" version of the input file

     Input Format Requirements:  
        * Each parameter must be defined on its own line (separate by newline)
        * A parameter (key) MUST be separated from its value by a colon ':' (ie. --> key: value)
        * Values may also be placed on lines after the 'key'
        * Comment Format:  On a line containing  // or / ``*``, nothing after ``*`` / or // will be processed  but text before a comment will be processed 
    
    Parameters
    ------------
        self : DFN Class Objects

    Returns
    ---------
        None

    Notes
    -----
        There are warnings and errors raised in this function. Warning will let you continue while errors will stop the run. Continue past warnings are your own risk.     
    """
    print()
    print('=' * 80)
    print("Checking Input File\n")
    ## Copy input file
    if os.path.isfile(self.dfnGen_file):
        try:
            print(f"--> Copying input file: {self.dfnGen_file}")
            shutil.copy(self.dfnGen_file, self.jobname)
            print("--> Copying input file successful")
        except:
            error = f"Unable to copy dfnGen input file to working directory \n{self.dfnGen_file}\n Exiting"
            sys.stderr.write(error)
            sys.exit(1)
    else:
        error = f"Input file \n{self.dfnGen_file} not found\n Exiting"
        sys.stderr.write(error)
        sys.exit(1)

    input_file = self.local_dfnGen_file
    output_file = input_file[:-4] + '_clean.dat'
    print(f"--> Reading input file: {input_file}")
    print(f"--> Clean output file name: {output_file}")
    params = parse_input(input_file)
    verify_params(params)
    dump_params(params, output_file)
    print("\nChecking Input File Complete")
    print('=' * 80)
    print()
