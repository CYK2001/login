from flask import render_template, request, jsonify, session
from app import app
from app.utils import make_json_response, get_request_data, execute_db_query
from app.decorators import is_logged_in, requires_permission

# 审计日志页面 - Web界面
@app.route('/admin/audit_logs')
@is_logged_in
@requires_permission('审计日志管理')
def audit_logs_page():
    return render_template('audit_logs.html')

# 获取审计日志API - RESTful接口
@app.route('/api/audit_logs', methods=['GET'])
@is_logged_in
@requires_permission('审计日志管理')
def get_audit_logs_api():
    # 获取请求参数
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', int(request.args.get('pageSize', 10))))
    search = request.args.get('search', '')
    action = request.args.get('action', '')
    username = request.args.get('username', '')
    target = request.args.get('target', '')
    details = request.args.get('details', '')
    start_date = request.args.get('start_time', request.args.get('startDate', ''))
    end_date = request.args.get('end_time', request.args.get('endDate', ''))
    
    # 构建查询条件
    where_clause = "WHERE 1=1"
    params = []
    
    if search:
        where_clause += " AND (username LIKE %s OR action LIKE %s OR target LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    
    if action:
        where_clause += " AND action LIKE %s"
        params.append(f"%{action}%")
    
    if username:
        where_clause += " AND username LIKE %s"
        params.append(f"%{username}%")
    
    if target:
        where_clause += " AND target LIKE %s"
        params.append(f"%{target}%")
    
    if details:
        where_clause += " AND details LIKE %s"
        params.append(f"%{details}%")
    
    if start_date:
        where_clause += " AND created_at >= %s"
        params.append(start_date)
    
    if end_date:
        where_clause += " AND created_at <= %s"
        params.append(end_date)
    
    # 获取总数
    count_query = f"SELECT COUNT(*) as count FROM audit_logs {where_clause}"
    total = execute_db_query(count_query, params, fetch_one=True)['count']
    
    # 计算分页偏移量
    offset = (page - 1) * page_size
    
    # 获取审计日志列表
    logs_query = f"SELECT * FROM audit_logs {where_clause} ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([page_size, offset])
    logs = execute_db_query(logs_query, params)
    
    # 格式化审计日志数据
    for log in logs:
        if log.get('details'):
            import json
            if isinstance(log['details'], str):
                log['details'] = json.loads(log['details'])
    
    # 计算总页数
    total_pages = (total + page_size - 1) // page_size
    
    # 返回完整的分页数据
    return make_json_response(200, '获取审计日志列表成功', {
        'total': total,
        'logs': logs,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages
    })

# 获取审计日志详情API - RESTful接口
@app.route('/api/audit_logs/<int:log_id>', methods=['GET'])
@is_logged_in
@requires_permission('审计日志管理')
def get_audit_log_detail_api(log_id):
    # 获取审计日志详情
    log = execute_db_query('SELECT * FROM audit_logs WHERE id = %s', [log_id], fetch_one=True)
    
    if not log:
        return make_json_response(404, '审计日志不存在', status_code=404)
    
    # 格式化详情数据
    if log.get('details'):
        import json
        if isinstance(log['details'], str):
            log['details'] = json.loads(log['details'])
    
    return make_json_response(200, '获取审计日志详情成功', log)

# 导出审计日志API
@app.route('/api/audit_logs/export', methods=['GET'])
@is_logged_in
@requires_permission('审计日志管理')
def export_audit_logs_api():
    # 获取请求参数
    search = request.args.get('search', '')
    action = request.args.get('action', '')
    username = request.args.get('username', '')
    target = request.args.get('target', '')
    details = request.args.get('details', '')
    start_date = request.args.get('start_time', request.args.get('startDate', ''))
    end_date = request.args.get('end_time', request.args.get('endDate', ''))
    
    # 构建查询条件
    where_clause = "WHERE 1=1"
    params = []
    
    if search:
        where_clause += " AND (username LIKE %s OR action LIKE %s OR target LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    
    if action:
        where_clause += " AND action LIKE %s"
        params.append(f"%{action}%")
    
    if username:
        where_clause += " AND username LIKE %s"
        params.append(f"%{username}%")
    
    if target:
        where_clause += " AND target LIKE %s"
        params.append(f"%{target}%")
    
    if details:
        where_clause += " AND details LIKE %s"
        params.append(f"%{details}%")
    
    if start_date:
        where_clause += " AND created_at >= %s"
        params.append(start_date)
    
    if end_date:
        where_clause += " AND created_at <= %s"
        params.append(end_date)
    
    # 优化查询：使用分页分批获取数据，避免一次性加载大量数据
    logs = []
    batch_size = 1000
    page = 0
    
    while True:
        offset = page * batch_size
        logs_query = f"SELECT * FROM audit_logs {where_clause} ORDER BY created_at DESC LIMIT %s OFFSET %s"
        batch_params = params + [batch_size, offset]
        batch_logs = execute_db_query(logs_query, batch_params)
        
        if not batch_logs:
            break
            
        logs.extend(batch_logs)
        page += 1
        
        # 防止无限循环（安全措施）
        if page > 1000:  # 最多100万条记录
            break
    
    # 生成CSV内容
    import csv
    import io
    from datetime import datetime
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入标题行
    writer.writerow(['序号', '用户名', '操作类型', '操作目标', '操作详情', 'IP地址', '创建时间'])
    
    # 写入数据行
    for index, log in enumerate(logs):
        # 使用连续序号，从1开始
        sequential_number = index + 1
        details_str = ''
        if log.get('details'):
            import json
            details = log['details']
            if isinstance(details, str):
                try:
                    details = json.loads(details)
                except:
                    details_str = details
                    details = None
            
            if isinstance(details, dict):
                # 优先使用后端提供的格式化详情
                if details.get('formatted'):
                    details_str = details['formatted']
                else:
                    # 使用与前端相同的格式化逻辑
                    action = log['action']
                    try:
                        if not details: 
                            details_str = '无详细信息'
                        elif action == '登录':
                            error_msg = details.get('error') or details.get('reason') or ''
                            result = '成功' if details.get('result') == '成功' else f'失败：{error_msg}'
                            details_str = f"登录{result}"
                        elif action in ['注销', '退出登录']:
                            details_str = '用户退出登录系统'
                        elif action == '创建用户':
                            details_str = f"创建用户：{details.get('username')} (角色：{details.get('role')})"
                        elif action == '编辑用户':
                            if details.get('old_role') and details.get('new_role') and details.get('old_role') != details.get('new_role'):
                                details_str = f"更新用户角色设置，从 {details.get('old_role')} 改为 {details.get('new_role')}"
                            else:
                                details_str = '更新用户信息'
                        elif action == '删除用户':
                            details_str = f"删除用户：{details.get('username')}"
                        elif action == '重置密码':
                            details_str = f"重置用户密码：{details.get('username')}"
                        elif action == '批量重置密码':
                            usernames = details.get('usernames', [])
                            if usernames:
                                details_str = f"批量重置密码：{', '.join(usernames)}"
                            else:
                                details_str = f"批量重置密码：共{details.get('count', 0)}个用户"
                        elif action == '修改密码':
                            details_str = '修改个人密码'
                        elif action == '更新角色':
                            details_str = f"更新角色 {details.get('role') or details.get('new_role_name')} 权限设置"
                        elif action == '删除角色':
                            details_str = f"删除角色：{details.get('role') or details.get('role_name')}"
                        elif action == '批量删除角色':
                            if details.get('roles') and details['roles']:
                                details_str = f"批量删除角色：{', '.join(details['roles'])}"
                            else:
                                details_str = f"批量删除角色：共{details.get('count', 0)}个"
                        elif action == '创建角色':
                            details_str = f"创建角色 {details.get('role_name')}，包含 {len(details.get('permissions') or [])} 个权限"
                        elif action == '更换头像':
                            details_str = '更换个人头像'
                        elif action == '修改资料':
                            details_str = '修改个人资料'
                        else:
                            # 通用格式
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
                            details_str = '；'.join(entries) if entries else '无详细信息'
                    except:
                        details_str = json.dumps(details, ensure_ascii=False)
            
        writer.writerow([
            sequential_number,
            log['username'],
            log['action'],
            log['target'],
            details_str,
            log['ip_address'],
            log['created_at']
        ])
    
    # 设置响应头
    output.seek(0)
    from flask import make_response
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=audit_logs_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv'
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    
    return response
