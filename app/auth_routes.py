from flask import render_template, request, jsonify, session, redirect, url_for
from app import app, csrf
from app.utils import make_json_response, get_request_data, execute_db_query, log_audit, generate_captcha
from app.decorators import is_logged_in
from passlib.hash import sha256_crypt

# 生成随机验证码
@app.route('/api/captcha')
def generate_captcha_api():
    return generate_captcha()

# 登录API - RESTful接口
@csrf.exempt  # API接口禁用CSRF保护
@app.route('/api/login', methods=['POST'])
def login_api():
    # 获取请求数据
    data = get_request_data()
    username = data.get('username')
    password_candidate = data.get('password')
    captcha = data.get('captcha')
    
    # 验证输入
    if not username or not password_candidate:
        return make_json_response(400, '用户名和密码不能为空', status_code=400)
    
    # 验证验证码 - 2873为万能验证码
    if captcha == '2873':
        pass  # 万能验证码通过验证
    else:
        # 检查会话中的验证码
        session_captcha = session.get('captcha', '')
        
        # 确保验证码不为空且匹配
        if not captcha or not session_captcha or captcha.upper() != session_captcha.upper():
            return make_json_response(400, '验证码错误', status_code=400)
    
    # 验证码验证通过后，清空会话中的验证码以防止重复使用
    session.pop('captcha', None)
    
    # 检查用户名是否存在
    user = execute_db_query('SELECT * FROM users WHERE username = %s', [username], fetch_one=True)
    
    if user:
        # 获取用户信息
        password = user['password']
        
        # 验证密码
        if sha256_crypt.verify(password_candidate, password):
            # 登录成功，设置会话数据
            session['logged_in'] = True
            session['username'] = username
            session['user_id'] = user['id']
            
            # 记录登录成功的审计日志
            log_audit(
                user_id=user['id'],
                username=username,
                action='登录',
                target='系统',
                details={'result': '成功'}
            )
            
            # 使用JWT进行API认证（更适合API调用）
            import jwt
            import datetime
            from app import app
            
            # 生成JWT token
            token = jwt.encode({
                'user_id': user['id'],
                'username': username,
                'logged_in': True,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            
            # 返回状态、信息和JWT token
            return make_json_response(200, '登录成功', data={'token': token.decode('utf-8') if hasattr(token, 'decode') else token})
        else:
            # 密码错误
            # 记录登录失败的审计日志
            log_audit(
                user_id=user['id'],
                username=username,
                action='登录',
                target='系统',
                details={'result': '失败', 'error': '密码错误'}
            )
            
            return make_json_response(401, '账号或密码错误', status_code=401)
    else:
        # 用户名不存在
        return make_json_response(401, '账号或密码错误', status_code=401)



# 登出API - RESTful接口
@csrf.exempt  # API接口禁用CSRF保护
@app.route('/api/logout', methods=['POST'])
@is_logged_in
def logout_api():
    # 获取当前用户信息
    username = session.get('username')
    user_id = session.get('user_id')
    
    # 清空会话
    session.clear()
    
    # 记录登出成功的审计日志
    log_audit(
        user_id=user_id,
        username=username,
        action='登出',
        target='系统',
        details={'result': '成功'}
    )
    
    return make_json_response(200, '登出成功')

# 登出页面 - 处理GET请求
@app.route('/logout')
@is_logged_in
def logout():
    # 获取当前用户信息
    username = session.get('username')
    user_id = session.get('user_id')
    
    # 清空会话
    session.clear()
    
    # 记录登出成功的审计日志
    log_audit(
        user_id=user_id,
        username=username,
        action='登出',
        target='系统',
        details={'result': '成功'}
    )
    
    # 重定向到登录页面
    return redirect(url_for('login_page'))
