from PySide6.QtWidgets import (QWidget, QGroupBox, QFormLayout, QLabel, QSlider,
                               QCheckBox, QComboBox, QSpinBox, QHBoxLayout, QToolTip)
from PySide6.QtCore import Qt, QTimer, QPoint
import math
import asyncio
import logging

from pydglab_ws import Channel, StrengthOperationType
from pulse_data import PULSE_NAME

logger = logging.getLogger(__name__)

class ControllerSettingsTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.dg_controller = None

        self.layout = QFormLayout(self)
        self.setLayout(self.layout)

        # 控制器參數設置
        self.controller_group = QGroupBox("DGLabController 設置")
        self.controller_group.setEnabled(False)  # 預設禁用
        self.controller_form = QFormLayout()

        # 添加 A 通道滑動條和標籤
        self.a_channel_label = QLabel("A 通道強度: 0 / 100")  # 默認顯示
        self.a_channel_slider = QSlider(Qt.Horizontal)
        self.a_channel_slider.setRange(0, 100)  # 默認範圍
        self.a_channel_slider.valueChanged.connect(self.set_a_channel_strength)
        self.a_channel_slider.sliderPressed.connect(self.disable_a_channel_updates)  # 用戶開始拖動時禁用外部更新
        self.a_channel_slider.sliderReleased.connect(self.enable_a_channel_updates)  # 用戶釋放時重新啟用外部更新
        self.a_channel_slider.valueChanged.connect(lambda: self.show_tooltip(self.a_channel_slider))  # 即時顯示提示
        self.controller_form.addRow(self.a_channel_label)
        self.controller_form.addRow(self.a_channel_slider)

        # 添加 B 通道滑動條和標籤
        self.b_channel_label = QLabel("B 通道強度: 0 / 100")  # 默認顯示
        self.b_channel_slider = QSlider(Qt.Horizontal)
        self.b_channel_slider.setRange(0, 100)  # 默認範圍
        self.b_channel_slider.valueChanged.connect(self.set_b_channel_strength)
        self.b_channel_slider.sliderPressed.connect(self.disable_b_channel_updates)  # 用戶開始拖動時禁用外部更新
        self.b_channel_slider.sliderReleased.connect(self.enable_b_channel_updates)  # 用戶釋放時重新啟用外部更新
        self.b_channel_slider.valueChanged.connect(lambda: self.show_tooltip(self.b_channel_slider))  # 即時顯示提示
        self.controller_form.addRow(self.b_channel_label)
        self.controller_form.addRow(self.b_channel_slider)

        # 控制滑動條外部更新的狀態標誌
        self.allow_a_channel_update = True
        self.allow_b_channel_update = True

        # 是否啟用面板控制
        self.enable_panel_control_checkbox = QCheckBox("允許 avatar 控制設備") # PanelControl 關閉後忽略所有遊戲內傳入的控制
        self.enable_panel_control_checkbox.setChecked(True)
        self.controller_form.addRow(self.enable_panel_control_checkbox)

        # ChatBox狀態開關
        self.enable_chatbox_status_checkbox = QCheckBox("啟用ChatBox狀態顯示")
        self.enable_chatbox_status_checkbox.setChecked(False)
        self.controller_form.addRow(self.enable_chatbox_status_checkbox)

        # 創建水平布局用於放置 dynamic_bone_mode 和 current_select_channel 顯示
        dynamic_bone_layout = QHBoxLayout()

        # 動骨模式選擇
        self.dynamic_bone_mode_a_checkbox = QCheckBox("A通道交互模式")
        self.dynamic_bone_mode_b_checkbox = QCheckBox("B通道交互模式")

        # 添加複選框到水平布局
        dynamic_bone_layout.addWidget(self.dynamic_bone_mode_a_checkbox)
        dynamic_bone_layout.addWidget(self.dynamic_bone_mode_b_checkbox)

        # 在同行右側增加 current_select_channel 顯示標籤
        self.current_channel_label = QLabel("面板當前控制通道: 未設置")
        dynamic_bone_layout.addWidget(self.current_channel_label)

        # 將水平布局添加到主布局
        self.controller_form.addRow(dynamic_bone_layout)

        # 波形模式選擇
        self.pulse_mode_a_combobox = QComboBox()
        self.pulse_mode_b_combobox = QComboBox()
        for pulse_name in PULSE_NAME:
            self.pulse_mode_a_combobox.addItem(pulse_name)
            self.pulse_mode_b_combobox.addItem(pulse_name)
        self.controller_form.addRow("A通道波形模式:", self.pulse_mode_a_combobox)
        self.controller_form.addRow("B通道波形模式:", self.pulse_mode_b_combobox)

        # 強度步長
        self.strength_step_spinbox = QSpinBox()
        self.strength_step_spinbox.setRange(0, 100)
        self.strength_step_spinbox.setValue(30)
        self.controller_form.addRow("開火強度步長:", self.strength_step_spinbox)

        self.controller_group.setLayout(self.controller_form)
        self.layout.addRow(self.controller_group)

        # Connect UI to controller update methods
        self.strength_step_spinbox.valueChanged.connect(self.update_strength_step)
        self.enable_panel_control_checkbox.stateChanged.connect(self.update_panel_control)
        self.dynamic_bone_mode_a_checkbox.stateChanged.connect(self.update_dynamic_bone_mode_a)
        self.dynamic_bone_mode_b_checkbox.stateChanged.connect(self.update_dynamic_bone_mode_b)
        self.pulse_mode_a_combobox.currentIndexChanged.connect(self.update_pulse_mode_a)
        self.pulse_mode_b_combobox.currentIndexChanged.connect(self.update_pulse_mode_b)
        self.enable_chatbox_status_checkbox.stateChanged.connect(self.update_chatbox_status)

    def bind_controller_settings(self):
        """將GUI設置與DGLabController變數綁定"""
        if self.main_window.controller:
            self.dg_controller = self.main_window.controller
            self.dg_controller.fire_mode_strength_step = self.strength_step_spinbox.value()
            self.dg_controller.enable_panel_control = self.enable_panel_control_checkbox.isChecked()
            self.dg_controller.is_dynamic_bone_mode_a = self.dynamic_bone_mode_a_checkbox.isChecked()
            self.dg_controller.is_dynamic_bone_mode_b = self.dynamic_bone_mode_b_checkbox.isChecked()
            self.dg_controller.pulse_mode_a = self.pulse_mode_a_combobox.currentIndex()
            self.dg_controller.pulse_mode_b = self.pulse_mode_b_combobox.currentIndex()
            self.dg_controller.enable_chatbox_status = self.enable_chatbox_status_checkbox.isChecked()
            logger.info("DGLabController 參數已綁定")
        else:
            logger.warning("Controller is not initialized yet.")

    # Controller update methods
    def update_strength_step(self, value):
        if self.main_window.controller:
            controller = self.main_window.controller
            self.dg_controller.fire_mode_strength_step = value
            logger.info(f"Updated strength step to {value}")
            self.dg_controller.send_value_to_vrchat("/avatar/parameters/SoundPad/Volume", 0.01*value)

    def update_panel_control(self, state):
        if self.main_window.controller:
            controller = self.main_window.controller
            self.dg_controller.enable_panel_control = bool(state)
            logger.info(f"Panel control enabled: {self.dg_controller.enable_panel_control}")
            self.dg_controller.send_value_to_vrchat("/avatar/parameters/SoundPad/PanelControl", bool(state))

    def update_dynamic_bone_mode_a(self, state):
        if self.main_window.controller:
            controller = self.main_window.controller
            self.dg_controller.is_dynamic_bone_mode_a = bool(state)
            logger.info(f"Dynamic bone mode A: {self.dg_controller.is_dynamic_bone_mode_a}")

    def update_dynamic_bone_mode_b(self, state):
        if self.main_window.controller:
            controller = self.main_window.controller
            self.dg_controller.is_dynamic_bone_mode_b = bool(state)
            logger.info(f"Dynamic bone mode B: {self.dg_controller.is_dynamic_bone_mode_b}")

    def update_pulse_mode_a(self, index):
        if self.main_window.controller:
            asyncio.create_task(self.dg_controller.set_pulse_data(None, Channel.A, index))
            logger.info(f"Pulse mode A updated to {PULSE_NAME[index]}")

    def update_pulse_mode_b(self, index):
        if self.main_window.controller:
            asyncio.create_task(self.dg_controller.set_pulse_data(None, Channel.B, index))
            logger.info(f"Pulse mode B updated to {PULSE_NAME[index]}")

    def update_chatbox_status(self, state):
        if self.main_window.controller:
            controller = self.main_window.controller
            self.dg_controller.enable_chatbox_status = bool(state)
            logger.info(f"ChatBox status enabled: {self.dg_controller.enable_chatbox_status}")

    def set_a_channel_strength(self, value):
        """根據滑動條的值設定 A 通道強度"""
        if self.main_window.controller:
            asyncio.create_task(self.dg_controller.client.set_strength(Channel.A, StrengthOperationType.SET_TO, value))
            self.dg_controller.last_strength.a = value  # 同步更新 last_strength 的 A 通道值
            self.a_channel_slider.setToolTip(f"SET A 通道強度: {value}")

    def set_b_channel_strength(self, value):
        """根據滑動條的值設定 B 通道強度"""
        if self.main_window.controller:
            asyncio.create_task(self.dg_controller.client.set_strength(Channel.B, StrengthOperationType.SET_TO, value))
            self.dg_controller.last_strength.b = value  # 同步更新 last_strength 的 B 通道值
            self.b_channel_slider.setToolTip(f"SET B 通道強度: {value}")

    def disable_a_channel_updates(self):
        """禁用 A 通道的外部更新"""
        self.allow_a_channel_update = False

    def enable_a_channel_updates(self):
        """啟用 A 通道的外部更新"""
        self.allow_a_channel_update = True
        self.set_a_channel_strength(self.a_channel_slider.value())  # 用戶釋放時，更新設備

    def disable_b_channel_updates(self):
        """禁用 B 通道的外部更新"""
        self.allow_b_channel_update = False

    def enable_b_channel_updates(self):
        """啟用 B 通道的外部更新"""
        self.allow_b_channel_update = True
        self.set_b_channel_strength(self.b_channel_slider.value())  # 用戶釋放時，更新設備

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

    def update_current_channel_display(self, channel_name):
        """更新當前選擇通道顯示"""
        self.current_channel_label.setText(f"面板當前控制通道: {channel_name}")

    def update_channel_strength_labels(self, strength_data):
        logger.info(f"通道狀態已更新 - A通道強度: {strength_data.a}, B通道強度: {strength_data.b}")
        if self.main_window.controller and self.main_window.controller.last_strength:
            # 僅當允許外部更新時更新 A 通道滑動條
            if self.allow_a_channel_update:
                self.a_channel_slider.blockSignals(True)
                self.a_channel_slider.setRange(0, self.main_window.controller.last_strength.a_limit)  # 根據限制更新範圍
                self.a_channel_slider.setValue(self.main_window.controller.last_strength.a)
                self.a_channel_slider.blockSignals(False)
                self.a_channel_label.setText(
                    f"A 通道強度: {self.main_window.controller.last_strength.a} 強度上限: {self.main_window.controller.last_strength.a_limit}  波形: {PULSE_NAME[self.main_window.controller.pulse_mode_a]}")

            # 僅當允許外部更新時更新 B 通道滑動條
            if self.allow_b_channel_update:
                self.b_channel_slider.blockSignals(True)
                self.b_channel_slider.setRange(0, self.main_window.controller.last_strength.b_limit)  # 根據限制更新範圍
                self.b_channel_slider.setValue(self.main_window.controller.last_strength.b)
                self.b_channel_slider.blockSignals(False)
                self.b_channel_label.setText(
                    f"B 通道強度: {self.main_window.controller.last_strength.b} 強度上限: {self.main_window.controller.last_strength.b_limit}  波形: {PULSE_NAME[self.main_window.controller.pulse_mode_b]}")
