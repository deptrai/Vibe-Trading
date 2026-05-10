import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

class PerpetualSimulator:
    """
    Simulation Engine for Perpetual Futures.
    Handles Margin, Liquidation, and Funding Rates logic using Decimal precision.
    """
    def __init__(self, maintenance_margin_ratio: Decimal = Decimal('0.01')):
        self.maintenance_margin_ratio = maintenance_margin_ratio

    def calculate_initial_margin_ratio(self, leverage: Decimal) -> Decimal:
        if leverage <= Decimal('0'):
            raise ValueError("Leverage must be greater than 0.")
        return Decimal('1.0') / leverage

    def calculate_liquidation_price(self, entry_price: Decimal, leverage: Decimal, is_long: bool) -> Decimal:
        imr = self.calculate_initial_margin_ratio(leverage)
        if is_long:
            return entry_price * (Decimal('1') - imr + self.maintenance_margin_ratio)
        else:
            return entry_price * (Decimal('1') + imr - self.maintenance_margin_ratio)

    def check_liquidation(self, mark_price: Decimal, liquidation_price: Decimal, is_long: bool) -> bool:
        """
        Returns True if the position should be liquidated.
        Long positions are liquidated when mark_price falls to or below liquidation_price.
        Short positions are liquidated when mark_price rises to or above liquidation_price.
        """
        if is_long:
            return mark_price <= liquidation_price
        else:
            return mark_price >= liquidation_price

    def calculate_funding_fee(self, position_size: Decimal, funding_rate: Decimal, is_long: bool) -> Decimal:
        """
        Calculates the funding fee PnL adjustment.
        Positive funding rate: longs pay shorts.
        Negative funding rate: shorts pay longs.
        Return value is the adjustment to apply to the trader's balance (negative means they paid).
        """
        fee = position_size * funding_rate
        if is_long:
            return -fee
        else:
            return fee
