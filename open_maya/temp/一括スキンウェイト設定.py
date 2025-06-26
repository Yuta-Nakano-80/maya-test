import maya.api.OpenMaya as om
import maya.cmds as cmds


def set_skin_weights(mesh_name, skin_cluster_name, joint_names, weights_per_vertex):
    # メッシュのMObject取得
    sel = om.MSelectionList()
    sel.add(mesh_name)
    dagPath = sel.getDagPath(0)

    # スキンクラスタのMObject取得
    sel = om.MSelectionList()
    sel.add(skin_cluster_name)
    skin_cluster_obj = sel.getDependNode(0)
    skin_fn = om.MFnSkinCluster(skin_cluster_obj)

    # インフルエンスジョイントのインデックス取得
    influence_paths = [om.MSelectionList().add(jnt).getDagPath(0) for jnt in joint_names]
    influence_indices = [skin_fn.indexForInfluenceObject(p) for p in influence_paths]

    # メッシュの全頂点取得
    vertex_count = om.MFnMesh(dagPath).numVertices
    components = om.MFnSingleIndexedComponent().create(om.MFn.kMeshVertComponent)
    om.MFnSingleIndexedComponent(components).addElements(list(range(vertex_count)))

    # ウェイト設定（weights_per_vertexは[[0.0, 1.0], [0.2, 0.8], ...]の形）
    flat_weights = []
    for weights in weights_per_vertex:
        flat_weights.extend(weights)

    # FloatArray作成
    weight_array = om.MDoubleArray(flat_weights)

    # setWeights
    skin_fn.setWeights(dagPath, components, influence_indices, weight_array, False)


# 使用例:
mesh = "pSphere1"
skin_cluster = "skinCluster1"
joints = ["joint1", "joint2"]
# 各頂点ごとのジョイントウェイト
weights = [[0.5, 0.5]] * 382  # 頂点数分の重み

set_skin_weights(mesh, skin_cluster, joints, weights)
