"""

シーン1

import importlib
from maya_test.test_scene import scene_1
importlib.reload(scene_1)
scene_1.main()

"""
import time

from maya import cmds

def rebind_with_joint1_only():
    # duplicate_root 配下の joint1 を探す
    joints = cmds.listRelatives('duplicate_root', allDescendents=True, type='joint', f=True) or []
    target_joint = next((j for j in joints if j.endswith('joint_0')), None)

    if not target_joint:
        cmds.error("duplicate_root 以下に 'joint1' が見つかりません。")
        return

    meshes = cmds.listRelatives('duplicate_root', allDescendents=True, type='mesh', f=True) or []

    for mesh in meshes:
        if mesh.endswith('Orig'):
            continue

        transform = cmds.listRelatives(mesh, parent=True, f=True)[0]

        # 既存の skinCluster を削除
        existing_clusters = cmds.ls(cmds.listHistory(transform), type='skinCluster') or []
        for sc in existing_clusters:
            try:
                cmds.delete(sc)
            except Exception:
                pass

        # joint1 のみで再バインド
        cmds.skinCluster(target_joint, transform, tsb=True, nw=1, mi=1, omi=True)


def main(count=10):
    """

    Returns:
        length (int): 長さ

    """
    start = time.time()
    cmds.file(new=True, force=True)

    length = 10

    # ルートの作成
    root_group = cmds.group(em=True, name="root", world=True)
    mesh_group = cmds.group(em=True, name="mesh", world=True)
    for i in range(count):
        cylinder = cmds.polyCylinder(n='cylinder_{:000}'.format(i), sy=50, h=length, subdivisionsAxis=50)[0]
        cmds.rotate(90, 0, 0, cylinder)
        cmds.move(0, 0, length / 2 * i * -1)
        cmds.delete(cylinder, ch=True)
        cmds.parent(cylinder, mesh_group)
    cmds.parent(mesh_group, root_group)

    # ジョイントの作成
    joint_list = []
    joint_count = int(length / 2) * count
    for i in range(joint_count):
        position = length / 2 - 2 * i
        joint = cmds.joint(name="joint_{}".format(i), p=(0, 0, position))
        if i == 0:
            cmds.parent(joint, root_group)
        joint_list.append(joint)

    root_mesh_list = cmds.listRelatives(root_group, allDescendents=True, f=True, type='mesh')
    root_joint_list = cmds.listRelatives(root_group, allDescendents=True, f=True, type='joint')

    for root_mesh in root_mesh_list:
        cmds.skinCluster(root_joint_list, root_mesh)

    # 複製グループの作成
    duplicate_root = cmds.duplicate(root_group, n='duplicate_root')[0]
    cmds.move(5, 0, 0, duplicate_root)

    duplicate_mesh_list = cmds.listRelatives(duplicate_root, allDescendents=True, f=True, type='mesh')
    duplicate_joint_list = cmds.listRelatives(duplicate_root, allDescendents=True, f=True, type='joint')

    for mesh in duplicate_mesh_list:
        cmds.delete(mesh, ch=True)
        if mesh.endswith('Orig'):
            continue
        cmds.skinCluster(duplicate_joint_list, mesh)

    rebind_with_joint1_only()


    end = time.time()
    print(f"シーン構築処理 : {end - start:.4f} 秒")
