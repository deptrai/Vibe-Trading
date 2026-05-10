import pytest
from decimal import Decimal
from src.defi_simulator import DeFiSimulator

def test_calculate_gas_fee():
    # Test low gas model
    sim_low = DeFiSimulator(gas_fee_model="low")
    assert sim_low.calculate_gas_fee() == Decimal('0.5')
    assert sim_low.calculate_gas_fee(complexity_multiplier=2.0) == Decimal('1.0')
    
    # Test high gas model
    sim_high = DeFiSimulator(gas_fee_model="high")
    assert sim_high.calculate_gas_fee() == Decimal('10.0')

def test_calculate_slippage():
    sim = DeFiSimulator(slippage_tolerance=0.001)
    
    # Large liquidity, small trade -> low slippage (bounded by tolerance)
    assert sim.calculate_slippage(trade_size=100, pool_liquidity=1000000) == 0.001
    
    # Small liquidity, large trade -> high slippage
    # impact = 1000 / (1000 + 1000) = 0.5
    assert sim.calculate_slippage(trade_size=1000, pool_liquidity=1000) == 0.5

def test_calculate_impermanent_loss():
    sim = DeFiSimulator(track_impermanent_loss=True)
    
    # Price doubled (P_ratio = 2)
    # IL = (2 * sqrt(2)) / (1 + 2) - 1 = (2 * 1.414) / 3 - 1 ≈ 0.942 - 1 = -0.057
    il = sim.calculate_impermanent_loss(price_ratio=2.0)
    assert float(il) < 0
    assert round(float(il), 3) == -0.057
    
    # Price halved (P_ratio = 0.5)
    il_half = sim.calculate_impermanent_loss(price_ratio=0.5)
    assert round(float(il_half), 3) == -0.057

def test_apply_defi_impact():
    sim = DeFiSimulator(gas_fee_model="standard", slippage_tolerance=0.01)
    # standard gas = 2.0
    # gas_impact = 2.0 / 1000 = 0.002
    # slippage = 100 / (1000 + 100) ≈ 0.09
    # il (price_ratio 1.0) = 0
    
    initial_return = 0.10 # 10%
    final_return = sim.apply_defi_impact(
        trade_return=initial_return,
        trade_size=100,
        pool_liquidity=1000,
        price_ratio=1.0,
        initial_capital=1000
    )
    
    # expected total impact ≈ 0.002 + 0.0909 + 0 ≈ 0.0929
    # final_return ≈ 0.10 - 0.0929 ≈ 0.0071
    assert final_return < initial_return
    assert round(final_return, 4) == 0.0071
