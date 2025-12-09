# 通用工具函数模块
import os
import json
import datetime
from typing import Any, Dict, List, Optional, Union


def ensure_dir_exists(directory_path: str) -> None:
    """
    确保目录存在，如果不存在则创建
    
    参数:
        directory_path: 目录路径
    """
    os.makedirs(directory_path, exist_ok=True)


def get_file_path(base_dir: str, *path_parts: str) -> str:
    """
    获取文件路径，处理路径拼接
    
    参数:
        base_dir: 基础目录
        path_parts: 路径部分列表
    
    返回:
        完整的文件路径
    """
    return os.path.join(base_dir, *path_parts)


def convert_datetime_fields(data: Union[Dict[str, Any], List[Dict[str, Any]]], 
                            datetime_format: str = '%Y-%m-%d %H:%M:%S') -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    将字典或字典列表中的datetime对象转换为字符串格式
    
    参数:
        data: 包含datetime字段的字典或字典列表
        datetime_format: 日期时间字符串格式
    
    返回:
        转换后的字典或字典列表
    """
    if isinstance(data, list):
        return [_convert_datetime_fields_dict(item, datetime_format) for item in data]
    elif isinstance(data, dict):
        return _convert_datetime_fields_dict(data, datetime_format)
    return data


def _convert_datetime_fields_dict(data_dict: Dict[str, Any], datetime_format: str) -> Dict[str, Any]:
    """
    辅助函数：将单个字典中的datetime对象转换为字符串格式
    
    参数:
        data_dict: 包含datetime字段的字典
        datetime_format: 日期时间字符串格式
    
    返回:
        转换后的字典
    """
    for key, value in data_dict.items():
        if isinstance(value, datetime.datetime):
            data_dict[key] = value.strftime(datetime_format)
    return data_dict


def json_loads_safe(json_str: Optional[str]) -> Optional[Union[Dict[str, Any], List[Any]]]:
    """
    安全地解析JSON字符串
    
    参数:
        json_str: JSON字符串
    
    返回:
        解析后的JSON对象，如果解析失败则返回None
    """
    if not json_str:
        return None
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None


def json_dumps_safe(data: Any, ensure_ascii: bool = False) -> str:
    """
    安全地将Python对象转换为JSON字符串
    
    参数:
        data: Python对象
        ensure_ascii: 是否确保ASCII编码，默认为False（支持中文）
    
    返回:
        JSON字符串，如果转换失败则返回空字符串
    """
    try:
        return json.dumps(data, ensure_ascii=ensure_ascii)
    except (TypeError, ValueError):
        return ""


def str_to_bool(value: Optional[str], default: bool = False) -> bool:
    """
    将字符串转换为布尔值
    
    参数:
        value: 字符串值
        default: 默认值
    
    返回:
        布尔值
    """
    if value is None:
        return default
    
    return value.lower() in ['true', '1', 'yes', 'on', 'y']


def get_timestamp_filename(prefix: str, suffix: str, 
                          datetime_format: str = '%Y-%m-%d_%H-%M-%S') -> str:
    """
    生成带时间戳的文件名
    
    参数:
        prefix: 文件名前缀
        suffix: 文件名后缀（如.csv、.zip）
        datetime_format: 时间戳格式
    
    返回:
        带时间戳的文件名
    """
    timestamp = datetime.datetime.now().strftime(datetime_format)
    return f"{prefix}_{timestamp}{suffix}"
