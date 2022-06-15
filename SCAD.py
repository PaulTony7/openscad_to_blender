bl_info = {
    "name": "Add-on SCAD",
    "blender": (3, 2, 0),
    "category": "Interface",
    "author": "Paul Kokot",
    "location": "Text Editor -> Header",
    "version": (1, 2, 10)
}

help("modules")
import bpy
from lark import Lark, Tree, Token
from numpy import array, ndarray

class TEXT_OT_run_scad(bpy.types.Operator):
    """Runs SCAD script"""
    bl_idname = "text.run_scad"
    bl_label = "Run SCAD"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        st = context.space_data
        text = st.text
        parse_openscad(text.as_string())
        return {'FINISHED'}

variables = {}
objects = {}
materials = {}
colors = {
    '"red"': [1.0, 0.0, 0.0],
    '"blue"': [0.0, 0.0, 1.0],
    '"green"': [0.0, 1.0, 0.0]
}

def run_instruction(t):
    if(t.data == 'assign'):
        assign_implementation(t)
    elif t.data == "block" or t.data == "instruction":
        block_implementation(t)
    elif t.data == "color":
        color_implementation(t)
    elif t.data == "action":
       action_implementation(t)
    elif t.data == "transform":
        transform_implementation(t)
    else:
        raise SyntaxError('Unknown instruction: %s' % t.data)

def action_implementation(t):
    if t.children[0] == "clear":
        print(t.children[0])
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=False)
    else:
        parameter = value_breakdown(t.children[1])
        if type(parameter) == ndarray:
            x = parameter[0]
            y = parameter[1]
            z = parameter[2]
            print(f"creating {t.children[0]} of size [{x}, {y}, {z}]")
            create_object(t.children[0], x, y, z)
        else:
            print(f"creating {t.children[0]} of size {parameter}")
            create_object(t.children[0], parameter, parameter, parameter)

def transform_implementation(t):
    parameter = value_breakdown(t.children[1])
    operation = operation_breakdown(t.children[0])
    if type(parameter) == ndarray:
        x = parameter[0]
        y = parameter[1]
        z = parameter[2]
        print(f"transform operation {t.children[0]} with parameters [{x}, {y}, {z}]")
        bpy.ops.transform.transform(mode=operation, value=(x,y,z,1))
    elif operation == "ROTATION":
        print(f"transform operation {t.children[0]} with parameters {parameter}")
        bpy.ops.transform.rotate(value=(parameter))
    else:
        print(f"transform operation {t.children[0]} with parameters {parameter}")
        bpy.ops.transform.transform(mode=operation, value=(parameter,parameter,parameter,1))

def color_implementation(t):
    if type(t.children[0]) == Token:
        print(f"applying color {value_breakdown(t.children[0])}")
        
    else:
        print(f"applying color", *t.children[0].children)
        parameter = value_breakdown(t.children[0])
        if type(parameter) == ndarray:
            x = parameter[0]
            y = parameter[1]
            z = parameter[2]
            mat = create_material(x,y,z)
            for i in range(len(bpy.context.selected_objects)):
                bpy.context.selected_objects[i].active_material = mat
        elif type(parameter.value) == str:
            for color in colors.keys():
                if parameter == color:
                    parameter = colors[color]
                    x = parameter[0]
                    y = parameter[1]
                    z = parameter[2]
                    mat = create_material(x,y,z)
                    for i in range(len(bpy.context.selected_objects)):
                        bpy.context.selected_objects[i].active_material = mat


def check_material(name):
    for item in materials.keys():
        if item == name:
            return materials[item]
    return None

def create_material(r, g, b):
    intr = int(r * 255)
    intg = int(g * 255)
    intb = int(b * 255)
    matname = "mat" + str(intr) + "_" + str(intg) + "_" + str(intb)
    matg = check_material(matname)
    if matg is not None:
        return matg
    matg = bpy.data.materials.new(matname)
    matg.use_nodes = True
    tree = matg.node_tree
    nodes = tree.nodes
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
    matg.diffuse_color = (r, g, b, 1.0)
    materials[matname] = matg
    return matg

def block_implementation(t):
    for cmd in t.children:
        run_instruction(cmd)

# Assign to veriable 
def assign_implementation(t):
    if type(t.children[1]) is Tree:
        res = expression_breakdown(t.children[1])
        variables[t.children[0]] = res
        print(f"assigning {t.children[0]} value {res}")
    else:
        variables[t.children[0]] = t.children[1]
        print(f"assigning {t.children[0]} value {t.children[1]}")

# Breakdown expression
def expression_breakdown(t):
    if t.data == "value":
        return value_breakdown(t.children[0])
    elif t.data == "addition":
        return expression_breakdown(t.children[0]) + expression_breakdown(t.children[1]) 
    elif t.data == "multiplication":
        return expression_breakdown(t.children[0]) * expression_breakdown(t.children[1]) 
    elif t.data == "division":
        return expression_breakdown(t.children[0]) / expression_breakdown(t.children[1]) 
    elif t.data == "subtraction":
        return expression_breakdown(t.children[0]) - expression_breakdown(t.children[1]) 
    elif t.data == "parentheses":
        return expression_breakdown(t.children[0])
    elif t.data == "negation":
        return -expression_breakdown(t.children[0])
    elif t.data == "string":
        return t.children[0]

def value_breakdown(t):
    if type(t) == Tree and t.data == "string":
        return t.children[0]
    elif type(t) == Tree and t.data == "vector":
        return array([float(x) for x in t.children])
    elif t.type == "INTEGER":
        return int(t)
    elif t.type == "FLOAT":
        return float(t)
    elif t.type == "IDENTIFIER":
        return variables[t]

# Breakdown operation
def operation_breakdown(t):
    if t == "translate":
        return "TRANSLATION"
    elif t == "rotate":
        return "ROTATION"
    elif t == "scale":
        return "RESIZE"

# Create primitive
def create_object(t, x, y, z):
    if t == "cube":
        bpy.ops.mesh.primitive_cube_add(location=(0,0,0), scale=(x,y,z))
    elif t == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(location=(0,0,0), scale=(x,y,z))
    elif t == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(location=(0,0,0), scale=(x,y,z))
    elif t == "monkey":
        bpy.ops.mesh.primitive_monkey_add(location=(0,0,0), scale=(x,y,z))
    elif t == "uvsphere":
        bpy.ops.mesh.primitive_uv_sphere_add(location=(0,0,0), scale=(x,y,z))
    elif t == "cone":
        bpy.ops.mesh.primitive_cone_add(location=(0,0,0), scale=(x,y,z))
    elif t == "torus":
        bpy.ops.mesh.primitive_torus_add(location=(0,0,0), major_radius=x, minor_radius=x/4)
    elif t == "icosphere":
        bpy.ops.mesh.primitive_ico_sphere_add(location=(0,0,0), scale=(x,y,z))

# Parse text in text context
def parse_openscad(text):
    openscad_parser = Lark(r"""
    start: instruction+

    instruction: action operator+ ";"   
    |            action ";"                     
    |            IDENTIFIER "=" (expression) ";"                                -> assign
    |            "{" instruction+ "}" operator+ ";"                             -> block

    action: OBJECT "(" (INTEGER | FLOAT | vector | IDENTIFIER) ")"
    | SPECIAL

    operator: TRANSFORM "(" (INTEGER | FLOAT | vector | IDENTIFIER)")"          -> transform
    |         "color" "(" (string | INTEGER | FLOAT | vector | IDENTIFIER) ")"  -> color

    vector: "[" (INTEGER | FLOAT) ["," (INTEGER | FLOAT)]+"]"
    expression: (INTEGER | FLOAT | vector | string | IDENTIFIER)                -> value
    |           "-" expression                                                  -> negation
    |           expression "+" expression                                       -> addition
    |           expression "-" expression                                       -> subtraction
    |           expression "*" expression                                       -> multiplication
    |           expression "/" expression                                       -> division
    |           "(" expression ")"                                              -> parentheses

    OBJECT: "cube"|"sphere"|"cylinder"|"monkey"|"uvsphere"|"cone"|"torus"|"icosphere"
    TRANSFORM: "translate"|"rotate"|"scale"
    SPECIAL: "clear"

    string : ESCAPED_STRING

    %import common.WORD -> IDENTIFIER
    %import common.INT -> INTEGER
    %import common.FLOAT -> FLOAT
    %import common.ESCAPED_STRING
    %import common.WS
    %ignore WS
    %import common.SH_COMMENT
    %ignore SH_COMMENT
    """, parser='earley')
    
    for inst in openscad_parser.parse(text).children:
        run_instruction(inst)

# Add UI element to draw execute button
def draw(self, context):
    self.layout.operator("text.run_scad", text="", icon='MONKEY')

addon_keymaps = []

# Register and unregister add-on 
def register():
    bpy.utils.register_class(TEXT_OT_run_scad)
    bpy.types.TEXT_HT_header.append(draw)
    #Add hotkey
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='Run OpenSCAD mode', space_type='EMPTY')
        kmi = km.keymap_items.new(TEXT_OT_run_scad.bl_idname, 'T', 'PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))

def unregister():
    # Remove the hotkey
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.utils.unregister_class(TEXT_OT_run_scad)
    bpy.types.TEXT_HT_header.remove(draw)

if __name__ == "__main__":
    register()