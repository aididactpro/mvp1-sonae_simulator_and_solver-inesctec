
################# LIBRARY IMPORTATION ####################

import streamlit as st
import networkx as nx
import numpy as np
import pandas as pd
import time
from streamlit_gsheets import GSheetsConnection

################# FILE IMPORTATION ####################

from heuristic_solver import heuristic_solver
from verification import verification
from visualize_store_dynamic import visualize_store_dynamic
from graph import create_graph, get_movement_bools
from product_catalogue import read_products_from_excel, read_products_from_json
#from exact_solver import mip_solver

################# STREAMLIT CONFIGURATION ####################

st.set_page_config(page_title=" MATOSINHOS SIMULATION 🛒", 
page_icon="🛒", 
layout="wide"
)

################# INITIALIZE ALL STATE VARIABLES ####################

none_st_variables = ['next_product', 'last_product', 'meat_wait_time', 'fish_wait_time', 'ExpectedShoppingTime', 'ExpectedShoppingDistance', 'products_to_purchase', 'satisfaction', 'survey', 'cf_meat', 'cf_fish', 'cf_frozen', 'cf_fresh', 'cf_next', 'cf_last']

for variable in none_st_variables:
    if variable not in st.session_state:
        st.session_state[variable] = None
    
false_st_variables = ['disable_up', 'disable_down', 'disable_left', 'disable_right', 'checkout', 'show_verification','frozen_last', 'fresh_last']

for variable in false_st_variables:
    if variable not in st.session_state:
        st.session_state[variable] = False

true_st_variables = ['xai_counterfactuals']

for variable in true_st_variables:
    if variable not in st.session_state:
        st.session_state[variable] = True

empty_list_st_variables = ['shopping_list', 'basket', 'ordered_nodes', 'product_nodes', 'precedence_constraints', 'after', 'before', 'history_current_position', 'history_current_time', 'history_meat_wait_time', 'history_fish_wait_time', 'history_shopping_list', 'history_basket', 'history_expected_shopping_time', 'history_expected_shopping_distance', 'history_action', 'history_proposed_action', "history_next_product", "history_last_product", "history_precedences", "frozen_products", "fresh_products", "selected_categories", "ordered_products", "history_frozen_last", "history_fresh_last", "history_ordered_nodes", "history_product_nodes", "history_ordered_products", "cf_precedence", "before_private_list", "after_private_list", "infeasible_constraints"]

for variable in empty_list_st_variables:
    if variable not in st.session_state:
        st.session_state[variable] = []

if 'current_position' not in st.session_state:
    st.session_state.current_position = 0

if 'current_time' not in st.session_state:
    st.session_state.current_time = 0

if 'avatar' not in st.session_state:
    st.session_state.avatar = "🧍"

if 'target' not in st.session_state:
    st.session_state.target = "Minimize shopping time"

if 'solver' not in st.session_state:
    st.session_state.solver = heuristic_solver #mip_solver

################## STORE CONFIGURATION ####################

# Import the products from the excel file
if 'products' not in st.session_state:
    
    file_path = 'products.xlsx'
    st.session_state.products = read_products_from_excel(file_path)
    st.session_state.product_ids = list(st.session_state.products.keys())


V_pay = [109]
meat_station = 98
fish_station = 102
V_frozen = [63, 71, 79, 87]
V_fresh = [68, 76, 84, 92, 79, 77, 85, 93]
horizontal = [1,2,2,2,2,1,2,2,2,2,1]
max_column = 15

if 'G' not in st.session_state and 'nodes' not in st.session_state:
    #Create Matosinhos store
    st.session_state.G, st.session_state.nodes = create_graph(horizontal, max_column, st.session_state.products, V_pay,  V_frozen, V_fresh, meat_station, fish_station)
    st.session_state.bias_G = st.session_state.G.copy()
    #Add bias to the edges more distant from (0,0)
    for i in st.session_state.G.nodes:
        for j in st.session_state.G.nodes:
            if i != j:
                distance = nx.shortest_path_length(st.session_state.G, source=i, target=j, weight='distance')
                bias = 1+ 0.001 * (st.session_state.nodes[i].coords[0] + st.session_state.nodes[i].coords[1] + st.session_state.nodes[j].coords[0] + st.session_state.nodes[j].coords[1])
                st.session_state.bias_G.add_edge(i, j, length=distance+bias, time=distance+bias)


movement_options = get_movement_bools(st.session_state.nodes)

################# SOLVER FUNCTION ####################

def run_solver():

    input_instance = {
                    "graph": st.session_state.G, 
                    "products": st.session_state.products, 
                    "K": st.session_state.shopping_list, 
                    "V_pay": V_pay, 
                    "meat_station": meat_station, 
                    "fish_station": fish_station, 
                    "v_0": st.session_state.current_position, 
                    "frozen_last": st.session_state.frozen_last, 
                    "fresh_last": st.session_state.fresh_last, 
                    "next_product": st.session_state.next_product, 
                    "last_product": st.session_state.last_product, 
                    "precedence_constraints": st.session_state.precedence_constraints, 
                    "meat_wait_time": st.session_state.meat_wait_time, 
                    "fish_wait_time": st.session_state.fish_wait_time,
                    "target": "min_time" if st.session_state.target == "Minimize shopping time" else "min_distance"
                    }

    if st.session_state.current_position in V_pay:

        st.session_state.ordered_nodes = []
        st.session_state.product_nodes = []
        st.session_state.ExpectedShoppingTime = 0
        st.session_state.ExpectedShoppingDistance = 0
        st.session_state.checkout = True

    else:
        st.session_state.products_to_purchase = []
        st.session_state.ordered_nodes, st.session_state.product_nodes, st.session_state.ExpectedShoppingTime, st.session_state.ExpectedShoppingDistance = st.session_state.solver(input_instance)

        #Give me the ordered products given the ordered_nodes and the product_nodes
        st.session_state.ordered_products = []
        if st.session_state.ordered_nodes.count(st.session_state.ordered_nodes[0]) == 1:
            resized_ordered_nodes = st.session_state.ordered_nodes
        else:
            resized_ordered_nodes = st.session_state.ordered_nodes[1:]
        for node in resized_ordered_nodes:
            node_products = []
            for idx, product_node in enumerate(st.session_state.product_nodes):
                if product_node == node:
                    node_products.append(st.session_state.shopping_list[idx])
            if st.session_state.next_product != None and st.session_state.next_product in node_products:
                st.session_state.ordered_products.append(st.session_state.next_product)
                node_products.remove(st.session_state.next_product)
            if st.session_state.last_product == None or st.session_state.last_product not in node_products:
                st.session_state.ordered_products.extend(node_products)
            else:
                for product in node_products:
                    if product != st.session_state.last_product:
                        st.session_state.ordered_products.append(product)
                st.session_state.ordered_products.append(st.session_state.last_product)



        #st.session_state.verification = verification(st.session_state.G, st.session_state.products, st.session_state.shopping_list, V_pay, st.session_state.current_position, st.session_state.next_product, st.session_state.last_product, st.session_state.precedence_constraints, st.session_state.ordered_nodes, st.session_state.product_nodes, meat_station, fish_station, st.session_state.meat_wait_time, st.session_state.fish_wait_time)      
        #Find the shortest path between the first and second node

        if st.session_state.shopping_list != []:
            if st.session_state.product_nodes[st.session_state.shopping_list.index(st.session_state.ordered_products[0])] == st.session_state.current_position:
                st.session_state.products_to_purchase.append(st.session_state.ordered_products[0])
                if st.session_state.current_position == meat_station and st.session_state.meat_wait_time > 0:
                    st.session_state.next_node = meat_station
                    st.session_state.proposed_action = "wait"
                elif st.session_state.current_position == fish_station and st.session_state.fish_wait_time > 0:
                    st.session_state.next_node = fish_station
                    st.session_state.proposed_action = "wait"
                else:
                    st.session_state.next_node = st.session_state.current_position
                    st.session_state.proposed_action = "purchase"
            else:

                first_node = st.session_state.ordered_nodes[0]
                second_node = st.session_state.ordered_nodes[1]
                if first_node == second_node:
                    second_node = st.session_state.ordered_nodes[2]
                shortest_path = nx.shortest_path(st.session_state.G, source=first_node, target=second_node, weight='distance')
                st.session_state.next_node = shortest_path[1]
                #Get the action from Left, Right, Up, Down (get the key of the movement_options dictionary if the value is the next node)
                st.session_state.proposed_action = next(key for key, value in movement_options[st.session_state.current_position].items() if value == st.session_state.next_node)

        else:
            first_node = st.session_state.ordered_nodes[0]
            second_node = st.session_state.ordered_nodes[1]
            if first_node == second_node:
                second_node = st.session_state.ordered_nodes[2]
            shortest_path = nx.shortest_path(st.session_state.G, source=first_node, target=second_node, weight='distance')
            st.session_state.next_node = shortest_path[1]
            #Get the action from Left, Right, Up, Down (get the key of the movement_options dictionary if the value is the next node)
            st.session_state.proposed_action = next(key for key, value in movement_options[st.session_state.current_position].items() if value == st.session_state.next_node)

    get_counterfactuals()

def suggest_product():
    input_instance = {
                    "graph": st.session_state.G, 
                    "products": st.session_state.products, 
                    "K": st.session_state.shopping_list, 
                    "V_pay": V_pay, 
                    "meat_station": meat_station, 
                    "fish_station": fish_station, 
                    "v_0": st.session_state.current_position, 
                    "frozen_last": st.session_state.frozen_last, 
                    "fresh_last": st.session_state.fresh_last, 
                    "next_product": st.session_state.next_product, 
                    "last_product": st.session_state.last_product, 
                    "precedence_constraints": st.session_state.precedence_constraints, 
                    "meat_wait_time": st.session_state.meat_wait_time, 
                    "fish_wait_time": st.session_state.fish_wait_time,
                    "target": "min_time" if st.session_state.target == "Minimize shopping time" else "min_distance"
                    }

    action = None #policy(input_instance, st.session_state.recommendable_products, st.session_state.ordered_nodes, heuristic="closest_to_route")
    st.session_state.recommended_product = action
    

def get_counterfactuals():

    if len(st.session_state.shopping_list) >= 1 and st.session_state.current_position not in V_pay:

        input_instance = {
                        "graph": st.session_state.G, 
                        "products": st.session_state.products, 
                        "K": st.session_state.shopping_list, 
                        "V_pay": V_pay, 
                        "meat_station": meat_station, 
                        "fish_station": fish_station, 
                        "v_0": st.session_state.current_position, 
                        "frozen_last": st.session_state.frozen_last, 
                        "fresh_last": st.session_state.fresh_last, 
                        "next_product": st.session_state.next_product, 
                        "last_product": st.session_state.last_product, 
                        "precedence_constraints": st.session_state.precedence_constraints, 
                        "meat_wait_time": st.session_state.meat_wait_time, 
                        "fish_wait_time": st.session_state.fish_wait_time,
                        "target": "min_time" if st.session_state.target == "Minimize shopping time" else "min_distance"
                        }   
        
        input_meat = input_instance.copy()
        for product_id in st.session_state.shopping_list:
            if st.session_state.products[product_id]['meat'] == 1:
                break
            else:
                product_id = None 
        input_meat['next_product'] = product_id

        input_fish = input_instance.copy()
        for product_id in st.session_state.shopping_list:
            if st.session_state.products[product_id]['fish'] == 1:
                break
            else:
                product_id = None
        input_fish['next_product'] = product_id

        input_frozen = input_instance.copy()
        input_frozen['frozen_last'] = False

        input_fresh = input_instance.copy()
        input_fresh['fresh_last'] = False

        input_next = input_instance.copy()
        input_next['next_product'] = None

        input_last = input_instance.copy()
        input_last['last_product'] = None

        
        input_precedence = []
        baseline_input = input_instance.copy()
        all_constraints = st.session_state.precedence_constraints.copy()
        for precedence in st.session_state.precedence_constraints:
            baseline_input['precedence_constraints'] = all_constraints.remove(precedence)
            input_precedence.append(baseline_input)
        
        all_variations = []

        if st.session_state.meat_wait_time != None and st.session_state.next_product == None and not any(product in st.session_state.after for product in st.session_state.shopping_list if st.session_state.products[product]['meat'] == 1):
            all_variations.append("input_meat")
        else:
            st.session_state.cf_meat = None
        
        if st.session_state.fish_wait_time != None and st.session_state.next_product == None and not any(product in st.session_state.after for product in st.session_state.shopping_list if st.session_state.products[product]['fish'] == 1):
            all_variations.append("input_fish")
        else:
            st.session_state.cf_fish = None

        if st.session_state.frozen_products:
            all_variations.append("input_frozen")
        else:
            st.session_state.cf_frozen = None

        if st.session_state.fresh_products:
            all_variations.append("input_fresh")
        else:
            st.session_state.cf_fresh = None

        if st.session_state.next_product != None:
            all_variations.append("input_next")
        else:
            st.session_state.cf_next = None

        if st.session_state.last_product != None:
            all_variations.append("input_last")
        else:
            st.session_state.cf_last

        
        if st.session_state.precedence_constraints != []:
            all_variations.append("input_precedence")
        else:
            st.session_state.cf_precedence = []
        
        for variation in all_variations:
            if variation == "input_meat":
                ordered_nodes, product_nodes, ExpectedShoppingTime, ExpectedShoppingDistance = st.session_state.solver(input_meat)
                st.session_state.cf_meat = ExpectedShoppingTime - st.session_state.ExpectedShoppingTime
            elif variation == "input_fish":
                ordered_nodes, product_nodes, ExpectedShoppingTime, ExpectedShoppingDistance = st.session_state.solver(input_fish)
                st.session_state.cf_fish = ExpectedShoppingTime - st.session_state.ExpectedShoppingTime
            elif variation == "input_frozen":
                ordered_nodes, product_nodes, ExpectedShoppingTime, ExpectedShoppingDistance = st.session_state.solver(input_frozen)
                st.session_state.cf_frozen = ExpectedShoppingTime - st.session_state.ExpectedShoppingTime
            elif variation == "input_fresh":
                ordered_nodes, product_nodes, ExpectedShoppingTime, ExpectedShoppingDistance = st.session_state.solver(input_fresh)
                st.session_state.cf_fresh = ExpectedShoppingTime - st.session_state.ExpectedShoppingTime
            elif variation == "input_next":
                ordered_nodes, product_nodes, ExpectedShoppingTime, ExpectedShoppingDistance = st.session_state.solver(input_next)
                st.session_state.cf_next = ExpectedShoppingTime - st.session_state.ExpectedShoppingTime
            elif variation == "input_last":
                ordered_nodes, product_nodes, ExpectedShoppingTime, ExpectedShoppingDistance = st.session_state.solver(input_last)
                st.session_state.cf_last = ExpectedShoppingTime - st.session_state.ExpectedShoppingTime
            elif variation == "input_precedence":
                st.session_state.cf_precedence = []
                for specific_input in input_precedence:
                    ordered_nodes, product_nodes, ExpectedShoppingTime, ExpectedShoppingDistance = st.session_state.solver(specific_input)
                    st.session_state.cf_precedence.append(ExpectedShoppingTime - st.session_state.ExpectedShoppingTime)
        
def store_gsheet():

    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Read existing data from Google Sheets
    existing_action_data = conn.read(worksheet="main")

    st.session_state.date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    #Get the highest id in the existing data (column == "UserId") if there is no data, set id to 0
    try: 
        id = max(existing_action_data["UserId"]) + 1
    except:
        id = 0

    new_row_action =  pd.DataFrame({"UserId": [id for i in range(len(st.session_state.history_current_position))],
                        "Date": [st.session_state.date for i in range(len(st.session_state.history_current_position))],
                        "XAI": [st.session_state.xai_counterfactuals for i in range(len(st.session_state.history_current_position))],
                        "CurrentPosition": st.session_state.history_current_position,
                        "CurrentTime": st.session_state.history_current_time,
                        "MeatWaitTime": st.session_state.history_meat_wait_time,
                        "FishWaitTime": st.session_state.history_fish_wait_time,
                        "ShoppingList": st.session_state.history_shopping_list,
                        "Basket": st.session_state.history_basket,
                        "ExpectedShoppingTime": st.session_state.history_expected_shopping_time,
                        "ExpectedShoppingDistance": st.session_state.history_expected_shopping_distance,
                        "NextProduct": st.session_state.history_next_product,
                        "LastProduct": st.session_state.history_last_product,
                        "Precedences": st.session_state.history_precedences,
                        "LimitFresh": st.session_state.history_fresh_last,
                        "LimitFrozen": st.session_state.history_frozen_last,
                        "OrderedNodes": st.session_state.history_ordered_nodes,
                        "ProductNodes": st.session_state.history_product_nodes,
                        "OrderedProducts": st.session_state.history_ordered_products,
                        "Action": st.session_state.history_action,
                        "ProposedAction": st.session_state.history_proposed_action})

    if id == 0:
        updated_data_action = new_row_action
    else:
        # Append new data to the existing DataFrame
        updated_data_action = pd.concat([existing_action_data, new_row_action], ignore_index=True)

    # Update Google Sheets with the new combined data
    conn.update(worksheet="main", data=updated_data_action)

    existing_feedback_data = conn.read(worksheet="feedback")

    new_row_feedback =  pd.DataFrame({"UserId": [id],
                                    "Date": [st.session_state.date],
                                    "XAI": [st.session_state.xai_counterfactuals],
                                    "Satifaction": [st.session_state.satisfaction],
                                    "Survey": [st.session_state.survey]})
    
    # Append new data to the existing DataFrame
    updated_data_feedback = pd.concat([existing_feedback_data, new_row_feedback], ignore_index=True)

    # Update Google Sheets with the new combined data
    conn.update(worksheet="feedback", data=updated_data_feedback)

    existing_preferences_data = conn.read(worksheet="preferences")

    new_row_preferences =  pd.DataFrame({"UserId": [id],
                                         "Date": [st.session_state.date],
                                         "Preferences": [st.session_state.selected_categories]})

    updated_data_preferences = pd.concat([existing_preferences_data, new_row_preferences], ignore_index=True)

    conn.update(worksheet="preferences", data=updated_data_preferences)

    st.stop()

def purchase(selected_product_ids):
    with col2:
        if st.session_state.current_position == meat_station and st.session_state.meat_wait_time != 0:
            st.warning("You must wait for your turn at the meat station!")
        elif st.session_state.current_position == fish_station and st.session_state.fish_wait_time != 0:
            st.warning("You must wait for your turn at the fish station!")
        else:
            for product_id in selected_product_ids:
                if product_id not in st.session_state.basket:
                    st.session_state.basket.append(product_id)
                    st.success(f"{st.session_state.products[product_id]['name']} {st.session_state.products[product_id]['icon']} added to basket!")
                if product_id in st.session_state.shopping_list:
                    st.session_state.shopping_list.remove(product_id)
                    if st.session_state.next_product == product_id:
                        st.session_state.next_product = None
                    if st.session_state.last_product == product_id:
                        st.session_state.last_product = None
                    for precedence in st.session_state.precedence_constraints:
                        if product_id in precedence:
                            st.session_state.precedence_constraints.remove(precedence)
                    remaining_meat_products = [product_id for product_id in st.session_state.shopping_list if st.session_state.products[product_id]['meat'] == 1]
                    remaining_fish_products = [product_id for product_id in st.session_state.shopping_list if st.session_state.products[product_id]['fish'] == 1]
                    if st.session_state.meat_wait_time != None and st.session_state.products[product_id]['meat'] == 1 and len(remaining_meat_products) == 0:
                        st.session_state.meat_wait_time = None
                    if st.session_state.fish_wait_time != None and st.session_state.products[product_id]['fish'] == 1 and len(remaining_fish_products) == 0:
                        st.session_state.fish_wait_time = None

        st.session_state.frozen_products = [product_id for product_id in st.session_state.shopping_list if st.session_state.products[product_id]['frozen'] == 1]
        st.session_state.fresh_products = [product_id for product_id in st.session_state.shopping_list if st.session_state.products[product_id]['fresh'] == 1]
        run_solver()

def update_all_info(action):

    st.session_state.history_current_position.append(int(st.session_state.current_position))
    st.session_state.history_current_time.append(int(st.session_state.current_time))
    st.session_state.history_meat_wait_time.append(st.session_state.meat_wait_time)
    st.session_state.history_fish_wait_time.append(st.session_state.fish_wait_time)
    st.session_state.history_shopping_list.append(','.join(map(str, st.session_state.shopping_list)))
    st.session_state.history_basket.append(','.join(map(str, st.session_state.basket)))
    st.session_state.history_expected_shopping_time.append(int(st.session_state.ExpectedShoppingTime))
    st.session_state.history_expected_shopping_distance.append(int(st.session_state.ExpectedShoppingDistance))
    st.session_state.history_next_product.append(st.session_state.next_product)
    st.session_state.history_last_product.append(st.session_state.last_product)
    st.session_state.history_precedences.append(','.join(map(str, st.session_state.precedence_constraints)))
    st.session_state.history_fresh_last.append(st.session_state.fresh_last)
    st.session_state.history_frozen_last.append(st.session_state.frozen_last)
    st.session_state.history_ordered_nodes.append(','.join(map(str, st.session_state.ordered_nodes)))
    st.session_state.history_product_nodes.append(','.join(map(str, st.session_state.product_nodes)))
    st.session_state.history_ordered_products.append(','.join(map(str, st.session_state.ordered_products)))
    st.session_state.history_action.append(action)
    st.session_state.history_proposed_action.append(st.session_state.proposed_action)


########################## UPDADE MOVEMENT OPTIONS FUNCTION ############################

def update_movement_options():
        st.session_state.up = movement_options[st.session_state.current_position]['up']
        if st.session_state.up == None:
            st.session_state.disable_up = True
        else:
            st.session_state.disable_up = False
        st.session_state.down = movement_options[st.session_state.current_position]['down']
        if st.session_state.down == None:
            st.session_state.disable_down = True
        else:
            st.session_state.disable_down = False
        st.session_state.left = movement_options[st.session_state.current_position]['left']
        if st.session_state.left == None:
            st.session_state.disable_left = True
        else:
            st.session_state.disable_left = False
        st.session_state.right = movement_options[st.session_state.current_position]['right']
        if st.session_state.right == None:
            st.session_state.disable_right = True
        else:
            st.session_state.disable_right = False

def move_up():
    st.session_state.current_position = st.session_state.up
    update_movement_options()
    if st.session_state.meat_wait_time != None and st.session_state.meat_wait_time > 0:
        st.session_state.meat_wait_time -= 1
    if st.session_state.fish_wait_time != None and st.session_state.fish_wait_time > 0:
        st.session_state.fish_wait_time -= 1
    st.session_state.current_time += 1
    update_all_info("up")
    run_solver()

def move_left():
    st.session_state.current_position = st.session_state.left
    update_movement_options()
    if st.session_state.meat_wait_time != None and st.session_state.meat_wait_time > 0:
        st.session_state.meat_wait_time -= 1
    if st.session_state.fish_wait_time != None and st.session_state.fish_wait_time > 0:
        st.session_state.fish_wait_time -= 1
    st.session_state.current_time += 1
    update_all_info("left")
    run_solver()

def move_right():
    # Normal movement if not a paying node
    st.session_state.current_position = st.session_state.right
    update_movement_options()
    if st.session_state.meat_wait_time is not None and st.session_state.meat_wait_time > 0:
        st.session_state.meat_wait_time -= 1
    if st.session_state.fish_wait_time is not None and st.session_state.fish_wait_time > 0:
        st.session_state.fish_wait_time -= 1
    st.session_state.current_time += 1
    update_all_info("right")
    run_solver()

def wait():
    if st.session_state.meat_wait_time != None and st.session_state.meat_wait_time > 0:
        st.session_state.meat_wait_time -= 1
    if st.session_state.fish_wait_time != None and st.session_state.fish_wait_time > 0:
        st.session_state.fish_wait_time -= 1
    st.session_state.current_time += 1
    update_all_info("wait")
    run_solver()

def move_down():
    
    if st.session_state.down in V_pay:
        st.session_state.shopping_list = []
        st.session_state.next_product = None
        st.session_state.last_product = None
        st.session_state.precedence_constraints = []
    
    st.session_state.current_position = st.session_state.down
    update_movement_options()
    if st.session_state.meat_wait_time != None and st.session_state.meat_wait_time > 0:
        st.session_state.meat_wait_time -= 1
    if st.session_state.fish_wait_time != None and st.session_state.fish_wait_time > 0:
        st.session_state.fish_wait_time -= 1
    st.session_state.current_time += 1
    update_all_info("down")
    run_solver()

def follow_proposed_action():
    if st.session_state.proposed_action == "purchase":
        purchase(st.session_state.products_to_purchase)
    else:
        if st.session_state.meat_wait_time != None and st.session_state.meat_wait_time > 0:
            st.session_state.meat_wait_time -= 1
        if st.session_state.fish_wait_time != None and st.session_state.fish_wait_time > 0:
            st.session_state.fish_wait_time -= 1
        st.session_state.current_time += 1
        if st.session_state.proposed_action != "wait":
            st.session_state.current_position = st.session_state.next_node
            update_movement_options()
            update_all_info(st.session_state.proposed_action)
    run_solver()

def show_verification_ghost():
    pass

def show_verification():
    st.session_state.verification = verification(st.session_state.G, st.session_state.products, st.session_state.shopping_list, V_pay, st.session_state.current_position, st.session_state.next_product, st.session_state.last_product, st.session_state.precedence_constraints, st.session_state.ordered_nodes, st.session_state.product_nodes, meat_station, fish_station, st.session_state.meat_wait_time, st.session_state.fish_wait_time)

    if st.session_state.verification['first_node_constraint'] == True:
        st.write("First node constraint satisfied ✅")
    elif st.session_state.verification['first_node_constraint'] == False:
        st.write("First node constraint not satisfied ❌")
    elif st.session_state.verification['first_node_constraint'] == None:
        st.write("First node constraint not applicable ❓")
    
    if st.session_state.verification['last_node_constraint'] == True:
        st.write("Last node constraint satisfied ✅")
    elif st.session_state.verification['last_node_constraint'] == False:
        st.write("Last node constraint not satisfied ❌")
    elif st.session_state.verification['last_node_constraint'] == None:
        st.write("Last node constraint not applicable ❓")
    
    if st.session_state.verification['all_products_delivered'] == True:
        st.write("All products delivered ✅")
    elif st.session_state.verification['all_products_delivered'] == False:
        st.write("All products not delivered ❌")
    elif st.session_state.verification['all_products_delivered'] == None:
        st.write("All products delivered not applicable ❓")

    if st.session_state.next_product != None:    
        if st.session_state.verification['first_product_constraint'] == True:
            st.write("First product constraint satisfied ✅")
        elif st.session_state.verification['first_product_constraint'] == False:
            st.write("First product constraint not satisfied ❌")
        
    if st.session_state.last_product != None:
        if st.session_state.verification['last_product_constraint'] == True:
            st.write("Last product constraint satisfied ✅")
        elif st.session_state.verification['last_product_constraint'] == False:
            st.write("Last product constraint not satisfied ❌")
    
    if st.session_state.precedence_constraints != []:
        if st.session_state.verification['precedence_constraints'] == True:
            st.write("Precedences constraint satisfied ✅")
        elif st.session_state.verification['precedence_constraints'] == False:
            st.write("Precedences constraint not satisfied ❌")

    if st.session_state.verification['fresh_time']!= None:
        st.write(f"Fresh product time: {st.session_state.verification['fresh_time']}")

    if st.session_state.verification['frozen_time']!= None:
        st.write(f"Frozen product time: {st.session_state.verification['frozen_time']}")
    
    if st.session_state.verification['meat_time']!= None:
        st.write(f"Meat time: {st.session_state.verification['meat_time']}")

    if st.session_state.verification['fish_time']!= None:
        st.write(f"Fish time: {st.session_state.verification['fish_time']}")
    
    st.write(f"Total shopping time: {int(st.session_state.verification['time_solution'])}")

    st.write(f"Total shopping distance: {int(st.session_state.verification['distance_solution'])}")




























################# SHOPPING LIST AND BASKET ###################

with st.sidebar:
    st.subheader("Customer menu")

    with st.expander("Shopping List 🛒"):
        st.write("Here you can manage your shopping list.")
        
        # Multiselect with product IDs but displaying names
        selected_product_ids = st.multiselect(
            "Select products to add",
            options=st.session_state.product_ids,
            format_func=lambda product_id: st.session_state.products[product_id]["name"] + " " + st.session_state.products[product_id]["icon"]
        )

        # Button to add selected products to the shopping list
        if st.button("Add products"):
            st.session_state.shopping_list.extend(selected_product_ids)
            st.session_state.shopping_list = list(set(st.session_state.shopping_list))  # Remove duplicates
            st.success("Products added to shopping list!")
            st.session_state.selected_product_ids = []
            for product_id in selected_product_ids:
                if st.session_state.products[product_id]['meat'] == 1:
                    #st.session_state.meat_wait_time = int(np.random.normal(35, 10))
                    st.session_state.meat_wait_time = 30
                if st.session_state.products[product_id]['fish'] == 1:
                    #st.session_state.fish_wait_time = int(np.random.normal(35, 10))
                    st.session_state.fish_wait_time = 30
                if st.session_state.products[product_id]['fresh'] == 1:
                    st.session_state.fresh_products.append(product_id)
                if st.session_state.products[product_id]['frozen'] == 1:
                    st.session_state.frozen_products.append(product_id)
            run_solver()
        
        if st.button("Remove products"):
            removed_product_names = []
            for product_id in selected_product_ids:
                if product_id in st.session_state.shopping_list:
                    st.session_state.shopping_list.remove(product_id)
                    #Remove constraints that may include the product
                    if st.session_state.next_product == product_id:
                        st.session_state.next_product = None
                    if st.session_state.last_product == product_id:
                        st.session_state.last_product = None
                    for precedence in st.session_state.precedence_constraints:
                        if product_id in precedence:
                            st.session_state.precedence_constraints.remove(precedence)
                    removed_product_names.append(st.session_state.products[product_id]['name'] + " " + st.session_state.products[product_id]['icon'])
            
            if removed_product_names:
                st.success(f"Removed from shopping list: {', '.join(removed_product_names)}")
                run_solver()
            
            if removed_product_names == []:
                st.warning("No products removed from shopping list!")
            else:
                pass            

        # Button to view the shopping list
        if st.session_state.shopping_list:
            st.write("**Your Shopping List:**")
            for item in st.session_state.shopping_list:
                st.write(f"- {st.session_state.products[item]['name']} {st.session_state.products[item]['icon']}")
        if st.session_state.basket:
            for item in st.session_state.basket:
                st.write(f"- {st.session_state.products[item]['name']} {st.session_state.products[item]['icon']} ✅")  
        else:
            st.write("Your shopping list is currently empty.")


#################### CONSTRAINTS ############################
    def reset_next_product():
        st.session_state.next_product = None
        run_solver()
    
    def reset_last_product():
        st.session_state.last_product = None
        run_solver()

    with st.expander("Constraints ⚙️"):
        st.write("Here you can set constraints for the simulation.")
        
        # Only show the input boxes if the user has selected products
        if st.session_state.shopping_list:

            if st.session_state.fresh_products and not any(product in st.session_state.before for product in st.session_state.fresh_products):
                st.checkbox("Collect fresh products in the end", key="fresh_last", value=False, on_change=run_solver)
                
            if st.session_state.frozen_products and not any(product in st.session_state.before for product in st.session_state.frozen_products):
                st.checkbox("Collect frozen products in the end", key="frozen_last", value=False, on_change=run_solver)
               
            next_product = st.selectbox("Select the next product to add", options = [product_id for product_id in st.session_state.shopping_list if product_id not in st.session_state.after and product_id != st.session_state.last_product], format_func = lambda product_id: st.session_state.products[product_id]['name'] + " " + st.session_state.products[product_id]['icon'])
            if st.button("Add next product"):
                st.session_state.next_product = next_product
                run_solver()

            last_product = st.selectbox("Select the last product to add", options = [product_id for product_id in st.session_state.shopping_list if product_id not in st.session_state.before and product_id != st.session_state.next_product], format_func = lambda product_id: st.session_state.products[product_id]['name'] + " " + st.session_state.products[product_id]['icon'])
            if st.button("Add last product"):
                st.session_state.last_product = last_product
                run_solver()
            
        
            
            st.write("Set Precedence Constraints")
            
            
            product_A = st.selectbox("Select Product A", options=[product_id for product_id in st.session_state.shopping_list if product_id != st.session_state.next_product and product_id != st.session_state.last_product], key="product_A", format_func = lambda product_id: st.session_state.products[product_id]['name']+" "+st.session_state.products[product_id]['icon'])
            st.write("before")
            product_B = st.selectbox("Select Product B", options=[product_id for product_id in st.session_state.shopping_list if product_id != st.session_state.next_product and product_id != st.session_state.last_product], key="product_B", format_func = lambda product_id: st.session_state.products[product_id]['name']+" "+st.session_state.products[product_id]['icon'])

            def has_cycle(graph, start, visited, rec_stack):
                """Detects cycles in the precedence graph using DFS."""
                visited.add(start)
                rec_stack.add(start)

                for neighbor in graph.get(start, []):
                    if neighbor not in visited:
                        if has_cycle(graph, neighbor, visited, rec_stack):
                            return True
                    elif neighbor in rec_stack:
                        return True  # Cycle detected

                rec_stack.remove(start)
                return False

            def is_constraint_feasible(all_nodes, constraints, new_constraint):
                """Checks if adding a new precedence constraint creates a cycle."""
                graph = {node: [] for node in all_nodes}
                
                # Build the graph from existing constraints
                for a, b in constraints:
                    graph[a].append(b)
                
                # Add the new constraint
                a, b = new_constraint
                graph[a].append(b)
                
                # Check for cycles
                visited = set()
                rec_stack = set()
                for node in all_nodes:
                    if node not in visited:
                        if has_cycle(graph, node, visited, rec_stack):
                            return False  # Cycle detected, constraint is infeasible
                
                return True  # No cycle detected, constraint is feasible

            if st.button("Add Precedence Constraint"):
                if product_A != product_B:
                    constraint = (product_A, product_B)
                    if constraint in st.session_state.precedence_constraints:
                        st.warning("Precedence constraint already exists!")
                    #elif constraint in st.session_state.infeasible_constraints:
                    elif not is_constraint_feasible(st.session_state.shopping_list, st.session_state.precedence_constraints, constraint):
                        st.warning("Constraint is infeasible!")
                    elif constraint[0] in V_fresh and st.session_state.fresh_last:
                        st.warning("Remember you want fresh products to be in the end!")
                    elif constraint[0] in V_frozen and st.session_state.frozen_last:
                        st.warning("Remember you want frozen products to be in the end!")
                    else:
                        if constraint[0] in V_fresh:
                            st.session_state.fresh_last = False
                        if constraint[0] in V_frozen:
                            st.session_state.frozen_last = False
                        st.session_state.before.append(constraint[0])
                        st.session_state.after.append(constraint[1])
                        st.session_state.infeasible_constraints.append((product_B, product_A))
                        for const in st.session_state.precedence_constraints:
                            if const[0] == product_B:
                                st.session_state.infeasible_constraints.append((const[1], product_A))
                            if const[1] == product_A:
                                st.session_state.infeasible_constraints.append((product_B, const[0]))
                        st.session_state.precedence_constraints.append(constraint)
                        st.success("Precedence constraint added!")  
                        run_solver()
                else:
                    st.warning("Product A and Product B must be different!")

            # Box to see the created precedence constraints allowing to remove them

            # Function to remove constraints
            
            st.write("Requests")
            for constraint in st.session_state.precedence_constraints:
                if st.button(f"Remove {st.session_state.products[constraint[0]]['name']}{st.session_state.products[constraint[0]]['icon']}-before-{st.session_state.products[constraint[1]]['name']}{st.session_state.products[constraint[1]]['icon']}", key=f"remove_{constraint}"):
                    st.session_state.before.remove(constraint[0])
                    st.session_state.after.remove(constraint[1])
                    st.session_state.precedence_constraints.remove(constraint)
                    for const in st.session_state.infeasible_constraints:
                        if const[0] or const[1] in constraint:
                            st.session_state.infeasible_constraints.remove(const)
                    run_solver()
                    st.rerun()
            

            if st.session_state.next_product != None:
                if st.button(f"Remove {st.session_state.products[st.session_state.next_product]['name']}{st.session_state.products[st.session_state.next_product]['icon']}-next", key=f"remove_next", on_click=reset_next_product):
                    pass

               
            if st.session_state.last_product != None:
                if st.button(f"Remove {st.session_state.products[st.session_state.last_product]['name']}{st.session_state.products[st.session_state.last_product]['icon']}-last", key=f"remove_last", on_click=reset_last_product):
                    pass
            
                    
    with st.expander("Target 🎯"):
        st.write("Select your target")
        target = st.radio(
            "What is your target?",
            ("Minimize shopping time", "Minimize shopping distance"), key='target', on_change=run_solver
        )

    #################### SOLVER SELECTION ############################

    # with st.expander("Avatar selection 🧍"):
    #     st.write("Here you can choose the avatar for the simulation.")
        
    #     st.session_state.avatar = st.selectbox("Avatar", ["🧍", "🎅🏼", "🧑", "👩", "👨", "👵", "👴", "👶", "👧", "👦", "🧔", "👱", "👨‍🦰", "👩‍🦰", "👨‍🦱", "👩‍🦱", "👨‍🦳", "👩‍🦳", "👨‍🦲", "👩‍🦲"])


    # with st.expander("Preferences quizz 📝"):
    #     st.write("Please fill out the following survey to help us suggest the best products for you.")

    #     product_categories = ["🍷 Wine", "🥤 Beverages", "🍱 Prepared meals", "❄️ Frozen", "🥛 Dairy Products", "🍞 Bread", "🍬 Candies", "🍫 Chocolate", "🥫 Canned Goods", "🥦 Vegetables", "🍎 Fruit", "🏠 Home"]

    #     #Use a multiselect to select the products that the user likes
    #     selected_categories = st.multiselect(
    #         "Select the product categories you want to buy",
    #         options=product_categories
    #     )

    #     #Button to submit the selected products
    #     if st.button("Submit Preferences"):
    #         st.success("Thank you for your preferences!")
    #         st.session_state.selected_categories = selected_categories

     
    # st.subheader("Technical menu")
    
    
    # with st.expander("Heuristics 🧠"):
    #     st.write("Here you can choose the solver for the simulation.")
        
    #     option = st.selectbox(
    #     'Choose an algorithm:',
    #     ('MIP solver', 
    #     'Nearest Neighbor Heuristic'), on_change=run_solver)
    #     if option == 'Nearest Neighbor Heuristic':
    #         st.session_state.solver = heuristic_solver
    #     elif option == 'MIP solver':
    #         st.session_state.solver = mip_solver
    
    # with st.expander("Explainable AI 🤖"):
    #     st.write("Here you can choose the desired explanation for the simulation.")
        
    #     st.session_state.xai_counterfactuals = st.checkbox("Counterfactuals", value=True)

    # with st.expander("Verification 🔍"):
    #     st.session_state.show_verification = st.checkbox("Show verification", value=True)
        

########################## METRICS ########################################
    
try:
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    with col1:
        st.metric("Basket 🧺", f'{len(st.session_state.basket)}', delta=None, delta_color="normal") 
    with col2:
        st.metric("Shopping list 📋", f'{len(st.session_state.shopping_list)}', delta=None, delta_color="normal") 
    with col3:
        if st.session_state.ExpectedShoppingTime != None:
            st.metric("Expected time 🕒", f"{int(st.session_state.ExpectedShoppingTime)} min", delta=None, delta_color="normal")
        else:
            st.metric("Expected time 🕒", "--", delta=None, delta_color="normal")
    with col4:
        if st.session_state.ExpectedShoppingDistance != None:
            st.metric("Expected distance 📏", f"{int(st.session_state.ExpectedShoppingDistance)} steps", delta=None, delta_color="normal")
        else:
            st.metric("Expected distance 📏", "--", delta=None, delta_color="normal")
    with col5:
        if st.session_state.meat_wait_time == None:
            st.metric("Meat queue time 🕒", '--', delta=None, delta_color="normal")
        elif st.session_state.meat_wait_time == 0:
            st.metric("Meat queue time 🕒", 'Your turn!', delta=None, delta_color="normal")
        elif st.session_state.meat_wait_time != 0:
            st.metric("Meat queue time 🕒", f"{st.session_state.meat_wait_time} min", delta=None, delta_color="normal")
        
    with col6:            
        if st.session_state.fish_wait_time == None:
            st.metric("Fish queue time 🕒", '--', delta=None, delta_color="normal")
        elif st.session_state.fish_wait_time == 0:
            st.metric("Fish queue time 🕒", 'Your turn!', delta=None, delta_color="normal")
        elif st.session_state.fish_wait_time != 0:
            st.metric("Fish queue time 🕒", f"{st.session_state.fish_wait_time} min", delta=None, delta_color="normal")
        
    with col7:            
        st.metric("Current time 🕒", f"{st.session_state.current_time} min", delta=None, delta_color="normal")
except NameError:
    pass


############################# MOVEMENT CONTROL ####################################

col1, col2 = st.columns([3, 1])

with col2:

    if not st.session_state.checkout:

        # Create arrow buttons (up, down, left, right) to alter the current_position variable
        st.markdown("<h3 style='text-align: center;'>Control Current Position</h3>", unsafe_allow_html=True)

        col2_1, col2_2, col2_3, col2_4, col2_5 = st.columns([1, 1, 1.1, 1, 1])

        update_movement_options()

        col2_3.button("⬆️", disabled=st.session_state.disable_up, on_click=move_up)
            
        col2_2.write("")
        col2_2.write("")
        col2_2.write("")
        col2_4.write("")
        col2_4.write("")
        col2_4.write("")


        col2_2.button("⬅️", disabled=st.session_state.disable_left, on_click=move_left)     
    
        col2_4.button("➡️", disabled=st.session_state.disable_right, on_click=move_right)

        col2_3.button("🛑", on_click = wait)
        
        col2_3.button("⬇️", disabled=st.session_state.disable_down, on_click = move_down)

            
# with col2:

    # if not st.session_state.checkout:
        
    #     #Create a button called "Follow proposed route"
    #     col2_2, col2_3, col2_4 = st.columns([1, 3, 1])
    #     col2_3.button("Follow proposed action", on_click = follow_proposed_action)
   

############################### PLOT THE STORE ####################################
############################## ASK FOR CUSTOMER FEEDBACK ##########################
############################## PRESENT EXPLANATIONS ###############################
############################## VERIFICATION OF CONSTRAINTS ########################

with col1:   
    
    if st.session_state.checkout:
        st.markdown("<h2 style='text-align: center; color: black; margin-top: 80px;'>Thank you for shopping with us! 🛒</h2>", unsafe_allow_html=True)
        st.write("How satisfied are you with your shopping experience?")
        st.session_state.satisfaction = st.radio(
            "Please select one:",
            ("1", "2", "3", "4", "5")
        )
        st.write("Please fill out the following survey to help us improve our service.")
        st.session_state.survey = st.text_area("Survey")
        if st.button("Submit"):
            st.success("Thank you for your feedback!")
            store_gsheet()

    else:
        
        if st.session_state.ExpectedShoppingTime == None:
            run_solver()

        fig = visualize_store_dynamic(st.session_state.G, st.session_state.products, st.session_state.nodes, st.session_state.ordered_nodes, V_pay, meat_station, fish_station, V_frozen, V_fresh, st.session_state.current_position, max_column, horizontal, st.session_state.product_nodes, st.session_state.shopping_list, st.session_state.avatar, None)
        
        st.plotly_chart(fig)

        #Show the shopping list with emojis
        
        st.write("**Route plan:**")
        
        currently_in_meat_station = False
        currently_in_fish_station = False
        written_list = "🧍"
        current_node = st.session_state.current_position
        if st.session_state.meat_wait_time != None:
            current_meat_time = st.session_state.meat_wait_time
        else:
            current_meat_time = 0
        if st.session_state.fish_wait_time != None:
            current_fish_time = st.session_state.fish_wait_time
        else:
            current_fish_time = 0
        for product_id in st.session_state.ordered_products:
            idx = st.session_state.shopping_list.index(product_id)
            if st.session_state.current_position in st.session_state.product_nodes:
                if idx == 0:
                    written_list += "-" * int(nx.shortest_path_length(st.session_state.G, current_node, st.session_state.product_nodes[idx], weight='distance'))
                    if st.session_state.products[product_id]['meat'] == 1 and current_meat_time > 0:
                        if not currently_in_meat_station:
                            written_list += "/" * current_meat_time
                        currently_in_meat_station = True
                    else:
                        currently_in_meat_station = False
                    if st.session_state.products[product_id]['fish'] == 1 and current_fish_time > 0:
                        if not currently_in_fish_station:
                            written_list += "/" * current_fish_time
                        currently_in_fish_station = True
                    else:
                        currently_in_fish_station = False
                else:
                    written_list += "-" * int(nx.shortest_path_length(st.session_state.G, current_node, st.session_state.product_nodes[idx], weight='distance'))
                    current_node = st.session_state.product_nodes[idx]
                    current_meat_time -= 1
                    current_fish_time -= 1
            else:
                written_list += "-" * int(nx.shortest_path_length(st.session_state.G, current_node, st.session_state.product_nodes[idx], weight='distance'))
                current_node = st.session_state.product_nodes[idx]
                current_meat_time -= 1
                current_fish_time -= 1
            if st.session_state.products[product_id]['meat'] == 1 and current_meat_time > 0:
                if not currently_in_meat_station:
                    written_list += "/" * current_meat_time
                currently_in_meat_station = True
            else:
                currently_in_meat_station = False
            if st.session_state.products[product_id]['fish'] == 1 and current_fish_time > 0:
                if not currently_in_fish_station:
                    written_list += "/" * current_fish_time
                currently_in_fish_station = True
            else:
                currently_in_fish_station = False
            written_list += f" {st.session_state.products[product_id]['icon']}"
        written_list += "-" * int(nx.shortest_path_length(st.session_state.G, current_node, V_pay[0], weight='distance'))
        written_list += "💰"
        st.write(written_list)
 

        if st.session_state.xai_counterfactuals and st.session_state.target == "Minimize shopping time":
            if st.session_state.cf_meat != None or st.session_state.cf_fish != None or st.session_state.cf_fresh != None or st.session_state.cf_frozen != None or st.session_state.cf_next != None or st.session_state.cf_last != None or st.session_state.cf_precedence != [0]*len(st.session_state.precedence_constraints):
                st.write("")
                st.write("**Explanation:**")   
            if st.session_state.cf_meat!=None: 
                st.write(f"You save **{int(abs(st.session_state.cf_meat))} minute{'s' if int(abs(st.session_state.cf_meat)) != 1 else ''}** by picking other products before going to the meat station 🥩.")
                
            if st.session_state.cf_fish != None:
                st.write(f"You save **{int(abs(st.session_state.cf_fish))} minute{'s' if int(abs(st.session_state.cf_fish)) != 1 else ''}** by picking other products before going to the fish station 🐟.")
                
            if st.session_state.cf_fresh != None and st.session_state.cf_frozen != None:
                if min(int(st.session_state.cf_fresh), int(st.session_state.cf_frozen)) != 0:
                    st.write(f"If you don't collect all the fresh and frozen products in the end, you can save **{min(int(abs(st.session_state.cf_fresh)), int(abs(st.session_state.cf_frozen)))} minute{'s' if min(int(abs(st.session_state.cf_fresh)), int(abs(st.session_state.cf_frozen))) != 1 else ''}. 🥚**")
                else:
                    st.write(f"You can collect all the fresh and frozen products in the end without any delay 🥚.")
            elif st.session_state.cf_fresh != None:
                if int(st.session_state.cf_fresh) != 0:
                    st.write(f"If you don't collect fresh products in the end, you can save **{int(abs(st.session_state.cf_fresh))} minute{'s' if int(abs(st.session_state.cf_fresh)) != 1 else ''}. 🥚**")
                else:
                    st.write(f"You can collect all the fresh products in the end without any delay 🥚.")
            elif st.session_state.cf_frozen != None:
                if int(st.session_state.cf_frozen) != 0:
                    st.write(f"If you don't collect frozen products in the end, you can save **{int(abs(st.session_state.cf_frozen))} minute{'s' if int(abs(st.session_state.cf_frozen)) != 1 else ''}. 🍦**") 
                else:
                    st.write(f"You can collect all the frozen products in the end without any delay 🍦.")
            if st.session_state.next_product != None:
                if st.session_state.cf_next != 0:
                    st.write(f"Purchasing {st.session_state.products[st.session_state.next_product]['name']} {st.session_state.products[st.session_state.next_product]['icon']} first is delaying you by **{int(abs(st.session_state.cf_next))} minute{'s' if int(abs(st.session_state.cf_next)) != 1 else ''}. 🕒**")
                else:
                    st.write(f"Purchasing {st.session_state.products[st.session_state.next_product]['name']} {st.session_state.products[st.session_state.next_product]['icon']} first is not delaying you. 🕒")
            if st.session_state.last_product != None:
                st.write(f"Purchasing {st.session_state.products[st.session_state.last_product]['name']} {st.session_state.products[st.session_state.last_product]['icon']} last is delaying you by **{int(abs(st.session_state.cf_last))} minute{'s' if int(abs(st.session_state.cf_last)) != 1 else ''}. 🕒**")
            if st.session_state.precedence_constraints != []:
                for idx, value_cf_precedence in enumerate(st.session_state.cf_precedence):
                    st.write(f"Picking {st.session_state.products[st.session_state.precedence_constraints[idx][0]]['name']} {st.session_state.products[st.session_state.precedence_constraints[idx][0]]['icon']} before {st.session_state.products[st.session_state.precedence_constraints[idx][1]]['name']} {st.session_state.products[st.session_state.precedence_constraints[idx][1]]['icon']} is delaying you by **{int(abs(value_cf_precedence))} minute{'s' if int(abs(value_cf_precedence)) != 1 else ''}. 🕒**")
        
        if st.session_state.show_verification:
            st.write("")
            #st.write("**Verification:**")
            #show_verification()
            show_verification_ghost()

######################### PURCHASE PRODUCTS ####################################
           
with col2:
    st.markdown("<h3 style='text-align: center;'>Products in <br> Current Position</h3>", unsafe_allow_html=True)
    
    current_node_products = st.session_state.nodes[st.session_state.current_position].products
    #If one of the products is in the shopping list, place it as the first element of the list
    current_node_products = [product_id for product_id in st.session_state.shopping_list if product_id in current_node_products] + [product_id for product_id in current_node_products if product_id not in st.session_state.shopping_list]
    if current_node_products:
        selected_product_ids = st.multiselect(
            "Select a product to purchase",
            options=current_node_products,
            default=[product_id for product_id in current_node_products if product_id in st.session_state.shopping_list],
            format_func=lambda product_id: st.session_state.products[product_id]['name'] + " " + st.session_state.products[product_id]['icon']
        )
        # Multiselect for selecting products to add to the shopping list
        if st.button("Purchase"):
            purchase(selected_product_ids)
    else:
        st.write("No products in this location.")

