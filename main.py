# main.py
from fastapi import FastAPI,Request,Depends,Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import sessionmaker,Session
from models import engine,Material,StockRecord,StockAlarm,AgvTask,PredictResult

app = FastAPI(title="仓储预测AGV调度系统")
SessionLocal = sessionmaker(bind=engine,autocommit=False,autoflush=False)

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/",response_class=HTMLResponse)
async def index(request:Request,db:Session=Depends(get_db)):
    mats = db.query(Material).all()
    html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>仓储物料管理系统</title>
    <style>
*{box-sizing:border-box;font-family:Microsoft Yahei;}
body{padding:20px;margin:0;background:#f4f7fa;}
.box{background:#fff;padding:20px;border-radius:8px;margin-bottom:20px;box-shadow:0 1px 4px #00000018;}
table{width:100%;border-collapse:collapse;}
th,td{border:1px solid #ddd;padding:8px 12px;text-align:center;}
th{background:#2b7bba;color:white;}
button{padding:6px 12px;border:none;border-radius:4px;background:#2b7bba;color:#fff;cursor:pointer;margin:2px;}
button.red{background:#dc3545;}
input{padding:6px;width:120px;margin:0 4px;}
</style>
</head>
<body>
<h1>仓储物料管理系统</h1>
<div class="box">
    <h3>物料列表</h3>
    <table>
        <tr>
            <th>ID</th>
            <th>物料名称</th>
            <th>安全库存</th>
            <th>当前库存</th>
            <th>操作(输入数量再点按钮)</th>
        </tr>
"""
    for m in mats:
        html +=f"""
        <tr>
            <td>{m.id}</td>
            <td>{m.material_name}</td>
            <td>{m.safe_stock}</td>
            <td>{m.current_stock}</td>
            <td>
                <input type="number" id="q_{m.id}" value="10">
                <button onclick="stockIn({m.id})">入库</button>
                <button class="red" onclick="stockOut({m.id})">出库</button>
            </td>
        </tr>
"""
    html+="""
    </table>
</div>
<script>
async function stockIn(mid){
    let q = document.getElementById("q_"+mid).value;
    let fd=new FormData();
    fd.append("material_id",mid);
    fd.append("op_type","in");
    fd.append("qty",parseInt(q));
    const res = await fetch("/stock_io",{method:"POST",body:fd});
    const ret = await res.json();
    console.log(ret);
    location.reload();
}
async function stockOut(mid){
    let q = document.getElementById("q_"+mid).value;
    let fd=new FormData();
    fd.append("material_id",mid);
    fd.append("op_type","out");
    fd.append("qty",parseInt(q));
    const res = await fetch("/stock_io",{method:"POST",body:fd});
    const ret = await res.json();
    console.log(ret);
    location.reload();
}
</script>
</body>
</html>
"""
    return HTMLResponse(content=html)


@app.post("/stock_io")
def stock_io(
    material_id:int=Form(...),
    op_type:str=Form(...),
    qty:int=Form(...),
    db:Session=Depends(get_db)
):
    mat = db.query(Material).filter(Material.id==material_id).first()
    if not mat:
        return {"code":-1,"msg":"物料不存在"}
    if op_type=="in":
        mat.current_stock += qty
    else:
        mat.current_stock = max(0,mat.current_stock-qty)
    rec = StockRecord(material_id=material_id,op_type=op_type,qty=qty)
    db.add(rec)
    db.commit()
    return {"code":0,"current_stock":mat.current_stock}

if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app",host="127.0.0.1",port=8000,reload=True)





