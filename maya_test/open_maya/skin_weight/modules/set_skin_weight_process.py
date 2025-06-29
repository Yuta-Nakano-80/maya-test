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

from maya_test.open_maya.skin_weight.modules import set_weight_get_process_info
from maya_test.open_maya.skin_weight.modules import set_skin_weight

importlib.reload(set_weight_get_process_info)
importlib.reload(set_skin_weight)


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

    def __init__(self, weight_data, target_root, rig_model_shape, delivery_shape_short_name_list):
        self.weight_data = weight_data
        self.target_root = target_root
        self.rig_model_shape = rig_model_shape
        self.delivery_shape_short_name_list = delivery_shape_short_name_list

        self.order(rig_model_shape)

    def order_old(self, rig_model_shape):
        """
        処理純
        """
        start = time.time()

        # デリバリーアセットのショートネームのリスト化
        # リグモデルのアセットに対応するアセットを判別する際に利用する
        self.get_delivery_shape_short_namelist()

        rig_model_short_name = rig_model_shape.split('|')[-1]

        shape_start = time.time()

        # ウェイト割り当てのための準備
        result = self.prepare_set_skin_weight(rig_model_shape)
        if result is None:
            return

        rig_model_short_name = result['rig_model_short_name']
        weight_info = result['weight_info']
        skin_cluster = result['skin_cluster']
        rig_model_shape_dag_path = result['rig_model_shape_dag_path']
        fn_skin_obj = result['fn_skin_obj']
        joint_index_map = result['joint_index_map']

        fn_skin_obj = result['fn_skin_obj']
        rig_model_shape_dag_path = result['rig_model_shape_dag_path']
        vertex_component = result['vertex_component']
        joint_index_reference = result['joint_index_reference']
        all_weights = result['all_weights']

        # 一括でウェイトを設定
        fn_skin_obj.setWeights(
            rig_model_shape_dag_path,
            vertex_component,
            joint_index_reference,
            all_weights,
            False
        )

        shape_end = time.time()
        print(f"シェイプごとのウェイト割り当て {rig_model_short_name} : {shape_end - shape_start:.4f} 秒")

        end = time.time()
        print(f"ウェイト設定処理 : {end - start:.4f} 秒")

    def order(self, rig_model_shape):

        result = {}

        # リグモデルのトランスフォーム取得
        rig_model_transform = cmds.listRelatives(rig_model_shape, parent=True, fullPath=True)[0]
        delivery_shape = self.get_delivery_shape(rig_model_shape)

        print('\n\n------------------------------------------------------------------------\n')
        print('     rig_model :', rig_model_transform)
        print('               :', rig_model_shape)
        print('delivery_model :', delivery_shape)

        if delivery_shape is None:
            return None

        rig_model_short_name = rig_model_transform.split('|')[-1]
        result['rig_model_short_name'] = rig_model_short_name

        # デリバリーアセットのウェイト情報
        weight_info = self.weight_data[delivery_shape]
        result['weight_info'] = weight_info
        # print('\nウェイト情報')
        # print(json.dumps(weight_map, indent=4, ensure_ascii=False))

        # スキンクラスターの取得
        skin_cluster = self.get_skin_cluster(rig_model_transform)
        if skin_cluster is None:
            return None
        result['skin_cluster'] = skin_cluster
        # print('  skin_cluster :', skin_cluster)

        # DAGパスとSkinClusterオブジェクトの取得
        rig_model_shape_dag_path = self.get_dag_path(rig_model_shape)
        result['rig_model_shape_dag_path'] = rig_model_shape_dag_path
        print('      dag_path :', rig_model_shape_dag_path.fullPathName())

        # スキンクラスターオブジェクトの取得
        test = True
        influence_obj_list, fn_skin_obj = self.get_influence_obj_list(skin_cluster, test)
        result['fn_skin_obj'] = fn_skin_obj

        # ジョイントインデックスマップの取得
        # これ必要かかなり怪しい。あとで検討
        test = False
        joint_index_map = self.get_joint_index_map(influence_obj_list, fn_skin_obj, rig_model_short_name, test)
        result['joint_index_map'] = joint_index_map

        return result
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

    def get_delivery_shape_short_namelist(self):
        """
        weight_info のショートネームのリストを取得する
        後にインデックスを調べたいときに利用する
        """

        for delivery_transform in list(self.weight_data.keys()):
            short_name = delivery_transform.split('|')[-1]
            self.delivery_shape_short_name_list.append(short_name)
        test = True
        if test:
            print('\nself.delivery_shape_list')
            print(json.dumps(self.delivery_shape_short_name_list, indent=4, ensure_ascii=False))

    def get_rig_model_shape_list(self):
        """
        ターゲットのルート以下のメッシュのシェイプノードをリストで取得する

        Returns:
            list: ウェイトを割り当てるシェイプノードのリスト
        """
        rig_model_shapes = cmds.listRelatives(self.target_root, allDescendents=True, type='mesh', f=True) or []
        rig_model_shapes = [m for m in rig_model_shapes if not cmds.getAttr(m + ".intermediateObject")]

        # print(json.dumps(rig_model_shapes, indent=4, ensure_ascii=False))
        return rig_model_shapes

    def get_delivery_shape(self, rig_model_shape):
        """
        デリバリーアセット側（ウェイトインフォ）に同名のメッシュがある場合に
        その同名のメッシュの名前を返す。
        階層は違うがノード名は同じ。

        Args:
            rig_model_shape(str): リグモデルのトランスフォームノード

        Returns:
            str: デリバリーアセットのメッシュ名
            none: 存在しない場合に None を返す
        """
        test = False
        shape_short_name = rig_model_shape.split('|')[-1]

        if test:
            print()
            print(shape_short_name)

        if shape_short_name not in self.delivery_shape_short_name_list:
            if test:
                print('デリバリーアセットなし : {}'.format(shape_short_name))
            return None

        index = self.delivery_shape_short_name_list.index(shape_short_name)
        delivery_shape = list(self.weight_data.keys())[index]

        if test:
            print('index :', index)
            print('delivery_shape :', delivery_shape)
        return delivery_shape

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
    def get_influence_obj_list(skin_cluster, test):
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

        if test:
            for i in range(influence_obj_list.length()):
                if i == 0:
                    print('     influence :', influence_obj_list[i].fullPathName())
                else:
                    print('               :', influence_obj_list[i].fullPathName())

        return influence_obj_list, fn_skin_obj

    @staticmethod
    def get_joint_index_map(influence_obj_list, fn_skin_obj, rig_model_short_name, test):
        """
        ジョイントマップの取得
        """
        joint_index_map = {}
        for i in range(influence_obj_list.length()):
            joint_name = influence_obj_list[i].fullPathName()
            index = fn_skin_obj.indexForInfluenceObject(influence_obj_list[i])
            joint_index_map[joint_name] = index

        if test:
            save_json(r'joint_index_map\{}.json'.format(rig_model_short_name), joint_index_map)

        return joint_index_map

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
        print('  target_shape :', rig_model_shape)
        print()

        time_shape_start = time.time()

        # ウェイトの割り当てに必要なデータ収集
        start_information_gathering = time.time()
        result = set_weight_get_process_info.main(weight_data, rig_model_shape, delivery_shape_short_name_list)
        if result is None:
            continue
        end_information_gathering = time.time()
        print('data_gathering : {:.4f} 秒'.format(end_information_gathering - start_information_gathering))
        time_shape_end = time.time()

        # ウェイトの割り当て
        start_set_weight = time.time()
        set_skin_weight.main(result)
        end_set_weight = time.time()
        print('    set_weight : {:.4f} 秒'.format(end_set_weight - start_set_weight))

        print("  process_time : {:.4f} 秒".format(time_shape_end - time_shape_start))

    end = time.time()
