## 1. 위험 소리 감지 및 촉각/시각 알림 팔찌

import machine
import time

# 1. 핀 및 센서 설정
sound_sensor = machine.ADC(26)  # 아날로그 소리 센서
vibe_motor = machine.Pin(15, machine.Pin.OUT) # 진동 모터
led = machine.Pin(14, machine.Pin.OUT)        # LED

# MPU6050 I2C 설정
i2c = machine.I2C(0, sda=machine.Pin(4), scl=machine.Pin(5), freq=400000)
MPU6050_ADDR = 0x68
i2c.writeto_mem(MPU6050_ADDR, 0x6B, bytes([0])) # MPU6050 깨우기

def get_z_acceleration():
    """MPU6050에서 Z축 가속도 읽기 (낙상/충격 감지용)"""
    try:
        data = i2c.readfrom_mem(MPU6050_ADDR, 0x3F, 2)
        raw_z = (data[0] << 8) | data[1]
        if raw_z > 32767:
            raw_z -= 65536
        return abs(raw_z)
    except:
        return 0

# 2. 임계값(Threshold) 설정
SOUND_THRESHOLD = 35000   # 급격한 경적/알람 소리 기준 (0~65535 범위)
FALL_THRESHOLD = 25000    # Z축 가속도 급변(낙상) 기준

print("=== 위험 소리 감지 팔찌 가동 시작 ===")

while True:
    # 센서 값 수집
    sound_val = sound_sensor.read_u16()
    z_accel = get_z_acceleration()
    
    # [상태 1] 응급 상황: 위험 소리 + 사용자 낙상/충격 동시 감지
    if sound_val > SOUND_THRESHOLD and z_accel > FALL_THRESHOLD:
        print(f"[응급] 위험 소리({sound_val}) 및 충격({z_accel}) 동시 감지!")
        # 강력하고 긴 진동 + LED 점등
        led.value(1)
        vibe_motor.value(1)
        time.sleep(2.0)
        vibe_motor.value(0)
        led.value(0)

    # [상태 2] 경고 상황: 위험 소리(경적/경보음) 감지
    elif sound_val > SOUND_THRESHOLD:
        print(f"[경고] 위험 소리 감지! (크기: {sound_val})")
        # 촉각 패턴 피드백 (짧게 3번 진동)
        for _ in range(3):
            led.value(1)
            vibe_motor.value(1)
            time.sleep(0.1)
            vibe_motor.value(0)
            led.value(0)
            time.sleep(0.1)

    # [상태 3] 정상 상태
    else:
        vibe_motor.value(0)
        led.value(0)
        
    time.sleep(0.05) # 20Hz 주기로 빠른 신호 수집



## 2. 스마트 복약 관리 및 보관 환경 약통

import machine
import time
import dht

# 1. 핀 및 센서 설정
ldr_sensor = machine.ADC(26)            # 조도 센서 (약통 개폐 감지)
dht_sensor = dht.DHT11(machine.Pin(16)) # 온습도 센서
buzzer = machine.Pin(15, machine.Pin.OUT) # 부저
led = machine.Pin(14, machine.Pin.OUT)     # LED

# 2. 변수 및 임계값 설정
LDR_OPEN_THRESHOLD = 20000  # 약통이 열렸을 때 빛 밝기 기준 (값 이하일 때 밝음)
TEMP_LIMIT = 30              # 약물 변질 위험 온도 (°C)
HUMI_LIMIT = 70              # 약물 변질 위험 습도 (%)

MEDICATION_INTERVAL = 10     # 테스트용 복약 주기 (실제 구현 시 8시간=28800초로 변경)
last_taken_time = time.time()
dht_last_check = 0

print("=== 스마트 약통 시스템 가동 시작 ===")

while True:
    current_time = time.time()
    ldr_val = ldr_sensor.read_u16()
    
    # A. 복약 확인 (조도 센서로 약통 개폐 감지)
    if ldr_val < LDR_OPEN_THRESHOLD:  # 약통이 열림
        print(f"[복약 완료] 약통이 열렸습니다. (조도 값: {ldr_val})")
        last_taken_time = current_time # 복약 시각 갱신
        
        # 확인 알림음
        led.value(1)
        buzzer.value(1)
        time.sleep(0.2)
        buzzer.value(0)
        led.value(0)
        time.sleep(2) # 중복 감지 방지 대기
    
    # B. 복약 시간 알림 (정해진 주기가 지난 경우)
    if current_time - last_taken_time > MEDICATION_INTERVAL:
        print("[복약 알림] 약을 복용할 시간입니다!")
        # 부저 및 LED 점빡임
        led.value(1)
        buzzer.value(1)
        time.sleep(0.3)
        buzzer.value(0)
        led.value(0)
        
    # C. 보관 환경 모니터링 (2초마다 측정)
    if current_time - dht_last_check > 2:
        dht_last_check = current_time
        try:
            dht_sensor.measure()
            temp = dht_sensor.temperature()
            humi = dht_sensor.humidity()
            
            # 약물 변질 환경 경고
            if temp >= TEMP_LIMIT or humi >= HUMI_LIMIT:
                print(f"[환경 경고] 약물 변질 위험! (온도: {temp}°C, 습도: {humi}%)")
                # 환경 경고 패턴 (경고등 빠르게 flicker)
                for _ in range(2):
                    led.value(1)
                    time.sleep(0.05)
                    led.value(0)
                    time.sleep(0.05)
        except Exception as e:
            pass # 센서 읽기 오류 예외 처리

    time.sleep(0.2)
