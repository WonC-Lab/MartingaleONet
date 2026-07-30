import os
import sys
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import time
import json
import numpy as np
import pandas as pd
import torch
import torch.optim as optim
import matplotlib.pyplot as plt

from heston_solver import HestonReferenceSolver
from deeponet_model import DeepONetOptionPricer

plt.style.use('seaborn-v0_8-paper' if 'seaborn-v0_8-paper' in plt.style.available else 'default')
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10

def run_experiment_hedging_transaction_costs():
    """
    Experiment 2: Dynamic Deep Hedging under Proportional Transaction Costs.
    Compares MartingaleONet Autograd Greeks vs FDM Greeks vs Unhedged.
    Calculates PnL Variance, Expected Loss, 95% VaR, 95% CVaR under alpha = [0.0, 0.001, 0.002] (0, 10bps, 20bps).
    """
    print("\n========================================================================")
    print("=== [Paper 1 - Exp 2] Dynamic Deep Hedging under Transaction Costs   ===")
    print("========================================================================")
    
    np.random.seed(2026)
    torch.manual_seed(2026)
    
    # 1. Train DeepONet Pricer
    branch_t = torch.tensor([[2.0, 0.04, 0.3, -0.7, 0.04]], dtype=torch.float32)
    
    # Generate synthetic training grid
    S_range = np.linspace(80, 120, 100)
    T_range = np.linspace(0.05, 1.0, 50)
    
    branch_train = []
    trunk_train = []
    target_train = []
    
    solver = HestonReferenceSolver(r=0.03, kappa=2.0, theta=0.04, sigma=0.3, rho=-0.7, v0=0.04)
    
    for s in S_range:
        for t in T_range:
            c = solver.price_call(s, 100.0, t)
            branch_train.append([2.0, 0.04, 0.3, -0.7, 0.04])
            trunk_train.append([s, 100.0, t])
            target_train.append([c])
            
    branch_train_t = torch.tensor(branch_train, dtype=torch.float32)
    trunk_train_t = torch.tensor(trunk_train, dtype=torch.float32)
    target_train_t = torch.tensor(target_train, dtype=torch.float32)
    
    model = DeepONetOptionPricer(branch_dim=5, trunk_dim=3, hidden_dim=64, p=32)
    optimizer = optim.Adam(model.parameters(), lr=3e-3)
    
    for _ in range(150):
        optimizer.zero_grad()
        v_pred = model(branch_train_t, trunk_train_t)
        loss = torch.mean((v_pred - target_train_t) ** 2) + 0.01 * model.compute_physics_informed_heston_loss(branch_train_t, trunk_train_t)
        loss.backward()
        optimizer.step()
        
    print("DeepONet trained successfully for hedging simulation.")
    
    # 2. Simulate Asset Price Paths via Heston Monte Carlo
    N_paths = 200
    N_steps = 30 # 30 daily rebalancing steps
    dt = 1.0 / 252.0
    r = 0.03
    S0 = 100.0
    v0 = 0.04
    K = 100.0
    T_initial = 30.0 / 252.0
    
    paths_S = np.zeros((N_paths, N_steps + 1))
    paths_v = np.zeros((N_paths, N_steps + 1))
    paths_S[:, 0] = S0
    paths_v[:, 0] = v0
    
    kappa, theta, sigma, rho = 2.0, 0.04, 0.3, -0.7
    
    for t_step in range(N_steps):
        z1 = np.random.randn(N_paths)
        z2 = rho * z1 + np.sqrt(1 - rho**2) * np.random.randn(N_paths)
        v_curr = np.maximum(paths_v[:, t_step], 1e-6)
        paths_v[:, t_step + 1] = np.maximum(v_curr + kappa * (theta - v_curr) * dt + sigma * np.sqrt(v_curr * dt) * z2, 1e-6)
        paths_S[:, t_step + 1] = paths_S[:, t_step] * np.exp((r - 0.5 * v_curr) * dt + np.sqrt(v_curr * dt) * z1)
        
    print(f"Simulated {N_paths} Heston paths for dynamic hedging.")
    
    # 3. Dynamic Delta-Vega Hedging with Transaction Costs
    transaction_cost_rates = [0.0, 0.001, 0.002] # 0, 10bps, 20bps
    hedging_results = {}
    
    for tc in transaction_cost_rates:
        tc_key = f"{int(tc*10000)}bps"
        pnl_autograd = []
        pnl_fdm = []
        pnl_unhedged = []
        
        for i in range(N_paths):
            # Short Call Option position
            init_price = solver.price_call(paths_S[i, 0], K, T_initial)
            
            # Initial Hedge
            tr_0 = torch.tensor([[paths_S[i, 0], K, T_initial]], dtype=torch.float32)
            br_0 = torch.tensor([[kappa, theta, sigma, rho, v0]], dtype=torch.float32)
            res_0 = model.compute_autograd_greeks(br_0, tr_0)
            delta_auto_curr = res_0['delta'][0, 0]
            
            # FDM Delta initial
            eps = 0.5
            c_plus = solver.price_call(paths_S[i, 0] + eps, K, T_initial)
            c_minus = solver.price_call(paths_S[i, 0] - eps, K, T_initial)
            delta_fdm_curr = (c_plus - c_minus) / (2 * eps)
            
            cash_auto = init_price - delta_auto_curr * paths_S[i, 0] - tc * paths_S[i, 0] * abs(delta_auto_curr)
            cash_fdm = init_price - delta_fdm_curr * paths_S[i, 0] - tc * paths_S[i, 0] * abs(delta_fdm_curr)
            
            for t_step in range(1, N_steps):
                S_curr = paths_S[i, t_step]
                T_rem = max(T_initial - t_step * dt, 1e-4)
                
                # Rebalance Autograd Delta
                tr_step = torch.tensor([[S_curr, K, T_rem]], dtype=torch.float32)
                br_step = torch.tensor([[kappa, theta, sigma, rho, paths_v[i, t_step]]], dtype=torch.float32)
                res_step = model.compute_autograd_greeks(br_step, tr_step)
                delta_auto_new = res_step['delta'][0, 0]
                
                # Rebalance FDM Delta
                c_p = solver.price_call(S_curr + eps, K, T_rem)
                c_m = solver.price_call(S_curr - eps, K, T_rem)
                delta_fdm_new = (c_p - c_m) / (2 * eps)
                
                # Cash update with interest & transaction costs
                d_delta_auto = delta_auto_new - delta_auto_curr
                cash_auto = cash_auto * np.exp(r * dt) - d_delta_auto * S_curr - tc * S_curr * abs(d_delta_auto)
                delta_auto_curr = delta_auto_new
                
                d_delta_fdm = delta_fdm_new - delta_fdm_curr
                cash_fdm = cash_fdm * np.exp(r * dt) - d_delta_fdm * S_curr - tc * S_curr * abs(d_delta_fdm)
                delta_fdm_curr = delta_fdm_new
                
            # Expiration payoff
            payoff = max(paths_S[i, -1] - K, 0.0)
            final_pnl_auto = cash_auto + delta_auto_curr * paths_S[i, -1] - payoff
            final_pnl_fdm = cash_fdm + delta_fdm_curr * paths_S[i, -1] - payoff
            final_pnl_unhedged = init_price * np.exp(r * T_initial) - payoff
            
            pnl_autograd.append(final_pnl_auto)
            pnl_fdm.append(final_pnl_fdm)
            pnl_unhedged.append(final_pnl_unhedged)
            
        pnl_autograd = np.array(pnl_autograd)
        pnl_fdm = np.array(pnl_fdm)
        pnl_unhedged = np.array(pnl_unhedged)
        
        hedging_results[tc_key] = {
            'auto_std': float(np.std(pnl_autograd)),
            'auto_mean': float(np.mean(pnl_autograd)),
            'auto_var95': float(np.percentile(pnl_autograd, 5)),
            'auto_cvar95': float(np.mean(pnl_autograd[pnl_autograd <= np.percentile(pnl_autograd, 5)])),
            'fdm_std': float(np.std(pnl_fdm)),
            'fdm_mean': float(np.mean(pnl_fdm)),
            'fdm_cvar95': float(np.mean(pnl_fdm[pnl_fdm <= np.percentile(pnl_fdm, 5)])),
            'unhedged_std': float(np.std(pnl_unhedged)),
            'unhedged_cvar95': float(np.mean(pnl_unhedged[pnl_unhedged <= np.percentile(pnl_unhedged, 5)]))
        }
        print(f"  [TC = {tc_key}] MartingaleONet Autograd PnL Std: ${hedging_results[tc_key]['auto_std']:.4f} | CVaR(95%): ${hedging_results[tc_key]['auto_cvar95']:.4f}")
        print(f"                FDM Greeks PnL Std:          ${hedging_results[tc_key]['fdm_std']:.4f} | CVaR(95%): ${hedging_results[tc_key]['fdm_cvar95']:.4f}")
        
    # 4. Generate Plot fig5
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Left: PnL Distribution Comparison (10bps)
    tc_plot = '10bps'
    axes[0].hist(pnl_autograd, bins=40, alpha=0.6, color='#1f77b4', label=f'MartingaleONet Autograd (Std=${hedging_results[tc_plot]["auto_std"]:.2f})')
    axes[0].hist(pnl_fdm, bins=40, alpha=0.5, color='#ff7f0e', label=f'FDM Greeks (Std=${hedging_results[tc_plot]["fdm_std"]:.2f})')
    axes[0].axvline(0, color='black', linestyle='--', linewidth=1)
    axes[0].set_title(f'Dynamic Hedging PnL Distribution (Transaction Cost = {tc_plot})', fontweight='bold')
    axes[0].set_xlabel('Hedging PnL ($)')
    axes[0].set_ylabel('Frequency')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Right: PnL Std vs Transaction Cost Rate
    tc_labels = ['0bps', '10bps', '20bps']
    auto_stds = [hedging_results[k]['auto_std'] for k in tc_labels]
    fdm_stds = [hedging_results[k]['fdm_std'] for k in tc_labels]
    unhedged_stds = [hedging_results[k]['unhedged_std'] for k in tc_labels]
    
    x = np.arange(len(tc_labels))
    width = 0.25
    
    axes[1].bar(x - width, auto_stds, width, label='MartingaleONet Autograd', color='#1f77b4')
    axes[1].bar(x, fdm_stds, width, label='FDM Greeks', color='#ff7f0e')
    axes[1].bar(x + width, unhedged_stds, width, label='Unhedged Position', color='#d62728')
    axes[1].set_title('PnL Standard Deviation vs Transaction Cost Rate', fontweight='bold')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(tc_labels)
    axes[1].set_ylabel('PnL Standard Deviation ($)')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_fig = os.path.join(root_dir, 'fig5_deep_hedging_transaction_costs.png')
    plt.savefig(out_fig, dpi=300)
    plt.close()
    print(f"Saved figure {out_fig}")
    
    with open(os.path.join(root_dir, 'hedging_results.json'), 'w') as f:
        json.dump(hedging_results, f, indent=2)
        
    return hedging_results

if __name__ == '__main__':
    run_experiment_hedging_transaction_costs()
