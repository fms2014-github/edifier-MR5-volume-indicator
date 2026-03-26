import asyncio
import threading
import subprocess
import tkinter as tk
from bleak import BleakClient
import os
import json
import configparser

# ==========================================
# 파일 경로 설정
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KILL_SWITCH_FILE = os.path.join(BASE_DIR, "stop.txt")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config.ini")

RAINMETER_CONFIG = "EdifierMR5"
osd_app = None


# ==========================================
# 레인미터 통신 및 설정 읽기
# ==========================================
def send_to_rainmeter(variable_name, value):
    try:
        CREATE_NO_WINDOW = 0x08000000
        subprocess.run(["C:\\Program Files\\Rainmeter\\Rainmeter.exe", "!SetVariable", variable_name, str(value),
                        RAINMETER_CONFIG], creationflags=CREATE_NO_WINDOW)
        subprocess.run(["C:\\Program Files\\Rainmeter\\Rainmeter.exe", "!Update", RAINMETER_CONFIG],
                       creationflags=CREATE_NO_WINDOW)
    except Exception:
        pass


def get_config():
    """INI 파일을 읽고, 문제가 있으면 구체적인 에러 메시지를 반환합니다."""
    config = configparser.ConfigParser()

    if not os.path.exists(CONFIG_FILE):
        return None, None, "오류: config.ini 파일이 없습니다"

    config.read(CONFIG_FILE, encoding='utf-8')
    try:
        mac = config['Device']['MAC_ADDRESS']
        uuid = config['Device']['VOLUME_UUID']

        if not mac or not uuid or mac == "XX:XX:XX:XX:XX:XX":
            return None, None, "오류: MAC 주소나 UUID가 비어있습니다"
        return mac, uuid, None
    except KeyError:
        return None, None, "오류: config.ini 양식이 잘못되었습니다"


# ==========================================
# 데이터 저장 및 불러오기
# ==========================================
def save_last_volume(volume_text):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_volume": volume_text}, f)
    except Exception:
        pass


def load_last_volume():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("last_volume", "--")
        except Exception:
            return "--"
    return "--"


# ==========================================
# OSD 클래스 및 블루투스 핸들러
# ==========================================
class VolumeOSD:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.85)
        self.root.configure(bg='#1c1c1c')

        window_width = 250
        window_height = 60
        x_pos = (self.root.winfo_screenwidth() // 2) - (window_width // 2)
        y_pos = self.root.winfo_screenheight() - 150
        self.root.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")

        self.label = tk.Label(self.root, text="볼륨: --", font=("맑은 고딕", 20, "bold"), bg="#1c1c1c", fg="#ffffff")
        self.label.pack(expand=True, fill="both")

        self.hide_timer = None
        self.root.withdraw()
        self.check_kill_switch()

    def check_kill_switch(self):
        if os.path.exists(KILL_SWITCH_FILE):
            self.root.quit()
            os._exit(0)
        self.root.after(1000, self.check_kill_switch)

    def update_volume(self, display_text):
        self.label.config(text=f"🔊 볼륨: {display_text}")
        self.root.deiconify()
        if self.hide_timer:
            self.root.after_cancel(self.hide_timer)
        self.hide_timer = self.root.after(1500, self.root.withdraw)

    def run(self):
        self.root.mainloop()


def volume_notification_handler(sender, data):
    decimal_values = list(data)
    try:
        if len(decimal_values) >= 7 and decimal_values[0] == 187:
            volume_level = decimal_values[6]
            if 0 <= volume_level <= 30:
                display_text = "MAX" if volume_level == 30 else str(volume_level)
                save_last_volume(display_text)
                if osd_app:
                    osd_app.root.after(0, osd_app.update_volume, display_text)
                send_to_rainmeter("MR5Volume", display_text)
    except Exception:
        pass


# ==========================================
# 핵심 실행 로직 (에러 핸들링 포함)
# ==========================================
async def ble_task():

    # 1. config.ini 설정 검사 (문제가 있으면 스킨에 에러 띄우고 종료)
    mac, uuid, error_msg = get_config()
    if error_msg:
        send_to_rainmeter("MR5Status", error_msg)
        os._exit(0)
        return

    # 2. 이전 볼륨 불러오기
    send_to_rainmeter("MR5Volume", load_last_volume())

    # 3. 블루투스 연결 시도
    send_to_rainmeter("MR5Status", "연결 시도 중...")
    try:
        async with BleakClient(mac) as client:
            send_to_rainmeter("MR5Status", "연결됨")
            await client.start_notify(uuid, volume_notification_handler)
            while True:
                await asyncio.sleep(1)
    except Exception as e:
        # 블루투스 오류 시 세부 원인을 분석하여 스킨에 표시
        error_str = str(e).lower()
        if "was not found" in error_str or "device not found" in error_str:
            send_to_rainmeter("MR5Status", "오류: 기기를 찾을 수 없음 (전원/페어링 확인)")
        else:
            send_to_rainmeter("MR5Status", "오류: 연결 끊김 / 실패")
        os._exit(0)

def start_ble_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ble_task())


if __name__ == "__main__":
    if os.path.exists(KILL_SWITCH_FILE):
        try:
            os.remove(KILL_SWITCH_FILE)
        except Exception:
            pass

    ble_thread = threading.Thread(target=start_ble_loop, daemon=True)
    ble_thread.start()

    osd_app = VolumeOSD()
    osd_app.run()