import sys
import asyncio
import os
os.environ['QT_API'] = 'pyside6'
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PySide6.QtGui import QIcon
from qasync import QEventLoop
import logging

from config import load_settings
from logger_config import setup_logging

# Import the GUI modules
from gui.network_config_tab import NetworkConfigTab
from gui.controller_settings_tab import ControllerSettingsTab
from gui.ton_damage_system_tab import TonDamageSystemTab
from gui.log_viewer_tab import LogViewerTab
from gui.osc_parameters import OSCParametersTab

setup_logging()
# Configure the logger
logger = logging.getLogger(__name__)

def resource_path(relative_path):
    """ 獲取資源的絕對路徑，確保開發和打包後都能正常使用。 """
    if hasattr(sys, '_MEIPASS'):  # PyInstaller 打包後的路徑
        return os.path.join(sys._MEIPASS, relative_path)
    # 對於開發環境下，從 src 跳到項目根目錄，再進入 docs/images
    return os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), relative_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DG-Lab WebSocket Controller for VRChat")
        self.setGeometry(300, 300, 650, 600)

        # 設置窗口圖示
        self.setWindowIcon(QIcon(resource_path('docs/images/fish-cake.ico')))

        # Load settings from file or use defaults
        self.settings = load_settings() or {
            'interface': '',
            'ip': '',
            'port': 5678,
            'osc_port': 9001
        }

        # Set initial controller to None
        self.controller = None
        self.app_status_online = False

        # Create the tab widget
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Create tabs and pass reference to MainWindow
        self.network_config_tab = NetworkConfigTab(self)
        self.controller_settings_tab = ControllerSettingsTab(self)
        self.ton_damage_system_tab = TonDamageSystemTab(self)
        self.log_viewer_tab = LogViewerTab(self)
        self.osc_parameters_tab = OSCParametersTab(self)


        # Add tabs to the tab widget
        self.tab_widget.addTab(self.network_config_tab, "網路配置")
        self.tab_widget.addTab(self.controller_settings_tab, "控制器設置")
        self.tab_widget.addTab(self.osc_parameters_tab, "OSC參數配置")
        self.tab_widget.addTab(self.ton_damage_system_tab, "ToN遊戲同步")
        self.tab_widget.addTab(self.log_viewer_tab, "日誌查看")

        # Setup logging to the log viewer
        self.app_setup_logging()

    def app_setup_logging(self):
        """設置日誌系統輸出到 QTextEdit 和控制台"""
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        # 創建 QTextEditHandler 並添加到日誌系統中
        self.log_handler = self.log_viewer_tab.log_handler
        logger.addHandler(self.log_handler)

        # 限制日誌框中的最大行數
        self.log_viewer_tab.log_text_edit.textChanged.connect(lambda: self.limit_log_lines(max_lines=100))

    def limit_log_lines(self, max_lines=500):
        """限制 QTextEdit 中的最大行數，保留顏色和格式，並保持顯示最新日誌"""
        self.log_viewer_tab.limit_log_lines(max_lines)

    def update_current_channel_display(self, channel_name):
        """Update current selected channel display."""
        self.controller_settings_tab.update_current_channel_display(channel_name)

    def get_osc_addresses(self):
        return self.osc_parameters_tab.get_addresses()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    with loop:
        loop.run_forever()
