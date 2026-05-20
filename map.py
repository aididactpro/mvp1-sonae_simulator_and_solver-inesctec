import networkx as nx
import matplotlib.pyplot as plt
import mplcursors
import matplotlib.patches as mpatches

# Function to visualize the path between a list of node IDs
def visualize_store(graph, nodes, ordered_nodes, V_pay, meat_station, fish_station, V_frozen, V_fresh, v_0):

    pos = {i: data.coords for i, data in nodes.items()}  # Access coords using dot notation
    plt.figure(figsize=(11, 8))

    # Draw the entire graph
    nx.draw(graph, pos, with_labels=True, node_size=500, node_color='lightblue', font_size=10)

    # Highlight ordered nodes
    ordered_node_colors = [
        'orange' if node in ordered_nodes and node != v_0 and node not in V_pay
        else 'yellow' if node == v_0
        else 'gray' 
        for node in graph.nodes()
    ]
    nx.draw_networkx_nodes(graph, pos, node_color=ordered_node_colors, node_size=500)

    # Draw baseline colors for all nodes
    baseline_node_colors = [
        'brown' if node in V_pay
        else 'green' if node == fish_station
        else 'pink' if node == meat_station
        else 'yellow' if node == v_0
        else 'blue' if node in V_frozen
        else 'lightblue' if node in V_fresh
        else 'grey'  # Default color for other nodes
        for node in graph.nodes()
    ]
    nx.draw_networkx_nodes(graph, pos, node_color=baseline_node_colors, node_size=500)

    # Draw red border for ordered nodes
    ordered_node_border_colors = [
        'orange' if node in ordered_nodes else 'none'
        for node in graph.nodes()
    ]
    nx.draw_networkx_nodes(graph, pos, node_color='none', edgecolors=ordered_node_border_colors, node_size=700, linewidths=2)
    nx.draw_networkx_nodes(graph, pos, node_color=baseline_node_colors, node_size=700, alpha=0.3)

    # Create legend
    orange_patch = mpatches.Patch(color='orange', label='Ordered Nodes')
    brown_patch = mpatches.Patch(color='brown', label='Paying Stations')
    green_patch = mpatches.Patch(color='green', label='Fish station')
    pink_patch = mpatches.Patch(color='pink', label='Meat station')
    blue_patch = mpatches.Patch(color='blue', label='Frozen Products')
    lightblue_patch = mpatches.Patch(color='lightblue', label='Fresh Products')
    yellow_patch = mpatches.Patch(color='yellow', label='Start Node')
    gray_patch = mpatches.Patch(color='gray', label='Other Nodes')
    plt.legend(handles=[orange_patch, brown_patch, green_patch, pink_patch, blue_patch, lightblue_patch, yellow_patch, gray_patch], loc='lower center', ncol=4)
    
    # Highlight the specified path
    for start, end in zip(ordered_nodes[:-1], ordered_nodes[1:]):
        # Find the shortest path between consecutive nodes
        path = nx.shortest_path(graph, source=start, target=end)
        path_edges = list(zip(path[:-1], path[1:]))
    
        # Add concave arrows manually for better visibility
        for (u, v) in path_edges:
            arrowprops = dict(facecolor='red', edgecolor='red', arrowstyle='->', lw=2, connectionstyle="arc3,rad=0.2")
            x_start, y_start = pos[u]
            x_end, y_end = pos[v]
            plt.annotate('', xy=(x_end, y_end), xytext=(x_start, y_start), arrowprops=arrowprops)

    # Setup cursor hover for nodes (products display on hover)
    cursor = mplcursors.cursor(hover=True)

    @cursor.connect("add")
    def on_add(sel):
        # get the current coordinates
        x, y = sel.target
        #get the closest node
        closest_node = min(pos, key=lambda node: (pos[node][0] - x)**2 + (pos[node][1] - y)**2)
        # get the node ID
        node_id = closest_node
        # get the node products
        products_at_node = nodes[node_id].products if node_id in nodes else None

        # set the text for the annotation
        if node_id in V_pay:
            sel.annotation.set_text(f"Node {node_id}: Paying Station")
        else:
            products_at_node = nodes[node_id].products if node_id in nodes else None
            sel.annotation.set_text(f"Node {node_id}: Products: {', '.join(products_at_node) if products_at_node else 'No products'}")
    

        '''
        node_id = list(graph.nodes())[sel.index]
        if node_id in V_pay:
            sel.annotation.set_text(f"Node {node_id}: Paying Station")
        else:
            products_at_node = nodes[node_id].products if node_id in nodes else None
            sel.annotation.set_text(f"Node {node_id}: Products: {', '.join(products_at_node) if products_at_node else 'No products'}")
        '''

    # Show plot
    #plt.title("Matosinhos SONAE Store")
    #plt.show()

    #Return the plot with all the interactive features

    return plt

if __name__ == "__main__":
    # Example ordered list of node IDs to visualize
    from graph import create_graph
    from product_catalogue import read_products_from_excel

    file_path = 'products.xlsx'
    products=read_products_from_excel(file_path)

    horizontal = [1,1,2,2,2,2,1,2,2,2,2,1]
    max_row = 15

    G, nodes = create_graph(horizontal, max_row, products)

    ordered_nodes = [0, 67, 100, 14]  # Replace with your actual ordered list
    V_pay = [1, 2, 3, 4]  # Replace with your actual V_pay list
    V_stations = [112, 114, 116]  # Replace with your actual V_stations list
    V_frozen = [77, 85, 93, 101]  # Replace with your actual V_frozen list
    V_fresh = [82, 90, 98, 106, 83, 91, 99, 107]  # Replace with your actual V_fresh list
    v_0 = 0  # Replace with your actual v_0 value
    visualize_store(G, nodes, ordered_nodes, V_pay, V_stations, V_frozen, V_fresh, v_0)