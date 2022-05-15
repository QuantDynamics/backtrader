import math
import backtrader as bt


class MySimpleMovingAverage1(bt.Indicator):
    lines = ('sma',)
    params = (('period', 20),)

    def next(self):
        datasum = math.fsum(self.data.get(size=self.p.period))
        self.lines.sma[0] = datasum / self.p.period
