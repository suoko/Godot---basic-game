def load_obj(file_path):
    vertices = []
    faces = []
    materials = []

    current_material = "default"

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            if line.startswith('v '):
                _, x, y, z = line.split()
                vertices.append((float(x), float(y), float(z)))

            elif line.startswith('usemtl '):
                parts = line.split()
                if len(parts) > 1:
                    current_material = parts[1]

            elif line.startswith('f '):
                # Only keep vertex indices
                face_indices = [int(p.split('/')[0]) - 1 for p in line.split()[1:]]
                faces.append(face_indices)
                materials.append(current_material)

    return vertices, faces, materials


def save_colored_obj(output_file, vertices, faces, materials):
    mtllib_line = "mtllib scene_materials.mtl\n"

    with open(output_file, 'w') as f:
        # Write material library inline
        f.write(mtllib_line)

        # Write vertices
        for vertex in vertices:
            f.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")

        # Write faces grouped by material
        current_material = None
        for i, face in enumerate(faces):
            mat_name = materials[i]

            # Map material name to final color category
            if mat_name == "roof":
                final_mat = "red"
            elif mat_name == "wall":
                final_mat = "yellow"
            elif mat_name in ["paths_cycleway", "paths_footway", "paths_steps"]:
                final_mat = "grey"
            elif mat_name in ["roads_residential", "roads_service", "roads_tertiary"]:
                final_mat = "dark_grey"
            elif mat_name in ["Terrain", "roads_unclassified"]:
                final_mat = "dark_green"
            elif mat_name == "water":
                final_mat = "blue"
            else:
                final_mat = "default"

            if current_material != final_mat:
                f.write(f"usemtl {final_mat}\n")
                current_material = final_mat

            f.write("f " + " ".join(str(idx + 1) for idx in face) + "\n")


def save_material_file():
    mtl_content = """
newmtl red
Kd 1.0 0.0 0.0
Ka 0.2 0.2 0.2
Ks 0.5 0.5 0.5
Ns 10.0

newmtl yellow
Kd 1.0 1.0 0.0
Ka 0.2 0.2 0.2
Ks 0.5 0.5 0.5
Ns 10.0

newmtl grey
Kd 0.5 0.5 0.5
Ka 0.2 0.2 0.2
Ks 0.5 0.5 0.5
Ns 10.0

newmtl dark_grey
Kd 0.3 0.3 0.3
Ka 0.2 0.2 0.2
Ks 0.4 0.4 0.4
Ns 10.0

newmtl dark_green
Kd 0.0 0.4 0.0
Ka 0.2 0.2 0.2
Ks 0.5 0.5 0.5
Ns 10.0

newmtl blue
Kd 0.0 0.0 1.0
Ka 0.2 0.2 0.2
Ks 0.5 0.5 0.5
Ns 10.0

newmtl default
Kd 1.0 1.0 1.0
Ka 0.2 0.2 0.2
Ks 0.5 0.5 0.5
Ns 10.0
"""

    with open("scene_materials.mtl", 'w') as f:
        f.write(mtl_content.strip())


# Main function
def color_by_material_group(input_file="scuola2_red_roof.obj", output_file="scuola2_final_colored.obj"):
    print(f"Loading {input_file}...")
    vertices, faces, materials = load_obj(input_file)

    print("Saving final model...")
    save_colored_obj(output_file, vertices, faces, materials)
    save_material_file()

    print(f"✅ Final colored model saved as {output_file}")
    print(f"   - Also created: scene_materials.mtl")


if __name__ == "__main__":
    color_by_material_group()