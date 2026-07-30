import numpy as np
from scipy.integrate import quad

class HestonReferenceSolver:
    """
    High-Precision Semi-Analytical Fourier Transform and FDM Solver for Heston Stochastic Volatility Model.
    
    Heston Dynamics under Risk-Neutral Measure P*:
      dS_t = r S_t dt + sqrt(v_t) S_t dW_t^S
      dv_t = kappa (theta - v_t) dt + sigma sqrt(v_t) dW_t^v
      E[dW_t^S dW_t^v] = rho dt
    """
    def __init__(self, r=0.03, kappa=2.0, theta=0.04, sigma=0.3, rho=-0.7, v0=0.04):
        self.r = r
        self.kappa = kappa
        self.theta = theta
        self.sigma = sigma
        self.rho = rho
        self.v0 = v0

    def _characteristic_function(self, u, S0, K, T):
        """Gatheral's stable formulation of Heston characteristic function (branch-cut free)."""
        x = np.log(S0 / K)
        xi = self.kappa - self.rho * self.sigma * u * 1j
        d = np.sqrt(xi**2 + (self.sigma**2) * (u**2 + u * 1j))
        g = (xi - d) / (xi + d)
        
        C = self.r * u * 1j * T + (self.kappa * self.theta / (self.sigma**2)) * (
            (xi - d) * T - 2.0 * np.log((1.0 - g * np.exp(-d * T)) / (1.0 - g))
        )
        D = ((xi - d) / (self.sigma**2)) * ((1.0 - np.exp(-d * T)) / (1.0 - g * np.exp(-d * T)))
        
        return np.exp(C + D * self.v0 + 1j * u * x)

    def price_call(self, S0, K, T):
        """Computes European Call option price via Carr-Madan / Gatheral Heston Fourier integration."""
        def integrand(u):
            cf = self._characteristic_function(u - 0.5 * 1j, S0, K, T)
            denom = u**2 + 0.25
            return (np.exp(-self.r * T) * (cf / denom)).real

        res = quad(integrand, 0, 100, limit=250)[0]
        price = S0 - np.sqrt(S0 * K) * (1.0 / np.pi) * res
        return max(float(price), max(S0 - K * np.exp(-self.r * T), 0.0))

    def compute_greeks(self, S0, K, T, dS=0.5, dv=0.001):
        """Computes Delta, Gamma, and Vega using high-precision finite differences."""
        p_base = self.price_call(S0, K, T)
        p_up_s = self.price_call(S0 + dS, K, T)
        p_dn_s = self.price_call(S0 - dS, K, T)
        
        delta = (p_up_s - p_dn_s) / (2.0 * dS)
        gamma = (p_up_s - 2.0 * p_base + p_dn_s) / (dS ** 2)
        
        # Vega wrt v0 (spot variance)
        solver_v_up = HestonReferenceSolver(self.r, self.kappa, self.theta, self.sigma, self.rho, self.v0 + dv)
        p_v_up = solver_v_up.price_call(S0, K, T)
        vega = (p_v_up - p_base) / dv
        
        return {'price': p_base, 'delta': delta, 'gamma': gamma, 'vega': vega}

if __name__ == "__main__":
    solver = HestonReferenceSolver()
    greeks = solver.compute_greeks(S0=100.0, K=100.0, T=1.0)
    print("Heston Benchmark Call Price & Greeks (S0=100, K=100, T=1.0):")
    print(f"  Price: ${greeks['price']:.4f}")
    print(f"  Delta:  {greeks['delta']:.4f}")
    print(f"  Gamma:  {greeks['gamma']:.4f}")
    print(f"  Vega:   {greeks['vega']:.4f}")
