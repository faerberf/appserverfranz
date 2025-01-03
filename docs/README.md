# Application Server Documentation

## Overview
This application server provides a modular system for managing business data with versioning support.

## Package Structure

### Base Package (`base/`)
Core functionality for node management, storage, and metadata handling.
- [API Documentation](base.md)
- Key Features:
  - Node creation and management
  - Abstract storage interface
  - Metadata management
  - Version upgrade support

### Finance Package (`finance/`)
Financial operations and sales order management.
- [API Documentation](finance.md)
- Key Features:
  - Sales order creation and management
  - Order item management
  - Total calculation
  - Status tracking

### Master Data Package (`masterdata/`)
Master data management for products and customers.
- [API Documentation](masterdata.md)
- Key Features:
  - Product management
  - Data versioning
  - CRUD operations

## Getting Started

1. Install the package in development mode:
```bash
pip install -e .
```

2. Run the example application:
```bash
python main.py
```

## Architecture

The application follows a modular architecture with clear separation of concerns:

1. **Base Layer**
   - Provides core functionality
   - Abstract interfaces for storage
   - Version management
   - Metadata handling

2. **Business Layers**
   - Finance: Sales order processing
   - Master Data: Product and customer management
   - Each layer uses the base layer for persistence

3. **Storage**
   - File system based by default
   - Extensible through Storage interface
   - Version history support

## Data Versioning

All data types support versioning through metadata definitions:
- Version upgrades are automatic
- Data is upgraded when read
- Version history is maintained
- Clean upgrade paths defined in metadata

## Best Practices

1. Always use package interfaces instead of direct module imports
2. Follow version upgrade patterns when modifying data structures
3. Use proper type hints and documentation
4. Handle errors appropriately
5. Use decimal for financial calculations
