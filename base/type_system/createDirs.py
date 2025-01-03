import os


directories = [
    "core",
    "connectors",
    "definitions",
    "tests",
    "examples",
]

files = {
    "core": ["__init__.py", "types.py", "events.py", "errors.py", "utils.py"],
    "connectors": ["__init__.py", "base.py", "database.py", "api.py"],
    "definitions": ["__init__.py", "business.py", "finance.py", "products.py", "basic_types.py"],
    "tests": ["__init__.py", "test_types.py", "test_connectors.py", "test_events.py"],
    "examples": ["example_usage.py"],
}

base_dir = "C:\\projects\\appserver\\base\\type_system"
# Create the base directory
if not os.path.exists(base_dir):
    os.makedirs(base_dir)

# Create subdirectories and files
for directory in directories:
    dir_path = os.path.join(base_dir, directory)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    if directory in files:
        for file in files[directory]:
            file_path = os.path.join(dir_path, file)
            with open(file_path, "w") as f:
                if file == "README.md":
                    f.write(f"# {directory.capitalize()} Directory\n")
                elif file == "__init__.py":
                    f.write(f"# Package initializer for {directory}\n")
                elif file == "types.py":
                    f.write("# Type model definitions and core functions.\n")
                elif file == "events.py":
                    f.write("# Event handling mechanism.\n")
                elif file == "errors.py":
                    f.write("# Custom exception classes.\n")
                elif file == "utils.py":
                    f.write("# Utility functions.\n")
                elif file == "base.py":
                    f.write("# Abstract base class for connectors.\n")
                elif file == "database.py":
                    f.write("# Database connector example.\n")
                elif file == "api.py":
                    f.write("# API connector example.\n")
                elif file == "business.py":
                    f.write("# Business-related types (e.g., Customer, Invoice).\n")
                elif file == "finance.py":
                    f.write("# Finance-related types (e.g., Currency, Payment).\n")
                elif file == "products.py":
                    f.write("# Product-related types (e.g., Product, Category).\n")
                elif file == "basic_types.py":
                    f.write("# Basic types.\n")
                elif file == "test_types.py":
                    f.write("# Unit tests for types module.\n")
                elif file == "test_connectors.py":
                    f.write("# Unit tests for connectors module.\n")
                elif file == "test_events.py":
                    f.write("# Unit tests for events module.\n")
                elif file == "example_usage.py":
                    f.write("# Example usage of the type system.\n")
                
                # You can add more detailed initial content here if needed
                pass  # Create an empty file





