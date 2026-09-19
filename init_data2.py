from models import SessionLocal, Material

db = SessionLocal()
# 检查是否已有数据，避免重复插入
if db.query(Material).count() == 0:
    materials = [
        Material(name="螺丝", safety_stock=50, current_stock=120),
        Material(name="螺母", safety_stock=60, current_stock=150),
        Material(name="轴承", safety_stock=30, current_stock=45),
        Material(name="齿轮", safety_stock=40, current_stock=80),
        Material(name="轴承座", safety_stock=20, current_stock=25),
    ]
    db.add_all(materials)
    db.commit()
    print("已插入5条示例物料数据")
else:
    print("物料表已有数据，跳过")
db.close()
