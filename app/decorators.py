from functools import wraps
from flask import session, redirect, url_for, request
from app.utils import execute_db_query, make_json_response

# 登录检查装饰器
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        # 检查传统的session（用于网页和API登录）
        if 'logged_in' in session:
            return f(*args, **kwargs)
        
        # 如果是API请求，返回未登录响应
        if request.path.startswith('/api/'):
            return make_json_response(401, '未登录')
        
        # 如果是Web请求，重定向到登录页面
        return redirect(url_for('login_page'))
    return wrap

# 角色检查装饰器
def requires_role(role):
    def decorator(f):
        @wraps(f)
        def wrap(*args, **kwargs):
            if 'logged_in' in session:
                # 获取当前用户信息
                user = execute_db_query('SELECT * FROM users WHERE username = %s', [session['username']], fetch_one=True)
                if user and user['role'] == role:
                    return f(*args, **kwargs)
                else:
                    # 如果是API请求，返回JSON响应
                    if request.path.startswith('/api/'):
                        return make_json_response(403, '权限不足')
                    # 如果是Web请求，重定向到登录页面或显示错误
                    return redirect(url_for('login_page'))
            else:
                # 如果是API请求，返回JSON响应
                if request.path.startswith('/api/'):
                    return make_json_response(401, '未登录')
                # 如果是Web请求，重定向到登录页面
                return redirect(url_for('login_page'))
        return wrap
    return decorator

# 权限检查装饰器
def requires_permission(permission):
    def decorator(f):
        @wraps(f)
        def wrap(*args, **kwargs):
            if 'logged_in' in session:
                # 获取当前用户信息
                user = execute_db_query('SELECT * FROM users WHERE username = %s', [session['username']], fetch_one=True)
                if user:
                    # 只检查角色权限
                    role_permissions = []
                    if user['role']:
                        role = execute_db_query('SELECT * FROM roles WHERE role = %s', [user['role']], fetch_one=True)
                        if role:
                            role_permissions = role.get('permissions', '[]')
                            if isinstance(role_permissions, str):
                                import json
                                role_permissions = json.loads(role_permissions)
                    
                    # 检查是否有需要的权限
                    if permission in set(role_permissions):
                        return f(*args, **kwargs)
                
                # 如果是API请求，返回JSON响应
                if request.path.startswith('/api/'):
                    return make_json_response(403, '权限不足')
                # 如果是Web请求，重定向到登录页面或显示错误
                return redirect(url_for('login_page'))
            else:
                # 如果是API请求，返回JSON响应
                if request.path.startswith('/api/'):
                    return make_json_response(401, '未登录')
                # 如果是Web请求，重定向到登录页面
                return redirect(url_for('login_page'))
        return wrap
    return decorator
