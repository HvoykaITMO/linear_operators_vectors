import bpy
import mathutils
import uuid
import os
import sys
from bpy.props import BoolProperty, FloatVectorProperty, PointerProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import Context, Event

vector_object = bpy.data.texts["vector_object.py"].as_module()


def update_radius(self, context):
    obj = self.id_data  # объект, к которому привязаны свойства
    if hasattr(obj, "scale"):
        obj.scale = (self.radius, self.radius, self.radius)

        # Далее для пересчёта снова проходимся по векторам
        for obj in bpy.data.objects:
            if hasattr(obj, "vector_props") and getattr(obj.vector_props, "is_vector", False):  # type: ignore
                for applied_op in obj.vector_props.applied_endomorphisms:  # type: ignore
                    if applied_op.endomorphism_uuid == self.uuid:
                        vector_object.update_vector_end(
                            obj.vector_props, context)  # type: ignore


def update_matrix(self, context):
    obj = self.id_data  # объект-сфера, к которому привязан PropertyGroup
    # Здесь можно, например, пересчитать и сохранить матрицу (или применить к чему-то)
    # Далее идёт просто
    col0 = mathutils.Vector(self.matrix_col0)
    col1 = mathutils.Vector(self.matrix_col1)
    col2 = mathutils.Vector(self.matrix_col2)
    mat = mathutils.Matrix((col0, col1, col2)).transposed()  # type: ignore

    for obj in bpy.data.objects:
        if hasattr(obj, "vector_props") and getattr(obj.vector_props, "is_vector", False):  # type: ignore
            for applied_op in obj.vector_props.applied_endomorphisms:  # type: ignore
                if applied_op.endomorphism_uuid == self.uuid:
                    vector_object.update_vector_end(
                        obj.vector_props, context)  # type: ignore


def update_all_endomorphisms(scene):
    for obj in bpy.data.objects:
        if hasattr(obj, "endomorphism_props") and getattr(obj.endomorphism_props, "is_endomorphism", False):  # type: ignore
            props = obj.endomorphism_props  # type: ignore
            obj.scale = (props.radius, props.radius, props.radius)
            obj.endomorphism_props.matrix_col0 = props.matrix_col0  # type: ignore
            obj.endomorphism_props.matrix_col1 = props.matrix_col1  # type: ignore
            obj.endomorphism_props.matrix_col2 = props.matrix_col2  # type: ignore
            obj.endomorphism_props.radius = props.radius  # type: ignore


class RecreateEndomorphismObject(bpy.types.Operator):
    bl_idname = "object.recreate_endomorphism_object"
    bl_label = "Recreate Sphere"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object

        segments = obj.endomorphism_props.segments_amount  # type: ignore
        rings = obj.endomorphism_props.rings_amount  # type: ignore
        radius = obj.endomorphism_props.radius  # type: ignore

        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=segments,
            ring_count=rings,
            radius=radius,  # Базовый радиус
            location=obj.location  # type: ignore
        )

        new_sphere = context.active_object
        new_sphere.display_type = 'WIRE'  # type: ignore

        old_name = obj.name  # type: ignore

        new_sphere.endomorphism_props.is_endomorphism = True  # type: ignore
        new_sphere.endomorphism_props.uuid = obj.endomorphism_props.uuid  # type: ignore
        new_sphere.endomorphism_props.radius = radius  # type: ignore
        new_sphere.endomorphism_props.segments_amount = segments  # type: ignore
        new_sphere.endomorphism_props.rings_amount = rings  # type: ignore
        new_sphere.endomorphism_props.matrix_col0 = obj.endomorphism_props.matrix_col0  # type: ignore
        new_sphere.endomorphism_props.matrix_col1 = obj.endomorphism_props.matrix_col1  # type: ignore
        new_sphere.endomorphism_props.matrix_col2 = obj.endomorphism_props.matrix_col2  # type: ignore

        bpy.data.objects.remove(obj, do_unlink=True)  # type: ignore

        new_sphere.name = old_name  # type: ignore

        self.report({'INFO'}, "Sphere recreated")
        return {'FINISHED'}


class EndomorphismProperties(bpy.types.PropertyGroup):
    uuid: StringProperty(
        name="UUID",
        default=""
    )
    is_endomorphism: BoolProperty(
        default=False
    )
    matrix_col0: FloatVectorProperty(
        name='Col 0',
        size=3,
        default=(1, 0, 0),
        update=update_matrix
    )
    matrix_col1: FloatVectorProperty(
        name='Col 1',
        size=3,
        default=(0, 1, 0),
        update=update_matrix
    )
    matrix_col2: FloatVectorProperty(
        name='Col 2',
        size=3,
        default=(0, 0, 1),
        update=update_matrix
    )
    radius: FloatProperty(
        name="Radius",
        default=5.0,
        min=0.1,
        update=update_radius
    )
    segments_amount: IntProperty(
        name="Segments amount",
        description="Number of vertical segments",
        default=32,
        min=3,
        max=1000
    )
    rings_amount: IntProperty(
        name="Rings amount",
        description="Number of horizontal rings",
        default=16,
        min=3,
        max=1000
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
        min=0.1,
        update=update_radius
    )
    segments_amount: IntProperty(
        name="Segments amount",
        description="Number of vertical segments",
        default=32,
        min=3,
        max=1000
    )
    rings_amount: IntProperty(
        name="Rings amount",
        description="Number of horizontal rings",
        default=16,
        min=3,
        max=1000
    )

    def execute(self, context: Context):
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=1, segments=self.segments_amount, ring_count=self.rings_amount, location=(0, 0, 0))
        sphere = bpy.context.active_object
        sphere.display_type = 'WIRE'  # type: ignore
        sphere.name = "Endomorphism"  # type: ignore
        sphere.scale = (self.radius, self.radius, self.radius)  # type: ignore

        # Инициализация свойств
        sphere.endomorphism_props.uuid = str(uuid.uuid4())  # type: ignore
        sphere.endomorphism_props.is_endomorphism = True  # type: ignore
        sphere.endomorphism_props.matrix_col0 = self.matrix_col0  # type: ignore
        sphere.endomorphism_props.matrix_col1 = self.matrix_col1  # type: ignore
        sphere.endomorphism_props.matrix_col2 = self.matrix_col2  # type: ignore
        sphere.endomorphism_props.radius = self.radius  # type: ignore
        sphere.endomorphism_props.segments_amount = self.segments_amount  # type: ignore
        sphere.endomorphism_props.rings_amount = self.rings_amount  # type: ignore

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
        layout.prop(self, "segments_amount", text='Sphere segments')
        layout.prop(self, "rings_amount", text='Sphere rings')


class Endomorphism_PT_PANEL(bpy.types.Panel):
    bl_label = "Properties"
    bl_idname = 'Endomorphism_PT_Panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Endomorphism"

    @classmethod
    def poll(cls, context):
        obj = context.object
        is_great = obj is not None and hasattr(  # type: ignore
            obj, "endomorphism_props") and getattr(obj.endomorphism_props, "is_endomorphism", False)  # type: ignore
        return is_great

    def draw(self, context):
        layout = self.layout
        obj = context.object

        props = obj.endomorphism_props  # type: ignore

        layout.label(text="Matrix:")
        row = layout.row(align=True)
        col0 = row.column()
        col1 = row.column()
        col2 = row.column()
        col0.prop(props, "matrix_col0", text="Col 0")
        col1.prop(props, "matrix_col1", text="Col 1")
        col2.prop(props, "matrix_col2", text="Col 2")

        layout.prop(props, "radius", text='Sphere radius')

        layout.label(text="Sphere Parameters:")
        layout.prop(props, "segments_amount")
        layout.prop(props, "rings_amount")
        layout.operator(RecreateEndomorphismObject.bl_idname,
                        icon='FILE_REFRESH')


def menu_func(self, context):
    self.layout.operator(AddEndomorphismObject.bl_idname,
                         icon='SPHERE')


def register():
    bpy.utils.register_class(RecreateEndomorphismObject)
    bpy.utils.register_class(EndomorphismProperties)
    bpy.utils.register_class(AddEndomorphismObject)
    bpy.utils.register_class(Endomorphism_PT_PANEL)
    bpy.types.Object.endomorphism_props = PointerProperty(  # type: ignore
        type=EndomorphismProperties)  # type: ignore
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)
    bpy.app.handlers.frame_change_post.append(update_all_endomorphisms)


def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    bpy.utils.unregister_class(RecreateEndomorphismObject)
    bpy.utils.unregister_class(EndomorphismProperties)
    bpy.utils.unregister_class(AddEndomorphismObject)
    bpy.utils.unregister_class(Endomorphism_PT_PANEL)
    del bpy.types.Object.endomorphism_props  # type: ignore
    if update_all_endomorphisms in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(update_all_endomorphisms)


if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
