"""

スキンウェイトのセットを行うために必要な情報を収集する

"""
import os
import time
import json

import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaAnim as oma


def save_json(path, data):
    """
    json ファイルの保存
    """
    file_path = os.path.join(r'D:\_temp\py_test', path)
    dir_path = os.path.dirname(file_path)

    # print('file_path :', file_path)
    # print('dir_path :', dir_path)

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_delivery_shape(rig_model_shape, weight_data, delivery_shape_short_name_list):
    """
    デリバリーアセット側（ウェイトインフォ）に同名のメッシュがある場合に
    その同名のメッシュの名前を返す。
    階層は違うがノード名は同じ。

    Args:
        rig_model_shape(str): リグモデルのトランスフォームノード
        weight_data:
        delivery_shape_short_name_list:

    Returns:
        str: デリバリーアセットのメッシュ名
        none: 存在しない場合に None を返す
    """
    shape_short_name = rig_model_shape.split('|')[-1]

    if shape_short_name not in delivery_shape_short_name_list:
        print('\nデリバリーアセットなし :', shape_short_name)
        print()
        return None

    index = delivery_shape_short_name_list.index(shape_short_name)
    delivery_shape = list(weight_data.keys())[index]

    return delivery_shape


def get_skin_cluster(rig_model_transform):
    """
    リグモデルのスキンクラスターの取得

    Returns:
        str: スキンクラスター名
        None: バインドされていない場合
    """
    # リグモデルのスキンクラスターの取得
    history = cmds.listHistory(rig_model_transform)
    skin_cluster_list = cmds.ls(history, type='skinCluster')
    if not skin_cluster_list:
        return None
    else:
        skin_cluster = skin_cluster_list[0]
        return skin_cluster


def get_dag_path(mesh_shape):
    """
    OpenMaya の初期化

    Returns:
        MDagPath: dag_path.fullPathName() でリグモデルのメッシュのフルパスがとれる
    """
    sel_list = om.MSelectionList()
    sel_list.add(mesh_shape)
    dag_path = om.MDagPath()
    sel_list.getDagPath(0, dag_path)
    # print(dag_path.fullPathName())
    sel_list.clear()
    return dag_path


def get_influence_obj_list(skin_cluster):
    """
    スキンクラスターオブジェクト の取得

    Returns:
        OpenMayaAnim.MFnSkinCluster:
    """
    sel_list = om.MSelectionList()
    sel_list.add(skin_cluster)
    skin_obj = om.MObject()
    sel_list.getDependNode(0, skin_obj)
    fn_skin_obj = oma.MFnSkinCluster(skin_obj)

    influence_obj_list = om.MDagPathArray()
    fn_skin_obj.influenceObjects(influence_obj_list)

    return influence_obj_list, fn_skin_obj


def get_joint_index_map(influence_obj_list, fn_skin_obj):
    """
    ジョイントマップの取得
    """
    joint_index_map = {}
    for i in range(influence_obj_list.length()):
        joint_name = influence_obj_list[i].fullPathName()
        index = fn_skin_obj.indexForInfluenceObject(influence_obj_list[i])
        joint_index_map[joint_name] = index
    return joint_index_map


def main(weight_data, rig_model_shape, delivery_shape_short_name_list):
    """
    スキンウェイトのセットを行うために必要な情報を収集する
    Returns:

    """
    result = {}

    # リグモデルのトランスフォームノード
    rig_model_transform = cmds.listRelatives(rig_model_shape, parent=True, fullPath=True)[0]
    result['rig_model_transform'] = rig_model_transform

    # 対応するデリバリーアセットのシェイプノード
    delivery_shape = get_delivery_shape(rig_model_shape, weight_data, delivery_shape_short_name_list)
    result['delivery_shape'] = delivery_shape

    # スキンクラスター
    skin_cluster = get_skin_cluster(rig_model_transform)
    result['skin_cluster'] = skin_cluster

    # dag オブジェクト
    dag_path = get_dag_path(rig_model_shape)
    result['dag_path'] = dag_path

    # インフルエンスオブジェクトとスキンオブジェクト
    influence_obj_list, fn_skin_obj = get_influence_obj_list(skin_cluster)
    result['influence_obj_list'] = influence_obj_list
    result['fn_skin_obj'] = fn_skin_obj

    # ジョイントインデックスマップ | 不要な気がする
    joint_index_map = get_joint_index_map(influence_obj_list, fn_skin_obj)
    result['joint_index_map'] = joint_index_map

    # 1つでもエラーがある場合は None を返して処理を止める
    if any(x is None for x in [rig_model_transform, delivery_shape, skin_cluster, dag_path,
                               influence_obj_list, joint_index_map]):
        return None

    weight_info = weight_data[delivery_shape]
    result['weight_info'] = weight_info

    rig_model_short_name = rig_model_shape.split('|')[-1]
    print('          name :', rig_model_short_name)
    print('delivery_shape :', delivery_shape)
    print('  skin_cluster :', skin_cluster)
    print('      dag_path :', dag_path.fullPathName())

    test = False
    if test:
        for i in range(influence_obj_list.length()):
            if i == 0:
                print('     influence :', influence_obj_list[i].fullPathName())
            else:
                print('               :', influence_obj_list[i].fullPathName())
        save_json(r'joint_index_map\{}.json'.format(rig_model_short_name), joint_index_map)

        print()
        for vtx_path in list(weight_info.keys()):
            print()
            print('   weight_info :', vtx_path)
            for influence in list(weight_info[vtx_path].keys()):
                weight = weight_info[vtx_path][influence]
                print('     influence :', influence)
                print('        weight :', weight)
            print()

    return result
