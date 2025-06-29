"""

スキンウェイトのセット

成功したが遅い

import importlib
from maya_test.open_maya.skin_weight import set_skin_weight
importlib.reload(set_skin_weight)
set_skin_weight.test()


"""
import os
import time
import json
import importlib
import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaAnim as oma

from maya_test.open_maya.skin_weight.modules import set_weight_get_process_info_1
from maya_test.open_maya.skin_weight.modules import set_weight_get_process_info_2

importlib.reload(set_weight_get_process_info_1)
importlib.reload(set_weight_get_process_info_2)


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


def get_delivery_shape_short_name_list(weight_data):
    """
    デリバリーアセットのメッシュシェイプのショートネームのリストを取得する
    Returns:
        list: ショートネームのリスト
    """
    delivery_shape_short_name_list = []
    for delivery_transform in list(weight_data.keys()):
        short_name = delivery_transform.split('|')[-1]
        delivery_shape_short_name_list.append(short_name)

    return delivery_shape_short_name_list


def print_dbug(delivery_shape_short_name_list):
    """
    デバッグ用の出力
    Args:
        delivery_shape_short_name_list:
    """
    print('\n\n\n==============================================================================================\n\n')
    print('ウェイトの転送処理\n\n')
    print('ターゲットのメッシュノード')
    print(json.dumps(delivery_shape_short_name_list, indent=4, ensure_ascii=False))


def main(weight_data, target_root):
    """
    Args:
        weight_data: { 'mesh.vtx[0]' : { 'joint' : weight, ... }, ... }
        target_root: 割り当て側のルートノード
    """
    start = time.time()

    # シェイプノードの取得。中間オブジェクトを弾く
    rig_model_shape_list = cmds.listRelatives(target_root, allDescendents=True, type='mesh', f=True) or []
    rig_model_shape_list = [m for m in rig_model_shape_list if not cmds.getAttr(m + ".intermediateObject")]

    # ショートネームのリストを取得
    delivery_shape_short_name_list = get_delivery_shape_short_name_list(weight_data)
    print_dbug(delivery_shape_short_name_list)

    for rig_model_shape in rig_model_shape_list:
        print('\n-------------------------------------------------------\n')
        print('       target_shape :', rig_model_shape)
        print()

        time_process_start = time.time()

        # ウェイトの割り当てに必要なデータ収集
        start_information_gathering = time.time()
        result = set_weight_get_process_info_1.main(weight_data, rig_model_shape, delivery_shape_short_name_list)
        if result is None:
            continue

        fn_skin_obj, dag_path, vertex_component, all_joint_index_array, all_weight_array = set_weight_get_process_info_2.main(result)
        end_information_gathering = time.time()
        print('     data_gathering : {:.4f} 秒'.format(end_information_gathering - start_information_gathering))

        # ウェイトの割り当て
        start_set_weight = time.time()
        fn_skin_obj.setWeights(
            dag_path,
            vertex_component,
            all_joint_index_array,
            all_weight_array,
            False
        )
        end_set_weight = time.time()

        set_weight_second = end_set_weight - start_set_weight
        set_weight_minute = int(set_weight_second / 60)
        set_weight_second_m = set_weight_second % 60
        print('         set_weight : {}分 {:.4f} 秒'.format(set_weight_minute, set_weight_second_m))

        time_process_end = time.time()
        proces_time = time_process_end - time_process_start
        process_minute = int(set_weight_second / 60)
        process_second_m = set_weight_second % 60
        print('         set_weight : {}分 {:.4f} 秒'.format(set_weight_minute, set_weight_second_m))
        print("       process_time : {}分 {:.4f} 秒".format(process_minute, process_second_m))

    print('\n\n\n========================================================\n\n')
    end = time.time()
    all_proces_time = end - start
    _minute = int(all_proces_time / 60)
    hours = int(_minute / 60)
    minute = int(hours % 60)
    second = minute % 60

    print('ウェイト割り当ての総処理時間 : {}時間 {}分 {:.4f}秒'.format(hours, minute, second))


