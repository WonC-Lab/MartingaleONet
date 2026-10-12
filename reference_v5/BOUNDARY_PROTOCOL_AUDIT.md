# Phase 1B.5 경계 acceptance protocol 감사

**결론: OUTCOME C — TRUE PROTOCOL GAP.** CORE PASS와 경계 600점의 pointwise 수치 해결은 유지합니다. 그러나 pre-result 설계가 요구한 v=0 호환성 review의 numerical acceptance와 time-sensitivity uncertainty 기준은 정해져 있지 않습니다. BOUNDARY=FAIL(REVIEW_REQUIRED), PHASE_1C_AUTHORIZED=NO입니다.

## 무엇이 원래 선언돼 있었는가

Phase 1A는 L_b에 “exact terminal … certified finite-x/v traces, limiting v=0 equation”을 포함했습니다. 같은 문서 line99는 “v=0 boundary draws use the limiting PDE”라고 명시합니다. 이를 price-only boundary objective로 바꾸면 원래 과학적 주장을 바꾸는 것이므로 허용하지 않습니다.

반대로 numerical MP/PDE residual을 network target으로 공급한다는 정의는 없습니다. network의 AD residual은 알려진 0을 target으로 합니다. 경계 Vv label supervision과 독립적인 continuity regularizer도 없으며 L_g는 positive-v training support의 supervised Greek subset입니다. exact S=0은 external check로 기재됐고 log-coordinate trunk에서 유한 x 입력이 아닙니다.

## 기준 종류의 엄격한 구분

finite trace/price/right-Vv pointwise 기준은 PREDECLARED_EXPLICIT입니다. 기존 T_C/T_Delta/T_nu와 stable-refinement, physical FD amplification 기준으로 평가할 수 있고, v4의 기존 adjudication에서 통과했습니다. c_x=e^x Delta의 error budget은 고정 x에서 e^x를 곱하는 유일한 chain-rule 결과이므로 PREDECLARED_IMPLICIT_BUT_UNAMBIGUOUS입니다.

R0[c_theta]=0이라는 수학적 target은 명시적입니다. 그러나 계산된 R0[c_ref]의 **수치 acceptance test**는 별개의 NOT_PREDECLARED 항목입니다. equation의 exactness는 time FD truncation/cutoff/roundoff acceptance rule을 자동으로 만들지 않습니다.

value continuity 및 positive-v derivative approach sequence는 원래 조사·보고할 DIAGNOSTIC_ONLY 항목입니다. “안정적인 극한을 조사하라”는 요구를 독립 loss term 또는 숫자 threshold로 바꾸지 않습니다. 실제 모델의 finite-v 변화는 numerical error와 다릅니다. right derivative의 pointwise 수렴과 positive-v derivative limit의 uniform equality도 서로 다른 주장입니다.

## 왜 implicit criterion으로 residual을 통과시킬 수 없는가

1. R0=c_tau-r exp(x)Delta-kappa theta nu+r c이며 nu=Vv/K입니다.
2. 이미 고정된 c, Delta, nu budgets로 RHS uncertainty는 계수별 선형 전파할 수 있습니다.
3. 그러나 time FD의 uncertainty는 sum|a_j| u_price_j/(12h_tau)와 time truncation을 필요로 합니다. 한 점의 T_C는 이를 유일하게 결정하지 않습니다.
4. h_tau에 따라 T_C/h_tau가 달라집니다. T_C/tau_*, T_C/tau, 실제 더 작은 refined stencil uncertainty는 서로 다른 reasonable 정책입니다. time derivative budget이나 residual 예산 배분이 없으므로 어느 하나를 기존 규칙이라고 부를 수 없습니다.
5. 마지막 step 차이가 작아도 고정 cutoff/degree tail과 derivative amplification을 통제했다는 결론이 나오지 않습니다. 기존 u_ref도 rigorous enclosure가 아닙니다.
6. 원래 residual-to-value lemma는 v>=v_min>0을 가정하며 v=0을 명시적으로 제외합니다. 이를 degenerate boundary의 합격 예산으로 옮길 수 없습니다. 해당 lemma도 boundary-error b와 residual delta의 예산 배분을 고정하지 않았습니다.

**정규화 자체는 없었던 것이 아닙니다.** Phase1A line91의 tau_*=1year, v_*=.04는 이미 존재했습니다. 부족했던 것은 normalized residual의 acceptance/uncertainty allocation입니다. 가격 nRMSE의 1e-3, 특정 unit test의 2e-7 또는 CF tolerance를 boundary PDE tolerance로 재사용할 근거도 없습니다.

## 코드와 테스트의 증거

reference_v2/boundary_pde.py는 DIAGNOSTIC_ONLY와 “No PDE tolerance declared; finite-cutoff agreement is not a boundary certificate”를 기록합니다. reference_v3/boundary_pde.py도 REVIEW_REQUIRED를 하드코딩하고, time-stencil/MP configuration을 저장하지만 acceptance rule을 만들지 않았습니다. continuity.py는 DIAGNOSTIC 상태입니다.

원래 unit tests는 payoff, CF identities, physical FD, right variance offsets, cache 정확도 및 요구 label을 검사합니다. 특정 case Gamma assertion은 general limiting-PDE gate가 아닙니다. 테스트나 comments 어디에도 boundary residual을 전체 training population에서 합격시키는 predeclared criterion은 없습니다. Phase1C의 새 L_b 구현은 아직 없으므로 consumption은 실행 증거가 아니라 원래 loss specification으로 판정했습니다. legacy src의 loss를 새로운 설계로 가져오지 않았습니다.

## chronology의 한계

아래는 logical Phase1A→1B→1B2→1B3 관계와 별도로 첫 Git content 증거의 실제 author/committer 날짜를 보존합니다. 일부 1B2 기록이 1A 문서 commit보다 먼저 나타나는 것은 묶음 게시 이력이며, commit 날짜만으로 최초 작성 순서를 발명하지 않습니다. 첨부 요청은 message 순서만 확인 가능하고 신뢰할 send timestamp는 없습니다. 모든 아래 기록은 final Colab evidence(2026-10-10)보다 앞섭니다. 기존 문서의 earlier local 결과가 곧 pre-all-results preregistration을 의미하지도 않습니다. 이 감사는 final-result 이전 조건 존재 여부를 확인합니다.

| 조건 | 첫 Git 기록 | author / committer 시각 | 근거 |
| --- | --- | --- | --- |
| limiting equation | e8d6372 | 2026-10-07T11:35:40+09:00 / 2026-10-07T12:34:04+09:00 | [design/PHASE1A_RESEARCH_DESIGN.md:41](C:/Users/WonChan/Desktop/Research/MartingaleONet/design/PHASE1A_RESEARCH_DESIGN.md:41) |
| L_b composition | e8d6372 | 2026-10-07T11:35:40+09:00 / 2026-10-07T12:34:04+09:00 | [design/PHASE1A_RESEARCH_DESIGN.md:87](C:/Users/WonChan/Desktop/Research/MartingaleONet/design/PHASE1A_RESEARCH_DESIGN.md:87) |
| PDE scales | e8d6372 | 2026-10-07T11:35:40+09:00 / 2026-10-07T12:34:04+09:00 | [design/PHASE1A_RESEARCH_DESIGN.md:91](C:/Users/WonChan/Desktop/Research/MartingaleONet/design/PHASE1A_RESEARCH_DESIGN.md:91) |
| v0 collocation | e8d6372 | 2026-10-07T11:35:40+09:00 / 2026-10-07T12:34:04+09:00 | [design/PHASE1A_RESEARCH_DESIGN.md:99](C:/Users/WonChan/Desktop/Research/MartingaleONet/design/PHASE1A_RESEARCH_DESIGN.md:99) |
| value numerical budget | e8d6372 | 2026-10-07T11:35:40+09:00 / 2026-10-07T12:34:04+09:00 | [design/REFERENCE_ENGINE_SPEC.md:57](C:/Users/WonChan/Desktop/Research/MartingaleONet/design/REFERENCE_ENGINE_SPEC.md:57) |
| right variance derivative | e8d6372 | 2026-10-07T11:35:40+09:00 / 2026-10-07T12:34:04+09:00 | [design/REFERENCE_ENGINE_SPEC.md:70](C:/Users/WonChan/Desktop/Research/MartingaleONet/design/REFERENCE_ENGINE_SPEC.md:70) |
| Greek numerical budget | e8d6372 | 2026-10-07T11:35:40+09:00 / 2026-10-07T12:34:04+09:00 | [design/REFERENCE_ENGINE_SPEC.md:76](C:/Users/WonChan/Desktop/Research/MartingaleONet/design/REFERENCE_ENGINE_SPEC.md:76) |
| boundary sequences | 85e14cc | 2026-10-07T11:27:26+09:00 / 2026-10-07T11:27:26+09:00 | [reference_v2/PROTOCOL.md:13](C:/Users/WonChan/Desktop/Research/MartingaleONet/reference_v2/PROTOCOL.md:13) |
| no PDE acceptance tolerance | 85e14cc | 2026-10-07T11:27:26+09:00 / 2026-10-07T11:27:26+09:00 | [reference_v2/boundary_pde.py:23](C:/Users/WonChan/Desktop/Research/MartingaleONet/reference_v2/boundary_pde.py:23) |
| minimal training label map | 03f83b7 | 2026-10-07T12:33:47+09:00 / 2026-10-07T12:34:06+09:00 | [reference_v3/boundary.py:16](C:/Users/WonChan/Desktop/Research/MartingaleONet/reference_v3/boundary.py:16) |
| limiting PDE review required | 03f83b7 | 2026-10-07T12:33:47+09:00 / 2026-10-07T12:34:06+09:00 | [reference_v3/boundary_pde.py:25](C:/Users/WonChan/Desktop/Research/MartingaleONet/reference_v3/boundary_pde.py:25) |
| continuity diagnostic status | 03f83b7 | 2026-10-07T12:33:47+09:00 / 2026-10-07T12:34:06+09:00 | [reference_v3/continuity.py:25](C:/Users/WonChan/Desktop/Research/MartingaleONet/reference_v3/continuity.py:25) |


## old gate의 과도한 부분과 실제 남은 blocker

v4가 generic continuity sequence에 독립 training gate를 요구한 설명은 과도했습니다. 이 추가 gate를 제외하고 diagnostic을 유지합니다. 별도의 v=0 Greek label supervision이나 finite-boundary Gamma 인증을 새 의무로 추가하는 것도 원래 L_b에 맞지 않습니다. 다만 v4는 이미 unused Gamma를 인증 대상에서 제외했으므로 이를 이번에 바꿨다고 과거를 재작성하지 않습니다. earlier reference reports와 Phase1B3 요청은 원래 objective의 v0 compatibility/treatment를 training 전에 검토하도록 요구했고, code는 그 수치 판정을 의도적으로 미결로 남겼습니다. 이 requirement 전체를 diagnostic-only로 재분류해 지우는 것은 원래 specification에 맞지 않습니다.

따라서 blocker는 “uncertified numeric residual label” 또는 “수치가 크다”가 아니라 **경계 호환성 검토의 acceptance policy 부재**입니다. 이것은 protocol/governance gap이며 모델 방정식이나 기존 pointwise label의 오류를 뜻하지 않습니다. OUTCOME B로 전체 gate를 풀 수 없고 OUTCOME A로 새로운 numerical threshold를 소급 유도할 수도 없습니다.

Phase1B6 제안은 이미 보았던 수치에 맞춘 threshold를 선택하지 않고 기존 scale/price/Greek budgets의 prospective propagation policy와 blinded 신규 inputs를 고정합니다. 제안의 새로운 time-budget allocation 및 residual /4 규칙은 신규 결정임을 명시합니다. 승인·동결 전 실행하지 않습니다.
