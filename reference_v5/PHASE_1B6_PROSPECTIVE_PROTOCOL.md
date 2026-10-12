# Phase 1B.6 — 사전 경계 호환성 검증 제안

상태: **DRAFT_NOT_EXECUTED / 승인·버전 고정 전 실행 금지**. 이 문서는 Phase 1B.5에서 확인된 프로토콜 공백을 메우는 **새 제안**입니다. Phase 1A에 이미 존재했던 잔차 합격 기준이라고 주장하지 않으며, Phase 1B.3/1B.4 잔차에 소급 적용하지 않습니다. 새 결과를 보거나 계산하지 않고 입력 규칙과 기존 price/Greek 예산으로 설계했습니다. 기존 CORE, Domain v1, Feller 포함 정책, price/Greek 허용오차는 그대로입니다.

## 1. 검증 대상과 훈련 의존성

\(p=(\kappa,\theta,\sigma,\rho,r),\ x=\log(S/K),\ c=V/K\)라 둡니다. 양의 만기에서 exact v=0의 모델 항등식은

\[
R_0[c]=c_\tau-r c_x-\kappa\theta c_v^++r c=0.
\]

이것은 미래 네트워크에 적용할 AD penalty의 **알려진 0 target**입니다. 숫자로 계산한 reference residual을 네트워크 target으로 사용하는 제안이 아닙니다. 이 검증은 경계 reference 값/민감도가 이 방정식과 수치적으로 호환되는지를 확인하며, 일반적인 v=0 경계 정칙성 정리를 대신하지 않습니다. future surrogate의 잔차 합격 기준이나 optimizer stopping rule도 아닙니다.

finite-x/v_max의 가격 trace는 기존 가격 인증을 그대로 사용합니다. v=0 Gamma나 독립적인 continuity loss, Vv label loss를 새로 L_b에 추가하지 않습니다.

## 2. 이미 선언된 정규화

원래 설계의 \(\tau_*=1\ \mathrm{year},\ v_*=0.04\)를 그대로 사용합니다. \(t=\tau/\tau_*,\ z=v/v_*\)로 두면

\[
\widetilde R_0=\tau_* R_0
=c_t-\tau_*r c_x-\frac{\tau_*\kappa\theta}{v_*}c_z^++\tau_*r c.
\]

\(c_x=e^x\Delta,\ c_v^+=V_v^+/K,\ c_z^+=v_*c_v^+\)입니다. 따라서 physical-S Delta를 잔차로 옮길 때 e^x를 반드시 포함합니다. variance 스케일이 생략되거나 두 번 곱해지는 구현을 금지합니다.

## 3. 새로 제안하는 합격 예산 — 기존 기준과의 차이

원래의 pointwise 예산을 사용합니다.

\[
T_C=10^{-8}+10^{-6}\max(|c_A|,|c_B|),\quad
T_\Delta=2\cdot10^{-6}+10^{-5}\max(|\Delta_A|,|\Delta_B|),
\]
\[
T_\nu=2\cdot10^{-5}+10^{-4}\max(|c_{v,A}|,|c_{v,B}|).
\]

이미 인증된 case는 동결된 원래 예산을 사용합니다. 새 blinded case에서는 동일한 공식으로 동결된 최종 refinement estimator envelope를 사용하며 예산에 잔차 값 자체를 넣지 않습니다.

**새 정책 선택**은 time sensitivity에 가격 오차가 characteristic time 동안 누적되는 척도 \(T_{c_\tau}=T_C/\tau_*\)를 배정하는 것입니다. 단위와 기존 스케일에 근거하지만, 기존 문서에서 유일하게 도출되던 규칙은 아닙니다. \(T_C/\tau\) 또는 다른 오차 배분도 가능했기 때문에 이 선택은 사전 승인해야 합니다. v=0을 제외하는 interior stability lemma로 이를 증명했다고 주장하지 않습니다.

삼각부등식으로 정규화된 잔차의 성분 예산을 합하면

\[
B_R=\tau_*\left[T_C/\tau_*+|r|e^xT_\Delta
                 +\kappa\theta T_\nu+|r|T_C\right].
\]

기존 관찰 잔차에 맞춘 독립 절대 상수는 도입하지 않습니다. 다음 **새 전향적 규칙**으로만 평가합니다.

- 두 독립 estimator 각각 \(U_R\le B_R/4\).
- 두 estimator 각각 \(|\widehat{\widetilde R}_0|+U_R\le B_R\). 불확실성이 큰 값을 합격시키는 방식이 아닙니다.
- 두 estimator 간 \(|\widehat R_1-\widehat R_2|\le U_{R,1}+U_{R,2}\).
- 모든 독립 numerical axis의 마지막 두 increment가 \(B_R/4\) 이하이고, 아래의 공통 FD 안정 구간이 존재해야 합니다.

이 규칙의 /4 배분은 기존 reference refinement 정책을 새 잔차에 확장하는 **명시적 신규 선택**입니다. 과거에 이미 선언된 PDE 기준으로 소급 해석하지 않습니다.

## 4. Numerical uncertainty의 계산

노드/degree/precision/cutoff를 고정하지 않은 상태에서 time FD만 작아졌다고 합격시키지 않습니다. 각 stencil price에 independently assessed normalized uncertainty \(u_{c,j}\)를 붙입니다. 표본 차이를 엄밀한 구간 또는 95% 신뢰구간으로 표현하지 않습니다.

time 5-point FD는 \(a=(1,-8,0,8,-1)\), offsets=(-2,-1,0,1,2)입니다.

\[
\widehat c_\tau(h)=\frac{\sum_j a_j c(\tau+jh)}{12h},\qquad
u_{\tau,\mathrm{price}}=\frac{\sum_j|a_j|u_{c,j}}{12h}.
\]

계수 L1 합은 18입니다. 다음 항을 모두 기록합니다.

\[
u_\tau=u_{\tau,\mathrm{price}}+u_{\tau,\mathrm{step}}+u_{\tau,\mathrm{round}},
\]
\[
U_R=\tau_*[u_\tau+|r|e^x u_\Delta+\kappa\theta u_\nu+|r|u_c].
\]

각 price/Greek uncertainty는 마지막 두 cutoff, degree, precision, 해당 route의 mesh/tolerance 변화를 보수적으로 누적하여 기록합니다. 중간 axis 중 하나의 차이만 선택하지 않습니다. cross-estimator 차이는 독립된 consistency 검사로 보고합니다. time-step truncation diagnostic은 마지막 두 time increment의 최대값과 마지막 3-point/5-point 차이 중 최대값을 사용합니다. Richardson 비교는 추가 일관성 검사로 기록하되, 아직 확인되지 않은 smoothness를 근거로 observed difference/15만을 오차 상한이라 주장하지 않습니다. roundoff와 serialize 오차도 포함합니다. 추정이 불가능하면 `UNRESOLVED`입니다.

## 5. 독립 estimator와 고정 refinement schedule

E1: genuine MP Lewis prices에서 physical-time FD, independent physical-S/variance FD.

E2: 확장된 Route A P1/P2 또는 Route B COS prices에서 **별도의** physical-time 및 right-variance FD. analytic RHS와 같은 프로그램 값을 재배열하는 것은 독립 time estimator가 아닙니다. 실제 stencil price를 별도로 계산해야 합니다. float64의 propagated error가 예산을 못 맞추면 기록된 진짜 MP P1/P2/COS 구현을 따로 검토해야 하며, float64를 decimal string으로 바꾸는 대체는 금지합니다. 이 구현은 아직 실행하지 않았습니다. 공유 affine-model/CF 위험도 보고합니다. exact-v0 QuantLib 미지원은 epsilon 대체로 숨기지 않습니다.

동결 schedule:

- MP digits: 50,80,120.
- quadrature degrees: 24,40,64; 필요 시 사전에 포함한 96까지. coupling-only refinement 금지.
- cutoff: 1024부터 2배씩 1,048,576까지. 기존 작은 cutoff를 건너뛴 이유와 기존 checkpoint 참조는 기록하며, 최소 세 연속 cutoff 결과를 확보합니다.
- Route A tolerance: 1e-9,1e-11,1e-13 및 독립 panel 4,8,16. solver warning을 삭제하지 않습니다.
- Route B N=4096,8192,16384,32768; L=16,24,32,48. N/L을 독립적으로 변화시킵니다.
- time steps \(h_j=\tau/2^j,\ j=6,\ldots,16\). \(\tau-2h_j>0\)이며 terminal kink를 통과하지 않습니다.
- physical-S 및 right-v steps는 원래 10-step sequence (.02,.01,.005,.0025,.00125,.000625,.0001,.00001,.000001,.0000001)를 사용합니다. v=0에서는 \(h_v=.01q\), offsets=0,1,2,3,4만 사용합니다.

FD acceptance는 세 연속 step이 만드는 **두 increment**의 변화, 3/5-point 일관성, uncertainty amplification이 동시에 예산 안에 드는 공통 window를 요구합니다. time FD의 두 increment와 3/5-point 차이는 각각 \(\tau_*\)를 곱해 \(B_R/4\) 이하여야 합니다. Delta/Vv는 각각 원래 \(T_\Delta/4,T_\nu/4\) 기준으로 두 increment, 5-point/analytic 차이, price-uncertainty amplification을 검사합니다. 모든 항은 위 U_R에도 전파합니다. 작은 h 한 쌍만 골라 통과시키지 않습니다. noisy/singular case에 창이 없으면 unresolved입니다. 안정 창의 존재를 검사하되 모든 실패 step은 원시 출력에 남깁니다.

## 6. 경우 선택과 blinded 확인

최소 훈련 경계 catalog의 **기존 v=0 210점 전체**를 유지합니다. 여기에 별도 validation seed 6106의 Owen-scrambled Sobol 5차원 p-block 8개를 Domain v1 parameter box에 입력만으로 매핑합니다. 각 block은 원래 x={-1.2,-.7,-.1,0,.1,.7,1.2}, tau={1/252,.1,2}의 21개 v=0 상태를 가집니다. 신규 168점으로 **총 378점**입니다. `PHASE_1B6_CASE_MANIFEST.json`의 case 목록과 SHA를 실행 전에 고정합니다.

Feller로 제거하거나 이미 관찰된 유리한 잔차로 선택하지 않습니다. 새 block은 train/dev/final-evaluator seeds와 별도이며 최종 모델 test로 재사용하지 않습니다. 이 유한 catalog는 연속 parameter box 전체의 엄밀한 certificate가 아닙니다. 나중에 생성할 실제 훈련 reference label은 각각 원래 price/Greek gate를 별도로 통과해야 합니다.

기존 210점의 새 criterion 평가가 retrospective임을 별도 표시하고, **사전 동결된 새 168점 평가까지** 없이는 새 boundary validation을 완료로 선언하지 않습니다. 새 잔차를 본 뒤 threshold 또는 case list를 변경하면 새로운 protocol version과 별도 unopened cases가 필요합니다.

## 7. 연속성 및 특이 경계

value continuity \(c(x,v,\tau)\to c(x,0,\tau)\) 및 derivative-limit sequence는 기존 v={0,1e-8,1e-7,1e-6,1e-5,1e-4,1e-3,1e-2}로 진단합니다. 새로운 continuity loss나 무관한 독립 PASS threshold를 추가하지 않습니다. finite positive-v와 zero-v 값이 다른 것은 그 자체로 solver error가 아닙니다.

right derivative는 고정된 5-point one-sided estimator와 원래 \(T_\nu\), plateau/propagation 기준을 사용합니다. 존재/수렴을 수치 증거가 뒷받침하지 않으면 `UNRESOLVED`이지 임의의 큰 값/0 대체가 아닙니다. \(Vega_s=0\)은 Vv 인증으로 사용하지 않습니다. positive \(\kappa\theta\)에서는 zero variance 이후에도 stochastic variance를 유지하며 discounted intrinsic payoff를 대체 라벨로 쓰지 않습니다. Feller 위반을 삭제하지 않고 별도 strata로 보고합니다.

## 8. 집계와 stopping rule

모든 378점의 required reference quantity/잔차 판정이 통과해야 해당 empirical boundary compatibility job을 PASS로 판정합니다. 누락, 예외, 정밀도·축 불안정, 수렴하지 않는 derivative는 분모에 남겨 FAIL/INCOMPLETE로 표시합니다. 기존 finite-price 390점의 인증도 함께 확인해야 BOUNDARY 전체를 판정할 수 있습니다. CORE/CHALLENGE 결과는 별도입니다.

첫 PASS만 보고 종료하지 않습니다. 각 축에서 최소 세 연속 level, 두 안정 increment, 두 독립 estimator를 확보해야 합니다. schedule ceiling 도달 시 unresolved이며 더 큰 sweep을 자동 시작하지 않습니다. 한 case 30 CPU분 또는 batch 8 wall-hours(최대 4 workers)에서 checkpoint 후 중단하고 pending으로 남깁니다. 이 숫자는 과학적 허용오차가 아니라 **제안된 계산 비용 상한**이며 예상 runtime이 아닙니다. 실제 실행 전 missing estimator 구현, 대표 input의 비용 및 user-approved 실행 범위를 제시해야 합니다.

출력은 향후 새 `reference_v6/`에 raw stencil, 모든 실패, 축별 uncertainty, case manifest, pointwise CSV, gate report, source/environment hash를 저장합니다. CORE 전수, 전체 기존 MP, large QuantLib PDE sweep, neural training은 이 protocol의 작업 범위가 아닙니다.

**이 파일과 입력 manifest를 생성했을 뿐, 새로운 가격/잔차 계산은 실행하지 않았습니다. Phase 1C 승인도 아닙니다.**
