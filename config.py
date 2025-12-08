# 导入os模块用于读取环境变量
import os

# 数据库配置
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')  # 您的MySQL用户名
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '287323')  # 用户提供的密码
MYSQL_DB = os.getenv('MYSQL_DB', 'login_system')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
MYSQL_CHARSET = 'utf8mb4'
MYSQL_CURSORCLASS = 'DictCursor'

# MySQL连接池配置
MYSQL_POOL_SIZE = int(os.getenv('MYSQL_POOL_SIZE', 5))
MYSQL_POOL_TIMEOUT = int(os.getenv('MYSQL_POOL_TIMEOUT', 30))
MYSQL_POOL_RECYCLE = int(os.getenv('MYSQL_POOL_RECYCLE', 3600))
MYSQL_POOL_PRE_PING = True

# Flask配置
# 使用强随机生成的密钥用于会话加密
SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'your_very_secure_secret_key_1234567890!@#$%^&*()')

# 会话配置
SESSION_TYPE = os.getenv('SESSION_TYPE', 'filesystem')
SESSION_PERMANENT = os.getenv('SESSION_PERMANENT', 'False').lower() in ['true', '1', 'yes']
PERMANENT_SESSION_LIFETIME = int(os.getenv('PERMANENT_SESSION_LIFETIME', 3600))  # 1小时

# 安全配置
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() in ['true', '1', 'yes']  # 生产环境应设为True
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() in ['true', '1', 'yes']  # 生产环境应设为True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')  # 使用Lax以确保同域请求正确传递cookie
SESSION_COOKIE_PATH = '/'  # 确保cookie在整个应用中都可用

# SSL/TLS配置
SSL_CERT_FILE = os.getenv('SSL_CERT_FILE')
SSL_KEY_FILE = os.getenv('SSL_KEY_FILE')
