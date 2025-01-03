"""
Streamlit UI for Sales Order Management.
This module provides a professional interface for creating and managing sales orders.
"""
import os
import sys
import streamlit as st
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
import pandas as pd

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from base.generator import Generator
from base.schema.evolution import SchemaEvolution
from finance.sales_order import SalesOrder, SalesOrderAPI


def load_schema_evolution(metadata_path: str) -> SchemaEvolution:
    """Load schema evolution from metadata path."""
    evolution = SchemaEvolution()
    
    for schema_file in [
        os.path.join(metadata_path, "global_node_definitions.json"),
        os.path.join(metadata_path, "finance", "sales_order_header.json"),
        os.path.join(metadata_path, "finance", "sales_order_item.json"),
    ]:
        if os.path.exists(schema_file):
            schema = SchemaEvolution.from_file(schema_file)
            for version in schema.get_all_versions():
                evolution.add_version(version)
    return evolution

def initialize_services():
    """Initialize required services."""
    base_path = project_root
    data_path = os.path.join(base_path, "data")
    metadata_path = os.path.join(base_path, "metadata")
    
    schema_evolution = load_schema_evolution(metadata_path)
    finance_generator = Generator(data_path, metadata_path, schema_evolution=schema_evolution)
    
    order_service = SalesOrder(finance_generator)
    order_api = SalesOrderAPI(order_service, finance_generator.version_manager)
    
    return order_api

def initialize_session_state():
    """Initialize session state variables."""
    if "mode" not in st.session_state:
        st.session_state.mode = "list"
    if "items_list" not in st.session_state:
        st.session_state.items_list = []
    if "order_header" not in st.session_state:
        st.session_state.order_header = {}

def reset_session_state():
    """Reset session state variables."""
    st.session_state.mode = "list"
    st.session_state.items_list = []
    st.session_state.order_header = {}
    if "edit_initialized" in st.session_state:
        del st.session_state.edit_initialized
    if "selected_order" in st.session_state:
        del st.session_state.selected_order

def create_order_header(existing_data: Dict = None) -> Dict:
    """Create order header form."""
    st.subheader("Order Information")
    
    # Store form data in session state
    if "order_header" not in st.session_state:
        st.session_state.order_header = existing_data or {}
    
    customer_name = st.text_input("Customer Name", key="customer_name", 
                                value=st.session_state.order_header.get("customer_name", ""))
    customer_email = st.text_input("Customer Email", key="customer_email", 
                                 value=st.session_state.order_header.get("customer_email", ""))
    customer_phone = st.text_input("Customer Phone", key="customer_phone", 
                                 value=st.session_state.order_header.get("customer_phone", ""))
    shipping_address = st.text_area("Shipping Address", key="shipping_address", 
                                  value=st.session_state.order_header.get("shipping_address", ""))
    payment_method = st.selectbox(
        "Payment Method",
        ["credit_card", "bank_transfer", "cash"],
        key="payment_method",
        index=["credit_card", "bank_transfer", "cash"].index(
            st.session_state.order_header.get("payment_method", "credit_card")
        )
    )
    
    # Update session state
    st.session_state.order_header = {
        "customer_name": customer_name,
        "customer_email": customer_email,
        "customer_phone": customer_phone,
        "shipping_address": shipping_address,
        "payment_method": payment_method
    }
    
    return st.session_state.order_header

def create_order_items(existing_items: List = None) -> List[Dict]:
    """Create order items form."""
    st.subheader("Order Items")
    
    # Initialize items list in session state if not exists
    if "items_list" not in st.session_state:
        st.session_state.items_list = []
        # If we have existing items (editing mode), add them to the session state
        if existing_items:
            st.session_state.items_list = list(existing_items)  # Create a new list
    
    with st.form("order_item"):
        cols = st.columns(5)
        with cols[0]:
            product_code = st.text_input("Product Code", key="product_code")
        with cols[1]:
            product_name = st.text_input("Product Name", key="product_name")
        with cols[2]:
            price = st.number_input("Price", min_value=0.0, step=0.01, key="price")
        with cols[3]:
            quantity = st.number_input("Quantity", min_value=1, step=1, key="quantity")
        with cols[4]:
            unit = st.selectbox("Unit", ["pcs", "kg", "l"], key="unit")
        
        if st.form_submit_button("Add Item"):
            if not product_code or not product_name:
                st.error("Product code and name are required")
            else:
                new_item = {
                    "product_code": product_code,
                    "product_name": product_name,
                    "price": str(Decimal(str(price))),
                    "quantity": quantity,
                    "unit": unit,
                    "_schema_version": 2
                }
                st.session_state.items_list.append(new_item)
                st.rerun()
    
    # Display current items in a table
    if st.session_state.items_list:
        st.subheader("Current Items")
        items_data = []
        for idx, item in enumerate(st.session_state.items_list):
            items_data.append({
                "Index": idx,
                "Product Code": item["product_code"],
                "Product Name": item["product_name"],
                "Price": f"${float(Decimal(item['price'])):.2f}",
                "Quantity": item["quantity"],
                "Unit": item["unit"]
            })
        
        df = pd.DataFrame(items_data)
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_columns(["Product Code", "Product Name", "Price", "Quantity", "Unit"], 
                           sortable=True)
        gb.configure_selection(selection_mode="single")
        
        grid_response = AgGrid(
            df,
            gridOptions=gb.build(),
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            allow_unsafe_jscode=True,
            theme="streamlit"
        )
        
        if grid_response["selected_rows"]:
            selected = grid_response["selected_rows"][0]
            if st.button("Remove Selected Item"):
                st.session_state.items_list.pop(selected["Index"])
                st.rerun()
    
    return st.session_state.items_list

def list_orders(order_api: SalesOrderAPI):
    """List all orders with basic information."""
    st.subheader("Orders List")
    
    try:
        # Get orders using the API
        orders = order_api.list_orders("v1")
        
        if not orders:
            st.info("No orders found in the system")
            return

        # Prepare data for AgGrid
        grid_data = []
        for order in orders:
            try:
                header = order["header"]
                customer_name = header.get("customer_name", "Unknown Customer")
                order_date = datetime.fromisoformat(header.get("created_at", "")).strftime("%Y-%m-%d %H:%M:%S") if header.get("created_at") else "Unknown Date"
                
                grid_data.append({
                    "ID": order["id"],
                    "Customer": customer_name,
                    "Date": order_date,
                    "Payment Method": header.get("payment_method", "N/A"),
                    "Status": "Active" if not header.get("date_to") else "Deleted"
                })
            except Exception as e:
                st.error(f"Error processing order: {str(e)}")
                continue

        # Create DataFrame and configure grid
        df = pd.DataFrame(grid_data)
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_columns(["ID", "Customer", "Date", "Payment Method", "Status"], 
                           sortable=True, filterable=True)
        gb.configure_selection(selection_mode="single")
        gb.configure_pagination(enabled=True, paginationAutoPageSize=True)

        # Add button above grid
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("New Order", key="new_order_btn"):
                st.session_state.selected_order = None
                st.session_state.mode = "create"
                st.rerun()

        # Display grid
        grid_response = AgGrid(
            df,
            gridOptions=gb.build(),
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            allow_unsafe_jscode=True,
            theme="streamlit"
        )

        # Handle selection
        if grid_response["selected_rows"]:
            selected = grid_response["selected_rows"][0]
            order_id = str(selected["ID"])
            
            full_order = order_api.get_order("v1", order_id)
            if full_order and isinstance(full_order, dict) and "header" in full_order:
                full_order["id"] = full_order["header"]["id"]
                st.session_state.selected_order = full_order
                st.session_state.mode = "edit"
                st.rerun()
            else:
                st.error(f"Failed to load complete order data for order {order_id}")

    except Exception as e:
        st.error(f"Error listing orders: {str(e)}")

def main():
    """Main application entry point."""
    st.set_page_config(page_title="Sales Order Management", layout="wide")
    st.title("Sales Order Management")
    
    try:
        # Initialize services
        order_api = initialize_services()
        
        # Initialize session state
        if "mode" not in st.session_state:
            st.session_state.mode = "list"
            st.session_state.items_list = []
        
        if st.session_state.mode == "list":
            list_orders(order_api)
        else:  # create or edit mode
            if st.session_state.mode == "edit" and "selected_order" in st.session_state:
                st.subheader(f"Edit Order {st.session_state.selected_order['id']}")
                order = st.session_state.selected_order
                
                # Initialize edit mode data
                if "edit_initialized" not in st.session_state:
                    st.session_state.order_header = order["header"]
                    # Initialize items from the complete order data
                    st.session_state.items_list = list(order.get("items", []))
                    st.session_state.edit_initialized = True
                
                # Create forms
                header = create_order_header(st.session_state.order_header)
                items = create_order_items()
                
                # Save and Cancel buttons side by side
                col1, col2 = st.columns([1, 1])
                with col1:
                    save_clicked = st.button("Save Order", type="primary")
                with col2:
                    cancel_clicked = st.button("Cancel")
                
                if save_clicked:
                    if header.get("customer_name") and st.session_state.items_list:
                        try:
                            if order_api.update_order(
                                "v1",
                                order["id"],
                                header,
                                st.session_state.items_list
                            ):
                                st.success("Order updated successfully!")
                                reset_session_state()
                                st.rerun()
                            else:
                                st.error("Failed to update order")
                        except Exception as e:
                            st.error(f"Error updating order: {str(e)}")
                    else:
                        st.warning("Please fill in customer name and add at least one item.")
                
                if cancel_clicked:
                    reset_session_state()
                    st.rerun()
            else:
                st.subheader("Create New Order")
                
                # Create forms
                header = create_order_header()
                items = create_order_items()
                
                # Save and Cancel buttons side by side
                col1, col2 = st.columns([1, 1])
                with col1:
                    save_clicked = st.button("Save Order", type="primary")
                with col2:
                    cancel_clicked = st.button("Cancel")
                
                if save_clicked:
                    if header.get("customer_name") and st.session_state.items_list:
                        try:
                            if order_api.create_order(
                                "v1",
                                header,
                                st.session_state.items_list
                            ):
                                st.success("Order created successfully!")
                                reset_session_state()
                                st.rerun()
                            else:
                                st.error("Failed to create order")
                        except Exception as e:
                            st.error(f"Error creating order: {str(e)}")
                    else:
                        st.warning("Please fill in customer name and add at least one item.")
                
                if cancel_clicked:
                    reset_session_state()
                    st.rerun()
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
