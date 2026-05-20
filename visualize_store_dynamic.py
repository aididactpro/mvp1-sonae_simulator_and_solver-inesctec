import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import numpy as np

# Example function to create a random graph layout for visualization
def visualize_store_dynamic(graph, products, nodes, ordered_nodes, V_pay, meat_station, fish_station, V_frozen, V_fresh, v_0, max_column, horizontal, product_nodes, K, avatar, recommended_product):
    pos = {i: data.coords for i, data in nodes.items()}  # Extracting coordinates

    edge_x = []
    edge_y = []
    for edge in graph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    node_x = []
    node_y = []
    for node in graph.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
    
    
    # Draw edges
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines'
    )

    
    # Draw nodes
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        text=[f"Node {node}<br>Products: {', '.join(products[prod_id]['name'] for prod_id in nodes[node].products)}" for node in graph.nodes()],
        marker=dict(
            size=5,
            color='black',
            line=dict(width=2, color='black') 
        ),
        hoverinfo='text'
    )


    #fig = go.Figure(data=[edge_trace, node_trace])
    fig = go.Figure()


    # Add rectangles to represent shelves
    shapes = [
        # Example shelf rectangles
        dict(type="rect", x0=0.4, y0=1.4, x1=1, y1=5.6, line=dict(color="RoyalBlue"), fillcolor="LightSkyBlue"),
        dict(type="rect", x0=1, y0=1.4, x1=1.6, y1=5.6, line=dict(color="RoyalBlue"), fillcolor="LightSkyBlue")
        # Add more rectangles as needed to represent all shelves
    ]

    shapes = []
    # Get all the positions of the number 1 in the horizontal list
    positions = [index for index, value in enumerate(horizontal) if value == 1]

    for i,position in enumerate(positions[:-1]):
        next_position = positions[i+1]
        shapes.append(
                dict(
                    type="rect",
                    x0=0,
                    y0=position+1.4,
                    x1=0.6,
                    y1=next_position+0.6,
                    line=dict(color="gray"),
                    fillcolor="lightgray"
                )
            )

        shapes.append(
                dict(
                    type="rect",
                    x0=max_column+0.4,
                    y0=position+1.4,
                    x1=max_column + 1,
                    y1=next_position+0.6,
                    line=dict(color="gray"),
                    fillcolor="lightgray"
                )
            )
        
    
        for j in range(np.floor(max_column/2).astype(int)):
            shapes.append(
                dict(
                    type="rect",
                    x0=2*j+1.4,
                    y0=position+1.4,
                    x1=2*j+2,
                    y1=next_position+0.6,
                    line=dict(color="gray"),
                    fillcolor="lightgray"
                )
            )

            shapes.append(
                dict(
                    type="rect",
                    x0=2*j+2,
                    y0=position+1.4,
                    x1=2*j+2.6,
                    y1=next_position+0.6,
                    line=dict(color="gray"),
                    fillcolor="lightgray"
                )
            )
            
    shapes.append(
                dict(
                    type="rect",
                    x0=4,
                    y0=len(horizontal) + 0.5,
                    x1=6,
                    y1=len(horizontal) + 1.2,
                    line=dict(color="gray"),
                    fillcolor="lightgray"
                )
            )
    
    fig.add_annotation(
        x=5,
        y=len(horizontal) + 0.85,
        text="🥩 Meat station",
        showarrow=False,
        font=dict(color="black", size=12),
        textangle=0  # Make the text vertical
    )


    shapes.append(
                dict(
                    type="rect",
                    x0=8,
                    y0=len(horizontal) + 0.5,
                    x1=10,
                    y1=len(horizontal) + 1.2,
                    line=dict(color="gray"),
                    fillcolor="lightgray"
                )
            )

    fig.add_annotation(
        x=9,
        y=len(horizontal) + 0.85,
        text="🐟 Fish station",
        showarrow=False,
        font=dict(color="black", size=12),
        textangle=0  # Make the text vertical
    )

    for shape in shapes:
        fig.add_shape(shape)

    # Add text to each shape

    #Create dictionary that associates corridor column and row eith the shelf name

    shelf_names = {
        (0, 1): '🍷 Wine', 
        (1, 1): '🥤 Beverages', 
        (2, 1): '🍱 Prepared meals', 
        (3, 1): '🍱 Prepared meals', 
        (4, 1): '❄️ Frozen', 
        (5, 1): '❄️ Frozen', 
        (8, 1): '🥛 Dairy Products', 
        (9, 1): '🥛 Dairy Products', 
        (12, 1): '🍞 Bread', 
        (13, 1): '🥐 Pastry',
        (0, 2): '🍬 Candies', 
        (1, 2): '🍫 Chocolate', 
        (2, 2): '🥫 Canned Goods', 
        (3, 2): '🥫 Canned Goods', 
        (6, 2): '🥦 Vegetables', 
        (7, 2): '🥦 Vegetables', 
        (10, 2): '🍎 Fruit', 
        (11, 2): '🍎 Fruit', 
        (14, 2): '🏠 Home', 
        (15, 2): '🏠 Home'
    }

    #Right the names of the shelves

    columns = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
    rows = [0,1,2,3]

    y_row = {0: 0.25, 1: 3.5, 2: 8.5, 3: 10}

    def odd_even(n):
        return n % 2 == 0

    for i in columns:
        for j in rows:
            try:
                shelf_name = shelf_names[(i,j)]
                if odd_even(i):
                    fig.add_annotation(
                        x=i+0.3,
                        y=y_row[j],
                        text=shelf_name,
                        showarrow=False,
                        font=dict(color="black", size=12),
                        textangle=90  # Make the text vertical
                    )
                else:
                    fig.add_annotation(
                        x=i+0.75,
                        y=y_row[j],
                        text=shelf_name,
                        showarrow=False,
                        font=dict(color="black", size=12),
                        textangle=90  # Make the text vertical
                    )
            except:
                pass
            
    
    # Path highlighting logic
    path_edges = []
    for start, end in zip(ordered_nodes[:-1], ordered_nodes[1:]):
        path = nx.shortest_path(graph, source=start, target=end)
        path_edges.extend(list(zip(path[:-1], path[1:])))
    
    path_edges.append((ordered_nodes[-1], V_pay[0]))
    

    '''
    for (u, v) in path_edges:
        fig.add_trace(go.Scatter(
            x=[pos[u][0], pos[v][0]],
            y=[pos[u][1], pos[v][1]],
            mode='lines',
            line=dict(width=line_width, color='red', dash='dot'),
            hoverinfo='none'
        ))
    '''

    def get_path_movement(edge):
        u, v = edge
        if pos[u][0] == pos[v][0] and pos[u][1] < pos[v][1]:
            return 'up'
        elif pos[u][0] == pos[v][0] and pos[u][1] > pos[v][1]:
            return 'down'
        elif pos[u][1] == pos[v][1] and pos[u][0] < pos[v][0]:
            return 'right'
        elif pos[u][1] == pos[v][1] and pos[u][0] > pos[v][0]:
            return 'left'
        else:
            return 'down'
    
    deviation = 0.15
    line_width = 3
    
    if get_path_movement(path_edges[0]) == 'up':
        current_x = pos[v_0][0] + deviation
        current_y = pos[v_0][1]
    elif get_path_movement(path_edges[0]) == 'down':
        current_x = pos[v_0][0] - deviation
        current_y = pos[v_0][1]
    elif get_path_movement(path_edges[0]) == 'left':
        current_x = pos[v_0][0]
        current_y = pos[v_0][1] + deviation
    elif get_path_movement(path_edges[0]) == 'right':
        current_x = pos[v_0][0]
        current_y = pos[v_0][1] - deviation

    global arrow_coordinates
    arrow_coordinates = []

    global number_of_arrows
    number_of_arrows = 0

    def plot_edge(x, y, movement, arrows_limit = 5):

        color_up = 'red'
        color_down = 'red'
        color_right = 'red'
        color_left = 'red'

        if movement == 'up':
            color = color_up
        elif movement == 'down':
            color = color_down
        elif movement == 'right':
            color = color_right
        elif movement == 'left':
            color = color_left

        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode='lines',
            line=dict(width=line_width, color=color, dash='dot'),
            hoverinfo='none'
        ))
        # Add arrows at the midpoint
        mid_x = (x[0] + x[1]) / 2
        mid_y = (y[0] + y[1]) / 2

        if (mid_x, mid_y) not in arrow_coordinates:
            global number_of_arrows
            if number_of_arrows < arrows_limit:
                fig.add_annotation(
                    x=mid_x,
                    y=mid_y,
                    ax=current_x,
                    ay=current_y,
                    xref="x", yref="y",
                    axref="x", ayref="y",
                    showarrow=True,
                    arrowhead=3,
                    arrowsize=1.2,
                    arrowwidth=2,
                    arrowcolor="red"
                )

                arrow_coordinates.append((mid_x, mid_y))
                number_of_arrows += 1

    for idx in range(len(path_edges)-1):

        if get_path_movement(path_edges[idx]) == 'up':

            if get_path_movement(path_edges[idx+1]) == 'up':
                
                u, v = path_edges[idx]
                x = [current_x, pos[v][0] + deviation]
                y = [current_y, pos[v][1] + 0]

                plot_edge(x, y, get_path_movement(path_edges[idx]))

                current_x = x[1]
                current_y = y[1]

            elif get_path_movement(path_edges[idx+1]) == 'down':

                u, v = path_edges[idx]
                x=[current_x, pos[v][0] + deviation]
                y=[current_y, pos[v][1] + 0]
                
                plot_edge(x, y, get_path_movement(path_edges[idx]))

                current_x = pos[v][0] + -deviation
                current_y = pos[v][1] + 0

            elif get_path_movement(path_edges[idx+1]) == 'left':

                u, v = path_edges[idx]
                x=[current_x, pos[v][0] + deviation]
                y=[current_y, pos[v][1] + deviation]
                
                plot_edge(x, y, get_path_movement(path_edges[idx]))

                current_x = pos[v][0] + deviation
                current_y = pos[v][1] + deviation

            elif get_path_movement(path_edges[idx+1]) == 'right':

                u, v = path_edges[idx]
                x=[current_x, pos[v][0] + deviation]
                y=[current_y, pos[v][1] -deviation]
                
                plot_edge(x, y, get_path_movement(path_edges[idx]))

                current_x = pos[v][0] + deviation
                current_y = pos[v][1] - deviation

        if get_path_movement(path_edges[idx]) == 'down':
            if get_path_movement(path_edges[idx+1]) == 'up':

                u, v = path_edges[idx]
                x=[current_x, pos[v][0] - deviation]
                y=[current_y, pos[v][1] + 0]
                
                plot_edge(x, y, get_path_movement(path_edges[idx]))

                current_x = pos[v][0] + deviation
                current_y = pos[v][1] + 0

            elif get_path_movement(path_edges[idx+1]) == 'down':

                u, v = path_edges[idx]
                x=[current_x, pos[v][0] - deviation]
                y=[current_y, pos[v][1] + 0]
                
                plot_edge(x, y, get_path_movement(path_edges[idx]))

                current_x = pos[v][0] - deviation
                current_y = pos[v][1] + 0

            elif get_path_movement(path_edges[idx+1]) == 'left':

                u, v = path_edges[idx]
                x=[current_x, pos[v][0] - deviation]
                y=[current_y, pos[v][1] + deviation]

                plot_edge(x, y, get_path_movement(path_edges[idx]))
                
                current_x = pos[v][0] - deviation
                current_y = pos[v][1] + deviation

            elif get_path_movement(path_edges[idx+1]) == 'right':

                u, v = path_edges[idx]
                x=[current_x, pos[v][0] - deviation]
                y=[current_y, pos[v][1] - deviation]
                
                plot_edge(x, y, get_path_movement(path_edges[idx]))

                current_x = pos[v][0] - deviation
                current_y = pos[v][1] - deviation

        if get_path_movement(path_edges[idx]) == 'left':

            if get_path_movement(path_edges[idx+1]) == 'up':

                u, v = path_edges[idx]
                x=[current_x, pos[v][0] + deviation]
                y=[current_y, pos[v][1] + deviation]

                plot_edge(x, y, get_path_movement(path_edges[idx]))
                
                current_x = pos[v][0] + deviation
                current_y = pos[v][1] + deviation

            elif get_path_movement(path_edges[idx+1]) == 'down':

                u, v = path_edges[idx]
                x=[current_x, pos[v][0] - deviation]
                y=[current_y, pos[v][1] + deviation]
                
                plot_edge(x, y, get_path_movement(path_edges[idx]))

                current_x = pos[v][0] - deviation
                current_y = pos[v][1] + deviation

            elif get_path_movement(path_edges[idx+1]) == 'left':

                u, v = path_edges[idx]
                x=[current_x, pos[v][0] + 0]
                y=[current_y, pos[v][1] + deviation]

                plot_edge(x, y, get_path_movement(path_edges[idx]))

                current_x = pos[v][0] + 0
                current_y = pos[v][1] + deviation

            elif get_path_movement(path_edges[idx+1]) == 'right':

                u, v = path_edges[idx]
                x=[current_x, pos[v][0] + 0]
                y=[current_y, pos[v][1] + deviation]
                
                plot_edge(x, y, get_path_movement(path_edges[idx]))

                current_x = pos[v][0] + 0
                current_y = pos[v][1] - deviation

        if get_path_movement(path_edges[idx]) == 'right':

            if get_path_movement(path_edges[idx+1]) == 'up':

                u, v = path_edges[idx]
                x=[current_x, pos[v][0] + deviation]
                y=[current_y, pos[v][1] - deviation]
                
                plot_edge(x, y, get_path_movement(path_edges[idx]))

                current_x = pos[v][0] + deviation
                current_y = pos[v][1] - deviation

            elif get_path_movement(path_edges[idx+1]) == 'down':

                u, v = path_edges[idx]
                x=[current_x, pos[v][0] - deviation]
                y=[current_y, pos[v][1] - deviation]
                
                plot_edge(x, y, get_path_movement(path_edges[idx]))

                current_x = pos[v][0] - deviation
                current_y = pos[v][1] - deviation

            elif get_path_movement(path_edges[idx+1]) == 'left':

                u, v = path_edges[idx]
                x=[current_x, pos[v][0] + 0]
                y=[current_y, pos[v][1] - deviation]
                
                plot_edge(x, y, get_path_movement(path_edges[idx]))

                current_x = pos[v][0] + 0
                current_y = pos[v][1] + deviation

            elif get_path_movement(path_edges[idx+1]) == 'right':

                u, v = path_edges[idx]
                x=[current_x, pos[v][0] + 0]
                y=[current_y, pos[v][1] - deviation]

                plot_edge(x, y, get_path_movement(path_edges[idx]))

                current_x = pos[v][0] + 0
                current_y = pos[v][1] - deviation
    
    
    for index,k in enumerate(K):
        node = product_nodes[index]
        #Count number of times node is in the list
        node_products = []
        for i in range(len(product_nodes)):
            if product_nodes[i] == node:
                node_products.append(K[i])
        
        if len(node_products) == 1:

            fig.add_annotation(
                x=pos[node][0],
                y=pos[node][1],
                text=products[k]['icon'],  # Unicode symbol or text to represent the product
                showarrow=False,
                font=dict(color="black", size=30)
            )
        
        else:
            deviation = -0.2
            for product in node_products:
                fig.add_annotation(
                    x=pos[node][0] + deviation,
                    y=pos[node][1],
                    text=products[product]['icon'],  # Unicode symbol or text to represent the product
                    showarrow=False,
                    font=dict(color="black", size=20)
                )
                deviation = 0.2

    if recommended_product is not None:
        
        node = products[recommended_product]['locations'][0]

        # Add a green circle around the recommended product
        fig.add_shape(
            type="circle",
            xref="x", yref="y",
            x0=pos[node][0] - 0.5, y0=pos[node][1] - 0.8,
            x1=pos[node][0] + 0.5, y1=pos[node][1] - 0.2,
            line=dict(color="green", width=2),
            fillcolor="rgba(0, 255, 0, 0.2)"  # Optional: fill color with transparency
        )
        
        fig.add_annotation(
            x=pos[node][0],
            y=pos[node][1] - 0.3,
            text=products[recommended_product]['icon'],  # Unicode symbol or text to represent the product
            showarrow=False,
            font=dict(color="red", size=30)
        )
    
    # 💰 (Payment)
    for node in V_pay:
        fig.add_annotation(
            x=pos[node][0],
            y=pos[node][1],
            text="💰",  # Unicode symbol or text to represent the product
            showarrow=False,
            font=dict(color="black", size=35)
        )
    
    # 🧍 (Current location)
    fig.add_annotation(
        x=pos[v_0][0],
        y=pos[v_0][1],
        text=avatar,  # Unicode symbol or text to represent the product
        showarrow=False,
        font=dict(color="black", size=40)
    )

    '''
    #Print the node ID on each node
    for node in graph.nodes():
        fig.add_annotation(
            x=pos[node][0],
            y=pos[node][1],
            text=str(node),
            showarrow=False,
            font=dict(color="black", size=10)
        )
    '''
    # Add layout and legend
    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        height=600,  # Increase the height of the figure
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)    
    )
    
    return fig