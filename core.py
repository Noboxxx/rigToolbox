from maya import cmds
from maya.api import OpenMaya

from .utils import *


@chunk
def split_bone(sections=4):
    selection = cmds.ls(sl=True, type='joint')

    if len(selection) != 1:
        raise Exception(f'Please select exactly one joint. Got {len(selection)}')

    joint = selection[0]

    joint_children = cmds.listRelatives(joint, children=True, type='joint')

    if len(joint_children) != 1:
        raise Exception(f'Joint {joint!r} should have exactly one joint as a child. Got {len(selection)}')

    joint_child = joint_children[0]

    joint_translation = cmds.xform(joint, q=True, translation=True, worldSpace=True)

    joint_child_translation = cmds.xform(joint_child, q=True, translation=True, worldSpace=True)

    radius = cmds.getAttr(f'{joint}.radius')

    new_joint_parent = joint
    for index in range(sections - 1):
        cmds.select(new_joint_parent)
        blender = (index + 1) / sections

        translation = blend_vector(joint_translation, joint_child_translation, blender)
        new_joint = cmds.joint(position=translation, radius=radius)

        new_joint_parent = new_joint

    cmds.parent(joint_child, new_joint_parent)

    cmds.select(selection)

def scale_joints_down():
    size = cmds.jointDisplayScale(q=True)
    cmds.jointDisplayScale(size * .8)

def scale_joints_up():
    size = cmds.jointDisplayScale(q=True)
    cmds.jointDisplayScale(size * 1.2)

@chunk
def create_matrix_constraint(parent, child, maintain_offset=True, translation=True, rotation=True, scale=True, shear=True):
    # parent plug
    if '.' in parent:
        parent_plug = parent
    elif cmds.objectType(parent, isAType='transform'):
        parent_plug = f'{parent}.worldMatrix[0]'
    else:
        parent_plug = f'{parent}.outputMatrix[0]'
        if not cmds.objExists(parent_plug):
            raise Exception(f'plug {parent_plug!r} doesnt exist')

    # offset
    if maintain_offset:
        parent_world_matrix = cmds.getAttr(parent_plug)
        parent_world_inverse_matrix = OpenMaya.MMatrix(parent_world_matrix).inverse()

        child_world_matrix = cmds.getAttr(f'{child}.worldMatrix[0]')
        child_world_matrix = OpenMaya.MMatrix(child_world_matrix)

        offset_matrix = child_world_matrix * parent_world_inverse_matrix
    else:
        offset_matrix = OpenMaya.MMatrix()

    # mult
    mult_matrix_name = f'{child}_multMatrix'
    mult_matrix = cmds.createNode('multMatrix', name=mult_matrix_name)
    cmds.setAttr(f'{mult_matrix}.matrixIn[0]', offset_matrix, type='matrix')

    cmds.connectAttr(parent_plug, f'{mult_matrix}.matrixIn[1]')
    cmds.connectAttr(f'{child}.parentInverseMatrix[0]', f'{mult_matrix}.matrixIn[2]')

    # decompose
    decompose_matrix_name = f'{child}_decomposeMatrix'
    decompose_matrix = cmds.createNode('decomposeMatrix', name=decompose_matrix_name)
    cmds.connectAttr(f'{mult_matrix}.matrixSum', f'{decompose_matrix}.inputMatrix')

    attributes = list()
    if translation:
        attributes.append('translate')

    if rotation:
        attributes.append('rotate')

    if scale:
        attributes.append('scale')

    if shear:
        attributes.append('shear')

    for attr in attributes:
        cmds.connectAttr(f'{decompose_matrix}.output{attr.title()}', f'{child}.{attr}')

    # data
    data = {
        # params
        'parent': parent,
        'child': child,
        'maintain_offset': maintain_offset,
        'translation': translation,
        'rotation': rotation,
        'scale': scale,
        'shear': shear,

        # utils
        'parent_plug': parent_plug,
        'offset_matrix': offset_matrix,

        # created
        'mult_matrix': mult_matrix,
        'decompose_matrix': decompose_matrix,
    }
    return data

@chunk
def create_matrix_constraint_on_selected():
    selection = cmds.ls(sl=True)

    if len(selection) < 2:
        raise Exception(f'Selection must contain at least two transforms. Got {len(selection)}')

    parent = selection[0]
    children = selection[1:]

    for child in children:
        create_matrix_constraint(parent, child)

@chunk
def create_locator_on_gizmo():
    # gizmo
    active_context = cmds.currentCtx()
    if active_context == 'RotateSuperContext':
        position = cmds.manipRotateContext('Rotate', position=True, q=True)
    elif active_context == 'moveSuperContext':
        position = cmds.manipMoveContext('Move', position=True, q=True)
    elif active_context == 'scaleSuperContext':
        position = cmds.manipScaleContext('Scale', position=True, q=True)
    else:
        cmds.warning(f'Unable to find position for context {active_context!r}')
        position = None

    if not position:
        position = 0, 0, 0

    # locator
    locator, = cmds.spaceLocator(name='help_loc#')
    cmds.xform(locator, translation=position, worldSpace=True)

@chunk
def create_joints_on_curve(curve, n_joints=5, name='default'):
    held_selection = cmds.ls(sl=True)
    cmds.select(clear=True)

    joints = list()
    for index in range(n_joints):
        percentage = index / (n_joints - 1)
        position = cmds.pointOnCurve(curve, parameter=percentage, turnOnPercentage=True, position=True)

        joint = cmds.joint(position=position, name=f'{name}{index}_jnt')
        joints.append(joint)

    cmds.joint(
        joints[0],
        edit=True,
        orientJoint='xyz',
        secondaryAxisOrient='yup',
        children=True,
        zeroScaleOrient=True
    )

    cmds.setAttr(f'{joints[-1]}.jointOrient', 0, 0, 0)

    cmds.select(held_selection)

    return joints

@chunk
def create_joints_on_selected_curve(n_joints=5, name='default'):
    selection = cmds.ls(selection=True)
    if not selection:
        cmds.error("Please select a curve.")
        return

    for node in selection:
        if not cmds.objectType(node, isType='nurbsCurve'):
            curves = cmds.listRelatives(node, shapes=True, type='nurbsCurve')
            if not curves:
                raise Exception(f'Node {node!r} has no curve')
            curve = curves[0]
        else:
            curve = node

        create_joints_on_curve(curve, n_joints=n_joints, name=name)

def toggle(attr):
    # get
    panels = cmds.getPanel(allPanels=True)

    model_panels = list()
    for panel in panels:
        if cmds.modelEditor(panel, exists=True):
            model_panels.append(panel)

    get_kwargs = {
        'q': True,
        attr: True,
    }

    # set
    state = not cmds.modelEditor(model_panels[0], **get_kwargs)

    set_kwargs = {
        'e': True,
        attr: state,
    }

    for model_panel in model_panels:
        cmds.modelEditor(model_panel, **set_kwargs)