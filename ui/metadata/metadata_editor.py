import os
import sys
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

import streamlit as st
import pandas as pd
from datetime import datetime

# Replace these with your actual enums or definitions if you have them elsewhere
class FieldType:
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    FLOAT = "float"
    INTEGER = "integer"
    


    @classmethod
    def values(cls):
        return [cls.STRING, cls.NUMBER, cls.BOOLEAN]

class ValidationMode:
    STRICT = "strict"
    LOOSE = "loose"
    NONE = "none"

    @classmethod
    def values(cls):
        return [cls.STRICT, cls.LOOSE, cls.NONE]

# Import the merged MetadataAPI and helper functions from your backend api.py
# Adjust this import to match your actual project path:
# from base.metadata.api import MetadataAPI, convert_fields_dict_to_list, convert_fields_list_to_dict

# Example (dummy) imports for demonstration. Replace with real imports:
from base.metadata.api import (
    MetadataAPI,
    convert_fields_dict_to_list,
    convert_fields_list_to_dict
)

def init_metadata_api():
    """Initialize and return a MetadataAPI instance from the backend."""
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    metadata_path = os.path.join(base_path, "metadata")
    return MetadataAPI(metadata_path)

def display_node_type_selector(api: MetadataAPI) -> Optional[str]:
    """Let the user select or create a node type, and rerun on change."""
    try:
        node_types = api.list_node_types()
        options = ["[Create New Node Type]"] + sorted(node_types)
        selected = st.selectbox("Select Node Type", options, index=0, key="node_type_selector")

        if "prev_node_type" not in st.session_state:
            st.session_state["prev_node_type"] = selected
        elif st.session_state["prev_node_type"] != selected:
            st.session_state["prev_node_type"] = selected
            st.rerun()

        if selected == "[Create New Node Type]":
            with st.expander("Create New Node Type", expanded=True):
                new_type = st.text_input(
                    "New Node Type",
                    placeholder="e.g., finance/invoice",
                    help="Use '/' to organize nodes into categories"
                )
                if new_type:
                    if st.button("Create", type="primary"):
                        try:
                            api.create_metadata(
                                new_type,
                                fields=[],
                                description=f"Metadata for {new_type}"
                            )
                            st.success(f"Created new node type: {new_type}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating node type: {str(e)}")
                return None

        return selected if selected != "[Create New Node Type]" else None

    except Exception as e:
        st.error(f"Error listing node types: {str(e)}")
        return None

def field_editor(field: Optional[Dict[str, Any]] = None, key_suffix: str = "") -> Optional[Dict[str, Any]]:
    """Display form for adding or editing a single field (compact layout)."""
    form_key = f"field_editor_form_{key_suffix}"
    submit_state_key = f"field_editor_submitted_{key_suffix}"

    if submit_state_key not in st.session_state:
        st.session_state[submit_state_key] = False

    with st.form(form_key):
        st.write("### Field Editor")

        # Row 1: Name & Field Type
        col1, col2 = st.columns([1, 1])
        with col1:
            name = st.text_input("Field Name", value=field.get("name", "") if field else "")
        with col2:
            field_type_opts = FieldType.values()
            default_field_type = FieldType.STRING
            if field and "type" in field and field["type"] in field_type_opts:
                default_field_type = field["type"]
            field_type = st.selectbox("Field Type", field_type_opts, index=field_type_opts.index(default_field_type))

        # Row 2: Required, Validation Mode, Field Number
        col3, col4, col5 = st.columns([1, 1, 1])
        with col3:
            required = st.checkbox("Required", value=field.get("required", False) if field else False)
        with col4:
            val_modes = ValidationMode.values()
            default_val_mode = ValidationMode.STRICT
            if field and "validation_mode" in field and field["validation_mode"] in val_modes:
                default_val_mode = field["validation_mode"]
            validation_mode = st.selectbox("Validation Mode", val_modes, index=val_modes.index(default_val_mode))
        with col5:
            field_number = st.number_input(
                "Field Number",
                value=field.get("field_number", 1) if field else 1,
                min_value=1
            )

        # Row 3: Default Value, Description
        col6, col7 = st.columns([1, 2])
        with col6:
            default_value = st.text_input(
                "Default Value",
                value=str(field.get("default", "")) if field and "default" in field else ""
            )
        with col7:
            description = st.text_area(
                "Description",
                value=field.get("description", "") if field else "",
                height=80
            )

        # Constraints
        with st.expander("Constraints"):
            c1, c2 = st.columns([1, 1])
            with c1:
                min_value = st.text_input(
                    "Min Value",
                    value=str(field.get("constraints", {}).get("min", "")) if field else ""
                )
            with c2:
                max_value = st.text_input(
                    "Max Value",
                    value=str(field.get("constraints", {}).get("max", "")) if field else ""
                )

        submitted = st.form_submit_button("Save Field")
        if submitted:
            st.session_state[submit_state_key] = True

    if st.session_state[submit_state_key]:
        if not name:
            st.error("Field name is required")
            return None

        constraints = {}
        if min_value:
            constraints["min"] = min_value
        if max_value:
            constraints["max"] = max_value

        updated_field = {
            "name": name,
            "type": field_type,
            "description": description,
            "required": required,
            "validation_mode": validation_mode,
            "field_number": field_number,
            "constraints": constraints
        }
        if default_value:
            updated_field["default"] = default_value

        if form_key in st.session_state:
            del st.session_state[form_key]
        st.session_state[submit_state_key] = False

        return updated_field

    return None

def display_field_editor(fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Show a small table for fields and allow adding or editing them."""
    updated_fields = fields.copy()

    if updated_fields:
        df = pd.DataFrame([
            {
                "Select": False,
                **{k: str(v) if isinstance(v, dict) else v for k, v in f.items() if k != "validation_mode"}
            }
            for f in updated_fields
        ])

        edited_df = st.data_editor(
            df,
            hide_index=True,
            use_container_width=True,
            disabled=[col for col in df.columns if col != "Select"],
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    "Select",
                    help="Select field to edit",
                    default=False,
                )
            }
        )

        selected_rows = edited_df[edited_df["Select"]]
        num_selected = len(selected_rows)

        if num_selected > 1:
            st.warning("Please select only one field to edit.")
            return updated_fields

        if num_selected == 1:
            field_name = selected_rows.iloc[0]["name"]
            for i, f in enumerate(updated_fields):
                if f["name"] == field_name:
                    result = field_editor(f, key_suffix=f"edit_{field_name}")
                    if result:
                        updated_fields[i] = result
                    return updated_fields

    # If no fields selected, show the form for adding a new one
    result = field_editor(key_suffix="add")
    if result:
        updated_fields.append(result)

    return updated_fields

def display_node_metadata_editor(node_metadata_key: str, original_metadata: Dict[str, Any]):
    """
    Display node metadata in a 2-items-per-row layout for editing,
    with a non-empty label for accessibility (hidden via label_visibility).
    """
    if node_metadata_key not in st.session_state:
        st.session_state[node_metadata_key] = original_metadata.copy()

    meta_dict = st.session_state[node_metadata_key]

    st.write("### Node Metadata")

    # Convert dict items into a list
    pairs = list(meta_dict.items())
    pairs.sort(key=lambda x: x[0])

    new_meta = {}
    for i in range(0, len(pairs), 2):
        chunk = pairs[i : i + 2]
        cols = st.columns(len(chunk))
        for col, (k, v) in zip(cols, chunk):
            with col:
                key_col, val_col = st.columns([1, 3])
                key_col.write(k)  # Display key as read-only text
                # Provide a non-empty label, then hide it.
                new_val = val_col.text_input(
                    "Metadata Value",
                    value=str(v),
                    key=f"meta_val_{k}_{i}",
                    label_visibility="collapsed",
                )
            new_meta[k] = new_val

    st.write("Add a New Metadata Entry:")

    # Also ensure non-empty labels for these inputs
    create_cols = st.columns([1, 3, 1, 3])
    create_cols[0].write("Key")
    new_k = create_cols[1].text_input(
        "New Key",
        "",
        key="meta_new_key",
        label_visibility="collapsed",
    )
    create_cols[2].write("Value")
    new_v = create_cols[3].text_input(
        "New Value",
        "",
        key="meta_new_value",
        label_visibility="collapsed",
    )

    if new_k:
        new_meta[new_k] = new_v

    st.session_state[node_metadata_key] = new_meta

def display_version_history(metadata: Dict[str, Any]):
    """
    Display a single version at a time, including a table for node metadata.
    To avoid Arrow serialization errors (e.g., mixed object types or booleans),
    we explicitly convert values to strings in DataFrames.
    """
    st.write("### Version History")

    versions = metadata.get("versions", {})
    if not versions:
        st.info("No version history available")
        return

    version_nums = sorted(int(v) for v in versions.keys())
    default_index = max(0, len(version_nums) - 2)  # Show previous version if >1, else latest
    selected_version_num = st.selectbox("Select a version", version_nums, index=default_index)
    version_data = versions[str(selected_version_num)]

    st.subheader(f"Version {version_data.get('version', selected_version_num)}")

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Description", value=version_data.get("description", ""), disabled=True)
        st.text_input("Valid From", value=version_data.get("valid_from", ""), disabled=True)
    with col2:
        st.text_input("Version", value=str(version_data.get("version", "")), disabled=True)
        st.text_input("Valid To", value=str(version_data.get("valid_to", "None")), disabled=True)

    # Display Node Metadata as a table, converting all values to str
    st.subheader("Node Metadata")
    node_metadata = version_data.get("node_metadata", {})
    if node_metadata:
        node_metadata_items = [(k, str(v)) for k, v in node_metadata.items()]
        nm_df = pd.DataFrame(node_metadata_items, columns=["Key", "Value"])
        nm_df.set_index("Key", inplace=True)
        st.table(nm_df)
    else:
        st.info("No node metadata")

    # Fields
    st.subheader("Fields")
    fields = version_data.get("fields", {})
    if fields:
        fields_list = convert_fields_dict_to_list(fields)
        # Convert each field's values to strings so Arrow serialization won't fail
        data_for_display = []
        for f in fields_list:
            row = {}
            for k, v in f.items():
                if k == "validation_mode":
                    # You may skip or handle differently; here we exclude it from display
                    continue
                row[k] = str(v)
            data_for_display.append(row)

        df = pd.DataFrame(data_for_display)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No fields defined")

    # Upgrade Definitions
    upgrade_defs = version_data.get("upgrade_definitions", {})
    if upgrade_defs:
        st.subheader("Upgrade Definitions")
        st.json(upgrade_defs)

def edit_current_metadata(api, selected_type: str, metadata: Dict[str, Any]):
    """
    Display and edit metadata for an existing node, ensuring node_metadata and fields
    are in the proper formats (dict for node_metadata, dict-of-fields for fields)
    before displaying the UI.
    """
    versions = metadata.get("versions", {})
    if not versions:
        st.error("No versions found in metadata")
        return

    version_nums = sorted(int(v) for v in versions.keys())
    current_version_num = max(version_nums)
    current_version = versions[str(current_version_num)]

    # Description
    col1, col2 = st.columns(2)
    with col1:
        current_description = current_version.get("description", "") or "No description available"
        description = st.text_area("Description", value=current_description, height=100, key="metadata_description")
    with col2:
        schema_version_str = str(current_version.get("_schema_version", 1))
        st.text_input("Schema Version", value=schema_version_str, disabled=True, key="schema_version")

    # Node metadata (ensure dict)
    existing_node_metadata = current_version.get("node_metadata", {})
    if not isinstance(existing_node_metadata, dict):
        st.warning("Warning: node_metadata was not stored as a dictionary. Converting automatically.")
        if isinstance(existing_node_metadata, list):
            existing_node_metadata = {f"item_{i}": val for i, val in enumerate(existing_node_metadata)}
        else:
            existing_node_metadata = {}

    display_node_metadata_editor("node_metadata_dict", existing_node_metadata)

    # Fields (ensure dict)
    current_fields_dict = current_version.get("fields", {})
    if isinstance(current_fields_dict, list):
        st.warning("Warning: 'fields' was stored as a list. Converting to a dictionary automatically.")
        new_dict = {}
        for i, field_data in enumerate(current_fields_dict):
            if isinstance(field_data, dict):
                name = field_data.get("name", f"field_{i}")
                new_dict[name] = field_data
            else:
                new_dict[f"field_{i}"] = {"name": f"field_{i}", "value": field_data}
        current_fields_dict = new_dict

    current_fields = convert_fields_dict_to_list(current_fields_dict)

    if "updated_fields" not in st.session_state:
        st.session_state.updated_fields = current_fields

    new_fields = display_field_editor(st.session_state.updated_fields)
    if new_fields != st.session_state.updated_fields:
        st.session_state.updated_fields = new_fields

    meta_changed = {
        k: str(v) for k, v in st.session_state["node_metadata_dict"].items()
    } != {
        k: str(v) for k, v in existing_node_metadata.items()
    }
    fields_changed = (st.session_state.updated_fields != current_fields)
    desc_changed = (description != current_description)

    if meta_changed or fields_changed or desc_changed:
        st.info("You have unsaved changes. Click 'Save Changes' to save them.")

    if st.button("Save Changes", type="primary", key="save_changes"):
        try:
            fields_list = st.session_state.updated_fields
            node_metadata = st.session_state["node_metadata_dict"]
            api.update_metadata(
                selected_type,
                fields=fields_list,  # Pass a list, let the backend convert if needed
                description=description,
                node_metadata=node_metadata
            )
            st.success("Changes saved successfully!")
            del st.session_state.updated_fields
            del st.session_state.node_metadata_dict
            st.rerun()
        except Exception as e:
            st.error(f"Error saving changes: {str(e)}")


def create_new_metadata(api: MetadataAPI, selected_type: str):
    """If no previous metadata exists, create a new one."""
    st.write("## Create New Metadata")
    col1, col2 = st.columns(2)
    with col1:
        description = st.text_area("Description", key="metadata_description", height=100)
        node_metadata_str = st.text_area(
            "Node Metadata (JSON)",
            value="{}",
            height=150,
            key="node_metadata_str"
        )
    with col2:
        st.text_input("Schema Version", value="1", disabled=True, key="schema_version")

    updated_fields = display_field_editor([])

    if st.button("Create Metadata", type="primary", key="create_metadata"):
        try:
            node_metadata_input = node_metadata_str.strip()
            node_metadata = {}
            if node_metadata_input:
                try:
                    node_metadata = json.loads(node_metadata_input)
                except json.JSONDecodeError:
                    st.error("Invalid JSON in Node Metadata. Please correct and try again.")
                    return
                if not isinstance(node_metadata, dict):
                    st.error("Node Metadata must be a JSON object.")
                    return

            api.create_metadata(
                selected_type,
                updated_fields,
                description=description,
                node_metadata=node_metadata,
                _schema_version=1
            )
            st.success("Metadata created successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error creating metadata: {str(e)}")

def main():
    """Main application, now split into two tabs: one for current metadata, one for version history."""
    st.set_page_config(page_title="Metadata Manager", page_icon="🔧", layout="wide")
    st.title("Metadata Manager")

    try:
        api = init_metadata_api()
        selected_type = display_node_type_selector(api)
        if not selected_type:
            return

        metadata = api.get_metadata(selected_type)

        # Reset if node type changed
        if "current_node_type" not in st.session_state:
            st.session_state["current_node_type"] = selected_type
        if st.session_state["current_node_type"] != selected_type:
            st.session_state["current_node_type"] = selected_type
            if "updated_fields" in st.session_state:
                del st.session_state["updated_fields"]
            if "node_metadata_dict" in st.session_state:
                del st.session_state["node_metadata_dict"]

        if metadata:
            ##st.write(f"## Manage Metadata for: {selected_type}")
            tab_current, tab_history = st.tabs(["Current Metadata", "Version History"])

            with tab_current:
                edit_current_metadata(api, selected_type, metadata)

            with tab_history:
                display_version_history(metadata)

        else:
            create_new_metadata(api, selected_type)

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()