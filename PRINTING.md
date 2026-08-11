# 3D 프린팅 로그 & 가이드

vishnusivampeta 6DOF 팔([Thingiverse thing:6152986](https://www.thingiverse.com/thing:6152986)) 부품 출력 기록.
STL 원본은 repo에 없음(용량) — Thingiverse에서 받아 `files/` 에 두고 사용.

## 장비 & 소프트웨어

- **프린터**: Sindoh **3DWOX** (연구실에 **DP200**·**2X** 보유). 베드 ≈ 210×200×195mm
- **슬라이서**: **3DWOX Desktop** (Sindoh 전용, Cura 기반)
- **재료**: PLA

## 슬라이스 설정 (간편 모드)

| 항목 | 값 |
|---|---|
| 빠른 출력 설정 | **기본 속도 출력** (소형·기어엔 고속 비추 — 품질↓·냉각부족) |
| 재질 | PLA |
| 서포트 | 기어·소형은 **끔**(톱니 망가짐), 오버행 큰 부품만 켬 |
| 베드 고정 | 브림 권장(소형 안착) |
| 익스트루더 | 2X(듀얼)는 **전부 Extruder 1** 통일 |

## 부품 목록 & 출력 상태

| 부품 | 크기(mm) | 부피 | 상태 |
|---|---|---|---|
| BasePlate | 150×150×14 | 201㎤ | ⬜ 대기 (분할/장시간) |
| Pi-PcaMount | 120×70×9 | 74㎤ | ⬜ 대기 |
| JointOne | 99×60×96 | 60㎤ | ⬜ 대기 |
| JointTwoV2Gear | 163×42×35 | 40㎤ | ⬜ 대기 |
| JointThree | 34×34×116 | 24㎤ | ⬜ 대기 |
| JointFour | 38×36×147 | 17㎤ | ⬜ 대기 |
| Gripper__Housing | 46×30×37 | 12㎤ | 🖨️ 배치2 |
| JointThreeCoupler | 38×38×36 | 8㎤ | ⬜ 대기 |
| JointFive | 33×25×22 | 7㎤ | 🖨️ 배치2 |
| MeshGear | 35×7×35 | 4.6㎤ | ✅ 배치1 |
| Gripper_Plain_Side | 26×26×23 | 2.7㎤ | ✅ 배치1 |
| Gripper_Actuated_Side | 21×28×23 | 2.5㎤ | ✅ 배치1 |
| Gripper_Gear_Holder_Plate | 46×8×6 | 1.2㎤ | ✅ 배치1 |
| JointSix | 12×12×15 | 0.6㎤ | 🖨️ 배치2 |
| Gripper_SpurGear | 12×12×4 | 0.3㎤ | ✅ 배치1 |
| Gripper_Actuator | 11×5×12 | 0.2㎤ | ✅ 배치1 |

## 출력 배치 로그

- **배치1** (~1h14) — 그리퍼 소형 6개: SpurGear·MeshGear·Actuator·Gear_Holder_Plate·Plain_Side·Actuated_Side
- **배치2** (~1h40) — Gripper__Housing·JointFive·JointSix (그리퍼 완성)
- **배치3~ 예정** — JointThreeCoupler·JointFour·JointThree·JointTwoV2Gear·JointOne·Pi-PcaMount·BasePlate

전략: 부품당 세션 시간에 맞춰 배치, **여러 대에 나눠 동시 출력**. BasePlate는 커서 분할 또는 장시간 슬롯.

## 삽질에서 얻은 교훈 (다음에 헤매지 말 것)

- **USB는 FAT32만 인식** — exFAT/NTFS면 프린터가 파일 목록을 못 봄
  - 32GB 초과 USB는 Windows 기본 포맷에 FAT32가 안 뜸 → `diskpart` 로 ≤32GB FAT32 파티션 생성:
    `select disk N` → `clean` → `create partition primary size=30000` → `format fs=fat32 quick` → `assign`
- **gcode는 USB 루트에 저장** (폴더 안에 넣으면 프린터가 못 찾음)
- **프린터 모델 = 슬라이스 모델 일치 필수** — DP200용 gcode를 2X에 넣으면 안 됨(베드·시작동작·듀얼 상이). 기계 바꾸면 재슬라이스
- **출력 중 USB 뽑지 말 것** — 프린터가 출력 내내 USB에서 읽음. 완료 후 제거
- **WiFi 네트워크 출력 가능** (3DWOX Desktop → 프린터 → 네트워크 프린터 추가) → 여러 대 동시 전송. 단 **대학망 client isolation** 이면 PC↔프린터 통신 차단되어 실패 → USB로
- **필라멘트 잼**: 억지로 빼지 말 것(끊어짐·기어 손상). 화면 언로드(예열 후) 절차 사용. **내부 PTFE 튜브/노즐은 직접 만지지 말고 관리자에게** — 잘못 재조립하면 더 큰 고장
