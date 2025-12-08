# 导入必要的模块
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from flask import request
from app import app
from app.utils import init_db

# 配置日志

def setup_logging():
    # 创建日志目录
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 创建日志格式器
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    
    # 创建文件日志处理器（每天自动轮换）
    log_file = os.path.join(log_dir, 'app.log')
    # when='midnight' 表示每天凌晨轮换
    # backupCount=0 表示不保留旧文件（我们将手动处理备份）
    file_handler = TimedRotatingFileHandler(
        log_file,
        when='midnight',
        interval=1,
        backupCount=0,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)  # 改为DEBUG级别以便调试
    
    # 清除默认处理器
    app.logger.handlers.clear()
    
    # 添加自定义处理器（只保留文件日志，不输出到控制台）
    app.logger.addHandler(file_handler)
    
    # 设置日志级别
    app.logger.setLevel(logging.INFO)  # 改为DEBUG级别以便调试

# 初始化日志配置
setup_logging()
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
    debug = os.getenv('FLASK_DEBUG', 'True').lower() in ['true', '1', 'yes']
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    # 获取SSL配置
    ssl_context = None
    if app.config.get('SSL_CERT_FILE') and app.config.get('SSL_KEY_FILE'):
        ssl_context = (app.config['SSL_CERT_FILE'], app.config['SSL_KEY_FILE'])
    
    # 运行应用
    app.run(host=host, port=port, debug=debug, ssl_context=ssl_context)
