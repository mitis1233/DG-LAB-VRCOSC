from PySide6.QtWidgets import (QWidget, QGroupBox, QFormLayout, QCheckBox, QLabel,
                               QProgressBar, QSlider, QSpinBox, QHBoxLayout, QToolTip)
from PySide6.QtCore import Qt, QTimer, QPoint
import math
import asyncio
import logging
import json

from pydglab_ws import Channel, StrengthOperationType

from ton_websocket_handler import WebSocketClient

logger = logging.getLogger(__name__)

class TonDamageSystemTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.layout = QFormLayout(self)
        self.setLayout(self.layout)

        # Damage System UI
        self.damage_group = QGroupBox("Terrors of Nowhere")
        self.damage_group.setEnabled(False)
        self.damage_layout = QFormLayout()

        self.damage_info_layout = QHBoxLayout()
        # Enable Damage System Checkbox
        self.enable_damage_checkbox = QCheckBox("ToN Damage System")
        self.enable_damage_checkbox.stateChanged.connect(self.toggle_damage_system)
        self.damage_info_layout.addWidget(self.enable_damage_checkbox)

        # 增加用於顯示 DisplayName 的標籤
        self.display_name_label = QLabel("User Display Name: 未知")  # 默認顯示為 "未知"
        self.damage_info_layout.addWidget(self.display_name_label)

        # WebSocket Status Label
        self.websocket_status_label = QLabel("WebSocket Status: Disconnected")
        self.damage_info_layout.addWidget(self.websocket_status_label)

        # 將水平布局添加到主布局中
        self.damage_layout.addRow(self.damage_info_layout)

        # Damage Progress Bar
        self.damage_progress_bar = QProgressBar()
        self.damage_progress_bar.setRange(0, 100)
        self.damage_progress_bar.setValue(0)  # Initial damage is 0%
        self.damage_layout.addRow("累計傷害:", self.damage_progress_bar)

        # 統一滑動條的寬度
        slider_max_width = 450

        # 創建橫向布局，用於傷害減免滑動條和標籤
        self.damage_reduction_layout = QHBoxLayout()
        self.damage_reduction_label = QLabel("每秒傷害減免強度: 2 / 10")  # 默認顯示
        self.damage_reduction_slider = QSlider(Qt.Horizontal)
        self.damage_reduction_slider.setRange(0, 10)
        self.damage_reduction_slider.setValue(2)  # Default reduction strength per second
        self.damage_reduction_slider.setMaximumWidth(slider_max_width)  # 設置滑動條的最大寬度
        self.damage_reduction_slider.valueChanged.connect(
            lambda value: self.damage_reduction_label.setText(f"每秒傷害減免強度: {value} / 10"))
        self.damage_reduction_slider.valueChanged.connect(
            lambda: self.show_tooltip(self.damage_reduction_slider))  # 即時顯示提示
        self.damage_reduction_layout.addWidget(self.damage_reduction_label)
        self.damage_reduction_layout.addWidget(self.damage_reduction_slider)
        self.damage_reduction_layout.setAlignment(Qt.AlignRight)  # 使整個布局靠右對齊
        self.damage_layout.addRow(self.damage_reduction_layout)

        # 創建橫向布局，用於傷害強度滑動條和標籤
        self.damage_strength_layout = QHBoxLayout()
        self.damage_strength_label = QLabel("傷害對應強度上限: 50 / 200")  # 默認顯示
        self.damage_strength_slider = QSlider(Qt.Horizontal)
        self.damage_strength_slider.setRange(0, 200)
        self.damage_strength_slider.setValue(60)  # Default strength multiplier
        self.damage_strength_slider.setMaximumWidth(slider_max_width)  # 設置滑動條的最大寬度
        self.damage_strength_slider.valueChanged.connect(
            lambda value: self.damage_strength_label.setText(f"傷害對應強度上限: {value} / 200"))
        self.damage_strength_slider.valueChanged.connect(
            lambda: self.show_tooltip(self.damage_strength_slider))  # 即時顯示提示
        self.damage_strength_layout.addWidget(self.damage_strength_label)
        self.damage_strength_layout.addWidget(self.damage_strength_slider)
        self.damage_strength_layout.setAlignment(Qt.AlignRight)  # 使整個布局靠右對齊
        self.damage_layout.addRow(self.damage_strength_layout)

        # 創建橫向布局，用於死亡懲罰強度滑動條和標籤
        self.death_penalty_strength_layout = QHBoxLayout()
        self.death_penalty_strength_label = QLabel("死亡懲罰強度: 30 / 100")  # 默認顯示
        self.death_penalty_strength_slider = QSlider(Qt.Horizontal)
        self.death_penalty_strength_slider.setRange(0, 100)
        self.death_penalty_strength_slider.setValue(30)  # Default death penalty strength is 100%
        self.death_penalty_strength_slider.setMaximumWidth(slider_max_width)  # 設置滑動條的最大寬度
        self.death_penalty_strength_slider.valueChanged.connect(
            lambda value: self.death_penalty_strength_label.setText(f"死亡懲罰強度: {value} / 100"))
        self.death_penalty_strength_slider.valueChanged.connect(
            lambda: self.show_tooltip(self.death_penalty_strength_slider))  # 即時顯示提示
        self.death_penalty_strength_layout.addWidget(self.death_penalty_strength_label)
        self.death_penalty_strength_layout.addWidget(self.death_penalty_strength_slider)
        self.death_penalty_strength_layout.setAlignment(Qt.AlignRight)  # 使整個布局靠右對齊
        self.damage_layout.addRow(self.death_penalty_strength_layout)

        # 死亡懲罰持續時間
        self.death_penalty_time_spinbox = QSpinBox()
        self.death_penalty_time_spinbox.setRange(0, 60)
        self.death_penalty_time_spinbox.setValue(5)  # Default penalty time is 10 seconds
        self.damage_layout.addRow("死亡懲罰持續時間 (s):", self.death_penalty_time_spinbox)

        self.damage_group.setLayout(self.damage_layout)
        self.layout.addRow(self.damage_group)

        # Main Timer for Damage Reduction
        self.damage_timer = QTimer(self)
        self.damage_timer.timeout.connect(self.reduce_damage)

        # WebSocket Client (Initialized as None)
        self.websocket_client = None

    def show_tooltip(self, slider):
        """顯示滑動條當前值的工具提示在滑塊上方"""
        value = slider.value()

        # 獲取滑塊的位置
        slider_min = slider.minimum()
        slider_max = slider.maximum()
        slider_range = slider_max - slider_min
        slider_length = slider.width()  # 滑條的總長度

        # 計算滑塊的位置
        slider_pos = (value - slider_min) / slider_range * slider_length

        # 滑塊的位置轉換為全局坐標，並計算顯示位置
        global_pos = slider.mapToGlobal(slider.rect().topLeft())
        tooltip_x = global_pos.x() + slider_pos - 15  # 調整 tooltip 水平位置，使其居中
        tooltip_y = global_pos.y() - 40  # 調整 tooltip 垂直位置，使其顯示在滑塊上方

        # 顯示提示框
        QToolTip.showText(QPoint(tooltip_x, tooltip_y), f"{value}", slider)

    def toggle_damage_system(self, enabled):
        """Enable or disable the damage system, including WebSocket connection."""
        if enabled:
            logger.info("Enabling damage system and starting WebSocket connection.")
            # Start WebSocket connection and damage timer
            self.websocket_client = WebSocketClient("ws://localhost:11398")
            self.websocket_client.status_update_signal.connect(self.handle_websocket_status_update)
            self.websocket_client.message_received.connect(self.handle_websocket_message)
            self.websocket_client.error_signal.connect(self.handle_websocket_error)
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(self.websocket_client.start_connection(), loop)
            self.damage_timer.start(1000)  # Reduce damage every second
        else:
            logger.info("Disabling damage system and closing WebSocket connection.")
            # Stop WebSocket connection and damage timer
            if self.websocket_client:
                loop = asyncio.get_event_loop()
                asyncio.run_coroutine_threadsafe(self.websocket_client.close(), loop)
                self.websocket_client = None
            self.damage_timer.stop()
            self.reset_damage()
            self.websocket_status_label.setText("WebSocket Status: 未連接")
            self.websocket_status_label.setStyleSheet("color: red;")

    def reduce_damage(self):
        """Reduce the accumulated damage based on the set reduction strength every second."""
        reduction_strength = self.damage_reduction_slider.value()
        current_value = self.damage_progress_bar.value()
        new_value = max(0, current_value - reduction_strength)  # Ensure damage does not go below 0%
        new_strength = math.floor(0.01 * new_value * self.damage_strength_slider.value())
        self.damage_progress_bar.setValue(new_value)
        if current_value > 0:
            logger.info(f"Damage reduced by {reduction_strength}%. Current damage: {new_value}%")
        if self.main_window.app_status_online and self.main_window.controller.last_strength and self.main_window.controller.last_strength.a != new_value and not self.main_window.controller.fire_mode_active:
            asyncio.create_task(self.main_window.controller.client.set_strength(Channel.A, StrengthOperationType.SET_TO, new_strength))

    def handle_websocket_message(self, message):
        """Handle incoming WebSocket messages and update status or damage accordingly."""
        logger.info(f"Received WebSocket message: {message}")

        # 如果消息是字串類型，嘗試解析為 JSON
        if isinstance(message, str):
            try:
                message = json.loads(message)
            except json.JSONDecodeError:
                logger.error("Received message is not valid JSON format.")
                return

        # 處理不同類型的消息
        if message.get("Type") == "DAMAGED":
            damage_value = message.get("Value", 0)  # 確保獲取大小寫正確的 "Value"
            self.accumulate_damage(damage_value)
        elif message.get("Type") == "SAVED":
            self.reset_damage()
            logger.info("存檔更新，重設強度")
        elif message.get("Type") == "ALIVE":
            is_alive = message.get("Value", 0)
            if not is_alive:
                asyncio.create_task(self.trigger_death_penalty())
                logger.info("已死亡，觸發死亡懲罰")
        elif message.get("Type") == "STATS":
            if message.get("DisplayName"):
                user_display_name = message.get("DisplayName")
                self.display_name_label.setText(f"User Display Name: {user_display_name}")
        elif message.get("Type") == "CONNECTED":
            if message.get("DisplayName"):
                user_display_name = message.get("DisplayName")
                self.display_name_label.setText(f"User Display Name: {user_display_name}")

    def handle_websocket_status_update(self, status):
        """Update WebSocket status label based on connection status."""
        logger.info(f"WebSocket status updated: {status}")
        # Log the exact value of the status for better debugging
        if status.lower() == "connected":
            self.websocket_status_label.setText("WebSocket Status: 已連接")
            self.websocket_status_label.setStyleSheet("color: green;")
        elif status.lower() == "disconnected":
            self.websocket_status_label.setText("WebSocket Status: 未連接")
            self.websocket_status_label.setStyleSheet("color: red;")
        else:
            logger.warning(f"Unexpected WebSocket status: {status}")
            self.websocket_status_label.setText(f"WebSocket Status: 錯誤 - {status}")
            self.websocket_status_label.setStyleSheet("color: orange;")

    def handle_websocket_error(self, error_message):
        """Handle WebSocket errors by displaying an error message."""
        logger.error(f"WebSocket error: {error_message}")
        self.websocket_status_label.setText(f"WebSocket Status: 錯誤 - {error_message}")
        self.websocket_status_label.setStyleSheet("color: orange;")

    def accumulate_damage(self, value):
        """Accumulate damage based on incoming value."""
        current_value = self.damage_progress_bar.value()
        new_value = min(100, current_value + value)  # Cap damage at 100%
        self.damage_progress_bar.setValue(new_value)
        logger.info(f"Accumulated damage by {value}%. Current damage: {new_value}%")

    def reset_damage(self):
        """Reset the damage accumulation."""
        logger.info("Resetting damage accumulation.")
        self.damage_progress_bar.setValue(0)
        if self.main_window.app_status_online and self.main_window.controller:
            asyncio.create_task(self.main_window.controller.client.set_strength(Channel.A, StrengthOperationType.SET_TO, 0))
            asyncio.create_task(self.main_window.controller.strength_fire_mode(False, Channel.A, self.death_penalty_strength_slider.value(), self.main_window.controller.last_strength)) #可能遺漏

    async def trigger_death_penalty(self):
        """Trigger death penalty by setting damage to 100% and applying penalty."""
        penalty_strength = self.death_penalty_strength_slider.value()  # 獲取懲罰強度
        penalty_time = self.death_penalty_time_spinbox.value()  # 獲取懲罰持續時間
        logger.warning(f"Death penalty triggered: Strength={penalty_strength}, Time={penalty_time}s")
        self.damage_progress_bar.setValue(100)  # 將傷害設置為 100%
        if self.main_window.controller:
            last_strength_mod = self.main_window.controller.last_strength
            last_strength_mod.a = self.damage_strength_slider.value() # 開火值基於傷害強度上限更新
            logger.warning(f"Death penalty triggered: a {last_strength_mod.a} fire {penalty_strength}")
            # 開始懲罰
            if self.main_window.app_status_online:
                asyncio.create_task(self.main_window.controller.strength_fire_mode(True, Channel.A, penalty_strength, last_strength_mod))
                await asyncio.sleep(penalty_time)  # 等待指定的懲罰持續時間
                asyncio.create_task(self.main_window.controller.strength_fire_mode(False, Channel.A, penalty_strength, last_strength_mod))
