# Phase 1B.6: frozen prospective limiting-v0 protocol v6.0

**검토용 동결. 새 blinded validation은 아직 승인되지 않았습니다.** 이 단계는 이 문서/JSON/입력/코드를 커밋하고 멈춥니다. targeted runner 및 MP COS 구현도 다음 승인 단계에서 구현·검증·커밋해야 합니다. CORE, 기존600 boundary, 기존 전체 MP, large QuantLib PDE 및 neural training을 실행하지 않습니다.

이 기준은 Phase1B.5의 초안에서 출발한 **새 전향적 기준**입니다. 과거 observed residual에 소급 PASS를 부여하지 않습니다. 기존 outcome은 formula debugging 및 비용 추정에만 쓸 수 있습니다. 입력 seed, 집계, alpha, step schedule을 새 결과를 본 뒤 조정하지 않습니다. machine-readable `BOUNDARY_CERT_PROTOCOL.json`과 이 문서가 충돌하면 실행을 중단하고 protocol coding/math bug로 취급합니다.

## 1. Notation, sign and normalization

원래 설계의 \(x=\log(S/K), c=V/K,\Delta=e^{-x}c_x,\nu=c_v=V_v/K\)를 사용합니다. 입력은 K=1, exact v=0, \(\tau\ge1/252\)입니다.

\[
R_0[c]=c_\tau-r e^x\Delta-\kappa\theta\nu+r c.
\]

이는 Phase1A의 \(c_\tau=r c_x+\kappa\theta c_v-r c\)와 같은 부호입니다. phi/model evaluation의 각 precision에서 JSON 숫자의 canonical decimal 값을 쓰며, \(S=K\exp(x)\)를 **MP에서** 계산합니다. 기존 `Case.S`의 float 값을 무심코 쓰지 않고 `Integrator.values(S=...)`를 override합니다. physical-S/v/time stencil도 정확한 MP 좌표를 사용합니다.

이미 선언된 \(\tau_*=1\mathrm{year},v_*=.04\)와 K로 정규화된 가격 단위 \(C_*=1\)을 사용합니다. \(t=\tau/\tau_*,z=v/v_*\)이면

\[
\widehat R=\frac{\tau_*R_0}{C_*}
=c_t-\tau_*r c_x-\frac{\tau_*\kappa\theta}{v_*}c_z+\tau_*r c.
\]

signed \(\widehat R\)와 \(|\widehat R|\)를 모두 저장합니다. r는 year^-1, kappa*theta는 variance/year, nu는 price-ratio/variance이므로 R0는 price-ratio/year이고 위 식은 dimensionless입니다. v_*는 c_z=v_*nu에서 정확히 소거됩니다.

관찰된 RHS magnitude로 나누는 `max(...)` denominator를 채택하지 않습니다. c가 이미 K로 정규화되고 기존 acceptance가 absolute-plus-relative component budget이므로 fixed numeraire scale이면 충분합니다. 큰 drift 항으로 불일치를 희석하거나 nearzero case에 별도 observed floor를 만들지 않습니다.

## 2. Old component budgets and new time budget

두 독립 route의 reference field가 정밀도/axis/physical-FD 기준으로 수렴한 후, 잔차 합격 판정 **전에** 아래 예산을 고정합니다.

\[
T_C=10^{-8}+10^{-6}\max(|c_1|,|c_2|),\quad
T_\Delta=2\cdot10^{-6}+10^{-5}\max(|\Delta_1|,|\Delta_2|),
\]
\[
T_\nu=2\cdot10^{-5}+10^{-4}\max(|\nu_1|,|\nu_2|).
\]

가격/Greek tolerance와 Domain v1은 바꾸지 않습니다. Gamma는 이 boundary constraint의 요구 label이 아니므로 인증 대상으로 추가하지 않습니다.

새 prospective choice는 \(T_{c_\tau}=T_C/\tau_*\)입니다. characteristic year 동안의 가격 오차 척도라는 단위 근거가 있지만 **옛 문서에서 유일하게 도출된 threshold는 아닙니다**. 이것과 /4 잔차 uncertainty allocation을 명시적으로 새 정책으로 고정합니다.

\[
B_R=\frac{\tau_*}{C_*}\left[T_{c_\tau}+|r|e^x T_\Delta
                 +|\kappa\theta|T_\nu+|r|T_C\right].
\]

예산에 observed R0를 넣지 않습니다. 다음 criteria가 B_R에 비해 작은 numerical uncertainty와 zero consistency를 각각 요구합니다.

## 3. Exact time estimator and truncation

\[
D_j=\frac{c(\tau-2h_j)-8c(\tau-h_j)+8c(\tau+h_j)-c(\tau+2h_j)}{12h_j},
\qquad h_j=\tau/2^j,\quad j=6,7,\ldots,16.
\]

offsets=(-2,-1,0,1,2), coefficients=(1,-8,0,8,-1), nominal order4. h0=tau/64이며 tau-2h0>0입니다. terminal kink를 지나거나 tau=0 Greek을 만들지 않습니다. 미만 tau는 이 training boundary protocol 밖에 있으며 OOD 성공으로 대체하지 않습니다.

아래 설명의 index j는 입력 exponent schedule의 순서를 의미합니다. 인접 step이 절반이므로 leading order-four error는

\[
D(h)=c_\tau+A h^4+O(h^6),\qquad
E^{Rich}_j=|D_j-D_{j-1}|/15,
\]
\[
Q_j=(16D_j-D_{j-1})/15.
\]

15는 \(2^4-1\)이며 empirical coverage multiplier가 아닙니다. 원래 scheme의 첫 nonzero omitted moment도 fourth-order임을 symbolic checks로 확인합니다. 하지만 leading asymptotic term만의 estimate를 검증된 상한이라고 부르지 않습니다.

\[
d_j=|D_j-D_{j-1}|,\quad
u_{trunc,j}=\max(d_j,d_{j-1})\quad(j\ge2).
\]

E_Rich, previous estimate/16, Q_j와 Q_j−Q_{j−1}을 모두 기록하고 실제 판정에는 위 conservative observed-increment guard를 사용합니다. smoothness/수렴 pattern이 없으면 unresolved입니다. 이는 reproducible numerical diagnostic이며 rigorous continuum enclosure가 아닙니다.

## 4. Full uncertainty decomposition

각 reference quantity q에 대해 cutoff/N/L, degree, precision을 독립적으로 변화시킵니다. axis a의 마지막 두 absolute increment 최대값을 e_a(q)라 하고

\[
u_{axis}(q)=\sum_a e_a(q).
\]

\(u_c=u_{axis}(c)+u_{round}(c)\)입니다. Delta/nu에는 같은 axis uncertainty에 physical-FD truncation, analytic/FD discrepancy와 absolute stencil-price amplification을 더합니다. right variance derivative는 offsets=(0,1,2,3,4), coefficients=(-25,48,-36,16,-3)/(12h_v), h_v=.01q를 사용합니다. 기존 10 relative steps (.02,.01,.005,.0025,.00125,.000625,.0001,.00001,.000001,.0000001)에서 두 stable increments와 uncertainty/T_G<=1/4를 확인합니다. 계산한 price/Greek을 clip하지 않습니다.

time derivative에서는

\[
u_{\tau,price}={\sum_{m=-2}^2|a_m|u_{c,m}\over12h_j},\qquad
u_\tau=u_{\tau,price}+u_{trunc}+u_{\tau,arithmetic}.
\]

계수 L1 합은18입니다. covariance cancellation, 독립이라는 통계 가정 또는 base price 하나의 uncertainty를 모든 stencil에 복사하는 가정은 허용하지 않습니다. 각 time-price의 실제 axis uncertainty를 보존합니다.

\[
u_R=u_\tau+|r e^x|u_\Delta+|\kappa\theta|u_\nu+|r|u_c,
\qquad \widehat u_R=\tau_*u_R/C_*.
\]

price/reference, Delta, right-nu, time FD, cutoff/quadrature, time truncation, cancellation/roundoff를 별도 column으로 저장합니다. tail/COS-domain/degree 항은 이미 u_axis에 포함되므로 같은 uncertainty를 별도 scalar로 중복 더하지 않습니다. cross-route difference는 별도 consistency test입니다.

roundoff allowance는 실제 MP bit precision b에서 eps=2^(1-b), gamma_m=m*eps/(1-m*eps)이며 m=64*n_terms+256을 기록합니다. signed summands와 constants의 absolute 합에 gamma_m을 곱합니다. time weighted arithmetic에는 gamma_64*sum|a_m c_m|/(12h)를 추가합니다. 이는 cancellation-aware operation-count diagnostic이지 elementary functions의 interval bound가 아닙니다. 50/80/120-digit 독립 평가도 반드시 만족해야 합니다. 값이나 uncertainty가 nonfinite/unknown이면 unresolved이며0으로 대체하지 않습니다.

## 5. Independent methods and fixed axes

E1: 기존 genuine MP Lewis inversion 및 검증된 affine-variance cache.

E2: 기존 독립 hyperbolic Riccati/COS 수식을 **진짜 MP로 이식**한 inversion. float64 결과의 decimal-string 변환은 MP가 아닙니다. 아직 이 이식/targeted runner는 구현·실행하지 않았습니다. 다음 승인 단계에서 known cases로 convention/port correctness를 확인하고 source commit/hash를 기록해야 합니다. affine model 공유 위험은 유지되며 exact-v0 QuantLib를 epsilon으로 대체하지 않습니다.

고정 schedules:

- MP digits=50,80,120; quadrature degree=24,40,64.
- U=64,128,…,1,048,576 (2배). 옛 ladder의 작은 U로 시작해 long-maturity의 불필요한 과대 grid를 피하지만 적어도3 level과 마지막 두 stable increments는 필요합니다.
- COS N=4096,8192,16384,32768,65536; L=16,24,32,48,64. 각 L에서 N의 두 안정 increment와 수렴한 N에서 L의 두 안정 increment를 확인합니다.
- COS base-tau interval은 해당 case/L의 모든 time 및 physical-S/v stencils에 고정합니다. cumulant interval은 heuristic이며 tail proof가 아닙니다.
- phase_span은 원래 입력 기반 span 공식을 사용합니다. 동일 p/base-tau cache family의 모든 선언된 stencils에 대한 입력 기반 최대 span을 쓸 수 있습니다. observed residual로 mesh를 선택하지 않습니다.
- 각 axis는 다른 axes를 고정하여 측정합니다. 후보 endpoint의 precision/degree/cutoff 값 및 physical-FD base가 같은 인증 후보와 해당 예산 안에서 일치해야 합니다.

## 6. Pointwise rule, alpha and deterministic stopping

**alpha=1**입니다. 이미 absolute propagated uncertainty를 모두 더하므로 별도2/3/4 empirical coverage multiplier를 도입하지 않습니다. estimated numerical band가0을 포함하는지 검사하며 통계적95% confidence claim을 하지 않습니다.

각 estimator의 세 연속 eligible time levels에 대해:

1. 각 level에서 \(|\widehat R|\le\widehat u_R\).
2. 각 level에서 \(\widehat u_R\le B_R/4\).
3. 두 time increments 각각 <=B_R/4.
4. 마지막/이전 time increment ratio <=1/2 **또는** 두 increments가 각각 그 두 level의 independently propagated time-price uncertainties 합 이하.
5. 각 연속 uncertainty ratio <=2. 이는 h를 절반으로 줄이면 first-derivative amplification이2배가 된다는 수치 guard입니다. 모든 level의 absolute cap도 계속 적용합니다.
6. c/Delta/nu의 원래 reference/FD criteria를 만족하고 unresolved amplification/solver flag가 없어야 합니다.

ratio의 분모가0이고 분자0이면0, 분자가 양수이면 infinity로 저장합니다. ratio1/2는 nominal1/16보다 느슨한 one-bit contraction guard이며 **사전에 새로 선택한 규칙**입니다. old residual pattern으로 fit하지 않았습니다. refinement 또는 uncertainty를 만족시키기 위해 failure row/step을 버리지 않습니다.

u_trunc는 세 estimates 뒤에 정의되므로 처음 eligible three-level window에5개 time estimates가 필요합니다. 첫 qualifying window 뒤 **한 finer confirming step**을 계산해 다음 overlapping window도 조건을 만족해야 합니다. 최소6개, 최대11개 levels입니다. 가장 작은 h나 가장 유리한 residual을 골라 채택하지 않습니다.

두 독립 estimator의 confirming level에서 \(|\widehat R_1-\widehat R_2|\le\widehat u_{R,1}+\widehat u_{R,2}\)도 검사합니다. 실제 times 및 constituent fields를 일치시켜야 합니다. 각 estimator가 따로 zero consistency를 만족하므로 이 조건만을 독립 증거라고 과장하지 않습니다.

미측정/exception/axis/uncertainty failure는 NUMERICAL_UNRESOLVED입니다. estimator 안정성과 reference criteria가 통과했지만 zero consistency가 안 맞으면 RESIDUAL_INCOMPATIBLE로 기록합니다. 이것이 곧 Heston 방정식 오류라는 주장은 아닙니다. frozen coding/math bug를 발견하면 전체 run을 무효화하고 v6.1 및 새 unopened inputs로 재동결합니다.

## 7. New population and aggregation

**128점 전부 신규**이며 기존600 boundary와 full input tuple 중복이0입니다. primary prospective test로 기존210점이나600점을 재점수화하지 않습니다.

32 p-blocks ×4 states: 8개 input-box anchor blocks＋seed6107 Sobol candidates에서 Feller 만족12개/위반12개 blocks. 두 strata의 할당만 입력으로 정하며 양쪽을 모두 포함합니다. seed6108은 random interior x에만 사용합니다. input manifest의 actual coordinates/hash가 authoritative입니다.

각 block은 ATM-short(x0,tau1/252), interior-medium(x[-.7,.7],tau.1), left-collar-long(x−1.2,tau2), right-collar-short(x1.2,tau1/252)를 갖습니다. 모든 parameter bounds의 endpoints는 anchors가 포함합니다. 총 Feller 만족68점, 위반60점입니다. param bounds는 kappa[.5,4],theta[.02,.12],sigma[.1,.8],rho[-.9,-.1],r[0,.08]입니다. original partition에서 v0가 CHALLENGE라는 이름은 보존하지만 이 검증의 역할은 원래 훈련 경계입니다. evaluation OOD를 training CORE로 재분류하지 않습니다.

128은 독립 model probability bound를 위한 sample size가 아닙니다. 8개 input anchors와24개 QMC blocks 각각에4개의 훈련-relevant geometry를 배치한 targeted empirical certification 크기입니다. 전체 연속 domain certificate나 IID-binomial confidence를 주장하지 않습니다. 새 outcomes를 본 뒤256으로 늘려 실패율을 개선하는 선택은 하지 않습니다.

**128/128 모두 PASS**여야 boundary compatibility job을 통과시킵니다. REVIEW_REQUIRED, solver failure, missing/pending도 승인에 허용하지 않습니다. 기존 CORE PASS 및 finite-price/실제 소비 quantity의 인증이 유지되고 다른 blocker가 없을 때만 향후 BOUNDARY PASS / PHASE_1C_AUTHORIZED YES를 판정할 수 있습니다. 그 판정도 training 실행 명령이 아닙니다.

## 8. Cost, equivalent efficiency and approval

최소6/최대11 time levels는 nested offsets 재사용으로 estimator당15–25 unique time prices입니다. E1에서 단순히 time-price API를 따로 부르면1,920–3,200회이며 각 call 안의 precision/degree/cutoff 검사와 physical FD는 추가됩니다. E2도 별도로 필요합니다.

`COMPUTE_COST_ESTIMATE.json`은 **새 residual을 평가하지 않고** input geometry 및 기존 timing metadata만으로 작성했습니다. E1 reference-axis configurations는 최소7에서 최대19, E2는 최소11에서 최대27입니다. 이에 따른 time-price output 수는 E1 약13,440–60,800개, E2 약21,120–86,400개입니다. 이 숫자는 cached CF를 별도로 재계산하는 cold API call 수와 다릅니다. physical FD outputs는 별도입니다. 기존 MP80 node throughput의 중앙값은 약2,229 nodes/sec입니다. input-only tail planning은 cutoff/FD 증폭의 비용 추정이며 certification tail bound나 adaptive stopping rule이 아닙니다.

E1의 prefix/group-cache를 가정한 4 CPU wall-time envelope는 약12–22시간입니다. 120-digit, right/spot FD 및 미구현 MP COS overhead는 추가될 수 있어 전체는 더 오래 걸릴 수 있습니다. 이것은 실행 benchmark 또는 완료 보장이 아니며 가정 오차가 큽니다. 몇 시간 이내라고 승인 요청하지 않습니다.

동일 frozen decision을 지키는 가장 효율적인 계획은4096-node streaming, Gauss rules 및 completed-prefix 재사용, 고정 p의 beta/root/ratio caching, 동일 p/base-tau의 x별 spectrum 공유, affine-variance FD 재사용, COS frequency prefix caching, 첫 stable-window＋one-confirmation stopping입니다. individual price uncertainty의 covariance cancellation 또는 paired-error 할인으로 기준을 바꾸지 않습니다. source correctness는 구현 후 known inputs로 별도 검증해야 합니다.

full array 방식은 worst input에서약166만 nodes이므로25 spectral arrays를 보관하지 않습니다. 목표 memory는 worker512MiB 이하,4 workers＋parent4GiB 안이며 실제 구현의 allocation profiling이 필요합니다. CPU 기반 mpmath/gmpy2이므로 A100/GPU는 요구하지 않습니다. Colab CPU는 계산에 사용할 수 있으나 여러 session/checkpoint가 필요할 수 있습니다.

case30 CPU분, batch8 wall-hours, 최대4 workers에서 checkpoint 후 stop합니다. 이 ceiling은 tolerance가 아니며 남은 점을 성공으로 바꾸지 않습니다. 필요하면 분할 재개를 제안하되 승인 전 실행하지 않습니다. 새 deterministic case/setting checkpoints에는 protocol/input/executor/reference hashes가 모두 포함되어야 합니다. 미완료 checkpoint는 atomic rename 전에 완료로 표시하지 않습니다.

## 9. Freeze receipt and execution binding

`BOUNDARY_BLINDED_INPUTS.sha256`와 receipt의 protocol/입력/코드 SHA는 실행 전 엄격히 검증해야 합니다. v6의 `.gitattributes`는 UTF8 LF Git transport를 고정합니다. reference source는 기존 Windows/Linux CRLF transport를 구분하여 canonical-LF SHA로 검증합니다.

Git commit 자체를 그 commit 안의 receipt에 넣는 self-reference는 불가능합니다. 따라서 protocol/inputs/code를 **commit A**로 동결하고 receipt에 A의 정확한 commit을 기록한 뒤 receipt를 **commit B**로 저장합니다. A의 frozen Git bytes와 현재 files가 일치하는지도 검증합니다. 두 commit 모두 prospective evaluation 전에 존재합니다.

code version은 `limiting-v0-certification-v6.0`, policy.py와 generator/reference source SHA를 포함합니다. executable runner는 아직 없으므로 그 hash를 있는 것처럼 쓰지 않습니다. 다음 승인 단계의 구현 commit 및 executor SHA를 execution provenance에 추가하고 frozen policy를 다시 검증해야 합니다.

**STOP_AFTER_FREEZE. 새 R0/c_tau/reference evaluation, 결과 생성 및 Phase1C training을 실행하지 않았습니다.**
