import math

def read_obj(path):
    vertices = []
    faces = []
    with open(path, 'r') as f:
        for line in f:
            if line.startswith('v '):
                parts = line.strip().split()
                x, y, z = map(float, parts[1:4])
                vertices.append([x, y, z])
            elif line.startswith('f '):
                parts = line.strip().split()[1:]
                face = []
                for part in parts:
                    idx = int(part.split('/')[0]) - 1
                    face.append(idx)
                faces.append(face)
    return vertices, faces

def write_obj(path, vertices, faces):
    with open(path, 'w') as f:
        for v in vertices:
            f.write(f'v {v[0]} {v[1]} {v[2]}\n')
        for face in faces:
            f.write(f'f {" ".join(str(i+1) for i in face)}\n')

def get_base_vertices(vertices, threshold=0.01):
    min_y = min(v[1] for v in vertices)
    return [v for v in vertices if abs(v[1] - min_y) < threshold]

def compute_bounding_box(vertices):
    xs = [v[0] for v in vertices]
    zs = [v[2] for v in vertices]
    return {
        'min_x': min(xs),
        'max_x': max(xs),
        'min_z': min(zs),
        'max_z': max(zs)
    }

def compute_scaling_factors(house_bbox, pyramid_bbox):
    house_width = house_bbox['max_x'] - house_bbox['min_x']
    house_depth = house_bbox['max_z'] - house_bbox['min_z']
    pyramid_width = pyramid_bbox['max_x'] - pyramid_bbox['min_x']
    pyramid_depth = pyramid_bbox['max_z'] - pyramid_bbox['min_z']
    
    scale_x = pyramid_width / house_width
    scale_z = pyramid_depth / house_depth
    return (scale_x, scale_z)

def scale_and_translate(vertices, scale_x, scale_z, translation):
    translated = []
    for v in vertices:
        new_x = (v[0] - house_center[0]) * scale_x + translation[0]
        new_z = (v[2] - house_center[2]) * scale_z + translation[2]
        translated.append([new_x, v[1], new_z])
    return translated

# Read files
house_vertices, house_faces = read_obj('SquareHouseA.obj')
pyramid_vertices, _ = read_obj('pyramid.obj')

# Extract bases
house_base = get_base_vertices(house_vertices)
pyramid_base = get_base_vertices(pyramid_vertices)

# Compute bounding boxes
house_bbox = compute_bounding_box(house_base)
pyramid_bbox = compute_bounding_box(pyramid_base)

# Compute scaling factors
scale_x, scale_z = compute_scaling_factors(house_bbox, pyramid_bbox)

# Compute center of house base for scaling
house_center = [
    (house_bbox['min_x'] + house_bbox['max_x']) / 2,
    0,  # Y-center isn't needed here
    (house_bbox['min_z'] + house_bbox['max_z']) / 2
]

# Translate to align with pyramid's base (example translation)
translation = [
    pyramid_bbox['min_x'] - (house_bbox['min_x'] * scale_x),
    0,  # Adjust Y if needed
    pyramid_bbox['min_z'] - (house_bbox['min_z'] * scale_z)
]

# Scale and translate all vertices
scaled_house = scale_and_translate(house_vertices, scale_x, scale_z, translation)

# Write result
write_obj('scaled_SquareHouseA.obj', scaled_house, house_faces)