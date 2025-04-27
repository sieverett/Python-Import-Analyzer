import os
import ast
import shutil
import tempfile
import pytest
import networkx as nx
import plotly.graph_objects as go
from python_import_analyzer.dependency_analyzer import (
    extract_imports, 
    find_python_files, 
    map_imports_to_files,
    build_dependency_graph, 
    find_required_files, 
    find_unused_files,
    analyze_dependencies,
    visualize_dependency_graph,
    visualize_interactive_graph,
    visualize_interactive_2d_graph,
    ImportVisitor
)

class TestDependencyAnalyzer:
    """Test cases for dependency_analyzer.py functions."""
    
    @pytest.fixture
    def test_project(self):
        """Create a temporary test project with Python files."""
        temp_dir = tempfile.mkdtemp()
        
        # Create main.py
        with open(os.path.join(temp_dir, "main.py"), "w") as f:
            f.write("import util\nimport helper\n\ndef main():\n    pass")
            
        # Create util.py
        with open(os.path.join(temp_dir, "util.py"), "w") as f:
            f.write("import external_lib\n\ndef util_func():\n    pass")
            
        # Create helper.py
        with open(os.path.join(temp_dir, "helper.py"), "w") as f:
            f.write("import util\n\ndef helper_func():\n    pass")
            
        # Create unused.py
        with open(os.path.join(temp_dir, "unused.py"), "w") as f:
            f.write("import sys\n\ndef unused_func():\n    pass")
        
        # Create a subdirectory with __init__.py
        os.makedirs(os.path.join(temp_dir, "submodule"))
        with open(os.path.join(temp_dir, "submodule", "__init__.py"), "w") as f:
            f.write("# Init file")
            
        # Create a submodule file
        with open(os.path.join(temp_dir, "submodule", "subfile.py"), "w") as f:
            f.write("import util\n\ndef sub_func():\n    pass")
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_import_visitor(self):
        """Test the ImportVisitor AST node visitor."""
        # Test with import statements
        visitor = ImportVisitor()
        import_node = ast.parse("import os\nimport sys, pathlib").body[0]
        visitor.visit_Import(import_node)
        assert "os" in visitor.imports
        
        # Test with from import statements
        visitor = ImportVisitor()
        from_import_node = ast.parse("from os import path").body[0]
        visitor.visit_ImportFrom(from_import_node)
        assert "os" in visitor.imports
    
    def test_extract_imports(self, test_project):
        """Test extracting imports from a Python file."""
        main_file = os.path.join(test_project, "main.py")
        imports = extract_imports(main_file)
        assert imports == {"util", "helper"}
        
        helper_file = os.path.join(test_project, "helper.py")
        imports = extract_imports(helper_file)
        assert imports == {"util"}
    
    def test_extract_imports_error_handling(self, test_project):
        """Test that extract_imports handles errors gracefully."""
        # Create a file with invalid syntax
        invalid_file = os.path.join(test_project, "invalid.py")
        with open(invalid_file, "w") as f:
            f.write("def broken_func():\n    return 'unclosed string")
        
        # Should return an empty set and not raise an exception
        imports = extract_imports(invalid_file)
        assert imports == set()
    
    def test_find_python_files(self, test_project):
        """Test finding all Python files in a directory."""
        python_files = find_python_files(test_project)
        assert len(python_files) == 6  # main.py, util.py, helper.py, unused.py, invalid.py, submodule/subfile.py, submodule/__init__.py
        
        # Check if all expected files are found
        filenames = [os.path.basename(f) for f in python_files]
        assert "main.py" in filenames
        assert "util.py" in filenames
        assert "helper.py" in filenames
        assert "unused.py" in filenames
        assert "__init__.py" in filenames
        assert "subfile.py" in filenames
        
        # Test with a non-existent directory
        non_existent = os.path.join(test_project, "does_not_exist")
        assert find_python_files(non_existent) == []
    
    def test_map_imports_to_files(self, test_project):
        """Test mapping imports to file paths."""
        module_to_file, file_imports = map_imports_to_files(test_project)
        
        # Check module_to_file mapping
        assert len(module_to_file) >= 6  # At least the 6 Python files we created
        
        # Verify that main.py is correctly mapped
        main_rel_path = os.path.join("main").replace(os.sep, '.')
        main_file = os.path.join(test_project, "main.py")
        assert module_to_file.get(main_rel_path) == main_file
        
        # Check that submodule is mapped to __init__.py
        submodule_rel_path = os.path.join("submodule").replace(os.sep, '.')
        submodule_init = os.path.join(test_project, "submodule", "__init__.py")
        assert module_to_file.get(submodule_rel_path) == submodule_init
        
        # Check file_imports
        assert len(file_imports) >= 6  # At least the 6 Python files we created
        assert file_imports[main_file] == {"util", "helper"}
        
        # Test with module_base
        module_to_file, file_imports = map_imports_to_files(test_project, module_base="testpkg")
        
        # With module_base, the keys should have the prefix
        main_with_base = f"testpkg.{main_rel_path}"
        assert module_to_file.get(main_with_base) == main_file
    
    def test_build_dependency_graph(self, test_project):
        """Test building a dependency graph for a project."""
        G, file_to_module = build_dependency_graph(test_project)
        
        # Check nodes
        assert len(G.nodes()) >= 5  # At least main.py, util.py, helper.py, unused.py, submodule/__init__.py
        
        # Check edges
        main_file = os.path.join(test_project, "main.py")
        util_file = os.path.join(test_project, "util.py")
        helper_file = os.path.join(test_project, "helper.py")
        
        # main.py imports util.py and helper.py
        assert G.has_edge(main_file, util_file)
        assert G.has_edge(main_file, helper_file)
        
        # helper.py imports util.py
        assert G.has_edge(helper_file, util_file)
        
        # Check file_to_module
        assert util_file in file_to_module
        assert file_to_module[util_file] == "util"
        
        # Test with module_base
        G, file_to_module = build_dependency_graph(test_project, module_base="testpkg")
        assert file_to_module[util_file] == "testpkg.util"
    
    def test_find_required_files(self, test_project):
        """Test finding files required by an entry point."""
        G, _ = build_dependency_graph(test_project)
        
        main_file = os.path.join(test_project, "main.py")
        required = find_required_files(G, main_file)
        
        # Check that main.py and its dependencies are in required
        util_file = os.path.join(test_project, "util.py")
        helper_file = os.path.join(test_project, "helper.py")
        
        assert main_file in required
        assert util_file in required
        assert helper_file in required
        
        # Test with a node not in the graph
        with pytest.raises(ValueError):
            find_required_files(G, "nonexistent.py")
    
    def test_find_unused_files(self, test_project):
        """Test finding files not required by an entry point."""
        G, _ = build_dependency_graph(test_project)
        
        main_file = os.path.join(test_project, "main.py")
        unused = find_unused_files(G, main_file)
        
        # Check that unused.py is in the unused set
        unused_file = os.path.join(test_project, "unused.py")
        assert unused_file in unused
        
        # Check that main's dependencies are not in unused
        util_file = os.path.join(test_project, "util.py")
        helper_file = os.path.join(test_project, "helper.py")
        
        assert util_file not in unused
        assert helper_file not in unused
    
    def test_analyze_dependencies(self, test_project, monkeypatch):
        """Test the analyze_dependencies function."""
        # Mock visualization to avoid showing plots during tests
        monkeypatch.setattr("matplotlib.pyplot.show", lambda: None)
        
        # Test without visualization
        G, file_to_module = analyze_dependencies(test_project, visualize=False)
        assert isinstance(G, nx.DiGraph)
        assert isinstance(file_to_module, dict)
        
        # Test with entry point
        main_file = os.path.join(test_project, "main.py")
        G, file_to_module = analyze_dependencies(test_project, entry_point=main_file, visualize=False)
        assert isinstance(G, nx.DiGraph)
        
        # Test with interactive 2D visualization
        G, file_to_module, fig = analyze_dependencies(
            test_project, 
            entry_point=main_file, 
            visualize=True, 
            interactive=True, 
            viz_type='2d'
        )
        assert isinstance(fig, go.Figure)
        
        # Test with interactive 3D visualization
        G, file_to_module, fig = analyze_dependencies(
            test_project, 
            entry_point=main_file, 
            visualize=True, 
            interactive=True, 
            viz_type='3d'
        )
        assert isinstance(fig, go.Figure)
        
        # Test with relative entry point path
        rel_main = os.path.relpath(main_file, test_project)
        G, file_to_module = analyze_dependencies(test_project, entry_point=rel_main, visualize=False)
        assert isinstance(G, nx.DiGraph)
        
        # Test with non-existent entry point
        G, file_to_module = analyze_dependencies(test_project, entry_point="nonexistent.py", visualize=False)
        assert isinstance(G, nx.DiGraph)
    
    def test_visualize_dependency_graph(self, test_project, monkeypatch):
        """Test visualizing a dependency graph."""
        G, file_to_module = build_dependency_graph(test_project)
        
        # Mock show and savefig to avoid displaying or saving plots during tests
        monkeypatch.setattr("matplotlib.pyplot.show", lambda: None)
        saved_path = [None]
        def mock_savefig(path, **kwargs):
            saved_path[0] = path
        monkeypatch.setattr("matplotlib.pyplot.savefig", mock_savefig)
        
        # Test standard visualization
        visualize_dependency_graph(G, file_to_module)
        
        # Test with save
        visualize_dependency_graph(G, file_to_module, save_path="test.png")
        assert saved_path[0] == "test.png"
        
        # Test interactive (should return a figure)
        fig = visualize_dependency_graph(G, file_to_module, interactive=True)
        assert isinstance(fig, go.Figure)
    
    def test_visualize_interactive_graph(self, test_project, monkeypatch):
        """Test interactive 3D graph visualization."""
        G, file_to_module = build_dependency_graph(test_project)
        
        # Mock spring_layout to get deterministic positions for testing
        def mock_spring_layout(G, **kwargs):
            pos = {}
            for i, node in enumerate(G.nodes()):
                pos[node] = (i, i, i)  # Simple position
            return pos
        monkeypatch.setattr(nx, "spring_layout", mock_spring_layout)
        
        # Generate the figure
        fig = visualize_interactive_graph(G, file_to_module)
        
        # Check that the figure is created
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2  # Should have edge trace and node trace
        
        # Check edge trace
        edge_trace = fig.data[0]
        assert isinstance(edge_trace, go.Scatter3d)
        assert edge_trace.mode == 'lines'
        
        # Check node trace
        node_trace = fig.data[1]
        assert isinstance(node_trace, go.Scatter3d)
        assert node_trace.mode == 'markers'
        assert len(node_trace.text) == len(G.nodes())
    
    def test_visualize_interactive_2d_graph(self, test_project, monkeypatch):
        """Test interactive 2D graph visualization."""
        G, file_to_module = build_dependency_graph(test_project)
        main_file = os.path.join(test_project, "main.py")
        
        # Mock spring_layout to get deterministic positions for testing
        def mock_spring_layout(G, **kwargs):
            pos = {}
            for i, node in enumerate(G.nodes()):
                pos[node] = (i, i)  # Simple 2D position
            return pos
        monkeypatch.setattr(nx, "spring_layout", mock_spring_layout)
        
        # Test without entry point
        fig = visualize_interactive_2d_graph(G, file_to_module)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2  # Should have edge trace and node trace
        
        # Test with entry point
        fig = visualize_interactive_2d_graph(G, file_to_module, entry_point=main_file)
        assert isinstance(fig, go.Figure)
        
        # Check that node colors are different for entry point/required/unused
        node_trace = fig.data[1]
        assert len(set(node_trace.marker.color)) > 1  # Should have different colors
