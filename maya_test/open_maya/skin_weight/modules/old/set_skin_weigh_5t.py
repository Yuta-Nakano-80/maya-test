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


class SetSkinWeight:
    """
    ウェイト情報から対象のノードにウェイトを設定する
    """

    def __init__(self, weight_data, target_root):
        self.weight_data = weight_data
        self.target_root = target_root
        self.mesh_weight_map = {}
        self.delivery_transform_list = []
        self.delivery_transform_short_list = []

        self.order()

    def order(self):
        """
        処理純
        """
        start = time.time()

        # ウェイト情報の整理
        mesh_weight_map = self.organize_weight_data()
        # print(json.dumps(self.delivery_transform_list, indent=4, ensure_ascii=False))

        # デリバリーアセットのショートネームのリスト化
        # リグモデルのアセットに対応するアセットを判別する際に利用する
        self.get_delivery_transform_short_list()
        # print(json.dumps(self.delivery_transform_short_list, indent=4, ensure_ascii=False))

        rig_model_shape_list = self.get_rig_model_shape_list()
        for rig_model_shape in rig_model_shape_list:
            rig_model_short_name = rig_model_shape.split('|')[-1]

            shape_start = time.time()

            # ウェイト割り当てのための準備
            result = self.prepare_set_skin_weight(rig_model_shape, mesh_weight_map)
            if result is None:
                continue

            # rig_model_shape_dag_path = result['rig_model_shape_dag_path']
            # vertex_component = result['vertex_component']
            # weight_array = result['weight_array']
            # joint_index_list = result['joint_index_list']
            # fn_skin_obj = result['fn_skin_obj']

            # fn_skin_obj.setWeights(rig_model_shape_dag_path, vertex_component, joint_index_list, weight_array, False)

            shape_end = time.time()
            print(f"シェイプごとのウェイト割り当て {rig_model_short_name} : {shape_end - shape_start:.4f} 秒")

        end = time.time()
        print(f"ウェイト設定処理 : {end - start:.4f} 秒")

    def prepare_set_skin_weight(self, rig_model_shape, mesh_weight_map):

        result = {}

        # リグモデルのトランスフォーム取得
        rig_model_transform = cmds.listRelatives(rig_model_shape, parent=True, fullPath=True)[0]
        delivery_transform = self.get_delivery_transform(mesh_weight_map, rig_model_transform)
        if delivery_transform is None:
            return None

        rig_model_short_name = rig_model_transform.split('|')[-1]

        # デリバリーアセットのウェイト情報
        weight_map = mesh_weight_map[delivery_transform]

        # スキンクラスターの取得
        skin_cluster = self.get_skin_cluster(rig_model_transform)
        if skin_cluster is None:
            return None

        # DAGパスとSkinClusterオブジェクトの取得
        rig_model_shape_dag_path = self.get_dag_path(rig_model_shape)
        result['rig_model_shape_dag_path'] = rig_model_shape_dag_path

        influence_obj_list, fn_skin_obj = self.get_influence_obj_list(skin_cluster)
        result['fn_skin_obj'] = fn_skin_obj

        joint_index_map = self.get_joint_index_map(influence_obj_list, fn_skin_obj, rig_model_short_name)

        # 複数頂点の情報を一括収集
        index_list = om.MIntArray()
        all_weights = om.MDoubleArray()
        weights_per_vertex = []
        joint_index_reference = None

        for delivery_vertex_path, joint_weight_info in weight_map.items():
            # 頂点番号取得
            vtx_index = int(delivery_vertex_path.split('[')[-1].rstrip(']'))
            index_list.append(vtx_index)

            # 重みとジョイントインデックスの配列
            weight_array, joint_index_list = self.get_vertex_joint_array(
                joint_weight_info, joint_index_map, rig_model_short_name)

            # 最初の頂点の joint_index_list を基準とする
            if joint_index_reference is None:
                joint_index_reference = joint_index_list
            else:
                # 全頂点で joint_index_list が一致しないと setWeights に渡せない
                if list(joint_index_list) != list(joint_index_reference):
                    print(f'警告: {rig_model_short_name} でジョイントの順番が一致しません。スキップされました。')
                    return None

            for joint_indices, weight_array in weights_per_vertex:
                for i in range(weight_array.length()):
                    all_weights.append(weight_array[i])

        # 複数頂点の component 作成
        comp_fn = om.MFnSingleIndexedComponent()
        vertex_component = comp_fn.create(om.MFn.kMeshVertComponent)
        comp_fn.addElements(index_list)

        # 一括でウェイトを設定
        fn_skin_obj.setWeights(
            rig_model_shape_dag_path,
            vertex_component,
            joint_index_reference,
            all_weights,
            False
        )

        return result

    @staticmethod
    def get_vertex_joint_array(joint_weight_info, joint_index_map, rig_model_short_name):
        """
        ウェイトとジョイント配列の取得
        Returns:

        """
        weight_array = om.MDoubleArray()
        joint_index_list = om.MIntArray()
        for joint, weight in joint_weight_info.items():
            if joint not in joint_index_map:
                continue  # 一致するジョイントが見つからない
            joint_index_list.append(joint_index_map[joint])
            weight_array.append(weight)

        test = True
        if test:
            save_json(r'joint_index_list/{}.json'.format(
                rig_model_short_name), [joint_index_list[i] for i in range(joint_index_list.length())])
            save_json(r'weight_array/{}.json'.format(
                rig_model_short_name), [weight_array[i] for i in range(weight_array.length())])

        return weight_array, joint_index_list

    @staticmethod
    def get_vertex_component(delivery_vertex_index):
        """
        頂点コンポーネントの取得
        Args:
            delivery_vertex_index (int): 頂点番号
        """
        indices = om.MIntArray()
        indices.append(delivery_vertex_index)
        comp_fn = om.MFnSingleIndexedComponent()
        vertex_component = comp_fn.create(om.MFn.kMeshVertComponent)
        comp_fn.addElements(indices)

        test = False
        if test:
            print('\n comp -----------------------')
            comp_fn = om.MFnSingleIndexedComponent()
            comp_fn.setObject(vertex_component)
            indices = om.MIntArray()
            comp_fn.getElements(indices)
            print("Vertex Indices in Component:", list(indices))

        return vertex_component

    @staticmethod
    def get_joint_index_map(influence_obj_list, fn_skin_obj, rig_model_short_name):
        """
        ジョイントマップの取得
        """
        joint_index_map = {}
        for i in range(influence_obj_list.length()):
            joint_name = influence_obj_list[i].fullPathName()
            index = fn_skin_obj.indexForInfluenceObject(influence_obj_list[i])
            joint_index_map[joint_name] = index

        test = False
        if test:
            save_json(r'joint_index_map\{}.json'.format(rig_model_short_name), joint_index_map)

        return joint_index_map

    @staticmethod
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

        # for i in range(influence_obj_list.length()):
        #     print(influence_obj_list[i].fullPathName())

        return influence_obj_list, fn_skin_obj

    @staticmethod
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

    @staticmethod
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

    def get_delivery_transform(self, mesh_weight_map, rig_model_transform):
        """
        デリバリーアセット側（ウェイトインフォ）に同名のメッシュがある場合に
        その同名のメッシュの名前を返す。
        階層は違うがノード名は同じ。

        Returns:
            str: デリバリーアセットのメッシュ名
            none: 存在しない場合に None を返す
        """

        rig_model_short_name = rig_model_transform.split('|')[-1]

        if rig_model_short_name not in self.delivery_transform_short_list:
            print('デリバリーアセットなし : {}'.format(rig_model_short_name))
            return None

        index = self.delivery_transform_short_list.index(rig_model_short_name)
        delivery_transform = self.delivery_transform_list[index]
        return delivery_transform

    def get_delivery_transform_short_list(self):

        for delivery_transform in self.delivery_transform_list:
            short_name = delivery_transform.split('|')[-1]
            self.delivery_transform_short_list.append(short_name)

        # print(json.dumps(self.delivery_transform_short_list, indent=4, ensure_ascii=False)

    def get_rig_model_shape_list(self):
        """
        ターゲットのルート以下のメッシュのシェイプノードをリストで取得する
        """
        rig_model_shapes = cmds.listRelatives(self.target_root, allDescendents=True, type='mesh', f=True) or []
        rig_model_shapes = [m for m in rig_model_shapes if not cmds.getAttr(m + ".intermediateObject")]

        # print(json.dumps(rig_model_shapes, indent=4, ensure_ascii=False))
        return rig_model_shapes

    def organize_weight_data(self):
        """
        ウェイトデータの整理
        本来 get_skin_weight でやっとくべきだったけど時間がないのでここで記載。
        """
        mesh_weight_map = {}
        for vtx_path in list(self.weight_data.keys()):
            mesh_name, vtx_info = vtx_path.split('.vtx')
            mesh_name = mesh_name.strip()
            if mesh_name not in mesh_weight_map:
                mesh_weight_map[mesh_name] = {}
            mesh_weight_map[mesh_name][vtx_path] = self.weight_data[vtx_path]

        test = False
        if test:
            with open(r'D:\_temp\py_test\mesh_weight_map.json', 'w') as f:
                json.dump(mesh_weight_map, f, indent=4, ensure_ascii=False)

        self.delivery_transform_list = list(mesh_weight_map.keys())

        # print(json.dumps(self.delivery_transform_list, indent=4, ensure_ascii=False))
        return mesh_weight_map


def main(weight_data, target_root):
    """
    Args:
        weight_data: { 'mesh.vtx[0]' : { 'joint' : weight, ... }, ... }
        target_root: 割り当て側のルートノード
    """
    SetSkinWeight(weight_data, target_root)
