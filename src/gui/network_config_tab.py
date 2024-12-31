from PySide6.QtWidgets import (QWidget, QGroupBox, QFormLayout, QComboBox, QSpinBox,
                               QLabel, QPushButton, QHBoxLayout)
from PySide6.QtCore import Qt
import logging
import asyncio

from config import get_active_ip_addresses, save_settings
from pydglab_ws import DGLabWSServer, RetCode, StrengthData, FeedbackButton
from dglab_controller import DGLabController
from qasync import asyncio
from pythonosc import osc_server, dispatcher, udp_client

import functools # Use the built-in functools module
import sys
import os
import qrcode
import io
from PySide6.QtGui import QPixmap

logger = logging.getLogger(__name__)

class NetworkConfigTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.layout = QHBoxLayout(self)
        self.setLayout(self.layout)

        # 創建網路配置組
        self.network_config_group = QGroupBox("網路配置")
        self.form_layout = QFormLayout()

        # 網卡選擇
        self.ip_combobox = QComboBox()
        active_ips = get_active_ip_addresses()
        for interface, ip in active_ips.items():
            self.ip_combobox.addItem(f"{interface}: {ip}")
        self.form_layout.addRow("選擇網卡:", self.ip_combobox)

        # 埠選擇
        self.port_spinbox = QSpinBox()
        self.port_spinbox.setRange(1024, 65535)
        self.port_spinbox.setValue(self.main_window.settings['port'])  # Set the default or loaded value
        self.form_layout.addRow("WS連接埠:", self.port_spinbox)

        # OSC埠選擇
        self.osc_port_spinbox = QSpinBox()
        self.osc_port_spinbox.setRange(1024, 65535)
        self.osc_port_spinbox.setValue(self.main_window.settings['osc_port'])  # Set the default or loaded value
        self.form_layout.addRow("OSC接收埠:", self.osc_port_spinbox)

        # 創建 dispatcher 和地址處理器字典
        self.dispatcher = dispatcher.Dispatcher()
        self.osc_address_handlers = {}  # 自訂 OSC 地址的處理器
        self.panel_control_handlers = {}  # 面板控制 OSC 地址的處理器

        # 添加用戶端連接狀態標籤
        self.connection_status_label = QLabel("未連接, 請在點擊啟動後掃描二維碼連接")
        self.connection_status_label.setAlignment(Qt.AlignCenter)  # 設置內容居中
        self.connection_status_label.setStyleSheet("QLabel {background-color: red; color: white; border-radius: 5px; padding: 5px;}")
        self.connection_status_label.adjustSize()  # 調整大小以適應內容
        self.form_layout.addRow("用戶端連接狀態:", self.connection_status_label)

        # 啟動按鈕
        self.start_button = QPushButton("啟動")
        self.start_button.setStyleSheet("background-color: green; color: white;")  # 設置按鈕初始為綠色
        self.start_button.clicked.connect(self.start_server_button_clicked)
        self.form_layout.addRow(self.start_button)

        self.network_config_group.setLayout(self.form_layout)

        # 將網路配置組添加到布局
        self.layout.addWidget(self.network_config_group)

        # 二維碼顯示
        self.qrcode_label = QLabel(self)
        self.layout.addWidget(self.qrcode_label)

        # Apply loaded settings to the UI components
        self.apply_settings_to_ui()

        # Save settings whenever network configuration is changed
        self.ip_combobox.currentTextChanged.connect(self.save_network_settings)
        self.port_spinbox.valueChanged.connect(self.save_network_settings)
        self.osc_port_spinbox.valueChanged.connect(self.save_network_settings)

    def apply_settings_to_ui(self):
        """Apply the loaded settings to the UI elements."""
        # Find the correct index for the loaded interface and IP
        for i in range(self.ip_combobox.count()):
            interface_ip = self.ip_combobox.itemText(i).split(": ")
            if len(interface_ip) == 2:
                interface, ip = interface_ip
                if interface == self.main_window.settings['interface'] and ip == self.main_window.settings['ip']:
                    self.ip_combobox.setCurrentIndex(i)
                    logger.info("set to previous used network interface")
                    break

    def save_network_settings(self):
        """Save network settings to the settings.yml file."""
        selected_interface_ip = self.ip_combobox.currentText().split(": ")
        if len(selected_interface_ip) == 2:
            selected_interface, selected_ip = selected_interface_ip
            selected_port = self.port_spinbox.value()
            osc_port = self.osc_port_spinbox.value()
            self.main_window.settings['interface'] = selected_interface
            self.main_window.settings['ip'] = selected_ip
            self.main_window.settings['port'] = selected_port
            self.main_window.settings['osc_port'] = osc_port

            save_settings(self.main_window.settings)
            logger.info("Network settings saved.")

    def start_server_button_clicked(self):
        """啟動按鈕被點擊後的處理邏輯"""
        self.start_button.setText("已啟動")  # 修改按鈕文本
        self.start_button.setStyleSheet("background-color: grey; color: white;")  # 將按鈕置灰
        self.start_button.setEnabled(False)  # 禁用按鈕
        self.start_server()  # 調用現有的啟動伺服器邏輯

    def start_server(self):
        """啟動 WebSocket 伺服器"""
        selected_ip = self.ip_combobox.currentText().split(": ")[-1]
        selected_port = self.port_spinbox.value()
        osc_port = self.osc_port_spinbox.value()
        logger.info(
            f"正在啟動 WebSocket 伺服器，監聽地址: {selected_ip}:{selected_port} 和 OSC 數據接收埠: {osc_port}")
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.run_server(selected_ip, selected_port, osc_port))
            logger.info('WebSocket 伺服器已啟動')
            # After starting the server, connect the addresses_updated signal
            self.main_window.osc_parameters_tab.addresses_updated.connect(self.update_osc_mappings)
            # 啟動成功後，將按鈕設為灰色並禁用
            self.start_button.setText("已啟動")
            self.start_button.setStyleSheet("background-color: grey; color: white;")
            self.start_button.setEnabled(False)
        except OSError as e:
            error_message = f"啟動伺服器失敗: {str(e)}"
            # Log the error with error level
            logger.error(error_message)
            # Update the UI to reflect the error
            self.start_button.setText("啟動失敗,請重試")
            self.start_button.setStyleSheet("background-color: red; color: white;")
            self.start_button.setEnabled(True)
            # 記錄異常日誌
            logger.error(f"伺服器啟動過程中發生異常: {str(e)}")

    async def run_server(self, ip: str, port: int, osc_port: int):
        """運行伺服器並啟動OSC伺服器"""
        try:
            async with DGLabWSServer(ip, port, 60) as server:
                client = server.new_local_client()
                logger.info("WebSocket 用戶端已初始化")

                # Generate QR code
                url = client.get_qrcode(f"ws://{ip}:{port}")
                qrcode_image = self.generate_qrcode(url)
                self.update_qrcode(qrcode_image)
                logger.info(f"二維碼已生成，WebSocket URL: ws://{ip}:{port}")

                osc_client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
                # Initialize controller
                controller = DGLabController(client, osc_client, self.main_window)
                self.main_window.controller = controller
                logger.info("DGLabController 已初始化")
                # After controller initialization, bind settings
                self.main_window.controller_settings_tab.bind_controller_settings()

                # 設置 OSC 伺服器
                osc_server_instance = osc_server.AsyncIOOSCUDPServer(
                    ("0.0.0.0", osc_port), self.dispatcher, asyncio.get_event_loop()
                )
                osc_transport, osc_protocol = await osc_server_instance.create_serve_endpoint()
                logger.info(f"OSC Server Listening on port {osc_port}")

                # 連接 addresses_updated 信號到 update_osc_mappings 方法
                self.main_window.osc_parameters_tab.addresses_updated.connect(self.update_osc_mappings)
                # 初始化 OSC 映射，包括面板控制和自訂地址
                self.update_osc_mappings(controller)

                # Start the data processing loop
                async for data in client.data_generator():
                    if isinstance(data, StrengthData):
                        logger.info(f"接收到封包 - A通道: {data.a}, B通道: {data.b}")
                        controller.last_strength = data
                        controller.data_updated_event.set()  # 數據更新，觸發開火操作的後續事件
                        controller.app_status_online = True
                        self.main_window.app_status_online = True
                        self.update_connection_status(controller.app_status_online)
                        # Update UI components related to strength data
                        self.main_window.controller_settings_tab.update_channel_strength_labels(data)
                    elif isinstance(data, FeedbackButton):
                        logger.info(f"App 觸發了回饋按鈕：{data.name}")
                    elif data == RetCode.CLIENT_DISCONNECTED:
                        logger.info("App 已斷開連接，你可以嘗試重新掃碼進行連接綁定")
                        controller.app_status_online = False
                        self.main_window.app_status_online = False
                        self.update_connection_status(controller.app_status_online)
                        await client.rebind()
                        logger.info("重新綁定成功")
                        controller.app_status_online = True
                        self.update_connection_status(controller.app_status_online)
                    else:
                        logger.info(f"獲取到狀態碼：{RetCode}")

                osc_transport.close()
        except OSError as e:
            # Handle specific errors and log them
            error_message = f"WebSocket 伺服器啟動失敗: {str(e)}"
            logger.error(error_message)

            # 啟動過程中發生異常，恢復按鈕狀態為可點擊的紅色
            self.start_button.setText("啟動失敗，請重試")
            self.start_button.setStyleSheet("background-color: red; color: white;")
            self.start_button.setEnabled(True)
            self.main_window.log_viewer_tab.log_text_edit.append(f"ERROR: {error_message}")

    def handle_osc_message_task_pad(self, address, *args):
        asyncio.create_task(self.main_window.controller.handle_osc_message_pad(address, *args))

    def handle_osc_message_task_pb(self, address, *args):
        asyncio.create_task(self.main_window.controller.handle_osc_message_pb(address, *args))

    def generate_qrcode(self, data: str):
        """生成二維碼並轉換為PySide6可顯示的QPixmap"""
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

    def update_qrcode(self, qrcode_pixmap):
        """更新二維碼並調整QLabel的大小"""
        self.qrcode_label.setPixmap(qrcode_pixmap)
        self.qrcode_label.setFixedSize(qrcode_pixmap.size())  # 根據二維碼尺寸調整QLabel大小
        logger.info("二維碼已更新")

    def update_connection_status(self, is_online):
        self.main_window.app_status_online = is_online
        """根據設備連接狀態更新標籤的文本和顏色"""
        if is_online:
            self.connection_status_label.setText("已連接")
            self.connection_status_label.setStyleSheet("QLabel {background-color: green; color: white; border-radius: 5px; padding: 5px;}")
            # 啟用 DGLabController 設置
            self.main_window.controller_settings_tab.controller_group.setEnabled(True)  # 啟用控制器設置
            self.main_window.ton_damage_system_tab.damage_group.setEnabled(True)
        else:
            self.connection_status_label.setText("未連接")
            self.connection_status_label.setStyleSheet("QLabel {background-color: red; color: white; border-radius: 5px; padding: 5px;}")
            # 禁用 DGLabController 設置
            self.main_window.controller_settings_tab.controller_group.setEnabled(False)  # 禁用控制器設置
            self.main_window.ton_damage_system_tab.damage_group.setEnabled(False)
        self.connection_status_label.adjustSize()  # 根據內容調整標籤大小

    def update_osc_mappings(self, controller=None):
        if controller is None:
            controller = self.main_window.controller
        asyncio.run_coroutine_threadsafe(self._update_osc_mappings(controller), asyncio.get_event_loop())

    async def _update_osc_mappings(self, controller):
        # 首先，移除之前的自訂 OSC 地址映射
        for address, handler in self.osc_address_handlers.items():
            self.dispatcher.unmap(address, handler)
        self.osc_address_handlers.clear()

        # 添加新的自訂 OSC 地址映射
        osc_addresses = self.main_window.get_osc_addresses()
        for addr in osc_addresses:
            address = addr['address']
            channels = addr['channels']
            handler = functools.partial(self.handle_osc_message_task_pb_with_channels, controller=controller, channels=channels)
            self.dispatcher.map(address, handler)
            self.osc_address_handlers[address] = handler
        logger.info("OSC dispatcher mappings updated with custom addresses.")

        # 確保面板控制的 OSC 地址映射被添加（如果尚未添加）
        if not self.panel_control_handlers:
            self.add_panel_control_mappings(controller)

    def add_panel_control_mappings(self, controller):
        # 添加面板控制功能的 OSC 地址映射
        panel_addresses = [
            "/avatar/parameters/SoundPad/Button/*",
            "/avatar/parameters/SoundPad/Volume",
            "/avatar/parameters/SoundPad/Page",
            "/avatar/parameters/SoundPad/PanelControl"
        ]
        for address in panel_addresses:
            handler = functools.partial(self.handle_osc_message_task_pad, controller=controller)
            self.dispatcher.map(address, handler)
            self.panel_control_handlers[address] = handler
        logger.info("OSC dispatcher mappings updated with panel control addresses.")

    def handle_osc_message_task_pad(self, address, *args, controller):
        asyncio.create_task(controller.handle_osc_message_pad(address, *args))

    def handle_osc_message_task_pb_with_channels(self, address, *args, controller, channels):
        asyncio.create_task(controller.handle_osc_message_pb(address, *args, channels=channels))
