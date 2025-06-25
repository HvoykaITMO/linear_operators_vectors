from . import endomorphism
from . import vector_object
import importlib
bl_info = {
    "name": "Linear Operators and Vectors",
    "author": "HvoykaITMO",
    "version": (1, 0, 0),
    "blender": (4, 4, 3),
    "description": "Vectors and endomorphisms with their narrowing into subspaces",
    "category": "Object",
}


def register():
    vector_object.register()
    endomorphism.register()


def unregister():
    endomorphism.unregister()
    vector_object.unregister()
