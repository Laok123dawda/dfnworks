import networkx as nx
import numpy as np
import json

from networkx.algorithms.flow.shortestaugmentingpath import *
from networkx.algorithms.flow.edmondskarp import *
from networkx.algorithms.flow.preflowpush import *
from networkx.readwrite import json_graph
import matplotlib.pylab as plt
from itertools import islice

def create_graph(self, graph_type, inflow, outflow):
#def create_graph(graph_type, inflow, outflow):

    if graph_type == "fracture":
        G = create_graph_fracture(inflow, outflow)
    elif graph_type == "intersection":
        G = create_graph_intersection(inflow, outflow)
    elif graph_type == "bipartite":
        G = create_graph_bipartite(inflow, outflow)
    else:
        print("ERROR! Unknown graph type")
        return [] 
    return G

def create_graph_fracture(inflow, outflow, topology_file = "connectivity.dat"):
    ''' Create a graph based on topology of network. Fractures 
    are represented as nodes and if two fractures intersect 
    there is an edge between them in the graph. 
    
    Source and Target node are added to the graph. 
    
    Inputs: 
    inflow: name of inflow boundary 
        (connect to source)
    outflow: name of outflow boundary 
        (connect to target)
    topology_file: default=connectivity.dat  
    Output: G (NetworkX Graph)
    ''' 
    print("Loading Graph based on topology in "+topology_file)
    G = nx.Graph(representation="fracture")
    with open(topology_file, "r") as infile:
        for i,line in enumerate(infile):
            conn = [int(n) for n in line.split()]
            for j in conn:
                G.add_edge(i,j-1) 
    ## Create Source and Target and add edges
    inflow_filename = inflow + ".dat"
    outflow_filename = outflow + ".dat"
    inflow = np.genfromtxt(inflow_filename) - 1
    outflow = np.genfromtxt(outflow_filename) - 1
    inflow = list(inflow)
    outflow = list(outflow)
    G.add_node('s')
    G.add_node('t')
    G.add_edges_from(zip(['s']*(len(inflow)),inflow))
    G.add_edges_from(zip(outflow,['t']*(len(outflow))))    
    print("Graph loaded")
    return G

def boundary_index(bc):
    ''' determines boundary index in intersections_list.dat from name

    input : bc name
    output : bc index

    top = -1
    bottom = -2
    left = -3
    front = -4
    right = -5
    back = -6
    ''' 
    if bc == 'top':
        return -1
    elif bc == 'bottom':
        return -2
    elif bc == 'left':
        return -3
    elif bc == 'front':
        return -4
    elif bc == 'right':
        return -5
    elif bc == 'back':
        return -6
    else:
        sys.exit("unknown boundary condition: %s\nExiting"%bc)

def create_graph_intersection(inflow, outflow, intersection_file="intersection_list.dat"):
    ''' Create a graph based on topology of network.
    Edges are represented as nodes and if two intersections
    are on the same fracture, there is an edge between them in the graph. 
    
    Source and Target node are added to the graph. 
    
    Inputs: intersection_file: File containing intersection information
    --> File Format
    fracture 1, fracture 2, x center, y center, z center, intersection length

    source can be either -1 or s, target can be either -2 or t
    
    Output: G (NetworkX Graph)
    ''' 

    print("Creating Graph Based on DFN")
    print("Intersections being mapped to nodes and Fractures to Edges")
    inflow_index=boundary_index(inflow)
    outflow_index=boundary_index(outflow)

    f=open(intersection_file)
    f.readline()
    frac_edges = []
    for line in f:
        frac_edges.append(line.rstrip().split())
    f.close()

    # Tag mapping
    G = nx.Graph(representation="intersections")
    remove_list=[]

    # each edge in the DFN is a node in the graph
    for i in range(len(frac_edges)):
        f1 = int(frac_edges[i][0]) - 1
        keep=True
        if frac_edges[i][1] is 's' or frac_edges[i][1] is 't':
            f2 = frac_edges[i][1]
        elif int(frac_edges[i][1]) > 0:
            f2 = int(frac_edges[i][1]) - 1  
        elif int(frac_edges[i][1]) == inflow_index:
            f2 = 's'
        elif int(frac_edges[i][1]) == outflow_index:
            f2 = 't'
        elif int(frac_edges[i][1]) < 0:
            keep=False

        if keep: 
            # note fractures of the intersection 
            G.add_node(i,frac=(f1,f2))
            # keep intersection location and length
            G.node[i]['x'] = float(frac_edges[i][2])
            G.node[i]['y'] = float(frac_edges[i][3])
            G.node[i]['z'] = float(frac_edges[i][4])
            G.node[i]['length'] = float(frac_edges[i][5])
    
    nodes = list(nx.nodes(G))    
    f1 = nx.get_node_attributes(G,'frac') 
    # identify which edges are on whcih fractures
    for i in nodes:
        e = set(f1[i])
        for j in nodes:
            if i != j:
                tmp = set(f1[j])
                x = e.intersection(tmp)
                if len(x) > 0:
                    x = list(x)[0]
                    # Check for Boundary Intersections
                    # This stops boundary fractures from being incorrectly
                    # connected 
                    #if x is 's' or x is 't':
                    #      k = 1
                    # If not, add edge between
                    if x != 's' and x != 't':
                        xi = G.node[i]['x']
                        yi = G.node[i]['y']
                        zi = G.node[i]['z']

                        xj = G.node[j]['x']
                        yj = G.node[j]['y']
                        zj = G.node[j]['z']
            
                        distance = np.sqrt((xi-xj)**2 + (yi-yj)**2 + (zi-zj)**2)
                        G.add_edge(i,j,frac = x, length = distance)

    # Add Sink and Source nodes
    G.add_node('s')
    G.add_node('t')

    for i in nodes:
        e = set(f1[i])
        if len(e.intersection(set('s'))) > 0 or len(e.intersection(set([-1]))) > 0:
            G.add_edge(i,'s',frac='s', length=0.0)
        if len(e.intersection(set('t'))) > 0 or len(e.intersection(set([-2]))) > 0:
            G.add_edge(i,'t',frac='t', length=0.0)     
    print("Graph Construction Complete")
    return G


def create_graph_bipartite(inflow, outflow):
    print("Not supported yet, returning empty graph")
    return nx.Graph()

def k_shortest_paths(G, k, source='s', target='t', weight=None):
    return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))

def k_shortest_paths_backbone(self, G,k):
#def k_shortest_paths_backbone(G,k):
    print("\n--> Determining %d shortest paths in the network"%k)
    k_shortest= set([])
    for path in k_shortest_paths(G, k):
        k_shortest |= set(path)
    paths = sorted(list(k_shortest))
    paths.remove('s')
    paths.remove('t')
    backbone = []
    for n in paths:
        backbone.append(int(n) +1)
    print('--> Number of Fractures in %d shortest Paths Backbone %d: '%(k,len(backbone)))
    filename_out = 'sp_%02d_fractures.txt'%k
    print("--> Writting union of fracture in %d shortest path fractures into %s"%(k,filename_out))
    np.savetxt(filename_out, backbone, fmt = "%d")
    print("--> Complete\n")
    return filename_out

def plot_graph(G, source='s', target='t',output_name="dfn_graph"):
    ''' Create a png of a graph with source nodes colored blue, target red, and all over nodes black
    
    Inputs: 
    G: networkX graph
    source: source nodes
    target: target nodes
    output_name: name of output file (no .png)
    ''' 
    print("\n--> Plotting Graph")
    print("--> Output file: %s.png"%output_name)
    # get positions for all nodes
    pos=nx.spring_layout(G)
    nodes=list(G.nodes)
    # draw nodes
    nx.draw_networkx_nodes(G,pos,
                           nodelist=nodes,
                           node_color='k',
                           node_size=10,
                       alpha=1.0)
    nx.draw_networkx_nodes(G,pos,
                           nodelist=[source],
                           node_color='b',
                           node_size=10,
                       alpha=1.0)
    nx.draw_networkx_nodes(G,pos,
                           nodelist=[target],
                           node_color='r',
                           node_size=10,
                       alpha=1.0)
    
    nx.draw_networkx_edges(G,pos,width=1.0,alpha=0.5)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_name+".png")
    plt.clf()
    print("--> Plotting Graph Complete") 

def dump_json_graph(G, name):
    print("Dumping Graph into file: "+name+".json")
    jsondata = json_graph.node_link_data(G)
    with open(name+'.json', 'w') as fp:
        json.dump(jsondata, fp)
    print("Complete")

def load_json_graph(name):
    print("Loading Graph in file: "+name+".json")
    fp = open(name+'.json')
    G = json_graph.node_link_graph(json.load(fp))
    print("Complete")
    return G

def add_perm(G):
    ''' Add fracture permeability to Graph. If Graph represenation is
    fracture, then permeability is a node attribute. If graph represenation 
    is intersection, then permeability is an edge attribute '''

    perm = np.genfromtxt('fracture_info.dat', skip_header =1)[:,1]
    if G.graph['representaion'] == "fracture":
        nodes = list(nx.nodes(G))
        for n in nodes:
            if n != 's' and n != 't':
                G.node[n]['perm'] = perm[n]
            else:
                G.node[n]['perm'] = 1.0

    elif G.graph['represenation'] == "intersection":
        edges = list(nx.edges(G))
        for u,v in edges:
            x = G[u][v]['frac']
            if x != 's' and x != 't':
                G[u][v]['perm'] = perm[x]
            else:   
                G[u][v]['perm'] = 1.0




