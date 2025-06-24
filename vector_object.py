import bpy
from bpy.props import FloatVectorProperty, BoolProperty, EnumProperty, PointerProperty
from bpy.types import Context, Event
from typing import Literal
import mathutils


# Функция для изменения координат вектора при их изменении в панели свойств.
def update_vector_end(self, context):
    obj = self.id_data  # объект, к которому привязаны свойства

    # Обновляем положение точки
    if self.vector_type == 'POINT':
        if obj.type == 'MESH':
            mesh = obj.data
            mesh.vertices[0].co = self.vector_end
    # Обновляем направление и длину стрелки
    elif self.vector_type == 'ARROW':
        obj.location = (0, 0, 0)
        vec = mathutils.Vector(self.vector_end)
        obj.rotation_mode = 'QUATERNION'
        if vec.length > 0:
            obj.rotation_quaternion = vec.to_track_quat('Z', 'Y')
        obj.scale = (1, 1, vec.length)


# Функция для изменения кординат при анимации сцены.
def update_all_vectors(scene):
    for obj in bpy.data.objects:  # Перебираем все объекты и выбираем только наши вектора по свойству is_vector
        if hasattr(obj, "vector_props") and getattr(obj.vector_props, "is_vector", False):  # type: ignore
            props = obj.vector_props  # type: ignore
            # Для точки
            if props.vector_type == 'POINT' and obj.type == 'MESH':
                if obj.data.vertices:  # type: ignore
                    # Изменяем координату конца - единственной точки меша
                    obj.data.vertices[0].co = props.vector_end  # type: ignore
            # Для стрелки - пересчёт направления
            elif props.vector_type == 'ARROW' and obj.type == 'EMPTY':
                obj.location = (0, 0, 0)
                vec = mathutils.Vector(props.vector_end)
                obj.rotation_mode = 'QUATERNION'
                if vec.length > 0:
                    obj.rotation_quaternion = vec.to_track_quat('Z', 'Y')
                obj.scale = (1, 1, vec.length)


# Класс с кастомными свойствами
class VectorProperties(bpy.types.PropertyGroup):
    is_vector: bpy.props.BoolProperty(
        name="Is Vector object", default=False
    )
    vector_end: FloatVectorProperty(
        name="Vector End",
        description="Coordinates of the vector end point",
        default=(0, 0, 0),
        subtype='TRANSLATION',
        # Функция для обновления координат вектора при изменении в панели свойств
        update=update_vector_end
    )
    vector_type: bpy.props.EnumProperty(
        name="Vector Type",
        items=[('POINT', "Point", ""), ('ARROW', "Arrow", "")],
        default='POINT'
    )


class AddVectorObject(bpy.types.Operator):
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

            # Поворот и масштабирование стрелки
            direction = self.vector_end
            vec = mathutils.Vector(direction)
            obj.rotation_mode = 'QUATERNION'
            if vec.length > 0:
                obj.rotation_quaternion = vec.to_track_quat('Z', 'Y')
            obj.scale = (1, 1, direction.length)

        context.collection.objects.link(obj)

        # Инициализация свойств
        obj.vector_props.is_vector = True  # type: ignore
        obj.vector_props.vector_type = self.vector_type  # type: ignore
        obj.vector_props.vector_end = self.vector_end  # type: ignore

        self.report({'INFO'}, f"Vector created to {self.vector_end}")
        return {'FINISHED'}

    def invoke(self, context: Context, event: Event):
        return context.window_manager.invoke_props_dialog(self)


# Панель, которая показывает свойства только для векторов
class Vector_PT_Panel(bpy.types.Panel):
    bl_label = "Properties"
    bl_idname = "Vector_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vector"

    # Blender в данной функции требует подать класс cls, а ни экземпляр self.
    @classmethod
    def poll(cls, context):
        obj = context.object
        # Выбран ли объект
        # Имеет ли он атрибут vector_props (например, у старых объектов сцены их не будет, как и у некоторых "нетипичных" объектов)
        # Вектора ли это (по флажку is_vector)
        is_great = obj is not None and hasattr(
            obj, "vector_props") and obj.vector_props.is_vector  # type: ignore
        return is_great

    def draw(self, context):
        layout = self.layout
        obj = context.object
        props = obj.vector_props  # type: ignore

        # Создаём колонку. aling говорит, что элементы будут плотно прилегать друг к другу
        col = layout.column(align=True)
        col.label(text='Coordinates')
        # Далее разбиваем одно свойство на 3 поля по index
        col.prop(props, "vector_end", index=0, text="X")
        col.prop(props, "vector_end", index=1, text="Y")
        col.prop(props, "vector_end", index=2, text="Z")


# Отображение нового типа в панели создания объектов (shift + A)
def menu_func(self, context):
    self.layout.operator(AddVectorObject.bl_idname,
                         icon='EMPTY_SINGLE_ARROW')


def register():
    bpy.utils.register_class(VectorProperties)
    bpy.utils.register_class(AddVectorObject)
    bpy.utils.register_class(Vector_PT_Panel)
    bpy.types.Object.vector_props = PointerProperty(  # type: ignore
        type=VectorProperties)  # type: ignore
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)
    bpy.app.handlers.frame_change_post.append(update_all_vectors)


def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    bpy.utils.unregister_class(Vector_PT_Panel)
    bpy.utils.unregister_class(AddVectorObject)
    bpy.utils.unregister_class(VectorProperties)
    del bpy.types.Object.vector_props  # type: ignore
    if update_vector_end in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(update_all_vectors)


if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
