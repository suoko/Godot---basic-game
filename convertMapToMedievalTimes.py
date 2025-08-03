import math
import random
import shutil
import os

# --- Utility Functions ---

def read_obj(path):
    """
    Reads a .obj file, capturing vertices, texture coordinates, normals,
    faces, materials, and object groups.
    Returns:
        vertices: List of [x, y, z]
        tex_coords: List of [u, v] (can be empty if not present)
        normals: List of [nx, ny, nz] (can be empty if not present)
        faces: List of (face_data, material_name, object_name)
               face_data is a list of (v_idx, vt_idx, vn_idx) tuples (0-based, None if missing)
        materials: List of mtllib filenames found
        objects: Dict of {object_name: [(face_data, material_name), ...]}
    """
    vertices = []
    tex_coords = []
    normals = []
    faces = []  # Will store (face_data, material_name, object_name)
    materials = [] # To store mtllib references
    current_material = None
    current_object = "default_object" # Default if no 'o' statement
    objects = {current_object: []} # Initialize default object

    try:
        with open(path, 'r') as f:
            for line_number, line in enumerate(f, 1): # Include line number for better error reporting
                line = line.strip()
                if not line:
                    continue

                parts = line.split()
                if not parts:
                    continue

                keyword = parts[0]

                try:
                    if keyword == 'v':
                        if len(parts) < 4:
                            print(f"Warning: Skipping invalid vertex line {line_number}: {line}")
                            continue
                        x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                        vertices.append([x, y, z])

                    elif keyword == 'vt':
                        # Texture coordinates (optional)
                        if len(parts) >= 2:
                             u = float(parts[1])
                             v = float(parts[2]) if len(parts) > 2 else 0.0 # Default v=0 if missing
                             tex_coords.append([u, v])
                        else:
                             print(f"Warning: Skipping invalid vt line {line_number}: {line}")

                    elif keyword == 'vn':
                        # Vertex normals (optional)
                        if len(parts) >= 4:
                            nx, ny, nz = float(parts[1]), float(parts[2]), float(parts[3])
                            normals.append([nx, ny, nz])
                        else:
                            print(f"Warning: Skipping invalid vn line {line_number}: {line}")

                    elif keyword == 'f':
                        # Face definition
                        face_indices = []
                        for part in parts[1:]: # Iterate through vertex definitions (v/vt/vn)
                            indices = part.split('/')
                            # Initialize indices as None
                            v_idx = None
                            vt_idx = None
                            vn_idx = None
                            try:
                                if indices[0]: # Vertex index
                                    v_idx = int(indices[0]) - 1 # Convert to 0-based
                                if len(indices) > 1 and indices[1]: # Texture coord index
                                    vt_idx = int(indices[1]) - 1 # Convert to 0-based
                                if len(indices) > 2 and indices[2]: # Normal index
                                    vn_idx = int(indices[2]) - 1 # Convert to 0-based
                            except ValueError:
                                print(f"Warning: Skipping invalid face index part '{part}' on line {line_number}: {line}")
                                continue # Skip this part of the face
                            face_indices.append((v_idx, vt_idx, vn_idx))

                        if face_indices: # Only add face if we parsed at least one valid vertex
                            faces.append((face_indices, current_material, current_object))
                            objects[current_object].append((face_indices, current_material))
                        else:
                            print(f"Warning: Skipping face line with no valid indices {line_number}: {line}")

                    elif keyword == 'usemtl':
                        # Material assignment
                        # Handle case where there's no material name or only whitespace
                        if len(parts) > 1 and parts[1].strip():
                            current_material = parts[1].strip()
                        else:
                            # print(f"Info: 'usemtl' command without name on line {line_number}, setting material to None.")
                            current_material = None # Or use a default string like "default_material"

                    elif keyword == 'o':
                        # Object/group name
                        if len(parts) > 1 and parts[1].strip():
                            current_object = parts[1].strip()
                        else:
                            # print(f"Info: 'o' command without name on line {line_number}, using default object name.")
                            current_object = "unnamed_object" # Assign a default name
                        if current_object not in objects:
                            objects[current_object] = [] # Initialize list for new object

                    elif keyword == 'mtllib':
                        # Material library reference
                        if len(parts) > 1:
                            materials.append(parts[1]) # Store the filename

                except (ValueError, IndexError) as e:
                    print(f"Warning: Error parsing line {line_number}: {line}. Error: {e}")
                    continue # Skip lines with parsing errors

    except FileNotFoundError:
        print(f"Error: File not found: {path}")
        return [], [], [], [], [], {}
    except Exception as e:
        print(f"Error reading file {path}: {e}")
        return [], [], [], [], [], {}

    return vertices, tex_coords, normals, faces, materials, objects


def write_obj(path, vertices, tex_coords, normals, objects_faces_data, mtllib_line=None):
    """
    Writes a .obj file with vertices, texture coordinates, normals, and organized faces.
    """
    with open(path, 'w') as f:
        if mtllib_line:
            f.write(f"{mtllib_line}\n")
        # Add a default mtllib line if not provided and house might need it
        # elif mtllib_line is None:
        #     f.write("mtllib map.mtl\n") # Or SquareHouseA.mtl if different

        # Write vertices
        for v in vertices:
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

        # Write texture coordinates (if any)
        for vt in tex_coords:
            if len(vt) >= 2: # Check if vt data is valid
                 f.write(f"vt {vt[0]:.6f} {vt[1]:.6f}\n")

        # Write normals (if any)
        for vn in normals:
            if len(vn) >= 3: # Check if vn data is valid
                f.write(f"vn {vn[0]:.6f} {vn[1]:.6f} {vn[2]:.6f}\n")

        # Write faces organized by object
        for obj_name, obj_faces in objects_faces_data.items():
            if obj_faces: # Only write object header if it has faces
                f.write(f"o {obj_name}\n")
                current_mat = None
                for face_indices, mat_name in obj_faces:
                    # Check if material changed (including from None to a name, or name to None)
                    if mat_name != current_mat:
                        if mat_name: # Only write usemtl if a material name exists
                            f.write(f"usemtl {mat_name}\n")
                        elif current_mat is not None: # If previous face had a material but this one doesn't
                             # Optionally write "usemtl" without name or just rely on implicit None change
                             # For simplicity, we'll just track the change
                             pass
                        # Update current material tracker
                        current_mat = mat_name

                    # Format face line
                    face_str_parts = []
                    for v_idx, vt_idx, vn_idx in face_indices:
                        # Build the v/vt/vn string for this vertex
                        part_str = ""
                        if v_idx is not None:
                            part_str += str(v_idx + 1) # Convert back to 1-based
                        # Add texture coordinate index
                        if vt_idx is not None:
                            part_str += f"/{vt_idx + 1}" # Add vt (1-based)
                        elif vn_idx is not None:
                            part_str += "/" # Placeholder for missing vt if vn exists (v//vn format)
                        # Add normal index
                        if vn_idx is not None:
                            # If vt was missing, part_str might be "v_idx/", now add "/vn_idx"
                            # If vt was present, part_str is "v_idx/vt_idx", now add "/vn_idx"
                            # If both missing, part_str is "v_idx", now add "//vn_idx"
                            if '/' in part_str:
                                part_str += f"/{vn_idx + 1}" # Append vn (1-based)
                            else:
                                part_str += f"//{vn_idx + 1}" # Handle v//vn format
                        face_str_parts.append(part_str)

                    if face_str_parts: # Only write face if it has valid parts
                        f.write(f"f {' '.join(face_str_parts)}\n")

def copy_or_merge_mtl_files(original_scene_mtl_path, house_mtl_paths, output_mtl_path):
    """
    Copies the original scene's MTL and appends house MTL definitions.
    This assumes house materials don't conflict or are compatible.
    """
    try:
        with open(output_mtl_path, 'w') as out_f:
            # 1. Copy original scene MTL content
            if os.path.exists(original_scene_mtl_path):
                with open(original_scene_mtl_path, 'r') as in_f:
                    out_f.write(in_f.read())
                print(f"Copied material definitions from '{original_scene_mtl_path}'")
            else:
                print(f"Warning: Original scene MTL '{original_scene_mtl_path}' not found. Output MTL will only contain house materials.")

            # 2. Append house MTL content
            for mtl_path in house_mtl_paths:
                if os.path.exists(mtl_path):
                    with open(mtl_path, 'r') as in_f:
                        # Add a separator comment for clarity (optional)
                        out_f.write(f"\n# --- Material definitions from {os.path.basename(mtl_path)} ---\n")
                        out_f.write(in_f.read())
                    print(f"Appended material definitions from '{mtl_path}'")
                else:
                     print(f"Warning: House MTL '{mtl_path}' not found.")

        print(f"Successfully created merged material file '{output_mtl_path}'")

    except Exception as e:
        print(f"Error creating merged MTL file '{output_mtl_path}': {e}")


def get_face_bbox(face_vertices):
    """
    Calculates the 2D bounding box (X, Z) of a list of vertices.
    """
    if not face_vertices:
        return {'min_x': 0, 'max_x': 0, 'min_z': 0, 'max_z': 0}
    xs = [v[0] for v in face_vertices]
    zs = [v[2] for v in face_vertices]
    return {
        'min_x': min(xs),
        'max_x': max(xs),
        'min_z': min(zs),
        'max_z': max(zs),
    }

def get_model_y_extents(vertices):
    """Gets the min and max Y values of the model's vertices."""
    if not vertices:
        return 0.0, 0.0
    ys = [v[1] for v in vertices]
    return min(ys), max(ys)

def get_model_base_bbox(vertices):
    """Gets the 2D bounding box of the model's base (vertices with minimum Y)."""
    if not vertices:
        return {'min_x': 0, 'max_x': 0, 'min_z': 0, 'max_z': 0}
    min_y = min(v[1] for v in vertices)
    base_vertices = [v for v in vertices if abs(v[1] - min_y) < 0.01] # Small threshold
    return get_face_bbox(base_vertices)


def compute_base_y(face_vertices):
    """Computes the minimum Y-coordinate (base height) of the wall vertices."""
    if not face_vertices:
        return 0.0
    return min(v[1] for v in face_vertices)

def compute_top_y(face_vertices):
    """Computes the maximum Y-coordinate (top height) of the wall/roof vertices."""
    if not face_vertices:
        return 0.0
    return max(v[1] for v in face_vertices)

def scale_house_to_fit_base_and_height(house_vertices, target_base_bbox, target_height):
    """
    Scales the house model to fit the target base footprint and height.
    """
    # --- 1. Get house base bbox and Y extents ---
    house_base_bbox = get_model_base_bbox(house_vertices)
    house_min_y, house_max_y = get_model_y_extents(house_vertices)
    house_base_height = house_min_y
    house_original_height = house_max_y - house_min_y if house_max_y > house_min_y else 1.0 # Avoid div by zero

    # --- 2. Calculate scale factors ---
    # X, Z scaling based on base footprint
    house_width_x = house_base_bbox['max_x'] - house_base_bbox['min_x']
    house_width_z = house_base_bbox['max_z'] - house_base_bbox['min_z']

    target_width_x = target_base_bbox['max_x'] - target_base_bbox['min_x']
    target_width_z = target_base_bbox['max_z'] - target_base_bbox['min_z']

    if house_width_x == 0 or house_width_z == 0:
        print("Warning: House base has zero dimension. Cannot scale X/Z.")
        scale_x, scale_z = 1.0, 1.0
    else:
        scale_x = target_width_x / house_width_x
        scale_z = target_width_z / house_width_z

    # Y scaling based on height
    scale_y = target_height / house_original_height if house_original_height != 0 else 1.0

    # --- 3. Calculate centers ---
    house_center_x = (house_base_bbox['min_x'] + house_base_bbox['max_x']) / 2.0
    house_center_z = (house_base_bbox['min_z'] + house_base_bbox['max_z']) / 2.0
    target_center_x = (target_base_bbox['min_x'] + target_base_bbox['max_x']) / 2.0
    target_center_z = (target_base_bbox['min_z'] + target_base_bbox['max_z']) / 2.0

    # --- 4. Scale and translate vertices ---
    scaled_translated_vertices = []
    for v in house_vertices:
        # Translate house base center to origin
        dx = v[0] - house_center_x
        dy = v[1] - house_base_height # Translate base to Y=0
        dz = v[2] - house_center_z

        # Scale
        scaled_dx = dx * scale_x
        scaled_dy = dy * scale_y # Scale height
        scaled_dz = dz * scale_z

        # Translate to target center and base height
        new_x = target_center_x + scaled_dx
        new_y = scaled_dy # Y is now scaled relative to base (Y=0)
        new_z = target_center_z + scaled_dz

        scaled_translated_vertices.append([new_x, new_y, new_z])

    return scaled_translated_vertices

# --- Configuration for Multiple House Models ---
# List the paths to your additional house models here
# Make sure these files exist in the same directory or provide full paths.
HOUSE_MODEL_FILES = [
    "SquareHouseA.obj",
    "SquareHouseB.obj",
    "SquareHouseC.obj",
    "SquareHouseD.obj",
    "SquareHouseE.obj",
]

def load_house_models(house_model_paths):
    """Loads all house models into a dictionary."""
    house_models = {}
    for path in house_model_paths:
        name = os.path.splitext(os.path.basename(path))[0] # Use filename without extension as key
        print(f"Loading house model: {name} from {path}...")
        vertices, tex_coords, normals, faces, materials, objects = read_obj(path)
        if vertices:
            house_models[name] = {
                'vertices': vertices,
                'tex_coords': tex_coords,
                'normals': normals,
                'faces': faces, # List of (face_data, mat_name, obj_name)
                'materials': materials, # List of mtllib filenames (e.g., ['SquareHouseA.mtl'])
                'objects': objects # Dict of {obj_name: [(face_data, mat_name), ...]}
            }
            print(f"  Successfully loaded {name} ({len(vertices)} vertices)")
        else:
            print(f"  Failed to load {name}")
    return house_models

def main():
    # --- Configuration ---
    input_path = 'map.obj' # Use the original file
    output_obj_path = 'map_replaced_buildings_final_corrected.obj' # Final output OBJ name
    output_mtl_path = 'map_replaced_buildings_final_corrected.mtl' # Final output MTL name
    original_scene_mtl_name = 'map.mtl' # Original scene's MTL name (from OBJ file)

    # --- Load All House Models ---
    house_models = load_house_models(HOUSE_MODEL_FILES)
    if not house_models:
        print("Error: No house models could be loaded. Exiting.")
        return
    print(f"Loaded {len(house_models)} house model(s).")

    # --- Load Target Model ---
    print("Loading target model...")
    target_vertices, target_tex_coords, target_normals, target_faces, target_materials, target_objects = read_obj(input_path)

    if not target_vertices:
        print("Error: Failed to load target model vertices. Exiting.")
        return

    # --- Prepare Output Data ---
    final_vertices = list(target_vertices) # Start with target vertices
    final_tex_coords = list(target_tex_coords)
    final_normals = list(target_normals)
    final_objects_faces = {}

    # Track base indices for appended data (house instances)
    v_base_idx = len(final_vertices)
    vt_base_idx = len(final_tex_coords)
    vn_base_idx = len(final_normals)

    # --- Identify Buildings to Replace ---
    # Include both 'element.<number>' and 'element'
    buildings_to_replace = [obj_name for obj_name in target_objects.keys() if obj_name.startswith("element")]
    print(f"Found {len(buildings_to_replace)} buildings to process: {buildings_to_replace}")

    # --- Process Each Building ---
    print("Processing buildings...")
    processed_count = 0
    for obj_name in buildings_to_replace:
        processed_count += 1
        print(f"  [{processed_count}/{len(buildings_to_replace)}] Processing building: {obj_name}")

        obj_faces = target_objects.get(obj_name, [])
        if not obj_faces:
             print(f"    Skipping {obj_name}: No faces found.")
             # Add original faces of this object to output since it's not replaced
             final_objects_faces[obj_name] = obj_faces
             continue

        # Collect roof and wall vertices for this specific object
        roof_vertices = []
        wall_vertices = []
        all_building_vertices = [] # Collect all vertices for this building to get overall height if needed
        for face_indices, mat_name in obj_faces: # Iterate over (face_data, material_name) tuples
            # Get actual vertex coordinates for this face
            face_vertex_coords = []
            valid_face = True
            for v_idx, _, _ in face_indices:
                if v_idx is not None and 0 <= v_idx < len(target_vertices):
                    face_vertex_coords.append(target_vertices[v_idx])
                else:
                    valid_face = False
                    break
            if valid_face and face_vertex_coords:
                all_building_vertices.extend(face_vertex_coords)
                if mat_name == 'roof':
                    roof_vertices.extend(face_vertex_coords)
                elif mat_name == 'wall':
                    wall_vertices.extend(face_vertex_coords)

        if not roof_vertices:
            print(f"    Warning: No 'roof' faces found for {obj_name}. Keeping original geometry.")
            # Add original faces of this object to output since it's not replaced
            final_objects_faces[obj_name] = obj_faces
            continue # Skip to next building

        # --- 1. Calculate roof footprint (for scaling house base) ---
        roof_bbox = get_face_bbox(roof_vertices)
        print(f"    Roof footprint: X({roof_bbox['min_x']:.3f}-{roof_bbox['max_x']:.3f}), Z({roof_bbox['min_z']:.3f}-{roof_bbox['max_z']:.3f})")

        # --- 2. Calculate building height ---
        # Option 1: Use wall vertices if available
        if wall_vertices:
            wall_base_height = compute_base_y(wall_vertices)
            wall_top_height = compute_top_y(wall_vertices) # Top of walls
            original_building_height = wall_top_height - wall_base_height
            print(f"    Original building height (from walls): {original_building_height:.3f}")
        # Option 2: Fallback to all building vertices if no distinct walls
        elif all_building_vertices:
             building_min_y, building_max_y = get_model_y_extents(all_building_vertices)
             original_building_height = building_max_y - building_min_y
             wall_base_height = building_min_y # Use overall min as base
             print(f"    Original building height (from all vertices): {original_building_height:.3f}")
        else:
             print(f"    Warning: Could not determine building height for {obj_name}. Using default height 5.0.")
             original_building_height = 5.0
             # Fallback for base height if no walls or all vertices - use roof base
             wall_base_height = min(v[1] for v in roof_vertices)

        # --- Enhancement 1: Make house 1/3 taller ---
        target_building_height = original_building_height * (4.0 / 3.0) # 1 + 1/3 = 4/3
        print(f"    Target house height (1/3 taller): {target_building_height:.3f}")


        # --- 3. Select a Random House Model ---
        selected_house_name = random.choice(list(house_models.keys()))
        selected_house_data = house_models[selected_house_name]
        print(f"    Selected house model: {selected_house_name}")

        # --- 4. Scale selected house to fit roof footprint and target height ---
        try:
            # Pass the base bbox and the calculated height
            scaled_house_vertices = scale_house_to_fit_base_and_height(
                selected_house_data['vertices'], roof_bbox, target_building_height
            )
        except Exception as e:
            print(f"    Error scaling house '{selected_house_name}' for {obj_name}: {e}. Keeping original geometry.")
            # Add original faces of this object to output since it's not replaced
            final_objects_faces[obj_name] = obj_faces
            continue

        # --- 5. Adjust house Y-position to match wall base height ---
        if scaled_house_vertices:
            # Find the base of the *scaled* house (its minimum Y after scaling relative to its own base)
            # The scaling function should have placed the base at Y=0, so we just need to add the target base height.
            # Let's double-check the min Y of the scaled house to be sure.
            house_base_height_after_scaling = min(v[1] for v in scaled_house_vertices)
            dy = wall_base_height - house_base_height_after_scaling
            # Translate all house vertices vertically
            translated_house_vertices = [[v[0], v[1] + dy, v[2]] for v in scaled_house_vertices]
        else:
            print(f"    Error: Scaled house '{selected_house_name}' has no vertices for {obj_name}. Keeping original geometry.")
            # Add original faces of this object to output since it's not replaced
            final_objects_faces[obj_name] = obj_faces
            continue

        # --- 6. Add transformed house data to final lists ---
        num_new_house_verts = len(translated_house_vertices)
        final_vertices.extend(translated_house_vertices)
        num_new_house_tex_coords = len(selected_house_data['tex_coords'])
        final_tex_coords.extend(selected_house_data['tex_coords'])
        num_new_house_normals = len(selected_house_data['normals'])
        final_normals.extend(selected_house_data['normals'])

        # --- 7. Adjust house face indices and add to output objects ---
        adjusted_house_faces = []
        # Iterate through faces from all house objects (usually just 'default_object')
        for house_obj_name, house_obj_faces in selected_house_data['objects'].items():
             for house_face_indices, house_mat_name in house_obj_faces: # house_obj_faces contains (face_data, mat_name) tuples
                 adjusted_face_indices = []
                 for v_idx, vt_idx, vn_idx in house_face_indices:
                     # Adjust indices relative to the appended positions in final lists
                     # Handle None values correctly
                     new_v_idx = v_idx + v_base_idx if v_idx is not None else None
                     new_vt_idx = vt_idx + vt_base_idx if vt_idx is not None else None
                     new_vn_idx = vn_idx + vn_base_idx if vn_idx is not None else None
                     adjusted_face_indices.append((new_v_idx, new_vt_idx, new_vn_idx))
                 adjusted_house_faces.append((adjusted_face_indices, house_mat_name)) # Store as (adjusted_face_data, mat_name)

        # Add the adjusted house faces under a new object name in the output
        house_instance_name = f"house_instance_{obj_name}_{selected_house_name}" # Include model name
        final_objects_faces[house_instance_name] = adjusted_house_faces # Store as {obj_name: [(face_data, mat_name), ...]}

        # --- 8. Update base indices for the *next* house instance ---
        v_base_idx += num_new_house_verts
        vt_base_idx += num_new_house_tex_coords
        vn_base_idx += num_new_house_normals

        # Note: We do NOT add the original 'element.XXX' object's faces to final_objects_faces
        # This effectively "removes" the original building.

    # --- Add Non-Replaced Objects (if any) ---
    # Objects that don't start with 'element' or were skipped due to errors
    non_building_objects = [name for name in target_objects.keys() if name not in buildings_to_replace]
    print(f"Adding {len(non_building_objects)} non-building objects to output...")
    for obj_name in non_building_objects:
        final_objects_faces[obj_name] = target_objects[obj_name] # Add as-is (list of (face_data, mat_name) tuples)


    # --- Write Output OBJ ---
    print("Writing output OBJ file...")
    # Use target model's mtllib line name, but point it to our new merged MTL file.
    # Assuming the first one is the main one. Adjust if needed.
    mtllib_line_for_obj = f"mtllib {os.path.basename(output_mtl_path)}" # Point to the new merged MTL
    try:
        write_obj(output_obj_path, final_vertices, final_tex_coords, final_normals, final_objects_faces, mtllib_line=mtllib_line_for_obj)
        print(f"Successfully saved merged model to '{output_obj_path}'")
    except Exception as e:
        print(f"Error writing output OBJ file '{output_obj_path}': {e}")
        return # Stop if OBJ write fails

    # --- Write Output MTL ---
    print("Creating merged MTL file...")
    # Collect MTL paths from house models
    house_mtl_paths = []
    for model_data in house_models.values():
        for mtl_filename in model_data.get('materials', []):
             # Construct full path assuming MTL is in the same dir as the OBJ
             mtl_full_path = mtl_filename # os.path.join(os.path.dirname(model_data['path']), mtl_filename) if 'path' was stored
             house_mtl_paths.append(mtl_full_path)

    # Merge original scene MTL with house MTLs
    copy_or_merge_mtl_files(original_scene_mtl_name, house_mtl_paths, output_mtl_path)

    print("Process completed.")


if __name__ == "__main__":
    # Set seed for reproducible randomness if needed
    # random.seed(42)
    main()