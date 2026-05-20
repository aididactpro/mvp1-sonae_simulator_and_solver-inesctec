import networkx as nx

def heuristic_solver(instance):
    
    G = instance['graph']
    products = instance['products']
    K = instance['K']
    V_pay = instance['V_pay']
    meat_station = instance['meat_station']
    fish_station = instance['fish_station']
    v_0 = instance['v_0']
    frozen_last = instance['frozen_last']
    fresh_last = instance['fresh_last']
    next_product = instance['next_product']
    last_product = instance['last_product']
    precedence_constraints = instance['precedence_constraints']
    meat_wait_time = instance['meat_wait_time']
    fish_wait_time = instance['fish_wait_time']

    #Preprocessing the graph

    V_k = {product: [] for product in K}
    for product in V_k:
        for node in products[product]['locations']:
            V_k[product].append(node)

    #Total nodes (join start_node and all product locations)
    V_products = [v_0] + [node for product in V_k for node in V_k[product]]
    #Exclude repeated nodes
    V_products = list(set(V_products))

    #Define the frozen and fresh products
    K_frozen = []
    K_fresh = []
    K_meat = []
    K_fish = []

    for product in K:
        if products[product]['frozen'] == 1:
            K_frozen.append(product)
        if products[product]['fresh'] == 1:
            K_fresh.append(product)
        if products[product]['meat'] == 1:
            K_meat.append(product)
        if products[product]['fish'] == 1:
            K_fish.append(product)


    V = V_products + V_pay

    #Store the d(i,j) for nodes in total_nodes (assuming the graph shortest paths)
    distance = {(i, j): nx.shortest_path_length(G, i, j, weight='length') for i in V for j in V } #if i != j}
    time = {(i, j): nx.shortest_path_length(G, i, j, weight='time') for i in V for j in V}  #if i != j}

    # Heuristic to determin the paying station
    v_end = V_pay[0]

    # Heuristic to determin the node in which the product is picked
    product_nodes = []
    product_nodes_dict = {k: None for k in K}
    for k in K:
        min_distance = float('inf')
        best_node = None
        for node in V_k[k]:
            # Calculate a score that benefits nodes that are close
            score = distance[v_0, node] - sum(distance[node, other_node] for other_node in V_k[k] if other_node != node)
            if score < min_distance:
                min_distance = score
                best_node = node
        product_nodes_dict[k] = best_node
        product_nodes.append(best_node)
    
    unique_product_nodes = list(set(product_nodes))

    # Heuristic to determine the order of the nodes using the nearest neighbor heuristic
    current_node = v_0
    if current_node in unique_product_nodes:
        ordered_nodes = []
    else:
        ordered_nodes = [current_node]
    remaining_nodes = set(unique_product_nodes)
    if last_product != None and last_product in remaining_nodes:
        remaining_nodes.remove(last_product)

    while remaining_nodes:
        if next_product and product_nodes_dict[next_product] in remaining_nodes:
            next_node = product_nodes_dict[next_product]
        else:
            next_node = min(remaining_nodes, key=lambda node: distance[current_node, node])
        ordered_nodes.append(next_node)
        remaining_nodes.remove(next_node)
        current_node = next_node
    
    if last_product != None:
        ordered_nodes.append(product_nodes_dict[last_product])

    # Ensure the path ends at the paying station
    ordered_nodes.append(v_end)

    #Calculate the total distance and time
    total_distance = sum(distance[ordered_nodes[i], ordered_nodes[i+1]] for i in range(len(ordered_nodes)-1))
    total_time = sum(time[ordered_nodes[i], ordered_nodes[i+1]] for i in range(len(ordered_nodes)-1))

    #Provide all nodes to be visited consider the shortest path between them (use networkx to find the shortest path between nodes in ordered_nodes
    full_ordered_nodes = []
    for i in range(len(ordered_nodes)-1):
        path = nx.shortest_path(G, ordered_nodes[i], ordered_nodes[i+1], weight='length')
        full_ordered_nodes.extend(path[:-1])  # Exclude the last node to avoid duplication
    full_ordered_nodes.append(ordered_nodes[-1])  # Add the last node
    
    return ordered_nodes, product_nodes, total_time, total_distance #, full_ordered_nodes