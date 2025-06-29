"""

スキンウェイトのセット

成功したが遅い

import importlib
from maya_test.open_maya.skin_weight import set_skin_weight
importlib.reload(set_skin_weight)
set_skin_weight.test()

"""

import importlib
import os
import time
import json

import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaAnim as oma


class SetWeight:

    def __init__(self, vtx_weight_list, joint_index_map, rig_model_shape_dag_path, fn_skin_obj):
        self.vtx_weight_list = vtx_weight_list
        self.joint_index_map = joint_index_map
        self.rig_model_shape_dag_path = rig_model_shape_dag_path
        self.fn_skin_obj = fn_skin_obj
        self.order()

    def order(self):
        """
        処理順
        """
        for vtx_full, joint_weight_list in self.vtx_weight_list.items():
            vtx_index = int(vtx_full.split('[')[-1].rstrip(']'))
            indices = om.MIntArray()
            indices.append(vtx_index)
            comp_fn = om.MFnSingleIndexedComponent()
            comp = comp_fn.create(om.MFn.kMeshVertComponent)
            comp_fn.addElements(indices)

            # joint index とウェイトの配列を準備
            weight_array = om.MDoubleArray()
            joint_indices = om.MIntArray()
            for joint, weight in joint_weight_list.items():
                if joint not in self.joint_index_map:
                    continue  # 一致するジョイントが見つからない
                joint_indices.append(self.joint_index_map[joint])
                weight_array.append(weight)

            self.fn_skin_obj.setWeights(self.rig_model_shape_dag_path, comp, joint_indices, weight_array, False)


def main(vtx_weight_list, joint_index_map, rig_model_shape_dag_path, fn_skin_obj):
    SetWeight(vtx_weight_list, joint_index_map, rig_model_shape_dag_path, fn_skin_obj)
