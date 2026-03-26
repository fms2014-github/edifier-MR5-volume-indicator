# 🔊 Edifier MR5 BLE Volume OSD & Rainmeter Widget

데스크탑 환경에서 **Edifier MR5** 스피커를 3.5mm(AUX) 단자로 사용할 때, 기기의 볼륨 노브를 돌리면 화면에 즉각적으로 볼륨 정보가 표시되도록 만든 파이썬(Python) 및 레인미터(Rainmeter) 연동 프로젝트입니다.

스마트폰 전용 앱을 켜지 않아도 PC 화면에서 스피커의 현재 볼륨과 연결 상태를 직관적으로 확인할 수 있습니다!

## ✨ 주요 기능 (Features)
* **실시간 OSD 오버레이:** 볼륨 조절 시 윈도우 중앙 하단에 부드럽고 투명한 커스텀 OSD 창이 즉각적으로 나타났다 사라집니다.
* **레인미터(Rainmeter) 연동:** 바탕화면의 레인미터 스킨에 현재 볼륨과 블루투스 연결 상태, 에러 메시지 등이 실시간으로 동기화됩니다.
* **설정 저장 (Auto-save):** 마지막으로 설정한 볼륨값을 기억하여 프로그램을 다시 켜도 이전 볼륨을 화면에 띄워줍니다.
* **독립적인 설정 관리 (`config.ini`):** 소스 코드를 직접 수정할 필요 없이 설정 파일에 MAC 주소와 UUID만 적으면 누구나 사용할 수 있습니다.
* **완벽한 프로세스 제어 (Kill Switch):** 레인미터의 [해제] 버튼을 누르면 좀비 프로세스 없이 깔끔하게 모든 백그라운드 작업이 종료됩니다.

## 🛠️ 요구 사항 (Prerequisites)
* **OS:** Windows 10 또는 Windows 11
* **Hardware:** Bluetooth 통신이 가능한 데스크탑 또는 노트북 (동글 가능)
* **Software:** * Python 3.10 이상
  * [Rainmeter](https://www.rainmeter.net/) 최신 버전

## 📦 설치 및 설정 (Installation & Setup)

### 1. 파이썬 라이브러리 설치
명령 프롬프트(cmd) 또는 PowerShell을 열고 필요한 패키지를 설치합니다.
```bash
pip install bleak
```
(참고: tkinter, asyncio, json, configparser 등은 파이썬 기본 내장 라이브러리입니다.)

### 2. MAC 주소 및 UUID 찾기
에디파이어 MR5의 BLE(Bluetooth Low Energy) 통신용 MAC 주소와 볼륨 Notify UUID를 알아야 합니다.

스마트폰에 nRF Connect for Mobile 앱을 설치하여 기기를 스캔하고 볼륨 Characteristic UUID를 확인하세요.

### 3. 레인미터 스킨 설치
1. 내 문서\Rainmeter\Skins 경로에 EdifierMR5 라는 폴더를 생성합니다.

2. 그 안에 @Resources 폴더를 하나 더 생성합니다.

3. 이 레포지토리의 파일들을 다음과 같이 배치합니다:
   * `MR5_Overlay.ini` ➡️ `EdifierMR5` 폴더 안
   * `mr5_service.py` ➡️ `@Resources` 폴더 안
   * `config.ini` ➡️ `@Resources` 폴더 안

### 4. Config.ini 설정
`@Resources/config.ini` 파일을 열고 본인 기기의 정보로 수정합니다.

```
Ini, TOML
[Device]
MAC_ADDRESS = A1:B2:C3:D4:E5:F6  # 본인의 MR5 MAC 주소로 변경
VOLUME_UUID = 0000xxxx-0000-1000-8000-00805f9b34fb # 본인의 볼륨 UUID로 변경
```
### 🚀 사용 방법 (Usage)
1. 바탕화면 우측 하단의 레인미터 아이콘을 우클릭하고 **전체 새로고침(Refresh all)** 을 누릅니다.

2. 레인미터 관리자에서 `EdifierMR5` 스킨을 찾아 **불러오기(Load)** 합니다.

3. 바탕화면에 나타난 스킨에서 **[ 연결 ]** 버튼을 클릭합니다.

4. 상태가 `연결됨`으로 변경되면, MR5 스피커의 볼륨 노브를 돌려보세요!

5. 사용을 중지하려면 **[ 해제 ]** 버튼을 누르면 완벽하게 종료됩니다.

### 🚨 문제 해결 (Troubleshooting)
* 오류: config.ini 파일이 없습니다 / 양식이 잘못되었습니다: @Resources 폴더 안에 config.ini 파일이 올바르게 존재하는지, 주소 형식이 맞는지 확인하세요.

* 오류: 기기를 찾을 수 없음: 스피커의 전원이 켜져 있는지, PC와 너무 멀리 떨어져 있지 않은지 확인하세요.

* 볼륨이 튀거나 이상한 값이 나옴: 코드는 데이터 패킷의 첫 번째 바이트가 187 (0xBB)인 경우만 볼륨으로 인식하도록 필터링되어 있습니다. 펌웨어 버전에 따라 패킷 구조가 다를 수 있으니 파이썬 코드의 volume_notification_handler 부분을 디버깅해 보세요.

### 📝 라이선스
MIT License