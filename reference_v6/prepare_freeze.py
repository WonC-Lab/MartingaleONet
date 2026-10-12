"""Generate prospective inputs and policy artifacts. Never price a case."""
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import numpy
import scipy
from scipy.stats import qmc

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reference_v6'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data):
    p=OUT/name
    if isinstance(data,str):p.write_text(data,encoding='utf-8',newline='\n')
    else:p.write_bytes(data)
def save(name,value):write(name,json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def run():
    if (OUT/'PROTOCOL_FREEZE_RECEIPT.json').exists():raise RuntimeError('Already frozen; create a new version, never rewrite')
    bounds=dict(kappa=[.5,4],theta=[.02,.12],sigma=[.1,.8],rho=[-.9,-.1],r=[0,.08])
    anchors=[(.5,.02,.8,-.9,0),(.5,.12,.8,-.1,.08),(4,.02,.8,-.1,0),
             (4,.12,.8,-.9,.08),(.5,.02,.1,-.1,.08),(.5,.12,.1,-.9,0),
             (4,.02,.1,-.9,.08),(4,.12,.1,-.1,0)]
    blocks=[dict(zip(bounds,p),block_id=i,selection='input_box_anchor') for i,p in enumerate(anchors)]
    unit=qmc.Sobol(d=5,scramble=True,seed=6107).random_base2(m=10)
    counts={'feller_satisfied':0,'feller_violating':0};candidate_audit=[]
    for i,u in enumerate(unit):
        p={k:float(a+(b-a)*z) for k,(a,b),z in zip(bounds,bounds.values(),u)}
        beta=2*p['kappa']*p['theta']/p['sigma']**2
        stratum='feller_satisfied' if beta>=1 else 'feller_violating'
        selected=counts[stratum]<12
        candidate_audit.append(dict(index=i,input=p,feller_ratio=beta,stratum=stratum,selected=selected))
        if selected:
            blocks.append(dict(**p,block_id=len(blocks),selection='stratified_sobol',candidate_index=i));counts[stratum]+=1
        if all(v==12 for v in counts.values()):break
    assert len(blocks)==32 and all(v==12 for v in counts.values())
    state=qmc.Sobol(d=1,scramble=True,seed=6108).random_base2(m=5).ravel()
    rows=[]
    for p in blocks:
        block=p['block_id'];middle_x=(-.7 if block%2==0 else .7) if block<8 else float(-.7+1.4*state[block])
        queries=[(0,1/252,'ATM_SHORT'),(middle_x,.1,'INTERIOR_MEDIUM'),(-1.2,2,'LEFT_COLLAR_LONG'),(1.2,1/252,'RIGHT_COLLAR_SHORT')]
        for j,(x,tau,tag) in enumerate(queries):
            inp={k:p[k] for k in bounds}
            rows.append(dict(case_id=f'v6_{block:02d}_{j}',block_id=block,x=x,v=0,tau=tau,K=1,**inp,
                             stratum=tag,parameter_stratum='feller_satisfied' if 2*p['kappa']*p['theta']/p['sigma']**2>=1 else 'feller_violating',
                             original_partition='CHALLENGE',certification_role='TRAINING_REQUIRED_V0_NOT_EVALUATION_OOD'))
    from reference.certification_grid import deterministic
    from reference_v2.domains import parameter_core
    keys=('x','v','tau','K','kappa','theta','sigma','rho','r')
    old={tuple(c.row()[k] for k in keys) for c in deterministic() if parameter_core(c.p) and 1/252<=c.tau<=2 and (c.v==0 or c.v==.25 or (abs(c.x)==1.2 and c.v>0))}
    assert len(rows)==128 and len({tuple(r[k] for k in keys) for r in rows})==128
    assert not any(tuple(r[k] for k in keys) in old for r in rows)
    write('BOUNDARY_BLINDED_INPUTS.jsonl',''.join(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n' for r in rows))
    inputs_sha=sha(OUT/'BOUNDARY_BLINDED_INPUTS.jsonl')
    write('BOUNDARY_BLINDED_INPUTS.sha256',inputs_sha+'  BOUNDARY_BLINDED_INPUTS.jsonl\n')
    sources=['reference/types.py','reference/route_a.py','reference/route_b.py','reference_v2/high_precision.py','reference_v2/workflow.py','reference_v3/mp.py']
    source_hashes={p:dict(raw_sha256=sha(ROOT/p),canonical_lf_sha256=hashlib.sha256((ROOT/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest()) for p in sources}
    protocol=dict(
        version='limiting-v0-certification-v6.0',state='FROZEN_FOR_REVIEW_EXECUTION_NOT_AUTHORIZED',
        scope='128 new v0 inputs only; no CORE, old boundary sweep, old MP sweep, QuantLib large sweep or training',
        notation=dict(c='V/K',Delta='exp(-x)*c_x',nu='c_v=V_v/K',K=1,v=0,
                      raw_R0='c_tau-r*exp(x)*Delta-kappa*theta*nu+r*c'),
        normalization=dict(tau_star_years='1',v_star='0.04',C_star='1',signed_R_hat='tau_star*R0/C_star',absolute_R_hat='abs(signed_R_hat)',
                           dimensionless_operator='c_t-tau_star*r*c_x-(tau_star*kappa*theta/v_star)*c_z+tau_star*r*c',
                           no_observed_term_max_or_floor=True),
        reference_budgets=dict(T_C='1e-8+1e-6*max(abs(c_E1),abs(c_E2))',T_Delta='2e-6+1e-5*max(abs(Delta_E1),abs(Delta_E2))',
                              T_nu='2e-5+1e-4*max(abs(nu_E1),abs(nu_E2))',two_final_axis_changes_fraction='1/4',
                              freeze_before_residual_decision=True,no_Gamma_requirement=True),
        new_time_budget=dict(formula='T_ctau=T_C/tau_star',status='NEW_PROSPECTIVE_POLICY_NOT_UNIQUELY_IMPLIED_BY_OLD_PROTOCOL',
                             rationale='one characteristic year price-error scale; no fit to previously observed residuals'),
        residual_budget=dict(formula='B_R=tau_star*(T_ctau+abs(r)*exp(x)*T_Delta+abs(kappa*theta)*T_nu+abs(r)*T_C)/C_star'),
        time_stencil=dict(order=4,coefficients=[1,-8,0,8,-1],offsets=[-2,-1,0,1,2],denominator='12*h_tau',
                          j=list(range(6,17)),h_tau='tau/2**j',minimum_tau='float(1/252)',
                          L1_coefficient_sum=18,unique_time_prices_minimum=15,unique_time_prices_maximum=25,
                          minimum_levels=6,maximum_levels=11,terminal_crossing_forbidden=True),
        truncation=dict(D_j='FD5(h_j)',difference='d_j=abs(D_j-D_{j-1})',richardson_finest='d_j/15',
                        richardson_previous_scaled='d_{j-1}/240',richardson_extrapolate='(16*D_j-D_{j-1})/15',
                        accepted_guard='u_trunc_j=max(d_j,d_{j-1}) for j>=2',
                        rationale='order-four leading Richardson factor derived; full observed increments retained as conservative guard, not a rigorous error bound'),
        uncertainty=dict(
            axis_component='u_axis(q)=sum_over_axes max(abs(q_last-q_previous),abs(q_previous-q_preprevious))',
            axes_E1=['cutoff','degree','precision'],axes_E2=['COS_N','COS_L','precision'],
            reference_c='u_c=u_axis(c)+u_round(c)',
            reference_Delta_nu='u_q=u_axis(q)+u_round(q)+u_FD(q), q in {Delta,nu}',
            physical_FD='u_FD=max(last_two_FD_increments)+abs(FD5-analytic)+sum(abs(weights)*stencil_price_uncertainties)',
            u_tau_price='sum(abs([1,-8,0,8,-1])*u_c_at_each_time)/(12*h_tau)',
            u_tau='u_tau_price+u_trunc+u_time_arithmetic_round',
            u_R='u_tau+abs(r*exp(x))*u_Delta+abs(kappa*theta)*u_nu+abs(r)*u_c',u_R_hat='tau_star*u_R/C_star',
            tail_and_quadrature='cutoff/N/L/degree uncertainties already included; do not double count a tail scalar',
            roundoff='eps=2**(1-actual_mp_bit_precision); gamma_m=m*eps/(1-m*eps); u_round=gamma_m*sum(abs(all_signed_summands_and_constants)); m=64*n_integral_or_COS_terms+256',
            time_arithmetic_round='gamma_64*sum(abs(weight_j*c_j))/(12*h_tau), using actual_mp_bit_precision',
            unknown_or_nonfinite='UNRESOLVED; never silently zero',
            no_independence_or_covariance_cancellation=True,no_statistical_confidence_claim=True,
            forward_roundoff_limit='diagnostic operation-count allowance plus mandatory 50/80/120-digit checks; elementary-function interval enclosure not claimed'),
        estimators=dict(E1='genuine MP Lewis, pinned reference_v2/high_precision.py algebra and reference_v3 affine cache',
                        E2='genuine MP independent hyperbolic Riccati COS algebra port from pinned reference/route_b.py; NOT float64 relabeled as MP',
                        implementation_state='targeted runner and MP COS port must be implemented, tested and source-committed AFTER this freeze and before any blinded pricing',
                        shared_risk='same affine Heston model; independent inversion/algebra is numerical triangulation, not a model truth proof',
                        coordinates='parse JSON numeric literals by their canonical decimal strings; S=K*mp.exp(x) at each precision; explicitly override old Integrator.values(S=...) and use exact-MP physical stencils, never default Case.S float',
                        COS_interval='pin base-tau interval for each case/L across all time and physical-S/v stencils; original cumulant interval is heuristic; N/L refinements required'),
        refinement=dict(MP_digits=[50,80,120],quadrature_degrees=[24,40,64],
                        cutoffs=[2**j for j in range(6,21)],COS_N=[4096,8192,16384,32768,65536],COS_L=[16,24,32,48,64],
                        phase_span='old span formula abs(x)+.04+abs(r)*tau+abs(rho)*(v+kappa*theta*tau)/max(sigma,.1); input-only group maximum over shared p/base-tau and all declared stencils allowed',
                        physical_relative_steps=['.02','.01','.005','.0025','.00125','.000625','.0001','.00001','.000001','.0000001'],
                        physical_hS='exp(x)*q',physical_hv='.01*q',right_v_offsets=[0,1,2,3,4],right_v_coefficients=[-25,48,-36,16,-3],
                        axis_decoupling='at least three levels per axis and two final differences; when varying one axis hold the others fixed',
                        selection='earliest qualifying common three-step window followed by one finer confirming step; retain all computed failures; no strongest-looking pair selection',
                        ceiling='UNRESOLVED if no confirmed window by j=16 or any reference axis ceiling'),
        acceptance=dict(alpha='1',alpha_rationale='absolute uncertainty sum; zero must belong to numerical consistency band; no empirical coverage multiplier',
                        level_zero_consistency='abs(R_hat)<=u_R_hat',uncertainty_cap='u_R_hat<=B_R/4',
                        window='all three consecutive levels satisfy zero_consistency and uncertainty_cap',
                        refinement_stability='each last time FD increment <=B_R/4, and ratio last/previous<=1/2 OR both increments <=sum of their two propagated time-price uncertainties',
                        contraction_rationale='one-bit reduction guard, weaker than nominal 1/16 fourth-order asymptotics; explicitly new, not calibrated on residual outcomes',
                        uncertainty_growth='successive u_R_hat ratios <=2 within window',
                        growth_rationale='first derivative absolute stencil amplification doubles when h halves; absolute cap still applies at every window level',
                        confirmation='one additional finer step must yield another qualifying overlapping three-step window',
                        independent_residuals='abs(R_hat_E1-R_hat_E2)<=u_R_hat_E1+u_R_hat_E2 at selected confirming level',
                        components='all c/Delta/nu reference axes, cross-route agreement and physical-FD budgets satisfied; no unresolved amplification or solver flags',
                        classification=dict(PASS='every frozen condition satisfied',NUMERICAL_UNRESOLVED='missing/error/budget/amplification/refinement failure',
                                            RESIDUAL_INCOMPATIBLE='reference and numerical stability criteria pass but abs(R_hat)>u_R_hat',
                                            caution='incompatibility is estimator/model-boundary discrepancy, not automatic proof that Heston PDE is wrong')),
        population=dict(sample_size=128,new_only=True,all_must_PASS=True,REVIEW_REQUIRED_permitted_for_PASS=False,
                        missing_or_solver_failure_blocks=True,primary_population='new blinded128 only; old600 not rescored under new rule',
                        Phase1C='YES only after new128 PASS AND existing CORE/finite trace requirements unchanged AND no other training blocker; never launch training'),
        sampling=dict(parameter_seed=6107,state_seed=6108,sampler='SciPy Owen-scrambled Sobol d=5; fixed first1024 candidates; input-only Feller-stratified selection of12+12 blocks',
                      anchors=anchors,bounds=bounds,blocks=32,queries_per_block=4,strata_counts=dict(Counter(r['parameter_stratum'] for r in rows)),
                      queries='ATM_SHORT(x0,tau1/252), INTERIOR_MEDIUM(x[-.7,.7],tau.1), LEFT_COLLAR_LONG(x-1.2,tau2), RIGHT_COLLAR_SHORT(x1.2,tau1/252)',
                      candidates_examined=len(candidate_audit),zero_overlap_original_boundary600=True,
                      original_partition_preserved=True,no_evaluation_OOD=True,no_IID_population_confidence_claim=True,
                      environment=dict(numpy=numpy.__version__,scipy=scipy.__version__),input_sha256=inputs_sha),
        stopping=dict(case_CPU_seconds=1800,batch_wall_seconds=28800,workers_max=4,raw_checkpoint_before_stop=True,
                      no_automatic_extra_grid=True,algorithmic_stop='frozen first-window-plus-confirmation rule',
                      cost_budget_is_not_accuracy_threshold=True),
        reproducibility=dict(reference_sources=source_hashes,policy_code_sha256=sha(OUT/'policy.py'),generator_code_sha256=sha(Path(__file__)),
                             serialization='UTF8 LF; reference_v6/.gitattributes enforces identical Git transport',
                             old_gate_sources={n:sha(ROOT/n) for n in ['reference_v4/FINAL_GATE_DECISION.json','reference_v4/RECONCILIATION_SUMMARY.json']}),
        corruption_policy='any frozen math/coding bug invalidates entire run; newv6.1 freeze and unopened inputs, not threshold patch',
        execution_authorization='NOT_GRANTED; STOP_AFTER_FREEZE')
    save('BOUNDARY_CERT_PROTOCOL.json',protocol)
    save('INPUT_SELECTION_AUDIT.json',dict(candidates=candidate_audit,blocks=blocks,counts=protocol['sampling']['strata_counts'],selection_uses_numerical_outcomes=False))
    print('Created protocol and128 new inputs. Parameter strata:',protocol['sampling']['strata_counts'])

if __name__=='__main__':run()
