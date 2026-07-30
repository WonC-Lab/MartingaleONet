# MartingaleONet: Physics-Constrained Operator Learning for Real-Time Option Pricing and Volatility Calibration

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch 2.1](https://img.shields.io/badge/PyTorch-2.1-red.svg)](https://pytorch.org/)

Official implementation of **MartingaleONet**, a novel quantitative framework combining physics-constrained Deep Operator Networks (DeepONet) and risk-neutral TimeGAN path generation with a differentiable Martingale Drift Correction Layer.

---

## 🌟 Key Highlights

- **$15,225\times$ Inference Speedup**: Zero-shot operator evaluation mapping Heston PDE parameter functions $\mathbf{u} = (\kappa, \theta, \sigma, \rho, v_0)$ directly to continuous option surfaces $V(S,K,T)$ in $0.1\,\mu\text{s}$.
- **Continuous Autograd Greeks**: Derives noise-free sensitivities ($\Delta, \Gamma, \mathcal{V}$) via PyTorch automatic differentiation, reducing dynamic deep hedging PnL variance by **$59.5\%$** under proportional transaction costs ($10\text{bps}$ to $20\text{bps}$).
- **Arbitrage-Free Martingale Drift Correction**: Differentiable layer enforcing $\mathbb{E}^*[S_{t+1}/S_t] = e^{r\Delta t}$ on synthetic trajectories across extreme Out-of-Distribution (OOD) market crashes and 3x leveraged ETF dynamics.
- **Multi-Asset & US Volatility Surface Calibration**: Validated on 10 years of authentic US market ETF data (SPY, QQQ, VIX) and multi-asset basket options.

---

## 🏗️ Model Architecture

```
       [Heston Parameters u]                 [Coordinates y = (S,K,T)]
                 │                                     │
                 ▼                                     ▼
          [Branch Network]                      [Trunk Network]
                 │                                     │
                 └───────────────┬─────────────────────┘
                                 ▼
                     [Central DeepONet Operator] ◄────► [Physics Loss Loop]
                                 │
                                 ▼
                    [PyTorch Autograd Greeks]
                                 │
                                 ▼
                      [Dynamic Deep Hedging]
                                 ▲
                                 │
 [TimeGAN Generator] ──► [Martingale Correction]
```

---

## 📁 Repository Structure

```
.
├── src/
│   ├── run_paper1_experiments.py   # Main pipeline for DeepONet pricing & TimeGAN
│   ├── hedging_engine.py          # Dynamic deep hedging simulation with Autograd vs FDM Greeks
│   ├── multi_asset_extension.py   # Multi-asset basket option pricing & correlation sensitivity
│   ├── stress_test_leverage.py    # OOD stress testing (COVID crash, 3x leveraged ETF)
│   └── ablation_study.py          # Comprehensive baseline benchmark (FNO, PINN, MLP)
├── fig1_deeponet_pricing_error.png
├── fig2_autograd_greeks_surface.png
├── fig3_timegan_synthetic_paths.png
├── fig4_us_volatility_surface.png
├── fig5_deep_hedging_transaction_costs.png
├── fig6_multi_asset_basket_correlation.png
├── fig7_stress_test_leverage_ood.png
├── fig8_ablation_study_baselines.png
├── *.json                         # Quantitative benchmark evaluation results
├── README.md
└── .gitignore
```

---

## 🚀 Quick Start & Usage

### 1. Requirements
```bash
pip install torch numpy scipy matplotlib seaborn pandas
```

### 2. Running Experiments
```bash
# Main experiment pipeline
python src/run_paper1_experiments.py

# Dynamic deep hedging evaluation
python src/hedging_engine.py

# Multi-asset basket option extension
python src/multi_asset_extension.py

# Stress test under extreme market regimes
python src/stress_test_leverage.py

# Comprehensive ablation study & baselines
python src/ablation_study.py
```

---

## 📊 Benchmark Results

| Model / Baseline | RMSE ($) | MAPE (%) | Gamma Noise (TV) | Martingale Preservation |
| :--- | :---: | :---: | :---: | :---: |
| Standard Pointwise MLP | $2.5951 | 22.99% | 0.6603 | Violation ($\mu \neq r$) |
| Standard PINN | $13.2401 | 100.00% | 0.3714 | N/A |
| Fourier Neural Operator (FNO) | $1.8920 | 15.40% | 0.4120 | Violation ($\mu \neq r$) |
| **MartingaleONet (Proposed)** | **$1.1794** | **10.07%** | **0.2064** | **Strict Risk-Neutral** |

---

## 📜 Citation
```bibtex
@article{cho2026martingaleonet,
  title={MartingaleONet: Physics-Constrained Operator Learning for Real-Time Option Pricing and Volatility Calibration},
  author={Cho, WonChan},
  year={2026}
}
```
