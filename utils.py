import inspect
import random
import string

try:
    from PySide6.QtCore import *
    from PySide6.QtWidgets import *
    from PySide6.QtGui import *
    from shiboken6 import wrapInstance
except ModuleNotFoundError:
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from shiboken2 import wrapInstance


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

class DockableWidget(QWidget):

    def __init__(self, parent=None):
        if parent is None:
            parent = get_maya_window()
        super().__init__(parent)

        self.id = ''.join(random.choice(string.ascii_uppercase) for _ in range(4))

        class_name = self.__class__.__name__
        object_name = f'{class_name}_{self.id}'

        self.setObjectName(object_name)

    @classmethod
    def open_in_workspace(cls, workspace_name=None):
        # widget
        widget = cls()
        widget_pointer = OpenMayaUI.MQtUtil.findControl(widget.objectName())

        # workspace
        if workspace_name is None:
            # create workspace control
            workspace_name = cmds.workspaceControl(
                f'{widget.objectName()}_workspaceControl',
                initialWidth=widget.width(),
                initialHeight=widget.height(),
                label=widget.windowTitle(),
            )

            # ui script
            module_name = inspect.getmodule(widget).__name__
            class_name = widget.__class__.__name__

            command = f'import {module_name}; {module_name}.{class_name}.open_in_workspace({workspace_name!r})'
            command = f'cmds.evalDeferred({command!r}, lowestPriority=True)'

            cmds.workspaceControl(workspace_name, e=True, uiScript=command)

        workspace_control = OpenMayaUI.MQtUtil.findControl(workspace_name)

        # parent widget to workspace control
        OpenMayaUI.MQtUtil.addWidgetToMayaLayout(int(widget_pointer), int(workspace_control))

        return widget
