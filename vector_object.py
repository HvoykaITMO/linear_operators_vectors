import bpy
from bpy.props import FloatVectorProperty, BoolProperty
from bpy.types import Context, Event
from typing import Literal
import mathutils


class AddVectorObject(bpy.types.Operator):
    bl_idname = "mesh.add_vector_object"
    bl_label = "Add Vector Object"
    bl_options = {'REGISTER', 'UNDO'}

    vector_end: FloatVectorProperty(
        name="Vector End",
        description="Coordinates of the vector end point",
        default=(0, 0, 0),
        subtype='TRANSLATION'
    )

    create_arrow: BoolProperty(
        name="Create arrow",
        description="Create an arrow empty",
        default=True
    )

    def execute(self, context: Context):
        verts = [self.vector_end]
        edges = []
        faces = []

        mesh = bpy.data.meshes.new("VectorMesh")
        mesh.from_pydata(verts, edges, faces)
        mesh.update()

        obj = bpy.data.objects.new("Vector", mesh)
        context.collection.objects.link(obj)

        if self.create_arrow:
            arrow = bpy.data.objects.new("VectorArrow", None)
            arrow.empty_display_type = 'SINGLE_ARROW'
            arrow.empty_display_size = 1

            start = mathutils.Vector((0, 0, 0))
            end = mathutils.Vector(self.vector_end)
            arrow.location = start
            direction = end - start
            arrow.rotation_mode = 'QUATERNION'
            arrow.rotation_quaternion = direction.to_track_quat('Z', 'Y')
            arrow.scale = (1, 1, direction.length)
            context.collection.objects.link(arrow)

            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            arrow.select_set(True)
            bpy.context.view_layer.objects.active = arrow
            bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

            context.view_layer.objects.active = arrow
            obj.select_set(False)

        self.report({'INFO'}, f"Vector created to {self.vector_end}")
        return {'FINISHED'}

    def invoke(self, context: Context, event: Event):
        return context.window_manager.invoke_props_dialog(self)


def menu_func(self, context):
    self.layout.operator("mesh.add_vector_object",
                         icon='EMPTY_SINGLE_ARROW')


def register():
    bpy.utils.register_class(AddVectorObject)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    bpy.utils.unregister_class(AddVectorObject)
    bpy.types.VIEW3D_MT_add.remove(menu_func)


if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
