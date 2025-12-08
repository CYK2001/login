from flask import render_template, request, jsonify, session
from app import app, csrf
from app.utils import make_json_response, get_request_data, execute_db_query, log_audit
from app.decorators import is_logged_in

# 个人信息页面 - Web界面
@app.route('/admin/profile')
@is_logged_in
def profile_page():
    # 获取当前登录用户ID
    user_id = session.get('user_id')
    
    # 获取用户信息
    user = execute_db_query('SELECT * FROM users WHERE id = %s', [user_id], fetch_one=True)
    
    return render_template('profile.html', user=user)

# 获取当前用户信息API - RESTful接口
@app.route('/api/profile', methods=['GET'])
def get_profile_api():
    # 尝试从请求参数获取token
    token = request.args.get('token')
    if token:
        # 直接解析token作为session数据
        from flask.sessions import SecureCookieSessionInterface
        interface = SecureCookieSessionInterface()
        try:
            session_data = interface.get_signing_serializer(app).loads(token)
            if 'logged_in' in session_data and session_data['logged_in']:
                # 获取用户信息
                user_id = session_data.get('user_id')
                if user_id:
                    user = execute_db_query('SELECT id, username, role, name, phone, email, created_at, avatar FROM users WHERE id = %s', [user_id], fetch_one=True)
                    if user:
                        return make_json_response(200, '获取个人信息成功', user)
        except Exception as e:
            app.logger.debug(f"Failed to parse token: {e}")
    
    # 如果没有token或解析失败，使用传统的session检查
    from app.decorators import is_logged_in
    def original_function():
        # 获取当前登录用户ID
        user_id = session.get('user_id')
        
        # 获取用户信息
        user = execute_db_query('SELECT id, username, role, name, phone, email, created_at, avatar FROM users WHERE id = %s', [user_id], fetch_one=True)
        
        if not user:
            return make_json_response(404, '用户不存在', status_code=404)
        
        return make_json_response(200, '获取个人信息成功', user)
    return is_logged_in(original_function)()

# 更新个人信息API - RESTful接口
@csrf.exempt  # API接口禁用CSRF保护
@app.route('/api/profile', methods=['PUT'])
@is_logged_in
def update_profile_api():
    # 获取当前登录用户ID
    user_id = session.get('user_id')
    username = session.get('username')
    
    # 获取请求数据
    data = get_request_data()
    name = data.get('name', '')
    phone = data.get('phone', '')
    email = data.get('email', '')
    
    # 验证输入
    if not name:
        return make_json_response(400, '姓名不能为空', status_code=400)
    
    if phone:
        import re
        if not re.match(r'^1[3-9]\d{9}$', phone):
            return make_json_response(400, '请输入有效的手机号码', status_code=400)
    
    if email:
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return make_json_response(400, '请输入有效的邮箱地址', status_code=400)
    
    # 更新用户信息
    query = "UPDATE users SET name = %s, phone = %s, email = %s WHERE id = %s"
    params = (name, phone, email, user_id)
    execute_db_query(query, params, commit=True)
    
    # 记录更新个人信息的审计日志
    log_audit(
        user_id=user_id,
        username=username,
        action='更新个人信息',
        target=f'用户:{username}',
        details={'result': '成功', 'name': name, 'phone': phone, 'email': email}
    )
    
    return make_json_response(200, '更新个人信息成功')

# 修改密码API - RESTful接口
@csrf.exempt  # API接口禁用CSRF保护
@app.route('/api/profile/change_password', methods=['POST'])
@is_logged_in
def change_password_api():
    # 获取当前登录用户ID和用户名
    user_id = session.get('user_id')
    username = session.get('username')
    
    # 获取请求数据
    data = get_request_data()
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')
    
    # 验证输入
    if not old_password or not new_password or not confirm_password:
        return make_json_response(400, '旧密码、新密码和确认密码不能为空', status_code=400)
    
    if new_password != confirm_password:
        return make_json_response(400, '新密码和确认密码不一致', status_code=400)
    
    if len(new_password) < 6:
        return make_json_response(400, '新密码长度不能少于6位', status_code=400)
    
    # 验证旧密码
    from passlib.hash import sha256_crypt
    user = execute_db_query('SELECT * FROM users WHERE id = %s', [user_id], fetch_one=True)
    
    if not user or not sha256_crypt.verify(old_password, user['password']):
        return make_json_response(400, '旧密码错误', status_code=400)
    
    # 检查新密码是否与旧密码相同
    if old_password == new_password:
        return make_json_response(400, '新密码不能与旧密码相同', status_code=400)
    
    # 更新密码
    hashed_new_password = sha256_crypt.hash(new_password)
    query = "UPDATE users SET password = %s WHERE id = %s"
    execute_db_query(query, [hashed_new_password, user_id], commit=True)
    
    # 记录修改密码的审计日志
    log_audit(
        user_id=user_id,
        username=username,
        action='修改密码',
        target=f'用户:{username}',
        details={'result': '成功'}
    )
    
    # 强制用户重新登录
    session.clear()
    # 确保所有登录相关的session键都被清除
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    session.permanent = False
    
    return make_json_response(200, '密码修改成功，请重新登录')

# 获取用户权限API - RESTful接口
@app.route('/api/profile/permissions', methods=['GET'])
@is_logged_in
def get_user_permissions_api():
    # 获取当前登录用户信息
    user_id = session.get('user_id')
    username = session.get('username')
    
    # 获取用户角色
    user = execute_db_query('SELECT role FROM users WHERE id = %s', [user_id], fetch_one=True)
    
    if not user:
        return make_json_response(404, '用户不存在', status_code=404)
    
    user_role = user['role']
    
    # 获取角色权限
    permissions = []
    if user_role:
        role = execute_db_query('SELECT permissions FROM roles WHERE role = %s', [user_role], fetch_one=True)
        if role:
            import json
            role_permissions = role.get('permissions', '[]')
            if isinstance(role_permissions, str):
                permissions = json.loads(role_permissions)
            elif isinstance(role_permissions, list):
                permissions = role_permissions
    
    # 记录获取权限的审计日志
    log_audit(
        user_id=user_id,
        username=username,
        action='获取用户权限',
        target=f'用户:{username}',
        details={'result': '成功', 'role': user_role, 'permission_count': len(permissions)}
    )
    
    return make_json_response(200, '获取用户权限成功', {
        'role': user_role,
        'permissions': permissions
    })

# 更新头像API - RESTful接口
@csrf.exempt  # API接口禁用CSRF保护
@app.route('/api/profile/update', methods=['POST'])
@is_logged_in
def update_avatar_api():
    # 获取当前登录用户ID和用户名
    user_id = session.get('user_id')
    username = session.get('username')
    
    # 检查是否有文件上传
    if 'avatar' not in request.files:
        return make_json_response(400, '未选择头像文件', status_code=400)
    
    file = request.files['avatar']
    
    # 检查文件是否为空
    if file.filename == '':
        return make_json_response(400, '未选择头像文件', status_code=400)
    
    # 检查文件类型
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return make_json_response(400, '只允许上传PNG、JPG、JPEG和GIF格式的图片', status_code=400)
    
    # 检查文件大小（限制为2MB）
    if file.content_length > 2 * 1024 * 1024:
        return make_json_response(400, '图片大小不能超过2MB', status_code=400)
    
    # 获取用户当前的头像信息
    current_user = execute_db_query('SELECT avatar FROM users WHERE id = %s', [user_id], fetch_one=True)
    old_avatar = current_user.get('avatar') if current_user else None
    
    # 生成新的文件名，使用用户名
    import os
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{username}.{file_ext}"
    
    # 确保uploads目录存在
    upload_path = os.path.join(app.static_folder, 'uploads')
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    
    # 保存文件
    file.save(os.path.join(upload_path, filename))
    
    # 更新用户头像信息
    query = "UPDATE users SET avatar = %s WHERE id = %s"
    execute_db_query(query, [filename, user_id], commit=True)
    
    # 如果用户有旧头像，删除旧头像文件
    if old_avatar and old_avatar != filename:
        old_avatar_path = os.path.join(upload_path, old_avatar)
        if os.path.exists(old_avatar_path):
            try:
                os.remove(old_avatar_path)
            except Exception as e:
                # 记录删除旧头像失败的日志
                app.logger.error(f"删除旧头像失败: {str(e)}")
    
    # 记录更换头像的审计日志
    log_audit(
        user_id=user_id,
        username=username,
        action='更换头像',
        target=f'用户:{username}',
        details={'result': '成功', 'avatar': filename, 'old_avatar': old_avatar}
    )
    
    return make_json_response(200, '头像上传成功', {'avatar': filename})
