from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List
import mysql.connector
from mysql.connector import Error
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

# 允许跨域请求的来源
origins = [
    "http://localhost:3000",  # React开发服务器的URL
"http://localhost:3001",  # React开发服务器的URL
]

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'feishuandopenai',
    'raise_on_warnings': True,
    'use_unicode': True,
    'charset': 'utf8mb4'
}

# 创建 MySQL 数据库连接
def create_connection():
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            print('成功连接到 MySQL 数据库')
    except Error as e:
        print(f"连接 MySQL 数据库时发生错误: {e}")
    return conn

class Article(BaseModel):
    number: int
    update_log: str
    summary: str
    link: str
    keywords: List[str]

@app.get("/api/data", response_model=List[Article])
async def get_data(page: int = Query(1, le=100), limit: int = Query(10, le=100)):
    conn = create_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="无法连接到数据库")

    cursor = conn.cursor(dictionary=True)
    offset = (page - 1) * limit
    cursor.execute("SELECT number, update_log, summary, link, keywords FROM articles LIMIT %s OFFSET %s", (limit, offset))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    # 处理 keywords 列
    for row in rows:
        if isinstance(row['keywords'], str):
            row['keywords'] = row['keywords'].split(',')  # 将关键词从字符串转换为列表
        else:
            row['keywords'] = []  # 如果不是字符串，则设置为一个空列表

    return rows

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
