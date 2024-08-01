# data_fetcher.py
import asyncio
from playwright.async_api import async_playwright
import requests
import mysql.connector
from mysql.connector import Error
import hashlib
from datetime import datetime

# 存在的问题：1.重复点击链接的去重判断，根据link_hash进行判断，重复则不去交给gpt，直接偏移，，，，重复点击，无法插入数据带来的number不连续的问题
# 2:坐标左对齐，居中的问题
#3：坐标回退判断
#4：点击链接以后，没有进行插入数据，number已经+1，后端服务崩溃，number不连续的问题
#5：有时候在一个单元格内不去滑动，不知道什么原因，文本内容太长，超出单元格范围，无法滚动
# 6：服务重启滑动距离不对

# 替换为你的 OneAI API 密钥
api_key = 'sk-ozYXQPQjeu0xCHFg0a1f329dA2194689931b8a6a6809558c'
api_url = 'https://api.ezchat.top/v1/chat/completions'

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json',
}

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


def create_table(conn):
    try:
        cursor = conn.cursor()
        # 创建文章表
        sql_create_articles_table = """
            CREATE TABLE IF NOT EXISTS articles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                number INT NOT NULL,
                update_log TEXT,
                summary TEXT,
                link TEXT,
                link_hash CHAR(64) UNIQUE,  # 链接哈希唯一约束
                keywords TEXT
            );
            """
        cursor.execute(sql_create_articles_table)

        # 创建滑动状态和点击次数表
        sql_create_scroll_state_table = """
            CREATE TABLE IF NOT EXISTS scroll_state (
                id INT AUTO_INCREMENT PRIMARY KEY,
                last_scroll_y INT NOT NULL,
                scroll_count INT NOT NULL,
                click_count INT NOT NULL  # 添加点击次数字段
            );
            """
        cursor.execute(sql_create_scroll_state_table)

        # 插入初始化记录，如果表为空
        cursor.execute("""
                INSERT IGNORE INTO scroll_state (id, last_scroll_y, scroll_count, click_count)
                VALUES (1, 6, 0, 0)
            """)
        conn.commit()

    except Error as e:
        print(f"创建表格时发生错误: {e}")



def generate_link_hash(url):
    """生成链接的唯一哈希值"""
    return hashlib.sha256(url.encode('utf-8')).hexdigest()


def insert_article(conn, article):
    link_hash = generate_link_hash(article['link'])
    cursor = conn.cursor()

    # 检查记录是否已经存在
    cursor.execute("SELECT COUNT(*) FROM articles WHERE link_hash = %s", (link_hash,))
    if cursor.fetchone()[0] > 0:
        print(f"记录已存在: {article['link']}")
        return

    # 插入新记录
    sql = """
        INSERT INTO articles (number, update_log, summary, link, link_hash, keywords)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
    cursor.execute(sql, (article['number'], article['update_log'], article['summary'], article['link'], link_hash,
                         article['keywords']))
    conn.commit()
    print("记录插入成功。")


def save_scroll_state(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
                        UPDATE scroll_state
                        SET scroll_count = scroll_count + 1
                        WHERE id = 1
                    """)
        conn.commit()
        print("滑动状态保存成功。")
    except Error as e:
        print(f"保存滑动状态时发生错误: {e}")

def update_click_count(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
                UPDATE scroll_state
                SET click_count = click_count + 1
                WHERE id = 1
            """)
        conn.commit()
        print("点击次数更新成功。")
    except Error as e:
        print(f"更新点击次数时发生错误: {e}")

def get_last_scroll_state(conn):
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT last_scroll_y, scroll_count, click_count FROM scroll_state WHERE id = 1")
        result = cursor.fetchone()
        if result:
            last_scroll_y = int(result['last_scroll_y'])
            scroll_count = int(result['scroll_count'])
            click_count = int(result['click_count'])
            return last_scroll_y, scroll_count, click_count
        else:
            return 6, 0, 0  # 默认值
    except Error as e:
        print(f"获取滑动状态时发生错误: {e}")
        return 6, 0, 0  # 默认值


async def extract_article_data(page):
    await page.wait_for_load_state('networkidle', timeout=120000)
    content = await page.evaluate('''
            () => {
                return document.body.innerText;
            }
        ''')
    return content


async def handle_login(page):
    try:
        await page.wait_for_selector(".lite-login-dialog__inner", timeout=30000)
        close_button = await page.query_selector(".lite-login-dialog__close")
        if close_button:
            await close_button.click()
            print("登录弹窗已关闭")
    except Exception as e:
        print(f"登录弹窗处理错误: {e}")


async def get_gpt_summary_and_title(article_content):
    payload = {
        'model': 'gpt-3.5-turbo',
        'messages': [
            {
                'role': 'system',
                'content': '你是一个帮助生成文章标题和摘要的助手。'
            },
            {
                'role': 'user',
                'content': f"请为以下文章生成一个标题和摘要(摘要就是1-3个概括文章的关键字)：\n\n{article_content}"
            }
        ],
        'max_tokens': 100
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        content = data['choices'][0]['message']['content']

        # 清理返回内容，去掉多余的标签
        lines = content.split('\n')
        title = lines[0].strip() if lines else ''
        summary = ' '.join([line.strip() for line in lines[1:] if line.strip()]) if len(lines) > 1 else ''

        # 去掉可能存在的“标题：”或“摘,要,：”等多余标识
        title = title.replace('标题：', '').replace('标题:', '').strip()
        summary = summary.replace('摘要：', '').replace('摘要:', '').strip()

        return title, summary
    except requests.exceptions.RequestException as e:
        print(f"获取 GPT 响应时发生错误: {e}")
        return None, None


async def fetch_data():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        url = 'https://iqzeljuzeco.feishu.cn/sheets/N5Wts8V9Wh3gXJtyxPvcDbMZnJc'

        # 尝试增加超时时间
        try:
            await page.goto(url, timeout=180000, wait_until='networkidle')
        except TimeoutError as e:
            print(f"页面加载超时: {e}")
            return

        await handle_login(page)
        await page.wait_for_selector('[data-sheet-element="sheetHost"]')

        start_x = 300
        start_y = 245
        offset_y = 6
        max_scrolls = 5  # 最大滑动次数

        conn = create_connection()
        if conn is not None:
            create_table(conn)

            # 恢复上次滑动状态
            last_scroll_y, last_scroll_count, click_count = get_last_scroll_state(conn)
            total_scroll_y = int(last_scroll_count) * offset_y  # 确保 total_scroll_y 是整数

            # 先移动到指定位置
            await page.mouse.move(start_x, start_y)
            # 然后将页面滚动到上次的位置
            await page.mouse.wheel(0, total_scroll_y)
            print(f"恢复到上次位置: 滚动距离 = {total_scroll_y}")

            scroll_count = 0

            while scroll_count < max_scrolls:
                # 点击指定位置
                await page.mouse.move(start_x, start_y)
                await page.mouse.click(start_x, start_y)

                await page.wait_for_timeout(2000)

                current_url = page.url

                # 检查是否有新的页面打开
                new_page = None
                for p in context.pages:
                    if p.url != current_url and p != page:
                        new_page = p
                        break

                if new_page:
                    new_url = new_page.url
                    print(f"新页面的URL: {new_url}")


                    await handle_login(new_page)
                    await new_page.wait_for_load_state('networkidle', timeout=120000)

                    # 保存当前点击链接状态
                    update_click_count(conn)  # 异步调用保存点击状态

                    article_content = await extract_article_data(new_page)

                    title, summary = await get_gpt_summary_and_title(article_content)
                    print("标题:", title)
                    print("摘要:", summary)
                    last_scroll_y, last_scroll_count, click_count = get_last_scroll_state(conn)
                    article = {
                        "number": click_count,
                        "update_log": f"更新于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        "summary": title,
                        "link": new_url,
                        "keywords": summary  # 将摘要作为内容插入
                    }

                    insert_article(conn, article)

                    await new_page.close()
                    scroll_count = 0  # 成功获取到数据，重置滑动计数器
                else:
                    # 如果没有找到新页面，增加滑动计数器
                    scroll_count += 1
                    print(f"未能找到新页面，滑动计数器增加到 {scroll_count}")

                # 滚动页面
                await page.mouse.wheel(0, offset_y)
                print(f"滚动位置: (0, {offset_y})")

                # 保存当前滑动状态
                save_scroll_state(conn)

                await asyncio.sleep(2)

            print("表格数据抓取完成或达到滑动次数限制")
            await browser.close()
            if conn:
                conn.close()


async def main():
    while True:
        await fetch_data()
        print("数据抓取完成，休眠 60 分钟。")
        await asyncio.sleep(3600)  # 每 60 分钟运行一次


if __name__ == '__main__':
    asyncio.run(main())
