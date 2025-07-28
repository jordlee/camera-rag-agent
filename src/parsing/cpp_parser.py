# src/parsing/cpp_parser.py

import os
import json
import subprocess
import xml.etree.ElementTree as ET
import re

# Get the absolute path to the project root (where this script is likely run from)
# Assuming cpp_parser.py is in src/parsing/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# --- Configuration for Doxygen ---
# Base directory where different SDK versions are located
SDK_SOURCE_BASE_DIR = os.path.join(PROJECT_ROOT, "data/raw_sdk_docs/sdk_source")

# Base directories for Doxygen XML output and parsed JSON output
DOXYGEN_BASE_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data/doxygen_xml_output")
PARSED_CPP_BASE_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data/parsed_data/cpp")

# --- Phase 1: Run Doxygen to Generate XML ---
def generate_doxygen_xml(source_dir_for_doxygen_input, output_dir, sdk_version):
    """
    Generates Doxygen XML documentation for the C++ SDK *interface* code (primarily headers).

    Args:
        source_dir_for_doxygen_input (str): The specific CRSDK directory for a given version
                                            (e.g., 'data/raw_sdk_docs/sdk_source/V2.00.00/CRSDK').
        output_dir (str): The directory where Doxygen should output its XML files for this version.
        sdk_version (str): The current SDK version being processed (e.g., "V2.00.00").

    Returns:
        bool: True if Doxygen ran successfully, False otherwise.
    """
    print(f"Generating Doxygen XML for API interfaces for v{sdk_version} from: {source_dir_for_doxygen_input}")
    os.makedirs(output_dir, exist_ok=True)

    # The actual Doxygen 'INPUT' and 'INCLUDE_PATH' should point directly to the CRSDK folder
    # as per the user's clarification.
    
    # Create a Doxyfile dynamically
    doxyfile_content = f"""
    PROJECT_NAME     = "SDK Documentation - {sdk_version}"
    PROJECT_BRIEF    = "Parsed C++ SDK API for RAG - {sdk_version}"
    PROJECT_LOGO     = ""
    OUTPUT_DIRECTORY = "{output_dir}"
    GENERATE_XML     = YES
    GENERATE_HTML    = NO
    GENERATE_LATEX   = NO
    GENERATE_RTF     = NO
    GENERATE_MAN     = NO
    GENERATE_XML     = YES
    XML_OUTPUT       = "xml" # Doxygen will create a 'xml' subfolder in OUTPUT_DIRECTORY

    # Input settings
    # INPUT is set directly to the CRSDK folder for the current version
    INPUT            = "{source_dir_for_doxygen_input}"
    # Only process header files (*.h, *.hpp)
    FILE_PATTERNS    = *.h *.hpp
    RECURSIVE        = YES # Recurse within the CRSDK input directory

    # Explicitly add include paths for resolving types.
    # The source_dir_for_doxygen_input (CRSDK) is the primary include path.
    INCLUDE_PATH     = "{source_dir_for_doxygen_input}"

    # Exclude directories (e.g., OpenCV, build folders, etc.)
    EXCLUDE_PATTERNS = */opencv2/* */build/* */temp/* */test/* */examples/*

    # Extract all details, even private members and static functions
    EXTRACT_ALL      = YES
    EXTRACT_STATIC   = YES
    EXTRACT_PRIVATE  = YES
    EXTRACT_LOCAL_CLASSES = YES
    EXTRACT_LOCAL_METHODS = YES
    SHOW_INCLUDE_FILES = YES
    INLINE_SIMPLE_STRUCTS = YES

    # Preprocessor settings (Doxygen's internal preprocessor)
    ENABLE_PREPROCESSING = YES
    MACRO_EXPANSION = YES
    EXPAND_ONLY_PREDEF = NO
    # --- IMPORTANT: Define SCRSDK_API and TEXT() to empty strings for Doxygen ---
    # This helps Doxygen parse declarations using these macros.
    PREDEFINED = SCRSDK_API= TEXT(x)=x

    # Force Doxygen to parse .h files as C++
    EXTENSION_MAPPING = .h=C++

    # Source code Browse
    SOURCE_BROWSER   = YES
    VERBATIM_HEADERS = NO

    # Warnings and messages - KEEP ON FOR NOW FOR DEBUGGING!
    QUIET            = NO
    WARNINGS         = YES
    WARN_IF_UNDOCUMENTED = NO
    WARN_NO_PARAMDOC = NO
    """
    # Write the Doxyfile dynamically, including the version in its name
    doxyfile_path = os.path.join(PROJECT_ROOT, f"Doxyfile.api.{sdk_version}")
    with open(doxyfile_path, "w", encoding="utf-8") as f:
        f.write(doxyfile_content)

    # Run Doxygen
    try:
        print(f"Running Doxygen for API v{sdk_version}. Output will be in: {output_dir}/xml")
        result = subprocess.run(["doxygen", doxyfile_path], capture_output=True, text=True, check=False)
        
        print(f"Doxygen run complete for API v{sdk_version}.")
        if result.stdout:
            print(f"Doxygen stdout (API v{sdk_version}):\n", result.stdout)
        if result.stderr:
            print(f"Doxygen stderr (API v{sdk_version}):\n", result.stderr)
        
        if result.returncode != 0:
            print(f"Doxygen for API v{sdk_version} finished with non-zero exit code: {result.returncode}. Please review the Doxygen output above for warnings/errors.")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running Doxygen for API v{sdk_version}: {e}")
        print(f"Doxygen stdout:\n{e.stdout}")
        print(f"Doxygen stderr:\n{e.stderr}")
        return False
    except FileNotFoundError:
        print("Error: 'doxygen' command not found. Please ensure Doxygen is installed and in your system's PATH.")
        print("Download from: https://www.doxygen.nl/download.html")
        return False

# --- Phase 2: Parse Doxygen's XML Output ---
def parse_doxygen_xml(xml_dir, current_sdk_source_path, sdk_version):
    """
    Parses the XML files generated by Doxygen and extracts structured C++ API data.

    Args:
        xml_dir (str): The directory containing Doxygen's XML output (e.g., 'data/doxygen_xml_output/V2.00.00/xml').
        current_sdk_source_path (str): The absolute path to the CRSDK folder for the current version.
        sdk_version (str): The current SDK version being processed.

    Returns:
        list: A list of dictionaries, each representing a parsed C++ file's content.
    """
    print(f"Parsing Doxygen XML for API v{sdk_version} from: {xml_dir}")
    parsed_compounds_data = []

    index_file = os.path.join(xml_dir, "index.xml")
    if not os.path.exists(index_file):
        print(f"Error: Doxygen index.xml not found at {index_file}. Doxygen might not have run correctly or generated XML.")
        return []

    try:
        tree = ET.parse(index_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"ERROR: Could not parse index.xml: {e}")
        return []

    # Normalize the current SDK source path for efficient comparison
    normalized_sdk_source_path = os.path.normpath(current_sdk_source_path)
    print(f"DEBUG_PATH: Normalized SDK source path for comparison: {normalized_sdk_source_path}")


    # Iterate through all 'compound' elements (files, classes, namespaces, etc.) listed in index.xml
    for compound in root.findall(".//compound"):
        refid = compound.get("refid")
        kind = compound.get("kind")
        name = compound.find("name").text if compound.find("name") is not None else "Unknown"

        detail_xml_file = os.path.join(xml_dir, f"{refid}.xml")
        if not os.path.exists(detail_xml_file):
            print(f"WARNING_PARSE: Detail XML file '{detail_xml_file}' not found for {name} (kind: {kind}). Skipping.")
            continue

        try:
            detail_tree = ET.parse(detail_xml_file)
            detail_root = detail_tree.getroot()
        except ET.ParseError as e:
            print(f"ERROR: Could not parse {detail_xml_file}: {e}. Skipping.")
            continue

        compound_def = detail_root.find(".//compounddef")
        if compound_def is None:
            print(f"WARNING_PARSE: No <compounddef> found in '{detail_xml_file}' for {name} (kind: {kind}). Skipping.")
            continue

        # Extract the original file path from the Doxygen XML's <location> tag
        location_tag = compound_def.find("location")
        original_filepath = location_tag.get("file") if location_tag is not None else ""

        # Make original_filepath absolute before normalization for robust comparison
        # If Doxygen outputs paths relative to the current working directory where doxygen was run,
        # os.path.abspath will resolve it correctly.
        abs_original_filepath = os.path.abspath(original_filepath) if original_filepath else ""
        normalized_original_filepath = os.path.normpath(abs_original_filepath) if abs_original_filepath else ""
        
        print(f"\nDEBUG_PATH_COMPARE: Compound Name: '{name}', Kind: '{kind}'")
        print(f"DEBUG_PATH_COMPARE: Original Filepath from Doxygen (raw): '{original_filepath}'")
        print(f"DEBUG_PATH_COMPARE: Absolute Normalized Original Filepath: '{normalized_original_filepath}'")
        print(f"DEBUG_PATH_COMPARE: Normalized SDK Source Path (CRSDK): '{normalized_sdk_source_path}'")


        # Determine if this compound originates from a header within the CRSDK directory
        # This logic is crucial: it ensures we only parse headers and API definitions
        # that are actually part of your SDK source, not external headers like OpenCV.
        # The original_filepath from Doxygen is usually already relative to the Doxygen INPUT.
        # So we just need to check if it's within the current_sdk_source_path (CRSDK).
        is_sdk_relevant_file = (
            normalized_original_filepath.startswith(normalized_sdk_source_path) and
            (normalized_original_filepath.endswith((".h", ".hpp")) or kind != 'file') # Include all non-file types (classes, enums etc.) if they originate from SDK path
        )
        # For 'file' compounds, we specifically want headers within the CRSDK.
        if kind == 'file' and not normalized_original_filepath.endswith((".h", ".hpp")):
            is_sdk_relevant_file = False

        should_parse_compound = False

        # Parse specific kinds if they are within the SDK source path
        if is_sdk_relevant_file and kind in ['class', 'struct', 'union', 'namespace', 'enum', 'file']:
             should_parse_compound = True
             print(f"DEBUG_PARSE: Processing compound: refid='{refid}', kind='{kind}', name='{name}' (from {os.path.basename(original_filepath)})")
        else:
            print(f"DEBUG_PARSE: Skipping compound of kind '{kind}': '{name}' ({original_filepath}) - Not an SDK-relevant file or type.")


        if should_parse_compound:
            # Common parsing logic for all included compounds
            parsed_data = {
                "refid": refid,
                "kind": kind,
                "name": name,
                "source_file": original_filepath,
                "brief_description": "",
                "detailed_description": "",
                "members": [], # Functions, variables, enums, typedefs
                "inner_compounds": [] # Nested classes, structs, enums
            }

            # Extract brief and detailed descriptions
            brief_description_tag = compound_def.find(".//briefdescription")
            if brief_description_tag is not None:
                parsed_data["brief_description"] = "".join(brief_description_tag.itertext()).strip()

            detailed_description_tag = compound_def.find(".//detaileddescription")
            if detailed_description_tag is not None:
                parsed_data["detailed_description"] = "".join(detailed_description_tag.itertext()).strip()

            # Process sections (public, private, protected members)
            for sectiondef in compound_def.findall(".//sectiondef"):
                kind_section = sectiondef.get("kind")
                for memberdef in sectiondef.findall(".//memberdef"):
                    member_kind = memberdef.get("kind") # e.g., 'function', 'variable', 'enum', 'typedef'
                    member_id = memberdef.get("id")
                    member_name = memberdef.find("name").text if memberdef.find("name") is not None else "Unknown"
                    
                    member_data = {
                        "id": member_id,
                        "kind": member_kind,
                        "name": member_name,
                        "visibility": kind_section, # public-func, private-var, etc.
                        "type": "",
                        "definition": "",
                        "argsstring": "",
                        "brief_description": "",
                        "detailed_description": "",
                        "location": memberdef.find("location").get("file") if memberdef.find("location") is not None else "",
                        "params": [] # For functions
                    }

                    # Extract type, definition, and arguments
                    type_tag = memberdef.find("type")
                    if type_tag is not None and type_tag.text is not None:
                        member_data["type"] = "".join(type_tag.itertext()).strip()

                    definition_tag = memberdef.find("definition")
                    if definition_tag is not None and definition_tag.text is not None:
                        member_data["definition"] = definition_tag.text.strip()

                    argsstring_tag = memberdef.find("argsstring")
                    if argsstring_tag is not None and argsstring_tag.text is not None:
                        member_data["argsstring"] = argsstring_tag.text.strip()
                    else:
                        member_data["argsstring"] = ""

                    # Extract member brief and detailed descriptions
                    member_brief_tag = memberdef.find("briefdescription")
                    if member_brief_tag is not None:
                        member_data["brief_description"] = "".join(member_brief_tag.itertext()).strip()

                    member_detailed_tag = memberdef.find("detaileddescription")
                    if member_detailed_tag is not None:
                        member_data["detailed_description"] = "".join(member_detailed_tag.itertext()).strip()

                    # Extract parameters for functions
                    if member_kind == 'function':
                        for param in memberdef.findall(".//param"):
                            param_type_tag = param.find("type")
                            param_type = "".join(param_type_tag.itertext()).strip() if param_type_tag is not None and param_type_tag.text is not None else ""
                            
                            param_declname_tag = param.find("declname")
                            param_name = param_declname_tag.text if param_declname_tag is not None else ""
                            
                            param_defname_tag = param.find("defname")
                            param_desc = "".join(param_defname_tag.itertext()).strip() if param_defname_tag is not None and param_defname_tag.text is not None else ""
                            
                            member_data["params"].append({"type": param_type, "name": param_name, "description": param_desc})
                    
                    # Extract enum values if member_kind is 'enum'
                    if member_kind == 'enum':
                        enum_values = []
                        for enumvalue_tag in memberdef.findall(".//enumvalue"):
                            enum_value_name = enumvalue_tag.find("name").text if enumvalue_tag.find("name") is not None else "UnknownEnumValue"
                            enum_value_id = enumvalue_tag.get("id")
                            
                            enum_value_initializer_tag = enumvalue_tag.find("initializer")
                            enum_value_initializer = "".join(enum_value_initializer_tag.itertext()).strip() if enum_value_initializer_tag is not None else ""
                            
                            enum_value_brief_tag = enumvalue_tag.find("briefdescription")
                            enum_value_brief = "".join(enum_value_brief_tag.itertext()).strip() if enum_value_brief_tag is not None else ""

                            enum_values.append({
                                "enum_value_id": enum_value_id,
                                "name": enum_value_name,
                                "initializer": enum_value_initializer,
                                "brief_description": enum_value_brief
                            })
                        member_data["enum_values"] = enum_values # Add a new key to store these

                    parsed_data["members"].append(member_data)
            
            # Process inner compounds (nested classes/structs/enums)
            for innerclass in compound_def.findall(".//innerclass"):
                inner_compound_refid = innerclass.get("refid")
                inner_compound_prot = innerclass.get("prot")
                # We can choose to load more details for inner compounds later if needed,
                # for now, just store their reference.
                parsed_data["inner_compounds"].append({
                    "refid": inner_compound_refid,
                    "prot": inner_compound_prot # public, protected, private
                })

            parsed_compounds_data.append(parsed_data)
            print(f"  Extracted API data for Doxygen compound '{kind}': '{name}' (from {os.path.basename(original_filepath)})")
        # else: The compound was skipped by the filtering logic, message already printed above.

    return parsed_compounds_data

# --- Phase 3: Save Parsed Data to JSON ---
def save_parsed_cpp_data(parsed_data_list, output_dir, sdk_version):
    """
    Saves the list of parsed C++ data dictionaries into individual JSON files.

    Args:
        parsed_data_list (list): A list of dictionaries, each representing a parsed C++ compound.
        output_dir (str): The directory where JSON files should be saved.
        sdk_version (str): The current SDK version, used for naming output files.
    """
    print(f"\n--- Saving Parsed C++ Data for {len(parsed_data_list)} Doxygen compounds for v{sdk_version} ---")
    os.makedirs(output_dir, exist_ok=True)

    for data in parsed_data_list:
        # Create a clean filename from the compound name and kind, including version
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', data['name'])
        # Replace '.' in version with '_' for filename safety
        version_tag = sdk_version.replace('.', '_')
        filename = f"{clean_name}_{data['kind']}_v{version_tag}_parsed.json"
        filepath = os.path.join(output_dir, filename)

        # --- MODIFICATION START ---
        # Add the metadata object with the compound's name as the title and the SDK version.
        data["metadata"] = {
            "title": data["name"],
            "sdk_version": sdk_version
        }
        # --- MODIFICATION END ---
        
        # print(f"DEBUG_SAVE: Attempting to save: '{filepath}' (Kind: '{data['kind']}', Name: '{data['name']}', Version: '{sdk_version}')")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            print(f"  Saved: {filepath}")
        except Exception as e:
            print(f"ERROR_SAVE: Failed to save '{filepath}': {e}")

# --- Main Execution ---
if __name__ == "__main__":
    # Define the SDK versions to process
    sdk_versions_to_parse = ["V1.14.00", "V2.00.00"] # Use exact folder names as provided

    for version in sdk_versions_to_parse:
        print(f"\n--- Processing SDK API Version: {version} ---")

        # Dynamically set version-specific paths
        # Source directory for Doxygen INPUT should be the CRSDK folder
        current_sdk_source_for_doxygen_input = os.path.join(SDK_SOURCE_BASE_DIR, version, "CRSDK")
        current_doxygen_output_dir = os.path.join(DOXYGEN_BASE_OUTPUT_DIR, version)
        current_parsed_cpp_output_dir = os.path.join(PARSED_CPP_BASE_OUTPUT_DIR, version)

        os.makedirs(current_parsed_cpp_output_dir, exist_ok=True) # Ensure versioned output directory exists

        if not os.path.exists(current_sdk_source_for_doxygen_input):
            print(f"Error: SDK source directory for API '{current_sdk_source_for_doxygen_input}' for version {version} not found. Skipping this version.")
            continue # Skip to the next version

        print(f"--- Running Doxygen to generate XML for v{version} ---")
        doxygen_success = generate_doxygen_xml(
            current_sdk_source_for_doxygen_input,
            current_doxygen_output_dir,
            version # Pass the current SDK version
        )

        if doxygen_success:
            print(f"\n--- Parsing Doxygen XML for v{version} ---")
            # Doxygen puts XML files in a 'xml' subfolder within the DOXYGEN_OUTPUT_DIR
            parsed_api_data = parse_doxygen_xml(
                os.path.join(current_doxygen_output_dir, "xml"),
                current_sdk_source_for_doxygen_input, # Pass the CRSDK path for filtering
                version
            )
            
            if parsed_api_data:
                save_parsed_cpp_data(parsed_api_data, current_parsed_cpp_output_dir, version)
                print(f"\nSuccessfully parsed and saved {len(parsed_api_data)} C++ API compounds for version {version}.")
            else:
                print(f"No C++ API data was parsed for version {version}.")
        else:
            print(f"Doxygen XML generation failed for version {version}. Skipping parsing.")

    print("\nAll specified SDK API versions processed.")