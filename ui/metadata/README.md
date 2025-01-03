# Metadata Manager UI

A Streamlit-based user interface for managing metadata definitions.

## Features

- View and manage node types
- Create new metadata definitions
- Add and edit fields with validation
- View version history
- Support for field constraints
- Type-specific validation rules

## Installation

1. Install requirements:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
streamlit run app.py
```

## Usage

1. **Select Node Type**:
   - Choose an existing node type from the dropdown
   - Or create a new node type by selecting "[Create New Node Type]"

2. **Edit Metadata**:
   - Update description and schema version
   - Add/edit fields with their properties
   - Set validation rules and constraints

3. **View History**:
   - Expand version history to see changes
   - View upgrade definitions for each version

## Field Properties

- **Name**: Unique identifier for the field
- **Type**: Data type (string, integer, decimal, etc.)
- **Description**: Field description
- **Required**: Whether the field is mandatory
- **Validation Mode**: Validation strictness
- **Constraints**: Type-specific validation rules
  - Numeric: min/max values
  - String: regex patterns
