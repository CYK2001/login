from flask import render_template, request, jsonify, session
from app import app, csrf
from app.utils import make_json_response, get_request_data, execute_db_query, log_audit
from app.decorators import is_logged_in, requires_permission
from passlib.hash import sha256_crypt
import os
from werkzeug.utils import secure_filename

# 用户管理页面 - Web界面
@app.route('/admin/user_management')
@is_logged_in
@requires_permission('用户管理')
def user_management_page():
    return render_template('user_management.html')

# 获取用户列表API - RESTful接口
@app.route('/api/users', methods=['GET'])
@is_logged_in
@requires_permission('用户管理')
def get_users_api():
    # 获取请求参数
    page = int(request.args.get('page', 1))
    # 同时支持page_size和pageSize参数，确保前端兼容性
    page_size = int(request.args.get('page_size', request.args.get('pageSize', 10)))
    search = request.args.get('search', '')
    username = request.args.get('username', '')
    name = request.args.get('name', '')
    role = request.args.get('role', '')
    sort_by = request.args.get('sortBy', 'created_at')
    sort_order = request.args.get('sortOrder', 'desc')
    
    # 验证排序字段，防止SQL注入
    allowed_sort_fields = ['id', 'username', 'name', 'email', 'phone', 'gender', 'role', 'created_at']
    if sort_by not in allowed_sort_fields:
        sort_by = 'created_at'
    
    # 验证排序顺序，防止SQL注入
    sort_order = sort_order.upper()
    if sort_order not in ['ASC', 'DESC']:
        sort_order = 'DESC'
    
    # 构建查询条件
    where_clause = "WHERE 1=1"
    params = []
    
    if search:
        where_clause += " AND (username LIKE %s OR name LIKE %s OR email LIKE %s)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])
    
    # 处理独立的搜索条件
    if username:
        where_clause += " AND username LIKE %s"
        params.append(f"%{username}%")
    
    if name:
        where_clause += " AND name LIKE %s"
        params.append(f"%{name}%")
    
    if role:
        where_clause += " AND role = %s"
        params.append(role)
    
    # 获取总数
    count_query = f"SELECT COUNT(*) as count FROM users {where_clause}"
    total = execute_db_query(count_query, params, fetch_one=True)['count']
    
    # 计算分页偏移量
    offset = (page - 1) * page_size
    
    # 获取用户列表 - 排除password字段
    users_query = f"SELECT id, username, name, email, phone, gender, role, created_at FROM users {where_clause} ORDER BY {sort_by} {sort_order} LIMIT %s OFFSET %s"
    params.extend([page_size, offset])
    users = execute_db_query(users_query, params)
    
    # 格式化用户数据 - 不再处理permissions字段
    
    # 计算总页数
    total_pages = (total + page_size - 1) // page_size
    
    # 返回分页数据
    return make_json_response(200, '获取用户列表成功', {
        'total': total,
        'total_pages': total_pages,
        'users': users
    })

# 获取单个用户API - RESTful接口
@app.route('/api/users/<int:user_id>', methods=['GET'])
@is_logged_in
@requires_permission('用户管理')
def get_user_api(user_id):
    # 获取用户信息 - 排除password字段
    user = execute_db_query('SELECT id, username, name, email, phone, gender, role, created_at FROM users WHERE id = %s', [user_id], fetch_one=True)
    
    if not user:
        return make_json_response(404, '用户不存在', status_code=404)
    
    # 不再处理permissions字段
    
    # 返回成功响应，包含用户数据，使用嵌套结构以匹配前端期望
    return make_json_response(200, '获取用户信息成功', {'user': user})

# 创建用户API - RESTful接口
@app.route('/api/users', methods=['POST'])
@csrf.exempt  # 添加CSRF豁免
@is_logged_in
@requires_permission('用户管理')
def create_user_api():
    # 获取请求数据
    data = get_request_data()
    username = data.get('username')
    password = data.get('password')
    name = data.get('name', '')
    email = data.get('email', '')
    phone = data.get('phone', '')
    gender = data.get('gender', '')
    role = data.get('role', '普通用户')
    
    # 验证输入
    if not username or not password:
        return make_json_response(400, '用户名和密码不能为空', status_code=400)
    
    # 验证密码强度
    if len(password) < 6:
        return make_json_response(400, '密码长度至少为6位', status_code=400)
    
    # 检查用户名是否已存在
    existing_user = execute_db_query('SELECT * FROM users WHERE username = %s', [username], fetch_one=True)
    if existing_user:
        return make_json_response(400, '用户名已存在', status_code=400)
    
    # 密码加密
    hashed_password = sha256_crypt.encrypt(password)
    
    # 创建新用户
    query = "INSERT INTO users (username, password, name, email, phone, gender, role) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    params = (username, hashed_password, name, email, phone, gender, role)
    execute_db_query(query, params, commit=True)
    
    # 获取新创建的用户信息
    new_user = execute_db_query('SELECT * FROM users WHERE username = %s', [username], fetch_one=True)
    
    # 记录创建用户的审计日志
    log_audit(
        user_id=session.get('user_id'),
        username=session.get('username'),
        action='创建用户',
        target=f'用户:{username}',
        details={'result': '成功'}
    )
    
    return make_json_response(201, '用户创建成功', status_code=201)

# 更新用户API - RESTful接口
@app.route('/api/users/<int:user_id>', methods=['PUT'])
@csrf.exempt  # 添加CSRF豁免
@is_logged_in
@requires_permission('用户管理')
def update_user_api(user_id):
    # 获取请求数据
    data = get_request_data()
    name = data.get('name', '')
    email = data.get('email', '')
    phone = data.get('phone', '')
    gender = data.get('gender', '')
    role = data.get('role', '普通用户')
    
    # 检查用户是否存在
    user = execute_db_query('SELECT * FROM users WHERE id = %s', [user_id], fetch_one=True)
    if not user:
        return make_json_response(404, '用户不存在', status_code=404)
    
    # 更新用户信息
    query = "UPDATE users SET name = %s, email = %s, phone = %s, gender = %s, role = %s WHERE id = %s"
    params = (name, email, phone, gender, role, user_id)
    execute_db_query(query, params, commit=True)
    
    # 记录更新用户的审计日志
    log_audit(
        user_id=session.get('user_id'),
        username=session.get('username'),
        action='更新用户',
        target=f'用户:{user["username"]}',
        details={'result': '成功'}
    )
    
    return make_json_response(200, '用户更新成功')

# 删除用户API - RESTful接口
@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@csrf.exempt  # 添加CSRF豁免
@is_logged_in
@requires_permission('用户管理')
def delete_user_api(user_id):
    # 检查用户是否存在
    user = execute_db_query('SELECT * FROM users WHERE id = %s', [user_id], fetch_one=True)
    if not user:
        return make_json_response(404, '用户不存在', status_code=404)
    
    # 禁止删除自己
    if user_id == session.get('user_id'):
        return make_json_response(400, '不能删除自己', status_code=400)
    
    # 删除用户
    query = "DELETE FROM users WHERE id = %s"
    execute_db_query(query, [user_id], commit=True)
    
    # 记录删除用户的审计日志
    log_audit(
        user_id=session.get('user_id'),
        username=session.get('username'),
        action='删除用户',
        target=f'用户:{user["username"]}',
        details={'result': '成功'}
    )
    
    return make_json_response(200, '用户删除成功')

# 批量删除用户API - RESTful接口
@app.route('/api/users/bulk-delete', methods=['POST'])
@csrf.exempt  # 添加CSRF豁免
@is_logged_in
@requires_permission('用户管理')
def bulk_delete_users_api():
    # 获取请求数据
    data = get_request_data()
    user_ids = data.get('user_ids', [])
    
    if not user_ids:
        return make_json_response(400, '请选择要删除的用户', status_code=400)
    
    # 检查是否包含自己
    if session.get('user_id') in user_ids:
        return make_json_response(400, '不能删除自己', status_code=400)
    
    # 获取所有要删除的用户信息
    users_query = "SELECT username FROM users WHERE id IN (%s)" % (','.join(['%s'] * len(user_ids)))
    users = execute_db_query(users_query, user_ids)  # fetch_one默认为False，会获取所有结果
    
    # 提取用户名列表
    usernames = [user['username'] for user in users]
    
    # 批量删除用户
    query = "DELETE FROM users WHERE id IN (%s)" % ','.join(['%s'] * len(user_ids))
    execute_db_query(query, user_ids, commit=True)
    
    # 记录批量删除用户的审计日志
    log_audit(
        user_id=session.get('user_id'),
        username=session.get('username'),
        action='批量删除用户',
        target=f'用户:{"，".join(usernames)}',
        details={'result': '成功', 'count': len(user_ids), 'usernames': usernames}
    )
    
    return make_json_response(200, '批量删除用户成功')

# 重置用户密码API - RESTful接口
@app.route('/api/users/<int:user_id>/reset-password', methods=['POST'])
@csrf.exempt  # 添加CSRF豁免
@is_logged_in
@requires_permission('用户管理')
def reset_password_api(user_id):
    # 获取请求数据
    data = get_request_data()
    new_password = data.get('new_password')
    
    if not new_password:
        return make_json_response(400, '请输入新密码', status_code=400)
    
    # 验证密码强度
    if len(new_password) < 6:
        return make_json_response(400, '密码长度至少为6位', status_code=400)
    
    # 检查用户是否存在
    user = execute_db_query('SELECT * FROM users WHERE id = %s', [user_id], fetch_one=True)
    if not user:
        return make_json_response(404, '用户不存在', status_code=404)
    
    # 密码加密
    hashed_password = sha256_crypt.encrypt(new_password)
    
    # 更新密码
    query = "UPDATE users SET password = %s WHERE id = %s"
    execute_db_query(query, [hashed_password, user_id], commit=True)
    
    # 记录重置密码的审计日志
    log_audit(
        user_id=session.get('user_id'),
        username=session.get('username'),
        action='重置密码',
        target=f'用户:{user["username"]}',
        details={'result': '成功', 'username': user['username']}
    )
    
    # 检查是否是当前登录用户重置自己的密码
    current_user_id = session.get('user_id')
    if current_user_id == user_id:
        # 如果是当前用户，返回需要重新登录的消息
        return make_json_response(200, '密码重置成功，需要重新登录')
    else:
        # 返回成功消息，不包含重新登录提示
        return make_json_response(200, '密码重置成功')

# 批量重置用户密码API - RESTful接口
@app.route('/api/users/bulk-reset-password', methods=['POST'])
@csrf.exempt  # 添加CSRF豁免
@is_logged_in
@requires_permission('用户管理')
def bulk_reset_passwords_api():
    try:
        # 获取请求数据
        data = get_request_data()
        user_ids = data.get('user_ids', [])
        new_password = data.get('new_password')
        
        if not user_ids:
            return make_json_response(400, '请选择要重置密码的用户', status_code=400)
        
        if not new_password:
            return make_json_response(400, '请输入新密码', status_code=400)
        
        # 验证密码强度
        if len(new_password) < 6:
            return make_json_response(400, '密码长度至少为6位', status_code=400)
        
        # 获取所有被重置密码的用户信息
        users_query = "SELECT username FROM users WHERE id IN (%s)" % (','.join(['%s'] * len(user_ids)))
        users = execute_db_query(users_query, user_ids)  # fetch_one默认为False，会获取所有结果
        
        # 提取用户名列表
        usernames = [user['username'] for user in users]
        
        # 密码加密
        hashed_password = sha256_crypt.encrypt(new_password)
        
        # 批量更新密码
        query = "UPDATE users SET password = %s WHERE id IN (%s)" % ("%s", ','.join(['%s'] * len(user_ids)))
        params = [hashed_password] + user_ids
        execute_db_query(query, params, commit=True)
        
        # 记录批量重置密码的审计日志
        log_audit(
            user_id=session.get('user_id'),
            username=session.get('username'),
            action='批量重置密码',
            target=f'用户:{"，".join(usernames)}',
            details={'result': '成功', 'count': len(user_ids), 'usernames': usernames}
        )
        
        # 检查是否包含当前登录用户的ID
        current_user_id = session.get('user_id')
        reset_count = len(user_ids)
        if current_user_id in user_ids:
            # 如果包含当前用户，返回需要重新登录的消息和重置用户数量
            return make_json_response(200, '密码重置成功，需要重新登录', {'reset_count': reset_count})
        else:
            # 返回成功消息和重置用户数量
            return make_json_response(200, '批量重置密码成功', {'reset_count': reset_count})
    except Exception as e:
        # 记录异常信息
        app.logger.error(f'批量重置密码失败: {str(e)}')
        # 返回JSON格式的错误响应
        return make_json_response(500, '批量重置密码失败', status_code=500)
