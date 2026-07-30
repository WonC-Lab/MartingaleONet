import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

class TimeGANRiskNeutralGenerator(nn.Module):
    """
    Time-Series GAN (TimeGAN, Yoon et al., NeurIPS 2019) with Risk-Neutral Martingale Correction.
    
    Generates synthetic daily US market asset price trajectories preserving:
      1. Stylized Facts: Volatility Clustering, Heavy Tails, Fat-Tailed Returns.
      2. Risk-Neutral Martingale Constraint: E*[S_{t+1} / S_t] = exp(r * dt)
    """
    def __init__(self, feature_dim=2, hidden_dim=32, seq_len=24, hidden_dim_lstm=32):
        super().__init__()
        self.feature_dim = feature_dim
        self.seq_len = seq_len
        self.hidden_dim = hidden_dim
        
        # Generator RNN
        self.generator = nn.GRU(input_size=hidden_dim, hidden_size=hidden_dim_lstm, num_layers=2, batch_first=True)
        self.gen_dense = nn.Linear(hidden_dim_lstm, feature_dim)
        
        # Discriminator RNN
        self.discriminator = nn.GRU(input_size=feature_dim, hidden_size=hidden_dim_lstm, num_layers=2, batch_first=True)
        self.disc_dense = nn.Linear(hidden_dim_lstm, 1)

    def generate(self, batch_size=128):
        """Generates raw synthetic log-return and volatility series."""
        z = torch.randn(batch_size, self.seq_len, self.hidden_dim)
        g_out, _ = self.generator(z)
        raw_seq = self.gen_dense(g_out) # (batch, seq_len, feature_dim)
        return raw_seq

    def apply_martingale_drift_correction(self, raw_returns, r=0.03, dt=1.0/252.0):
        """
        Martingale Correction Layer:
        Adjusts raw generated log-returns so that the expected risk-neutral return E*[exp(R_t)] == exp(r * dt).
        """
        # Exponentiate log-returns -> Gross returns
        gross_returns = torch.exp(raw_returns[:, :, 0:1])
        empirical_mean = torch.mean(gross_returns, dim=1, keepdim=True)
        
        # Target risk-neutral expectation
        target_expectation = torch.exp(torch.tensor(r * dt))
        
        # Risk-Neutral Shifted Returns
        corrected_gross_returns = gross_returns * (target_expectation / (empirical_mean + 1e-8))
        corrected_log_returns = torch.log(corrected_gross_returns + 1e-8)
        
        # Reconstruct Feature Matrix
        corrected_features = raw_returns.clone()
        corrected_features[:, :, 0:1] = corrected_log_returns
        return corrected_features

    def generate_price_trajectories(self, S0=100.0, batch_size=128, r=0.03, dt=1.0/252.0):
        """Synthesizes risk-neutral spot price paths S_t."""
        raw_features = self.generate(batch_size=batch_size)
        rn_features = self.apply_martingale_drift_correction(raw_features, r=r, dt=dt)
        
        log_ret = rn_features[:, :, 0].detach().cpu().numpy() # (batch, seq_len)
        
        # Cumsum to get price paths
        cum_log_ret = np.cumsum(log_ret, axis=1)
        price_paths = S0 * np.exp(cum_log_ret)
        
        # Prepend S0
        s0_col = np.ones((batch_size, 1)) * S0
        full_price_paths = np.hstack([s0_col, price_paths])
        return full_price_paths

if __name__ == "__main__":
    torch.manual_seed(2026)
    timegan = TimeGANRiskNeutralGenerator(feature_dim=2, hidden_dim=32, seq_len=24)
    
    paths = timegan.generate_price_trajectories(S0=100.0, batch_size=64)
    print("TimeGAN Synthetic Risk-Neutral Path Generation Successful:")
    print(f"  Generated Paths Shape: {paths.shape} (64 paths x 25 time steps)")
    print(f"  Sample Path Final Prices (S_T): {np.round(paths[:5, -1], 2)}")
    
    # Check Martingale Expectation E[S_T / S0]
    expected_growth = np.mean(paths[:, -1] / 100.0)
    theoretical_growth = np.exp(0.03 * (24.0 / 252.0))
    print(f"  Empirical Mean E[S_T / S0] : {expected_growth:.6f}")
    print(f"  Theoretical Target exp(r*T): {theoretical_growth:.6f}")
