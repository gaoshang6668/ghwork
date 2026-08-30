import pandas as pd
import numpy as np
import os

# 原始数据路径
raw_dir = r"D:\gh\ghwork\data"
# 预处理后输出目录
processed_dir = os.path.join(raw_dir, "processed")
os.makedirs(processed_dir, exist_ok=True)

# ========== 1 读取全部原始csv ==========
df_material = pd.read_csv(os.path.join(raw_dir, "material_info.csv"), encoding="utf-8-sig")
df_workstation = pd.read_csv(os.path.join(raw_dir, "workstation_info.csv"), encoding="utf-8-sig")
df_consume = pd.read_csv(os.path.join(raw_dir, "material_consume_record.csv"), encoding="utf-8-sig")
df_agv_map = pd.read_csv(os.path.join(raw_dir, "agv_warehouse_map.csv"), encoding="utf-8-sig")

print("=====原始数据行数=====")
print(f"领料记录原始行数：{len(df_consume)}")

# ========== 2 领料消耗记录表核心预处理 material_consume_record ==========
# 2.1 缺失值处理
df_consume = df_consume.dropna(subset=["work_order_id","record_date","workstation_id","material_id","consume_qty"])

# 2.2 时间字段标准化
df_consume["record_date"] = pd.to_datetime(df_consume["record_date"], format="%Y-%m-%d", errors="coerce")
# 时间转换失败的脏记录删除
df_consume = df_consume.dropna(subset=["record_date"])

# 2.3 异常值处理：消耗数量必须>0
df_consume = df_consume[df_consume["consume_qty"] > 0]

# 2.4 去重：完全重复记录删除
df_consume = df_consume.drop_duplicates()

# 2.5 业务外键校验：物料id、工位id必须存在于基础表
valid_mid = set(df_material["material_id"].tolist())
valid_wid = set(df_workstation["workstation_id"].tolist())
df_consume = df_consume[df_consume["material_id"].isin(valid_mid)]
df_consume = df_consume[df_consume["workstation_id"].isin(valid_wid)]

# 2.6 构造衍生时间特征（用于LSTM时序预测）
df_consume["weekday"] = df_consume["record_date"].dt.weekday
df_consume["month"] = df_consume["record_date"].dt.month

# 2.7 构造Apriori事务数据集：按工单分组，每个工单为一条事务，物料集合
apriori_trans = df_consume.groupby("work_order_id")["material_id"].apply(list).reset_index()
apriori_trans.columns = ["work_order_id","material_items"]

print(f"预处理后领料记录行数：{len(df_consume)}")

# ==========3 基础表简单校验（物料、工位、AGV地图） ==========
# 删除基础表空行
df_material = df_material.dropna(subset=["material_id","material_name"])
df_workstation = df_workstation.dropna(subset=["workstation_id"])
df_agv_map = df_agv_map.dropna(subset=["node_id"])

# ==========4 保存预处理之后全部文件 ==========
df_consume.to_csv(os.path.join(processed_dir, "consume_processed.csv"), index=False, encoding="utf-8-sig")
df_material.to_csv(os.path.join(processed_dir, "material_processed.csv"), index=False, encoding="utf-8-sig")
df_workstation.to_csv(os.path.join(processed_dir, "workstation_processed.csv"), index=False, encoding="utf-8-sig")
df_agv_map.to_csv(os.path.join(processed_dir, "agv_map_processed.csv"), index=False, encoding="utf-8-sig")
apriori_trans.to_csv(os.path.join(processed_dir, "apriori_transactions.csv"), index=False, encoding="utf-8-sig")

print(f"\n✅数据预处理完成，输出目录：{processed_dir}")
print("输出文件：")
print("  consume_processed.csv      预处理后领料记录（给LSTM时序预测）")
print("  apriori_transactions.csv   工单物料事务集（给Apriori关联挖掘）")
print("  material_processed.csv")
print("  workstation_processed.csv")
print("  agv_map_processed.csv")
