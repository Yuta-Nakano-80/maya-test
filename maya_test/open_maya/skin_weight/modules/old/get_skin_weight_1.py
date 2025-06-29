"""

スキンウェイトの取得

import importlib
from maya_test.open_maya.skin_weight import get_skin_weight
importlib.reload(get_skin_weight)
get_skin_weight.test()


指定したノードを引数として、ウェイト情報をまとめる関数が欲しい。
指定したノード以下の階層にある全てのメッシュの全てのインフルエンスとウェイト値の情報を取得し、
下記の形にまとめたい。
openMaya を使用して取得したい。

｛
    'メッシュのフルパス.vtx[0]:{
        'インフルエンスのフルパス' : ウェイトの値
    },
    'メッシュのフルパス.vtx[1]:{
        'インフルエンスのフルパス' : ウェイトの値
    }
}


"""
import importlib
import json

import time
import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaAnim as oma


def collect_skin_weights(root_node_list):
    start = time.time()

    mesh_list = []
    weight_data = {}

    for root_node in root_node_list:
        # 全メッシュ取得
        meshes = cmds.listRelatives(root_node, allDescendents=True, fullPath=True, type="mesh") or []
        meshes = [m for m in meshes if not cmds.getAttr(m + ".intermediateObject")]
        mesh_list.extend(meshes)

    for mesh_shape in mesh_list:
        # 親トランスフォーム取得
        mesh_transform = cmds.listRelatives(mesh_shape, parent=True, fullPath=True)[0]

        # スキンクラスター取得
        skin_cluster = None
        history = cmds.listHistory(mesh_shape)
        for node in history:
            if cmds.nodeType(node) == "skinCluster":
                skin_cluster = node
                break
        if not skin_cluster:
            continue

        # メッシュとスキンの MObject を取得
        sel_list = om.MSelectionList()
        sel_list.add(mesh_shape)
        dag_path = om.MDagPath()
        sel_list.getDagPath(0, dag_path)

        sel_list = om.MSelectionList()
        sel_list.add(skin_cluster)
        skin_obj = om.MObject()
        sel_list.getDependNode(0, skin_obj)

        fn_skin = oma.MFnSkinCluster(skin_obj)

        # インフルエンスジョイントのフルパスを取得
        inf_paths = om.MDagPathArray()
        fn_skin.influenceObjects(inf_paths)

        # influence index → joint name マップ
        inf_index_map = {}
        for i in range(inf_paths.length()):
            index = fn_skin.indexForInfluenceObject(inf_paths[i])
            inf_index_map[index] = inf_paths[i].fullPathName()

        # 全頂点を対象にコンポーネント作成
        vert_comp = om.MFnSingleIndexedComponent()
        comp = vert_comp.create(om.MFn.kMeshVertComponent)
        num_verts = cmds.polyEvaluate(mesh_transform, vertex=True)

        # MIntArray を作成して追加
        vtx_indices = om.MIntArray()
        for i in range(num_verts):
            vtx_indices.append(i)

        vert_comp.addElements(vtx_indices)

        # ウェイト取得
        weights = om.MDoubleArray()
        inf_count = om.MScriptUtil()
        inf_count_ptr = inf_count.asUintPtr()

        fn_skin.getWeights(dag_path, comp, weights, inf_count_ptr)
        num_infs = om.MScriptUtil.getUint(inf_count_ptr)

        # 頂点ごとのウェイト辞書作成
        for vtx_index in range(num_verts):
            vtx_name = f"{mesh_transform}.vtx[{vtx_index}]"
            weight_data[vtx_name] = {}
            for i in range(num_infs):
                weight = weights[vtx_index * num_infs + i]
                if weight > 0.0:
                    joint_name = inf_index_map[i]
                    weight_data[vtx_name][joint_name] = weight
    end = time.time()
    print(f"ウェイト情報取得 : {end - start:.4f} 秒")

    test = True
    if test:
        with open(r'D:\_temp\py_test\weight_info.json', 'w') as f:
            json.dump(weight_data, f, indent=4, ensure_ascii=False)
        print('\njson データの保存')
        print(r'D:\_temp\py_test')
        print('weight_info.json\n')

    return weight_data


def test():
    # from maya_test.test_scene import scene_2
    # importlib.reload(scene_2)
    # scene_2.main()

    root_node_list = ['|ch00_0000_0000', '|ch01_0000_0000']

    weight_info = collect_skin_weights(root_node_list)
    print(json.dumps(weight_info, indent=4, ensure_ascii=False))

    with open(r'D:\_temp\py_test\weight_info.json', 'w') as f:
        json.dump(weight_info, f, indent=4, ensure_ascii=False)
