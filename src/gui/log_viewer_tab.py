from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QGroupBox, QLabel, QHBoxLayout, QFormLayout
from PySide6.QtGui import QTextCursor
from PySide6.QtCore import Qt, QTimer
import logging

logger = logging.getLogger(__name__)

class QTextEditHandler(logging.Handler):
    """Custom log handler to output log messages to QTextEdit."""
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit

    def emit(self, record):
        msg = self.format(record)
        # Highlight error logs in red
        if record.levelno >= logging.ERROR:
            msg = f"<b style='color:red;'>{msg}</b>"  # Display error messages in red
        elif record.levelno == logging.WARNING:
            msg = f"<b style='color:orange;'>{msg}</b>"  # Display warnings in orange
        else:
            msg = f"<span>{msg}</span>"  # 預設使用普通字體
        # Append the message to the text edit and reset the cursor position
        self.text_edit.append(msg)
        self.text_edit.ensureCursorVisible()  # Ensure the latest log is visible

class SimpleFormatter(logging.Formatter):
    """自訂格式化器，將日誌級別縮寫並調整時間格式"""

    def format(self, record):
        level_short = {
            'DEBUG': 'D',
            'INFO': 'I',
            'WARNING': 'W',
            'ERROR': 'E',
            'CRITICAL': 'C'
        }.get(record.levelname, 'I')  # 默認 INFO
        record.levelname = level_short
        return super().format(record)

class LogViewerTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.dg_controller = None

        self.layout = QFormLayout(self)
        self.setLayout(self.layout)

        # 日誌顯示框 - 使用 QGroupBox 包裝
        self.log_groupbox = QGroupBox("簡約日誌")
        self.log_groupbox.setCheckable(True)
        self.log_groupbox.setChecked(True)
        self.log_groupbox.toggled.connect(self.toggle_log_display)

        # 日誌顯示框
        self.log_text_edit = QTextEdit(self)
        self.log_text_edit.setReadOnly(True)

        # 將日誌顯示框添加到 GroupBox 的布局中
        log_layout = QVBoxLayout()
        log_layout.addWidget(self.log_text_edit)
        self.log_groupbox.setLayout(log_layout)

        # 將 GroupBox 添加到主布局
        self.layout.addWidget(self.log_groupbox)

        # 設置日誌處理器
        self.log_handler = QTextEditHandler(self.log_text_edit)
        self.log_handler.setLevel(logging.DEBUG)  # 捕獲所有日誌級別

        # 使用自訂格式化器，簡化時間和日誌級別
        formatter = SimpleFormatter('%(asctime)s-%(levelname)s: %(message)s', datefmt='%H:%M:%S')
        self.log_handler.setFormatter(formatter)

        # 增加可摺疊的除錯界面
        self.debug_group = QGroupBox("除錯資訊")
        self.debug_group.setCheckable(True)
        self.debug_group.setChecked(False)  # 默認摺疊狀態
        self.debug_group.toggled.connect(self.toggle_debug_info)  # 連接信號槽

        self.debug_layout = QHBoxLayout()
        self.debug_label = QLabel("DGLabController 參數:")
        self.debug_layout.addWidget(self.debug_label)

        # 顯示控制器的參數
        self.param_label = QLabel("正在載入控制器參數...")
        self.debug_layout.addWidget(self.param_label)

        self.debug_group.setLayout(self.debug_layout)
        self.layout.addRow(self.debug_group)

        # 啟動定時器，每秒刷新一次除錯資訊
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_debug_info)
        self.timer.start(1000)  # 每秒刷新一次

    def toggle_log_display(self, enabled):
        """摺疊或展開日誌顯示框"""
        if enabled:
            self.log_text_edit.show()  # 展開時顯示日誌框
        else:
            self.log_text_edit.hide()  # 摺疊時隱藏日誌框

    def limit_log_lines(self, max_lines=500):
        """限制 QTextEdit 中的最大行數，保留顏色和格式，並保持顯示最新日誌"""
        document = self.log_text_edit.document()
        block_count = document.blockCount()
        cursor = self.log_text_edit.textCursor()
        # 如果當前行數超過最大行數
        if block_count > max_lines:
            cursor.movePosition(QTextCursor.Start)  # 移動到文本開頭

            # 選擇並刪除前面的行，直到行數符合要求
            for _ in range(block_count - max_lines):
                cursor.select(QTextCursor.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()  # 刪除行後保留格式
        # 無論是否刪除行，都移動游標到文本末尾
        cursor.movePosition(QTextCursor.End)
        self.log_text_edit.setTextCursor(cursor)
        # 確保最新日誌可見
        self.log_text_edit.ensureCursorVisible()

    def toggle_debug_info(self, checked):
        """當除錯組被啟用/禁用時摺疊或展開內容"""
        # 控制除錯資訊組中所有子組件的可見性，而不是整個除錯組
        for child in self.debug_group.findChildren(QWidget):
            child.setVisible(checked)

    def update_debug_info(self):
        """更新除錯資訊"""
        if self.main_window.controller is not None:
            self.dg_controller = self.main_window.controller
            params = (
                f"Device online: app_status_online= {self.dg_controller.app_status_online}\n "
                f"Enable Panel Control: {self.dg_controller.enable_panel_control}\n"
                f"Dynamic Bone Mode A: {self.dg_controller.is_dynamic_bone_mode_a}\n"
                f"Dynamic Bone Mode B: {self.dg_controller.is_dynamic_bone_mode_b}\n"
                f"Pulse Mode A: {self.dg_controller.pulse_mode_a}\n"
                f"Pulse Mode B: {self.dg_controller.pulse_mode_b}\n"
                f"Fire Mode Strength Step: {self.dg_controller.fire_mode_strength_step}\n"
                f"Enable ChatBox Status: {self.dg_controller.enable_chatbox_status}\n"
            )
            self.param_label.setText(params)
        else:
            self.param_label.setText("控制器未初始化.")