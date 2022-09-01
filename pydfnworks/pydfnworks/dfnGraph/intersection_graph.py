import networkx as nx
import numpy as np
import json
import sys


def boundary_index(bc_name):
    """Determines boundary index in intersections_list.dat from name

    Parameters
    ----------
        bc_name : string
            Boundary condition name

    Returns
    -------
        bc_index : int
            integer indexing of cube faces

    Notes
    -----
    top = 1
    bottom = 2
    left = 3
    front = 4
    right = 5
    back = 6
    """
    bc_dict = {
        "top": -1,
        "bottom": -2,
        "left": -3,
        "front": -4,
        "right": -5,
        "back": -6
    }
    try:
        return bc_dict[bc_name]
    except:
        error = f"Error. Unknown boundary condition: {bc_name} \nExiting\n"
        sys.stderr.write(error)
        sys.exit(1)


def create_intersection_graph(inflow,
                              outflow,
                              intersection_file="intersection_list.dat",
                              fracture_info="fracture_info.dat"):
    """ Create a graph based on topology of network.
    Edges are represented as nodes and if two intersections
    are on the same fracture, there is an edge between them in the graph. 
    
    Source and Target node are added to the graph. 
   
    Parameters
    ----------
        inflow : string
            Name of inflow boundary
        outflow : string
            Name of outflow boundary
        intersection_file : string
             File containing intersection information
             File Format:
             fracture 1, fracture 2, x center, y center, z center, intersection length

        fracture_infor : str
                filename for fracture information
    Returns
    -------
        G : NetworkX Graph
            Vertices have attributes x,y,z location and length. Edges has attribute length

    Notes
    -----
    Aperture and Perm on edges can be added using add_app and add_perm functions
    """

    print("--> Creating Graph Based on DFN")
    print("--> Intersections being mapped to nodes and fractures to edges")
    inflow_index = boundary_index(inflow)
    outflow_index = boundary_index(outflow)

    # Load edges from intersection file
    frac_edges = np.genfromtxt(intersection_file, skip_header = 1)
    # Grab indices of internal edges
    internal_edges = np.where(frac_edges[:,1] > 0)
    # Grab indices of source edges
    source_edges = np.where(frac_edges[:,1] == inflow_index)
    # Grab indices of target edges
    target_edges = np.where(frac_edges[:,1] == outflow_index)
    # combine those indices from waht to keep
    edges_to_keep = list(internal_edges[0]) + list(source_edges[0]) + list(target_edges[0])
    # keep only the edges we care about 
    frac_edges = frac_edges[edges_to_keep,:]
    num_edges = len(frac_edges)
    G = nx.Graph(representation="intersection")
    print("--> Adding Nodes to Graph")
    for i in range(num_edges):
        frac_1 = int(frac_edges[i][0])
        if frac_edges[i][1]  > 0:
            frac_2 = int(frac_edges[i][1])
        elif int(frac_edges[i][1]) == inflow_index:
            frac_2 = 's'
        elif int(frac_edges[i][1]) == outflow_index:
            frac_2 = 't'
        # note fractures of the intersection
        G.add_node(i, frac = (frac_1, frac_2))
        # keep intersection location and length
        G.nodes[i]['x'] = float(frac_edges[i][2])
        G.nodes[i]['y'] = float(frac_edges[i][3])
        G.nodes[i]['z'] = float(frac_edges[i][4])
        G.nodes[i]['length'] = float(frac_edges[i][5])

    print("--> Adding Nodes to Graph Complete")

    print("--> Adding edges to Graph: Starting")
    nodes = list(nx.nodes(G))
    fractures = nx.get_node_attributes(G, 'frac')
    # Add Sink and Source nodes
    G.add_node('s')
    G.add_node('t')

    # identify which edges are on which fractures
    for i in nodes:
        node_1_fracs = fractures[i]
        for j in nodes[i+1:]:
            frac_int = list(set(node_1_fracs).intersection(set(fractures[j])))
            # print(i,j,frac_int)
            # Check if the intersection is empty
            if len(frac_int) > 0:
                # Check for source and target
                if 's' in frac_int:
                    G.add_edge(i, 's', frac='s', length = 0.0)
                    frac_int.remove('s')

                if 't' in frac_int:
                    G.add_edge(i, 't', frac='t', length = 0.0)
                    frac_int.remove('t')

                # if there is anything left, that's what we want
                if len(frac_int) > 0:
                    distance = np.sqrt(
                                (G.nodes[i]['x'] - G.nodes[j]['x'])**2 + 
                                (G.nodes[i]['y'] - G.nodes[j]['y'])**2 +
                                (G.nodes[i]['z'] - G.nodes[j]['z'])**2 )
                    G.add_edge(i, j, frac = frac_int[0], length = distance)

    print("--> Adding edges to Graph: Complete")
    add_perm(G, fracture_info)
    print("Graph Construction Complete")
    return G



