# generate_dataset.py
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

# ========== 修改输出目录 ==========
output_dir = r"D:\gh\ghwork\data"
# 如果文件夹不存在自动创建
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# ----------------------1.物料基础信息----------------------
material_data = [
    ["M001","螺栓A","件",80,150,0.2],
    ["M002","螺母B","件",70,140,0.1],
    ["M003","垫片C","件",60,120,0.05],
    ["M004","轴承D","套",30,60,1.2],
    ["M005","密封圈E","件",50,100,0.15],
    ["M006","弹簧F","件",45,90,0.08],
    ["M007","外壳G","个",20,40,2.5],
    ["M008","轴套H","件",35,70,0.8],
]
df_material = pd.DataFrame(material_data,columns=["material_id","material_name","unit","safety_stock","max_workstation_store","weight"])
df_material.to_csv(os.path.join(output_dir, "material_info.csv"), index=False, encoding="utf-8-sig")

# ----------------------2.工位信息----------------------
workstation_data = [
    ["W01","装配工位1",10,12],
    ["W02","装配工位2",22,14],
    ["W03","装配工位3",8,25],
    ["W04","装配工位4",26,28],
    ["W05","装配工位5",15,32],
    ["WH","仓库出库点",2,2],
]
df_workstation = pd.DataFrame(workstation_data,columns=["workstation_id","workstation_name","pos_x","pos_y"])
df_workstation.to_csv(os.path.join(output_dir, "workstation_info.csv"), index=False, encoding="utf-8-sig")

# ----------------------3.生成90天领料消耗记录（LSTM+Apriori）----------------------
start_date = datetime(2025,1,1)
days = 90
workstation_list = ["W01","W02","W03","W04","W05"]
material_list = ["M001","M002","M003","M004","M005","M006","M007","M008"]
# 预设物料关联：M001常和M002一起领用；M004常和M005一起领用，制造Apriori可以挖掘的规则
assoc_pairs = [("M001","M002"),("M004","M005")]

records = []
record_id = 1
work_order_id = 1

for d in range(days):
    current_dt = start_date + timedelta(days=d)
    weekday = current_dt.weekday()
    # 周末消耗降低
    scale = 0.4 if weekday>=5 else 1.0
    # 每日产生若干工单
    order_cnt = random.randint(3,7) if weekday<5 else random.randint(1,2)
    for _ in range(order_cnt):
        wo_id = f"WO{work_order_id:04d}"
        work_order_id +=1
        ws = random.choice(workstation_list)
        # 本次工单选物料，部分触发关联物料
        pick_mats = set()
        main_mat = random.choice(material_list)
        pick_mats.add(main_mat)
        for a,b in assoc_pairs:
            if main_mat == a and random.random()<0.6:
                pick_mats.add(b)
        # 额外随机加1‑2个物料
        extra = random.sample(material_list,k=random.randint(1,2))
        pick_mats.update(extra)
        for mid in pick_mats:
            base_qty = random.randint(10,50)
            qty = int(base_qty * scale * np.random.normal(loc=1.0,scale=0.12))
            qty = max(1,qty)
            records.append([record_id,wo_id,current_dt.strftime("%Y-%m-%d"),ws,mid,qty])
            record_id +=1

df_consume = pd.DataFrame(records,columns=["record_id","work_order_id","record_date","workstation_id","material_id","consume_qty"])
df_consume.to_csv(os.path.join(output_dir, "material_consume_record.csv"), index=False, encoding="utf-8-sig")

# ----------------------4.简易AGV地图csv----------------------
map_data = [
    ["N0","warehouse_out",2,2,"N1,N5"],
    ["N1","path",3,2,"N0,N2"],
    ["N2","path",4,2,"N1,N3"],
    ["N3","path",5,2,"N2,N4"],
    ["N10","workstation",10,12,"N9,N11"],
    ["N20","workstation",22,14,"N19,N21"],
]
df_map = pd.DataFrame(map_data,columns=["node_id","node_type","x","y","neighbor_nodes"])
df_map.to_csv(os.path.join(output_dir, "agv_warehouse_map.csv"), index=False, encoding="utf-8-sig")

print(f"✅模拟数据集生成完成！文件输出目录：{output_dir}")
print("输出文件列表：")
print("  material_info.csv")
print("  workstation_info.csv")
print("  material_consume_record.csv")
print("  agv_warehouse_map.csv")
