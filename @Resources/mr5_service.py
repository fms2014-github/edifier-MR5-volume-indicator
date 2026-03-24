import asyncio
import threading
import subprocess
import tkinter as tk
from bleak import BleakClient
import os
import json

# ==========================================
# 사용자 설정 값
# ==========================================
DEVICE_MAC_ADDRESS = "C8:24:70:45:6E:3C"  # MR5의 블루투스 MAC 주소
VOLUME_CHARACTERISTIC_UUID = "48090001-1a48-11e9-ab14-d663bd873d93"  # 볼륨 데이터가 들어오는 UUID
RAINMETER_CONFIG = "EdifierMR5"

# 파일 경로 설정 (킬 스위치 및 설정 저장 파일)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KILL_SWITCH_FILE = os.path.join(BASE_DIR, "stop.txt")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")  # 💡 설정 파일 경로 추가

osd_app = None


# ==========================================
# 1. 데이터 저장 및 불러오기 함수 (새로 추가됨)
# ==========================================
def save_last_volume(volume_text):
    """볼륨 값을 settings.json 파일에 저장합니다."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_volume": volume_text}, f)
    except Exception as e:
        print(f"저장 오류: {e}")


def load_last_volume():
    """settings.json 파일에서 마지막 볼륨 값을 불러옵니다."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("last_volume", "--")
        except Exception:
            return "--"
    return "--"


# ==========================================
# 2. 레인미터 통신 및 OSD 클래스
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


# ==========================================
# 3. 블루투스 데이터 처리 및 백그라운드 작업
# ==========================================
def volume_notification_handler(sender, data):
    decimal_values = list(data)
    try:
        if len(decimal_values) >= 7 and decimal_values[0] == 187:
            volume_level = decimal_values[6]
            if 0 <= volume_level <= 30:
                display_text = "MAX" if volume_level == 30 else str(volume_level)

                # 💡 볼륨이 변경될 때마다 파일에 저장합니다.
                save_last_volume(display_text)

                if osd_app:
                    osd_app.root.after(0, osd_app.update_volume, display_text)
                send_to_rainmeter("MR5Volume", display_text)
    except Exception:
        pass


async def ble_task():
    # 💡 프로그램이 시작될 때 저장된 마지막 볼륨을 불러와서 레인미터에 바로 띄워줍니다.
    last_vol = load_last_volume()
    send_to_rainmeter("MR5Volume", last_vol)

    send_to_rainmeter("MR5Status", "연결 시도 중...")
    try:
        async with BleakClient(DEVICE_MAC_ADDRESS) as client:
            send_to_rainmeter("MR5Status", "연결됨")
            await client.start_notify(VOLUME_CHARACTERISTIC_UUID, volume_notification_handler)
            while True:
                await asyncio.sleep(1)
    except Exception:
        send_to_rainmeter("MR5Status", "연결 끊김 / 대기 중")


def start_ble_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ble_task())


# ==========================================
# 4. 메인 실행부
# ==========================================
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