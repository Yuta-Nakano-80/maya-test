import importlib
import json

from maya_test.open_maya.skin_weight.modules import get_skin_weight
from maya_test.open_maya.skin_weight.modules import set_skin_weight

importlib.reload(get_skin_weight)
importlib.reload(set_skin_weight)

weight_info = get_skin_weight.collect_skin_weights(['|ch00_0000_0000', '|ch01_0000_0000'])

with open(r'D:\_temp\py_test\weight_info.json', 'w') as f:
    json.dump(weight_info, f, indent=4, ensure_ascii=False)

set_skin_weight.main(weight_info, '|ch03_000_0000_rig_model')
