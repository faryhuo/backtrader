import React, { createContext, useContext, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
    formatPortfolioCurrency,
    formatWeight,
    getCostColor,
    getValueColor,
    getReturnColor,
    formatDate,
    formatSharesChange,
} from '../utils/formatters';

/**
 * Portfolio Context - Provides shared dependencies to portfolio components.
 *
 * This context eliminates props drilling for common dependencies like
 * translation function and formatting utilities across portfolio components.
 *
 * Provides:
 * - t: Translation function from react-i18next
 * - Formatting utilities: formatCurrency, formatWeight, etc.
 * - Color utilities: getCostColor, getValueColor, etc.
 */
const PortfolioContext = createContext(null);

/**
 * Portfolio context provider component.
 *
 * Wrap your portfolio page or component tree with this provider
 * to give all children access to shared portfolio utilities.
 *
 * @param {Object} props
 * @param {React.ReactNode} props.children - Child components
 * @param {Object} props.additionalContext - Additional context values to merge
 *
 * @example
 * // In PortfolioBacktest.jsx:
 * <PortfolioProvider>
 *   <PortfolioResultsSection result={result} />
 * </PortfolioProvider>
 *
 * // In PortfolioResultsSection.jsx (no props drilling needed):
 * const { t, formatCurrency } = usePortfolioContext();
 */
export function PortfolioProvider({ children, additionalContext = {} }) {
    const { t, i18n } = useTranslation();

    // Memoize the context value to prevent unnecessary re-renders
    const value = useMemo(() => ({
        // Translation
        t,
        i18n,

        // Currency formatting
        formatCurrency: formatPortfolioCurrency,

        // Weight/percentage formatting
        formatWeight,

        // Color utilities
        getCostColor,
        getValueColor,
        getReturnColor,

        // Other formatters
        formatDate,
        formatSharesChange,

        // Merge any additional context
        ...additionalContext,
    }), [t, i18n, additionalContext]);

    return (
        <PortfolioContext.Provider value={value}>
            {children}
        </PortfolioContext.Provider>
    );
}

/**
 * Hook to access portfolio context.
 *
 * Must be used within a PortfolioProvider.
 *
 * @returns {Object} Context value with t, formatters, and color utilities
 * @throws {Error} If used outside of PortfolioProvider
 *
 * @example
 * function RebalancingEventItem({ event }) {
 *   const { t, formatCurrency, getCostColor } = usePortfolioContext();
 *   return (
 *     <Tag color={getCostColor(event.transaction_cost)}>
 *       {t('portfolio.cost')}: {formatCurrency(event.transaction_cost)}
 *     </Tag>
 *   );
 * }
 */
export function usePortfolioContext() {
    const context = useContext(PortfolioContext);

    if (!context) {
        throw new Error(
            'usePortfolioContext must be used within a PortfolioProvider. ' +
            'Wrap your component tree with <PortfolioProvider>.'
        );
    }

    return context;
}

/**
 * Convenience hook that returns only the translation function.
 *
 * Use this when you only need translation, not formatters.
 *
 * @returns {Function} Translation function (t)
 */
export function usePortfolioTranslation() {
    const { t } = usePortfolioContext();
    return t;
}

/**
 * Convenience hook that returns formatting utilities.
 *
 * Use this when you only need formatters, not translation.
 *
 * @returns {Object} Object with all formatting functions
 */
export function usePortfolioFormatters() {
    const context = usePortfolioContext();
    return {
        formatCurrency: context.formatCurrency,
        formatWeight: context.formatWeight,
        formatDate: context.formatDate,
        formatSharesChange: context.formatSharesChange,
    };
}

/**
 * Convenience hook that returns color utilities.
 *
 * @returns {Object} Object with all color functions
 */
export function usePortfolioColors() {
    const context = usePortfolioContext();
    return {
        getCostColor: context.getCostColor,
        getValueColor: context.getValueColor,
        getReturnColor: context.getReturnColor,
    };
}

/**
 * HOC that wraps a component with PortfolioProvider.
 *
 * Use this to wrap page components that need portfolio context.
 *
 * @param {React.ComponentType} WrappedComponent - Component to wrap
 * @returns {React.ComponentType} Enhanced component with PortfolioProvider
 *
 * @example
 * export default withPortfolioContext(PortfolioBacktestPage);
 */
export function withPortfolioContext(WrappedComponent) {
    const displayName = WrappedComponent.displayName || WrappedComponent.name || 'Component';

    function WithPortfolioContext(props) {
        return (
            <PortfolioProvider>
                <WrappedComponent {...props} />
            </PortfolioProvider>
        );
    }

    WithPortfolioContext.displayName = `withPortfolioContext(${displayName})`;

    return WithPortfolioContext;
}

export default PortfolioContext;
