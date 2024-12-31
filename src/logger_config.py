import logging
import colorlog
from datetime import datetime
import os

def setup_logging():
    # 獲取當前時間，用於生成日誌檔案名
    log_filename = datetime.now().strftime("DG-LAB-VRCOSC_%Y-%m-%d_%H-%M-%S.log")

    # 創建日誌目錄（如果不存在）
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # 配置日誌格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s [in %(filename)s:%(lineno)d]'

    # 創建文件日誌處理器，寫入新創建的日誌檔案
    file_handler = logging.FileHandler(os.path.join(log_dir, log_filename), encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # 文件日誌級別
    file_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)

    # 創建彩色控制台日誌處理器
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # 控制台日誌級別
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s' + log_format,
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )
    console_handler.setFormatter(console_formatter)

    # 獲取根記錄器，並添加文件和控制台處理器
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # 全局日誌級別
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # 可選：禁用第三方庫的日誌
    logging.getLogger("websockets.server").setLevel(logging.WARNING)
    logging.getLogger("websockets.protocol").setLevel(logging.WARNING)
    logging.getLogger('qasync').setLevel(logging.WARNING)

