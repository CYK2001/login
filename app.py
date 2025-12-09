# 导入必要的模块
import os
from flask import request
from app import app
from app.utils import init_db

# 记录应用启动日志
app.logger.info('应用启动')

# 添加错误处理
@app.errorhandler(404)
def page_not_found(e):
    from app.utils import make_json_response
    return make_json_response(404, '页面未找到', status_code=404)

@app.errorhandler(500)
def internal_server_error(e):
    app.logger.error('服务器内部错误: %s', e)
    from app.utils import make_json_response
    return make_json_response(500, '服务器内部错误', status_code=500)

# 添加全局异常处理
@app.errorhandler(Exception)
def handle_exception(e):
    # 记录异常日志
    app.logger.error('未捕获的异常: %s', str(e), exc_info=True)
    from app.utils import make_json_response
    # 根据是否是API请求返回不同格式
    if request.path.startswith('/api/'):
        return make_json_response(500, '服务器内部错误', status_code=500)
    # 页面请求返回简单信息
    return app.make_response(('服务器内部错误', 500))

# 主程序
if __name__ == '__main__':
    # 初始化数据库
    with app.app_context():
        init_db()
    
    # 获取环境变量配置
    # 根据FLASK_ENV环境变量设置debug模式，production环境下debug为False，其他为True
    debug = os.getenv('FLASK_ENV', 'development') != 'production'
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    # 获取SSL配置
    ssl_context = None
    if app.config.get('SSL_CERT_FILE') and app.config.get('SSL_KEY_FILE'):
        ssl_context = (app.config['SSL_CERT_FILE'], app.config['SSL_KEY_FILE'])
    
    # 运行应用
    app.run(host=host, port=port, debug=debug, ssl_context=ssl_context)
