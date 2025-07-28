import os
import json
import subprocess
import xml.etree.ElementTree as ET
import re

# --- Configuration for Example Code Parsing ---
# It's good practice to define paths relative to the script's location
# Get the absolute path to the project root (where this script is likely run from)
# Assuming example_parser.py is in src/parsing/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# These base directories remain, but the actual paths used in the loop will be version-specific.
SDK_EXAMPLES_BASE_SOURCE_DIR = os.path.join(PROJECT_ROOT, "data/raw_sdk_docs/sdk_source")
DOXYGEN_EXAMPLES_BASE_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data/doxygen_examples_xml_output") # Separate Doxygen output for examples
PARSED_EXAMPLES_BASE_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data/parsed_data/examples") # Where our Python script will save example JSONs


# --- Helper Function: Extract code from programlisting tag ---
def _extract_code_from_programlisting_tag(programlisting_tag):
    """
    Extracts the full code text from a <programlisting> XML tag,
    handling nested <highlight> tags and Doxygen's formatting.
    """
    if programlisting_tag is None:
        return ""
    extracted_code = ''.join(programlisting_tag.itertext()).strip()

    # Doxygen uses &#160; for non-breaking space, convert to regular space
    extracted_code = re.sub(r'&#160;', ' ', extracted_code)
    # Remove leading asterisks from multi-line comments that Doxygen might include
    extracted_code = re.sub(r'^\s*\*\s*', '', extracted_code, flags=re.MULTILINE)
    return extracted_code

# --- Helper Function: Extract code from original file ---
def _extract_code_from_file(filepath, start_line_hint, definition_string=None, bodystart=None, bodyend=None):
    """
    Reads specific lines from a file using bodystart/bodyend if available,
    otherwise falls back to definition string and brace matching.
    """
    # Debug prints removed for brevity in final version, but keep if troubleshooting
    # print(f" _extract_code_from_file: Attempting to extract from: {filepath}")
    # print(f" _extract_code_from_file: Doxygen hint line: {start_line_hint}, Definition: '{definition_string}'")
    # print(f" _extract_code_from_file: Doxygen body lines: bodystart={bodystart}, bodyend={bodyend}")

    if not os.path.exists(filepath):
        print(f" ERROR: Source file NOT FOUND at expected path: {filepath}")
        return ""

    all_lines = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
            # print(f" _extract_code_from_file: Successfully read {len(all_lines)} lines from {filepath}")
    except Exception as e:
        print(f" ERROR: Could not read file {filepath}: {e}")
        return ""

    if bodystart is not None and bodyend is not None and bodystart > 0 and bodyend > 0:
        # Use direct bodystart/bodyend lines from Doxygen XML
        # Adjust for 0-based indexing (Python lists)
        start_idx_python = bodystart - 1
        end_idx_python = bodyend # This line is inclusive in Doxygen, so exclusive in Python slice
        # print(f" _extract_code_from_file: Calculated Python slice indices: {start_idx_python}:{end_idx_python}")

        if 0 <= start_idx_python < end_idx_python <= len(all_lines):
            # print(f" _extract_code_from_file: Executing direct slice extraction.")
            extracted_segment = "".join(all_lines[start_idx_python:end_idx_python]).strip()
            # print(f" _extract_code_from_file: Direct slice extraction successful. Length: {len(extracted_segment)} chars.")
            return extracted_segment
        else:
            print(f" WARNING: Bodystart/bodyend ({bodystart}-{bodyend}) translated to Python slice ({start_idx_python}:{end_idx_python}) is OUT OF BOUNDS or invalid for file with {len(all_lines)} lines in {os.path.basename(filepath)}. Falling back to signature search.")


    # Fallback to definition string and brace matching if bodystart/bodyend failed or not provided
    # print(f" _extract_code_from_file: Falling back to signature search and brace matching for {os.path.basename(filepath)}.")
    actual_start_idx = -1

    if definition_string:
        # Improved regex to handle qualified names (e.g., Class::method, namespace::function)
        # It looks for the last word or the last `::` separated part followed by `(`
        # Example: "std::vector<std::uint16_t> cli::parse_f_number" -> "cli::parse_f_number"
        # Example: "MyClass::MyMethod" -> "MyClass::MyMethod"
        match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*(?:::[a-zA-Z_][a-zA-Z0-9_]*)*)\s*\(', definition_string)
        if match:
            search_pattern = re.escape(match.group(1)) + r'\s*\('
        else:
            # Fallback if no specific pattern is found, just search for the last word + (
            method_name_simple = definition_string.split()[-1]
            search_pattern = re.escape(method_name_simple) + r'\s*\('

        search_start_line_num = max(1, start_line_hint - 200) # For logging, 1-based
        search_end_line_num = min(len(all_lines), start_line_hint + 1000) # For logging, 1-based
        # print(f" _extract_code_from_file: Fallback: Searching for pattern '{search_pattern}' from line {search_start_line_num} to {search_end_line_num} (1-based).")

        found_definition_line = False
        for i in range(search_start_line_num - 1, search_end_line_num): # Adjust for 0-based iteration
            line = all_lines[i]
            if re.search(search_pattern, line):
                actual_start_idx = i # This is 0-based
                found_definition_line = True
                # print(f" _extract_code_from_file: Fallback: Found signature at line {actual_start_idx + 1} (0-based: {actual_start_idx}).")
                break
        if not found_definition_line:
            print(f" WARNING_CODE_EXTRACT: Fallback: Could not find signature '{search_pattern}' in {os.path.basename(filepath)} near line {start_line_hint}. Using hint as start.")
            actual_start_idx = start_line_hint - 1 # Fallback to original line hint if signature not found
    else:
        # print(f" DEBUG: No definition string provided for fallback. Using start_line_hint directly.")
        actual_start_idx = start_line_hint - 1 # No definition string, use hint directly

    if actual_start_idx < 0 or actual_start_idx >= len(all_lines):
        print(f" WARNING_CODE_EXTRACT: Fallback: Calculated start line {actual_start_idx + 1} out of bounds for {os.path.basename(filepath)}. Start hint: {start_line_hint}")
        return ""

    brace_count = 0
    in_function_body = False
    lines_collected = []
    # print(f" _extract_code_from_file: Fallback: Starting brace matching from line {actual_start_idx + 1}.")

    for i in range(actual_start_idx, len(all_lines)):
        line = all_lines[i]
        lines_collected.append(line) # Add the current line to the snippet
        if not in_function_body:
            if '{' in line:
                in_function_body = True
                brace_count += line.count('{') - line.count('}')
                # If the opening brace is on the same line as the closing brace (e.g., `void func() {}`)
                if brace_count == 0 and '}' in line:
                    # print(f" _extract_code_from_file: Fallback: Found single-line body at {i+1}. Stopping.")
                    break
        else:
            brace_count += line.count('{')
            brace_count -= line.count('}')
            # print(f" _extract_code_from_file: Fallback: Processing line {i+1}. Current brace count: {brace_count}")
            if brace_count == 0:
                # print(f" _extract_code_from_file: Fallback: Found matching closing brace at line {i+1}. Stopping.")
                break
    extracted_fallback_code = "".join(lines_collected).strip()
    # print(f" _extract_code_from_file: Fallback extraction complete. Length: {len(extracted_fallback_code)} chars for {os.path.basename(filepath)}.")
    return extracted_fallback_code

# --- Helper Function: Get all relevant source files ---
def _get_all_source_files(base_dir, exclude_dirs=None, file_extensions=None):
    """
    Recursively finds all files with specified extensions in base_dir,
    excluding specified subdirectories. Returns paths relative to base_dir.
    """
    if exclude_dirs is None:
        exclude_dirs = []
    if file_extensions is None:
        file_extensions = ['.cpp', '.h', '.cc'] # Common C++ extensions

    found_files = []
    for root, dirs, files in os.walk(base_dir):
        # Modify dirs in-place to prune directories we don't want to recurse into
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if any(file.endswith(ext) for ext in file_extensions):
                # Ensure the path is relative to the SDK_EXAMPLE_SOURCE_DIR
                relative_path = os.path.relpath(os.path.join(root, file), base_dir)
                found_files.append(relative_path)
    return found_files

# --- Phase 1: Run Doxygen for Example Files ---
def generate_doxygen_xml_for_examples(source_dir, output_dir, target_files, sdk_version): # Added sdk_version
    """
    Generates Doxygen XML documentation for specific example C++ files and their
    corresponding header files, including full program listings.
    """
    print(f"--- Running Doxygen to generate XML for Examples v{sdk_version} ---") # Added sdk_version
    print(f"Generating Doxygen XML for examples from: {source_dir}")
    os.makedirs(output_dir, exist_ok=True)

    # Doxygen input files will now include both .cpp and relevant .h files
    # from the target_files list.
    doxygen_input_files_absolute = []
    for f_relative in target_files:
        f_abs = os.path.join(source_dir, f_relative)
        if os.path.exists(f_abs):
            doxygen_input_files_absolute.append(f_abs)
        # Also add corresponding header if it exists and is in the same directory
        if f_relative.endswith(".cpp"):
            header_relative = f_relative.replace(".cpp", ".h")
            header_abs = os.path.join(source_dir, header_relative)
            if os.path.exists(header_abs):
                doxygen_input_files_absolute.append(header_abs)
            else:
                print(f" WARNING: Corresponding header for {f_relative} not found at {header_abs}") # Added warning
        else:
            print(f" WARNING: Target file specified for Doxygen not found: {f_abs}")

    input_str = " ".join(f'"{p}"' for p in doxygen_input_files_absolute)

    doxyfile_content = f"""
    PROJECT_NAME = "SDK Examples Documentation v{sdk_version}" # Added sdk_version
    PROJECT_BRIEF = "Parsed C++ SDK Examples for RAG v{sdk_version}" # Added sdk_version
    OUTPUT_DIRECTORY = "{output_dir}"
    GENERATE_XML = YES
    GENERATE_HTML = NO
    XML_OUTPUT = "xml"

    # Input files and directories - now includes all identified .cpp and relevant .h files
    INPUT = {input_str}
    FILE_PATTERNS = *.cpp *.cc *.h
    RECURSIVE = NO # We specify exact files, so no recursion needed for input

    # Include paths for resolving types (crucial for finding included headers within files)
    INCLUDE_PATH = "{source_dir}" "{os.path.join(source_dir, 'CRSDK')}"

    # Extraction settings to get as much detail as possible
    EXTRACT_ALL = YES
    EXTRACT_STATIC = YES
    EXTRACT_PRIVATE = YES
    EXTRACT_LOCAL_CLASSES = YES # Ensure local classes are extracted
    EXTRACT_LOCAL_METHODS = YES # Ensure local methods are extracted
    SHOW_INCLUDE_FILES = YES
    INLINE_SIMPLE_STRUCTS = YES

    # Preprocessing for macros and typedefs
    ENABLE_PREPROCESSING = YES
    MACRO_EXPANSION = YES
    EXPAND_ONLY_PREDEF = NO
    PREDEFINED = SCRSDK_API= TEXT(x)=x # Example: define common SDK macros

    # Force parsing of all entities
    ALPHABETICAL_INDEX = YES
    CASE_SENSE_NAMES = NO

    # Enable program listings in XML for code extraction
    XML_PROGRAMLISTING = YES

    # Suppress some warnings for cleaner output during generation
    QUIET = NO
    WARNINGS = YES
    WARN_IF_UNDOCUMENTED = NO
    WARN_NO_PARAMDOC = NO

    INTERNAL_DOCS = YES
    AUTOLINK_SUPPORT = YES

    # Ensure Doxygen processes inherited members, crucial for callbacks
    INHERIT_DOCS = YES
    """
    doxyfile_path = os.path.join(PROJECT_ROOT, f"Doxyfile.examples.{sdk_version}") # Doxyfile name includes version
    with open(doxyfile_path, "w", encoding="utf-8") as f:
        f.write(doxyfile_content)

    try:
        print(f"Running Doxygen for examples v{sdk_version}. Output will be in: {output_dir}/xml") # Added sdk_version
        result = subprocess.run(["doxygen", doxyfile_path], capture_output=True, text=True, check=False)
        print(f"Doxygen run complete for examples v{sdk_version}.") # Added sdk_version
        if result.stdout:
            print(f"Doxygen stdout (examples v{sdk_version}):\n", result.stdout) # Added sdk_version
        if result.stderr:
            print(f"Doxygen stderr (examples v{sdk_version}):\n", result.stderr) # Added sdk_version
        if result.returncode != 0:
            print(f"Doxygen for examples v{sdk_version} finished with non-zero exit code: {result.returncode}. Check output for warnings/errors.") # Added sdk_version
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running Doxygen for examples v{sdk_version}: {e}") # Added sdk_version
        print(f"Doxygen stdout:\n{e.stdout}")
        print(f"Doxygen stderr:\n{e.stderr}")
        return False
    except FileNotFoundError:
        print("Error: 'doxygen' command not found. Please ensure Doxygen is installed and in your system's PATH.")
        print("Download from: https://www.doxygen.nl/download.html")
        return False

# --- Phase 2: Parse Doxygen's XML Output for Examples ---
def parse_example_xml(xml_dir, source_root_dir, target_files_relative):
    """
    Parses the Doxygen XML output for example files and extracts code snippets.
    It now handles inner classes and namespaces where actual functions might be defined.
    """
    print(f"\n--- Parsing Doxygen XML for Examples from: {xml_dir} ---") # Modified print
    parsed_examples_data = []

    index_file = os.path.join(xml_dir, "index.xml")
    if not os.path.exists(index_file):
        print(f"ERROR: Doxygen index.xml not found at {index_file}. Doxygen might not have run correctly or generated XML.")
        return []

    try:
        tree = ET.parse(index_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"ERROR: Could not parse index.xml: {e}")
        return []

    # Store found class refids and namespace refids to process them after files
    class_compounds_to_process = {}
    namespace_compounds_to_process = {}

    for compound in root.findall(".//compound"):
        refid = compound.get("refid")
        kind = compound.get("kind")
        name = compound.find("name").text if compound.find("name") is not None else "Unknown"
        # Normalize name for comparison with target_files_relative (which are relative paths)
        # For file compounds, Doxygen's name is just the basename (e.g., "CameraDevice.cpp")
        # For our target_files_relative, it's also relative to SDK_EXAMPLE_SOURCE_DIR
        # Check if the compound name (for file kind) matches any of our target files' basenames
        # This prevents picking up files from CRSDK or other non-targeted locations
        compound_basename = os.path.basename(name)
        if kind == "file" and compound_basename in {os.path.basename(f) for f in target_files_relative}:
            print(f" INFO: Found target example file compound: name='{name}' (refid='{refid}')")
            process_compound_file(os.path.join(xml_dir, f"{refid}.xml"), name, refid, xml_dir, source_root_dir, parsed_examples_data) # Path directly formed
        
        elif kind == "class":
            # Doxygen's index.xml for a class may not point to its .cpp directly, but its .h
            # The actual implementation file is determined inside process_compound_class
            # We collect all class compounds and process them later.
            print(f" INFO: Found class compound: name='{name}' (refid='{refid}')")
            class_compounds_to_process[name] = refid # Store for later detailed processing
        elif kind == "namespace":
            # We collect all namespace compounds to process later.
            # The filtering to ensure members come from target .cpp files happens within
            # process_compound_namespace.
            print(f" INFO: Found namespace compound: name='{name}' (refid='{refid}')")
            namespace_compounds_to_process[name] = refid


    # Now, process the identified class files
    for class_name, refid in class_compounds_to_process.items():
        process_compound_class(os.path.join(xml_dir, f"{refid}.xml"), class_name, refid, xml_dir, source_root_dir, target_files_relative, parsed_examples_data) # Path directly formed

    # Process identified namespace files
    for namespace_name, refid in namespace_compounds_to_process.items():
        process_compound_namespace(os.path.join(xml_dir, f"{refid}.xml"), namespace_name, refid, xml_dir, source_root_dir, target_files_relative, parsed_examples_data) # Path directly formed


    print(f"DEBUG_EXAMPLE_PARSE: Final parsed_examples_data contains {len(parsed_examples_data)} items.")
    return parsed_examples_data

def process_compound_file(detail_xml_file, name, refid, xml_dir, source_root_dir, parsed_examples_data):
    """
    Processes a Doxygen XML file representing a top-level source file (.cpp).
    Extracts global functions and other elements directly defined within it.
    """
    if not os.path.exists(detail_xml_file):
        print(f"WARNING: Detail XML file {detail_xml_file} not found for {name}. Skipping.")
        return

    try:
        detail_tree = ET.parse(detail_xml_file)
        detail_root = detail_tree.getroot()
    except ET.ParseError as e:
        print(f"ERROR: Could not parse detail XML {detail_xml_file}: {e}")
        return

    file_compound_def = detail_root.find(f".//compounddef[@id='{refid}']")
    if file_compound_def is None:
        file_compound_def = detail_root.find(".//compounddef")

    if file_compound_def is None:
        print(f"WARNING: No main <compounddef> found in {detail_xml_file} for {name}. Skipping.")
        return

    location_tag = file_compound_def.find("location")
    original_filepath_doxygen_relative = location_tag.get("file") if location_tag is not None else name
    # Construct the absolute path by joining with the PROJECT_ROOT
    original_filepath_abs = os.path.normpath(os.path.join(PROJECT_ROOT, original_filepath_doxygen_relative))
    print(f" INFO: Processing file: {name}. Inferred absolute path: {original_filepath_abs}")
    file_examples = {
        "filepath": original_filepath_doxygen_relative,
        "name": name,
        "kind": "example_file",
        "functions": [],
        "other_snippets": []
    }

    # Iterate over all memberdefs found within this file compound
    for member_def in file_compound_def.findall(".//memberdef"):
        member_kind = member_def.get("kind")
        member_name = member_def.findtext("name", default="").strip()
        member_definition = member_def.findtext("definition", default="").strip()
        member_brief = member_def.findtext("briefdescription/para", default="").strip()
        member_detailed = member_def.findtext("detaileddescription/para", default="").strip()

        member_location = member_def.find("location")
        member_start_line = int(member_location.get("line")) if member_location is not None and member_location.get("line") else 0
        member_bodystart = int(member_location.get("bodystart")) if member_location is not None and member_location.get("bodystart") else None
        member_bodyend = int(member_location.get("bodyend")) if member_location is not None and member_location.get("bodyend") else None

        # Filter to only include members that are actually defined in this specific file's .cpp body
        # Doxygen's file compound can list members whose primary definition XML is elsewhere (e.g., in a class XML)
        # We want to make sure we're extracting from the correct source file.
        member_bodyfile = member_location.get("bodyfile") if member_location is not None else ""
        if not member_bodyfile.endswith(original_filepath_doxygen_relative) and \
           not member_bodyfile.endswith(original_filepath_doxygen_relative.replace(".cpp", ".h")): # Check for corresponding header for definitions
            # print(f" DEBUG: Skipping member {member_name} ({member_kind}) from {original_filepath_doxygen_relative} because its body is in {member_bodyfile}.")
            continue # Skip if the member's body is not in this file (or its paired .h)

        extracted_code = ""
        # Only extract functions/defines/members with bodies from the .cpp file.
        # Functions belonging to namespaces/classes will be handled by their respective processors.
        # The '::' in definition check is a heuristic to avoid global functions if they're actually
        # namespace-scoped and are already handled. However, for file-level functions, this might
        # be valid (e.g., utility functions not in a specific namespace/class).
        # We prioritize bodystart/bodyend, which usually means it's an implementation.
        if (member_kind == "function" or member_kind == "define" or
            (member_bodystart is not None and member_bodyend is not None)):

            programlisting_tag = member_def.find(".//programlisting")
            extracted_code = _extract_code_from_programlisting_tag(programlisting_tag)
            if not extracted_code:
                extracted_code = _extract_code_from_file(original_filepath_abs, member_start_line,
                                                        member_definition, member_bodystart, member_bodyend)
            if extracted_code:
                file_examples["functions"].append({
                    "name": member_name,
                    "kind": member_kind,
                    "code": extracted_code,
                    "brief_comment": member_brief,
                    "detailed_comment": member_detailed,
                    "start_line": member_start_line,
                    "definition": member_definition,
                    "source_file": original_filepath_doxygen_relative
                })
        elif member_kind in ["enum", "variable", "typedef", "struct", "union", "property"]:
            snippet_code = ""
            programlisting_tag = member_def.find(".//programlisting")
            if programlisting_tag is not None:
                snippet_code = _extract_code_from_programlisting_tag(programlisting_tag)
            if not snippet_code and member_start_line > 0:
                snippet_code = _extract_code_from_file(original_filepath_abs, member_start_line,
                                                    member_definition, member_bodystart, member_bodyend)
            if snippet_code:
                file_examples["other_snippets"].append({
                    "name": member_name,
                    "kind": member_kind,
                    "code": snippet_code,
                    "brief_comment": member_brief,
                    "detailed_comment": member_detailed,
                    "start_line": member_start_line,
                    "definition": member_definition,
                    "source_file": original_filepath_doxygen_relative
                })

    if file_examples["functions"] or file_examples["other_snippets"]:
        parsed_examples_data.append(file_examples)
        print(f" INFO: Extracted {len(file_examples['functions'])} funcs and {len(file_examples['other_snippets'])} snippets from file: {name}")


def process_compound_class(detail_xml_file, class_name, refid, xml_dir, source_root_dir, target_files_relative, parsed_examples_data):
    """
    Processes a Doxygen XML file representing a class.
    Extracts methods and other members of the class, prioritizing their .cpp implementation.
    """
    if not os.path.exists(detail_xml_file):
        print(f"WARNING: Detail XML file {detail_xml_file} not found for class {class_name}. Skipping.")
        return

    try:
        detail_tree = ET.parse(detail_xml_file)
        detail_root = detail_tree.getroot()
    except ET.ParseError as e:
        print(f"ERROR: Could not parse detail XML {detail_xml_file}: {e}")
        return

    class_compound_def = detail_root.find(f".//compounddef[@id='{refid}']")
    if class_compound_def is None:
        print(f"WARNING: No main <compounddef> found in {detail_xml_file} for class {class_name}. Skipping.")
        return

    # Determine the absolute path to the .cpp file where methods are implemented
    # Doxygen's location tag in the class XML points to the header where the class is declared.
    # We infer the .cpp from that.
    header_location_tag = class_compound_def.find("location")
    header_filepath_doxygen_relative = header_location_tag.get("file") if header_location_tag is not None else ""
    # Infer the .cpp implementation file path (assuming same directory, .cpp extension)
    inferred_cpp_relative_path = header_filepath_doxygen_relative.replace(".h", ".cpp")
    impl_filepath_abs = os.path.normpath(os.path.join(PROJECT_ROOT, inferred_cpp_relative_path))
    impl_filepath_doxygen_relative = inferred_cpp_relative_path # Keep for JSON output
    if not os.path.exists(impl_filepath_abs):
        # This is often okay, as methods might be defined inline in header or in a different .cpp.
        # But for extracting examples from specific .cpp files, we need to know where to look.
        # This warning is less critical now as _extract_code_from_file handles file not found gracefully.
        pass # print(f" WARNING: Inferred implementation file {impl_filepath_abs} DOES NOT EXIST for class {class_name}.")


    class_examples = {
        "filepath": impl_filepath_doxygen_relative, # This will be the inferred .cpp path
        "name": class_name,
        "kind": "class",
        "functions": [],
        "other_snippets": []
    }
    # Pre-process target_files_relative into a set of basenames for faster lookup
    target_basenames = {os.path.basename(f) for f in target_files_relative}

    for member_def in class_compound_def.findall(".//memberdef"):
        member_kind = member_def.get("kind")
        member_name = member_def.findtext("name", default="").strip()
        member_definition = member_def.findtext("definition", default="").strip()
        member_brief = member_def.findtext("briefdescription/para", default="").strip()
        member_detailed = member_def.findtext("detaileddescription/para", default="").strip()

        member_location = member_def.find("location")
        if member_location is None:
            continue # Skip if no location information

        member_start_line = int(member_location.get("line")) if member_location.get("line") else 0
        member_bodystart = int(member_location.get("bodystart")) if member_location.get("bodystart") else None
        member_bodyend = int(member_location.get("bodyend")) if member_location.get("bodyend") else None
        member_bodyfile_doxygen_relative = member_location.get("bodyfile")
        if member_bodyfile_doxygen_relative is None:
            continue

        # Crucial check: ensure this member's body is in one of our target .cpp files
        bodyfile_basename = os.path.basename(member_bodyfile_doxygen_relative)
        # We only care about .cpp files in our target set for *implementation* extraction
        if not bodyfile_basename.endswith(".cpp") or bodyfile_basename not in target_basenames:
            # print(f" DEBUG: Skipping member {class_name}::{member_name} ({member_kind}) because its body is in '{bodyfile_basename}' which is not a target .cpp.")
            continue

        # The actual file to extract from might be different from the inferred class_examples["filepath"]
        # because a method's body might be in a different .cpp than the class's main .cpp file (though rare).
        # Use the member_bodyfile_doxygen_relative to determine the actual file path.
        actual_member_impl_filepath_abs = os.path.normpath(os.path.join(PROJECT_ROOT, member_bodyfile_doxygen_relative))
        source_file_json_path = member_bodyfile_doxygen_relative


        extracted_code = ""
        if member_kind in ["function", "public-func", "protected-func", "private-func", "signal", "slot", "ctor", "dtor"] and member_start_line > 0:
            programlisting_tag = member_def.find(".//programlisting")
            extracted_code = _extract_code_from_programlisting_tag(programlisting_tag)
            if not extracted_code:
                # Use the actual_member_impl_filepath_abs for extraction
                extracted_code = _extract_code_from_file(actual_member_impl_filepath_abs, member_start_line,
                                                        member_definition, member_bodystart, member_bodyend)
            if extracted_code:
                class_examples["functions"].append({
                    "name": member_name,
                    "kind": member_kind,
                    "code": extracted_code,
                    "brief_comment": member_brief,
                    "detailed_comment": member_detailed,
                    "start_line": member_start_line,
                    "definition": member_definition,
                    "source_file": source_file_json_path
                })
        elif member_kind in ["enum", "variable", "typedef", "struct", "union", "property"]:
            snippet_code = ""
            programlisting_tag = member_def.find(".//programlisting")
            if programlisting_tag is not None:
                snippet_code = _extract_code_from_programlisting_tag(programlisting_tag)
            if not snippet_code and member_start_line > 0:
                snippet_code = _extract_code_from_file(actual_member_impl_filepath_abs, member_start_line,
                                                    member_definition, member_bodystart, member_bodyend)
            if snippet_code:
                class_examples["other_snippets"].append({
                    "name": member_name,
                    "kind": member_kind,
                    "code": snippet_code,
                    "brief_comment": member_brief,
                    "detailed_comment": member_detailed,
                    "start_line": member_start_line,
                    "definition": member_definition,
                    "source_file": source_file_json_path
                })

    if class_examples["functions"] or class_examples["other_snippets"]:
        parsed_examples_data.append(class_examples)
        print(f" INFO: Extracted {len(class_examples['functions'])} funcs and {len(class_examples['other_snippets'])} snippets from class: {class_name}")

def process_compound_namespace(detail_xml_file, namespace_name, refid, xml_dir, source_root_dir, target_files_relative, parsed_examples_data):
    """
    Processes a Doxygen XML file representing a namespace.
    Extracts functions and other members that are defined within the namespace
    and whose implementation resides in one of the target .cpp files.
    """
    if not os.path.exists(detail_xml_file):
        print(f"WARNING: Detail XML file {detail_xml_file} not found for namespace {namespace_name}. Skipping.")
        return

    try:
        detail_tree = ET.parse(detail_xml_file)
        detail_root = detail_tree.getroot()
    except ET.ParseError as e:
        print(f"ERROR: Could not parse detail XML {detail_xml_file}: {e}")
        return

    namespace_compound_def = detail_root.find(f".//compounddef[@id='{refid}']")
    if namespace_compound_def is None:
        print(f"WARNING: No main <compounddef> found in {detail_xml_file} for namespace {namespace_name}. Skipping.")
        return

    namespace_examples = {
        "name": namespace_name,
        "kind": "namespace",
        "functions": [],
        "other_snippets": []
    }

    # Pre-process target_files_relative into a set of basenames for faster lookup
    target_basenames = {os.path.basename(f) for f in target_files_relative}

    # Iterate over all memberdefs within this namespace compound
    for member_def in namespace_compound_def.findall(".//memberdef"):
        member_kind = member_def.get("kind")
        member_name = member_def.findtext("name", default="").strip()
        member_definition = member_def.findtext("definition", default="").strip()
        member_brief = member_def.findtext("briefdescription/para", default="").strip()
        member_detailed = member_def.findtext("detaileddescription/para", default="").strip()

        member_location = member_def.find("location")
        if member_location is None:
            # print(f" DEBUG: Skipping member {member_name} ({member_kind}) from namespace {namespace_name} due to missing location tag.")
            continue # Skip if no location information

        member_start_line = int(member_location.get("line")) if member_location.get("line") else 0
        member_bodystart = int(member_location.get("bodystart")) if member_location.get("bodystart") else None
        member_bodyend = int(member_location.get("bodyend")) if member_location.get("bodyend") else None
        member_bodyfile_doxygen_relative = member_location.get("bodyfile")
        if member_bodyfile_doxygen_relative is None:
            # print(f" DEBUG: Skipping member {member_name} ({member_kind}) from namespace {namespace_name} due to missing bodyfile attribute.")
            continue # Skip if no bodyfile attribute

        # Crucial check: ensure this member's body is in one of our target .cpp files
        # Normalize the bodyfile path from Doxygen to just its basename for comparison
        bodyfile_basename = os.path.basename(member_bodyfile_doxygen_relative)
        # We only care about .cpp files in our target set for *implementation* extraction
        if not bodyfile_basename.endswith(".cpp") or bodyfile_basename not in target_basenames:
            # print(f" DEBUG: Skipping member {member_name} ({member_kind}) from namespace {namespace_name}. Bodyfile '{bodyfile_basename}' not a target .cpp.")
            continue

        # Construct the absolute path to the implementation file based on source_root_dir
        # The member_bodyfile_doxygen_relative itself is usually already relative from the Doxygen INPUT path,
        # which aligns with how SDK_EXAMPLES_BASE_SOURCE_DIR is used.
        impl_filepath_abs = os.path.normpath(os.path.join(PROJECT_ROOT, member_bodyfile_doxygen_relative))
        # Ensure we use the path as Doxygen reported it for the 'source_file' field in JSON
        source_file_json_path = member_bodyfile_doxygen_relative

        extracted_code = ""
        if member_kind == "function" and member_start_line > 0:
            programlisting_tag = member_def.find(".//programlisting")
            extracted_code = _extract_code_from_programlisting_tag(programlisting_tag)
            if not extracted_code:
                extracted_code = _extract_code_from_file(impl_filepath_abs, member_start_line,
                                                        member_definition, member_bodystart, member_bodyend)
            if extracted_code:
                namespace_examples["functions"].append({
                    "name": member_name,
                    "kind": member_kind,
                    "code": extracted_code,
                    "brief_comment": member_brief,
                    "detailed_comment": member_detailed,
                    "start_line": member_start_line,
                    "definition": member_definition,
                    "source_file": source_file_json_path
                })
        elif member_kind in ["enum", "variable", "typedef", "struct", "union", "property"]:
            snippet_code = ""
            programlisting_tag = member_def.find(".//programlisting")
            if programlisting_tag is not None:
                snippet_code = _extract_code_from_programlisting_tag(programlisting_tag)
            if not snippet_code and member_start_line > 0:
                snippet_code = _extract_code_from_file(impl_filepath_abs, member_start_line,
                                                    member_definition, member_bodystart, member_bodyend)
            if snippet_code:
                namespace_examples["other_snippets"].append({
                    "name": member_name,
                    "kind": member_kind,
                    "code": snippet_code,
                    "brief_comment": member_brief,
                    "detailed_comment": member_detailed,
                    "start_line": member_start_line,
                    "definition": member_definition,
                    "source_file": source_file_json_path
                })

    if namespace_examples["functions"] or namespace_examples["other_snippets"]:
        parsed_examples_data.append(namespace_examples)
        print(f" INFO: Extracted {len(namespace_examples['functions'])} funcs and {len(namespace_examples['other_snippets'])} snippets from namespace: {namespace_name}")


# --- Main Execution Logic for Example Parser ---
if __name__ == "__main__":
    # Define the SDK versions to process
    sdk_versions_to_parse = ["1.14.00", "2.00.00"]

    for version in sdk_versions_to_parse:
        print(f"\n--- Processing SDK Examples Version: {version} ---")

        # Dynamically set version-specific paths
        current_sdk_example_source_dir = os.path.join(SDK_EXAMPLES_BASE_SOURCE_DIR, f"v{version}")
        current_doxygen_examples_output_dir = os.path.join(DOXYGEN_EXAMPLES_BASE_OUTPUT_DIR, f"v{version}")
        current_parsed_examples_output_dir = os.path.join(PARSED_EXAMPLES_BASE_OUTPUT_DIR, f"V{version}") # Output folder named with V prefix

        os.makedirs(current_parsed_examples_output_dir, exist_ok=True) # Ensure versioned output directory exists

        if not os.path.exists(current_sdk_example_source_dir):
            print(f"Error: SDK example source directory '{current_sdk_example_source_dir}' for version {version} not found. Skipping this version.")
            continue # Skip to the next version

        # Dynamically get all .cpp files, excluding the 'CRSDK' folder for the current version
        TARGET_EXAMPLE_FILES = _get_all_source_files(
            current_sdk_example_source_dir,
            exclude_dirs=['CRSDK'],
            file_extensions=['.cpp'] # Only target .cpp files for the main examples parsing
        )
        print(f"\nDiscovered {len(TARGET_EXAMPLE_FILES)} target .cpp files to process for v{version} (excluding CRSDK):")
        for f in TARGET_EXAMPLE_FILES:
            print(f" - {f}")

        # Phase 1: Run Doxygen for the current version
        doxygen_success = generate_doxygen_xml_for_examples(
            current_sdk_example_source_dir,
            current_doxygen_examples_output_dir,
            TARGET_EXAMPLE_FILES,
            version # Pass the current SDK version
        )

        if not doxygen_success:
            print(f"\nDoxygen XML generation for examples v{version} failed. Cannot proceed with parsing for this version.")
            continue # Skip to the next version

        doxygen_xml_sub_dir = os.path.join(current_doxygen_examples_output_dir, "xml")
        # Phase 2: Parse the generated XML for the current version
        parsed_examples_list = parse_example_xml(
            doxygen_xml_sub_dir,
            current_sdk_example_source_dir, # Pass the current source root for path resolution
            TARGET_EXAMPLE_FILES
        )

        print(f"\nDEBUG_SAVE: parsed_examples_list for v{version} has {len(parsed_examples_list)} items before saving.")

        # --- Phase 3: Save the parsed data for the current version ---
        if not parsed_examples_list:
            print(f"No C++ example code data extracted from Doxygen XML for v{version}.")
        else:
            print(f"\n--- Saving Parsed C++ Example Data for {len(parsed_examples_list)} files (v{version}) ---")
            for parsed_item in parsed_examples_list:
                # Determine output filename based on the 'kind'
                if parsed_item["kind"] == "example_file":
                    # For file-level examples, use the basename of the filepath
                    base_name = os.path.basename(parsed_item["filepath"]).replace(".", "_").lower()
                    output_file_name = f"{base_name}_v{version.replace('.', '_')}_examples_parsed.json" # Added version
                elif parsed_item["kind"] == "class":
                    # For class examples, use the class name
                    sanitized_class_name = parsed_item["name"].replace("::", "_").replace(" ", "_").lower()
                    output_file_name = f"{sanitized_class_name}_class_v{version.replace('.', '_')}_examples_parsed.json" # Added version
                elif parsed_item["kind"] == "namespace":
                    # For namespace examples, use the namespace name
                    sanitized_namespace_name = parsed_item["name"].replace("::", "_").replace(" ", "_").lower()
                    output_file_name = f"{sanitized_namespace_name}_namespace_v{version.replace('.', '_')}_examples_parsed.json" # Added version
                else:
                    # Fallback for unexpected kinds (shouldn't happen if logic is sound)
                    print(f"WARNING: Unknown parsed_item kind: {parsed_item['kind']}. Using generic filename for v{version}.")
                    base_name = parsed_item["name"].replace(".", "_").replace("::", "_").lower()
                    output_file_name = f"{base_name}_v{version.replace('.', '_')}_examples_parsed.json" # Added version

                # --- MODIFICATION START ---
                # Add the metadata object with the current SDK version.
                # The 'V' prefix is added to match your desired folder structure format.
                # Add the metadata object with the item's name as the title and the current SDK version.
                parsed_item["metadata"] = {
                    "title": parsed_item["name"],
                    "sdk_version": f"V{version}"
                }
                # --- MODIFICATION END ---

                output_path = os.path.join(current_parsed_examples_output_dir, output_file_name) # Use current_parsed_examples_output_dir

                print(f" Saving: {output_path}")

                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(parsed_item, f, indent=4, ensure_ascii=False)
                print(f" Saved: {output_path}")

            print(f"\nC++ example parsing process completed for v{version}.")

    print("\nAll specified SDK example versions processed.")