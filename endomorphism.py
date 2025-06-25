import bpy
import mathutils
import uuid
from bpy.props import BoolProperty, FloatVectorProperty, PointerProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import Context, Event
from .vector_object import update_vector_end

# --- Функции-обновления свойств эндоморфизма ---


def update_radius(self, context):
    """
    Обновляет масштаб сферы-оператора при изменении радиуса,
    а также пересчитывает все векторы, к которым применён этот оператор.
    """
    obj = self.id_data
    if hasattr(obj, "scale"):
        obj.scale = (self.radius, self.radius, self.radius)
        # Пересчитать все связанные векторы
        for obj in bpy.data.objects:
            if hasattr(obj, "vector_props") and getattr(obj.vector_props, "is_vector", False):
                for applied_op in obj.vector_props.applied_endomorphisms:
                    if applied_op.endomorphism_uuid == self.uuid:
                        update_vector_end(obj.vector_props, context)


def update_matrix(self, context):
    """
    Обновляет все векторы, использующие данный оператор,
    при изменении хотя бы одного столбца матрицы.
    """
    obj = self.id_data
    col0 = mathutils.Vector(self.matrix_col0)
    col1 = mathutils.Vector(self.matrix_col1)
    col2 = mathutils.Vector(self.matrix_col2)
    mat = mathutils.Matrix((col0, col1, col2)).transposed()
    # Обновить все связанные векторы
    for obj in bpy.data.objects:
        if hasattr(obj, "vector_props") and getattr(obj.vector_props, "is_vector", False):
            for applied_op in obj.vector_props.applied_endomorphisms:
                if applied_op.endomorphism_uuid == self.uuid:
                    update_vector_end(obj.vector_props, context)


def update_all_endomorphisms(scene):
    """
    Обработчик кадра: обновляет масштаб и матрицу всех эндоморфизмов на каждом кадре (для поддержки анимации).
    """
    for obj in bpy.data.objects:
        if hasattr(obj, "endomorphism_props") and getattr(obj.endomorphism_props, "is_endomorphism", False):
            props = obj.endomorphism_props
            obj.scale = (props.radius, props.radius, props.radius)
            obj.endomorphism_props.matrix_col0 = props.matrix_col0
            obj.endomorphism_props.matrix_col1 = props.matrix_col1
            obj.endomorphism_props.matrix_col2 = props.matrix_col2
            obj.endomorphism_props.radius = props.radius

# --- Операторы ---


class RecreateEndomorphismObject(bpy.types.Operator):
    """
    Оператор для пересоздания сферы-оператора с новыми параметрами (например, сегментами или кольцами).
    """
    bl_idname = "object.recreate_endomorphism_object"
    bl_label = "Recreate Sphere"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        segments = obj.endomorphism_props.segments_amount
        rings = obj.endomorphism_props.rings_amount
        radius = obj.endomorphism_props.radius

        # Создаём новую сферу с заданными параметрами
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=segments,
            ring_count=rings,
            radius=radius,
            location=obj.location
        )
        new_sphere = context.active_object
        new_sphere.display_type = 'WIRE'

        old_name = obj.name

        # Копируем все свойства
        new_sphere.endomorphism_props.is_endomorphism = True
        new_sphere.endomorphism_props.uuid = obj.endomorphism_props.uuid
        new_sphere.endomorphism_props.radius = radius
        new_sphere.endomorphism_props.segments_amount = segments
        new_sphere.endomorphism_props.rings_amount = rings
        new_sphere.endomorphism_props.matrix_col0 = obj.endomorphism_props.matrix_col0
        new_sphere.endomorphism_props.matrix_col1 = obj.endomorphism_props.matrix_col1
        new_sphere.endomorphism_props.matrix_col2 = obj.endomorphism_props.matrix_col2

        bpy.data.objects.remove(obj, do_unlink=True)
        new_sphere.name = old_name

        self.report({'INFO'}, "Sphere recreated")
        return {'FINISHED'}

# --- Свойства эндоморфизма ---


class EndomorphismProperties(bpy.types.PropertyGroup):
    """
    Свойства линейного оператора (эндоморфизма), включая UUID, матрицу, радиус и параметры сферы.
    """
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
    """
    Оператор для создания нового линейного оператора (эндоморфизма) в виде сферы.
    """
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
        # Создаём сферу-оператор с заданными параметрами
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=1, segments=self.segments_amount, ring_count=self.rings_amount, location=(0, 0, 0))
        sphere = bpy.context.active_object
        sphere.display_type = 'WIRE'
        sphere.name = "Endomorphism"
        sphere.scale = (self.radius, self.radius, self.radius)

        # Инициализация свойств PropertyGroup
        sphere.endomorphism_props.uuid = str(uuid.uuid4())
        sphere.endomorphism_props.is_endomorphism = True
        sphere.endomorphism_props.matrix_col0 = self.matrix_col0
        sphere.endomorphism_props.matrix_col1 = self.matrix_col1
        sphere.endomorphism_props.matrix_col2 = self.matrix_col2
        sphere.endomorphism_props.radius = self.radius
        sphere.endomorphism_props.segments_amount = self.segments_amount
        sphere.endomorphism_props.rings_amount = self.rings_amount

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
    """
    Панель свойств для выбранного эндоморфизма (отображается только для объектов-операторов).
    """
    bl_label = "Properties"
    bl_idname = 'Endomorphism_PT_Panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Endomorphism"

    @classmethod
    def poll(cls, context):
        obj = context.object
        # Панель показывается только для объектов с PropertyGroup эндоморфизма
        is_great = obj is not None and hasattr(
            obj, "endomorphism_props") and getattr(obj.endomorphism_props, "is_endomorphism", False)
        return is_great

    def draw(self, context):
        layout = self.layout
        obj = context.object
        props = obj.endomorphism_props

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
    """
    Добавляет пункт создания эндоморфизма в меню Shift+A → Mesh.
    """
    self.layout.operator(AddEndomorphismObject.bl_idname, icon='SPHERE')

# --- Регистрация классов и свойств ---


def register():
    bpy.utils.register_class(RecreateEndomorphismObject)
    bpy.utils.register_class(EndomorphismProperties)
    bpy.utils.register_class(AddEndomorphismObject)
    bpy.utils.register_class(Endomorphism_PT_PANEL)
    bpy.types.Object.endomorphism_props = PointerProperty(
        type=EndomorphismProperties)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)
    bpy.app.handlers.frame_change_post.append(update_all_endomorphisms)


def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    bpy.utils.unregister_class(RecreateEndomorphismObject)
    bpy.utils.unregister_class(EndomorphismProperties)
    bpy.utils.unregister_class(AddEndomorphismObject)
    bpy.utils.unregister_class(Endomorphism_PT_PANEL)
    del bpy.types.Object.endomorphism_props
    if update_all_endomorphisms in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(update_all_endomorphisms)


if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
