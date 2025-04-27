# Python-Import-Analyzer

A powerful tool for visualizing and analyzing import dependencies in Python projects. This tool helps you understand the structure of your Python codebase by creating interactive and static visualizations of module dependencies.

## Features

- **Interactive Dash Dashboard**: Explore your project dependencies through a full-featured web interface
- **Static and Interactive Visualizations**: Generate both matplotlib static images and plotly interactive graphs
- **2D and 3D Visualizations**: Choose between 2D and 3D interactive dependency graphs
- **Entry Point Analysis**: Identify required and potentially unused modules based on a specified entry point
- **Dependency Metrics**: Get insights about imports, module relationships, and dependency chains
- **Flexible Integration**: Use as a standalone tool or integrate into your development workflow

## Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Python-Import-Analyzer.git
   cd Python-Import-Analyzer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Interactive Dashboard Usage

The primary way to use Python-Import-Analyzer is through its interactive Dash dashboard.

### Running the Dashboard

Simply run the dashboard script from the command line:

```bash
python dependency_dashboard.py
```

This will start a local web server (typically at http://127.0.0.1:8050/) and automatically open the dashboard in your default web browser.

### Dashboard Interface

The dashboard provides a user-friendly interface with the following components:

#### Left Sidebar

- **Project Directory**: Enter the path to your Python project
- **Entry Point File**: (Optional) Specify an entry point to analyze required vs. unused files
- **Module Base**: (Optional) Specify a base module name for import resolution
- **Graph Layout**: Choose from various layout algorithms for the dependency graph
- **Include/Exclude Keywords**: Filter nodes by keywords in their paths
- **Connection Count Filter**: Filter nodes by their number of connections
- **Connection Depth**: Control the depth of connections shown when selecting a node

#### Main Visualization Area

- **Interactive Graph**: Nodes represent Python files, and edges represent import relationships
- **Node Selection**: Click on any node to focus on its connections
- **Node Colors**: Color-coded by directory for easy identification
- **Border Colors**: 
  - Red: Entry point files
  - Green: Files required by the entry point
  - Orange: Files not required by the entry point (potentially unused)
- **Node Size**: Larger nodes indicate files with more connections
- **Zoom & Navigation**: Pan and zoom to explore complex dependency structures
- **Selection Controls**: Reset selection to view the entire graph again

#### Data Table

- **Sortable Table**: View detailed information about all nodes in the graph
- **Filtering**: Filter the table by any column
- **CSV Export**: Download the dependency data as a CSV file
- **Node Statistics**: See connection counts and node types at a glance

### Dashboard Workflow

1. **Enter Project Information**:
   - Input your project directory path
   - Optionally specify an entry point file 
   - Optionally specify a module base

2. **Click "Analyze Dependencies"** to generate the visualization

3. **Explore Your Project**:
   - Use the filters to focus on specific parts of your code
   - Click on nodes to see their connections
   - Adjust connection depth to see more or fewer related nodes
   - Use different layouts to view your dependency structure from different perspectives

4. **Analyze Table Data**:
   - Sort by "Total" connections to find central modules
   - Sort by "Imported By" to find widely-used modules
   - Filter by "Type" to find potentially unused modules
   - Download the data for further analysis in spreadsheet software

## API Usage (For Programming Integration)

If you prefer to use Python-Import-Analyzer programmatically, you can import functions from the `dependency_analyzer` module:

```python
from dependency_analyzer import analyze_dependencies

# Generate a 2D interactive visualization
G, file_to_module, fig = analyze_dependencies(
    '/path/to/your/python/project',
    interactive=True,
    viz_type='2d'
)

# Display the interactive visualization
fig.show()
```

## API Reference

### Main Functions

- **analyze_dependencies(directory, entry_point=None, module_base=None, visualize=True, interactive=False, viz_type='2d')**
  
  Analyzes dependencies in a Python project.

  - `directory`: Path to the Python project
  - `entry_point`: Optional path to an entry point file to analyze required/unused files
  - `module_base`: Optional base module name for import resolution
  - `visualize`: Whether to generate visualizations
  - `interactive`: Whether to create interactive plotly visualizations
  - `viz_type`: Type of interactive visualization ('2d' or '3d')

- **build_dependency_graph(directory, module_base=None)**
  
  Builds a directed graph representing file dependencies.

- **find_required_files(G, entry_point)**
  
  Finds all files required by an entry point.

- **find_unused_files(G, entry_point)**
  
  Finds all files not required by an entry point.

## Examples

### Basic Dashboard Usage

```bash
# Start the interactive dashboard
python dependency_dashboard.py
```

### Programmatic Usage

```python
from dependency_analyzer import analyze_dependencies

# Launch dashboard with entry point analysis and 3D visualization
G, file_to_module, fig = analyze_dependencies(
    '/path/to/your/project',
    entry_point='/path/to/your/project/main.py',
    module_base='your_package',
    interactive=True,
    viz_type='3d'
)

# Save the interactive visualization to HTML
fig.write_html('dependency_graph.html')
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
