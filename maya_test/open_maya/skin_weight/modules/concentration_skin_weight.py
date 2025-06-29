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
        influence_count = inf_paths.length()

        # インフルエンス名 -> index の辞書
        joint_index_map = {inf_paths[i].fullPathName(): i for i in range(inf_paths.length())}

        # ターゲットジョイントの index
        target_index = joint_index_map.get(target_joint, -1)
        if target_index == -1:
            print(f"{target_joint} がスキンに含まれていません")
            continue

        # 無視ジョイント index
        ignore_joints = []
        for j_name in ["joint_0", "joint_1"]:
            for i in range(influence_count):
                if inf_paths[i].partialPathName().endswith(j_name):
                    ignore_joints.append(i)
                    break

        # 全頂点 index 取得
        geo_iter = om.MItGeometry(mesh_path)
        vertex_count = geo_iter.count()
        index_array = om.MIntArray()
        for i in range(vertex_count):
            index_array.append(i)

        # 全頂点コンポーネント
        comp_fn = om.MFnSingleIndexedComponent()
        comp_obj = comp_fn.create(om.MFn.kMeshVertComponent)
        comp_fn.addElements(index_array)

        # 全頂点のウェイト一括取得
        weights = om.MDoubleArray()
        util = om.MScriptUtil()
        util.createFromInt(0)
        influence_count_ptr = util.asUintPtr()
        skin_fn.getWeights(mesh_path, comp_obj, weights, influence_count_ptr)

        # 新しいウェイトを構築
        new_weights = om.MDoubleArray()
        for vtx_index in range(vertex_count):
            offset = vtx_index * influence_count
            vtx_weights = [weights[offset + i] for i in range(influence_count)]

            transfer_sum = sum(vtx_weights[i] for i in range(influence_count)
                               if i != target_index and i not in ignore_joints)

            for i in range(influence_count):
                if i in ignore_joints:
                    new_weights.append(vtx_weights[i])
                elif i == target_index:
                    new_weights.append(vtx_weights[i] + transfer_sum)
                else:
                    new_weights.append(0.0)

        # インフルエンス index 配列
        influence_indices = om.MIntArray()
        for i in range(influence_count):
            influence_indices.append(i)

        # 一括ウェイト設定
        skin_fn.setWeights(mesh_path, comp_obj, influence_indices, new_weights, False)

    end = time.time()
    print(f"ウェイトを特定のインフルエンスに集中させる処理 : {end - start:.4f} 秒")
