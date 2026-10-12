"""Numerical checks use synthetic inputs, never the blinded 128 cases."""
import unittest
from decimal import Decimal
from reference_v6.mp_backend import evaluate, hyperbolic_cf, parameters
from reference_v2.high_precision import context, cf
from reference_v6 import policy

ROW={'x':'.13','v':'.05','tau':'.73','kappa':'1.7','theta':'.05','sigma':'.25','rho':'-.4','r':'.02'}


class ExecutorTests(unittest.TestCase):
    def test_independent_characteristic_algebra(self):
        ctx=context(70);p=parameters(ROW)
        for u in ['0','0.3','2','17','301']:
            for shift in [0,-ctx.j/2]:
                argument=ctx.mpf(u)+shift
                a,da=cf(ctx,argument,'.05','.73',p,True)
                b,db=hyperbolic_cf(ctx,argument,'.05','.73',p)
                self.assertLess(abs(a-b),ctx.mpf('1e-60'))
                self.assertLess(abs(da-db),ctx.mpf('1e-60'))

    def test_independent_inversions_and_derivatives(self):
        coords=[('.13','.05','.73')]
        a=evaluate(ROW,'E1',{'dps':50,'degree':24,'cutoff':256,'span':'.75'},coords)
        b=evaluate(ROW,'E2',{'dps':50,'N':512,'L':16},coords)
        for f in ['c','Delta','nu']:
            self.assertLess(abs(Decimal(a['results'][0]['values'][f])-Decimal(b['results'][0]['values'][f])),Decimal('1e-8'))

    def test_stencil_sign_and_scaling(self):
        t=Decimal('.7');h=Decimal('.001')
        self.assertEqual(policy.time_fd5([(t+k*h)**4 for k in [-2,-1,0,1,2]],h),4*t**3)
        self.assertEqual(policy.propagated_time_uncertainty([1]*5,h),Decimal(18)/(12*h))
        self.assertFalse(policy.level_accepts('1e-6','1e-7','1e-4'))
        self.assertFalse(policy.level_accepts(0,'1e-3','1e-4'))

    def test_partial_resume_exact(self):
        cfg={'dps':50,'N':512,'L':16};coords=[('.13','.05','.73')];saved=[];calls=[]
        full=evaluate(ROW,'E2',cfg,coords)
        def stop_midway():
            calls.append(1)
            if len(calls)==3:raise TimeoutError('synthetic resource interruption')
        with self.assertRaises(TimeoutError):
            evaluate(ROW,'E2',cfg,coords,tick=stop_midway,checkpoint=saved.append)
        self.assertEqual(saved[-1]['nodes'],256)
        resumed=evaluate(ROW,'E2',cfg,coords,saved=saved[-1])
        self.assertEqual(full,resumed)

    def test_positive_v_pde_sign(self):
        # A synthetic sigma=0 case checks the time/PDE signs independently
        # without looking at a single blinded v0 residual.
        row={**ROW,'sigma':'0'}
        ctx=context(50);x=ctx.mpf('.13');v=ctx.mpf('.05');t=ctx.mpf('.73');h=ctx.mpf('.00001')
        coords=[(x,v,t+k*h) for k in [-2,-1,0,1,2]]
        z=evaluate(row,'E2',{'dps':50,'N':512,'L':16},coords)
        prices=[Decimal(q['values']['c']) for q in z['results']]
        ctau=policy.time_fd5(prices,str(h));base=z['results'][2]['values']
        # Recover c_xx-c_x = S^2*Gamma through a separate exact-MP spot stencil.
        S=ctx.exp(x);hs=ctx.mpf('.00001')*S
        sp=[(ctx.log(S+k*hs),v,t) for k in [-2,-1,0,1,2]]
        pv=evaluate(row,'E2',{'dps':50,'N':512,'L':16},sp)
        vals=[Decimal(q['values']['c']) for q in pv['results']]
        gamma=(-vals[4]+16*vals[3]-30*vals[2]+16*vals[1]-vals[0])/(12*Decimal(str(hs))**2)
        rhs=Decimal('.5')*Decimal(str(v))*Decimal(str(S))**2*gamma+Decimal('1.7')*(Decimal('.05')-Decimal(str(v)))*Decimal(base['nu'])+Decimal('.02')*Decimal(str(S))*Decimal(base['Delta'])-Decimal('.02')*Decimal(base['c'])
        self.assertLess(abs(ctau-rhs),Decimal('1e-8'))


if __name__=='__main__':unittest.main()
