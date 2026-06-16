import networkx as nx
import random
import numpy as np
import json

# Define the set of nodes with respective ids, coordinates, and product vector (initially empty)
class Nodes:
    def __init__(self, node_id, coords, products=None):
        self.node_id = node_id
        self.coords = coords
        self.products = products if products is not None else []

    def add_product(self, product):
        self.products.append(product)
    
    def remove_product(self, product):
        self.products.remove(product)

    def __repr__(self):
        return f"Nodes(id={self.node_id}, coords={self.coords}, products={self.products})"

def aisle_congestion(coords_a, coords_b):
    """Travel-time multiplier for the edge between two adjacent nodes.

    The *distance* objective is the pure walked length (one step per edge).
    The *time* objective is that length scaled by how congested the aisle is,
    so the two objectives are no longer identical and a genuine Pareto front
    exists for the multi-objective solver.

    Congestion is a deterministic function of the edge midpoint, modelling a
    typical hypermarket layout:
      - the central fresh/produce zone (mid columns) is crowded -> slower,
      - busy mid-store aisles add extra delay,
      - the top row near the service stations is a bottleneck,
      - outer perimeter lanes and the entrance lane near the tills are fast.

    Returns a multiplier in roughly [0.45, 3.0]. With factor == 1 everywhere
    this reduces to the original "time == distance" behaviour.
    """
    mx = 0.5 * (coords_a[0] + coords_b[0])   # edge midpoint x (column)
    my = 0.5 * (coords_a[1] + coords_b[1])   # edge midpoint y (row)

    factor = 1.0
    # Crowded central fresh & produce core (mid columns, mid rows): heavily
    # congested, so cutting straight through it is short but slow.  The
    # penalty is deliberately large so that detouring via the fast perimeter
    # lanes can genuinely save time at the cost of extra distance -- which is
    # what creates the Pareto trade-off between the distance and time
    # objectives.
    if 4 <= mx <= 12 and 2 <= my <= 10:
        factor += 5.0
    # Fast outer perimeter lanes (leftmost / rightmost columns).
    if mx <= 2 or mx >= 14:
        factor *= 0.4
    # Fast main entrance / checkout lane along the bottom.
    if my <= 1.5:
        factor *= 0.4
    return factor


def create_graph(horizontal, max_row, products, V_pay, V_frozen, V_fresh, meat_station, fish_station, seed=42, congestion=True):

    random.seed(seed)

    nodes = {}
    # Create set of nodes
    node_id = 0
    
    for row, step in enumerate(horizontal):
        for i in range(0, max_row, step):
            node = Nodes(node_id, (i+1, row+1), products=None)
            nodes[node_id] = node
            node_id += 1  # Increment the node_id after each node creation
    
    
    column = max_row + 1 - len(V_pay)
    for value in V_pay:
        node = Nodes(node_id, (column,0), products=None)
        nodes[node_id] = node
        node_id += 1
        column += 1


    #Change the category "locations" to "products" in the products dictionary given V_pay, V_stations, V_frozen, V_fresh
    V = np.arange(0, len(nodes))
    V_stations = [meat_station, fish_station]
    V_normal_products = list(np.setdiff1d(V, np.concatenate((V_pay, V_stations, V_frozen, V_fresh))))

    # Populate the product vector for each node based on product locations
    for product_id, product_info in products.items():
        for location in product_info['locations']:
            nodes[location].products.append(product_id)  # Access products using dot notation

    # Function to calculate Manhattan distance between two points
    def manhattan_distance(point1, point2):
        return abs(point1[0] - point2[0]) + abs(point1[1] - point2[1])

    # Create a set of arcs based on Manhattan distance and products
    def create_arcs(graph, nodes):
        arcs = {}  # To store the arcs
        for i, data1 in nodes.items():
            for j, data2 in nodes.items():
                if i != j:
                    distance = manhattan_distance(data1.coords, data2.coords)  # Access coords using dot notation
                    # Travel time = walked length scaled by aisle congestion, so
                    # the time objective genuinely differs from the distance one.
                    if congestion:
                        travel_time = distance * aisle_congestion(data1.coords, data2.coords)
                    else:
                        travel_time = distance  # legacy mode: 1 distance unit / time unit
                    if distance < 2:
                        #Add a small bias to the arcs with higher bias for the ones with higher x and y)
                        bias = 0.0001 * (data1.coords[0] + data1.coords[1] + data2.coords[0] + data2.coords[1])
                        graph.add_edge(i, j, length=distance+bias, time=travel_time+bias)
                        arcs[(i, j)] = {'distance': distance+bias, 'time': travel_time+bias}
                  
        return arcs

    # Create the graph
    G = nx.Graph()

    arcs = create_arcs(G, nodes)

    return G, nodes


# Function to get movement options as a boolean dictionary for each node
def get_movement_bools(nodes):
    movement_options = {}

    for node_id, node in nodes.items():
        # Get the coordinates of the current node
        node_coords = node.coords

        # Define the possible moves (up, down, left, right)
        directions = {
            'up': (node_coords[0], node_coords[1] + 1),
            'down': (node_coords[0], node_coords[1] - 1),
            'left': (node_coords[0] - 1, node_coords[1]),
            'right': (node_coords[0] + 1, node_coords[1])
        }

        # Initialize movement options for each direction
        movement_options[node_id] = {
            'up': None,
            'down': None,
            'left': None,
            'right': None
        }

        # Check for each direction if a neighboring node exists
        for direction, coords in directions.items():
            # Check if any node has the coordinates in this direction
            for neighbor_id, neighbor_node in nodes.items():
                if neighbor_node.coords == coords:
                    movement_options[node_id][direction] = neighbor_id  # Set to neighbor_id if neighbor exists
                    break  # No need to check further once found

    return movement_options

def save_graph_to_json(G, nodes, filepath):
    """
    Salva o grafo G e os nodes num ficheiro JSON com toda a informação necessária.
    
    Args:
        G: NetworkX Graph object
        nodes: Dicionário de Nodes objects
        filepath: Caminho do ficheiro JSON onde guardar
    """
    # Preparar dados dos nodes
    nodes_data = {}
    for node_id, node in nodes.items():
        nodes_data[str(node_id)] = {
            'node_id': node.node_id,
            'coords': list(node.coords),
            'products': node.products
        }
    
    # Preparar dados das arestas (edges)
    edges_data = []
    for u, v, data in G.edges(data=True):
        edges_data.append({
            'source': u,
            'target': v,
            'length': data.get('length', 0),
            'time': data.get('time', 0)
        })
    
    # Criar dicionário com toda a informação
    graph_data = {
        'nodes': nodes_data,
        'edges': edges_data
    }
    
    # Guardar em JSON
    with open(filepath, 'w') as f:
        json.dump(graph_data, f, indent=2)
    
    print(f"Grafo guardado em {filepath}")


def load_graph_from_json(filepath):
    """
    Lê um ficheiro JSON e cria o grafo G e os nodes correspondentes.
    
    Args:
        filepath: Caminho do ficheiro JSON
        
    Returns:
        tuple: (G, nodes) - NetworkX Graph object e dicionário de Nodes objects
    """
    # Carregar dados do JSON
    with open(filepath, 'r') as f:
        graph_data = json.load(f)
    
    # Reconstruir nodes
    nodes = {}
    for node_id_str, node_info in graph_data['nodes'].items():
        node_id = int(node_id_str)
        coords = tuple(node_info['coords'])
        products = node_info['products']
        
        nodes[node_id] = Nodes(node_id, coords, products=products)
    
    # Criar grafo e adicionar arestas
    G = nx.Graph()
    G.add_nodes_from(nodes.keys())
    
    for edge in graph_data['edges']:
        G.add_edge(
            edge['source'],
            edge['target'],
            length=edge['length'],
            time=edge['time']
        )
    
    print(f"Grafo carregado de {filepath}")
    return G, nodes

def read_products_from_json(file_path_1, file_path_2):
    products = {}
    import json
    with open(file_path_1, 'r') as f:
        products_df = json.load(f)
    with open(file_path_2, 'r') as f:
        locations_df = json.load(f)
    for product in products_df:
        product_id = product['unique_id']
        products[product_id] = {
            'name': product['title'],
            'frozen': 1 if product['sub_category1'] == "Congelados" else 0,
            'fresh': 1 if product['sub_category1'] == "Charcutaria&Queijos" else 0,
            'meat': 1 if product['sub_category1'] == 'Talho' else 0,
            'fish': 1 if product['sub_category2'] == 'Peixaria' else 0,
            'locations': [int(locations_df[product_id])] if product_id in locations_df else [random.randint(0, 108)],
            'image_url': product['image_url'],
            'icon': '🍎'
        }
    return products