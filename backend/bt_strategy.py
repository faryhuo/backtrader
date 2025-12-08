
import backtrader as bt
import yfinance as yf
import pandas as pd
import datetime
# 在 import 部分添加
import matplotlib
matplotlib.use('Agg') # 使用非交互式后端
import matplotlib.pyplot as plt
plt.ioff()  # Keep matplotlib headless so API calls never open local windows
plt.show = lambda *args, **kwargs: None  # Make show a no-op to avoid local popups


# --- 1. 定义策略 ---
class SmaCross(bt.Strategy):
    # 定义参数，方便后期优化
    params = (
        ('fast_period', 10),  # 快速均线
        ('slow_period', 30),  # 慢速均线
    )

    def log(self, txt, dt=None):
        ''' 日志打印函数 '''
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def __init__(self):
        # 初始化指标
        # bt.ind 是 Backtrader 内置的指标库
        self.fast_ma = bt.ind.SMA(period=self.params.fast_period)
        self.slow_ma = bt.ind.SMA(period=self.params.slow_period)
        
        # CrossOver 返回 1.0 (金叉), -1.0 (死叉), 0.0 (无)
        self.crossover = bt.ind.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        ''' 
        这是最核心的函数！
        每一根新的 K 线产生时，Cerebro 都会调用一次这个函数。
        '''
        
        # 打印今天的收盘价
        # self.datas[0] 指的是第一个导入的数据集
        # .close[0] 指的是“当前”收盘价, .close[-1] 是昨天, .close[-2] 是前天
        # self.log(f'Close: {self.datas[0].close[0]:.2f}')

        # 如果还没持仓
        if not self.position:
            if self.crossover > 0: # 金叉
                self.log(f'BUY CREATE, Price: {self.datas[0].close[0]:.2f}')
                self.buy() # 默认买入 1 手，可以在 Sizer 里改

        # 如果已经持仓
        else:
            if self.crossover < 0: # 死叉
                self.log(f'SELL CREATE, Price: {self.datas[0].close[0]:.2f}')
                self.close() # 平仓所有头寸

# --- 2. 准备数据 ---
def get_data(ticker, start, end):
    # 使用 yfinance 下载数据
    # 设置 auto_adjust=False 以避免 FutureWarning
    data = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False)
    
    # 修复 MultiIndex 列名问题
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    # 将 Pandas 数据转为 Backtrader 数据
    feeds = bt.feeds.PandasData(dataname=data)
    return feeds

def run_backtest(ticker='AAPL', start_date='2022-01-01', end_date='2023-12-31', initial_cash=100000.0, save_path=None):
    # 实例化大脑
    cerebro = bt.Cerebro()

    # 添加策略
    cerebro.addstrategy(SmaCross)

    # 添加数据
    try:
        data = get_data(ticker, start_date, end_date)
        cerebro.adddata(data)
    except Exception as e:
        print(f"Error downloading data: {e}")
        return None, None

    # 设置初始资金
    cerebro.broker.setcash(initial_cash)

    # 设置交易手续费
    cerebro.broker.setcommission(commission=0.0005)

    # 设置每次买卖的数量
    cerebro.addsizer(bt.sizers.FixedSize, stake=100)

    # Add Analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

    # 运行回测
    results = cerebro.run()
    strat = results[0]
    
    final_value = cerebro.broker.getvalue()
    
    # Extract metrics
    metrics = {
        'final_value': final_value,
        'sharpe': strat.analyzers.sharpe.get_analysis().get('sharperatio', None),
        'drawdown': strat.analyzers.drawdown.get_analysis().get('max', {}).get('drawdown', 0.0),
        'returns': strat.analyzers.returns.get_analysis().get('rnorm100', 0.0)
    }

    # 绘图
    # iplot=False 阻止自动弹窗
    try:
        if save_path:
            plt.ioff()
            figures = cerebro.plot(style='candlestick', iplot=False)
            first_fig = figures[0][0] if figures and figures[0] else None
            if first_fig:
                first_fig.savefig(save_path, bbox_inches='tight')
                plt.close(first_fig)
            plt.close('all')
        return metrics
    except Exception as e:
        print(f"Error plotting: {e}")
        plt.close('all')
        return metrics

# --- 3. 运行引擎 ---
if __name__ == '__main__':
    final_val, fig = run_backtest()
    print(f'Final Portfolio Value: {final_val:.2f}')
    
    if fig:
        fig.savefig('backtrader_plot.png')
        print("Plot saved to backtrader_plot.png")
