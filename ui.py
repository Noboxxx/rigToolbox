from functools import partial

try:
    from PySide6.QtCore import *
    from PySide6.QtWidgets import *
    from PySide6.QtGui import *
except ModuleNotFoundError:
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *

from .core import *
from .utils import *

from maya import cmds

class CreateJointsOnCurve(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Create joints on curve')
        self.resize(500, 500)

        self.name_line = QLineEdit()
        self.name_line.setPlaceholderText('default')

        self.n_joints_spin = QSpinBox()
        self.n_joints_spin.setMinimum(1)
        self.n_joints_spin.setValue(5)

        ok_btn = QPushButton('Create')
        ok_btn.clicked.connect(self.create_joints_on_curve)

        form_layout = QFormLayout()
        form_layout.addRow('name', self.name_line)
        form_layout.addRow('n joints', self.n_joints_spin)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def create_joints_on_curve(self):
        name = self.name_line.text() or self.name_line.placeholderText()
        n_joints = self.n_joints_spin.value()

        create_joints_on_selected_curve(n_joints, name)


class RigToolbox(DockableWidget):

    def __init__(self, parent=None):
        if parent is None:
            parent = get_maya_window()
        super().__init__(parent)

        self.setWindowTitle('Rig Toolbox')
        self.resize(500, 700)

        # utils
        matrix_constraint_btn = QPushButton('create matrix constraint')
        matrix_constraint_btn.clicked.connect(create_matrix_constraint_on_selected)

        create_locator_on_gizmo_btn = QPushButton('create locator on gizmo')
        create_locator_on_gizmo_btn.clicked.connect(create_locator_on_gizmo)

        split_bone_btn = QPushButton('split bone')
        def split_bone_func():
            sections = self.split_bone_sections_spin.value()
            split_bone(sections)
        split_bone_btn.clicked.connect(split_bone_func)

        self.split_bone_sections_spin = QSpinBox()
        self.split_bone_sections_spin.setValue(4)

        split_bone_layout = QHBoxLayout()
        split_bone_layout.addWidget(split_bone_btn)
        split_bone_layout.addWidget(self.split_bone_sections_spin)

        joints_on_curve_btn = QPushButton('create joints on curve')
        def joints_on_curve_btn_func():
            ui = CreateJointsOnCurve(self)
            ui.show()
        joints_on_curve_btn.clicked.connect(joints_on_curve_btn_func)

        self.joints_on_curve_spin = QSpinBox()
        self.joints_on_curve_spin.setValue(4)

        utils_layout = QVBoxLayout()
        utils_layout.addWidget(matrix_constraint_btn)
        utils_layout.addWidget(create_locator_on_gizmo_btn)
        utils_layout.addWidget(joints_on_curve_btn)
        utils_layout.addLayout(split_bone_layout)

        # display
        joint_size_up_btn = QPushButton('+')
        joint_size_up_btn.clicked.connect(scale_joints_up)

        joint_size_down_btn = QPushButton('-')
        joint_size_down_btn.clicked.connect(scale_joints_down)

        joint_size_layout = QGridLayout()
        joint_size_layout.addWidget(QLabel('Joint Size'), 0, 0)
        joint_size_layout.addWidget(joint_size_down_btn, 1, 0)
        joint_size_layout.addWidget(joint_size_up_btn, 1, 1)

        toggle_mesh_btn = QPushButton()
        toggle_mesh_btn.clicked.connect(partial(toggle, 'polymeshes'))
        toggle_mesh_btn.setToolTip('mesh')
        toggle_mesh_btn.setIcon(QIcon(':polyCube.png'))

        toggle_joint_btn = QPushButton()
        toggle_joint_btn.clicked.connect(partial(toggle, 'joints'))
        toggle_joint_btn.setToolTip('joint')
        toggle_joint_btn.setIcon(QIcon(':joint.svg'))

        toggle_ctrl_btn = QPushButton()
        toggle_ctrl_btn.clicked.connect(partial(toggle, 'nurbsCurves'))
        toggle_ctrl_btn.setToolTip('ctrl')
        toggle_ctrl_btn.setIcon(QIcon(':circle.png'))

        toggle_wireframe_btn = QPushButton()
        toggle_wireframe_btn.clicked.connect(partial(toggle, 'wireframeOnShaded'))
        toggle_wireframe_btn.setToolTip('wireframe')
        toggle_wireframe_btn.setIcon(QIcon(':cube.png'))

        toggle_layout = QGridLayout()
        toggle_layout.addWidget(QLabel('Toggle'), 0, 0)
        toggle_layout.addWidget(toggle_ctrl_btn, 1, 0)
        toggle_layout.addWidget(toggle_joint_btn, 1, 1)
        toggle_layout.addWidget(toggle_mesh_btn, 1, 2)
        toggle_layout.addWidget(toggle_wireframe_btn, 1, 3)

        display_layout = QVBoxLayout()
        display_layout.addLayout(joint_size_layout)
        display_layout.addLayout(toggle_layout)

        # windows
        def controller_editor_func():
            from controllerEditor.ui import open_controller_editor
            open_controller_editor()
        controller_editor_btn = QPushButton('Controller Editor')
        controller_editor_btn.clicked.connect(controller_editor_func)

        node_editor_btn = QPushButton('Node Editor')
        node_editor_btn.clicked.connect(cmds.NodeEditorWindow)

        script_editor_btn = QPushButton('Script Editor')
        script_editor_btn.clicked.connect(cmds.ScriptEditor)

        def multi_skin_editor_func():
            from multiSkinEditor.ui import open_multi_skin_editor
            open_multi_skin_editor()
        multi_skin_editor_btn = QPushButton('Multi-Skin Editor')
        multi_skin_editor_btn.clicked.connect(multi_skin_editor_func)

        windows_layout = QGridLayout()
        windows_layout.addWidget(node_editor_btn, 0, 0)
        windows_layout.addWidget(script_editor_btn, 0, 1)
        windows_layout.addWidget(controller_editor_btn, 1, 0)
        windows_layout.addWidget(multi_skin_editor_btn, 1, 1)

        # main layout
        display_label = QLabel('Display')
        display_label.setStyleSheet('font-weight: bold;')

        utils_label = QLabel('Utils')
        utils_label.setStyleSheet('font-weight: bold;')

        windows_label = QLabel('Windows')
        windows_label.setStyleSheet('font-weight: bold;')

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(display_label)
        main_layout.addLayout(display_layout)
        main_layout.addWidget(utils_label)
        main_layout.addLayout(utils_layout)
        main_layout.addWidget(windows_label)
        main_layout.addLayout(windows_layout)


def open_rig_toolbox():
    RigToolbox.open_in_workspace()