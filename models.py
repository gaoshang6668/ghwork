from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./gh.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 1.物料表
class Material(Base):
    __tablename__ = "material"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    safety_stock = Column(Float)
    current_stock = Column(Float, default=0.0)

# 2.出入库记录表
class StockRecord(Base):
    __tablename__ = "stock_record"
    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer)
    io_type = Column(String) # in入库 out出库
    quantity = Column(Float)
    create_time = Column(DateTime, default=datetime.now)
    is_abnormal = Column(Boolean, default=False) # 【新增】是否异常记录

#3.库存预测结果表（预留表现在投入使用）
class PredictResult(Base):
    __tablename__ = "predict_result"
    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer)
    predict_consume = Column(Float) #预测消耗
    suggest_supply = Column(Float) #建议补货量
    create_time = Column(DateTime, default=datetime.now)

#4.库存健康评估表（PHM）
class StockHealth(Base):
    __tablename__ = "stock_health"
    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer)
    health_status = Column(String) #正常 / 短缺风险 /积压风险
    remark = Column(String)
    create_time = Column(DateTime, default=datetime.now)

#5.AGV任务表（保留，不变）
class AgvTask(Base):
    __tablename__ = "agv_task"
    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String)
    material_id = Column(Integer)
    status = Column(String)

Base.metadata.create_all(bind=engine)

#获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
