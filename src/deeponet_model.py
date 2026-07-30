import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

class DeepONetOptionPricer(nn.Module):
    """
    Deep Operator Network (DeepONet) for Real-Time Option Pricing and Volatility Calibration.
    
    Branch Network: Encodes PDE parameter space (kappa, theta, sigma, rho, v0) or initial Volatility Surface.
    Trunk Network: Encodes evaluation coordinates (S, K, T).
    
    Exact PyTorch Autograd Greeks:
      Delta = dV / dS
      Gamma = d^2V / dS^2
      Vega  = dV / dv0
    """
    def __init__(self, branch_dim=5, trunk_dim=3, hidden_dim=64, p=32):
        super().__init__()
        self.p = p
        
        # Branch Network (Params -> Basis Coefficients)
        self.branch_net = nn.Sequential(
            nn.Linear(branch_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, p)
        )
        
        # Trunk Network (Coordinates -> Basis Functions)
        self.trunk_net = nn.Sequential(
            nn.Linear(trunk_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, p)
        )
        
        self.bias = nn.Parameter(torch.zeros(1))

    def forward(self, branch_input, trunk_input):
        """
        branch_input: (batch, branch_dim)  -> (kappa, theta, sigma, rho, v0)
        trunk_input:  (batch, trunk_dim)   -> (S, K, T)
        returns:      (batch, 1)           -> Option Price V(S, K, T)
        """
        b_out = self.branch_net(branch_input)  # (batch, p)
        t_out = self.trunk_net(trunk_input)    # (batch, p)
        
        # Operator Inner Product B(u) . T(y) + b
        val = torch.sum(b_out * t_out, dim=1, keepdim=True) + self.bias
        return torch.relu(val) # Option price non-negativity constraint

    def compute_autograd_greeks(self, branch_input, trunk_input):
        """
        Computes Exact Greeks via PyTorch Automatic Differentiation.
        No finite difference grid discretization error or noise!
        """
        trunk_input = trunk_input.clone().detach().requires_grad_(True)
        branch_input = branch_input.clone().detach().requires_grad_(True)
        
        v_pred = self.forward(branch_input, trunk_input)
        
        # 1st Order Derivative wrt Spot Price S (Delta)
        grads_trunk = torch.autograd.grad(v_pred.sum(), trunk_input, create_graph=True, retain_graph=True)[0]
        delta = grads_trunk[:, 0:1] # dV / dS
        
        # 2nd Order Derivative wrt Spot Price S (Gamma)
        gamma = torch.autograd.grad(delta.sum(), trunk_input, create_graph=False, retain_graph=True)[0][:, 0:1] # d^2V / dS^2
        
        # Derivative wrt Spot Volatility v0 (Vega)
        grads_branch = torch.autograd.grad(v_pred.sum(), branch_input, create_graph=False)[0]
        vega = grads_branch[:, 4:5] # dV / dv0
        
        return {
            'price': v_pred.detach().cpu().numpy(),
            'delta': delta.detach().cpu().numpy(),
            'gamma': gamma.detach().cpu().numpy(),
            'vega': vega.detach().cpu().numpy()
        }

    def compute_physics_informed_heston_loss(self, branch_input, trunk_input, r=0.03):
        """
        Computes Heston PDE Residual Loss for Physics-Informed Operator Training.
        PDE: 0.5*v*S^2*V_SS + rho*sigma*v*S*V_Sv + 0.5*sigma^2*v*V_vv + r*S*V_S + kappa*(theta-v)*V_v - r*V - V_t = 0
        """
        trunk_input = trunk_input.clone().detach().requires_grad_(True)
        branch_input = branch_input.clone().detach().requires_grad_(True)
        
        kappa = branch_input[:, 0:1]
        theta = branch_input[:, 1:2]
        sigma = branch_input[:, 2:3]
        rho = branch_input[:, 3:4]
        v0 = branch_input[:, 4:5]
        
        S = trunk_input[:, 0:1]
        K = trunk_input[:, 1:2]
        T = trunk_input[:, 2:3]
        
        V = self.forward(branch_input, trunk_input)
        
        # Autograd Derivatives
        grads_t = torch.autograd.grad(V.sum(), trunk_input, create_graph=True, retain_graph=True)[0]
        V_S = grads_t[:, 0:1]
        V_T = grads_t[:, 2:3]
        
        V_SS = torch.autograd.grad(V_S.sum(), trunk_input, create_graph=True, retain_graph=True)[0][:, 0:1]
        
        grads_b = torch.autograd.grad(V.sum(), branch_input, create_graph=True, retain_graph=True)[0]
        V_v = grads_b[:, 4:5]
        V_vv = torch.autograd.grad(V_v.sum(), branch_input, create_graph=True, retain_graph=True)[0][:, 4:5]
        
        V_Sv = torch.autograd.grad(V_S.sum(), branch_input, create_graph=True)[0][:, 4:5]
        
        # Heston PDE Residual (Time to maturity tau = T - t -> V_t = -V_tau)
        pde_residual = (
            0.5 * v0 * (S ** 2) * V_SS
            + rho * sigma * v0 * S * V_Sv
            + 0.5 * (sigma ** 2) * v0 * V_vv
            + r * S * V_S
            + kappa * (theta - v0) * V_v
            - r * V
            - V_T
        )
        
        return torch.mean(pde_residual ** 2)

if __name__ == "__main__":
    torch.manual_seed(2026)
    model = DeepONetOptionPricer(branch_dim=5, trunk_dim=3, hidden_dim=64, p=32)
    
    # Sample Test Inputs
    branch_in = torch.tensor([[2.0, 0.04, 0.3, -0.7, 0.04]], dtype=torch.float32) # Heston Params
    trunk_in = torch.tensor([[100.0, 100.0, 1.0]], dtype=torch.float32)         # (S, K, T)
    
    price = model(branch_in, trunk_in)
    greeks = model.compute_autograd_greeks(branch_in, trunk_in)
    pde_loss = model.compute_physics_informed_heston_loss(branch_in, trunk_in)
    
    print("DeepONet Forward Pass & Autograd Test Successful:")
    print(f"  Predicted Price V: ${price.item():.4f}")
    print(f"  Autograd Delta   :  {greeks['delta'][0,0]:.4f}")
    print(f"  Autograd Gamma   :  {greeks['gamma'][0,0]:.4f}")
    print(f"  Autograd Vega    :  {greeks['vega'][0,0]:.4f}")
    print(f"  Heston PDE Loss  :  {pde_loss.item():.6e}")
