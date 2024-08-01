from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error

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

app = Flask(__name__)

# 配置 CORS
CORS(app)

@app.route('/api/data', methods=['GET'])
def get_data():
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=10, type=int)

    conn = create_connection()
    if conn is None:
        return jsonify({"error": "无法连接到数据库"}), 500

    cursor = conn.cursor(dictionary=True)
    offset = (page - 1) * limit
    cursor.execute("SELECT number, update_log, summary, link, keywords FROM articles LIMIT %s OFFSET %s", (limit, offset))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    for row in rows:
        if isinstance(row['keywords'], str):
            row['keywords'] = row['keywords'].split(',')  # 将关键词从字符串转换为列表
        else:
            row['keywords'] = []  # 如果不是字符串，则设置为一个空列表

    return jsonify(rows)

if __name__ == '__main__':
    app.run(debug=True)
