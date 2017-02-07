import os
import sys
import meshdfn as mesh
import shutil

def make_working_directory(jobname):
    '''
    make working directories for fracture generation
    '''    

    try:
        os.mkdir(jobname)
    except OSError:
        print '\nFolder ', jobname, ' exists'
        keep = raw_input('Do you want to delete it? [yes/no] \n')
        if keep == 'yes' or keep == 'y':
            print 'Deleting', jobname 
            shutil.rmtree(jobname)
            print 'Creating', jobname 
            os.mkdir(jobname)    
        elif keep == 'no' or 'n':
            sys.exit("Not deleting folder. Exiting Program") 
        else:
            sys.exit("Unknown Response. Exiting Program") 
    os.mkdir(jobname + '/radii')
    os.mkdir(jobname + '/intersections')
    os.mkdir(jobname + '/polys')
    os.chdir(jobname)
    cwd = os.getcwd()
    print("Current directory is now: %s\n"%cwd)
    print "Jobname is ", jobname   

def create_network(local_dfnGen_file, jobname):
    print '--> Running DFNGEN'    
    # copy input file into job folder    
    os.system(os.environ['DFNGEN_PATH']+'/./DFNGen ' + local_dfnGen_file[:-4] + '_clean.dat' + ' ' + jobname )

    if os.path.isfile("params.txt") is False:
        print '--> Generation Failed'
        print '--> Exiting Program'
        exit()
    else:
        print('-'*80)
        print("Generation Succeeded")
        print('-'*80)
