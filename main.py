from fastapi import FastAPI, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
import pandas as pd
from sklearn.ensemble import IsolationForest
from statsmodels.tsa.arima.model import ARIMA
from models import get_db, Material, StockRecord, PredictResult, StockHealth, AgvTask
from datetime import datetime, timedelta
import random

app = FastAPI(title="仓储物料智能管理系统")

# 首页
@app.get("/", response_class=HTMLResponse)
def index(db:Session=Depends(get_db)):
    materials = db.query(Material).all()
    html = """
    <html>
    <head>
        <meta charset="utf-8">
        <title>智能仓储物料管理平台</title>
        <style>
            * {
                margin:0;
                padding:0;
                box-sizing:border-box;
                font-family:Microsoft YaHei, sans-serif;
            }
            body{
                background-color:#f4f7fa;
                padding:30px;
            }
            .container{
                max-width:1200px;
                margin:0 auto;
            }
            .header-card{
                background:#fff;
                padding:20px;
                border-radius:12px;
                box-shadow:0 2px 12px rgba(0,0,0,0.08);
                margin-bottom:20px;
                display:flex;
                justify-content:space-between;
                align-items:center;
            }
            h2{
                color:#2d3748;
            }
            .btn-group > button{
                padding:10px 16px;
                border:none;
                border-radius:8px;
                cursor:pointer;
                font-size:14px;
                margin-left:10px;
                transition: all 0.2s;
            }
            .btn-primary{
                background:#3182ce;
                color:white;
            }
            .btn-primary:hover{
                background:#2b6cb0;
            }
            .btn-success{
                background:#38a169;
                color:white;
            }
            .btn-success:hover{
                background:#2f855a;
            }
            .card{
                background:#fff;
                border-radius:12px;
                box-shadow:0 2px 12px rgba(0,0,0,0.08);
                padding:20px;
            }
            table{
                width:100%;
                border-collapse:collapse;
            }
            th,td{
                padding:14px 12px;
                text-align:center;
                border-bottom:1px solid #e2e8f0;
            }
            th{
                background:#edf2f7;
                color:#2d3748;
                font-weight:bold;
            }
            tr:hover{
                background-color:#f7fafc;
            }
            .input-qty{
                width:100px;
                padding:8px;
                border:1px solid #cbd5e0;
                border-radius:6px;
                text-align:center;
            }
            .btn-small{
                padding:6px 10px;
                border:none;
                border-radius:6px;
                color:white;
                cursor:pointer;
                margin:2px;
            }
            .in-btn{
                background:#38a169;
            }
            .out-btn{
                background:#e53e3e;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header-card">
                <h2>📦 智能仓储物料管理平台</h2>
                <div class="btn-group">
                    <a href="/analysis"><button class="btn-primary">智能AI分析面板</button></a>
                    <a href="/simulate"><button class="btn-success">自动模拟出入库数据</button></a>
                </div>
            </div>
            <div class="card">
                <table>
                    <tr>
                        <th>物料ID</th>
                        <th>物料名称</th>
                        <th>安全库存</th>
                        <th>当前库存</th>
                        <th>操作数量</th>
                        <th>入库操作</th>
                        <th>出库操作</th>
                    </tr>
    """
    for mat in materials:
        html += f"""
        <tr>
            <td>{mat.id}</td>
            <td>{mat.name}</td>
            <td>{mat.safety_stock}</td>
            <td>{mat.current_stock}</td>
            <form action="/stock_io" method="post">
                <td><input class="input-qty" type="number" step="0.1" name="qty" required></td>
                <td>
                    <input type="hidden" name="mid" value="{mat.id}">
                    <button type="submit" name="opt" value="in" class="btn-small in-btn">入库</button>
                </td>
                <td>
                    <button type="submit" name="opt" value="out" class="btn-small out-btn">出库</button>
                </td>
            </form>
        </tr>
        """
    html += "</table></div></div></body></html>"
    return html

# 【新增】一键模拟批量生成出库记录接口
@app.get("/simulate", response_class=HTMLResponse)
def simulate_data(db:Session=Depends(get_db)):
    # 选择物料ID=1生成20条历史出库记录，直接满足AI预测条件
    mid = 1
    for i in range(20):
        dt = datetime.now() - timedelta(days=i)
        qty = random.randint(8,22)
        rec = StockRecord(material_id=mid, io_type="out", quantity=qty, create_time=dt)
        db.add(rec)
    db.commit()
    html = """
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body{background:#f4f7fa; font-family:Microsoft YaHei; padding:40px;text-align:center;}
            .card{background:white;max-width:500px;margin:0 auto;padding:30px;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.08);}
            .success-text{color:#38a169;font-size:20px;margin-bottom:20px;}
            a button{padding:10px 16px;border:none;border-radius:8px;background:#3182ce;color:white;cursor:pointer;}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="success-text">✅ 模拟数据生成成功！</div>
            <p>已为物料ID=1生成20条出库历史记录，现在可以进入AI分析面板查看预测结果</p>
            <br>
            <a href="/analysis"><button>前往AI智能分析面板</button></a>
            &nbsp;&nbsp;
            <a href="/"><button>返回首页库存</button></a>
        </div>
    </body>
    </html>
    """
    return html

#出入库接口
@app.post("/stock_io")
def stock_io(
    mid: int = Form(),
    opt: str = Form(),
    qty: float = Form(),
    db: Session = Depends(get_db)
):
    mat = db.query(Material).filter(Material.id == mid).first()
    if not mat:
        return "物料不存在 <a href='/'>返回</a>"
    if opt == "in":
        mat.current_stock += qty
        rec = StockRecord(material_id=mid, io_type="in", quantity=qty)
    else:
        new_stock = mat.current_stock - qty
        mat.current_stock = max(0, new_stock)
        rec = StockRecord(material_id=mid, io_type="out", quantity=qty)
    db.add(rec)
    db.commit()

    #机器学习 孤立森林异常检测
    records = db.query(StockRecord).filter(StockRecord.material_id == mid).all()
    if len(records) >=5:
        df = pd.DataFrame([{"quantity":r.quantity} for r in records])
        model = IsolationForest(contamination=0.1, random_state=42)
        df["pred"] = model.fit_predict(df[["quantity"]])
        if df.iloc[-1]["pred"] == -1:
            rec.is_abnormal = True
            db.commit()
    return RedirectResponse("/", status_code=303)


# ========== AI智能分析页面 升级UI ==========
@app.get("/analysis", response_class=HTMLResponse)
def analysis_page(db:Session=Depends(get_db)):
    materials = db.query(Material).all()
    html = """
    <html>
    <head>
        <meta charset="utf-8">
        <title>AI智能分析面板</title>
        <style>
            * {
                margin:0;
                padding:0;
                box-sizing:border-box;
                font-family:Microsoft YaHei, sans-serif;
            }
            body{
                background-color:#f4f7fa;
                padding:30px;
            }
            .container{
                max-width:1200px;
                margin:0 auto;
            }
            .header-card{
                background:#fff;
                padding:20px;
                border-radius:12px;
                box-shadow:0 2px 12px rgba(0,0,0,0.08);
                margin-bottom:20px;
                display:flex;
                justify-content:space-between;
                align-items:center;
            }
            h2{
                color:#2d3748;
            }
            .back-btn{
                padding:10px 16px;
                border:none;
                border-radius:8px;
                background:#3182ce;
                color:white;
                cursor:pointer;
            }
            .card{
                background:#fff;
                border-radius:12px;
                box-shadow:0 2px 12px rgba(0,0,0,0.08);
                padding:20px;
            }
            table{
                width:100%;
                border-collapse:collapse;
            }
            th,td{
                padding:14px 12px;
                text-align:center;
                border-bottom:1px solid #e2e8f0;
            }
            th{
                background:#edf2f7;
                color:#2d3748;
                font-weight:bold;
            }
            tr:hover{
                background-color:#f7fafc;
            }
            .status-normal{
                color:#38a169;
                font-weight:bold;
            }
            .status-risk{
                color:#d69e2e;
                font-weight:bold;
            }
            .status-danger{
                color:#e53e3e;
                font-weight:bold;
            }
            .status-empty{
                color:#718096;
            }
            a .detail-btn{
                padding:6px 10px;
                background:#805ad5;
                color:white;
                text-decoration:none;
                border-radius:6px;
                font-size:14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header-card">
                <h2>📊 智能库存分析面板｜统计学习+机器学习+PHM库存健康评估</h2>
                <a href="/"><button class="back-btn">返回首页库存</button></a>
            </div>
            <div class="card">
                <table>
                    <tr>
                        <th>物料ID</th>
                        <th>物料名称</th>
                        <th>当前库存</th>
                        <th>预测未来7天消耗</th>
                        <th>建议补货量</th>
                        <th>库存健康状态(PHM)</th>
                        <th>操作</th>
                    </tr>
    """
    for mat in materials:
        #1.统计学习 ARIMA时序预测
        records = db.query(StockRecord).filter(StockRecord.material_id == mat.id, StockRecord.io_type=="out").all()
        pred_consume = 0
        suggest_supply =0
        health_status = "数据不足"
        status_class = "status-empty"
        remark = "出库记录≥6条才能评估"
        if len(records)>=6:
            df = pd.DataFrame([{"time":r.create_time,"qty":r.quantity} for r in records])
            df = df.sort_values("time")
            ts = df["qty"].values
            model = ARIMA(ts, order=(1,1,0))
            res = model.fit()
            pred = res.get_forecast(steps=7)
            pred_consume = float(pred.predicted_mean[0])
            suggest_supply = max(0, pred_consume + mat.safety_stock - mat.current_stock)

            #2.PHM库存健康评估
            if mat.current_stock >= pred_consume + mat.safety_stock:
                health_status = "正常"
                status_class = "status-normal"
                remark="库存充足"
            elif mat.current_stock < mat.safety_stock:
                health_status = "短缺风险"
                status_class = "status-danger"
                remark="库存低于安全库存，尽快补货"
            else:
                health_status = "积压风险"
                status_class = "status-risk"
                remark="库存偏高"

            #更新预测结果，不重复新增
            pre = db.query(PredictResult).filter(PredictResult.material_id == mat.id).first()
            if pre:
                pre.predict_consume = pred_consume
                pre.suggest_supply = suggest_supply
                pre.create_time = datetime.now()
            else:
                pre = PredictResult(material_id=mat.id, predict_consume=pred_consume, suggest_supply=suggest_supply)
                db.add(pre)

            health = db.query(StockHealth).filter(StockHealth.material_id == mat.id).first()
            if health:
                health.health_status = health_status
                health.remark = remark
                health.create_time = datetime.now()
            else:
                health = StockHealth(material_id=mat.id, health_status=health_status, remark=remark)
                db.add(health)
            db.commit()
        html += f"""
        <tr>
            <td>{mat.id}</td>
            <td>{mat.name}</td>
            <td>{mat.current_stock:.2f}</td>
            <td>{pred_consume:.2f}</td>
            <td>{suggest_supply:.2f}</td>
            <td class="{status_class}">{health_status}</td>
            <td><a href="/detail/{mat.id}" class="detail-btn">查看异常记录</a></td>
        </tr>
        """
    html += "</table></div></div></body></html>"
    return html

#查看异常出入库记录页面，同步升级UI
@app.get("/detail/{mid}", response_class=HTMLResponse)
def detail(mid:int, db:Session=Depends(get_db)):
    recs = db.query(StockRecord).filter(StockRecord.material_id==mid).all()
    html = """
    <html>
    <head>
        <meta charset="utf-8">
        <title>物料出入库明细</title>
        <style>
            * {margin:0;padding:0;box-sizing:border-box;font-family:Microsoft YaHei;}
            body{background:#f4f7fa;padding:30px;}
            .container{max-width:1000px;margin:0 auto;}
            .header-card{background:#fff;padding:20px;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.08);margin-bottom:20px;display:flex;justify-content:space-between;align-items:center;}
            h2{color:#2d3748;}
            .back-btn{padding:10px 16px;border:none;border-radius:8px;background:#3182ce;color:white;cursor:pointer;}
            .card{background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.08);padding:20px;}
            table{width:100%;border-collapse:collapse;}
            th,td{padding:14px 12px;text-align:center;border-bottom:1px solid #e2e8f0;}
            th{background:#edf2f7;color:#2d3748;font-weight:bold;}
            tr:hover{background-color:#f7fafc;}
            .abnormal{color:#e53e3e;font-weight:bold;}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header-card">
                <h2>📋 物料出入库记录详情，红色为异常操作</h2>
                <a href="/analysis"><button class="back-btn">返回AI分析面板</button></a>
            </div>
            <div class="card">
                <table>
                    <tr><th>出入库类型</th><th>数量</th><th>操作时间</th><th>是否异常记录</th></tr>
    """
    for r in recs:
        css_class = "abnormal" if r.is_abnormal else ""
        html += f"""
        <tr class="{css_class}">
            <td>{r.io_type}</td><td>{r.quantity}</td><td>{r.create_time}</td><td>{r.is_abnormal}</td>
        </tr>
        """
    html += "</table></div></div></body></html>"
    return html

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
