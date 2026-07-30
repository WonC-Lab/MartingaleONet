import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import time
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt

plt.style.use('seaborn-v0_8-paper' if 'seaborn-v0_8-paper' in plt.style.available else 'default')
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10

class MultiAssetBasketDeepONet(nn.Module):
    """
    Multi-Asset DeepONet for Basket Options under Correlated Stochastic Volatility.
    Branch Input: [vol1, vol2, correlation_rho, r]
    Trunk Input:  [S1, S2, K_basket, T]
    Output:       Basket Call Option Price V(S1, S2, K, T)
    """
    def __init__(self, branch_dim=4, trunk_dim=4, hidden_dim=128, p=64):
        super().__init__()
        self.branch_net = nn.Sequential(
            nn.Linear(branch_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, p)
        )
        self.trunk_net = nn.Sequential(
            nn.Linear(trunk_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, p)
        )
        self.bias = nn.Parameter(torch.zeros(1))
        
    def forward(self, branch_input, trunk_input):
        b = self.branch_net(branch_input)
        t = self.trunk_net(trunk_input)
        val = torch.sum(b * t, dim=1, keepdim=True) + self.bias
        return torch.relu(val)

def simulate_basket_option_mc(S1_0, S2_0, w1, w2, K, T, r, sigma1, sigma2, rho, N_mc=15000):
    """
    Monte Carlo solver for 2-asset European Basket Call option: Payoff = max(w1*S1_T + w2*S2_T - K, 0)
    """
    dt = T
    z1 = np.random.randn(N_mc)
    z2 = rho * z1 + np.sqrt(1 - rho**2) * np.random.randn(N_mc)
    
    S1_T = S1_0 * np.exp((r - 0.5 * sigma1**2) * dt + sigma1 * np.sqrt(dt) * z1)
    S2_T = S2_0 * np.exp((r - 0.5 * sigma2**2) * dt + sigma2 * np.sqrt(dt) * z2)
    
    basket_T = w1 * S1_T + w2 * S2_T
    payoff = np.maximum(basket_T - K, 0.0)
    price = np.exp(-r * T) * np.mean(payoff)
    return price

def run_experiment_multi_asset():
    print("\n========================================================================")
    print("=== [Paper 1 - Exp 3] Multi-Asset Basket Option & Cross-Correlation  ===")
    print("========================================================================")
    
    np.random.seed(2026)
    torch.manual_seed(2026)
    
    N_samples = 600
    branch_data = []
    trunk_data = []
    price_targets = []
    
    print("Generating Multi-Asset Basket Option Ground Truth via Monte Carlo...")
    for i in range(N_samples):
        sigma1 = np.random.uniform(0.15, 0.35) # e.g., SPY vol
        sigma2 = np.random.uniform(0.20, 0.40) # e.g., QQQ vol
        rho = np.random.uniform(0.3, 0.9)      # Cross-asset correlation
        r = 0.03
        
        S1 = np.random.uniform(80.0, 120.0)
        S2 = np.random.uniform(80.0, 120.0)
        K = 100.0
        T = np.random.uniform(0.2, 1.5)
        
        c_price = simulate_basket_option_mc(S1, S2, 0.5, 0.5, K, T, r, sigma1, sigma2, rho, N_mc=10000)
        
        branch_data.append([sigma1, sigma2, rho, r])
        trunk_data.append([S1, S2, K, T])
        price_targets.append([c_price])
        
    branch_t = torch.tensor(branch_data, dtype=torch.float32)
    trunk_t = torch.tensor(trunk_data, dtype=torch.float32)
    target_t = torch.tensor(price_targets, dtype=torch.float32)
    
    # Train Multi-Asset DeepONet
    model = MultiAssetBasketDeepONet(branch_dim=4, trunk_dim=4, hidden_dim=128, p=64)
    optimizer = optim.Adam(model.parameters(), lr=2e-3)
    
    for epoch in range(1, 401):
        optimizer.zero_grad()
        pred = model(branch_t, trunk_t)
        loss = torch.mean((pred - target_t) ** 2)
        loss.backward()
        optimizer.step()
        
    print(f"Multi-Asset DeepONet Trained. Final Loss: {loss.item():.6e}")
    
    with torch.no_grad():
        preds = model(branch_t, trunk_t).numpy()
    targets = target_t.numpy()
    
    rmse = float(np.sqrt(np.mean((preds - targets)**2)))
    mape = float(np.mean(np.abs((preds - targets) / (targets + 1e-5))) * 100.0)
    
    print(f"  Multi-Asset Pricing Error: RMSE = ${rmse:.4f} | MAPE = {mape:.2f}%")
    
    # Generate Plot fig6
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    max_val = float(np.max(targets))
    # Left: Parity Plot
    axes[0].scatter(targets.flatten(), preds.flatten(), alpha=0.5, color='#2ca02c', s=20)
    axes[0].plot([0, max_val], [0, max_val], 'r--', label='Perfect Fit')
    axes[0].set_title('Multi-Asset Basket Option Price Parity (SPY + QQQ)', fontweight='bold')
    axes[0].set_xlabel('Ground-Truth Monte Carlo Price ($)')
    axes[0].set_ylabel('MartingaleONet Predicted Price ($)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Right: Cross-Asset Correlation Sensitivity (Option Price vs Rho)
    rhos = np.linspace(0.1, 0.95, 50)
    prices_rho_mc = [simulate_basket_option_mc(100.0, 100.0, 0.5, 0.5, 100.0, 1.0, 0.03, 0.25, 0.30, r_val, N_mc=15000) for r_val in rhos]
    
    br_rho = torch.tensor([[0.25, 0.30, r_val, 0.03] for r_val in rhos], dtype=torch.float32)
    tr_rho = torch.tensor([[100.0, 100.0, 100.0, 1.0] for _ in rhos], dtype=torch.float32)
    with torch.no_grad():
        prices_rho_deeponet = model(br_rho, tr_rho).numpy().flatten()
        
    axes[1].plot(rhos, prices_rho_mc, 'o-', color='black', label='Ground-Truth Monte Carlo', markersize=4)
    axes[1].plot(rhos, prices_rho_deeponet, 's-', color='#2ca02c', label='MartingaleONet Prediction', markersize=4)
    axes[1].set_title('Basket Option Sensitivity wrt Cross-Asset Correlation ($\\rho_{12}$)', fontweight='bold')
    axes[1].set_xlabel('Cross-Asset Correlation $\\rho_{12}$')
    axes[1].set_ylabel('Basket Option Price ($)')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    out_fig = 'fig6_multi_asset_basket_correlation.png'
    plt.savefig(out_fig, dpi=300)
    plt.close()
    print(f"Saved figure {out_fig}")
    
    res = {'multi_asset_rmse': rmse, 'multi_asset_mape': mape}
    with open('multi_asset_results.json', 'w') as f:
        json.dump(res, f, indent=2)
        
    return res

if __name__ == '__main__':
    run_experiment_multi_asset()
