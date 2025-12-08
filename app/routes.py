from flask import render_template, jsonify, session, redirect, url_for
from app import app
from app.decorators import is_logged_in

# 登录页面 - Web界面
@app.route('/')
@app.route('/login', methods=['GET'])
def login_page():
    # GET请求时渲染登录页面
    return render_template('login.html')

# 重定向到个人信息页面
@app.route('/profile')
@is_logged_in
def profile_redirect():
    # 重定向到管理后台的个人信息页面
    return redirect(url_for('profile_page'))

# 测试cookie API - 完整版本
@app.route('/api/test_cookie', methods=['GET'])
def test_cookie_api():
    # 设置session
    session['test'] = '12345'
    session_id = session.sid if hasattr(session, 'sid') else 'no_sid'
    
    # 返回session信息
    from app.utils import make_json_response
    return make_json_response(200, '测试成功', {
        "session_id": session_id
    })
