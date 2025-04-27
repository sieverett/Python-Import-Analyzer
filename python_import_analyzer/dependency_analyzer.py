import ast
import os
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, List, Set, Tuple

# Add plotly imports
import plotly.graph_objects as go


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to extract import statements from Python files."""    
    
    def __init__(self):
        self.imports = set()
    
    def visit_Import(self, node):
        for name in node.names:
            self.imports.add(name.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.add(node.module)
        self.generic_visit(node)


def extract_imports(file_path: str) -> Set[str]:
    """Extract import statements from a Python file."""

    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read())
            visitor = ImportVisitor()
            visitor.visit(tree)
            return visitor.imports
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return set()


def find_python_files(directory: str) -> List[str]:
    """Find all Python files in a directory and its subdirectories."""    
    py_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))
    return py_files


def map_imports_to_files(directory: str, module_base: str = None) -> Tuple[Dict[str, str], Dict[str, Set[str]]]:
    """Map module names to file paths and track imports for each file."""    
    py_files = find_python_files(directory)
    module_to_file = {}
    file_imports = {}
    
    # Create mapping from module name to file path
    for file_path in py_files:
        rel_path = os.path.relpath(file_path, directory)
        module_name = rel_path.replace(os.sep, '.').replace('.py', '')
        if module_base:
            module_name = f"{module_base}.{module_name}"
        module_to_file[module_name] = file_path
        
        # Also map each directory as a potential package
        parts = module_name.split('.')
        for i in range(1, len(parts)):
            package_name = '.'.join(parts[:i])
            package_dir = os.path.join(directory, *parts[:i])
            if os.path.isdir(package_dir) and os.path.exists(os.path.join(package_dir, '__init__.py')):
                module_to_file[package_name] = os.path.join(package_dir, '__init__.py')
    
    # Extract imports for each file
    for file_path in py_files:
        file_imports[file_path] = extract_imports(file_path)
    
    return module_to_file, file_imports


def build_dependency_graph(directory: str, module_base: str = None) -> Tuple[nx.DiGraph, Dict[str, str]]:
    """Build a directed graph representing file dependencies."""    
    module_to_file, file_imports = map_imports_to_files(directory, module_base)
    file_to_module = {v: k for k, v in module_to_file.items()}
    
    # Create graph
    G = nx.DiGraph()
    
    # Add nodes (files)
    for file_path in file_imports.keys():
        G.add_node(file_path, name=os.path.basename(file_path))
    
    # Add edges (dependencies)
    for file_path, imports in file_imports.items():
        for imp in imports:
            # Check if this import can be resolved to a file in our codebase
            if imp in module_to_file:
                imported_file = module_to_file[imp]
                G.add_edge(file_path, imported_file)
            else:
                # Check if it's a submodule of any module we know
                for known_module, known_path in module_to_file.items():
                    if imp.startswith(f"{known_module}."):
                        G.add_edge(file_path, known_path)
                        break
    
    return G, file_to_module


def visualize_dependency_graph(G: nx.DiGraph, file_to_module: Dict[str, str], save_path: str = None, interactive: bool = False):
    """Visualize the dependency graph."""    
    if interactive:
        return visualize_interactive_graph(G, file_to_module)
    
    plt.figure(figsize=(12, 8))
    
    # Use spring layout for better visualization
    pos = nx.spring_layout(G, k=0.5, iterations=50)
    
    # Convert full file paths to more readable module names or file names for display
    labels = {}
    for node in G.nodes():
        if node in file_to_module:
            labels[node] = file_to_module[node]
        else:
            labels[node] = os.path.basename(node)
    
    # Draw the graph
    nx.draw(G, pos, with_labels=False, node_color='lightblue', node_size=500, arrows=True)
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=8)
    
    plt.title("Python Module Dependencies")
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    plt.show()


def visualize_interactive_graph(G: nx.DiGraph, file_to_module: Dict[str, str]):
    """Create an interactive visualization of the dependency graph using Plotly."""    
    # Get the positions of nodes using a layout algorithm
    pos = nx.spring_layout(G, dim=3, seed=42)
    
    # Create edges
    edge_x = []
    edge_y = []
    edge_z = []
    
    for edge in G.edges():
        x0, y0, z0 = pos[edge[0]]
        x1, y1, z1 = pos[edge[1]]
        
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])
    
    edge_trace = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines'
    )
    
    # Create nodes
    node_x = []
    node_y = []
    node_z = []
    
    for node in G.nodes():
        x, y, z = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)
    
    # Prepare node text for hover information
    node_text = []
    for node in G.nodes():
        if node in file_to_module:
            display_name = file_to_module[node]
        else:
            display_name = os.path.basename(node)
            
        imports = len(list(G.predecessors(node)))
        imported_by = len(list(G.successors(node)))
        
        node_text.append(f"File: {display_name}<br>"
                        f"Imports: {imports}<br>"
                        f"Imported by: {imported_by}")
    
    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            size=10,
            colorbar=dict(
                thickness=15,
                title=dict(
                    text='Node Connections',
                    side='right'
                ),
                xanchor='left'
            ),
            line_width=2,
            color=[len(list(G.successors(node))) for node in G.nodes()],
        )
    )
    
    # Create the figure
    fig = go.Figure(data=[edge_trace, node_trace],
                  layout=go.Layout(
                      title=dict(
                          text='Interactive Python Module Dependencies',
                          font=dict(size=16)
                      ),
                      showlegend=False,
                      hovermode='closest',
                      margin=dict(b=20,l=5,r=5,t=40),
                      scene=dict(
                          xaxis=dict(showticklabels=False),
                          yaxis=dict(showticklabels=False),
                          zaxis=dict(showticklabels=False)
                      ),
                      annotations=[dict(
                          showarrow=False,
                          xref="paper", yref="paper",
                          x=0.005, y=-0.002)],
                  )
                )
    
    return fig


def visualize_interactive_2d_graph(G: nx.DiGraph, file_to_module: Dict[str, str], entry_point: str = None):
    """Create a 2D interactive visualization with node colors based on entry point dependencies."""    
    # Get positions
    pos = nx.spring_layout(G, seed=42)
    
    # Determine node colors based on entry point relationship
    node_colors = []
    node_sizes = []
    required_nodes = set()
    
    if entry_point and entry_point in G:
        required_nodes = find_required_files(G, entry_point)
    
    for node in G.nodes():
        if not entry_point or entry_point not in G:
            # Default coloring if no entry point specified
            node_colors.append('rgba(31, 119, 180, 0.8)')
        elif node == entry_point:
            # Entry point
            node_colors.append('rgba(214, 39, 40, 0.9)')  # Red for entry point
        elif node in required_nodes:
            # Required by entry point
            node_colors.append('rgba(44, 160, 44, 0.8)')  # Green for required
        else:
            # Not required by entry point
            node_colors.append('rgba(255, 127, 14, 0.8)')  # Orange for unused
        
        # Size based on importance (in-degree)
        node_sizes.append(5 + 3 * G.in_degree(node))
    
    # Create edges
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.7, color='#888'),
        hoverinfo='none',
        mode='lines'
    )
    
    # Create nodes
    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
    
    # Prepare node text
    node_text = []
    for node in G.nodes():
        if node in file_to_module:
            display_name = file_to_module[node]
        else:
            display_name = os.path.basename(node)
            
        imports = len(list(G.predecessors(node)))
        imported_by = len(list(G.successors(node)))
        
        node_text.append(f"File: {display_name}<br>"
                        f"Imports: {imports}<br>"
                        f"Imported by: {imported_by}")
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            color=node_colors,
            size=node_sizes,
            line=dict(width=1, color='#000')
        )
    )
    
    # Create the figure
    fig = go.Figure(data=[edge_trace, node_trace],
                  layout=go.Layout(
                      title=dict(
                          text='Interactive Python Module Dependencies',
                          font=dict(size=16)
                      ),
                      showlegend=False,
                      hovermode='closest',
                      margin=dict(b=20,l=5,r=5,t=40),
                      xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                      yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                      plot_bgcolor='rgba(255, 255, 255, 0.9)',
                      annotations=[dict(
                          showarrow=False,
                          xref="paper", yref="paper",
                          x=0.005, y=-0.002)],
                  )
                )
    
    return fig


def find_required_files(G: nx.DiGraph, entry_point: str) -> Set[str]:
    """Find all files required by an entry point."""    
    if entry_point not in G:
        raise ValueError(f"Entry point {entry_point} not found in the graph")
    
    # Perform DFS from the entry point to find all reachable nodes
    reachable = nx.descendants(G, entry_point)
    reachable.add(entry_point)  # Include the entry point itself
    
    return reachable


def find_unused_files(G: nx.DiGraph, entry_point: str) -> Set[str]:
    """Find all files not required by an entry point."""    
    required = find_required_files(G, entry_point)
    all_files = set(G.nodes())
    
    return all_files - required


def analyze_dependencies(directory: str, entry_point: str = None, module_base: str = None, 
                       visualize: bool = True, interactive: bool = False, viz_type: str = '2d'):
    """Analyze dependencies in a Python project."""    
    G, file_to_module = build_dependency_graph(directory, module_base)
    
    # Print basic graph info
    print(f"Total Python files: {len(G.nodes())}")
    print(f"Total dependencies: {len(G.edges())}")
    
    if entry_point:
        # Make sure entry_point is a full file path
        if not os.path.isabs(entry_point):
            entry_point = os.path.join(directory, entry_point)
        
        if entry_point not in G:
            print(f"Warning: Entry point {entry_point} not found in the graph")
        else:
            required_files = find_required_files(G, entry_point)
            unused_files = find_unused_files(G, entry_point)
            
            print(f"\nRequired by {os.path.basename(entry_point)}: {len(required_files)} files")
            print(f"Not required by {os.path.basename(entry_point)}: {len(unused_files)} files")
            
            if unused_files:
                print("\nPotentially unused files:")
                for file in sorted(unused_files):
                    print(f"  - {file}")
    
    if visualize:
        if interactive:
            if viz_type == '3d':
                return G, file_to_module, visualize_interactive_graph(G, file_to_module)
            else:
                return G, file_to_module, visualize_interactive_2d_graph(G, file_to_module, entry_point)
        else:
            visualize_dependency_graph(G, file_to_module)
    
    return G, file_to_module