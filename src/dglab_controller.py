"""
dglab_controller.py
"""
import asyncio
import math

from pydglab_ws import StrengthData, FeedbackButton, Channel, StrengthOperationType, RetCode, DGLabWSServer
from pulse_data import PULSE_DATA, PULSE_NAME

import logging

logger = logging.getLogger(__name__)


class DGLabController:
    def __init__(self, client, osc_client, ui_callback=None):
        """
        初始化 DGLabController 實例
        :param client: DGLabWSServer 的用戶端實例
        :param osc_client: 用於發送 OSC 回復的用戶端實例
        :param is_dynamic_bone_mode 強度控制模式，交互模式通過動骨和Contact控制輸出強度，非動骨交互模式下僅可通過按鍵控制輸出
        此處的默認參數會被 UI 界面的默認參數覆蓋
        """
        self.client = client
        self.osc_client = osc_client
        self.main_window = ui_callback
        self.last_strength = None  # 記錄上次的強度值, 從 app更新, 包含 a b a_limit b_limit
        self.app_status_online = False  # App 端在線情況
        # 功能控制參數
        self.enable_panel_control = True   # 禁用面板控制功能 (雙向)
        self.is_dynamic_bone_mode_a = False  # Default mode for Channel A (僅程序端)
        self.is_dynamic_bone_mode_b = False  # Default mode for Channel B (僅程序端)
        self.pulse_mode_a = 0  # pulse mode for Channel A (雙向 - 更新名稱)
        self.pulse_mode_b = 0  # pulse mode for Channel B (雙向 - 更新名稱)
        self.current_select_channel = Channel.A  # 遊戲內面板控制的通道選擇, 預設為 A (雙向)
        self.fire_mode_strength_step = 30    # 一鍵開火默認強度 (雙向)
        self.fire_mode_active = False  # 標記當前是否在進行開火操作
        self.fire_mode_lock = asyncio.Lock()  # 一鍵開火模式鎖
        self.data_updated_event = asyncio.Event()  # 數據更新事件
        self.fire_mode_origin_strength_a = 0  # 進入一鍵開火模式前的強度值
        self.fire_mode_origin_strength_b = 0
        self.enable_chatbox_status = 1  # ChatBox 發送狀態 (雙向，遊戲內暫無直接開關變數)
        self.previous_chatbox_status = 1  # ChatBox 狀態記錄, 關閉 ChatBox 後進行內容清除
        # 定時任務
        self.send_status_task = asyncio.create_task(self.periodic_status_update())  # 啟動ChatBox發送任務
        self.send_pulse_task = asyncio.create_task(self.periodic_send_pulse_data())  # 啟動設定波形發送任務
        # 按鍵延遲觸發計時
        self.chatbox_toggle_timer = None
        self.set_mode_timer = None
        #TODO: 增加狀態消息OSC發送, 比使用 ChatBox 回饋更快
        # 回報速率設置為 1HZ，Updates every 0.1 to 1 seconds as needed based on parameter changes (1 to 10 updates per second), but you shouldn't rely on it for fast sync.

    async def periodic_status_update(self):
        """
        週期性通過 ChatBox 發送當前的配置狀態
        TODO: ChatBox 消息發送的速率限制是多少？當前的設置還是會撞到限制..
        """
        while True:
            try:
                if self.enable_chatbox_status:
                    await self.send_strength_status()
                    self.previous_chatbox_status = True
                elif self.previous_chatbox_status: # clear chatbox
                    self.send_message_to_vrchat_chatbox("")
                    self.previous_chatbox_status = False
            except Exception as e:
                logger.error(f"periodic_status_update 任務中發生錯誤: {e}")
                await asyncio.sleep(5)  # 延遲後重試
            await asyncio.sleep(3)  # 每 x 秒發送一次

    async def periodic_send_pulse_data(self):
        # 順序發送波形
        # TODO： 修復重連後自動發送中斷
        while True:
            try:
                if self.last_strength:  # 當收到設備狀態後再發送波形
                    logger.info(f"更新波形 A {PULSE_NAME[self.pulse_mode_a]} B {PULSE_NAME[self.pulse_mode_b]}")

                    # A 通道發送當前設定波形
                    specific_pulse_data_a = PULSE_DATA[PULSE_NAME[self.pulse_mode_a]]
                    await self.client.clear_pulses(Channel.A)

                    if PULSE_NAME[self.pulse_mode_a] == '壓縮' or PULSE_NAME[self.pulse_mode_a] == '節奏步伐':  # 單次發送長波形不能太多
                        await self.client.add_pulses(Channel.A, *(specific_pulse_data_a * 3))  # 長波形三組
                    else:
                        await self.client.add_pulses(Channel.A, *(specific_pulse_data_a * 5))  # 短波形五組

                    # B 通道發送當前設定波形
                    specific_pulse_data_b = PULSE_DATA[PULSE_NAME[self.pulse_mode_b]]
                    await self.client.clear_pulses(Channel.B)
                    if PULSE_NAME[self.pulse_mode_b] == '壓縮' or PULSE_NAME[self.pulse_mode_b] == '節奏步伐':  # 單次發送長波形不能太多
                        await self.client.add_pulses(Channel.B, *(specific_pulse_data_b * 3))  # 長波形三組
                    else:
                        await self.client.add_pulses(Channel.B, *(specific_pulse_data_b * 5))  # 短波形五組
            except Exception as e:
                logger.error(f"periodic_send_pulse_data 任務中發生錯誤: {e}")
                await asyncio.sleep(5)  # 延遲後重試
            await asyncio.sleep(3)  # 每 x 秒發送一次

    async def set_pulse_data(self, value, channel, pulse_index):
        """
            立即切換為當前指定波形，清空原有波形
        """
        if channel == Channel.A:
            self.pulse_mode_a = pulse_index
            self.main_window.controller_settings_tab.pulse_mode_a_combobox.setCurrentIndex(pulse_index)
        else:
            self.pulse_mode_b = pulse_index
            self.main_window.controller_settings_tab.pulse_mode_b_combobox.setCurrentIndex(pulse_index)

        await self.client.clear_pulses(channel)  # 清空檔前的生效的波形隊列

        logger.info(f"開始發送波形 {PULSE_NAME[pulse_index]}")
        specific_pulse_data = PULSE_DATA[PULSE_NAME[pulse_index]]
        await self.client.add_pulses(channel, *(specific_pulse_data * 3))  # 發送三份新選中的波形

    async def set_float_output(self, value, channel):
        """
        動骨與碰撞體活化對應通道輸出
        """
        if value >= 0.0:
            if channel == Channel.A and self.is_dynamic_bone_mode_a:
                final_output_a = math.ceil(
                    self.map_value(value, self.last_strength.a_limit * 0.2, self.last_strength.a_limit))
                await self.client.set_strength(channel, StrengthOperationType.SET_TO, final_output_a)
            elif channel == Channel.B and self.is_dynamic_bone_mode_b:
                final_output_b = math.ceil(
                    self.map_value(value, self.last_strength.b_limit * 0.2, self.last_strength.b_limit))
                await self.client.set_strength(channel, StrengthOperationType.SET_TO, final_output_b)

    async def chatbox_toggle_timer_handle(self):
        """1秒計時器 計時結束後切換 Chatbox 狀態"""
        await asyncio.sleep(1)

        self.enable_chatbox_status = not self.enable_chatbox_status
        mode_name = "開啟" if self.enable_chatbox_status else "關閉"
        logger.info("ChatBox顯示狀態切換為:" + mode_name)
        # 若關閉 ChatBox, 則立即發送一次空字串
        if not self.enable_chatbox_status:
            self.send_message_to_vrchat_chatbox("")
        self.chatbox_toggle_timer = None
        # 更新UI
        self.main_window.controller_settings_tab.enable_chatbox_status_checkbox.blockSignals(True)  # 防止觸發 valueChanged 事件
        self.main_window.controller_settings_tab.enable_chatbox_status_checkbox.setChecked(self.enable_chatbox_status)
        self.main_window.controller_settings_tab.enable_chatbox_status_checkbox.blockSignals(False)

    async def toggle_chatbox(self, value):
        """
        開關 ChatBox 內容發送
        TODO: 修改為按鍵按下 3 秒後觸發 enable_chatbox_status 的變更
        """
        if value == 1: # 按下按鍵
            if self.chatbox_toggle_timer is not None:
                self.chatbox_toggle_timer.cancel()
            self.chatbox_toggle_timer = asyncio.create_task(self.chatbox_toggle_timer_handle())
        elif value == 0: #鬆開按鍵
            if self.chatbox_toggle_timer:
                self.chatbox_toggle_timer.cancel()
                self.chatbox_toggle_timer = None

    async def set_mode_timer_handle(self, channel):
        await asyncio.sleep(1)

        if channel == Channel.A:
            self.is_dynamic_bone_mode_a = not self.is_dynamic_bone_mode_a
            mode_name = "可交互模式" if self.is_dynamic_bone_mode_a else "面板設置模式"
            logger.info("通道 A 切換為" + mode_name)
            # 更新UI
            self.main_window.controller_settings_tab.dynamic_bone_mode_a_checkbox.blockSignals(True)  # 防止觸發 valueChanged 事件
            self.main_window.controller_settings_tab.dynamic_bone_mode_a_checkbox.setChecked(self.is_dynamic_bone_mode_a)
            self.main_window.controller_settings_tab.dynamic_bone_mode_a_checkbox.blockSignals(False)
        elif channel == Channel.B:
            self.is_dynamic_bone_mode_b = not self.is_dynamic_bone_mode_b
            mode_name = "可交互模式" if self.is_dynamic_bone_mode_b else "面板設置模式"
            logger.info("通道 B 切換為" + mode_name)
            # 更新UI
            self.main_window.controller_settings_tab.dynamic_bone_mode_b_checkbox.blockSignals(True)  # 防止觸發 valueChanged 事件
            self.main_window.controller_settings_tab.dynamic_bone_mode_b_checkbox.setChecked(self.is_dynamic_bone_mode_b)
            self.main_window.controller_settings_tab.dynamic_bone_mode_b_checkbox.blockSignals(False)

    async def set_mode(self, value, channel):
        """
        切換工作模式, 延時一秒觸發，更改按下時對應的通道
        """
        if value == 1: # 按下按鍵
            if self.set_mode_timer is not None:
                self.set_mode_timer.cancel()
            self.set_mode_timer = asyncio.create_task(self.set_mode_timer_handle(channel))
        elif value == 0: #鬆開按鍵
            if self.set_mode_timer:
                self.set_mode_timer.cancel()
                self.set_mode_timer = None


    async def reset_strength(self, value, channel):
        """
        強度重設為 0
        """
        if value:
            await self.client.set_strength(channel, StrengthOperationType.SET_TO, 0)

    async def increase_strength(self, value, channel):
        """
        增大強度, 固定 5
        """
        if value:
            await self.client.set_strength(channel, StrengthOperationType.INCREASE, 5)

    async def decrease_strength(self, value, channel):
        """
        減小強度, 固定 5
        """
        if value:
            await self.client.set_strength(channel, StrengthOperationType.DECREASE, 5)

    async def strength_fire_mode(self, value, channel, fire_strength, last_strength):
        """
        一鍵開火：
            按下後設置為當前通道強度值 +fire_mode_strength_step
            鬆開後恢復為通道進入前的強度
        TODO: 修復連點開火按鍵導致輸出持續上升的問題
        """
        logger.info(f"Trigger FireMode: {value}")

        await asyncio.sleep(0.01)

        # 如果是開始開火並且已經在進行中，直接跳過
        if value and self.fire_mode_active:
            print("已有開火操作在進行中，跳過本次開始請求")
            return
        # 如果是結束開火並且當前沒有進行中的開火操作，跳過
        if not value and not self.fire_mode_active:
            print("沒有進行中的開火操作，跳過本次結束請求")
            return

        async with self.fire_mode_lock:
            if value:
                # 開始 fire mode
                self.fire_mode_active = True
                logger.debug(f"FIRE START {last_strength}")
                if last_strength:
                    if channel == Channel.A:
                        self.fire_mode_origin_strength_a = last_strength.a
                        await self.client.set_strength(
                            channel,
                            StrengthOperationType.SET_TO,
                            min(self.fire_mode_origin_strength_a + fire_strength, last_strength.a_limit)
                        )
                    elif channel == Channel.B:
                        self.fire_mode_origin_strength_b = last_strength.b
                        await self.client.set_strength(
                            channel,
                            StrengthOperationType.SET_TO,
                            min(self.fire_mode_origin_strength_b + fire_strength, last_strength.b_limit)
                        )
                self.data_updated_event.clear()
                await self.data_updated_event.wait()
            else:
                if channel == Channel.A:
                    await self.client.set_strength(channel, StrengthOperationType.SET_TO, self.fire_mode_origin_strength_a)
                elif channel == Channel.B:
                    await self.client.set_strength(channel, StrengthOperationType.SET_TO, self.fire_mode_origin_strength_b)
                # 等待數據更新
                self.data_updated_event.clear()  # 清除事件狀態
                await self.data_updated_event.wait()  # 等待下次數據更新
                # 結束 fire mode
                logger.debug(f"FIRE END {last_strength}")
                self.fire_mode_active = False

    async def set_strength_step(self, value):
        """
          開火模式步進值設定
        """
        if value > 0.0:
            self.fire_mode_strength_step = math.ceil(self.map_value(value, 0, 100))  # 向上取整
            logger.info(f"current strength step: {self.fire_mode_strength_step}")
            # 更新 UI 組件 (QSpinBox) 以反映新的值
            self.main_window.controller_settings_tab.strength_step_spinbox.blockSignals(True)  # 防止觸發 valueChanged 事件
            self.main_window.controller_settings_tab.strength_step_spinbox.setValue(self.fire_mode_strength_step)
            self.main_window.controller_settings_tab.strength_step_spinbox.blockSignals(False)

    async def set_channel(self, value):
        """
        value: INT
        選定當前調節對應的通道, 目前 Page 1-2 為 Channel A， Page 3 為 Channel B
        """
        if value >= 0:
            self.current_select_channel = Channel.A if value <= 1 else Channel.B
            logger.info(f"set activate channel to: {self.current_select_channel}")
            if self.main_window.controller_settings_tab:
                channel_name = "A" if self.current_select_channel == Channel.A else "B"
                self.main_window.controller_settings_tab.update_current_channel_display(channel_name)

    async def set_panel_control(self, value):
        """
        面板控制功能開關，禁用控制後無法通過 OSC 對郊狼進行調整
        """
        if value > 0:
            self.enable_panel_control = True
        else:
            self.enable_panel_control = False
        mode_name = "開啟面板控制" if self.enable_panel_control else "已禁用面板控制"
        logger.info(f": {mode_name}")
        # 更新 UI 組件 (QSpinBox) 以反映新的值
        self.main_window.controller_settings_tab.enable_panel_control_checkbox.blockSignals(True)  # 防止觸發 valueChanged 事件
        self.main_window.controller_settings_tab.enable_panel_control_checkbox.setChecked(self.enable_panel_control)
        self.main_window.controller_settings_tab.enable_panel_control_checkbox.blockSignals(False)


    async def handle_osc_message_pad(self, address, *args):
        """
        處理 OSC 消息
        1. Bool: Bool 類型變數觸發時，VRC 會先後發送 True 與 False, 回調中僅處理 True
        2. Float: -1.0 to 1.0， 但對於 Contact 與  Physbones 來說範圍為 0.0-1.0
        """
        # Parameters Debug
        logger.info(f"Received OSC message on {address} with arguments {args}")

        # 面板控制功能禁用
        if address == "/avatar/parameters/SoundPad/PanelControl":
            await self.set_panel_control(args[0])
        if not self.enable_panel_control:
            logger.info(f"已禁用面板控制功能")
            return

        #按鍵功能
        if address == "/avatar/parameters/SoundPad/Button/1":
            await self.set_mode(args[0], self.current_select_channel)
        elif address == "/avatar/parameters/SoundPad/Button/2":
            await self.reset_strength(args[0], self.current_select_channel)
        elif address == "/avatar/parameters/SoundPad/Button/3":
            await self.decrease_strength(args[0], self.current_select_channel)
        elif address == "/avatar/parameters/SoundPad/Button/4":
            await self.increase_strength(args[0], self.current_select_channel)
        elif address == "/avatar/parameters/SoundPad/Button/5":
            await self.strength_fire_mode(args[0], self.current_select_channel, self.fire_mode_strength_step, self.last_strength)

        # ChatBox 開關控制
        elif address == "/avatar/parameters/SoundPad/Button/6":#
            await self.toggle_chatbox(args[0])
        # 波形控制
        elif address == "/avatar/parameters/SoundPad/Button/7":
            await self.set_pulse_data(args[0], self.current_select_channel, 2)
        elif address == "/avatar/parameters/SoundPad/Button/8":
            await self.set_pulse_data(args[0], self.current_select_channel, 14)
        elif address == "/avatar/parameters/SoundPad/Button/9":
            await self.set_pulse_data(args[0], self.current_select_channel, 4)
        elif address == "/avatar/parameters/SoundPad/Button/10":
            await self.set_pulse_data(args[0], self.current_select_channel, 5)
        elif address == "/avatar/parameters/SoundPad/Button/11":
            await self.set_pulse_data(args[0], self.current_select_channel, 6)
        elif address == "/avatar/parameters/SoundPad/Button/12":
            await self.set_pulse_data(args[0], self.current_select_channel, 7)
        elif address == "/avatar/parameters/SoundPad/Button/13":
            await self.set_pulse_data(args[0], self.current_select_channel, 8)
        elif address == "/avatar/parameters/SoundPad/Button/14":
            await self.set_pulse_data(args[0], self.current_select_channel, 9)
        elif address == "/avatar/parameters/SoundPad/Button/15":
            await self.set_pulse_data(args[0], self.current_select_channel, 1)

        # 數值調節
        elif address == "/avatar/parameters/SoundPad/Volume": # Float
            await self.set_strength_step(args[0])
        # 通道調節
        elif address == "/avatar/parameters/SoundPad/Page": # INT
            await self.set_channel(args[0])

    async def handle_osc_message_pb(self, address, *args, channels):
        """
        處理 OSC 消息
        1. Bool: Bool 類型變數觸發時，VRC 會先後發送 True 與 False, 回調中僅處理 True
        2. Float: -1.0 to 1.0， 但對於 Contact 與  Physbones 來說範圍為 0.0-1.0
        """
        # Parameters Debug
        logger.debug(f"Received OSC message on {address} with arguments {args} and channels {channels}")

        if not self.enable_panel_control:
            return

        # Float parameter mapping to strength value
        value = args[0]
        # For each channel, set the output
        if channels.get('A', False):
            await self.set_float_output(value, Channel.A)
        if channels.get('B', False):
            await self.set_float_output(value, Channel.B)

    def map_value(self, value, min_value, max_value):
        """
        將 Contact/Physbones 值映射到強度範圍
        """
        return min_value + value * (max_value - min_value)

    def send_message_to_vrchat_chatbox(self, message: str):
        '''
        /chatbox/input s b n Input text into the chatbox.
        '''
        self.osc_client.send_message("/chatbox/input", [message, True, False])

    def send_value_to_vrchat(self, path: str, value):
        '''
        /chatbox/input s b n Input text into the chatbox.
        '''
        self.osc_client.send_message(path, value)

    async def send_strength_status(self):
        """
        通過 ChatBox 發送當前強度數值
        """
        if self.last_strength:
            mode_name_a = "交互" if self.is_dynamic_bone_mode_a else "面板"
            mode_name_b = "交互" if self.is_dynamic_bone_mode_b else "面板"
            channel_strength = f"[A]: {self.last_strength.a} B: {self.last_strength.b}" if self.current_select_channel == Channel.A else f"A: {self.last_strength.a} [B]: {self.last_strength.b}"
            self.send_message_to_vrchat_chatbox(
                f"MAX A: {self.last_strength.a_limit} B: {self.last_strength.b_limit}\n"
                f"Mode A: {mode_name_a} B: {mode_name_b} \n"
                f"Pulse A: {PULSE_NAME[self.pulse_mode_a]} B: {PULSE_NAME[self.pulse_mode_b]} \n"
                f"Fire Step: {self.fire_mode_strength_step}\n"
                f"Current: {channel_strength} \n"
            )
        else:
            self.send_message_to_vrchat_chatbox("未連接")
