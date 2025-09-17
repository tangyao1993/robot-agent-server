import aiomysql
import logging
import asyncio

logger = logging.getLogger("DatabaseManager")

class DatabaseManager:
    """处理所有与MySQL数据库的异步交互"""

    def __init__(self, host, port, user, password, db):
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._db = db
        self._pool = None

    async def connect(self):
        """创建数据库连接池"""
        try:
            self._pool = await aiomysql.create_pool(
                host=self._host,
                port=self._port,
                user=self._user,
                password=self._password,
                db=self._db,
                autocommit=True,
                loop=asyncio.get_event_loop()
            )
            logger.info("数据库连接池创建成功")
        except Exception as e:
            logger.error(f"无法创建数据库连接池: {e}", exc_info=True)
            raise

    def get_pool(self):
        """安全地获取数据库连接池"""
        return self._pool

    async def close(self):
        """关闭数据库连接池"""
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            logger.info("数据库连接池已关闭")

    async def get_device(self, mac_addr: str):
        """根据MAC地址查询设备信息"""
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM device WHERE mac_addr = %s", (mac_addr,))
                return await cursor.fetchone()

    async def register_device(self, mac_addr: str):
        """注册新设备"""
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "INSERT INTO device (mac_addr, login_time) VALUES (%s, NOW())",
                    (mac_addr,)
                )
                logger.info(f"新设备已注册，MAC地址: {mac_addr}")

    async def update_device_login(self, mac_addr: str):
        """更新设备的最后登录时间"""
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "UPDATE device SET login_time = NOW() WHERE mac_addr = %s",
                    (mac_addr,)
                )
    
    async def get_memory(self, mac_addr: str) -> str | None:
        """获取设备的长期记忆（摘要）"""
        device = await self.get_device(mac_addr)
        if device and device.get('memory'):
            logger.info(f"已为设备 {mac_addr} 加载记忆")
            return device['memory']
        logger.info(f"设备 {mac_addr} 没有找到历史记忆")
        return None

    async def save_memory(self, mac_addr: str, memory: str):
        """保存设备的长期记忆（摘要）"""
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "UPDATE device SET memory = %s WHERE mac_addr = %s",
                    (memory, mac_addr)
                )
                logger.info(f"已为设备 {mac_addr} 保存对话摘要") 



# 数据库配置
DB_HOST = "146.56.246.38"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = "wznba778899"
DB_NAME = "robot-ai"

db_manager = DatabaseManager(DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME)