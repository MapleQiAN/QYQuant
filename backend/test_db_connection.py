"""
测试 PostgreSQL 连接并创建数据库（如果不存在）
"""
import psycopg2
from psycopg2 import OperationalError

# 连接参数
db_config = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
}

def test_connection():
    """测试连接到 PostgreSQL"""
    try:
        # 先连接到默认的 postgres 数据库
        conn = psycopg2.connect(dbname='postgres', **db_config)
        conn.autocommit = True
        cursor = conn.cursor()

        print("✓ 成功连接到 PostgreSQL 服务器")

        # 检查 qyquant 数据库是否存在
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='qyquant'")
        exists = cursor.fetchone()

        if not exists:
            print("→ 数据库 'qyquant' 不存在，正在创建...")
            cursor.execute("CREATE DATABASE qyquant")
            print("✓ 成功创建数据库 'qyquant'")
        else:
            print("✓ 数据库 'qyquant' 已存在")

        cursor.close()
        conn.close()

        # 测试连接到 qyquant 数据库
        conn2 = psycopg2.connect(dbname='qyquant', **db_config)
        print("✓ 成功连接到数据库 'qyquant'")
        conn2.close()

        return True

    except OperationalError as e:
        print(f"✗ 连接失败: {e}")
        print("\n可能的原因:")
        print("1. PostgreSQL 服务未运行")
        print("2. 用户名或密码不正确（当前: postgres/postgres）")
        print("3. PostgreSQL 未安装")
        print("\n请检查数据库配置:")
        print(f"   主机: {db_config['host']}:{db_config['port']}")
        print(f"   用户: {db_config['user']}")
        return False
    except Exception as e:
        print(f"✗ 发生错误: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("PostgreSQL 连接测试")
    print("=" * 50)
    test_connection()
