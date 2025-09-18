from PySide6.QtWidgets import *
from shiboken6 import wrapInstance

from maya import OpenMayaUI, cmds

def get_maya_window():
    pointer = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(pointer), QMainWindow)

class Chunk:

    def __init__(self, name='untitled'):
        self.name = str(name)

    def __enter__(self):
        cmds.undoInfo(openChunk=True, chunkName=self.name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        cmds.undoInfo(closeChunk=True)

def chunk(func):
    def wrapper(*args, **kwargs):
        with Chunk(name=func.__name__):
            return func(*args, **kwargs)

    return wrapper


def blend_vector(vector_a, vector_b, blender):

    vector_c = list()

    for a, b in zip(vector_a, vector_b):
        c = a * (1 - blender) + b * blender
        vector_c.append(c)

    return vector_c