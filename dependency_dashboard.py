import os
import networkx as nx
from dash import Dash, dash_table, html, dcc, callback, Input, Output, State, callback_context, no_update
from dash.dcc import Download  # Import Download from dcc instead of directly from dash
import dash_cytoscape as cyto

from dependency_analyzer import build_dependency_graph, find_required_files
import hashlib
import colorsys
import pandas as pd

# Load Cytoscape stylesheet
cyto.load_extra_layouts()

# Initialize the Dash app with explicit favicon
app = Dash(
    __name__, 
    title="Python Dependency Analyzer",
    assets_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets'),
    update_title=None
)

# Explicitly set the favicon
app._favicon = 'assets/favicon.ico'

# Add Roboto font
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        <link rel="icon" type="image/x-icon" href="assets/favicon.ico">
        {%css%}
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
        <style>
            body {
                font-family: 'Roboto', sans-serif;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Add a function to generate consistent colors for directories
def generate_distinct_colors(n):
    """Generate n visually distinct colors using the HSL color space"""
    colors = []
    for i in range(n):
        # Generate evenly spaced hues
        hue = i / n
        # Use golden ratio to get well-distributed hues
        # This avoids adjacent colors being too similar
        hue = (hue + 0.618033988749895) % 1.0
        
        # Fixed saturation and lightness for good visibility
        saturation = 0.7
        lightness = 0.6
        
        # Convert to RGB
        r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
        
        # Convert to hex
        hex_color = "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))
        colors.append(hex_color)
    
    return colors

# Define the layout
app.layout = html.Div([
    html.H1("Python Import Dependency Analyzer", 
            style={'textAlign': 'center', 'marginBottom': '30px', 'marginTop': '20px'}),
    
    # Create a container with sidebar and main content
    html.Div([
        # Sidebar
        html.Div([
            # Project directory input
            html.Div([
                html.Label("Project Directory:"),
                dcc.Input(
                    id="project-directory",
                    type="text",
                    placeholder="Enter the path to your Python project",
                    value="",
                    style={'width': '100%'}
                ),
            ], style={'marginBottom': '15px'}),
            
            # Entry point input
            html.Div([
                html.Label("Entry Point File (optional):"),
                dcc.Input(
                    id="entry-point",
                    type="text",
                    placeholder="main.py or path/to/main.py",
                    value="",
                    style={'width': '100%'}
                ),
            ], style={'marginBottom': '15px'}),
            
            # Module base input (optional)
            html.Div([
                html.Label("Module Base (optional):"),
                dcc.Input(
                    id="module-base",
                    type="text",
                    placeholder="e.g., mypackage",
                    value="",
                    style={'width': '100%'}
                ),
            ], style={'marginBottom': '15px'}),
            
            # Layout type dropdown
            html.Div([
                html.Label("Graph Layout:"),
                dcc.Dropdown(
                    id="layout-type",
                    options=[
                        {'label': 'Circle', 'value': 'circle'},
                        {'label': 'Concentric', 'value': 'concentric'},
                        {'label': 'Breadthfirst', 'value': 'breadthfirst'},
                        {'label': 'Cose', 'value': 'cose'},
                        {'label': 'Grid', 'value': 'grid'},
                        {'label': 'Force-Directed (Cola)', 'value': 'cola'},
                        {'label': 'Euler', 'value': 'euler'},
                        {'label': 'Klay', 'value': 'klay'},
                    ],
                    value='cose',
                    style={'width': '100%'}
                ),
            ], style={'marginBottom': '15px'}),
            
            # Include keywords filter input
            html.Div([
                html.Label("Include Keywords:"),
                dcc.Input(
                    id="include-keywords",
                    type="text",
                    placeholder="e.g., api,utils,model",
                    value="",
                    style={'width': '100%'}
                ),
                html.P("Nodes containing any of these keywords will be included (comma-separated)", 
                       style={'fontSize': '12px', 'color': '#666'})
            ], style={'marginBottom': '15px'}),
            
            # Exclude keywords filter input
            html.Div([
                html.Label("Exclude Keywords:"),
                dcc.Input(
                    id="exclude-keywords",
                    type="text",
                    placeholder="e.g., test,deprecated",
                    value="",
                    style={'width': '100%'}
                ),
                html.P("Nodes containing any of these keywords will be excluded (comma-separated)", 
                       style={'fontSize': '12px', 'color': '#666'})
            ], style={'marginBottom': '15px'}),
            
            # Connection count filter slider
            html.Div([
                html.Label("Filter by Connection Count:"),
                html.Div([
                    dcc.RangeSlider(
                        id="connection-filter",
                        min=0,
                        max=20,
                        step=1,
                        value=[0, 20],
                        marks={i: str(i) for i in range(0, 21, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], style={'padding': '10px 0px'}),
                html.P(id="connections-description", children="", style={'fontSize': '12px'}),
            ], style={'marginBottom': '15px'}),
            
            # Add depth slider for node selection - hidden by default
            html.Div([
                html.Label("Connection Depth:"),
                dcc.Slider(
                    id="connection-depth",
                    min=1,
                    max=5,
                    step=1,
                    value=1,
                    marks={i: str(i) for i in range(1, 6)},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                html.P("Degree of separation from selected node", style={'fontSize': '12px', 'color': '#666'})
            ], id="depth-slider-container", style={'marginBottom': '15px', 'display': 'none'}),
            
            # Analyze button
            html.Button("Analyze Dependencies", id="analyze-button", n_clicks=0,
                        style={
                            'backgroundColor': '#4CAF50',
                            'color': 'white',
                            'padding': '10px 20px',
                            'fontSize': '16px',
                            'borderRadius': '5px',
                            'border': 'none',
                            'cursor': 'pointer',
                            'width': '100%',
                            'marginBottom': '20px',
                            'marginTop': '10px'
                        }),
            
            # Legend
            html.Div([
                html.Label("Legend:", style={'fontWeight': 'bold'}),
                html.Div([
                    html.Span("■", style={'color': '#1f77b4', 'fontSize': '16px', 'marginRight': '5px'}),
                    html.Span("Node colors indicate directories", style={'marginRight': '15px'})
                ], style={'marginBottom': '5px'}),
                html.Div([
                    html.Span("▢", style={'color': '#d62728', 'fontSize': '16px', 'marginRight': '5px'}),
                    html.Span("Entry Point (red border)", style={'marginRight': '15px'})
                ], style={'marginBottom': '5px'}),
                html.Div([
                    html.Span("▢", style={'color': '#2ca02c', 'fontSize': '16px', 'marginRight': '5px'}),
                    html.Span("Required (green border)", style={'marginRight': '15px'})
                ], style={'marginBottom': '5px'}),
                html.Div([
                    html.Span("▢", style={'color': '#ff7f0e', 'fontSize': '16px', 'marginRight': '5px'}),
                    html.Span("Unused (orange border)", style={'marginRight': '15px'})
                ], style={'marginBottom': '5px'}),
            ], style={'marginTop': '20px', 'backgroundColor': '#f8f9fa', 'padding': '10px', 'borderRadius': '5px'}),
            
        ], style={'width': '250px', 'padding': '20px', 'backgroundColor': '#f8f8f8', 
                  'boxShadow': '2px 0 5px -2px #888', 'height': '100vh', 'overflowY': 'auto'}),
        
        # Main content area
        html.Div([
            # Add reset button for node selection
            html.Div([
                html.Button(
                    "Reset Selection", 
                    id="reset-selection", 
                    style={
                        'backgroundColor': '#2196F3',
                        'color': 'white',
                        'padding': '5px 15px',
                        'fontSize': '14px',
                        'borderRadius': '5px',
                        'border': 'none',
                        'cursor': 'pointer',
                        'marginBottom': '10px',
                        'display': 'none'  # Hidden by default
                    }
                ),
                html.Div(id="selection-info", style={'marginBottom': '10px'})
            ], style={'textAlign': 'center'}),
            
            # Cytoscape component - maintain increased height
            html.Div([
                dcc.Loading(
                    id="loading-graph",
                    type="circle",
                    children=cyto.Cytoscape(
                        id='cytoscape-graph',
                        layout={'name': 'cose'},
                        style={'width': '100%', 'height': '75vh'},  # Further increased height since zoom controls are gone
                        elements=[],
                        stylesheet=[
                            # Group selectors
                            {
                                'selector': 'node',
                                'style': {
                                    'content': 'data(label)',
                                    'background-color': 'data(color)',
                                    'font-size': '12px',
                                    'text-valign': 'center',
                                    'text-halign': 'center',
                                    'text-wrap': 'wrap',
                                    'text-max-width': '100px',
                                    'width': 'data(size)',
                                    'height': 'data(size)',
                                    'border-width': 'data(border_width)',
                                    'border-color': 'data(border_color)'
                                }
                            },
                            {
                                'selector': 'edge',
                                'style': {
                                    'width': 1,
                                    'line-color': '#ccc',
                                    'target-arrow-color': '#ccc',
                                    'target-arrow-shape': 'triangle',
                                    'curve-style': 'bezier'
                                }
                            },
                            # Class selectors - REMOVE background-color from these
                            {
                                'selector': '.entrypoint',
                                'style': {
                                    'border-width': 3,
                                    'border-color': '#d62728'  # red border only
                                }
                            },
                            {
                                'selector': '.required',
                                'style': {
                                    'border-width': 2,
                                    'border-color': '#2ca02c'  # green border only
                                }
                            },
                            {
                                'selector': '.unused',
                                'style': {
                                    'border-width': 2,
                                    'border-color': '#ff7f0e'  # orange border only
                                }
                            },
                            {
                                'selector': '.selected',
                                'style': {
                                    'border-width': 3,
                                    'border-color': '#00F',
                                    'border-opacity': 0.8
                                }
                            },
                            {
                                'selector': '.connected-edge',
                                'style': {
                                    'line-color': '#00F',
                                    'target-arrow-color': '#00F',
                                    'width': 2
                                }
                            },
                            {
                                'selector': '.highlighted',
                                'style': {
                                    'border-width': 2,
                                    'border-color': '#00F',
                                }
                            },
                        ]
                    )
                )
            ]),
            
            # Add node data table with download button
            html.Div([
                html.Div([
                    html.H4("Nodes Information", style={'textAlign': 'center', 'display': 'inline-block', 'marginRight': '20px'}),
                    html.Button(
                        "Download CSV",
                        id="download-csv-button",
                        style={
                            'backgroundColor': '#4CAF50',
                            'color': 'white',
                            'padding': '5px 15px',
                            'fontSize': '14px',
                            'borderRadius': '5px',
                            'border': 'none',
                            'cursor': 'pointer',
                            'display': 'inline-block',
                            'verticalAlign': 'middle'
                        }
                    ),
                    dcc.Download(id="download-dataframe-csv"),
                ], style={'textAlign': 'center', 'marginTop': '20px', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center'}),
                html.Div(
                    id='node-table-container',
                    style={'marginTop': '10px', 'maxHeight': '200px', 'overflowY': 'auto'}
                )
            ], style={'marginTop': '20px'}),
            
        ], style={'flex': '1', 'padding': '20px', 'backgroundColor': 'white'}),
        
    ], style={'display': 'flex', 'flexDirection': 'row'}),
    
    # Store the complete graph data
    dcc.Store(id='graph-data'),
    
    # Store for selected node information
    dcc.Store(id='selected-node'),
    
    # Keep empty div for analysis results to prevent callback errors
    html.Div(id="analysis-results", style={'display': 'none'}),
    
    # Footer
    html.Div(
        "Created with Python, Dash, and Cytoscape.js",
        style={'textAlign': 'center', 'marginTop': '30px', 'marginBottom': '20px', 'color': '#666'}
    )
])

# Remove the zoom-related callbacks
# Keeping only the fit view functionality which is useful

# Add a fit-to-view button client-side callback using cytoscape.js API
app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks) {
            const cy = document.getElementById('cytoscape-graph')._cyreg.cy;
            if (cy) {
                cy.fit();
                cy.center();
            }
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('cytoscape-graph', 'stylesheet'),
    [Input('reset-selection', 'n_clicks')],  # Use reset-selection button to trigger fit
    prevent_initial_call=True
)

@app.callback(
    Output('cytoscape-graph', 'elements'),
    [Input('graph-data', 'data'),
     Input('layout-type', 'value'),
     Input('connection-filter', 'value'),
     Input('include-keywords', 'value'),
     Input('exclude-keywords', 'value'),
     Input('selected-node', 'data'),
     Input('connection-depth', 'value'),
     Input('reset-selection', 'n_clicks')]
)
def update_cytoscape_elements(graph_data, layout_type, connection_range, include_kw, exclude_kw, selected_node, depth, reset_clicks):
    if not graph_data:
        return []
    
    try:
        # Reconstruct basic graph structure
        G = nx.DiGraph()
        G.add_nodes_from(graph_data['nodes'])
        G.add_edges_from(graph_data['edges'])
        file_to_module = graph_data.get('file_to_module', {})
        connection_counts = graph_data.get('connection_counts', {})
        entry_point = graph_data.get('entry_point', None)
        required = set(graph_data.get('required', []))
        
        # Filter by connection count
        min_connections, max_connections = connection_range
        nodes_to_keep = [node for node in G.nodes() if min_connections <= connection_counts.get(node, 0) <= max_connections]
        
        # Parse keyword filters
        include_keywords = [kw.strip() for kw in include_kw.split(',')] if include_kw else []
        exclude_keywords = [kw.strip() for kw in exclude_kw.split(',')] if exclude_kw else []
        include_keywords = [kw for kw in include_keywords if kw]  # Remove empty items
        exclude_keywords = [kw for kw in exclude_keywords if kw]  # Remove empty items
        
        # Apply keyword filters
        if include_keywords:
            nodes_to_keep = [node for node in nodes_to_keep if 
                            any(kw.lower() in node.lower() or 
                               (node in file_to_module and kw.lower() in file_to_module[node].lower()) 
                               for kw in include_keywords)]
        
        if exclude_keywords:
            nodes_to_keep = [node for node in nodes_to_keep if not 
                            any(kw.lower() in node.lower() or 
                               (node in file_to_module and kw.lower() in file_to_module[node].lower()) 
                               for kw in exclude_keywords)]
        
        # Filter by selected node
        ctx = callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
        
        if trigger_id == "reset-selection":
            selected_node = None
        
        highlighted_nodes = set()
        highlighted_edges = set()
        
        if selected_node and selected_node.get('node') in G.nodes():
            node = selected_node.get('node')
            
            # Find nodes within specified depth
            connected_nodes = set([node])
            current_depth = 0
            frontier = {node}
            
            # Use breadth-first search to find nodes within depth
            while current_depth < depth and frontier:
                current_depth += 1
                next_frontier = set()
                
                for current in frontier:
                    # Add predecessors (nodes that import this one)
                    for pred in G.predecessors(current):
                        if pred not in connected_nodes:
                            connected_nodes.add(pred)
                            next_frontier.add(pred)
                            highlighted_edges.add((pred, current))
                    
                    # Add successors (nodes that this one imports)
                    for succ in G.successors(current):
                        if succ not in connected_nodes:
                            connected_nodes.add(succ)
                            next_frontier.add(succ)
                            highlighted_edges.add((current, succ))
                
                frontier = next_frontier
            
            # Only keep connected nodes that also match the connection count filter
            nodes_to_keep = [n for n in nodes_to_keep if n in connected_nodes]
            highlighted_nodes = connected_nodes
        
        # If no nodes match filters, return empty
        if not nodes_to_keep:
            return []
        
        # Create Cytoscape elements
        elements = []
        
        # Get all unique directories first
        unique_directories = set()
        for node in nodes_to_keep:
            directory = os.path.dirname(node)
            unique_directories.add(directory)
        
        # Generate distinct colors for all directories
        distinct_colors = generate_distinct_colors(len(unique_directories))
        
        # Map directories to colors
        directory_colors = {}
        for i, directory in enumerate(sorted(unique_directories)):
            directory_colors[directory] = distinct_colors[i]
        
        # Add nodes
        for node in nodes_to_keep:
            # Get display name
            if node in file_to_module:
                display_name = os.path.basename(file_to_module[node])
            else:
                display_name = os.path.basename(node)
                
            # Get node data
            connection_count = connection_counts.get(node, 0)
            imports = G.out_degree(node)
            imported_by = G.in_degree(node)
            
            # Get directory color from our pre-generated palette
            directory = os.path.dirname(node)
            color = directory_colors.get(directory, '#1f77b4')  # Use default blue if not found
            
            # Determine node class
            classes = []
            border_color = None
            border_width = 1
            
            # Add special status indicators (as border instead of changing the fill color)
            if entry_point and node == entry_point:
                classes.append('entrypoint')
                border_color = '#d62728'  # Red border for entry point
                border_width = 3
            elif required and node in required:
                classes.append('required')
                border_color = '#2ca02c'  # Green border for required
                border_width = 2
            elif required is not None:  # unused nodes
                classes.append('unused')
                border_color = '#ff7f0e'  # Orange border for unused
                border_width = 2
                
            # Add highlighted class if node is selected or connected
            if highlighted_nodes and node in highlighted_nodes:
                classes.append('highlighted')
                if node == selected_node.get('node'):
                    classes.append('selected')
                    
            # Compute node size based on connection count
            size = 20 + connection_count * 5
                
            # Create node element with directory info
            node_element = {
                'data': {
                    'id': str(node),
                    'label': display_name,
                    'imports': imports,
                    'imported_by': imported_by,
                    'total_connections': connection_count,
                    'size': size,
                    'color': color,
                    'fullpath': node,
                    'directory': directory,
                    'module_name': file_to_module.get(node, ''),
                    'border_color': border_color,
                    'border_width': border_width
                },
                'classes': ' '.join(classes)
            }
            
            elements.append(node_element)
            
        # Add edges between nodes that are in the filtered set
        for source, target in G.edges():
            if source in nodes_to_keep and target in nodes_to_keep:
                edge_classes = []
                if (source, target) in highlighted_edges:
                    edge_classes.append('connected-edge')
                    
                # Reverse direction: target becomes source, source becomes target
                # This makes arrows point FROM the imported module TO the importer
                elements.append({
                    'data': {
                        'source': str(target),  # Reversed
                        'target': str(source),  # Reversed
                        'id': f"{target}_{source}"  # Also reverse the ID
                    },
                    'classes': ' '.join(edge_classes)
                })
                
        # Update cytoscape layout
        return elements
    
    except Exception as e:
        print(f"Error updating cytoscape elements: {e}")
        return []

@app.callback(
    Output("depth-slider-container", "style"),
    [Input("selected-node", "data"),
     Input("reset-selection", "n_clicks")]
)
def toggle_depth_slider(selected_node, reset_clicks):
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    if trigger_id == "reset-selection" or not selected_node:
        return {'marginBottom': '15px', 'display': 'none'}
    
    return {'marginBottom': '15px', 'display': 'block'}

@app.callback(
    Output('cytoscape-graph', 'layout'),
    [Input('layout-type', 'value')]
)
def update_cytoscape_layout(layout_type):
    return {'name': layout_type, 'animate': True}

@app.callback(
    [Output("selected-node", "data"),
     Output("reset-selection", "style"),
     Output("selection-info", "children")],
    [Input("cytoscape-graph", "tapNodeData"),
     Input("reset-selection", "n_clicks")],
    [State("graph-data", "data"),
     State("selected-node", "data")]
)
def update_selected_node(node_data, reset_clicks, graph_data, current_selection):
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    # Default button style (hidden)
    button_style = {
        'backgroundColor': '#2196F3',
        'color': 'white',
        'padding': '5px 15px',
        'fontSize': '14px',
        'borderRadius': '5px',
        'border': 'none',
        'cursor': 'pointer',
        'marginBottom': '10px',
        'display': 'none'
    }
    
    # Reset the selection if reset button was clicked
    if trigger_id == "reset-selection":
        return None, button_style, ""
    
    # If no click data or no graph data, keep current selection
    if not node_data or not graph_data:
        return current_selection, button_style, ""
    
    try:
        selected_node = node_data.get('fullpath')
        if selected_node:
            display_name = node_data.get('label', os.path.basename(selected_node))
            imports = node_data.get('imports', 0)
            imported_by = node_data.get('imported_by', 0)
            
            # Show the reset button
            button_style['display'] = 'inline-block'
            
            # Create info text
            info_text = f"Selected: {display_name} (Imports: {imports}, Imported by: {imported_by})"
            
            return {'node': selected_node}, button_style, info_text
            
    except Exception as e:
        print(f"Error in node selection: {e}")
    
    return current_selection, button_style, ""

# Simplify the analysis results callback to return an empty div
@app.callback(
    Output("analysis-results", "children"),
    [Input("graph-data", "data"),
     Input("connection-filter", "value"),
     Input("selected-node", "data"),
     Input("connection-depth", "value")]
)
def update_analysis_results(graph_data, connection_range, selected_node, depth):
    # Return an empty div - we're not displaying these stats anymore
    return html.Div()

# Define callback for updating the slider max value and marks
@app.callback(
    [Output("connection-filter", "max"),
     Output("connection-filter", "marks"),
     Output("connection-filter", "value"),
     Output("connections-description", "children"),
     Output("graph-data", "data")],
    [Input("analyze-button", "n_clicks")],
    [State("project-directory", "value"),
     State("entry-point", "value"),
     State("module-base", "value")]
)
def update_slider_and_store_data(n_clicks, project_dir, entry_point, module_base):
    # Default values
    default_max = 20
    default_marks = {i: str(i) for i in range(0, 21, 5)}
    default_value = [0, default_max]
    description = "Adjust to filter nodes by their connection count (total imports + imported by)"
    
    # Return defaults if no analysis has been done
    if n_clicks == 0 or not project_dir:
        return default_max, default_marks, default_value, description, None
    
    try:
        # Build the dependency graph
        G, file_to_module = build_dependency_graph(project_dir, module_base)
        
        # Calculate connection counts
        connection_counts = {}
        for node in G.nodes():
            in_degree = G.in_degree(node)
            out_degree = G.out_degree(node)
            connection_counts[node] = in_degree + out_degree
        
        max_connections = max(connection_counts.values()) if connection_counts else 0
        max_val = max(max_connections, 1)  # Ensure at least 1
        
        # Create marks based on the maximum connection count
        step = max(1, max_val // 10)  # At most 10 marks
        marks = {i: str(i) for i in range(0, max_val + 1, step)}
        if max_val not in marks:
            marks[max_val] = str(max_val)
        
        # Store graph data
        graph_data = {
            'nodes': list(G.nodes()),
            'edges': list(G.edges()),
            'file_to_module': {k: v for k, v in file_to_module.items() if k in G.nodes()},
            'connection_counts': connection_counts
        }
        
        # Add entry point information
        if entry_point and entry_point.strip():
            if not os.path.isabs(entry_point):
                full_entry_point = os.path.join(project_dir, entry_point)
            else:
                full_entry_point = entry_point
            
            if full_entry_point in G:
                required = find_required_files(G, full_entry_point)
                graph_data['entry_point'] = full_entry_point
                graph_data['required'] = list(required)
        
        description = f"Filter by connection count: {len(connection_counts)} nodes with 0 to {max_connections} connections"
        
        return max_val, marks, [0, max_val], description, graph_data
    except Exception as e:
        return default_max, default_marks, default_value, f"Error: {str(e)}", None

# Add callback to update the node table
@app.callback(
    Output('node-table-container', 'children'),
    [Input('cytoscape-graph', 'elements'),
     Input('graph-data', 'data')]
)
def update_node_table(elements, graph_data):
    if not elements or not graph_data:
        return html.P("No data to display", style={'textAlign': 'center', 'color': '#666'})
    
    try:
        # Reconstruct basic graph structure
        G = nx.DiGraph()
        G.add_nodes_from(graph_data['nodes'])
        G.add_edges_from(graph_data['edges'])
        file_to_module = graph_data.get('file_to_module', {})
        connection_counts = graph_data.get('connection_counts', {})
        
        # Extract node data from the elements
        node_data = []
        for element in elements:
            if 'source' not in element['data']:  # It's a node, not an edge
                node_id = element['data']['id']
                
                # Get display name and directory
                display_name = element['data'].get('label', os.path.basename(node_id))
                directory = element['data'].get('directory', '')
                
                # Get just the last directory name for display
                dir_name = os.path.basename(directory) if directory else ""
                
                # Get connection stats
                imports = element['data'].get('imports', G.out_degree(node_id) if node_id in G else 0)
                imported_by = element['data'].get('imported_by', G.in_degree(node_id) if node_id in G else 0)
                total_connections = imports + imported_by
                
                # Collect node type/category
                node_type = "Default"
                if 'entrypoint' in element.get('classes', ''):
                    node_type = "Entry Point"
                elif 'required' in element.get('classes', ''):
                    node_type = "Required"
                elif 'unused' in element.get('classes', ''):
                    node_type = "Unused"
                
                node_data.append({
                    'id': node_id,
                    'name': display_name,
                    'directory': dir_name,
                    'imports': imports,
                    'imported_by': imported_by,
                    'total': total_connections,
                    'type': node_type,
                    'color': element['data'].get('color', '#cccccc')
                })
        
        # Sort by total connections (descending)
        node_data.sort(key=lambda x: x['total'], reverse=True)
        
        # Convert to DataFrame for the data table
        df = pd.DataFrame(node_data)
        
        # Create DataTable
        table = dash_table.DataTable(
            id='node-datatable',
            columns=[
                {'name': 'Module/File', 'id': 'name'},
                {'name': 'Directory', 'id': 'directory'},
                {'name': 'Imports', 'id': 'imports', 'type': 'numeric'},
                {'name': 'Imported By', 'id': 'imported_by', 'type': 'numeric'},
                {'name': 'Total', 'id': 'total', 'type': 'numeric'},
                {'name': 'Type', 'id': 'type'},
            ],
            data=df.to_dict('records'),
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '8px',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'maxWidth': 0,
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                },
                {
                    'if': {'filter_query': '{type} = "Entry Point"'},
                    'backgroundColor': 'rgba(214, 39, 40, 0.1)'
                },
                {
                    'if': {'filter_query': '{type} = "Required"'},
                    'backgroundColor': 'rgba(44, 160, 44, 0.1)'
                },
                {
                    'if': {'filter_query': '{type} = "Unused"'},
                    'backgroundColor': 'rgba(255, 127, 14, 0.1)'
                },
            ],
            style_cell_conditional=[
                {'if': {'column_id': 'name'}, 'width': '25%'},
                {'if': {'column_id': 'directory'}, 'width': '20%'},
                {'if': {'column_id': 'imports'}, 'textAlign': 'center', 'width': '15%'},
                {'if': {'column_id': 'imported_by'}, 'textAlign': 'center', 'width': '15%'},
                {'if': {'column_id': 'total'}, 'textAlign': 'center', 'width': '10%', 'fontWeight': 'bold'},
                {'if': {'column_id': 'type'}, 'textAlign': 'center', 'width': '15%'},
            ],
            page_size=20,  # Increased from 10 to 20
            sort_action='native',
            filter_action='native',
        )
        
        # Node count information
        count_info = html.Div([
            html.P(f"Showing {len(node_data)} nodes", style={'textAlign': 'right', 'fontStyle': 'italic', 'fontSize': '12px'})
        ])
        
        return html.Div([
            table,
            count_info
        ])
        
    except Exception as e:
        return html.Div([
            html.P("Error generating table:", style={'color': 'red', 'fontWeight': 'bold'}),
            html.P(str(e))
        ])

# Add callback for downloading the CSV
@app.callback(
    Output("download-dataframe-csv", "data"),
    [Input("download-csv-button", "n_clicks")],
    [State("node-datatable", "data")],
    prevent_initial_call=True,
)
def download_csv(n_clicks, data):
    if n_clicks is None or not data:
        return no_update
    
    df = pd.DataFrame(data)
    return dict(
        content=df.to_csv(index=False),
        filename="dependency-data.csv"
    )

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
