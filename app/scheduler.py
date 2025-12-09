from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import os
import zipfile
import json
import traceback
from app.utils import execute_db_query, format_audit_details
import csv
from io import StringIO
from app import app
from app.common import json_loads_safe, get_file_path, ensure_dir_exists, get_timestamp_filename

# 导出目录配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
export_dir = get_file_path(BASE_DIR, '..', 'audit_exports')

# 日志目录配置
log_dir = get_file_path(BASE_DIR, '..', 'logs')

# 确保目录存在
ensure_dir_exists(export_dir)
ensure_dir_exists(log_dir)

def export_audit_logs():
    """导出审计日志并压缩为zip文件"""
    try:
        with app.app_context():
            # 获取所有审计日志
            logs = execute_db_query('SELECT * FROM audit_logs ORDER BY created_at DESC')
            
            if not logs:
                app.logger.info("没有审计日志需要导出")
                return
            
            # 生成CSV内容
            csv_buffer = StringIO()
            writer = csv.writer(csv_buffer)
            
            # 写入标题行，与前端页面一致
            writer.writerow(['序号', '用户名', '操作类型', '操作目标', '操作详情', 'IP地址', '创建时间'])
            
            # 写入数据行
            for index, log in enumerate(logs):
                # 使用连续序号，从1开始
                sequential_number = index + 1
                details_str = ''
                if log.get('details'):
                    details = log['details']
                    if isinstance(details, str):
                        details_json = json_loads_safe(details)
                        if details_json is not None:
                            details = details_json
                        else:
                            details_str = details
                            details = None
                    
                    if isinstance(details, dict):
                        # 优先使用后端提供的格式化详情
                        if details.get('formatted'):
                            details_str = details['formatted']
                        else:
                            # 使用utils中的format_audit_details函数
                            details_str = format_audit_details(log['action'], details)
                    else:
                        details_str = str(details)
                        
                writer.writerow([
                    sequential_number,
                    log['username'],
                    log['action'],
                    log['target'],
                    details_str,
                    log['ip_address'],
                    log['created_at']
                ])
            
            csv_content = csv_buffer.getvalue()
            
            # 生成文件名
            csv_filename = get_timestamp_filename('audit_logs', '.csv')
            zip_filename = get_timestamp_filename('audit_logs', '.zip')
            
            csv_path = os.path.join(export_dir, csv_filename)
            zip_path = os.path.join(export_dir, zip_filename)
            
            # 保存CSV文件，添加newline=''避免空行问题
            with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
                f.write(csv_content)
            
            # 压缩为zip文件
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(csv_path, csv_filename)
            
            # 删除原始CSV文件
            os.remove(csv_path)
            
            app.logger.info(f"审计日志导出完成: {zip_filename}")
            
    except Exception as e:
        app.logger.error(f"审计日志导出失败: {str(e)}")

def clean_old_exports():
    """删除一个月前的压缩包文件"""
    try:
        one_month_ago = datetime.now() - timedelta(days=30)
        
        for filename in os.listdir(export_dir):
            file_path = os.path.join(export_dir, filename)
            if os.path.isfile(file_path) and filename.endswith('.zip'):
                # 获取文件修改时间
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_mtime < one_month_ago:
                    os.remove(file_path)
                    app.logger.info(f"删除旧审计日志文件: {filename}")
                    
    except Exception as e:
        app.logger.error(f"清理旧审计日志文件失败: {str(e)}")

def pack_log_files():
    """打包昨天的日志文件为zip"""
    try:
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        
        # 查找昨天的日志文件（TimedRotatingFileHandler会自动添加日期后缀）
        log_files = []
        for filename in os.listdir(log_dir):
            if (filename.endswith('.log') or filename.endswith('.log.' + yesterday_str)) and yesterday_str in filename:
                log_files.append(filename)
        
        if not log_files:
            app.logger.info(f"没有找到{yesterday_str}的日志文件需要打包")
            return
        
        # 生成zip文件名
        zip_filename = f"logs_{yesterday_str}.zip"
        zip_path = os.path.join(log_dir, zip_filename)
        
        # 创建zip文件
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for log_file in log_files:
                log_file_path = os.path.join(log_dir, log_file)
                zipf.write(log_file_path, log_file)
                # 删除原始日志文件
                os.remove(log_file_path)
                app.logger.info(f"已打包并删除日志文件: {log_file}")
        
        app.logger.info(f"日志文件打包完成: {zip_filename}")
        
    except Exception as e:
        app.logger.error(f"打包日志文件失败: {str(e)}")

def clean_old_logs():
    """删除一个月前的日志压缩文件"""
    try:
        one_month_ago = datetime.now() - timedelta(days=30)
        
        for filename in os.listdir(log_dir):
            file_path = os.path.join(log_dir, filename)
            if os.path.isfile(file_path) and filename.startswith('logs_') and filename.endswith('.zip'):
                # 获取文件修改时间
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_mtime < one_month_ago:
                    os.remove(file_path)
                    app.logger.info(f"删除旧日志压缩文件: {filename}")
                    
    except Exception as e:
        app.logger.error(f"清理旧日志压缩文件失败: {str(e)}")

def clean_old_db_logs():
    """删除数据库中超过一个月的审计日志"""
    try:
        with app.app_context():
            # 使用MySQL的日期函数直接在数据库中进行时间比较，避免时区问题
            # 删除超过一个月的审计日志
            result = execute_db_query(
                'DELETE FROM audit_logs WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY)',
                commit=True
            )
            deleted_count = result.rowcount if hasattr(result, 'rowcount') else 0
            
            if deleted_count > 0:
                app.logger.info(f"删除了{deleted_count}条超过一个月的数据库审计日志")
            else:
                app.logger.info("没有需要删除的数据库审计日志")
                    
    except Exception as e:
        app.logger.error(f"清理旧数据库审计日志失败: {str(e)}", exc_info=True)

# 初始化调度器
app.logger.info('正在初始化调度器...')
scheduler = BackgroundScheduler(daemon=True)
app.logger.info('调度器初始化完成')

# 添加每天导出任务（每天凌晨2点）
scheduler.add_job(func=export_audit_logs, trigger='cron', hour=2, minute=0)

# 添加每天日志打包任务（每天凌晨2点30分）
scheduler.add_job(func=pack_log_files, trigger='cron', hour=2, minute=30)

# 添加每月清理任务（每月的第一天凌晨3点）
scheduler.add_job(func=clean_old_exports, trigger='cron', day=1, hour=3, minute=0)

# 添加每月日志清理任务（每月的第一天凌晨3点30分）
scheduler.add_job(func=clean_old_logs, trigger='cron', day=1, hour=3, minute=30)

# 添加每月数据库审计日志清理任务（每月的第一天凌晨4点）
scheduler.add_job(func=clean_old_db_logs, trigger='cron', day=1, hour=4, minute=0)



# 启动调度器
def start_scheduler():
    try:
        # 确保调度器只启动一次
        if not scheduler.running:
            app.logger.info('正在启动调度器...')
            scheduler.start()
            app.logger.info('审计日志定时任务调度器已启动')
            # 记录所有已配置的定时任务
            jobs = scheduler.get_jobs()
            app.logger.info(f'已配置 {len(jobs)} 个定时任务:')
            for job in jobs:
                app.logger.info(f'  - 任务ID: {job.id}, 表达式: {job.trigger}, 函数: {job.func.__name__}')
        else:
            app.logger.info('调度器已经在运行中')
    except Exception as e:
        app.logger.error(f"启动审计日志定时任务调度器失败: {str(e)}", exc_info=True)

# 停止调度器
def stop_scheduler():
    try:
        scheduler.shutdown()
        app.logger.info("审计日志定时任务调度器已停止")
    except Exception as e:
        app.logger.error(f"停止审计日志定时任务调度器失败: {str(e)}")
