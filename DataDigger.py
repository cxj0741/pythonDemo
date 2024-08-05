# data_fetcher.py
import asyncio
import logging
from venv import logger

from playwright.async_api import async_playwright
import requests
import mysql.connector
from mysql.connector import Error
import hashlib
from datetime import datetime

#飞书表格65行无权访问
# 350行数据跳过

# 配置日志记录
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 创建文件处理器
file_handler = logging.FileHandler('test/app.log')
file_handler.setLevel(logging.INFO)

# 创建格式器
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# 将处理器添加到记录器
logger.addHandler(console_handler)
logger.addHandler(file_handler)

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
# 插入一个半透明的红色圆形标记
async def highlight_position(page, x, y, width=10, height=10):
    await page.evaluate(f'''
        () => {{
            const marker = document.createElement('div');
            marker.style.position = 'absolute';
            marker.style.left = '{x - width // 2}px';
            marker.style.top = '{y - height // 2}px';
            marker.style.width = '{width}px';
            marker.style.height = '{height}px';
            marker.style.borderRadius = '50%';
            marker.style.backgroundColor = 'rgba(255, 0, 0, 0.5)';
            marker.style.zIndex = '9999';
            marker.style.pointerEvents = 'none';  // 确保标记不影响点击
            document.body.appendChild(marker);
        }}
    ''')

# 创建表格
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
                VALUES (1, 4, 0, 0)
            """)
        conn.commit()

    except Error as e:
        print(f"创建表格时发生错误: {e}")


# 生成linkhash
def generate_link_hash(url):
    """生成链接的唯一哈希值"""
    return hashlib.sha256(url.encode('utf-8')).hexdigest()

# 插入文章信息
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

#更新滑动次数
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

# 更新点击次数
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

# 获取点击和滑动次数
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

# 获取文章内容
async def extract_article_data(page):
    await page.wait_for_load_state('networkidle', timeout=120000)
    content = await page.evaluate('''
            () => {
                return document.body.innerText;
            }
        ''')
    return content

# 处理登录弹窗
async def handle_login(page):
    try:
        await page.wait_for_selector(".lite-login-dialog__inner", timeout=30000)
        close_button = await page.query_selector(".lite-login-dialog__close")
        if close_button:
            await close_button.click()
            print("登录弹窗已关闭")
    except Exception as e:
        print(f"登录弹窗处理错误: {e}")



# 获取文章标题和摘要
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



# 最重要的处理数据流程
async def fetch_data():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        # context = await browser.new_context()
        # browser =  playwright.chromium.launch_persistent_context(
        #     user_data_dir=r'C:\Users\86157\AppData\Local\Google\Chrome\User Data',
        #     headless=False  # 设置为 False 以打开浏览器窗口
        # )
        # 启动 Playwright 和持久化上下文
        context = await p.chromium.launch_persistent_context(
            user_data_dir=r'C:\Users\86157\AppData\Local\Google\Chrome\User Data',
            headless=False  # 设置为 False 以打开浏览器窗口
        )

        # 创建新页面
        page = await context.new_page()

        original_url = 'https://iqzeljuzeco.feishu.cn/wiki/W25vw2dnaii2DWkZSGtc2ljFnrh'
        target_url = 'https://iqzeljuzeco.feishu.cn/wiki/HgrMwMLbZivmZekJHB3cn4CBnN4'

        # 前往原始网页
        await page.goto(original_url)

        # 点击选择器来选中全表
        await page.locator("#miniapp-faster canvas").click(position={"x": 35, "y": 13})

        # 按下快捷键复制特定文本
        str = await page.locator("#zh-CN").press("ControlOrMeta+c")

        # 等待复制操作完成
        await page.wait_for_timeout(2000)  # 等待2秒，可以根据实际情况调整

        # 前往目标网页，设置较长的超时时间和等待选项
        # await page.goto(target_url, timeout=180000, wait_until='networkidle')
        await page.goto(target_url)

        # 点击选择器来选中全表
        await page.locator("#miniapp-faster canvas").click(position={"x": 35, "y": 13})

        # 粘贴操作
        await page.locator("#zh-CN").press("ControlOrMeta+v")

        # 等待粘贴操作完成
        await page.wait_for_timeout(2000)  # 等待2秒，可以根据实际情况调整

        # url = 'https://iqzeljuzeco.feishu.cn/sheets/N5Wts8V9Wh3gXJtyxPvcDbMZnJc'
        # url = 'https://iqzeljuzeco.feishu.cn/wiki/W25vw2dnaii2DWkZSGtc2ljFnrh'

        # 尝试增加超时时间
        # try:
        #     await page.goto(url, timeout=180000, wait_until='networkidle')
        # except TimeoutError as e:
        #     print(f"页面加载超时: {e}")
        #     return

        # 处理登录弹窗
        # await handle_login(page)
        # 输入密码（确保选择器正确，可能需要根据实际页面调整）
        # await page.fill('input.password-input', '6#6283B3')
         # 等待按钮启用
        # await page.wait_for_selector('button.password-required-button:not([disabled])', timeout=30000)
        # 提交表单
        # await page.click('button.password-required-button')
        # 等待登录完成（根据需要修改等待条件）
        # await page.wait_for_load_state('networkidle')

        # await handle_login(page)
        # logger.info("将文章列表的登录弹窗关闭")

        await page.wait_for_selector('[data-sheet-element="sheetHost"]')

        # 进行数据备份到自己的飞书表格 createBackup()


        start_x = 300
        start_y = 245
        backup_x = 553
        backup_y = 245
        temp_x = 45  # 临时鼠标位置 x
        temp_y = 245   # 临时鼠标位置 y
        offset_y = 4
        max_scrolls = 8  # 最大滑动次数
        max_clicks_without_data = 8  # 连续点击次数阈值

        conn = create_connection()
        if conn is not None:
            create_table(conn)

            # 恢复上次滑动状态
            last_scroll_y, last_scroll_count, click_count = get_last_scroll_state(conn)


            # 初始化当前坐标为默认坐标
            current_x, current_y = start_x, start_y
            click_count_without_data = 0
            scroll_count = 0

            # 先移动到指定位置
            await page.mouse.move(current_x, current_y)
            await highlight_position(page, current_x, current_y)  # 添加高亮
            # 然后将页面滚动到上次的位置
            # 多次调用滚动
            for _ in range(last_scroll_count):
                await page.mouse.wheel(0, last_scroll_y)
                # await asyncio.sleep(0.2)  # 每次滚动后等待片刻
            logger.info(f"恢复上次滑动状态,滑动次数:{last_scroll_count},每次滑动距离:{last_scroll_y}")


            while scroll_count < max_scrolls:
                # 点击指定位置
                await page.mouse.move(current_x, current_y)
                await highlight_position(page, current_x, current_y)  # 添加高亮
                await page.mouse.click(current_x, current_y)

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

                    # 检查新 URL 是否已经访问过
                    link_hash = generate_link_hash(new_url)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM articles WHERE link_hash = %s", (link_hash,))
                    if cursor.fetchone()[0] > 0:
                        print(f"记录已存在: {new_url}")
                        await new_page.close()
                        scroll_count = 0  # 成功获取到数据，重置滑动计数器
                        click_count_without_data = 0  # 重置连续点击计数器
                        # 滚动页面
                        await page.mouse.move(temp_x, temp_y)  # 临时位置
                        await page.mouse.wheel(0, offset_y)  # 执行滚动操作
                        await asyncio.sleep(1)  # 等待滚动完成
                        await page.mouse.move(current_x, current_y)  # 切换回原位置
                        save_scroll_state(conn)
                        print(f"滚动位置: (0, {offset_y})")
                        continue

                    # await handle_login(new_page) #注释调弹窗处理
                    await new_page.wait_for_load_state('networkidle', timeout=120000)

                    # 保存当前点击链接状态
                    update_click_count(conn)

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

                    # 记录所有滑动次数
                    for i in range(scroll_count+1):
                        save_scroll_state(conn)

                    await new_page.close()
                    scroll_count = 0  # 成功获取到数据，重置滑动计数器
                    click_count_without_data = 0  # 重置连续点击计数器
                else:
                    # 如果没有找到新页面，增加滑动计数器
                    click_count_without_data += 1
                    scroll_count+=1
                    print(f"未能找到新页面，连续点击次数增加到 {click_count_without_data}")

                    # 如果连续点击次数达到阈值，切换坐标
                    if click_count_without_data >= max_clicks_without_data:
                        if (current_x, current_y) == (start_x, start_y):
                            current_x, current_y = backup_x, backup_y
                            print(f"切换到备用坐标: ({current_x}, {current_y})")
                            for i in range(max_scrolls):  #进行回退
                                await page.mouse.wheel(0, -last_scroll_y+1)
                                await asyncio.sleep(0.2)  # 每次滚动后等待片刻
                            scroll_count = 0  # 成功获取到数据，重置滑动计数器
                            click_count_without_data = 0  # 重置连续点击计数器
                        else:
                            print("备用坐标点击后仍无数据，结束数据抓取")
                            for i in range(max_scrolls):  # 进行回退
                                await page.mouse.wheel(0, -last_scroll_y+1)
                                await asyncio.sleep(0.2)  # 每次滚动后等待片刻
                            break  # 结束数据抓取

                # 处理长文本导致无法滚动的情况
                await page.mouse.move(temp_x, temp_y)  # 临时位置
                await page.mouse.wheel(0, offset_y)  # 执行滚动操作
                await asyncio.sleep(1)  # 等待滚动完成
                await page.mouse.move(current_x, current_y)  # 切换回原位置
                print(f"滚动位置: (0, {offset_y})")

                # 保存当前滑动状态
                # save_scroll_state(conn) 像这种空滑动先暂且不算

                await asyncio.sleep(2)
                print("-------------------------------------------------------------------------------")

            print("表格数据抓取完成或达到滑动次数限制")
            await browser.close()
            if conn:
                conn.close()



async def main():
    while True:
        try:
            await fetch_data()
            logger.info("数据抓取完成，休眠 60 分钟。")
        except Exception as e:
            logger.error(f"数据抓取过程中发生错误: {e}")
        await asyncio.sleep(300)  # 每 5 分钟运行一次

if __name__ == '__main__':
    asyncio.run(main())