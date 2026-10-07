from dataclasses import dataclass, asdict
import math

@dataclass(frozen=True)
class Parameters:
    kappa: float = 2.
    theta: float = .04
    sigma: float = .3
    rho: float = -.7
    r: float = .03

@dataclass(frozen=True)
class Case:
    x: float = 0.
    v: float = .04
    tau: float = 1.
    K: float = 1.
    p: Parameters = Parameters()
    label: str = "unspecified"

    @property
    def S(self):
        return self.K * math.exp(self.x)

    def row(self):
        return dict(S=self.S, K=self.K, x=self.x, v=self.v, tau=self.tau,
                    **asdict(self.p), label=self.label)

@dataclass
class Estimate:
    price: float
    Delta: float
    Gamma: float
    Vv: float
    Vega_s: float
    diagnostics: dict

    def row(self):
        return asdict(self)
