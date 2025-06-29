"""

スキンウェイトを適用する

"""

import os
import time
import json

import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaAnim as oma


def get_vertex_index(delivery_vertex_path):
    """

    Returns:

    """
    vertex_index = int(delivery_vertex_path.split('.vtx[')[-1].rstrip(']'))
    return vertex_index


def get_joint_weight_index(weight_info, delivery_vertex_path, joint_index_map):
    """
    ジョイントのインデックスのリストを取得する
    Returns:

    """
    joint_index_list = []
    weight_list = []

    # デリバリーアセットのインフルエンスのリスト
    delivery_influence_list = list(weight_info[delivery_vertex_path].keys())
    for delivery_influence in delivery_influence_list:
        delivery_influence_lower_path = '|'.join(delivery_influence.split('|')[2:])

        # リグモデルのインフルエンスのリスト
        rig_model_influence_list = list(joint_index_map.keys())
        for rig_model_influence in rig_model_influence_list:
            rig_model_lower_influence_path = '|'.join(rig_model_influence.split('|')[2:])

            # インフルエンスのインデックスを取得
            if rig_model_lower_influence_path == delivery_influence_lower_path:
                joint_index = joint_index_map[rig_model_influence]
                joint_index_list.append(joint_index)

                weight_value = weight_info[delivery_vertex_path][delivery_influence]
                weight_list.append(weight_value)

    return joint_index_list, weight_list


def main(gathering_data):
    """
    スキンウェイトを適用する
    Args:
        gathering_data (dict): set_weight_get_process_info.main() で集めたデータ
    """
    rig_model_transform = gathering_data['rig_model_transform']
    delivery_shape = gathering_data['delivery_shape']
    skin_cluster = gathering_data['skin_cluster']
    dag_path = gathering_data['dag_path']
    influence_obj_list = gathering_data['influence_obj_list']
    fn_skin_obj = gathering_data['fn_skin_obj']
    joint_index_map = gathering_data['joint_index_map']
    weight_info = gathering_data['weight_info']

    # ウェイト設定に必要なリスト
    # 順番は weight_info を基準にする
    vertex_index_list = om.MIntArray()
    all_joint_index_array = om.MIntArray()
    all_weight_array = om.MDoubleArray()

    all_joint_index_list = []
    all_weight_list = []

    vertex_list = list(weight_info.keys())
    for delivery_vertex_path in vertex_list:

        # バーテックスコンポーネント用に頂点リストを weight_info から取得する
        vertex_index = get_vertex_index(delivery_vertex_path)
        vertex_index_list.append(vertex_index)

        # ジョイントインデックスの取得
        joint_index_list, weight_list = get_joint_weight_index(weight_info, delivery_vertex_path, joint_index_map)

        # 登録
        all_joint_index_list.extend(joint_index_list)
        all_weight_list.extend(weight_list)

    for i in all_joint_index_list:
        all_joint_index_array.append(i)

    for i in all_weight_list:
        all_weight_array.append(i)

    # vertex コンポーネントの作成
    comp_fn = om.MFnSingleIndexedComponent()
    vertex_component = comp_fn.create(om.MFn.kMeshVertComponent)
    comp_fn.addElements(vertex_index_list)

    return fn_skin_obj, dag_path, vertex_component, all_joint_index_array, all_weight_array


