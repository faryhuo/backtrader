import { renderHook, act, waitFor } from '@testing-library/react';
import { useBacktestHistory } from '../useBacktestHistory';
import { api } from '../../services/api';

// Mock the api module
jest.mock('../../services/api', () => ({
    api: {
        getStrategies: jest.fn(),
        getBacktestHistory: jest.fn(),
        getPortfolioHistory: jest.fn(),
    }
}));

// Mock antd message
jest.mock('antd', () => ({
    message: {
        error: jest.fn(),
    }
}));

describe('useBacktestHistory', () => {
    const mockT = (key) => key;

    const mockStrategies = ['SMA_CrossOver', 'MACD_Strategy'];
    const mockBacktests = [
        { backtest_id: '1', ticker: 'AAPL', strategy_name: 'SMA_CrossOver' },
        { backtest_id: '2', ticker: 'GOOGL', strategy_name: 'MACD_Strategy' },
    ];
    const mockPortfolios = [
        { portfolio_id: '1', tickers: ['AAPL', 'GOOGL'] },
    ];

    beforeEach(() => {
        jest.clearAllMocks();
        api.getStrategies.mockResolvedValue(mockStrategies);
        api.getBacktestHistory.mockResolvedValue({ backtests: mockBacktests, total: 2 });
        api.getPortfolioHistory.mockResolvedValue({ results: mockPortfolios, count: 1 });
    });

    describe('initialization', () => {
        it('should initialize with default values', async () => {
            const { result } = renderHook(() =>
                useBacktestHistory({ initialRecordType: 'strategy', t: mockT })
            );

            expect(result.current.recordType).toBe('strategy');
            expect(result.current.loading).toBe(true);
            expect(result.current.backtests).toEqual([]);
            expect(result.current.portfolios).toEqual([]);
            expect(result.current.ticker).toBeNull();
            expect(result.current.strategyName).toBeNull();
            expect(result.current.dateRange).toBeNull();

            await waitFor(() => {
                expect(result.current.loading).toBe(false);
            });
        });

        it('should fetch strategies on mount', async () => {
            const { result } = renderHook(() =>
                useBacktestHistory({ initialRecordType: 'strategy', t: mockT })
            );

            await waitFor(() => {
                expect(api.getStrategies).toHaveBeenCalled();
                expect(result.current.strategies).toEqual(mockStrategies);
            });
        });

        it('should fetch backtests when recordType is strategy', async () => {
            const { result } = renderHook(() =>
                useBacktestHistory({ initialRecordType: 'strategy', t: mockT })
            );

            await waitFor(() => {
                expect(api.getBacktestHistory).toHaveBeenCalled();
                expect(result.current.backtests).toEqual(mockBacktests);
            });
        });

        it('should fetch portfolios when recordType is portfolio', async () => {
            const { result } = renderHook(() =>
                useBacktestHistory({ initialRecordType: 'portfolio', t: mockT })
            );

            await waitFor(() => {
                expect(api.getPortfolioHistory).toHaveBeenCalled();
                expect(result.current.portfolios).toEqual(mockPortfolios);
            });
        });
    });

    describe('filter management', () => {
        it('should update ticker filter', async () => {
            const { result } = renderHook(() =>
                useBacktestHistory({ initialRecordType: 'strategy', t: mockT })
            );

            await waitFor(() => expect(result.current.loading).toBe(false));

            act(() => {
                result.current.setTicker('AAPL');
            });

            expect(result.current.ticker).toBe('AAPL');
        });

        it('should update strategyName filter', async () => {
            const { result } = renderHook(() =>
                useBacktestHistory({ initialRecordType: 'strategy', t: mockT })
            );

            await waitFor(() => expect(result.current.loading).toBe(false));

            act(() => {
                result.current.setStrategyName('SMA_CrossOver');
            });

            expect(result.current.strategyName).toBe('SMA_CrossOver');
        });

        it('should update dateRange filter', async () => {
            const { result } = renderHook(() =>
                useBacktestHistory({ initialRecordType: 'strategy', t: mockT })
            );

            await waitFor(() => expect(result.current.loading).toBe(false));

            const dateRange = ['2022-01-01', '2022-12-31'];
            act(() => {
                result.current.setDateRange(dateRange);
            });

            expect(result.current.dateRange).toEqual(dateRange);
        });

        it('should reset all filters on handleReset', async () => {
            const { result } = renderHook(() =>
                useBacktestHistory({ initialRecordType: 'strategy', t: mockT })
            );

            await waitFor(() => expect(result.current.loading).toBe(false));

            // Set some filters first
            act(() => {
                result.current.setTicker('AAPL');
                result.current.setStrategyName('SMA_CrossOver');
                result.current.setDateRange(['2022-01-01', '2022-12-31']);
            });

            // Reset
            act(() => {
                result.current.handleReset();
            });

            expect(result.current.ticker).toBeNull();
            expect(result.current.strategyName).toBeNull();
            expect(result.current.dateRange).toBeNull();
        });
    });

    describe('record type switching', () => {
        it('should switch record type and reset pagination', async () => {
            const { result } = renderHook(() =>
                useBacktestHistory({ initialRecordType: 'strategy', t: mockT })
            );

            await waitFor(() => expect(result.current.loading).toBe(false));

            act(() => {
                result.current.handleRecordTypeChange('portfolio');
            });

            expect(result.current.recordType).toBe('portfolio');
            expect(result.current.pagination.current).toBe(1);
        });
    });

    describe('pagination', () => {
        it('should have default pagination values', async () => {
            const { result } = renderHook(() =>
                useBacktestHistory({ initialRecordType: 'strategy', t: mockT })
            );

            await waitFor(() => expect(result.current.loading).toBe(false));

            expect(result.current.pagination.current).toBe(1);
            expect(result.current.pagination.pageSize).toBe(20);
        });

        it('should update pagination on table change', async () => {
            const { result } = renderHook(() =>
                useBacktestHistory({ initialRecordType: 'strategy', t: mockT })
            );

            await waitFor(() => expect(result.current.loading).toBe(false));

            act(() => {
                result.current.handleTableChange(
                    { current: 2, pageSize: 10 },
                    {},
                    { field: 'created_at', order: 'ascend' }
                );
            });

            await waitFor(() => {
                expect(api.getBacktestHistory).toHaveBeenCalledWith(
                    expect.objectContaining({
                        limit: 10,
                        sort_by: 'created_at',
                        sort_order: 'asc'
                    })
                );
            });
        });
    });

    describe('error handling', () => {
        it('should handle fetch error gracefully', async () => {
            api.getBacktestHistory.mockRejectedValue(new Error('Network error'));

            const { result } = renderHook(() =>
                useBacktestHistory({ initialRecordType: 'strategy', t: mockT })
            );

            await waitFor(() => {
                expect(result.current.loading).toBe(false);
            });

            // Should not crash and backtests should remain empty
            expect(result.current.backtests).toEqual([]);
        });
    });
});
