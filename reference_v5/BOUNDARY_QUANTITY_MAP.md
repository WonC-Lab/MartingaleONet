# 훈련 경계 quantity map

각 quantity에 정확히 하나의 predeclaration 상태를 배정합니다. 수학적 target 선언과 reference numerical acceptance를 서로 다른 대상으로 명시하여 혼동하지 않습니다. 새 기준으로 기존 residual을 평가하지 않았습니다.

| quantity | status | 역할 / 직접 훈련 소비 | numerical adjudication |
| --- | --- | --- | --- |
| terminal_value | PREDECLARED_EXPLICIT | exact supervised value / L_b terminal term | EXACT_TARGET_DEFINED |
| absorbing_stock_zero | DIAGNOSTIC_ONLY | exact S=0 external check / not a separately declared sampled L_b target at finite x | DIAGNOSTIC_ONLY |
| finite_x_value | PREDECLARED_EXPLICIT | certified value label / L_b finite-x trace | PASS_EXISTING_POINTWISE_EVIDENCE |
| vmax_value | PREDECLARED_EXPLICIT | certified value label / L_b finite-v_max trace | PASS_EXISTING_POINTWISE_EVIDENCE |
| zero_variance_value | PREDECLARED_EXPLICIT | reference consistency component; not an additional v0 Dirichlet loss / c_theta appears in the v0 AD equation; reference residual is not a label | PASS_EXISTING_POINTWISE_EVIDENCE |
| right_Vv_point | PREDECLARED_EXPLICIT | reference derivative consistency component / network right derivative in v0 equation; no separate boundary Vv label loss declared | PASS_EXISTING_POINTWISE_EVIDENCE |
| mapped_cx_component | PREDECLARED_IMPLICIT_BUT_UNAMBIGUOUS | coordinate-mapped error bound / v0 AD equation component; no extra supervised cx target | PASS_FROM_EXISTING_DELTA_EVIDENCE |
| value_continuity_sequence | DIAGNOSTIC_ONLY | report boundary approach; no standalone continuity penalty / no direct loss term; qualitative consistency diagnostic | DIAGNOSTIC_ONLY_NO_INDEPENDENT_TRAINING_GATE |
| derivative_continuity_sequence | DIAGNOSTIC_ONLY | not identical to right derivative existence/value certification / no direct derivative-continuity regularization declared | DIAGNOSTIC_ONLY |
| network_v0_penalty_target | PREDECLARED_EXPLICIT | mathematically known zero penalty target / directly used by L_b at exact v0 | EXACT_TARGET_DEFINED_NOT_A_NUMERICAL_REFERENCE_CERTIFICATE |
| reference_v0_compatibility_acceptance | NOT_PREDECLARED | pre-training v0 consistency review obligation / indirect validation of the model boundary constraint, not a training label | PROTOCOL_GAP |
| reference_time_derivative_budget | NOT_PREDECLARED | missing component of reference residual acceptance / network AD derivative is a residual component; not a reference supervised time Greek | PROTOCOL_GAP |


## terminal_value

- 수학적 대상: c(x,v,0)=(exp(x)-1)^+
- 판정: **PREDECLARED_EXPLICIT**
- 역할: exact supervised value
- 훈련 의존성: L_b terminal term
- estimator: analytic payoff; no FD Greek at the kink
- grid/step: terminal sampling; no reference refinement required
- convergence/acceptance: exact identity
- 기존 기준에 대한 평가: EXACT_TARGET_DEFINED
- 근거: design/PHASE1A_RESEARCH_DESIGN.md:41,76,87,99

## absorbing_stock_zero

- 수학적 대상: V(0,v,K,tau)=0; x=-infinity is not a finite trunk query
- 판정: **DIAGNOSTIC_ONLY**
- 역할: exact S=0 external check
- 훈련 의존성: not a separately declared sampled L_b target at finite x
- estimator: analytic boundary identity
- grid/step: external diagnostic
- convergence/acceptance: do not replace x=-1.2 labels by zero
- 기존 기준에 대한 평가: DIAGNOSTIC_ONLY
- 근거: design/PHASE1A_RESEARCH_DESIGN.md:41,87

## finite_x_value

- 수학적 대상: c(x_b,v,tau,p), x_b=+-1.2
- 판정: **PREDECLARED_EXPLICIT**
- 역할: certified value label
- 훈련 의존성: L_b finite-x trace
- estimator: independent A/B + MP on failures
- grid/step: original cutoff/N/L/tolerance/precision refinements; required boundary catalog
- convergence/acceptance: T_C cross agreement and final two increments <=T_C/4
- 기존 기준에 대한 평가: PASS_EXISTING_POINTWISE_EVIDENCE
- 근거: design/PHASE1A_RESEARCH_DESIGN.md:41,87,99; design/REFERENCE_ENGINE_SPEC.md:57-61

## vmax_value

- 수학적 대상: c(x,.25,tau,p)
- 판정: **PREDECLARED_EXPLICIT**
- 역할: certified value label
- 훈련 의존성: L_b finite-v_max trace
- estimator: independent A/B/MP
- grid/step: same pointwise price criteria
- convergence/acceptance: T_C and two stable refinements
- 기존 기준에 대한 평가: PASS_EXISTING_POINTWISE_EVIDENCE
- 근거: design/PHASE1A_RESEARCH_DESIGN.md:41,99; design/REFERENCE_ENGINE_SPEC.md:57-61

## zero_variance_value

- 수학적 대상: c_0(x,tau,p)=c(x,0,tau,p)
- 판정: **PREDECLARED_EXPLICIT**
- 역할: reference consistency component; not an additional v0 Dirichlet loss
- 훈련 의존성: c_theta appears in the v0 AD equation; reference residual is not a label
- estimator: genuine MP and refined A/B price
- grid/step: v0 part of minimum boundary catalog
- convergence/acceptance: original T_C
- 기존 기준에 대한 평가: PASS_EXISTING_POINTWISE_EVIDENCE
- 근거: design/PHASE1A_RESEARCH_DESIGN.md:41,87,99; reference_v3/boundary.py:16

## right_Vv_point

- 수학적 대상: c_v^+(x,0,tau,p)=lim_h_down_0 [c(x,h,tau,p)-c_0]/h = V_v^+/K if it exists
- 판정: **PREDECLARED_EXPLICIT**
- 역할: reference derivative consistency component
- 훈련 의존성: network right derivative in v0 equation; no separate boundary Vv label loss declared
- estimator: (-25 f0+48 f1-36 f2+16 f3-3 f4)/(12h_v)
- grid/step: original six relative steps; v2 ten-step extension, h_v=.01q at zero
- convergence/acceptance: T_nu; two FD increments, analytic gap and propagated uncertainty <=T_nu/4
- 기존 기준에 대한 평가: PASS_EXISTING_POINTWISE_EVIDENCE
- 근거: design/REFERENCE_ENGINE_SPEC.md:70,74,76; reference_v2/PROTOCOL.md:11

## mapped_cx_component

- 수학적 대상: c_x=e^x Delta; T_cx=e^x T_Delta at fixed x
- 판정: **PREDECLARED_IMPLICIT_BUT_UNAMBIGUOUS**
- 역할: coordinate-mapped error bound
- 훈련 의존성: v0 AD equation component; no extra supervised cx target
- estimator: Delta + exact coordinate chain rule
- grid/step: same predeclared Delta refinements
- convergence/acceptance: multiply existing Delta budget by e^x; no extra tolerance selected
- 기존 기준에 대한 평가: PASS_FROM_EXISTING_DELTA_EVIDENCE
- 근거: design/PHASE1A_RESEARCH_DESIGN.md:66; design/REFERENCE_ENGINE_SPEC.md:76

## value_continuity_sequence

- 수학적 대상: lim_v_down_0 c(x,v,tau,p)=c_0(x,tau,p)
- 판정: **DIAGNOSTIC_ONLY**
- 역할: report boundary approach; no standalone continuity penalty
- 훈련 의존성: no direct loss term; qualitative consistency diagnostic
- estimator: g(v)=c(v)-c_0
- grid/step: v=0,1e-8,1e-7,1e-6,1e-5,1e-4,1e-3,1e-2
- convergence/acceptance: observed approach; no predeclared numeric pass threshold
- 기존 기준에 대한 평가: DIAGNOSTIC_ONLY_NO_INDEPENDENT_TRAINING_GATE
- 근거: reference_v2/PROTOCOL.md:13; reference_v3/continuity.py:25

## derivative_continuity_sequence

- 수학적 대상: lim_v_down_0 c_v(x,v,tau,p)=c_v^+ if the stronger trace condition exists
- 판정: **DIAGNOSTIC_ONLY**
- 역할: not identical to right derivative existence/value certification
- 훈련 의존성: no direct derivative-continuity regularization declared
- estimator: positive-v Greek sequences against endpoint
- grid/step: same v sequence
- convergence/acceptance: not a theorem of uniform C1 regularity; no numeric pass threshold
- 기존 기준에 대한 평가: DIAGNOSTIC_ONLY
- 근거: reference_v2/PROTOCOL.md:13; design/PHASE1A_RESEARCH_DESIGN.md:43

## network_v0_penalty_target

- 수학적 대상: R0[c_theta]=c_theta,tau-r c_theta,x-kappa theta c_theta,v^++r c_theta; target=0
- 판정: **PREDECLARED_EXPLICIT**
- 역할: mathematically known zero penalty target
- 훈련 의존성: directly used by L_b at exact v0
- estimator: network AD with declared coordinate map, not MP residual supervision
- grid/step: proposed finite-v boundary minibatch; no Phase1C code executed
- convergence/acceptance: equation defined; optimizer tolerance/weights not fully frozen
- 기존 기준에 대한 평가: EXACT_TARGET_DEFINED_NOT_A_NUMERICAL_REFERENCE_CERTIFICATE
- 근거: design/PHASE1A_RESEARCH_DESIGN.md:41,87,91,99

## reference_v0_compatibility_acceptance

- 수학적 대상: numerical acceptance of R0[c_ref] and its uncertainty
- 판정: **NOT_PREDECLARED**
- 역할: pre-training v0 consistency review obligation
- 훈련 의존성: indirect validation of the model boundary constraint, not a training label
- estimator: time FD minus reference Delta/Vv/price RHS
- grid/step: v2/v3 h_tau/tau=.001,.0005,.00025; MP at fixed cutoff/degree
- convergence/acceptance: missing residual acceptance budget and full time-price uncertainty propagation
- 기존 기준에 대한 평가: PROTOCOL_GAP
- 근거: reference_v2/boundary_pde.py:1,20-23; reference_v3/boundary_pde.py:25; reference_v2/REFERENCE_VALIDATION_REPORT.md

## reference_time_derivative_budget

- 수학적 대상: numerical error budget for c_tau(x,0,tau,p)
- 판정: **NOT_PREDECLARED**
- 역할: missing component of reference residual acceptance
- 훈련 의존성: network AD derivative is a residual component; not a reference supervised time Greek
- estimator: (f_-2-8 f_-1+8 f_1-f_2)/(12h_tau)
- grid/step: three original time steps; no two-axis uncertainty acceptance specified
- convergence/acceptance: T_C and T_nu do not uniquely define a c_tau budget
- 기존 기준에 대한 평가: PROTOCOL_GAP
- 근거: design/REFERENCE_ENGINE_SPEC.md:57,76; reference_v3/boundary_pde.py:17-25


## 유일한 implicit derivation

고정 x,K에서 c_x=(S/K)Delta=e^x Delta이므로 |delta c_x|=e^x|delta Delta|입니다. 이미 주어진 T_Delta를 만족하면 T_cx=e^x T_Delta는 유일한 선형 전파입니다. 같은 방식으로 c_z=v_*nu의 기존 budget은 v_*T_nu입니다. 이는 새 residual threshold가 아니라 이미 고정된 component budget의 coordinate transform입니다. 아직 선언되지 않은 c_tau budget을 이 식으로 채울 수는 없습니다.

finite-x 240 positive-v trace와 v_max210은 60점 중복, 합집합390입니다. v0 210점은 가격/Delta/right-Vv가 수치적으로 해결된 reference population입니다. finite-x/v0 corner의 가격은 v0 210 population에 이미 포함되며 새로운 독립 label을 만들지 않습니다. 이 수는 v4에서 원래 기준으로 평가된 결과를 인용한 것이고 이번 단계에서 새 pricing/FD 계산을 하지 않았습니다.
