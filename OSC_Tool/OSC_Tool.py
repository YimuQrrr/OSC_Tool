import os
import re
import sys
import time
import mido
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
    # 初始属性
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.iconbitmap(os.path.join(os.path.dirname(__file__), "app.ico"))
        self.protocol("WM_DELETE_WINDOW", self.closing)
        self.title("OSC_Address_Test")
        self.geometry(f"{350}x{85}")
        self.minsize(350, 85)
        self.maxsize(350, 85)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.attributes("-topmost", True)
        self.wm_attributes("-alpha", 90/100)

        self.create_entry_message_box()
        self.slider_main()



    # 获取滑条数值
    def slider_event(self, value):
        self.rounded_value = round(value, 3)
        self.send_osc_msg()
        self.slider.configure(from_=float(self.entry_message_box.get().split("[")[1].split(",")[0]),
                                to=float(self.entry_message_box.get().split(",")[1].split("]")[0]))


    # osc发送
    def send_osc_msg(self):
        osc_client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
        address = re.sub(r'\[.*?\]', '', self.entry_message_box.get())
        address = address.strip()
        print(f"{address}:{self.rounded_value}")
        self.title(f"OSC_address_test - [{self.rounded_value}]")
        osc_client.send_message(address, self.rounded_value)


    # 地址输入
    def create_entry_message_box(self):
        self.entry_message_box = customtkinter.CTkEntry(self, placeholder_text="OSCaddress")
        self.entry_message_box.grid(row=0, column=0, columnspan=2, padx=10, pady=(5, 10), sticky="nsew")
        self.entry_message_box.insert(0, "[-1,1]/avatar/parameters/null")


    # 滑条
    def slider_main(self):
        self.slider = customtkinter.CTkSlider(self, from_=float(self.entry_message_box.get().split("[")[1].split(",")[0]), 
                                                    to=float(self.entry_message_box.get().split(",")[1].split("]")[0]),
                                                    command=self.slider_event)
        self.slider.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")


    # 关闭osc地址测试GUI
    def closing(self):
        self.destroy()



# Main GUI
class App(customtkinter.CTk):
    # 初始属性
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.iconbitmap(os.path.join(os.path.dirname(__file__), "app.ico"))
        self.title("OSC_Tool")
        self.geometry(f"{255}x{180}")
        self.minsize(255, 180)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.attributes("-topmost", True)
        self.wm_attributes("-alpha", 90/100)

        self.create_textbox_message_log()
        self.create_entry_message_box()

        self.log_message("v1.05 - by - YimuQr", level="info")       ##################################################################################################

        self.midi_get = None
        self.osc_dispatcher = None
        self.osc_server_thread = None
        self.server_running = False
        self.dc_webhook_TG = False


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
    def start_osc_server(self):
            osc_dispatcher = dispatcher.Dispatcher()
            osc_dispatcher.map('*', self.handle_osc_signal)
            osc_server_thread = osc_server.ThreadingOSCUDPServer(('127.0.0.1', 9001), osc_dispatcher)
            self.osc_server_thread = osc_server_thread
            server_thread = threading.Thread(target=osc_server_thread.serve_forever)
            server_thread.start()
            self.geometry(f"{400}x{500}")
            threading.Thread(target=self.osc_server_icon).start()
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
        threading.Thread(target=self.msg_icon).start()
        message.add_arg(chat_message)
        message.add_arg(True)
        message.add_arg(True)
        message = message.build()
        osc_client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
        osc_client.send(message)


    # MIDI (如果琴键按下)
    def send_midi_osc_on(self, note):
        osc_client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
        address = f"/avatar/parameters/piano/key{note}"
        osc_client.send_message(address, True)


    # MIDI (如果琴键松开)
    def send_midi_osc_off(self, note):
        osc_client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
        address = f"/avatar/parameters/piano/key{note}"
        osc_client.send_message(address, False)


    # MIDI (其他控件[所有其他控件的value])
    def send_midi_control_osc(self, value):
        osc_client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
        address = f"/avatar/parameters/ys"
        osc_value = value / 10
        osc_client.send_message(address, osc_value)


    # MIDI 琴键 Debug
    def get_note_address(self, note):
        return f"/avatar/parameters/piano/key{note}"


    # MIDI 其他控件 Debug
    def get_control_address(self, value):
        return f"/avatar/parameters/piano/control{value}"


    # MIDI 获取midi日志和输出Debug
    def process_messages(self):
        while True:
            if self.midi_device is None:
                break
            for msg in self.midi_device.iter_pending():
                if msg.type == "note_off":
                    print(f"{self.get_note_address(msg.note)}: 0")
                    self.send_midi_osc_off(msg.note)
                elif msg.type == "note_on":
                    print(f"{self.get_note_address(msg.note)}: 1")
                    self.send_midi_osc_on(msg.note)
                elif msg.type == "control_change":
                    print(f"{self.get_control_address(msg.value)}")
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
        threading.Thread(target=self.process_messages).start()
        threading.Thread(target=self.midi_icon).start()


    #Discord Webhook test 
    def dc_webhook_message_send(self,chat_message):
        webhook_url = "https://discord.com/api/webhooks/1194649007641858048/OUfWDluk93KE-9e3NHQbDk01o9t0eWjVuG5tiuTsgPgpJ14Wncets2fV4Y8-NSFMjG2g"
        message = chat_message
        payload = {
            "content": message,
            "username": "OSC_Tool",  
            "avatar_url": "https://i.imgur.com/SwpBrbl.png"
        }
        requests.post(webhook_url, json=payload)

    def dc_webhook_message_send_start(self,chat_message):
        if self.dc_webhook_TG:
            threading.Thread(target=self.dc_webhook_message_send, args=(chat_message,)).start()
        else:
            pass



    # MIDI 扫描midi设备
    def scan_midi(self):
        mido.get_input_names()
        self.midi_get = mido.get_input_names()
        if self.midi_get:
            self.log_message(self.midi_get, level="midi")
        else:
            self.log_message("None - MIDI - device !", level="midi")



    # HELP
    def osc_tool_help(self):
        help_tx = """
> /help          --  Help

> /midi s       --  Scan MIDI devices
> /midi c       --  Connect first MIDI
> /midi c [ ]   --  Custom MIDI connection
> /midi d       --  Disconnect MIDI device

> /osc s        --  Start OSC scan server
> /osc d        --  Shutdown OSC server
> /osc t         --  OSC address test

> /open vrc  -- Open VRChat
> /kill vrc      --  Taskkill VRChat

> /exit          --    Exit
"""
        self.log_message(help_tx, level="help")
        self.geometry(f"{270}x{325}")


    # 输入检测
    def entry_message_box_press_key_enter(self, event):
        chat_message = self.entry_message_box.get()
        if chat_message:
            if chat_message == "/exit":
                self.ost_exit()

            elif chat_message =="/midi c":
                input_names = mido.get_input_names()
                if input_names:
                    midi_device_name = input_names[0]
                    self.connect_to_midi_device(midi_device_name)
                else:
                    self.log_message("None - MIDI - device !", level="midi")

            elif chat_message.startswith("/midi c "):
                midi_device_name = chat_message[8:]
                self.connect_to_midi_device(midi_device_name)

            elif chat_message == "/midi s":
                self.scan_midi()

            elif chat_message == "/help":
                self.osc_tool_help()

            elif chat_message == "/midi d":
                self.disconnect_midi_device()

            elif chat_message == "/osc s":
                self.start_osc_server()

            elif chat_message == "/osc d":
                self.shutdown_osc_server()

            elif chat_message == "/osc t":
                OSC_Address_Test_ToplevelWindow()

            elif chat_message == "/kill vrc":
                self.takkill_vrchat()

            elif chat_message == "/open vrc":
                self.open_vrchat() 

            #elif chat_message == "/oscm":
            #    OSC_Maps_ToplevelWindow()

            elif chat_message.startswith("/wbk on"):
                self.dc_webhook_TG = True
                self.log_message("Webhook - log - ON !", level="info")

            elif chat_message.startswith("/wbk off"):
                self.dc_webhook_TG = False
                self.log_message("Webhook - log - OFF !", level="info")

            else:
                self.dc_webhook_message_send_start(chat_message)
                self.send_osc_message(chat_message)
                self.log_message(chat_message, level="send")

            self.entry_message_box.delete(0, customtkinter.END)


    # 标题栏状态显示
    def midi_icon(self):
        while True:
            if self.midi_device is None:
                self.title("OSC_Tool")
                break
            else:
                self.title("OSC_Tool  -  🎹")
                time.sleep(1.0)
                self.title("OSC_Tool  -  🎵")
                time.sleep(1.0)

    # 标题栏状态显示
    def osc_server_icon(self):
        while True:
            if self.osc_server_thread is None:
                self.title("OSC_Tool")
                break
            else:
                self.title("OSC_Tool  -  📡")
                time.sleep(1.0)
                self.title("OSC_Tool  -  🔗")
                time.sleep(1.0)

    # 标题栏状态显示
    def msg_icon(self):
        self.title("OSC_Tool  -✉️")
        time.sleep(0.3)
        self.title("OSC_Tool  - ✉️")
        time.sleep(0.3)
        self.title("OSC_Tool  -  ✉️")
        time.sleep(0.3)
        self.title("OSC_Tool")


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
