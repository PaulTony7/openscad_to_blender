bl_info = {
    "name": "Add-on SCAD",
    "blender": (3, 0, 0),
    "category": "Interface",
    "author": "Paul Kokot",
    "location": "Text Editor -> Header",
    "version": (0, 0, 6)
}

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

def block_implementation(t):
    for cmd in t.children:
        run_instruction(cmd)

def assign_implementation(t):
    if type(t.children[1]) is Tree:
        res = expression_breakdown(t.children[1])
        variables[t.children[0]] = res
        print(f"assigning {t.children[0]} value {res}")
    else:
        variables[t.children[0]] = t.children[1]
        print(f"assigning {t.children[0]} value {t.children[1]}")

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
        return variables[t.value]

def operation_breakdown(t):
    if t.value == "translate":
        return "TRANSLATION"
    elif t.value == "rotate":
        return "ROTATION"
    elif t.value == "scale":
        return "RESIZE"

def create_object(t, x, y, z):
    if t == "cube":
        bpy.ops.mesh.primitive_cube_add(location=(0,0,0), scale=(x,y,z))
    elif t == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(location=(0,0,0), scale=(x,y,z))
    elif t == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(location=(0,0,0), scale=(x,y,z))

def parse_openscad(text):
    openscad_parser = Lark(r"""
    start: instruction+

    instruction: action ";"                              
    |            action operator+ ";"           
    |            IDENTIFIER "=" (expression) ";"                                -> assign
    |            "{" instruction+ "}" operator+ ";"                             -> block

    action: OBJECT "(" (INTEGER | FLOAT | vector | IDENTIFIER) ")"

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

    OBJECT: "cube"|"square"|"circle"|"sphere"|"cylinder"
    TRANSFORM: "translate"|"rotate"|"scale"

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

def draw(self, context):
    self.layout.operator("text.run_scad", text="", icon='MONKEY')

def register():
    bpy.utils.register_class(TEXT_OT_run_scad)
    bpy.types.TEXT_HT_header.append(draw)
def unregister():
    bpy.utils.unregister_class(TEXT_OT_run_scad)
    bpy.types.TEXT_HT_header.remove(draw)

# text = """x = [5,5,2];
# y = 2;
# x = x / y;

# sphere(x) translate(x);"""
# parse_openscad(text)