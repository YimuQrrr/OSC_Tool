import os
import re
import sys
import time
import mido
import ctypes
import psutil
import socket
import tkinter
import requests
import threading
import subprocess
import customtkinter
import mido.backends.rtmidi
import customtkinter as ctk
from datetime import datetime
from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc import osc_message_builder



# customtkinter 初始设置
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("dark-blue")


# OSC_TEST GUI
class OSC_Address_Test_ToplevelWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.protocol("WM_DELETE_WINDOW", self.closing)
        self.title("OSC_Address_Test")
        self.geometry("450x130")
        self.minsize(450, 130)
        self.maxsize(450, 130)
        self.grid_columnconfigure((0,1,2), weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.attributes("-topmost", True)
        self.wm_attributes("-alpha", 0.9)

        self.value_type = "Float"
        self.rounded_value = 0.0

        self.create_entry_message_box()
        self.create_range_inputs()
        self.create_slider()

    # 创建地址输入 + 类型下拉
    def create_entry_message_box(self):
        self.type_menu = ctk.CTkOptionMenu(
            self, values=["Float", "Int", "Bool"], command=self.change_type
        )
        self.type_menu.grid(row=0, column=0, padx=(10,5), pady=(5,10), sticky="ew")
        self.type_menu.set("Float")

        self.entry_message_box = ctk.CTkEntry(self, placeholder_text="OSC Address")
        self.entry_message_box.grid(row=0, column=1, columnspan=2, padx=(5,10), pady=(5,10), sticky="nsew")
        self.entry_message_box.insert(0,"/avatar/parameters/null")

    # 创建端口 + 最小最大输入框
    def create_range_inputs(self):
        # OSC端口输入
        self.port_entry = ctk.CTkEntry(self, placeholder_text="Port")
        self.port_entry.grid(row=2, column=0, padx=(10,5), pady=(5,10), sticky="ew")
        self.port_entry.insert(0,"9000")

        # 最小值输入
        self.min_entry = ctk.CTkEntry(self, placeholder_text="Min")
        self.min_entry.grid(row=2, column=1, padx=(5,5), pady=(5,10), sticky="ew")
        self.min_entry.insert(0,"-1")
        self.min_entry.bind("<Return>", self.update_slider_range)
        self.min_entry.bind("<FocusOut>", self.update_slider_range)

        # 最大值输入
        self.max_entry = ctk.CTkEntry(self, placeholder_text="Max")
        self.max_entry.grid(row=2, column=2, padx=(5,10), pady=(5,10), sticky="ew")
        self.max_entry.insert(0,"1")
        self.max_entry.bind("<Return>", self.update_slider_range)
        self.max_entry.bind("<FocusOut>", self.update_slider_range)

    # 创建滑条
    def create_slider(self):
        min_val, max_val = self.get_range()
        self.slider = ctk.CTkSlider(
            self, from_=min_val, to=max_val, command=self.slider_event,
            width=400, height=20
        )
        self.slider.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")
        self.slider.set((min_val+max_val)/2)
        self.rounded_value = self.slider.get()
        self.update_range_inputs_visibility()

    # 获取最小最大值
    def get_range(self):
        try:
            min_val = float(self.min_entry.get())
            max_val = float(self.max_entry.get())
            if min_val > max_val:
                min_val, max_val = max_val, min_val
        except:
            min_val, max_val = 0.0, 1.0
        return min_val, max_val

    # 更新滑条范围
    def update_slider_range(self, event=None):
        min_val, max_val = self.get_range()
        self.slider.configure(from_=min_val, to=max_val)
        value = self.rounded_value
        if value < min_val: value = min_val
        if value > max_val: value = max_val
        self.slider.set(value)
        self.slider_event(value)

    # 获取OSC端口
    def get_osc_port(self):
        try:
            port = int(self.port_entry.get())
            if port < 1 or port > 65535:
                port = 9000
        except:
            port = 9000
        return port

    # 滑条事件
    def slider_event(self, value):
        if self.value_type == "Int":
            self.rounded_value = int(round(value))
            self.slider.set(self.rounded_value)
        elif self.value_type == "Bool":
            if value < 0.5:
                self.rounded_value = False
                self.slider.set(0)
            else:
                self.rounded_value = True
                self.slider.set(1)
        else:  # Float
            self.rounded_value = round(value, 3)
        self.send_osc_msg()

    # 发送 OSC
    def send_osc_msg(self):
        address = self.entry_message_box.get().strip()
        port = self.get_osc_port()
        print(f"{address}: {self.rounded_value}")
        self.title(f"OSC_address_test - [{self.rounded_value}]")
        osc_client = udp_client.SimpleUDPClient("127.0.0.1", port)
        osc_client.send_message(address, self.rounded_value)

    # 切换类型
    def change_type(self, choice):
        self.value_type = choice
        # 切换类型时自动更新范围
        if choice == "Float":
            self.min_entry.delete(0,"end")
            self.min_entry.insert(0,"-1")
            self.max_entry.delete(0,"end")
            self.max_entry.insert(0,"1")
        elif choice == "Int":
            self.min_entry.delete(0,"end")
            self.min_entry.insert(0,"0")
            self.max_entry.delete(0,"end")
            self.max_entry.insert(0,"255")
        elif choice == "Bool":
            self.min_entry.delete(0,"end")
            self.min_entry.insert(0,"0")
            self.max_entry.delete(0,"end")
            self.max_entry.insert(0,"1")
        self.update_slider_range()
        self.update_range_inputs_visibility()

    # 更新输入框状态（Bool 禁用）
    def update_range_inputs_visibility(self):
        if self.value_type=="Bool":
            self.min_entry.configure(state="disabled")
            self.max_entry.configure(state="disabled")
        else:
            self.min_entry.configure(state="normal")
            self.max_entry.configure(state="normal")


    # 关闭
    def closing(self):
        self.destroy()


# Main GUI
class App(customtkinter.CTk):
    # 初始属性
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.iconbitmap(os.path.join(os.path.dirname(__file__), "app.ico"))
        self.title("OSC_Tool")
        self.geometry(f"{256}x{180}")
        self.minsize(256, 180)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.attributes("-topmost", True)
        self.wm_attributes("-alpha", 90/100)

        self.midi_get = None
        self.midi_device = None
        self.osc_dispatcher = None
        self.osc_server_thread = None
        self.server_running = False
        self.dc_webhook_TG = False
        self.now_title = None
        self.osc_lock = False
        self.log_monitor = False

        self.static_title = "OSC_Tool"

        self.create_textbox_message_log()
        self.create_entry_message_box()
        #self.start_send_osc_lock()
        threading.Thread(target=self.send_chatbox_state, daemon=True).start()







        self.log_message("v1.35 - by - YimuQr", level="info")       ##################################################################################################







    # log GUI
    def create_textbox_message_log(self):
        self.textbox_message_log = customtkinter.CTkTextbox(self)
        self.textbox_message_log.grid(row=0, column=1, padx=10, pady=(10, 5), sticky="nsew")
        self.textbox_message_log.configure(state='disabled')


    # 输入框 GUI
    def create_entry_message_box(self):
        self.entry_message_box = customtkinter.CTkEntry(self, placeholder_text="message")
        self.entry_message_box.grid(row=1, column=1, columnspan=2, padx=10, pady=(5, 10), sticky="nsew")
        self.entry_message_box.bind("<Return>", self.entry_message_box_press_key_enter)


    # 发送 log
    def log_message(self, message, level):
        current_time = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{current_time}] [{level}] {message}\n"
        self.textbox_message_log.configure(state='normal')
        self.textbox_message_log.insert("0.0", log_entry)
        self.textbox_message_log.see(0.0)
        self.textbox_message_log.configure(state='disabled')


    # OSC 扫描 debug
    def handle_osc_signal(self, address, args):
        argss = round(args, 3)
        print(f"{address} = {argss}")
        self.log_message(f"{address} = {argss}", level="OSC")


    # 启动 OSC 扫描
    def start_osc_server(self, osc_port):
            osc_port = int(osc_port)
            osc_dispatcher = dispatcher.Dispatcher()
            osc_dispatcher.map('*', self.handle_osc_signal)
            osc_server_thread = osc_server.ThreadingOSCUDPServer(('127.0.0.1', osc_port), osc_dispatcher)
            self.osc_server_thread = osc_server_thread
            server_thread = threading.Thread(target=osc_server_thread.serve_forever)
            server_thread.start()
            self.geometry(f"{400}x{500}")
            threading.Thread(target=self.osc_server_icon, daemon=True).start()
            self.log_message("OSC server listening !", level="OSC")
            print("OSC server listening on 127.0.0.1:9001")


    # 关闭 OSC 扫描
    def shutdown_osc_server(self):
        if self.osc_server_thread is not None:
            self.osc_server_thread.shutdown()
            self.osc_server_thread = None
            self.geometry(f"{255}x{180}")
            self.log_message("OSC server shutdown !", level="OSC")
            print("OSC server shutdown")
        else:
            self.log_message("None OSC server !", level="OSC")



    # 发送 chatbox osc
    def send_osc_message(self, chat_message):
        message = osc_message_builder.OscMessageBuilder(address="/chatbox/input")
        threading.Thread(target=self.msg_icon, daemon=True).start()
        message.add_arg(chat_message)
        message.add_arg(True)
        message.add_arg(True)
        message = message.build()
        osc_client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
        osc_client.send(message)
        osc_client.send_message("/chatbox/typing", False)
        threading.Thread(target=self.send_osc_message_status, daemon=True).start()


    # 发送 chatbox osc 状态
    def send_osc_message_status(self):
        osc_client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
        osc_client.send_message("/avatar/parameters/Message_Box", True)
        time.sleep(0.5)
        osc_client.send_message("/avatar/parameters/Message_Box", False)

    # 发送 chatbox 输入状态
    def send_chatbox_state(self):
        last_text = None
        last_typing_state = None
        while True:
            try:
                text = self.entry_message_box.get().strip()
                osc_client = udp_client.SimpleUDPClient("127.0.0.1", 9000)

                if text != last_text and text != "":
                    # 输入内容有变化而且不为空 → 每次变化都发 True
                    osc_client.send_message("/chatbox/typing", True)
                    last_typing_state = True

                elif text == "" and last_typing_state != False:
                    # 删除到空 → 只发一次 False
                    osc_client.send_message("/chatbox/typing", False)
                    last_typing_state = False

                last_text = text

            except Exception as e:
                break

            time.sleep(0.25)



    # 加载创建 env
    def load_keys_from_env(self):
        user_profile = os.getenv("USERPROFILE")
        if not user_profile:
            self.log_message("Unable to get USERPROFILE environment variable!", level="error")
            return

        env_dir = os.path.join(user_profile, "AppData", "LocalLow", "VRChat", "VRChat")
        if not os.path.exists(env_dir):
            os.makedirs(env_dir)

        env_path = os.path.join(env_dir, "keys.env")

        # 如果文件不存在，创建默认的
        if not os.path.exists(env_path):
            with open(env_path, "w", encoding="utf-8") as f:
                f.write("KEY_P_1=100\n")
                f.write("KEY_P_2=200\n")
                f.write("KEY_P_3=255\n")
            self.log_message("keys.env created !", level="info")

        # 读取 env 文件
        keys = {}
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    keys[k.strip()] = v.strip()

        # 赋值到类属性（读取不到就用默认）
        self.key_P_1 = int(keys.get("KEY_P_1", 255))
        self.key_P_2 = int(keys.get("KEY_P_2", 255))
        self.key_P_3 = int(keys.get("KEY_P_3", 255))

        self.log_message("Keys loaded !", level="info")

    # 发送 osc_lock 密钥
    def start_send_osc_lock(self):
        if self.osc_lock:
            self.osc_lock = False
            self.log_message("Key sending stopped !", level="info")
        else:
            # 每次开启时都重新读取 env
            self.load_keys_from_env()
            self.osc_lock = True
            threading.Thread(target=self.send_osc_lock, daemon=True).start()

    def send_osc_lock(self):
        while True:
            if self.osc_lock is False:
                self.title(f"{self.static_title}")
                break
            else:
                self.title(f"{self.static_title}  - 🔑")
                osc_client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
                osc_client.send_message("/avatar/parameters/key/P_1", self.key_P_1)
                osc_client.send_message("/avatar/parameters/key/P_2", self.key_P_2)
                osc_client.send_message("/avatar/parameters/key/P_3", self.key_P_3)
                time.sleep(0.5)
                osc_client.send_message("/avatar/parameters/key/P_1", 0)
                osc_client.send_message("/avatar/parameters/key/P_2", 0)
                osc_client.send_message("/avatar/parameters/key/P_3", 0)
                time.sleep(2.0)


    # MIDI (如果琴键按下)
    def send_midi_osc_on(self, note):
        osc_client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
        address = f"/avatar/parameters/piano/key_{note}"
        osc_client.send_message(address, True)



    # MIDI (如果琴键松开)
    def send_midi_osc_off(self, note):
        osc_client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
        address = f"/avatar/parameters/piano/key_{note}"
        osc_client.send_message(address, False)



    # MIDI (其他控件[所有其他控件的value])
    def send_midi_control_osc(self, value):
        osc_client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
        address = f"/avatar/parameters/ys"
        osc_value = value / 10
        osc_client.send_message(address, osc_value)



    # MIDI 琴键 Debug
    def get_note_address(self, note):
        return f"/avatar/parameters/piano/key_{note}"


    # MIDI 其他控件 Debug
    def get_control_address(self, value):
        return f"/avatar/parameters/piano/control_{value}"


    # MIDI 获取midi日志和输出Debug
    def process_messages(self):
        while True:
            if self.midi_device is None:
                break
            for msg in self.midi_device.iter_pending():
                print(msg)
                if msg.type == "note_off":
                    self.send_midi_osc_off(msg.note)
                elif msg.type == "note_on":
                    self.send_midi_osc_on(msg.note)
                elif msg.type == "control_change":
                    self.send_midi_control_osc(msg.value)
            time.sleep(0.005)


    # MIDI 断开连接
    def disconnect_midi_device(self):
        if  self.midi_device:
            self.midi_device.close()
            self.midi_device = None
        self.log_message("MIDI - disconnected !", level="midi")



    # MIDI 连接
    def connect_to_midi_device(self, midi_device_name):
        self.midi_device = mido.open_input(midi_device_name)
        self.log_message(f"MIDI - connected !", level="midi")
        #self.geometry(f"{400}x{500}")
        threading.Thread(target=self.process_messages, daemon=True).start()
        threading.Thread(target=self.midi_icon, daemon=True).start()


    #Discord Webhook test 
    def dc_webhook_message_send(self,chat_message):
        webhook_url = "https://discord.com/api/webhooks/0"
        message = chat_message
        payload = {
            "content": message,
            "username": "OSC_Tool",  
            "avatar_url": "https://i.imgur.com/SwpBrbl.png"
        }
        requests.post(webhook_url, json=payload)

    def dc_webhook_message_send_start(self,chat_message):
        if self.dc_webhook_TG:
            threading.Thread(target=self.dc_webhook_message_send, args=(chat_message), daemon=True).start()
        else:
            pass



    # MIDI 扫描midi设备
    def scan_midi(self):
        mido.get_input_names()
        self.midi_get = mido.get_input_names()
        if self.midi_get:
            self.log_message(f"Found {self.midi_get}", level="midi")
        else:
            self.log_message("None - MIDI - device !", level="midi")




    # VRC LOG

    # 启动日志监控
    def start_log_monitor(self):
        if self.log_monitor:
            self.log_monitor = False
        else:
            self.geometry(f"{800}x{400}")
            self.log_monitor = True
            threading.Thread(target=self.monitor, daemon=True).start()


    # 日志监控核心逻辑
    def monitor(self):
        user_profile = os.getenv("USERPROFILE")
        if not user_profile:
            self.log_message("Unable to get USERPROFILE environment variable!", level="error")
            return
        log_folder = os.path.join(user_profile, "AppData", "LocalLow", "VRChat", "VRChat")
        if not os.path.exists(log_folder):
            self.log_message(f"The log directory does not exist:{log_folder}", level="error")
            return
        last_line = ""
        last_filename = ""
        while self.log_monitor:
            try:
                log_files = [
                    f for f in os.listdir(log_folder)
                    if f.startswith("output_log_") and f.endswith(".txt")
                ]
                if not log_files:
                    time.sleep(1.0)
                    continue
                latest_file = max(
                    log_files,
                    key=lambda f: os.path.getmtime(os.path.join(log_folder, f))
                )
                latest_path = os.path.join(log_folder, latest_file)
                if latest_file != last_filename:
                    last_filename = latest_file
                    last_line = ""
                with open(latest_path, 'r', encoding='utf-8', errors='ignore') as f:
                    # 跳过上次读取的内容
                    if last_line:
                        for line in f:
                            if line.strip() == last_line:
                                break
                    # 逐行处理新增内容
                    for line in f:
                        stripped = line.strip()
                        if stripped:
                            self.log_message(stripped, level="log")
                            time.sleep(0.01)
                        last_line = stripped
            except Exception as e:
                self.log_message(f"Log reading error:{str(e)}", level="error")
            time.sleep(1.0)
        self.log_message("Log monitoring has stopped", level="info")




    # HELP
    def osc_tool_help(self):
        help_tx = """

> /help          --  Help

> /midi s       --  Scan MIDI devices
> /midi c       --  Connect first MIDI
> /midi c [  ]  --  Custom MIDI connection
> /midi d       --  Disconnect MIDI device

> /osc s        --  Scan port 9001 OSC
> /osc s [  ]   --  Custom OSC port scan
> /osc d        --  Shutdown OSC server
> /osc t         --  OSC address test

> /log         --  log output mode

> /key         --  Key sending mode

> /open vrc      -- Open VRChat
> /kill vrc      --  Taskkill VRChat

> /exit          --    Exit
"""
        self.log_message(help_tx, level="help")
        self.geometry(f"{270}x{450}")



    # 输入检测
    def entry_message_box_press_key_enter(self, event):
        chat_message = self.entry_message_box.get()
        if chat_message:
            if chat_message == "/exit":
                self.ost_exit()

            elif chat_message.startswith("/midi c"):
                if len(chat_message) > 8:   #检查长度
                    midi_device_name = chat_message[8:]     #获取设备名称
                    self.connect_to_midi_device(midi_device_name)   #连接到输入的设备
                else:
                    input_names = mido.get_input_names()    #获取查询到的设备名称
                    if input_names:
                        midi_device_name = input_names[0]
                        self.connect_to_midi_device(midi_device_name)   #连接到获取到的第一个设备
                    else:
                        self.log_message("None - MIDI - device !", level="midi")

            elif chat_message == "/midi s":
                self.scan_midi()

            elif chat_message == "/help":
                self.osc_tool_help()

            elif chat_message == "/midi d":
                self.disconnect_midi_device()

            elif chat_message.startswith("/osc s"):
                if len(chat_message) > 7:   #检查长度
                    osc_port = chat_message[7:]  # 获取端口号
                else:
                    osc_port = '9001'   #默认端口
                self.start_osc_server(osc_port)

            elif chat_message == "/osc d":
                self.shutdown_osc_server()

            elif chat_message == "/osc t":
                OSC_Address_Test_ToplevelWindow()

            elif chat_message == "/kill vrc":
                self.takkill_vrchat()

            elif chat_message == "/open vrc":
                self.open_vrchat() 

            elif chat_message == "/log":
                self.start_log_monitor()

            elif chat_message == "/key":
                self.start_send_osc_lock()

            #elif chat_message == "/oscm":
            #    OSC_Maps_ToplevelWindow()

            elif chat_message.startswith("/wbk on"):
                self.dc_webhook_TG = True
                self.log_message("Webhook - log - ON !", level="info")

            elif chat_message.startswith("/wbk off"):
                self.dc_webhook_TG = False
                self.log_message("Webhook - log - OFF !", level="info")

            else:
                #self.dc_webhook_message_send_start(chat_message)
                self.send_osc_message(chat_message)
                self.log_message(chat_message, level="send")

            self.entry_message_box.delete(0, customtkinter.END)



    # 标题栏状态显示
    def midi_icon(self):
        while True:
            if self.midi_device is None:
                self.title(f"{self.static_title}")
                break
            else:
                self.title(f"{self.static_title}  - 🎹")
                time.sleep(2.0)


    # 标题栏状态显示
    def osc_server_icon(self):
        while True:
            if self.osc_server_thread is None:
                self.title(f"{self.static_title}")
                break
            else:
                self.title(f"{self.static_title}  - 📡")
                time.sleep(2.0)


    # 标题栏状态显示
    def msg_icon(self):
        self.now_title = self.title()
        self.title(f"{self.static_title} -✉️")
        time.sleep(0.2)
        self.title(f"{self.static_title} -  ✉️")
        time.sleep(0.2)
        self.title(f"{self.static_title} -    ✉️")
        time.sleep(0.2)
        self.title(f"{self.now_title}")



    # 关闭进程VRCHat
    def takkill_vrchat(self):
        os.system("taskkill /F /IM VRChat.exe")

    # 开启进程 VRChat           
    def open_vrchat(self):
        os.system("start steam://rungameid/438100")

    def ost_exit(self):
        sys.exit()


if __name__ == "__main__":
    app = App()
    app.mainloop()
