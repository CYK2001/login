from flask import Flask, session, request
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect
import config
import os
import json

# 创建Flask应用实例，显式指定模板目录和静态目录路径
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates'),
            static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static'))

# 加载配置
app.config.from_object(config)

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
app.logger.info('正在启动调度器...')
with app.app_context():
    start_scheduler()
app.logger.info('调度器启动完成')
