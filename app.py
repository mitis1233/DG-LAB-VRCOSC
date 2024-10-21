import sys
import asyncio
import io
import qrcode
import logging
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QComboBox, QSpinBox, QFormLayout, QGroupBox, QTextEdit
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QByteArray
from qasync import QEventLoop
from pydglab_ws import StrengthData, FeedbackButton, Channel, StrengthOperationType, RetCode, DGLabWSServer
from dglab_controller import DGLabController
from config import get_active_ip_addresses
from pythonosc import dispatcher, osc_server, udp_client

# 配置日志记录器
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QTextEditHandler(logging.Handler):
    """自定义日志处理器，用于将日志消息输出到 QTextEdit"""
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit

    def emit(self, record):
        msg = self.format(record)
        self.text_edit.append(msg)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DG-Lab WebSocket Controller")
        self.setGeometry(300, 300, 600, 800)

        # 创建主布局
        self.layout = QVBoxLayout()

        # 创建网络配置组
        self.network_config_group = QGroupBox("网络配置")
        self.form_layout = QFormLayout()

        # 网卡选择
        self.ip_combobox = QComboBox()
        active_ips = get_active_ip_addresses()
        for interface, ip in active_ips.items():
            self.ip_combobox.addItem(f"{interface}: {ip}")
        self.form_layout.addRow("选择网卡:", self.ip_combobox)

        # 端口选择
        self.port_spinbox = QSpinBox()
        self.port_spinbox.setRange(1024, 65535)
        self.port_spinbox.setValue(5678)
        self.form_layout.addRow("WS连接端口:", self.port_spinbox)

        # OSC端口选择
        self.osc_port_spinbox = QSpinBox()
        self.osc_port_spinbox.setRange(1024, 65535)
        self.osc_port_spinbox.setValue(9001)  # Default OSC recv port for VRChat
        self.form_layout.addRow("OSC接收端口:", self.osc_port_spinbox)

        self.network_config_group.setLayout(self.form_layout)
        self.layout.addWidget(self.network_config_group)

        # 二维码显示
        self.qrcode_label = QLabel(self)
        self.layout.addWidget(self.qrcode_label)

        # 当前通道强度和波形
        self.strength_label = QLabel("A通道强度: 0, B通道强度: 0")
        self.pulse_label = QLabel("A通道波形: N/A, B通道波形: N/A")
        self.layout.addWidget(self.strength_label)
        self.layout.addWidget(self.pulse_label)

        # 控制器参数设置
        self.controller_group = QGroupBox("DGLabController 参数")
        self.controller_form = QFormLayout()

        self.strength_step_spinbox = QSpinBox()
        self.strength_step_spinbox.setRange(0, 100)
        self.strength_step_spinbox.setValue(30)
        self.controller_form.addRow("强度步长:", self.strength_step_spinbox)
        self.controller_group.setLayout(self.controller_form)
        self.layout.addWidget(self.controller_group)

        # 日志显示框
        self.log_text_edit = QTextEdit(self)
        self.log_text_edit.setReadOnly(True)
        self.layout.addWidget(self.log_text_edit)

        # 启动按钮
        self.start_button = QPushButton("启动")
        self.start_button.clicked.connect(self.start_server)
        self.layout.addWidget(self.start_button)

        # 设置窗口布局
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        # 设置日志处理器
        self.log_handler = QTextEditHandler(self.log_text_edit)
        logger.addHandler(self.log_handler)
        logger.setLevel(logging.INFO)

        self.controller = None

    def update_qrcode(self, qrcode_pixmap):
        """更新二维码并调整QLabel的大小"""
        self.qrcode_label.setPixmap(qrcode_pixmap)
        self.qrcode_label.setFixedSize(qrcode_pixmap.size())  # 根据二维码尺寸调整QLabel大小
        logger.info("二维码已更新")

    def update_status(self, strength_data, pulse_a, pulse_b):
        """更新通道强度和波形"""
        self.strength_label.setText(f"A通道强度: {strength_data.a}, B通道强度: {strength_data.b}")
        self.pulse_label.setText(f"A通道波形: {pulse_a}, B通道波形: {pulse_b}")
        logger.info(f"通道状态已更新 - A通道强度: {strength_data.a}, B通道强度: {strength_data.b}")

    def start_server(self):
        """启动 WebSocket 服务器"""
        selected_ip = self.ip_combobox.currentText().split(": ")[-1]
        selected_port = self.port_spinbox.value()
        osc_port = self.osc_port_spinbox.value()
        logger.info(f"正在启动 WebSocket 服务器，监听地址: {selected_ip}:{selected_port} 和 OSC 数据接收端口: {osc_port}")
        asyncio.ensure_future(run_server(self, selected_ip, selected_port, osc_port))


def generate_qrcode(data: str):
    """生成二维码并转换为PySide6可显示的QPixmap"""
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=6, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    qimage = QPixmap()
    qimage.loadFromData(buffer.read(), 'PNG')

    return qimage

def handle_osc_message_task_pad(address, list_object, *args):
    asyncio.create_task(list_object[0].handle_osc_message_pad(address, *args))

def handle_osc_message_task_pb(address, list_object, *args):
    asyncio.create_task(list_object[0].handle_osc_message_pb(address, *args))


async def run_server(window: MainWindow, ip: str, port: int, osc_port: int):
    """运行服务器并启动OSC服务器"""
    async with DGLabWSServer(ip, port, 60) as server:
        client = server.new_local_client()
        logger.info("WebSocket 客户端已初始化")

        # 生成二维码
        url = client.get_qrcode(f"ws://{ip}:{port}")
        qrcode_image = generate_qrcode(url)
        window.update_qrcode(qrcode_image)
        logger.info(f"二维码已生成，WebSocket URL: ws://{ip}:{port}")

        osc_client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
        # 初始化控制器
        controller = DGLabController(client, osc_client)
        window.controller = controller
        logger.info("DGLabController 已初始化")

        # 设置OSC服务器
        disp = dispatcher.Dispatcher()
        # 面板控制对应的 OSC 地址
        disp.map("/avatar/parameters/SoundPad/Button/*", handle_osc_message_task_pad, controller)
        disp.map("/avatar/parameters/SoundPad/Volume", handle_osc_message_task_pad, controller)
        disp.map("/avatar/parameters/SoundPad/Page", handle_osc_message_task_pad, controller)
        disp.map("/avatar/parameters/SoundPad/PanelControl", handle_osc_message_task_pad, controller)
        # PB/Contact 交互对应的 OSC 地址
        disp.map("/avatar/parameters/DG-LAB/*", handle_osc_message_task_pb, controller)
        disp.map("/avatar/parameters/Tail_Stretch", handle_osc_message_task_pb, controller)

        osc_server_instance = osc_server.AsyncIOOSCUDPServer(
            ("0.0.0.0", osc_port), disp, asyncio.get_event_loop()
        )
        osc_transport, osc_protocol = await osc_server_instance.create_serve_endpoint()
        logger.info(f"OSC Server Listening on port {osc_port}")

        async for data in client.data_generator():
            if isinstance(data, StrengthData):
                window.update_status(data, controller.pulse_mode_a, controller.pulse_mode_b)
                logger.info(f"接收到数据包 - A通道: {data.a}, B通道: {data.b}")
            # 接收 App 反馈按钮
            elif isinstance(data, FeedbackButton):
                logger.info(f"App 触发了反馈按钮：{data.name}")
            # 接收 心跳 / App 断开通知
            elif data == RetCode.CLIENT_DISCONNECTED:
                logger.info("App 已断开连接，你可以尝试重新扫码进行连接绑定")
                controller.app_status_online = False
                await client.rebind()
                logger.info("重新绑定成功")
                controller.app_status_online = True

        osc_transport.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    with loop:
        loop.run_forever()
