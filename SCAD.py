bl_info = {
    "name": "Add-on SCAD",
    "blender": (3, 0, 0),
    "category": "Interface",
    "author": "Paul Kokot",
    "location": "Text Editor -> Header",
    "version": (0, 0, 3)
}

import bpy

class TEXT_OT_run_scad(bpy.types.Operator):
    """Runs SCAD script"""
    bl_idname = "text.run_scad"
    bl_label = "Run SCAD"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        st = context.space_data
        text = st.text
        look_for_keywords(text.as_string())
        return {'FINISHED'}
    
def look_for_keywords(text):
    lines = text.splitlines()
    for line in lines:
        words = line.split(' ')
        if words[0] == "cube":
            print('here')
            bpy.ops.mesh.primitive_cube_add(location=(0,0,0))  
def draw(self, context):
    self.layout.operator("text.run_scad", text="", icon='MONKEY')

def register():
    bpy.utils.register_class(TEXT_OT_run_scad)
    bpy.types.TEXT_HT_header.append(draw)
def unregister():
    bpy.utils.unregister_class(TEXT_OT_run_scad)
    bpy.types.TEXT_HT_header.remove(draw)