from flask import request, jsonify, session, make_response
from app import mysql, app
import MySQLdb.cursors
import time
import json
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import random
import string
import io
from app.common import convert_datetime_fields, json_loads_safe, json_dumps_safe, str_to_bool

# 辅助函数：生成统一格式的JSON响应
def make_json_response(code, msg, data=None, status_code=200, errors=None):
    """
    统一JSON响应格式
    
    参数:
        code: 业务响应码（自定义）
        msg: 响应消息
        data: 响应数据（可选）
        status_code: HTTP状态码（默认200）
        errors: 错误详情（可选，用于表单验证等场景）
    
    返回:
        JSON响应对象
    """
    response = {
        'code': code,
        'msg': msg,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if data:
        response['data'] = data
    
    if errors:
        response['errors'] = errors
    
    # 设置CORS头部，允许跨域请求
    json_response = jsonify(response)
    json_response.headers.add('Access-Control-Allow-Origin', '*')
    json_response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    json_response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    
    # 设置HTTP状态码
    json_response.status_code = status_code
    
    return json_response

# 辅助函数：获取请求数据（支持JSON、表单和multipart/form-data）
def get_request_data():
    """根据请求类型获取请求数据"""
    try:
        # 优先尝试获取JSON数据，支持所有HTTP方法
        # force=True表示忽略Content-Type，总是尝试解析JSON
        json_data = request.get_json(force=True)
        if json_data is not None:
            return json_data
    except Exception as e:
        app.logger.debug(f"JSON解析错误: {e}")
        pass
    
    # 如果JSON解析失败或没有JSON数据，尝试获取表单数据
    # 将ImmutableMultiDict转换为普通字典以保持一致性
    return dict(request.form) or {}

# 辅助函数：执行数据库查询（自动管理游标）
def execute_db_query(query, params=None, fetch_one=False, commit=False):
    """
    执行数据库查询，自动管理游标和连接
    
    参数:
        query: SQL查询语句
        params: 查询参数（可选）
        fetch_one: 是否只返回一条结果
        commit: 是否提交事务
    
    返回:
        查询结果（根据fetch_one返回单个结果或结果列表）
    """
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # 记录查询开始日志
        query_type = query.strip().split()[0].upper() if query.strip() else 'UNKNOWN'
        app.logger.debug(f"执行数据库查询: {query_type} 查询")
        app.logger.debug(f"SQL语句: {query}")
        app.logger.debug(f"参数: {params}")
        
        # 对于非提交操作，先检查是否有未提交的事务
        if not commit:
            try:
                mysql.connection.commit()
                app.logger.debug("自动提交之前的事务")
            except Exception as e:
                app.logger.debug(f"自动提交事务失败，可能没有未提交的事务: {e}")
        
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        
        if commit:
            mysql.connection.commit()
            app.logger.debug("事务提交成功")
            # 返回游标对象，以便获取rowcount等属性
            return cur
        
        # 处理查询结果
        if fetch_one:
            result = cur.fetchone()
            if result:
                result = convert_datetime_fields(result)
            app.logger.debug(f"查询完成，返回1条记录")
            return result
        else:
            results = cur.fetchall()
            if results:
                results = convert_datetime_fields(results)
            app.logger.debug(f"查询完成，返回{len(results) if results else 0}条记录")
            return results
    except Exception as e:
        # 发生错误时回滚事务
        mysql.connection.rollback()
        app.logger.error(f"数据库查询错误: {str(e)}")
        app.logger.error(f"SQL语句: {query}")
        app.logger.error(f"参数: {params}")
        app.logger.exception("异常堆栈信息")
        raise
    finally:
        cur.close()
        app.logger.debug("数据库游标已关闭")

# 缓存装饰器
cache = {}

def clear_cache():
    """清除所有缓存"""
    global cache
    cache = {}
    app.logger.info("缓存已清除")

def cached(timeout=300):  # 默认缓存5分钟
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 创建缓存键
            key = str(args) + str(kwargs)
            
            # 检查缓存是否存在且未过期
            if key in cache and (time.time() - cache[key]['time']) < timeout:
                return cache[key]['value']
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache[key] = {'value': result, 'time': time.time()}
            
            return result
        return wrapper
    return decorator




# 辅助函数：格式化审计日志详情
def format_audit_details(action, details):
    """
    根据操作类型格式化审计日志详情，提供更详细的操作描述
    
    参数:
        action (str): 操作类型
        details (dict): 原始操作详情
    
    返回:
        str: 格式化后的操作详情
    """
    if not details:
        return "无详细信息"
    
    # 优先检查result字段
    result = details.get('result', '')
    error_msg = details.get('error') or details.get('reason') or ''
    
    try:
        # 所有成功操作只显示"成功"
        if result == '成功':
            return '成功'
        # 失败操作显示失败原因
        elif result == '失败' or error_msg:
            return f'失败：{error_msg}' if error_msg else '失败'
        
        # 如果没有明确的成功/失败标记，继续原有逻辑
        # 登录操作特殊处理（旧日志可能没有result字段）
        if action == '登录':
            # 对于没有明确result和error的旧日志，默认视为成功
            if not result and not error_msg:
                return '成功'
            result_bool = result == '成功'
            result = '成功' if result_bool else f'失败：{error_msg}'
            return result
        elif action in ['注销', '退出登录']:
            return '成功'
        elif action == '创建用户':
            return '成功'
        elif action == '编辑用户':
            return '成功'
        elif action == '删除用户':
            return '成功'
        elif action == '重置密码':
            return '成功'
        elif action == '批量重置密码':
            return '成功'
        elif action == '修改密码':
            return '成功'
        elif action == '更新角色':
            return '成功'
        elif action == '删除角色':
            return '成功'
        elif action == '批量删除角色':
            return '成功'
        elif action == '创建角色':
            return '成功'
        elif action == '更换头像':
            return '成功'
        elif action == '修改资料':
            return '成功'
        else:
            # 通用格式：如果没有明确的成功/失败标记，使用原有逻辑
            key_map = {
                'result': '结果',
                'username': '用户名',
                'role': '角色',
                'old_role': '原角色',
                'new_role': '新角色',
                'role_name': '角色名称',
                'permissions': '权限数量',
                'error': '错误',
                'reason': '原因',
                'name': '名称'
            }
            entries = []
            for key, value in details.items():
                if key != 'formatted' and value:
                    display_key = key_map.get(key, key)
                    if key == 'permissions' and isinstance(value, list):
                        display_value = f"{len(value)}个"
                    else:
                        display_value = value
                    entries.append(f"{display_key}：{display_value}")
            return '；'.join(entries) if entries else '无详细信息'
    except Exception as e:
        # 如果格式化失败，至少返回成功/失败结果
        if result == '成功':
            return '成功'
        elif result == '失败' or error_msg:
            return f'失败：{error_msg}' if error_msg else '失败'
        else:
            return '成功'


# 辅助函数：记录审计日志
def log_audit(user_id, username, action, target="", details=None):
    """
    记录用户操作审计日志
    
    参数:
        user_id (int): 用户ID
        username (str): 用户名
        action (str): 操作类型，如'登录', '创建用户', '更新角色'等
        target (str): 操作目标，如'用户:admin', '角色:管理员'等
        details (dict): 操作详情
    """
    try:
        # 获取客户端IP地址
        ip_address = request.remote_addr if request else 'unknown'
        
        # 格式化操作详情
        formatted_details = format_audit_details(action, details)
        
        # 将详细信息转换为JSON格式，同时保留原始详情
        details_json = json_dumps_safe({
            **(details or {}),
            "formatted": formatted_details
        })
        
        # 插入审计日志，使用数据库自动生成的时间戳
        query = "INSERT INTO audit_logs (user_id, username, action, target, details, ip_address) VALUES (%s, %s, %s, %s, %s, %s)"
        params = (user_id, username, action, target, details_json, ip_address)
        execute_db_query(query, params, commit=True)
    except Exception:
        # 记录日志失败不影响主流程
        pass

# 创建数据库和表（如果不存在）
def init_db():
    # 连接到MySQL服务器
    conn = mysql.connection
    cur = conn.cursor()
    
    # 创建数据库（如果不存在）
    cur.execute('CREATE DATABASE IF NOT EXISTS login_system')
    
    # 选择数据库
    cur.execute('USE login_system')
    
    # 创建用户表（如果不存在）
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            name VARCHAR(50),
            email VARCHAR(100),
            phone VARCHAR(20),
            gender VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 如果表已经存在但缺少字段，添加缺少的字段
    # 添加email字段
    cur.execute("SHOW COLUMNS FROM users LIKE 'email'")
    if cur.fetchone() is None:
        cur.execute("ALTER TABLE users ADD email VARCHAR(100)")
    
    # 添加phone字段
    cur.execute("SHOW COLUMNS FROM users LIKE 'phone'")
    if cur.fetchone() is None:
        cur.execute("ALTER TABLE users ADD phone VARCHAR(20)")
    
    # 添加gender字段
    cur.execute("SHOW COLUMNS FROM users LIKE 'gender'")
    if cur.fetchone() is None:
        cur.execute("ALTER TABLE users ADD gender VARCHAR(10)")
    
    # 移除不需要的字段
    cur.execute("SHOW COLUMNS FROM users LIKE 'is_star'")
    if cur.fetchone() is not None:
        cur.execute("ALTER TABLE users DROP COLUMN is_star")
    
    # 添加created_at字段
    cur.execute("SHOW COLUMNS FROM users LIKE 'created_at'")
    if cur.fetchone() is None:
        cur.execute("ALTER TABLE users ADD created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    
    # 添加name字段
    cur.execute("SHOW COLUMNS FROM users LIKE 'name'")
    if cur.fetchone() is None:
        cur.execute("ALTER TABLE users ADD name VARCHAR(50)")
    
    # 添加avatar字段
    cur.execute("SHOW COLUMNS FROM users LIKE 'avatar'")
    if cur.fetchone() is None:
        cur.execute("ALTER TABLE users ADD avatar VARCHAR(255)")
    
    # 添加role字段
    cur.execute("SHOW COLUMNS FROM users LIKE 'role'")
    if cur.fetchone() is None:
        cur.execute("ALTER TABLE users ADD role VARCHAR(20) DEFAULT '普通用户'")
    
    # 移除不需要的permissions字段
    cur.execute("SHOW COLUMNS FROM users LIKE 'permissions'")
    if cur.fetchone() is not None:
        cur.execute("ALTER TABLE users DROP COLUMN permissions")
    
    # 添加索引优化查询性能
    # 为username字段添加唯一索引
    cur.execute("SHOW INDEX FROM users WHERE Key_name = 'idx_users_username'")
    if cur.fetchone() is None:
        cur.execute("CREATE INDEX idx_users_username ON users (username)")
    
    # 为role字段添加索引
    cur.execute("SHOW INDEX FROM users WHERE Key_name = 'idx_users_role'")
    if cur.fetchone() is None:
        cur.execute("CREATE INDEX idx_users_role ON users (role)")
    
    # 为created_at字段添加索引（用于排序）
    cur.execute("SHOW INDEX FROM users WHERE Key_name = 'idx_users_created_at'")
    if cur.fetchone() is None:
        cur.execute("CREATE INDEX idx_users_created_at ON users (created_at)")
    
    # 创建权限表（如果不存在）
    cur.execute('''
        CREATE TABLE IF NOT EXISTS role_permissions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            permission VARCHAR(50) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 直接定义初始权限列表并插入数据库
    initial_permissions = [
        '个人信息管理',
        '用户管理',
        '角色管理',
        '审计日志管理'
    ]
    for permission in initial_permissions:
        try:
            cur.execute("INSERT IGNORE INTO role_permissions (permission) VALUES (%s)", 
                       (permission,))
        except Exception as e:
            app.logger.debug(f"插入权限数据失败: {e}")
    
    # 创建角色表（如果不存在）
    cur.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            role VARCHAR(50) UNIQUE NOT NULL,
            permissions JSON, -- 存储角色拥有的权限列表
            is_in_use BOOLEAN DEFAULT FALSE, -- 角色是否在使用中
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 为role字段添加索引
    cur.execute("SHOW INDEX FROM roles WHERE Key_name = 'role'")
    if cur.fetchone() is None:
        cur.execute("CREATE INDEX idx_roles_role ON roles (role)")
    
    # 删除description字段（如果存在）
    cur.execute("SHOW COLUMNS FROM roles LIKE 'description'")
    if cur.fetchone() is not None:
        cur.execute("ALTER TABLE roles DROP COLUMN description")
    
    # 添加permissions字段（如果不存在）
    cur.execute("SHOW COLUMNS FROM roles LIKE 'permissions'")
    if cur.fetchone() is None:
        cur.execute("ALTER TABLE roles ADD permissions JSON")
    
    # 删除user_count字段（如果存在）
    cur.execute("SHOW COLUMNS FROM roles LIKE 'user_count'")
    if cur.fetchone() is not None:
        cur.execute("ALTER TABLE roles DROP COLUMN user_count")
    
    
    # 创建审计日志表（如果不存在）
    cur.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            username VARCHAR(50),
            action VARCHAR(50) NOT NULL,
            target VARCHAR(50),
            details JSON,
            ip_address VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 添加索引优化查询性能
    # 为created_at字段添加索引
    cur.execute("SHOW INDEX FROM audit_logs WHERE Key_name = 'idx_audit_logs_created_at'")
    if cur.fetchone() is None:
        cur.execute("CREATE INDEX idx_audit_logs_created_at ON audit_logs (created_at)")
    
    # 为username字段添加索引
    cur.execute("SHOW INDEX FROM audit_logs WHERE Key_name = 'idx_audit_logs_username'")
    if cur.fetchone() is None:
        cur.execute("CREATE INDEX idx_audit_logs_username ON audit_logs (username)")
    
    # 为action字段添加索引
    cur.execute("SHOW INDEX FROM audit_logs WHERE Key_name = 'idx_audit_logs_action'")
    if cur.fetchone() is None:
        cur.execute("CREATE INDEX idx_audit_logs_action ON audit_logs (action)")
    
    # 为username+created_at添加组合索引（用于按用户名查询并按时间排序）
    cur.execute("SHOW INDEX FROM audit_logs WHERE Key_name = 'idx_audit_logs_username_created_at'")
    if cur.fetchone() is None:
        cur.execute("CREATE INDEX idx_audit_logs_username_created_at ON audit_logs (username, created_at DESC)")
    
    # 为action+created_at添加组合索引（用于按操作类型查询并按时间排序）
    cur.execute("SHOW INDEX FROM audit_logs WHERE Key_name = 'idx_audit_logs_action_created_at'")
    if cur.fetchone() is None:
        cur.execute("CREATE INDEX idx_audit_logs_action_created_at ON audit_logs (action, created_at DESC)")
    
    # 插入默认角色
    roles = [
        ('管理员', '["个人信息管理", "用户管理", "角色管理", "审计日志管理"]'),
        ('普通用户', '["个人信息管理"]')
    ]
    for role in roles:
        cur.execute("INSERT IGNORE INTO roles (role, permissions) VALUES (%s, %s) ON DUPLICATE KEY UPDATE permissions=VALUES(permissions)", role)
    
    # 初始化所有角色的is_in_use字段
    cur.execute("SELECT id, role FROM roles")
    all_roles = cur.fetchall()
    for role in all_roles:
        # 查询是否有用户使用该角色
        cur.execute("SELECT COUNT(*) as count FROM users WHERE role = %s", (role['role'],))
        user_count = cur.fetchone()['count']
        is_in_use = 1 if user_count > 0 else 0
        # 更新角色的is_in_use字段
        cur.execute("UPDATE roles SET is_in_use = %s WHERE id = %s", (is_in_use, role['id']))
    
    
    # 提交更改
    conn.commit()
    
    # 关闭游标
    cur.close()

# 生成随机验证码
def generate_captcha():
    # 生成4位随机字符
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    
    # 存储验证码到会话（不区分大小写）
    session['captcha'] = captcha_text
    
    # 创建验证码图片
    width, height = 100, 38
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # 尝试使用默认字体，如果失败则使用ImageFont加载系统字体
    try:
        font = ImageFont.truetype('arial.ttf', 20)
    except:
        font = ImageFont.load_default()
    
    # 在图片上绘制验证码
    # 使用textbbox替代textsize（Pillow 10+版本不再支持textsize）
    bbox = draw.textbbox((0, 0), captcha_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    draw.text((x, y), captcha_text, font=font, fill=(0, 0, 0))
    
    # 添加干扰线
    for _ in range(5):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(0, 0, 0), width=1)
    
    # 添加干扰点
    for _ in range(20):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=(0, 0, 0))
    
    # 将图片转换为字节流
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    # 返回图片响应
    response = make_response(img_byte_arr.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response
