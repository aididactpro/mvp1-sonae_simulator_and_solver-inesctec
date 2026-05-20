import networkx as nx
import numpy as np

def verification(G, products, K, V_pay, v_0, first_product, last_product, precedences, ordered_nodes, product_nodes, meat_station, fish_station, meat_wait_time, fish_wait_time):
    #Preprocessing the graph
    V_k = {product: [] for product in K}
    for product in V_k:
        for node in products[product]['locations']:
            V_k[product].append(node)

    #Total nodes (join start_node and all product locations)
    V_products = [v_0] + [node for product in V_k for node in V_k[product]]
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
    distance = {(i, j): nx.shortest_path_length(G, i, j, weight='length') for i in V for j in V if i != j}
    time = {(i, j): nx.shortest_path_length(G, i, j, weight='time') for i in V for j in V if i != j}

    # Check if the solution is feasible
    first_node_constraint = False
    last_node_constraint = False
    all_products_delivered = False
    first_product_constraint = False
    last_product_constraint = False
    precedence_constraints = False
    frozen_time = None
    fresh_time = None

    #Verify if the first node is the start node
    if ordered_nodes[0] == v_0:
        first_node_constraint = True

    #Verify if the last node is a payment node
    if ordered_nodes[-1] in V_pay:
        last_node_constraint = True

    # Verify if all products are delivered
    unique_product_nodes = list(set(product_nodes))
    if v_0 in unique_product_nodes:
        if sorted(unique_product_nodes) == sorted(ordered_nodes[:-1]):
            all_products_delivered = True
    else: 
        if sorted(unique_product_nodes) == sorted(ordered_nodes[1:-1]):
            all_products_delivered = True

    #Verify if the first_product constraint is satisfied
    if first_product != None:
        if v_0 in product_nodes:
            if ordered_nodes[0] in V_k[first_product]:
                first_product_constraint = True
        else:
            if ordered_nodes[1] in V_k[first_product]:
                first_product_constraint = True
    else:
        first_product_constraint = None
    
    #Verify if the last_product constraint is satisfied
    if last_product != None:
        if ordered_nodes[-2] in V_k[last_product]:
            last_product_constraint = True
    else:
        last_product_constraint = None

    # Calculate the time in each node
    time_node = {node: 0 for node in ordered_nodes}
    for i in range(len(ordered_nodes)-1):
        if ordered_nodes[i+1] == meat_station and meat_wait_time != None:
            time_node[ordered_nodes[i+1]] = max(time_node[ordered_nodes[i]] + time[(ordered_nodes[i], ordered_nodes[i+1])],meat_wait_time)
        elif ordered_nodes[i+1] == fish_station and fish_wait_time != None:
            time_node[ordered_nodes[i+1]] = max(time_node[ordered_nodes[i]] + time[(ordered_nodes[i], ordered_nodes[i+1])],fish_wait_time)
        else:
            time_node[ordered_nodes[i+1]] = time_node[ordered_nodes[i]] + time[(ordered_nodes[i], ordered_nodes[i+1])]
        
    last_node_time = time_node[ordered_nodes[-1]]

    # Calculate the product time
    product_time = {product: 0 for product in K}
    for id, node in enumerate(product_nodes):
        product_time[K[id]] = time_node[node]
    
    # Calculate the difference between frozen product time and the last node time
    frozen_product_time = [product_time[product] for product in K_frozen]
    if frozen_product_time != []:
        max_frozen_product_time = max(frozen_product_time)
        frozen_time = int(last_node_time - max_frozen_product_time)
    else:
        frozen_time = None

    # Calculate the difference between fresh product time and the last node time
    fresh_product_time = [product_time[product] for product in K_fresh]
    if fresh_product_time != []:
        max_fresh_product_time = max(fresh_product_time)
        fresh_time = int(last_node_time - max_fresh_product_time)
    else:
        fresh_time = None

    # Calculate the difference between meat product time and the last node time
    meat_time = None
    meat_time_vector = [product_time[product] for product in K_meat]
    if meat_time_vector != []:
        meat_time = int(max(meat_time_vector))
    else:
        meat_time = None

    # Calculate the difference between fish product time and the last node time
    fish_time = None
    fish_time_vector = [product_time[product] for product in K_fish]
    if fish_time_vector != []:
        fish_time = int(max(fish_time_vector))
    else:
        fish_time = None

    
    #Calculate the time and distance of the solution
    time_solution = 0
    distance_solution = 0
    for i in range(len(ordered_nodes)-1):
        #time_solution += time[(ordered_nodes[i], ordered_nodes[i+1])]
        distance_solution += distance[(ordered_nodes[i], ordered_nodes[i+1])]
    
    distance_solution = int(distance_solution)
    time_solution = int(time_node[ordered_nodes[-1]])
    
    #Verify if the precedences constraint is satisfied
    if precedences != []:
        for precedence in precedences:
            product_1_locations = V_k[precedence[0]]
            product_2_locations = V_k[precedence[1]]
            product_1_delivered = any(node in ordered_nodes for node in product_1_locations)
            product_2_delivered = any(node in ordered_nodes for node in product_2_locations)
            if product_1_delivered and product_2_delivered:
                product_1_index = min(ordered_nodes.index(node) for node in product_1_locations if node in ordered_nodes)
                product_2_index = min(ordered_nodes.index(node) for node in product_2_locations if node in ordered_nodes)
                if product_1_index < product_2_index:
                    precedence_constraints = True
                    break
    else:
        precedence_constraints = None
    
    output_instance = {
        'first_node_constraint': first_node_constraint,
        'last_node_constraint': last_node_constraint,
        'all_products_delivered': all_products_delivered,
        'first_product_constraint': first_product_constraint,
        'last_product_constraint': last_product_constraint,
        'precedence_constraints': precedence_constraints,
        'time_solution': time_solution,
        'distance_solution': distance_solution,
        'frozen_time': frozen_time,
        'fresh_time': fresh_time,
        'meat_time': meat_time,
        'fish_time': fish_time
    }

    return output_instance



    




    