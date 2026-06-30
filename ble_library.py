# ble_library.py
# ESP32 MicroPython용 BLE UART(Nordic UART Service) 주변장치
#   BLESimplePeripheral(ble, name)
#     .on_write(callback)   : 데이터 수신 시 callback(문자열) 호출
#     .send(data)           : 연결된 기기로 송신 (str/bytes)
#     .is_connected()       : 연결 여부
import bluetooth
import struct
from micropython import const

# ---- BLE 이벤트 ----
_IRQ_CENTRAL_CONNECT    = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE        = const(3)

# ---- 캐릭터리스틱 플래그 ----
_FLAG_READ              = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE             = const(0x0008)
_FLAG_NOTIFY            = const(0x0010)

# ---- Nordic UART Service UUID ----
_UART_UUID = bluetooth.UUID('6e400001-b5a3-f393-e0a9-e50e24dcca9e')
# TX: 보드 -> 상대 (Notify)
_UART_TX = (bluetooth.UUID('6e400003-b5a3-f393-e0a9-e50e24dcca9e'),
            _FLAG_READ | _FLAG_NOTIFY,)
# RX: 상대 -> 보드 (Write)
_UART_RX = (bluetooth.UUID('6e400002-b5a3-f393-e0a9-e50e24dcca9e'),
            _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,)
_UART_SERVICE = (_UART_UUID, (_UART_TX, _UART_RX),)

# ---- 광고(advertising) 페이로드 타입 ----
_ADV_TYPE_FLAGS            = const(0x01)
_ADV_TYPE_NAME             = const(0x09)
_ADV_TYPE_UUID128_COMPLETE = const(0x07)


def advertising_payload(name=None, services=None):
    payload = bytearray()

    def _append(adv_type, value):
        payload.extend(struct.pack("BB", len(value) + 1, adv_type))
        payload.extend(value)

    if name:
        _append(_ADV_TYPE_FLAGS, struct.pack("B", 0x06))   # LE General + BR/EDR 미지원
        _append(_ADV_TYPE_NAME, name.encode())
    if services:
        for uuid in services:
            b = bytes(uuid)
            if len(b) == 16:
                _append(_ADV_TYPE_UUID128_COMPLETE, b)
    return payload


class BLESimplePeripheral:
    def __init__(self, ble, name="ESP-000"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._tx_handle, self._rx_handle),) = \
            self._ble.gatts_register_services((_UART_SERVICE,))
        self._connections = set()
        self._write_callback = None
        # 이름은 광고에, 서비스 UUID는 스캔응답에 (31바이트 초과 방지)
        self._adv_payload  = advertising_payload(name=name)
        self._resp_payload = advertising_payload(services=[_UART_UUID])
        self._advertise()

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)
            self._advertise()                      # 끊기면 다시 광고
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            value = self._ble.gatts_read(value_handle)
            if value_handle == self._rx_handle and self._write_callback:
                try:
                    value = value.decode()         # bytes -> str
                except Exception:
                    pass
                self._write_callback(value)

    def send(self, data):
        if isinstance(data, str):
            data = data.encode()
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._tx_handle, data)

    def is_connected(self):
        return len(self._connections) > 0

    def on_write(self, callback):
        self._write_callback = callback

    def _advertise(self, interval_us=500000):
        self._ble.gap_advertise(interval_us,
                                adv_data=self._adv_payload,
                                resp_data=self._resp_payload)
