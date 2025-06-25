import bpy
from bpy.props import FloatVectorProperty, BoolProperty, EnumProperty, PointerProperty, StringProperty, IntProperty
from bpy.types import Context, Event
import mathutils

# --- Вспомогательные функции ---


def force_ui_redraw(context):
    """
    Принудительно перерисовывает 3D Viewport для немедленного обновления UI.
    """
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def find_endomorphism_by_uuid(uuid):
    """
    Поиск объекта-оператора по UUID среди всех объектов сцены.
    Возвращает объект-оператор или None.
    """
    for obj in bpy.data.objects:
        if hasattr(obj, "endomorphism_props") and getattr(obj.endomorphism_props, "uuid", None) == uuid:
            return obj
    return None


def is_point_inside_sphere(point, sphere_center, sphere_radius):
    """
    Проверяет, находится ли точка внутри сферы с заданным центром и радиусом.
    """
    return (point - sphere_center).length_squared <= sphere_radius * sphere_radius


def apply_endomorphisms(vector_obj):
    """
    Применяет все эндоморфизмы к вектору по порядку, если вектор находится внутри сферы действия оператора.
    Возвращает преобразованный вектор.
    """
    props = vector_obj.vector_props
    vec = mathutils.Vector(props.vector_end)
    for applied_op in props.applied_endomorphisms:
        endomorphism_obj = find_endomorphism_by_uuid(
            applied_op.endomorphism_uuid)
        if not endomorphism_obj:
            continue
        endomorphism_props = endomorphism_obj.endomorphism_props
        sphere_center = endomorphism_obj.location
        sphere_radius = endomorphism_props.radius
        if is_point_inside_sphere(vec, sphere_center, sphere_radius):
            mat = mathutils.Matrix((
                endomorphism_props.matrix_col0,
                endomorphism_props.matrix_col1,
                endomorphism_props.matrix_col2
            )).transposed()
            vec = mat @ vec
    return vec

# --- Функции обновления координат вектора ---


def update_vector_end(self, context):
    """
    Обновляет положение точки или стрелки вектора при изменении координат или применённых операторов.
    """
    obj = self.id_data
    transformed_end = apply_endomorphisms(obj)
    if self.vector_type == 'POINT':
        if obj.type == 'MESH':
            mesh = obj.data
            mesh.vertices[0].co = transformed_end
    elif self.vector_type == 'ARROW':
        obj.location = (0, 0, 0)
        vec = transformed_end
        obj.rotation_mode = 'QUATERNION'
        if vec.length > 0:
            obj.rotation_quaternion = vec.to_track_quat('Z', 'Y')
        obj.scale = (1, 1, vec.length)


def update_all_vectors(scene):
    """
    Обработчик кадра: обновляет все векторы на каждом кадре (для поддержки анимации и динамики).
    """
    for obj in bpy.data.objects:
        if hasattr(obj, "vector_props") and getattr(obj.vector_props, "is_vector", False):
            props = obj.vector_props
            transformed_end = apply_endomorphisms(obj)
            if props.vector_type == 'POINT' and obj.type == 'MESH':
                if obj.data.vertices:
                    obj.data.vertices[0].co = transformed_end
            elif props.vector_type == 'ARROW' and obj.type == 'EMPTY':
                obj.location = (0, 0, 0)
                if transformed_end.length > 0:
                    obj.rotation_mode = 'QUATERNION'
                    obj.rotation_quaternion = transformed_end.to_track_quat(
                        'Z', 'Y')
                obj.scale = (1, 1, transformed_end.length)

# --- Вспомогательные функции для UI ---


def get_operator_items(self, context):
    """
    Формирует список эндоморфизмов для выпадающего меню выбора (EnumProperty).
    """
    items = []
    for obj in bpy.data.objects:
        if hasattr(obj, "endomorphism_props") and obj.endomorphism_props.uuid:
            items.append((obj.endomorphism_props.uuid, obj.name, ""))
    return items

# --- PropertyGroup для одного применённого эндоморфизма ---


class VectorAppliedEndomorphism(bpy.types.PropertyGroup):
    """
    Свойства одного применённого к вектору эндоморфизма (ссылка по UUID).
    """
    endomorphism_uuid: bpy.props.StringProperty(
        name="Endomorphism UUID"
    )

# --- Основные свойства вектора ---


class VectorProperties(bpy.types.PropertyGroup):
    """
    Свойства вектора: тип, координаты конца, список применённых эндоморфизмов.
    """
    is_vector: bpy.props.BoolProperty(
        name="Is Vector object", default=False
    )
    vector_end: FloatVectorProperty(
        name="Vector End",
        description="Coordinates of the vector end point",
        default=(0, 0, 0),
        subtype='TRANSLATION',
        update=update_vector_end
    )
    vector_type: bpy.props.EnumProperty(
        name="Vector Type",
        items=[('POINT', "Point", ""), ('ARROW', "Arrow", "")],
        default='POINT'
    )
    applied_endomorphisms: bpy.props.CollectionProperty(
        type=VectorAppliedEndomorphism)
    applied_endomorphisms_index: bpy.props.IntProperty(default=-1)

# --- Оператор создания нового вектора ---


class AddVectorObject(bpy.types.Operator):
    """
    Оператор для создания нового вектора (точки или стрелки) в сцене.
    """
    bl_idname = "mesh.add_vector_object"
    bl_label = "Vector"
    bl_options = {'REGISTER', 'UNDO'}

    vector_end: bpy.props.FloatVectorProperty(
        name="Vector End",
        subtype='TRANSLATION',
        default=(1.0, 0.0, 0.0)
    )
    vector_type: bpy.props.EnumProperty(
        name="Vector Type",
        items=[('POINT', "Point", ""), ('ARROW', "Arrow", "")],
        default='POINT'
    )

    def execute(self, context: Context):
        # Создаём объект вектора (точка или стрелка)
        if self.vector_type == 'POINT':
            verts = [self.vector_end]
            edges = []
            faces = []
            mesh = bpy.data.meshes.new("PointMesh")
            mesh.from_pydata(verts, edges, faces)
            mesh.update()
            obj = bpy.data.objects.new("VectorPoint", mesh)
        elif self.vector_type == 'ARROW':
            obj = bpy.data.objects.new("VectorArrow", None)
            obj.empty_display_type = 'SINGLE_ARROW'
            obj.empty_display_size = 1
            obj.location = (0, 0, 0)
            direction = self.vector_end
            vec = mathutils.Vector(direction)
            obj.rotation_mode = 'QUATERNION'
            if vec.length > 0:
                obj.rotation_quaternion = vec.to_track_quat('Z', 'Y')
            obj.scale = (1, 1, direction.length)
        context.collection.objects.link(obj)
        # Инициализация свойств PropertyGroup
        obj.vector_props.is_vector = True
        obj.vector_props.vector_type = self.vector_type
        obj.vector_props.vector_end = self.vector_end
        self.report({'INFO'}, f"Vector created to {self.vector_end}")
        return {'FINISHED'}

    def invoke(self, context: Context, event: Event):
        return context.window_manager.invoke_props_dialog(self)

# --- Операторы для управления списком эндоморфизмов в векторе ---


class VECTOR_OT_add_endomorphism(bpy.types.Operator):
    """
    Оператор для добавления эндоморфизма к вектору через диалог выбора.
    """
    bl_idname = "vector.add_endomorphism"
    bl_label = "Add Endomorphism"
    bl_options = {'REGISTER', 'UNDO'}

    endomorphism_uuid: bpy.props.EnumProperty(
        name="Endomorphism",
        description="Choose an Endomorphism",
        items=get_operator_items
    )

    def execute(self, context):
        vector_props = context.object.vector_props
        new_op = vector_props.applied_endomorphisms.add()
        new_op.endomorphism_uuid = self.endomorphism_uuid
        vector_props.applied_endomorphisms_index = len(
            vector_props.applied_endomorphisms) - 1
        update_vector_end(context.object.vector_props, context)
        force_ui_redraw(context)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "endomorphism_uuid")

    def invoke(self, context, event):
        if not get_operator_items(self, context):
            self.report({'WARNING'}, "No Endomorphisms in the scene")
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self)


class VECTOR_OT_remove_endomorphism(bpy.types.Operator):
    """
    Оператор для удаления выбранного эндоморфизма из списка вектора.
    """
    bl_idname = "vector.remove_endomorphism"
    bl_label = "Remove Endomorphism"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        vector_props = context.object.vector_props
        index = vector_props.applied_endomorphisms_index
        if index >= 0:
            vector_props.applied_endomorphisms.remove(index)
            vector_props.applied_endomorphisms_index = min(
                index, len(vector_props.applied_endomorphisms) - 1)
        update_vector_end(context.object.vector_props, context)
        force_ui_redraw(context)
        return {'FINISHED'}


class VECTOR_OT_move_endomorphism(bpy.types.Operator):
    """
    Оператор для изменения порядка эндоморфизмов в списке (вверх/вниз).
    """
    bl_idname = "vector.move_endomorphism"
    bl_label = "Move Endomorphism"
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.EnumProperty(
        items=[('UP', 'Up', ''), ('DOWN', 'Down', '')])

    def execute(self, context):
        vector_props = context.object.vector_props
        index = vector_props.applied_endomorphisms_index
        new_index = index + (1 if self.direction == 'DOWN' else -1)
        if 0 <= new_index < len(vector_props.applied_endomorphisms):
            vector_props.applied_endomorphisms.move(index, new_index)
            vector_props.applied_endomorphisms_index = new_index
        update_vector_end(context.object.vector_props, context)
        force_ui_redraw(context)
        return {'FINISHED'}

# --- UIList для отображения и управления списком эндоморфизмов ---


class VECTOR_UL_endomorphisms_list(bpy.types.UIList):
    """
    Отображает список применённых к вектору эндоморфизмов в панели.
    """

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index=0, flt_flag=0):
        endomorphism_uuid = item.endomorphism_uuid
        endomorphism_obj = next((obj for obj in bpy.data.objects
                                 if hasattr(obj, "endomorphism_props") and
                                 obj.endomorphism_props.uuid == endomorphism_uuid), None)
        if endomorphism_obj:
            layout.label(text=endomorphism_obj.name)
        else:
            layout.label(text="Unknown Endomorphism")

# --- Панель свойств для векторов ---


class Vector_PT_Panel(bpy.types.Panel):
    """
    Панель свойств для выбранного вектора (точки или стрелки).
    """
    bl_label = "Properties"
    bl_idname = "Vector_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vector"

    @classmethod
    def poll(cls, context):
        obj = context.object
        is_great = obj is not None and hasattr(obj, "vector_props") and getattr(
            obj.vector_props, "is_vector", False)
        return is_great

    def draw(self, context):
        layout = self.layout
        obj = context.object
        props = obj.vector_props

        col = layout.column(align=True)
        col.label(text='Coordinates')
        col.prop(props, "vector_end", index=0, text="X")
        col.prop(props, "vector_end", index=1, text="Y")
        col.prop(props, "vector_end", index=2, text="Z")

        layout.separator()
        layout.label(text="Applied Endomorphisms:")
        row = layout.row()
        row.template_list(
            "VECTOR_UL_endomorphisms_list",
            "",
            context.object.vector_props,
            "applied_endomorphisms",
            context.object.vector_props,
            "applied_endomorphisms_index"
        )
        col = row.column(align=True)
        col.operator("vector.add_endomorphism", icon='ADD', text="")
        col.operator("vector.remove_endomorphism", icon='REMOVE', text="")
        col.operator("vector.move_endomorphism",
                     icon='TRIA_UP', text="").direction = 'UP'
        col.operator("vector.move_endomorphism",
                     icon='TRIA_DOWN', text="").direction = 'DOWN'

# --- Добавление вектора в меню создания объектов ---


def menu_func(self, context):
    """
    Добавляет пункт создания вектора в меню Shift+A → Mesh.
    """
    self.layout.operator(AddVectorObject.bl_idname, icon='EMPTY_SINGLE_ARROW')

# --- Регистрация классов и свойств ---


def register():
    bpy.utils.register_class(VECTOR_UL_endomorphisms_list)
    bpy.utils.register_class(VECTOR_OT_add_endomorphism)
    bpy.utils.register_class(VECTOR_OT_remove_endomorphism)
    bpy.utils.register_class(VECTOR_OT_move_endomorphism)
    bpy.utils.register_class(VectorAppliedEndomorphism)
    bpy.utils.register_class(VectorProperties)
    bpy.utils.register_class(AddVectorObject)
    bpy.utils.register_class(Vector_PT_Panel)
    bpy.types.Object.vector_props = PointerProperty(type=VectorProperties)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)
    bpy.app.handlers.frame_change_post.append(update_all_vectors)


def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    bpy.utils.unregister_class(VECTOR_UL_endomorphisms_list)
    bpy.utils.unregister_class(VECTOR_OT_add_endomorphism)
    bpy.utils.unregister_class(VECTOR_OT_remove_endomorphism)
    bpy.utils.unregister_class(VECTOR_OT_move_endomorphism)
    bpy.utils.unregister_class(VectorAppliedEndomorphism)
    bpy.utils.unregister_class(Vector_PT_Panel)
    bpy.utils.unregister_class(AddVectorObject)
    bpy.utils.unregister_class(VectorProperties)
    del bpy.types.Object.vector_props
    if update_all_vectors in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(update_all_vectors)


if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
