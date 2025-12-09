from flask import Flask, session, request
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect
import config
import os
import json
import logging
from logging.handlers import TimedRotatingFileHandler

# 配置日志
def setup_logging(app):
    # 创建日志目录
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 创建日志格式器
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    
    # 创建文件日志处理器（每天自动轮换）
    log_file = os.path.join(log_dir, 'app.log')
    # when='midnight' 表示每天凌晨轮换
    # backupCount=0 表示不保留旧文件（我们将手动处理备份）
    file_handler = TimedRotatingFileHandler(
        log_file,
        when='midnight',
        interval=1,
        backupCount=0,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)  # 改为DEBUG级别以便调试
    
    # 清除默认处理器
    app.logger.handlers.clear()
    
    # 添加自定义处理器（只保留文件日志，不输出到控制台）
    app.logger.addHandler(file_handler)
    
    # 设置日志级别
    app.logger.setLevel(logging.INFO)  # 改为DEBUG级别以便调试
    
    # 配置Werkzeug日志器（Flask底层的HTTP服务器）
    # 获取Werkzeug的日志器
    werkzeug_logger = logging.getLogger('werkzeug')
    # 清除Werkzeug的默认处理器（避免输出到终端）
    werkzeug_logger.handlers.clear()
    # 添加文件处理器
    werkzeug_logger.addHandler(file_handler)
    # 设置日志级别
    werkzeug_logger.setLevel(logging.INFO)

# 创建Flask应用实例，显式指定模板目录和静态目录路径
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates'),
            static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static'))

# 加载配置
app.config.from_object(config)

# 根据环境变量设置生产/开发模式
if os.environ.get('FLASK_ENV') == 'production':
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    # 确保生产环境下的安全配置
    app.config['SECURE_SSL_REDIRECT'] = True
    app.config['SESSION_COOKIE_SECURE'] = True
else:
    app.config['DEBUG'] = True
    app.config['TESTING'] = True

# 初始化日志配置
setup_logging(app)

# 安全配置 - 添加XSS防护头
app.config['SECURE_CONTENT_TYPE_NOSNIFF'] = True
app.config['X_CONTENT_TYPE_OPTIONS'] = 'nosniff'
app.config['X_XSS_PROTECTION'] = '1; mode=block'
app.config['CONTENT_SECURITY_POLICY'] = "default-src 'self'"

# 初始化MySQL
mysql = MySQL(app)

# 初始化CSRF保护
csrf = CSRFProtect(app)

# 权限列表将从数据库动态获取

# 中间件：解析请求头中的Cookie并加载到Flask session中
@app.before_request
def parse_cookie_to_session():
    if 'Cookie' in request.headers:
        from flask.sessions import SecureCookieSessionInterface
        cookie_value = request.headers.get('Cookie')
        # 查找session=开头的Cookie
        session_cookie = None
        for cookie in cookie_value.split(';'):
            cookie = cookie.strip()
            if cookie.startswith('session='):
                session_cookie = cookie[8:]  # 去掉session=前缀
                break
        
        if session_cookie:
            # 解析并加载session数据
            interface = SecureCookieSessionInterface()
            try:
                session_data = interface.get_signing_serializer(app).loads(session_cookie)
                # 先清空当前session，然后加载新的session数据
                session.clear()
                session.update(session_data)
            except Exception:
                # 如果解析失败，忽略该Cookie
                pass

# 上下文处理器：提供模板中可用的全局函数和变量
@app.context_processor
def inject_permission_check():
    def current_user_has_permission(permission):
        if 'logged_in' in session:
            from app.utils import execute_db_query
            
            # 获取当前用户信息
            user = execute_db_query('SELECT * FROM users WHERE username = %s', 
                                  [session['username']], fetch_one=True)
            
            if user and user.get('role'):
                # 获取角色权限
                role = execute_db_query('SELECT * FROM roles WHERE role = %s', 
                                      [user['role']], fetch_one=True)
                
                if role:
                    role_permissions = role.get('permissions', '[]')
                    if isinstance(role_permissions, str):
                        role_permissions = json.loads(role_permissions)
                    
                    # 检查是否有需要的权限
                    return permission in set(role_permissions)
        
        return False
    
    # 从数据库获取权限列表
    try:
        from app.utils import execute_db_query
        permissions = execute_db_query('SELECT permission FROM role_permissions ORDER BY id')
        PERMISSION_NAMES = [p['permission'] for p in permissions]
    except Exception as e:
        app.logger.error(f"获取权限列表失败: {e}")
        PERMISSION_NAMES = []
    
    # 提供PERMISSION_NAMES给模板
    return dict(
        current_user_has_permission=current_user_has_permission,
        PERMISSION_NAMES=PERMISSION_NAMES
    )

# 导入路由模块
from app import routes
from app import auth_routes
from app import user_routes
from app import role_routes
from app import audit_routes
from app import profile_routes

# 导入定时任务模块
app.logger.info('正在导入定时任务模块...')
from app.scheduler import start_scheduler
app.logger.info('定时任务模块导入完成')

# 应用启动时启动调度器
import os
# 检查是否在开发环境的重载器中运行
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or os.environ.get('FLASK_ENV') == 'production':
    # 在生产环境下直接启动调度器
    # 在开发环境下，只在实际运行的子进程中启动调度器，避免在重载器中启动两次
    app.logger.info('正在启动调度器...')
    with app.app_context():
        start_scheduler()
    app.logger.info('调度器启动完成')
