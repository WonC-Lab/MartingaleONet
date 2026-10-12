# CORE 판정 — PASS

고정 CORE catalog 1734/1734: **resolved 1734 / unresolved 0**. 초기 strict 187 PASS / 1547 FAIL은 수정하지 않았습니다. 1547개의 strict 실패는 별도 원시 MP/FD 증거로 수치적으로 해결됐습니다.

MP 1557 계획은 1552 returned checkpoints + 5 immutable Phase 1B.2 원시 기록으로 충족합니다. 세 정밀도, 독립 cutoff/degree, 실제 물리-S 및 variance 가격 스텐실, 두 stable increment, 증폭된 가격 불확실성, 필요 COS/strike 증거를 변경하지 않은 예산으로 재검사했습니다. 실제 derivative 검사는 최소 1734개이며 256 요구를 초과합니다. CF/ODE와 결정적 재현은 SHA 검증된 역사적 증거를 사용합니다.

외부 analytic 6개 지원 사례는 A/B/MP 및 마지막 두 analytic 변화 예산을 통과합니다. exact-v0 2개는 UNSUPPORTED_BY_QUANTLIB입니다. 외부 PDE의 유한 격자 결과는 삭제하지 않았고 별도 REVIEW_REQUIRED이며 certified labels로 사용하지 않습니다.

R5 x=0,v=.04,tau=1,kappa=4,theta=.12,sigma=.8,rho=-.1,r=0의 판정은 STALE_OR_CLASSIFIER_LOGIC_ARTIFACT입니다. 가격 reference 예산 1.3205230199960382E-7, 마지막 PDE/analytic 차이 1.3468615324E-7. 이를 A/B/MP 실패로 간주하지 않습니다. 가격/Greek reference 교차 차이는 모두 원래 예산 이내입니다.

이 판정은 사전 선언된 catalog의 경험적 수치 인증이며 모든 연속 상태의 엄밀한 인증이 아닙니다. BOUNDARY gate가 미충족이므로 Phase1C는 승인하지 않습니다.
