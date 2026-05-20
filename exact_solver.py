import random

import gurobipy as gp
from gurobipy import GRB
import networkx as nx

def mip_solver(instance):
    G = instance['graph']
    products = instance['products']
    K = instance['K']
    V_pay = instance['V_pay']
    meat_station = instance['meat_station']
    fish_station = instance['fish_station']
    current_position = instance['v_0']
    frozen_last = instance['frozen_last']
    fresh_last = instance['fresh_last']
    next_product = instance['next_product']
    last_product = instance['last_product']
    precedence_constraints = instance['precedence_constraints']
    meat_wait_time = instance['meat_wait_time']
    fish_wait_time = instance['fish_wait_time']  
    target = instance['target']

    v_0 = instance['v_0'] 
    

    #Preprocessing the graph

    V_k = {product: [] for product in K}
    for product in V_k:
        for node in products[product]['locations']:
            V_k[product].append(node)


    #Total nodes (join start_node and all product locations)
    V_products = [node for product in V_k for node in V_k[product]]

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


    # Store the d(i,j) for nodes in total_nodes (assuming the graph shortest paths)
    distance = {(i, j): nx.shortest_path_length(G, i, j, weight='length') for i in V for j in V if i != j}
    time = {(i, j): nx.shortest_path_length(G, i, j, weight='time') for i in V for j in V if i != j}

    for i in V:
        distance[v_0, i] = nx.shortest_path_length(G, current_position, i, weight='length')
        distance[i, v_0] = nx.shortest_path_length(G, i, current_position, weight='length')
        time[v_0, i] = nx.shortest_path_length(G, current_position, i, weight='time')
        time[i, v_0] = nx.shortest_path_length(G, i, current_position, weight='time')
    
    V += [v_0]

    # Create a Gurobi model
    model = gp.Model("Shopping_Optimization")

    model.setParam('OutputFlag', 0)

    # Decision Variables
    #UsedArcBinary = model.addVars(V, V, vtype=GRB.BINARY, name="UsedArc")
    A = [(i,j) for i in V for j in V if i != j]
    UsedArcBinary = model.addVars(A, vtype=GRB.BINARY)

    # Binary variables for whether product k is picked at node i
    ProductNodeBinary = model.addVars(K, V_products, vtype=GRB.BINARY, name="ProductNode")

    # Auxiliary Variables
    TotalDistance = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name="TotalDistance")
    max_time_bound = max(time[i, j] for i in V for j in V if i != j) * len(V)
    NodeTime = model.addVars(V, vtype=GRB.CONTINUOUS, lb=0, ub=max_time_bound, name="NodeTime")
    ProductTime = model.addVars(K, vtype=GRB.CONTINUOUS, lb=0, ub=max_time_bound, name="ProductTime")
    MaxTime = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name="MaxTime")


    # Objective Function: Minimize shopping time
    if target == 'min_time':
        model.setObjective(MaxTime, GRB.MINIMIZE)
    elif target == 'min_distance':
        model.setObjective(TotalDistance, GRB.MINIMIZE)

    # Constraints

    # Each product must be picked exactly once
    model.addConstrs((gp.quicksum(ProductNodeBinary[k, i] for i in V_k[k]) == 1 for k in K), name="PickEachProduct")

    # Each product can only be served in locations where it is available
    model.addConstrs(ProductNodeBinary[k,i] == 0 for k in K for i in V_products if i not in V_k[k])

    # If a product is picked at node i, the node must be visited
    model.addConstrs((gp.quicksum(UsedArcBinary[j, i] for j in V if j != i) >= ProductNodeBinary[k, i] for k in K for i in V_products), name="VisitNodeForProduct")

    # Start at the initial node
    model.addConstr(gp.quicksum(UsedArcBinary[v_0, j] for j in V if j != v_0) == 1, name="StartAtInitialNode")

    # Finish at a paying station
    model.addConstr(gp.quicksum(UsedArcBinary[i, j] for i in V for j in V_pay if i!=j) == 1, name="FinishAtPayingStation")

    # Flow conservation at each node
    model.addConstrs((gp.quicksum(UsedArcBinary[i, j] for j in V if j != i) == gp.quicksum(UsedArcBinary[j, i] for j in V if j != i) for i in V_products), name="FlowConservation")

    # Relation between product and node times
    model.addConstrs((ProductTime[k] == gp.quicksum(ProductNodeBinary[k, i] * NodeTime[i] for i in V_k[k]) for k in K), name="ProductTime")
    
    #M = 200
    #Make M as small as possible
    M = max_time_bound + 1
    # Time update constraint
    #model.addConstrs((NodeTime[j] >= NodeTime[i] + time[i, j] - (1 - UsedArcBinary[i, j]) * M for i in V for j in V if j!=i), name="TimeUpdate")
    #model.addConstrs((NodeTime[j] <= NodeTime[i] + time[i, j] + (1 - UsedArcBinary[i, j]) * M for i in V for j in V if j!=i), name="TimeUpdate")
    
    for i in V:
        for j in V:
            if i != j:
                model.addGenConstrIndicator(
                UsedArcBinary[i,j], True,
                NodeTime[j] >= NodeTime[i] + time[i,j]
                )
    
    if frozen_last and fresh_last:
        # Frozen products must be served within time limit
        #model.addConstrs((MaxTime - ProductTime[k] <= frozen_last for k in K_frozen), name="FrozenTimeLimit")
        #Ensure that frozen products are the last to be picked
        model.addConstrs((ProductTime[k] >= ProductTime[u] for k in K_frozen+K_fresh for u in K if u not in K_frozen+K_fresh and u != last_product), name="FrozenOrder")
    elif frozen_last:
        # Frozen products must be served within time limit
        #model.addConstrs((MaxTime - ProductTime[k] <= frozen_last for k in K_frozen), name="FrozenTimeLimit")
        model.addConstrs((ProductTime[k] >= ProductTime[u] for k in K_frozen for u in K if u not in K_frozen and u != last_product), name="FrozenOrder")
    elif fresh_last:
        # Fresh products must be served within time limit
        #model.addConstrs((MaxTime - ProductTime[k] <= fresh_last for k in K_fresh), name="FreshTimeLimit")
        model.addConstrs((ProductTime[k] >= ProductTime[u] for k in K_fresh for u in K if u not in K_fresh and u != last_product), name="FreshOrder")

    # Definition of MaxTime
    model.addConstrs((MaxTime >= NodeTime[i] for i in V), name="DefineMaxTime")

    # Definition the TotalDistance
    model.addConstr(TotalDistance == gp.quicksum(UsedArcBinary[i, j] * distance[i, j] for i in V for j in V if i != j), name="TotalDistance")

    #Define that no arcs leave the paying station
    #model.addConstrs(UsedArcBinary[i, j] == 0 for i in V_pay for j in V if j != i)
    
    
    if K_meat != [] and meat_wait_time != None:
        model.addConstr(NodeTime[meat_station] >= meat_wait_time, name="MeatStationTimeLimit")
       
    if K_fish != [] and fish_wait_time != None:
        model.addConstr(NodeTime[fish_station] >= fish_wait_time, name="FishStationTimeLimit")

    # CONSTRAINTS BY RECQUEST   

    if precedence_constraints != None:
        # Precedence constraint (between product 5 and 6 using ProductTime)
        for value_id,value in enumerate(precedence_constraints):
            first_product = value[0]
            second_product = value[1]
            model.addConstr(ProductTime[first_product] <= ProductTime[second_product], name="PrecedenceConstraint_" + str(value_id))


    if next_product != None:
        # First product to be picked is product 4
        model.addConstrs(ProductTime[next_product] <= ProductTime[k] for k in K if k != next_product)

    if last_product != None:
        # Last product to be picked is product 80
        model.addConstrs(ProductTime[last_product] >= ProductTime[k] for k in K if k != last_product)

    #Set gap to 0
    model.setParam('MIPGap', 0)

    # Optimize the model
    model.optimize()

    # Display results
    #if model.status == GRB.OPTIMAL or model.MIPGap < 0.5:
    if model.status == GRB.OPTIMAL:
        if target == 'min_time':
            print("Optimal shopping time:", MaxTime.X)
        elif target == 'min_distance':
            print("Optimal total distance:", TotalDistance.X)
    else:
        print("No optimal solution found.")

    #Extract the ordered nodes
    ordered_nodes = [current_position]
    current_node = v_0
    idx = 1
    while current_node not in V_pay:
        for j in V:
            if current_node != j and UsedArcBinary[current_node, j].X > 0.5:
                if idx == 1 and j == current_position:
                    pass
                else:
                    ordered_nodes.append(j)
                current_node = j
                idx+=1
                break

    #Extrac a vector with the size of K with the corresponding node for each product
    product_nodes = []
    for product in K:
        for node in V_k[product]:
            if ProductNodeBinary[product, node].X > 0.5:
                product_nodes.append(node)
    
    #print('MaxTime:', MaxTime.X)
    #print('TotalDistance:', TotalDistance.X)

    # Print the node time of all visited nodes
    #for node in ordered_nodes:
    #    print(f"Node {node} time: {NodeTime[node].X}")

    return ordered_nodes, product_nodes, MaxTime.X, TotalDistance.X

if __name__ == "__main__":

    from graph import create_graph
    from product_catalogue import read_products_from_excel
    import numpy as np

    # Import the products from the excel file
    file_path = 'products.xlsx'
    products=read_products_from_excel(file_path)

    #Create Matosinhos store
    horizontal = [1,1,2,2,2,2,1,2,2,2,2,1]
    max_row = 15
    V_pay = [14]
    meat_station = 112
    fish_station = 114
    V_frozen = [77, 85, 93, 101]
    V_fresh = [82, 90, 98, 106, 83, 91, 99, 107]

    G, nodes = create_graph(horizontal, max_row, products, V_pay,  V_frozen, V_fresh, meat_station, fish_station)

    #Test the MIP solver
    K = random.sample(list(products.keys()), 10)
    K = [37,38,52]
    frozen_last = 2
    fresh_last = 2
    v_0 = 0
    next_product = None
    last_product = None
    precedence_constraints = None
    meat_wait_time = None
    fish_wait_time = None
    target = 'min_time' 
    #target = 'min_distance' 
    instance = {'graph': G, 'products': products, 'K': K, 'V_pay': V_pay, 'meat_station': meat_station, 'fish_station': fish_station, 'v_0': v_0, 'frozen_last': frozen_last, 'fresh_last': fresh_last, 'next_product': next_product, 'last_product': last_product, 'precedence_constraints': precedence_constraints, 'meat_wait_time': meat_wait_time, 'fish_wait_time': fish_wait_time, 'target': target}
    ordered_nodes, product_nodes, shopping_time, total_distance = mip_solver(instance)

    print("Ordered nodes:", ordered_nodes)