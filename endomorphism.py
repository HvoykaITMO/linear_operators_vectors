import bpy
from bpy.props import BoolProperty, FloatVectorProperty, PointerProperty, FloatProperty
from bpy.types import Context, Event


class EndomorphismProperties(bpy.types.PropertyGroup):
    is_endomorphism: BoolProperty(
        default=True
    )
    matrix_col0: FloatVectorProperty(
        name='Col 0',
        size=3,
        default=(1, 0, 0)
    )
    matrix_col1: FloatVectorProperty(
        name='Col 1',
        size=3,
        default=(0, 1, 0)
    )
    matrix_col2: FloatVectorProperty(
        name='Col 2',
        size=3,
        default=(0, 0, 1)
    )
    radius: FloatProperty(
        name="Radius",
        default=5.0,
        min=0.1
    )


class AddEndomorphismObject(bpy.types.Operator):
    bl_idname = "mesh.add_endomorphism_object"
    bl_label = "Endomorphism"
    bl_options = {'REGISTER', 'UNDO'}

    matrix_col0: FloatVectorProperty(
        name="Col 0",
        size=3,
        default=(1, 0, 0)
    )
    matrix_col1: FloatVectorProperty(
        name="Col 1",
        size=3,
        default=(0, 1, 0)
    )
    matrix_col2: FloatVectorProperty(
        name="Col 2",
        size=3,
        default=(0, 0, 1)
    )
    radius: FloatProperty(
        name="Radius",
        default=5.0,
        min=0.1
    )

    def execute(self, context: Context):
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=self.radius, location=(0, 0, 0))
        sphere = bpy.context.active_object
        sphere.display_type = 'WIRE'  # type: ignore

        # Инициализация свойств
        sphere.endomorphism_props.matrix_col0 = self.matrix_col0  # type: ignore
        sphere.endomorphism_props.matrix_col1 = self.matrix_col1  # type: ignore
        sphere.endomorphism_props.matrix_col2 = self.matrix_col2  # type: ignore
        sphere.endomorphism_props.radius = self.radius  # type: ignore

        self.report({'INFO'}, f"Endomorphism created")
        return {'FINISHED'}

    def invoke(self, context: Context, event: Event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Matrix:")
        row = layout.row(align=True)
        col0 = row.column()
        col1 = row.column()
        col2 = row.column()
        col0.prop(self, "matrix_col0", text="Col 0")
        col1.prop(self, "matrix_col1", text="Col 1")
        col2.prop(self, "matrix_col2", text="Col 2")
        layout.prop(self, "radius", text='Sphere radius')


class Endomorphism_PT_PANEL(bpy.types.Panel):
    bl_label = "Properties"
    bl_idname = 'Endomorphism_PT_Panel'


def menu_func(self, context):
    self.layout.operator(AddEndomorphismObject.bl_idname,
                         icon='SPHERE')


def register():
    bpy.utils.register_class(EndomorphismProperties)
    bpy.utils.register_class(AddEndomorphismObject)
    bpy.types.Object.endomorphism_props = PointerProperty(  # type: ignore
        type=EndomorphismProperties)  # type: ignore
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    bpy.utils.unregister_class(EndomorphismProperties)
    bpy.utils.unregister_class(AddEndomorphismObject)
    del bpy.types.Object.endomorphism_props  # type: ignore


if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
