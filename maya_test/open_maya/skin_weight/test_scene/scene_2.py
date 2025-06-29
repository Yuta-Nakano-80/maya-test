"""

シーン2

同名ノードを含まない

import importlib
from maya_test.test_scene import scene_2
importlib.reload(scene_2)
scene_2.main()

"""
import time
from maya import cmds
import importlib

from maya_test.open_maya.skin_weight.modules import concentration_skin_weight


def create_cylinder(root_name, z=0, x=0):
    ch_id = root_name[:4]

    # ルートの作成
    root_group = cmds.group(em=True, name=root_name, world=True)
    mesh_group = cmds.group(em=True, name="MESH", world=True)

    count = 20
    if ch_id == 'ch03':
        count = 40
    parent = mesh_group
    for i in range(count):
        name = '{}_cylinder_{}'.format(ch_id, i + 1)
        cylinder = cmds.polyCylinder(n=name, radius=1.0, sy=100, h=5, subdivisionsAxis=50)[0]
        cmds.rotate(90, 0, 0, cylinder)
        cmds.move(0, 0, -2.5, cylinder)
        cmds.move(0, 0, -1 * 5 * i, cylinder, relative=True)
        cmds.delete(cylinder, ch=True)
        cmds.parent(cylinder, parent)
        cylinder = '|' + name
        parent = parent + cylinder
    cmds.parent(mesh_group, root_group)
    cmds.move(x, 0, -1 * z, root_group, relative=True)

    for i in range(200):
        joint = cmds.joint(name="joint_{}".format(i), p=(x, 0, -1 * i))
        if i == 0:
            cmds.parent(joint, root_group)

    return root_group


def set_bind(root_group):
    """
    バインド
    """
    mesh_list = cmds.listRelatives(root_group, allDescendents=True, f=True, type='mesh')
    joint_list = cmds.listRelatives(root_group, allDescendents=True, f=True, type='joint')

    for mesh in mesh_list:
        cmds.skinCluster(joint_list, mesh)


def main():
    """
    シーン2
    """
    all_start = time.time()
    start = time.time()
    cmds.file(new=True, force=True)

    root_01 = create_cylinder('ch00_0000_0000')
    root_02 = create_cylinder('ch01_0000_0000', 100, 20)
    cmds.duplicate('|ch00_0000_0000|MESH')


    # リグモデルのルート
    rig_model_root_group = cmds.group(em=True, name='ch03_000_0000_rig_model', world=True)
    cmds.parent('|ch00_0000_0000|MESH1', rig_model_root_group)
    cmds.rename('|ch03_000_0000_rig_model|MESH1', 'MESH')
    root_01_cylinder_root = '|ch01_0000_0000|MESH|ch01_cylinder_1'
    cmds.duplicate(root_01_cylinder_root)
    last_ch_03_cylinder_list = cmds.listRelatives('|ch03_000_0000_rig_model', allDescendents=True, f=True, type='transform')
    cmds.parent('|ch01_0000_0000|MESH|ch01_cylinder_21', w=True)
    cmds.move(-20, 0, 0, '|ch01_cylinder_21', relative=True)
    cmds.rename('|ch01_cylinder_21', 'ch01_cylinder_1')
    cmds.parent('|ch01_cylinder_1', last_ch_03_cylinder_list[-2])

    root_00_joint_root = cmds.listRelatives('|ch00_0000_0000', allDescendents=True, f=True, type='joint')
    cmds.duplicate(root_00_joint_root)
    cmds.parent('|ch00_0000_0000|joint_200', rig_model_root_group)
    cmds.rename('|ch03_000_0000_rig_model|joint_200', 'joint_0')

    cmds.move(40, 0, 0, rig_model_root_group)

    end = time.time()
    print(f"メッシュ・ジョイント構築 : {end - start:.4f} 秒")

    start = time.time()
    for root in [root_01, root_02, rig_model_root_group]:
        set_bind(root)
    end = time.time()
    print(f"バインド : {end - start:.4f} 秒")

    importlib.reload(concentration_skin_weight)
    concentration_skin_weight.main('|ch03_000_0000_rig_model|MESH|ch00_cylinder_1|ch00_cylinder_2|ch00_cylinder_3', '|ch03_000_0000_rig_model|joint_0|joint_1|joint_2|joint_3|joint_4|joint_5|joint_6|joint_7|joint_8')

    end = time.time()
    print(f"シーン構築処理全体 : {end - all_start:.4f} 秒")
