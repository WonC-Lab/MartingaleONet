# 훈련 필수 경계 — gate FAIL

사전 catalog 600/600 실행. 초기 strict PASS 34 / FAIL 566은 보존합니다. 훈련에서 실제 사용하는 quantity만 재검사하면 **600 resolved / 0 numerical unresolved**입니다. MP 566/566의 실제 원시 증거를 확인했습니다. 실패한 초기 float64 cutoff 결과를 그대로 보관하고, 확장된 A/B/MP 결과를 별도 인증 후보로 사용합니다.

| 항목 | coverage | 판정 |
| --- | --- | --- |
| finite-x, positive v 가격 | 240점 | PASS |
| v_max=.25 가격 | 210점; finite-x와60점 중복 | PASS |
| finite positive 합집합 | 390점 | PASS |
| exact v=0 가격/Delta/right Vv | 210점 | PASS |
| v→0+ 연속성 | 15 ATM sequences /120 values | REVIEW_REQUIRED |
| limiting-PDE compatibility | 210/210 | REVIEW_REQUIRED |


limiting-PDE 최종 절대 잔차 최대 2.898498E-16; 저장된 모든 5-point time 스텐실과 RHS 산술을 확인했습니다. 이 숫자를 합격 기준으로 새로 정의하지 않습니다. 단일 cutoff/degree의 time 스텐실은 전체 수치 오차 포락선이 아니며 원래 프로토콜에 residual 판정 예산이 없습니다.

연속성의 smallest-v 차이 최대: {'price': '1.280562E-8', 'Delta': '4.756897E-6', 'Vv': '5.134380E-5'}. 차이는 유한 v에서의 실제 모델 변화도 포함하므로 endpoint 예산에 단순 대입하지 않습니다. 15 ATM sequence는 600 경계의 모든 x/parameter 연속성을 증명하지 않습니다. 사전 판정 기준 부재 때문에 REVIEW_REQUIRED입니다.

right-sided Vv 210점은 원래 Greek/FD 예산으로 해결됐습니다. near-v=0 sequence의 별도 허용 판정과 limiting equation constraint의 최종 검토는 아직 완료되지 않았습니다. Gamma는 finite Dirichlet trace 또는 limiting-v0 training label이 아니므로 추가 인증 대상으로 만들지 않았습니다.

숫자 계산은 완료됐지만 L_b의 limiting-v0 equation과 경계 호환성이 승인되지 않았습니다. 조건부로 실패점을 제외하거나 잔차 threshold를 발명하지 않으므로 BOUNDARY FAIL입니다.
