from flask import render_template, request, jsonify, session
from app import app, csrf
from app.utils import make_json_response, get_request_data, execute_db_query, log_audit
from app.decorators import is_logged_in, requires_permission

# 角色管理页面 - Web界面
@app.route('/admin/role_management')
@is_logged_in
@requires_permission('角色管理')
def role_management_page():
    # 从数据库的role_permissions表中获取所有权限
    permissions = execute_db_query('SELECT id, permission FROM role_permissions ORDER BY id')
    
    # 将结果转换为模板需要的格式（id, permissions）
    formatted_permissions = []
    for perm in permissions:
        formatted_permissions.append({
            'id': perm['id'],
            'permissions': perm['permission']
        })
    
    return render_template('role_management.html', permissions=formatted_permissions)

# 获取角色列表API - RESTful接口
@app.route('/api/roles', methods=['GET'])
@is_logged_in
@requires_permission('角色管理')
def get_roles_api():
    try:
        # 获取请求参数
        page = int(request.args.get('page', 1))
        # 支持前端使用page_size参数
        page_size = int(request.args.get('page_size', request.args.get('pageSize', 10)))
        # 支持前端使用name参数进行搜索
        search = request.args.get('name', request.args.get('search', ''))
        
        # 构建查询条件
        where_clause = "WHERE 1=1"
        params = []
        
        if search:
            where_clause += " AND role LIKE %s"
            params.append(f"%{search}%")
        
        # 获取总数
        count_query = f"SELECT COUNT(*) as count FROM roles {where_clause}"
        total = execute_db_query(count_query, params, fetch_one=True)['count']
        
        # 计算分页偏移量
        offset = (page - 1) * page_size
        
        # 获取角色列表 - 明确指定要查询的字段
        roles_query = f"SELECT id, role, permissions, is_in_use, created_at FROM roles {where_clause} ORDER BY id DESC LIMIT %s OFFSET %s"
        params.extend([page_size, offset])
        roles = execute_db_query(roles_query, params)
        
        # 格式化角色数据
        formatted_roles = []
        for role in roles:
            # 创建新的角色字典，确保格式正确
            formatted_role = {
                'id': role['id'],
                'role': role['role'],
                'permissions': [],
                'is_in_use': bool(role['is_in_use']),
                'created_at': role['created_at']
            }
            
            # 处理权限字段
            if role.get('permissions'):
                import json
                try:
                    if isinstance(role['permissions'], str):
                        formatted_role['permissions'] = json.loads(role['permissions'])
                    elif isinstance(role['permissions'], (list, dict)):
                        formatted_role['permissions'] = role['permissions']
                except Exception as e:
                    app.logger.debug(f"解析角色 {role['role']} 的permissions失败: {e}")
            
            formatted_roles.append(formatted_role)
        
        # 计算总页数
        total_pages = (total + page_size - 1) // page_size
        
        # 返回分页数据
        return make_json_response(200, '获取角色列表成功', {
            'total': total,
            'roles': formatted_roles,
            'total_pages': total_pages
        })
    except Exception as e:
        app.logger.error(f"获取角色列表异常: {e}")
        return make_json_response(500, f'获取角色列表失败: {str(e)}')

# 获取单个角色API - RESTful接口
@app.route('/api/roles/<int:role_id>', methods=['GET'])
@is_logged_in
@requires_permission('角色管理')
def get_role_api(role_id):
    # 获取角色信息 - 明确指定要查询的字段
    role = execute_db_query('SELECT id, role, permissions, is_in_use, created_at FROM roles WHERE id = %s', [role_id], fetch_one=True)
    
    if not role:
        return make_json_response(404, '角色不存在', status_code=404)
    
    # 创建新的角色字典，确保格式正确
    formatted_role = {
        'id': role['id'],
        'role': role['role'],
        'permissions': [],
        'is_in_use': bool(role['is_in_use']),
        'created_at': role['created_at']
    }
    
    # 处理权限字段
    if role.get('permissions'):
        import json
        try:
            if isinstance(role['permissions'], str):
                formatted_role['permissions'] = json.loads(role['permissions'])
            elif isinstance(role['permissions'], (list, dict)):
                formatted_role['permissions'] = role['permissions']
        except Exception as e:
            app.logger.debug(f"解析角色 {role['role']} 的permissions失败: {e}")
    
    return make_json_response(200, '获取角色信息成功', formatted_role)

# 获取权限列表API - RESTful接口
@app.route('/api/permissions', methods=['GET'])
@is_logged_in
def get_permissions_api():
    # 从数据库的role_permissions表中获取所有权限
    permissions = execute_db_query('SELECT id, permission FROM role_permissions ORDER BY id')
    
    # 将结果转换为API需要的格式（id, permissions）
    formatted_permissions = []
    for perm in permissions:
        formatted_permissions.append({
            'id': perm['id'],
            'permissions': perm['permission']
        })
    
    return make_json_response(200, '获取权限列表成功', formatted_permissions)

# 创建角色API - RESTful接口
@app.route('/api/roles', methods=['POST'])
@is_logged_in
@requires_permission('角色管理')
@csrf.exempt  # 添加CSRF豁免装饰器
def create_role_api():
    # 获取请求数据
    data = get_request_data()
    role_name = data.get('name')  # 前端表单使用的是'name'字段
    permissions = data.get('permissions', [])
    
    # 验证输入
    if not role_name:
        return make_json_response(400, '角色名称不能为空', status_code=400)
    
    # 检查角色名称是否已存在
    existing_role = execute_db_query('SELECT * FROM roles WHERE role = %s', [role_name], fetch_one=True)
    if existing_role:
        return make_json_response(400, '角色名称已存在', status_code=400)
    
    # 处理权限数据
    import json
    permissions_json = json.dumps(permissions)
    
    # 创建新角色
    query = "INSERT INTO roles (role, permissions) VALUES (%s, %s)"
    params = (role_name, permissions_json)
    execute_db_query(query, params, commit=True)
    
    # 记录创建角色的审计日志
    log_audit(
        user_id=session.get('user_id'),
        username=session.get('username'),
        action='创建角色',
        target=f'角色:{role_name}',
        details={'result': '成功'}
    )
    
    return make_json_response(201, '角色创建成功', status_code=201)

# 更新角色API - RESTful接口
@app.route('/api/roles/<int:role_id>', methods=['PUT'])
@is_logged_in
@requires_permission('角色管理')
@csrf.exempt  # 添加CSRF豁免装饰器
def update_role_api(role_id):
    # 获取请求数据
    data = get_request_data()
    role_name = data.get('name')  # 前端表单使用的是'name'字段
    permissions = data.get('permissions', [])
    
    # 验证输入
    if not role_name:
        return make_json_response(400, '角色名称不能为空', status_code=400)
    
    # 检查角色是否存在
    role = execute_db_query('SELECT * FROM roles WHERE id = %s', [role_id], fetch_one=True)
    if not role:
        return make_json_response(404, '角色不存在', status_code=404)
    
    # 检查角色名称是否已存在（排除当前角色）
    existing_role = execute_db_query('SELECT * FROM roles WHERE role = %s AND id != %s', [role_name, role_id], fetch_one=True)
    if existing_role:
        return make_json_response(400, '角色名称已存在', status_code=400)
    
    # 处理权限数据
    import json
    permissions_json = json.dumps(permissions)
    
    # 更新角色信息
    query = "UPDATE roles SET role = %s, permissions = %s WHERE id = %s"
    params = (role_name, permissions_json, role_id)
    execute_db_query(query, params, commit=True)
    
    # 用户权限现在从角色表动态获取，不需要单独更新users表
    
    # 记录更新角色的审计日志
    log_audit(
        user_id=session.get('user_id'),
        username=session.get('username'),
        action='更新角色',
        target=f'角色:{role_name}',
        details={'result': '成功'}
    )
    
    return make_json_response(200, '角色更新成功')

# 删除角色API - RESTful接口
@app.route('/api/roles/<int:role_id>', methods=['DELETE'])
@is_logged_in
@requires_permission('角色管理')
@csrf.exempt  # 添加CSRF豁免装饰器
def delete_role_api(role_id):
    # 检查角色是否存在
    role = execute_db_query('SELECT * FROM roles WHERE id = %s', [role_id], fetch_one=True)
    if not role:
        return make_json_response(404, '角色不存在', status_code=404)
    
    # 检查是否有用户使用该角色
    user_count = execute_db_query('SELECT COUNT(*) as count FROM users WHERE role = %s', [role['role']], fetch_one=True)['count']
    if user_count > 0:
        return make_json_response(400, '该角色正在被使用，无法删除', status_code=400)
    
    # 删除角色
    query = "DELETE FROM roles WHERE id = %s"
    execute_db_query(query, [role_id], commit=True)
    
    # 记录删除角色的审计日志
    log_audit(
        user_id=session.get('user_id'),
        username=session.get('username'),
        action='删除角色',
        target=f'角色:{role["role"]}',
        details={'result': '成功'}
    )
    
    return make_json_response(200, '角色删除成功')

# 批量删除角色API - RESTful接口
@app.route('/api/roles/bulk-delete', methods=['POST'])
@is_logged_in
@requires_permission('角色管理')
@csrf.exempt  # 添加CSRF豁免装饰器
def bulk_delete_roles_api():
    # 获取请求数据
    data = get_request_data()
    role_ids = data.get('role_ids', [])
    
    if not role_ids:
        return make_json_response(400, '请选择要删除的角色', status_code=400)
    
    # 检查是否有角色正在被使用
    for role_id in role_ids:
        role = execute_db_query('SELECT * FROM roles WHERE id = %s', [role_id], fetch_one=True)
        if role:
            user_count = execute_db_query('SELECT COUNT(*) as count FROM users WHERE role = %s', [role['role']], fetch_one=True)['count']
            if user_count > 0:
                return make_json_response(400, f'角色{role["role"]}正在被使用，无法删除', status_code=400)
    
    # 在删除前获取要删除的角色名称
    deleted_roles = []
    for role_id in role_ids:
        role = execute_db_query('SELECT * FROM roles WHERE id = %s', [role_id], fetch_one=True)
        if role:
            deleted_roles.append(role['role'])
    
    # 批量删除角色
    query = "DELETE FROM roles WHERE id IN (%s)" % ','.join(['%s'] * len(role_ids))
    execute_db_query(query, role_ids, commit=True)
    
    # 记录批量删除角色的审计日志
    # 如果有删除的角色名称，在操作目标中显示具体角色
    if deleted_roles:
        target_text = f'角色:{", ".join(deleted_roles)}'
    else:
        target_text = f'角色:{len(role_ids)}个'
    
    log_audit(
        user_id=session.get('user_id'),
        username=session.get('username'),
        action='批量删除角色',
        target=target_text,
        details={'result': '成功', 'count': len(role_ids), 'roles': deleted_roles}
    )
    
    return make_json_response(200, '批量删除角色成功')
