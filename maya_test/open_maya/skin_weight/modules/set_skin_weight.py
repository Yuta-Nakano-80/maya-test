"""

スキンウェイトを適用する

"""

import os
import time
import json

import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaAnim as oma

def get_vertex_joint_array():
    """

    Returns:

    """


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

    vertex_path_list = list(weight_info.keys())

    vtx_index = int(delivery_vertex_path.split('[')[-1].rstrip(']'))


