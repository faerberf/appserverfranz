"""Helper script to run Python files with correct path."""
import os
import sys
import importlib.util

def run_module(module_path: str):
    """Run a Python module with the correct path setup."""
    # Add the project root to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Import and run the module
    module_name = os.path.splitext(os.path.basename(module_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run.py <module_path>")
        sys.exit(1)
    
    module_path = sys.argv[1]
    if not os.path.exists(module_path):
        print(f"Error: Module {module_path} does not exist")
        sys.exit(1)
        
    run_module(module_path)
