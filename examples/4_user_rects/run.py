#"""
#   :synopsis: run file for dfnworks 
#   :version: 1.0
#   :maintainer: Jeffrey Hyman
#.. moduleauthor:: Jeffrey Hyman <jhyman@lanl.gov>
#"""


from pydfnworks import * 

DFN = create_dfn()
# General Work Flow
DFN.dfn_gen()
fracture_list = list(range(1,5))
apertures = 4*[1e-4]
DFN.set_fracture_hydraulic_values("aperture", fracture_list, apertures)
DFN.dfn_flow()
DFN.dfn_trans()
