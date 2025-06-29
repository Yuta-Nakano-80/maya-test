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

    # オリジナルメッシュのマップ（名前ベースで高速アクセス）
    name_to_original_map = {
        m.split('|')[-1]: m for m in mesh_weight_map
    }

    # 複製側メッシュの取得
    mesh_shapes = cmds.listRelatives(target_root, allDescendents=True, type='mesh', f=True) or []
    mesh_shapes = [m for m in mesh_shapes if not cmds.getAttr(m + ".intermediateObject")]

    for mesh_shape in mesh_shapes:
        mesh_transform = cmds.listRelatives(mesh_shape, parent=True, fullPath=True)[0]
        short_name = mesh_transform.split('|')[-1]
        matched_original = name_to_original_map.get(short_name)

        if not matched_original:
            print(f"スキン情報なし: {mesh_transform}")
            continue

        vtx_weights = mesh_weight_map[matched_original]

        # スキンクラスターの取得
        history = cmds.listHistory(mesh_transform)
        skin_cluster_list = cmds.ls(history, type='skinCluster')
        if not skin_cluster_list:
            print(f"スキンクラスターが見つかりません: {mesh_transform}")
            continue
        skin_cluster = skin_cluster_list[0]

        # OpenMaya の初期化
        sel_list = om.MSelectionList()
        sel_list.add(mesh_shape)  # shape ノードを使用
        dag_path = om.MDagPath()
        sel_list.getDagPath(0, dag_path)

        print(dag_path)

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

        # 頂点インデックスとコンポーネントの作成
        vtx_indices = om.MIntArray()
        components_map = {}
        for vtx_full, joint_weights in vtx_weights.items():
            vtx_index = int(vtx_full.split('[')[-1].rstrip(']'))
            vtx_indices.append(vtx_index)
            components_map[vtx_index] = joint_weights

        comp_fn = om.MFnSingleIndexedComponent()
        comp = comp_fn.create(om.MFn.kMeshVertComponent)
        comp_fn.addElements(vtx_indices)

        influence_count = inf_paths.length()
        weights = om.MDoubleArray(influence_count * vtx_indices.length(), 0.0)

        # 各頂点ごとにウェイトを埋める
        for i in range(vtx_indices.length()):
            idx = vtx_indices[i]
            joint_weights = components_map[idx]
            for joint_name, weight in joint_weights.items():
                joint_index = joint_index_map.get(joint_name)
                if joint_index is not None:
                    weights[i * influence_count + joint_index] = weight

        # 正しく作成した comp と vtx_indices を渡して setWeights 実行
        fn_skin.setWeights(dag_path, comp, vtx_indices, weights, False)

        print(f"{mesh_transform} にウェイトを適用しました")

    end = time.time()
    print(f"ウェイト設定処理 : {end - start:.4f} 秒")


def test():
    from maya_test.open_maya.skin_weight.test_scene import scene_1
    importlib.reload(scene_1)
    scene_1.main()

    root_node = cmds.ls('|root')[0]
    weight_info = get_skin_weight.collect_skin_weights(root_node)
    main(weight_info, '|duplicate_root')
