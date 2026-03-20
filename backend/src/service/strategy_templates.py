"""
Strategy Template Registry and Service.

Provides a collection of classic trading strategy templates with metadata
for users to browse, learn, and import into their own strategies.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional

from src.config.settings import STRATEGY_DIR


# Strategy Categories
TREND_FOLLOWING = "trend_following"
MEAN_REVERSION = "mean_reversion"
STATISTICAL_ARBITRAGE = "statistical_arbitrage"
GRID_TRADING = "grid_trading"

# Difficulty Levels
BEGINNER = "beginner"
INTERMEDIATE = "intermediate"
ADVANCED = "advanced"


@dataclass
class StrategyTemplate:
    """Strategy template metadata and code."""
    id: str
    name: str
    name_zh: str
    category: str
    description: str
    description_zh: str
    difficulty: str
    markets: List[str]
    tags: List[str]
    params: List[Dict[str, str]]
    code: str = ""


# Template definitions with metadata
TEMPLATES: Dict[str, StrategyTemplate] = {}


def _register_template(template: StrategyTemplate) -> None:
    """Register a template in the registry."""
    TEMPLATES[template.id] = template


def _load_template_code(template_id: str) -> str:
    """Load template code from file."""
    template_dir = STRATEGY_DIR / "templates"
    template_file = template_dir / f"{template_id}.py"
    if template_file.exists():
        return template_file.read_text(encoding="utf-8")
    return ""


def _init_templates() -> None:
    """Initialize all strategy templates."""
    
    # MACD Strategy
    _register_template(StrategyTemplate(
        id="macd_strategy",
        name="MACD Crossover Strategy",
        name_zh="MACD 金叉死叉策略",
        category=TREND_FOLLOWING,
        description="Classic trend-following strategy using MACD indicator. Enters long on golden cross (DIF crosses above DEA) and exits on death cross.",
        description_zh="使用MACD指标的经典趋势跟踪策略。通过计算快速和慢速EMA的差值（DIF线）与其信号线（DEA线）的交叉来判断买卖时机。金叉做多，死叉平仓。",
        difficulty=BEGINNER,
        markets=["stocks", "etf", "futures", "crypto"],
        tags=["trend", "momentum", "classic"],
        params=[
            {"name": "fast_period", "default": "12", "description": "Fast EMA period"},
            {"name": "slow_period", "default": "26", "description": "Slow EMA period"},
            {"name": "signal_period", "default": "9", "description": "Signal line period"},
        ]
    ))
    
    # EMA Cross Strategy
    _register_template(StrategyTemplate(
        id="ema_cross",
        name="EMA Crossover Strategy",
        name_zh="EMA 交叉策略",
        category=TREND_FOLLOWING,
        description="Trend-following strategy using EMA crossovers. EMA is more responsive to recent price changes compared to SMA. Long on fast EMA crossing above slow EMA.",
        description_zh="使用指数移动平均线（EMA）交叉信号的趋势跟踪策略。EMA相比SMA对近期价格更敏感，能更快响应趋势变化。快线上穿慢线做多，快线下穿慢线平仓。",
        difficulty=BEGINNER,
        markets=["stocks", "etf", "indices"],
        tags=["trend", "moving-average", "simple"],
        params=[
            {"name": "fast_period", "default": "12", "description": "Fast EMA period"},
            {"name": "slow_period", "default": "26", "description": "Slow EMA period"},
        ]
    ))
    
    # Bollinger Bands Strategy
    _register_template(StrategyTemplate(
        id="bollinger_bands",
        name="Bollinger Bands Strategy",
        name_zh="布林带突破策略",
        category=MEAN_REVERSION,
        description="Mean reversion strategy using Bollinger Bands. Buy when price touches lower band (oversold), sell when price touches upper band (overbought).",
        description_zh="布林带均值回归策略。布林带由中轨（SMA）和上下轨（中轨±N倍标准差）组成。价格触及下轨时认为超卖买入，触及上轨时认为超买卖出。",
        difficulty=BEGINNER,
        markets=["stocks", "forex", "crypto"],
        tags=["mean-reversion", "volatility", "classic"],
        params=[
            {"name": "period", "default": "20", "description": "Bollinger Bands period"},
            {"name": "devfactor", "default": "2.0", "description": "Standard deviation multiplier"},
        ]
    ))
    
    # Keltner Channel Strategy
    _register_template(StrategyTemplate(
        id="keltner_channel",
        name="Keltner Channel Strategy",
        name_zh="Keltner 通道策略",
        category=MEAN_REVERSION,
        description="Mean reversion using Keltner Channels. Uses EMA as middle band and ATR for volatility. Smoother than Bollinger Bands.",
        description_zh="Keltner通道均值回归策略。使用EMA作为中轨，ATR作为波动率指标计算上下轨。相比布林带更平滑稳定，适合波动率变化大的市场。",
        difficulty=INTERMEDIATE,
        markets=["stocks", "futures", "forex"],
        tags=["mean-reversion", "volatility", "atr"],
        params=[
            {"name": "ema_period", "default": "20", "description": "EMA period for middle band"},
            {"name": "atr_period", "default": "10", "description": "ATR period for volatility"},
            {"name": "atr_multiplier", "default": "2.0", "description": "ATR multiplier for bands"},
        ]
    ))
    
    # Grid Trading Strategy
    _register_template(StrategyTemplate(
        id="grid_trading",
        name="Grid Trading Strategy",
        name_zh="网格交易策略",
        category=GRID_TRADING,
        description="Range trading strategy that places buy/sell orders at preset price intervals. Profits from price oscillation within a range by buying low and selling high.",
        description_zh="在预设价格区间内等间距设置买卖网格的区间交易策略。价格下跌触及网格线则买入，上涨触及网格线则卖出，通过高抛低吸在震荡市中持续获利。",
        difficulty=INTERMEDIATE,
        markets=["crypto", "etf", "forex"],
        tags=["range-trading", "grid", "automated"],
        params=[
            {"name": "grid_count", "default": "10", "description": "Number of grid levels"},
            {"name": "upper_price", "default": "110", "description": "Upper price boundary"},
            {"name": "lower_price", "default": "90", "description": "Lower price boundary"},
        ]
    ))
    
    # Turtle Trading Strategy
    _register_template(StrategyTemplate(
        id="turtle_trading",
        name="Turtle Trading Strategy",
        name_zh="海龟交易策略",
        category=TREND_FOLLOWING,
        description="Classic trend-following system created by Richard Dennis. Uses Donchian Channel breakouts with ATR-based position sizing and stop-loss management.",
        description_zh="传奇交易员理查德·丹尼斯创立的经典趋势跟踪系统。使用唐奇安通道（N日最高/最低价）判断突破，结合ATR进行动态仓位管理和止损。",
        difficulty=INTERMEDIATE,
        markets=["futures", "forex", "commodities"],
        tags=["trend", "breakout", "position-sizing", "classic"],
        params=[
            {"name": "entry_period", "default": "20", "description": "Entry breakout period"},
            {"name": "exit_period", "default": "10", "description": "Exit breakout period"},
            {"name": "atr_period", "default": "20", "description": "ATR period for volatility"},
            {"name": "risk_factor", "default": "0.02", "description": "Risk per trade (2%)"},
        ]
    ))
    
    # RSI Divergence Strategy
    _register_template(StrategyTemplate(
        id="rsi_divergence",
        name="RSI Divergence Strategy",
        name_zh="RSI 背离策略",
        category=MEAN_REVERSION,
        description="Combines RSI with price action to identify bullish/bearish divergences. Bullish divergence: price lower low, RSI higher low. Signals potential reversals.",
        description_zh="结合RSI与价格走势识别背离信号。看涨背离：价格创新低但RSI更高低点，预示反转。利用动量与价格的分歧捕捉转折点。",
        difficulty=INTERMEDIATE,
        markets=["stocks", "forex", "crypto"],
        tags=["momentum", "divergence", "reversal"],
        params=[
            {"name": "rsi_period", "default": "14", "description": "RSI calculation period"},
            {"name": "rsi_oversold", "default": "30", "description": "Oversold threshold"},
            {"name": "rsi_overbought", "default": "70", "description": "Overbought threshold"},
            {"name": "lookback", "default": "5", "description": "Bars for divergence detection"},
        ]
    ))
    
    # Stochastic Strategy
    _register_template(StrategyTemplate(
        id="stochastic_strategy",
        name="Stochastic Oscillator Strategy",
        name_zh="随机指标策略",
        category=MEAN_REVERSION,
        description="Uses Stochastic Oscillator to identify overbought/oversold conditions. Enters on %K/%D crossovers in extreme zones.",
        description_zh="使用随机指标（KDJ）识别超买超卖。通过%K线与%D线在极端区域的交叉产生买卖信号，适合震荡市场。",
        difficulty=BEGINNER,
        markets=["stocks", "forex", "crypto"],
        tags=["oscillator", "momentum", "classic"],
        params=[
            {"name": "period_k", "default": "14", "description": "%K period"},
            {"name": "period_d", "default": "3", "description": "%D smoothing period"},
            {"name": "oversold", "default": "20", "description": "Oversold level"},
            {"name": "overbought", "default": "80", "description": "Overbought level"},
        ]
    ))
    
    # Donchian Breakout Strategy
    _register_template(StrategyTemplate(
        id="donchian_breakout",
        name="Donchian Channel Breakout",
        name_zh="唐奇安通道突破策略",
        category=TREND_FOLLOWING,
        description="Uses Donchian Channels (N-period high/low) for breakout signals. Enter on new highs, exit on new lows. Simple but effective trend-following.",
        description_zh="使用唐奇安通道（N日最高最低价）进行突破交易。突破上轨做多，跌破下轨平仓。简单有效的趋势跟踪方法。",
        difficulty=BEGINNER,
        markets=["futures", "forex", "commodities"],
        tags=["breakout", "channel", "simple"],
        params=[
            {"name": "entry_period", "default": "20", "description": "Entry channel period"},
            {"name": "exit_period", "default": "10", "description": "Exit channel period"},
        ]
    ))
    
    # Dual Thrust Strategy
    _register_template(StrategyTemplate(
        id="dual_thrust",
        name="Dual Thrust Strategy",
        name_zh="Dual Thrust 策略",
        category=TREND_FOLLOWING,
        description="Famous intraday range breakout strategy. Calculates trigger range from previous bars, enters on breakout above/below triggers.",
        description_zh="著名的日内区间突破策略。根据历史K线计算触发区间，突破上轨做多，突破下轨做空。适合日内交易和期货市场。",
        difficulty=INTERMEDIATE,
        markets=["futures", "commodities", "forex"],
        tags=["breakout", "intraday", "range"],
        params=[
            {"name": "lookback", "default": "4", "description": "Bars to calculate range"},
            {"name": "k1", "default": "0.5", "description": "Upper trigger multiplier"},
            {"name": "k2", "default": "0.5", "description": "Lower trigger multiplier"},
        ]
    ))
    
    # ATR Trailing Stop Strategy
    _register_template(StrategyTemplate(
        id="atr_trailing_stop",
        name="ATR Trailing Stop Strategy",
        name_zh="ATR 跟踪止损策略",
        category=TREND_FOLLOWING,
        description="Uses ATR to set dynamic trailing stops that adapt to volatility. Wider stops in volatile markets, tighter in calm markets.",
        description_zh="使用ATR设置动态跟踪止损。高波动时止损宽松，低波动时止损紧密。让盈利奔跑，同时控制风险。",
        difficulty=INTERMEDIATE,
        markets=["stocks", "futures", "crypto"],
        tags=["atr", "trailing-stop", "risk-management"],
        params=[
            {"name": "atr_period", "default": "14", "description": "ATR calculation period"},
            {"name": "atr_multiplier", "default": "2.0", "description": "Stop distance in ATR"},
            {"name": "ma_period", "default": "50", "description": "Trend filter period"},
        ]
    ))
    
    # Volume Breakout Strategy
    _register_template(StrategyTemplate(
        id="volume_breakout",
        name="Volume Breakout Strategy",
        name_zh="量价突破策略",
        category=TREND_FOLLOWING,
        description="Combines price breakout with volume confirmation. Only enters when breakout is accompanied by above-average volume.",
        description_zh="结合价格突破与成交量确认。只有在放量突破时才入场，过滤低量假突破，提高信号可靠性。",
        difficulty=INTERMEDIATE,
        markets=["stocks", "etf", "crypto"],
        tags=["volume", "breakout", "confirmation"],
        params=[
            {"name": "price_period", "default": "20", "description": "Price channel period"},
            {"name": "volume_period", "default": "20", "description": "Volume average period"},
            {"name": "volume_multiplier", "default": "1.5", "description": "Volume vs average ratio"},
        ]
    ))
    
    # Triple MA Strategy
    _register_template(StrategyTemplate(
        id="triple_ma",
        name="Triple Moving Average Strategy",
        name_zh="三均线策略",
        category=TREND_FOLLOWING,
        description="Uses three MAs (fast, medium, slow) for trend confirmation. Enter when all align bullishly. More robust than dual MA.",
        description_zh="使用三条均线（快、中、慢）确认趋势。三线多头排列时做多，比双均线系统更稳健，减少假信号。",
        difficulty=BEGINNER,
        markets=["stocks", "etf", "indices"],
        tags=["moving-average", "trend", "simple"],
        params=[
            {"name": "fast_period", "default": "10", "description": "Fast MA period"},
            {"name": "medium_period", "default": "20", "description": "Medium MA period"},
            {"name": "slow_period", "default": "50", "description": "Slow MA period"},
        ]
    ))
    
    # Z-Score Reversion Strategy
    _register_template(StrategyTemplate(
        id="zscore_reversion",
        name="Z-Score Mean Reversion",
        name_zh="Z-Score 均值回归策略",
        category=STATISTICAL_ARBITRAGE,
        description="Uses Z-Score to measure deviation from mean in standard deviation units. Pure statistical mean reversion approach.",
        description_zh="使用Z-Score衡量价格偏离均值的程度（以标准差为单位）。极端超卖时买入，回归均值时卖出。纯统计套利方法。",
        difficulty=INTERMEDIATE,
        markets=["etf", "pairs", "stocks"],
        tags=["statistical", "zscore", "mean-reversion"],
        params=[
            {"name": "lookback", "default": "20", "description": "Period for mean/std"},
            {"name": "entry_zscore", "default": "-2.0", "description": "Entry Z-Score threshold"},
            {"name": "exit_zscore", "default": "0.0", "description": "Exit Z-Score threshold"},
        ]
    ))


# Initialize templates on module load
_init_templates()


def get_all_templates() -> List[Dict]:
    """Get all template metadata (without code) for listing."""
    result = []
    for template in TEMPLATES.values():
        result.append({
            "id": template.id,
            "name": template.name,
            "name_zh": template.name_zh,
            "category": template.category,
            "description": template.description,
            "description_zh": template.description_zh,
            "difficulty": template.difficulty,
            "markets": template.markets,
            "tags": template.tags,
            "params": template.params,
        })
    return result


def get_template_by_id(template_id: str) -> Optional[Dict]:
    """Get template detail including code."""
    if template_id not in TEMPLATES:
        return None
    
    template = TEMPLATES[template_id]
    code = _load_template_code(template_id)
    
    return {
        "id": template.id,
        "name": template.name,
        "name_zh": template.name_zh,
        "category": template.category,
        "description": template.description,
        "description_zh": template.description_zh,
        "difficulty": template.difficulty,
        "markets": template.markets,
        "tags": template.tags,
        "params": template.params,
        "code": code,
    }


def get_categories() -> List[Dict]:
    """Get all category definitions."""
    return [
        {"id": TREND_FOLLOWING, "name": "Trend Following", "name_zh": "趋势跟踪"},
        {"id": MEAN_REVERSION, "name": "Mean Reversion", "name_zh": "均值回归"},
        {"id": STATISTICAL_ARBITRAGE, "name": "Statistical Arbitrage", "name_zh": "统计套利"},
        {"id": GRID_TRADING, "name": "Grid Trading", "name_zh": "网格交易"},
    ]


def get_difficulty_levels() -> List[Dict]:
    """Get all difficulty level definitions."""
    return [
        {"id": BEGINNER, "name": "Beginner", "name_zh": "入门"},
        {"id": INTERMEDIATE, "name": "Intermediate", "name_zh": "进阶"},
        {"id": ADVANCED, "name": "Advanced", "name_zh": "高级"},
    ]
