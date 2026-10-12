# Greek 최종 조정

CORE 1734개에서 Delta, KGamma, Vv/K가 변경하지 않은 예산을 충족합니다. 고정밀 case의 물리-S 3/5-point 및 Richardson 기록을 보존하고, raw 가격에서 5-point 수식을 Decimal 산술로 다시 계산했습니다. 마지막 두 변화, analytic-FD 차이, cutoff/degree/precision 가격 불확실성의 계수 증폭을 함께 검사했습니다. 작은 h 한 쌍의 평탄함만으로 통과시키지 않았습니다.

strict PASS 사례는 원시 A/B 축 변화와 FD plateau/gap/propagation을 재검사했습니다. CORE Gamma나 Vv에서 남은 numerical unresolved는 없습니다. exact v0 right-sided Vv/Delta는 210개 모두 수치 기준을 통과하지만 limiting-PDE training constraint는 REVIEW_REQUIRED입니다. finite-x/v_max는 원래 L_b의 가격 trace만 사용하므로 불필요한 Gamma 인증을 요청하지 않았습니다.

R5의 MP Gamma=1.3523183008380165248, Vv=.1514871041211134970. 50/80/120 자리와 독립 cutoff/degree, 실제 FD windows가 모두 기준을 충족합니다. PDE Greek은 finite-grid diagnostic으로 기록하며 reference Gamma/Vv 라벨과 혼합하지 않습니다.
