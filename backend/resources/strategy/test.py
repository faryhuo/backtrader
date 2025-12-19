"""
Grid Trading Strategy - Range Trading

This strategy places buy and sell orders at preset price levels (grids).
It profits from price oscillation by buying at lower grids and selling at
higher grids, effectively implementing a "buy low, sell high" approach.

Suitable for: Sideways/ranging markets, crypto, ETFs, forex
Difficulty: Intermediate
"""
import backtrader as bt


class UserStrategy(bt.Strategy):
    """
    Grid Trading Strategy
    
    Parameters:
        grid_count: Number of grid levels (default: 10)
        upper_price: Upper price boundary (default: 110)
        lower_price: Lower price boundary (default: 90)
        total_investment: Total investment amount (default: 10000)
    """
    params = (
        ("grid_count", 10),
        ("upper_price", 110.0),
        ("lower_price", 90.0),
        ("total_investment", 10000.0),
    )

    def __init__(self):
        self.grid_size = (self.p.upper_price - self.p.lower_price) / self.p.grid_count
        self.position_per_grid = self.p.total_investment / self.p.grid_count / self.p.lower_price
        
        # Track which grids have been filled
        self.grid_positions = {}
        
    def get_grid_level(self, price):
        """Calculate which grid level a price falls into."""
        if price < self.p.lower_price:
            return 0
        if price > self.p.upper_price:
            return self.p.grid_count
        return int((price - self.p.lower_price) / self.grid_size)
    
    def next(self):
        current_price = self.data.close[0]
        prev_price = self.data.close[-1] if len(self.data) > 1 else current_price
        
        current_level = self.get_grid_level(current_price)
        prev_level = self.get_grid_level(prev_price)
        
        # Price moved down - buy opportunity
        if current_level < prev_level:
            for level in range(current_level, prev_level):
                if level not in self.grid_positions or not self.grid_positions[level]:
                    size = int(self.position_per_grid)
                    if size > 0:
                        self.buy(size=size)
                        self.grid_positions[level] = True
        
        # Price moved up - sell opportunity
        elif current_level > prev_level:
            for level in range(prev_level, current_level):
                if level in self.grid_positions and self.grid_positions[level]:
                    size = int(self.position_per_grid)
                    if size > 0 and self.position.size >= size:
                        self.sell(size=size)
                        self.grid_positions[level] = False
