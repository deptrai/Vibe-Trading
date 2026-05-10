import pytest
from decimal import Decimal
from src.perpetual_simulator import PerpetualSimulator

def test_initial_margin_ratio():
    simulator = PerpetualSimulator()
    # 10x leverage -> IMR should be 0.1
    imr = simulator.calculate_initial_margin_ratio(Decimal('10.0'))
    assert imr == Decimal('0.1')
    
    # 50x leverage -> IMR should be 0.02
    imr = simulator.calculate_initial_margin_ratio(Decimal('50.0'))
    assert imr == Decimal('0.02')

def test_liquidation_price_long():
    simulator = PerpetualSimulator(maintenance_margin_ratio=Decimal('0.01'))
    # entry = 1000, leverage = 10 (IMR=0.1, MMR=0.01)
    # Long Liq Price = entry * (1 - IMR + MMR) = 1000 * (1 - 0.1 + 0.01) = 1000 * 0.91 = 910
    liq_price = simulator.calculate_liquidation_price(
        entry_price=Decimal('1000.0'),
        leverage=Decimal('10.0'),
        is_long=True
    )
    assert liq_price == Decimal('910.0')

def test_liquidation_price_short():
    simulator = PerpetualSimulator(maintenance_margin_ratio=Decimal('0.01'))
    # entry = 1000, leverage = 10 (IMR=0.1, MMR=0.01)
    # Short Liq Price = entry * (1 + IMR - MMR) = 1000 * (1 + 0.1 - 0.01) = 1000 * 1.09 = 1090
    liq_price = simulator.calculate_liquidation_price(
        entry_price=Decimal('1000.0'),
        leverage=Decimal('10.0'),
        is_long=False
    )
    assert liq_price == Decimal('1090.0')

def test_check_liquidation():
    simulator = PerpetualSimulator()
    # Long position, Liq Price = 910
    is_liquidated = simulator.check_liquidation(mark_price=Decimal('900.0'), liquidation_price=Decimal('910.0'), is_long=True)
    assert is_liquidated is True
    
    is_liquidated = simulator.check_liquidation(mark_price=Decimal('920.0'), liquidation_price=Decimal('910.0'), is_long=True)
    assert is_liquidated is False

    # Short position, Liq Price = 1090
    is_liquidated = simulator.check_liquidation(mark_price=Decimal('1100.0'), liquidation_price=Decimal('1090.0'), is_long=False)
    assert is_liquidated is True

    is_liquidated = simulator.check_liquidation(mark_price=Decimal('1080.0'), liquidation_price=Decimal('1090.0'), is_long=False)
    assert is_liquidated is False

def test_calculate_funding_fee():
    simulator = PerpetualSimulator()
    # Funding fee = position_size * funding_rate
    # Positive funding rate means Long pays Short
    fee_long = simulator.calculate_funding_fee(position_size=Decimal('10000.0'), funding_rate=Decimal('0.0001'), is_long=True)
    assert fee_long == Decimal('-1.0') # Long pays, so it's a negative fee

    fee_short = simulator.calculate_funding_fee(position_size=Decimal('10000.0'), funding_rate=Decimal('0.0001'), is_long=False)
    assert fee_short == Decimal('1.0') # Short receives, so it's positive

    # Negative funding rate means Short pays Long
    fee_long_neg = simulator.calculate_funding_fee(position_size=Decimal('10000.0'), funding_rate=Decimal('-0.0001'), is_long=True)
    assert fee_long_neg == Decimal('1.0')

    fee_short_neg = simulator.calculate_funding_fee(position_size=Decimal('10000.0'), funding_rate=Decimal('-0.0001'), is_long=False)
    assert fee_short_neg == Decimal('-1.0')
