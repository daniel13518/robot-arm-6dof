"""
M0 · PCA9685 서보 구동 + 서보별 트림 캘리브레이션.
부품 도착 후 Jetson에서 실행. 하드웨어 없는 지금은 각도→명령 매핑 로직만 자가검증.

배선:
  Jetson I2C(SDA/SCL) → PCA9685 (SDA/SCL, VCC=로직 3.3~5V, 공통 GND)
  5V 6A 아답터 → DC잭단자대 → PCA9685 V+ / GND   (⚠️서보 전원은 V+, 로직 VCC와 별개)
  1000µF 커패시터를 V+/GND에 병렬로 (극성 주의)

라이브러리(Jetson에서): pip install adafruit-circuitpython-servokit
  ServoKit이 각도→펄스 계산을 다 해줘서 우리는 캘리브레이션만 얹으면 됨.

M0 목표: 서보 1개를 안전하게 왕복 → 배선·전원·라이브러리·트림 구조 전체 검증.
"""
from dataclasses import dataclass


# ── 서보별 캘리브레이션 (조립 후 실측으로 채우는 값) ──────────────────────
# ponytail: trim/range/invert 는 실측 전 임시값. 서보마다 물리 0점이 제각각이라
#           조립 후 반드시 한 개씩 보정. 이 표가 M0의 핵심 산출물.
@dataclass
class ServoCal:
    channel: int            # PCA9685 채널 (0~15)
    trim_deg: float = 0.0   # 기구학 0도 ↔ 서보 물리 0도 오프셋(도). 조립 후 실측
    min_pulse: int = 500    # 0도일 때 펄스폭(µs). 서보/개체마다 다름 → 실측 보정
    max_pulse: int = 2500   # 180도일 때 펄스폭(µs)
    invert: bool = False    # 관절 +방향과 서보 회전방향이 반대면 True
    lo: float = 0.0         # 안전 가동범위 하한(도) — 팔끼리·바닥 충돌 방지
    hi: float = 180.0       # 안전 가동범위 상한(도)


# 9서보: MG996R×5(큰 관절) + MG90S×4(손목·그리퍼). 채널·트림은 조립 후 확정.
JOINTS = [
    ServoCal(channel=0),   # J1 베이스 요
    ServoCal(channel=1),   # J2 어깨
    ServoCal(channel=2),   # J3 팔꿈치
    ServoCal(channel=3),   # J4 손목 피치
    ServoCal(channel=4),   # J5 손목 롤
    ServoCal(channel=5),   # 그리퍼
    # (어깨/팔꿈치가 서보 2개 겹침이면 여기에 미러 채널 추가하고 invert=True)
]


def to_servo_angle(cal: ServoCal, joint_angle: float) -> float:
    """기구학 관절각(도) → 서보에 실제 명령할 각도(도).
    순수 로직(하드웨어 무관) → 지금 자가검증 가능. 트림→반전→안전클램프 순."""
    a = joint_angle + cal.trim_deg
    if cal.invert:
        a = 180.0 - a
    lo, hi = min(cal.lo, cal.hi), max(cal.lo, cal.hi)
    return max(lo, min(hi, a))          # 안전범위 밖이면 잘라냄(충돌 방지)


# ── 하드웨어 I/O (Jetson에서만 동작; 없으면 self-check로 넘어감) ──────────
def _make_kit():
    from adafruit_servokit import ServoKit
    kit = ServoKit(channels=16)
    for cal in JOINTS:                   # 서보별 펄스범위 반영
        kit.servo[cal.channel].set_pulse_width_range(cal.min_pulse, cal.max_pulse)
    return kit


def move(kit, joint_idx: int, joint_angle: float):
    """관절각(도) 명령 → 캘리브레이션 적용 → 서보 구동."""
    cal = JOINTS[joint_idx]
    kit.servo[cal.channel].angle = to_servo_angle(cal, joint_angle)


def m0_sweep(joint_idx=0):
    """M0 실행: 서보 1개를 90°→45°→135°→90° 천천히 왕복."""
    import time
    kit = _make_kit()
    for target in (90, 45, 135, 90):
        move(kit, joint_idx, target)
        print(f"J{joint_idx} → {target}°")
        time.sleep(0.8)


if __name__ == "__main__":
    try:
        m0_sweep(0)                      # 하드웨어 있으면 실제 구동
    except (ImportError, NotImplementedError, ValueError):
        # 하드웨어/라이브러리 없음 → 순수 매핑 로직만 검증
        c = ServoCal(channel=0, trim_deg=10)       # 기본 범위 0~180
        assert to_servo_angle(c, 0) == 10          # 트림 적용
        assert to_servo_angle(c, 200) == 180       # 상한 클램프(기본 180)
        assert to_servo_angle(c, -100) == 0        # 하한 클램프(기본 0)
        s = ServoCal(channel=0, lo=20, hi=160)     # 안전 가동범위
        assert to_servo_angle(s, 200) == 160       # 안전 상한으로 잘림
        assert to_servo_angle(s, -100) == 20       # 안전 하한으로 잘림
        ci = ServoCal(channel=1, invert=True)
        assert to_servo_angle(ci, 30) == 150       # 반전
        assert to_servo_angle(ci, 90) == 90        # 반전 중심 불변
        print("self-check OK (하드웨어 없음 - 매핑 로직 검증 통과)")
