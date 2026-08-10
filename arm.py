"""
6축 서보 로봇팔 기구학 — 부트캠프 2·3주차 코드를 실물용으로 이식.
FK(정기구학) + 수치 자코비안 + 감쇠최소자승(DLS) IK(역기구학).

설계 메모:
- 2주차 dh_transform / forward_kinematics 를 그대로 가져와 config 기반으로 일반화.
- 3주차는 2링크 자코비안을 손으로 유도했지만, 6축은 손유도가 고통이라
  FK를 유한차분한 '수치 자코비안'으로 대체(개념 동일, 재유도 불필요).
  det(J) 특이점 판단 정신은 DLS 감쇠항(lambda)이 흡수 — 특이점 근처에서 발산 안 함.

⚠️ 하드웨어 캘리브레이션: LINKS(링크 길이)는 도면값이 아니라 '조립 후 실측값'.
   자로 재서 갱신할 것. 서보 트림/펄스범위는 M0(PCA9685 구동)에서 별도 관리.
"""
import numpy as np

# ── 팔 설계값 (조립 후 실측으로 교체할 캘리브레이션 값, 단위 m) ──────────
# ponytail: 실측 전 임시값. 조립 후 반드시 갱신.
LINKS = dict(
    base_h=0.065,   # 바닥 ~ 어깨 회전축 높이
    upper=0.105,    # 어깨 ~ 팔꿈치
    fore=0.095,     # 팔꿈치 ~ 손목
    wrist=0.060,    # 손목 ~ 끝단(그리퍼 장착점)
)


def dh_table(L):
    """표준 관절형 6축 서보팔 DH 템플릿.
    6번째 관절(그리퍼)은 위치에 영향 없어 FK에서 제외 → 5행."""
    return np.array([
        # a,          d,           alpha
        [0.0,         L["base_h"],  np.pi / 2],   # J1 베이스 요(수직축 회전)
        [L["upper"],  0.0,          0.0],         # J2 어깨
        [L["fore"],   0.0,          0.0],         # J3 팔꿈치
        [0.0,         0.0,          np.pi / 2],   # J4 손목 피치
        [0.0,         L["wrist"],   0.0],         # J5 손목 롤
    ])


def dh_transform(theta, d, a, alpha):
    """2주차 코드 그대로 — DH 파라미터 4개 → 4x4 변환행렬."""
    ct, st, ca, sa = np.cos(theta), np.sin(theta), np.cos(alpha), np.sin(alpha)
    return np.array([
        [ct, -st * ca,  st * sa, a * ct],
        [st,  ct * ca, -ct * sa, a * st],
        [0,   sa,       ca,      d],
        [0,   0,        0,       1],
    ])


def forward_kinematics(thetas, table):
    """관절각(rad) → (끝단 위치, 모든 관절 위치 리스트). 2주차 로직 일반화."""
    T = np.eye(4)
    positions = [T[:3, 3]]
    for theta, (a, d, alpha) in zip(thetas, table):
        T = T @ dh_transform(theta, d, a, alpha)
        positions.append(T[:3, 3])
    return T[:3, 3], np.array(positions)


def jacobian(thetas, table, eps=1e-6):
    """위치 자코비안(3xN) — FK 유한차분. 3주차 해석 자코비안의 수치판."""
    n = len(thetas)
    J = np.zeros((3, n))
    for i in range(n):
        dq = np.zeros(n)
        dq[i] = eps
        p_plus, _ = forward_kinematics(thetas + dq, table)
        p_minus, _ = forward_kinematics(thetas - dq, table)
        J[:, i] = (p_plus - p_minus) / (2 * eps)
    return J


def inverse_kinematics(target, table, seed=None, lam=0.05, iters=200, tol=1e-4):
    """감쇠최소자승 IK: target 위치로 가는 관절각을 반복 탐색.
    lam(감쇠) 덕에 특이점 근처에서도 J가 발산 안 함 → 3주차 det(J)≈0 문제 회피."""
    q = np.zeros(len(table)) if seed is None else np.array(seed, dtype=float)
    for _ in range(iters):
        pos, _ = forward_kinematics(q, table)
        err = target - pos
        if np.linalg.norm(err) < tol:
            break
        J = jacobian(q, table)
        # DLS: dq = Jᵀ (J Jᵀ + λ²I)⁻¹ err
        dq = J.T @ np.linalg.solve(J @ J.T + lam**2 * np.eye(3), err)
        q += dq
    return q, np.linalg.norm(target - forward_kinematics(q, table)[0])


if __name__ == "__main__":
    tbl = dh_table(LINKS)

    # 1) FK 관절 개수 = DH행 + 1(베이스)
    _, chain = forward_kinematics(np.zeros(5), tbl)
    assert chain.shape == (6, 3), chain.shape

    # 2) IK 왕복: 임의 자세 → FK로 목표 → 다른 시드로 IK → 위치 복원되는지
    rng = np.random.default_rng(0)
    for _ in range(20):
        q_true = rng.uniform(-1.0, 1.0, 5)
        target, _ = forward_kinematics(q_true, tbl)
        _, residual = inverse_kinematics(target, tbl, seed=rng.uniform(-0.3, 0.3, 5))
        assert residual < 1e-3, f"IK 미수렴: 잔차 {residual:.2e}"

    # 3) 수치 자코비안이 FK 변화율과 일치하는지(1차 근사)
    q = np.array([0.2, -0.4, 0.6, 0.1, -0.3])
    J = jacobian(q, tbl)
    dq = np.array([0.01, 0, 0, 0, 0])
    p0, _ = forward_kinematics(q, tbl)
    p1, _ = forward_kinematics(q + dq, tbl)
    assert np.allclose(J @ dq, p1 - p0, atol=1e-4), "자코비안 불일치"

    reach = np.linalg.norm(forward_kinematics(np.zeros(5), tbl)[0])
    print(f"self-check OK · 영자세 끝단거리 {reach:.3f} m · 최대도달 ~{LINKS['upper']+LINKS['fore']+LINKS['wrist']:.3f} m")
