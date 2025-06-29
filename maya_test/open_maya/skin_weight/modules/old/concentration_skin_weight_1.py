import time

import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaAnim as oma


def get_mobject(node_name):
    sel = om.MSelectionList()
    sel.add(node_name)
    mobj = om.MObject()
    sel.getDependNode(0, mobj)
    return mobj


def get_dag_path(node_name):
    sel = om.MSelectionList()
    sel.add(node_name)
    dag = om.MDagPath()
    sel.getDagPath(0, dag)
    return dag


def main(mesh_root, target_joint):
    start = time.time()

    mesh_shapes = cmds.listRelatives(mesh_root, allDescendents=True, fullPath=True, type='mesh') or []
    for mesh in mesh_shapes:
        skin_clusters = cmds.ls(cmds.listHistory(mesh), type='skinCluster')
        if not skin_clusters:
            continue

        skin_cluster = skin_clusters[0]
        skin_mobj = get_mobject(skin_cluster)
        skin_fn = oma.MFnSkinCluster(skin_mobj)
        mesh_path = get_dag_path(mesh)

        # インフルエンス取得
        inf_paths = om.MDagPathArray()
        skin_fn.influenceObjects(inf_paths)

        joint1_full = target_joint
        joint1_index = -1
        for i in range(inf_paths.length()):
            if inf_paths[i].fullPathName() == joint1_full:
                joint1_index = i
                break

        if joint1_index == -1:
            print(f"{joint1_full} がスキンに含まれていません")
            continue

        # 全頂点のウェイトを joint1_index=1.0 に、それ以外=0.0 にする
        geo_iter = om.MItGeometry(mesh_path)
        index_array = om.MIntArray()
        influence_count = inf_paths.length()
        indices_list = [i for i in range(influence_count)]
        influence_indices = om.MIntArray()
        for i in indices_list:
            influence_indices.append(i)
        weight_list = om.MDoubleArray()

        vertex_count = geo_iter.count()
        for vtx_index in range(vertex_count):
            index_array.append(vtx_index)
            for i in range(influence_count):
                weight_list.append(1.0 if i == joint1_index else 0.0)

        comp_fn = om.MFnSingleIndexedComponent()
        comp_obj = comp_fn.create(om.MFn.kMeshVertComponent)
        comp_fn.addElements(index_array)

        skin_fn.setWeights(mesh_path, comp_obj, influence_indices, weight_list, False)

    end = time.time()

    print(f"ウェイトを特定のインフルエンスに集中させる処理 : {end - start:.4f} 秒")

