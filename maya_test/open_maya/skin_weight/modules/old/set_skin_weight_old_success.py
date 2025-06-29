"""

スキンウェイトのセット

成功したが遅い

import importlib
from maya_test.open_maya.skin_weight import set_skin_weight
importlib.reload(set_skin_weight)
set_skin_weight.test()


"""
import importlib
import time

import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaAnim as oma

from maya_test.open_maya.skin_weight.modules import get_skin_weight


def main(weight_data, target_root):
    """
    Args:
        weight_data: { 'mesh.vtx[0]' : { 'joint' : weight, ... }, ... }
        target_root: 割り当て側のルートノード
    """

    start = time.time()

    # メッシュごとのデータに整理
    mesh_weight_map = {}
    for vtx, weights in weight_data.items():
        mesh_name, vtx_info = vtx.split('.vtx')
        mesh_name = mesh_name.strip()
        if mesh_name not in mesh_weight_map:
            mesh_weight_map[mesh_name] = {}
        mesh_weight_map[mesh_name][vtx] = weights

    # 複製側メッシュの取得
    mesh_shapes = cmds.listRelatives(target_root, allDescendents=True, type='mesh', f=True) or []
    mesh_shapes = [m for m in mesh_shapes if not cmds.getAttr(m + ".intermediateObject")]

    for mesh_shape in mesh_shapes:
        mesh_transform = cmds.listRelatives(mesh_shape, parent=True, fullPath=True)[0]

        # 元のメッシュと名前末尾が一致するか検索
        matched_original = None
        for original_mesh in mesh_weight_map.keys():
            if mesh_transform.split('|')[-1] == original_mesh.split('|')[-1]:
                matched_original = original_mesh
                break

        if not matched_original:
            print(f"スキン情報なし: {mesh_transform}")
            continue

        vtx_weights = mesh_weight_map[matched_original]

        # ジョイントの一覧を取得（このメッシュに関係するすべてのジョイント）
        # joints = set()
        # for w in vtx_weights.values():
        #     joints.update(w.keys())
        # joints = list(joints)

        # スキンクラスターの取得
        # skin_cluster = cmds.skinCluster(joints, mesh_transform, tsb=True, normalizeWeights=1, maximumInfluences=5)[0]
        history = cmds.listHistory(mesh_transform)
        skin_cluster_list = cmds.ls(history, type='skinCluster')
        if not skin_cluster_list:
            continue
        else:
            skin_cluster = skin_cluster_list[0]

        # OpenMaya の初期化
        sel_list = om.MSelectionList()
        sel_list.add(mesh_shape)
        dag_path = om.MDagPath()
        sel_list.getDagPath(0, dag_path)

        sel_list.clear()
        sel_list.add(skin_cluster)
        skin_obj = om.MObject()
        sel_list.getDependNode(0, skin_obj)
        fn_skin = oma.MFnSkinCluster(skin_obj)

        # インフルエンスジョイントと index の対応を構築
        inf_paths = om.MDagPathArray()
        fn_skin.influenceObjects(inf_paths)
        joint_index_map = {}
        for i in range(inf_paths.length()):
            joint_name = inf_paths[i].fullPathName()
            index = fn_skin.indexForInfluenceObject(inf_paths[i])
            joint_index_map[joint_name] = index

        # 各頂点にウェイトを適用
        for vtx_full, joint_weights in vtx_weights.items():
            vtx_index = int(vtx_full.split('[')[-1].rstrip(']'))

            indices = om.MIntArray()
            indices.append(vtx_index)
            comp_fn = om.MFnSingleIndexedComponent()
            comp = comp_fn.create(om.MFn.kMeshVertComponent)
            comp_fn.addElements(indices)

            # joint index とウェイトの配列を準備
            weight_array = om.MDoubleArray()
            joint_indices = om.MIntArray()
            for joint, weight in joint_weights.items():
                if joint not in joint_index_map:
                    continue  # 一致するジョイントが見つからない
                joint_indices.append(joint_index_map[joint])
                weight_array.append(weight)

            fn_skin.setWeights(dag_path, comp, joint_indices, weight_array, False)

        # print(f"{mesh_transform} にウェイトを適用しました")

    end = time.time()
    print(f"ウェイト設定処理 : {end - start:.4f} 秒")


def test():
    from maya_test.open_maya.skin_weight.test_scene import scene_1
    importlib.reload(scene_1)
    scene_1.main()

    root_node = cmds.ls('|root')[0]


    weight_info = get_skin_weight.collect_skin_weights(root_node)

    main(weight_info, '|duplicate_root')


