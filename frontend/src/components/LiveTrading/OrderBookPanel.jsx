import { Segmented, Typography } from 'antd';
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import './OrderBookPanel.css';

const { Text } = Typography;

function formatPrice(value) {
  if (value === null || value === undefined) return '--';
  return Number(value).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 8,
  });
}

function formatSize(value) {
  if (value === null || value === undefined) return '--';
  return Number(value).toLocaleString(undefined, {
    minimumFractionDigits: 4,
    maximumFractionDigits: 8,
  });
}

function buildRows(levels = []) {
  const maxSize = levels.reduce((acc, item) => Math.max(acc, Number(item?.size || 0)), 0);
  return levels.map((item, index) => ({
    ...item,
    key: `${item.price}-${index}`,
    sizeRatio: maxSize > 0 ? Math.max(Number(item.size || 0) / maxSize, 0.06) : 0,
  }));
}

export default function OrderBookPanel({
  orderBook,
  onDepthChange,
}) {
  const { t } = useTranslation();

  const asks = useMemo(
    () => buildRows(orderBook?.asks || []).slice().reverse(),
    [orderBook?.asks],
  );
  const bids = useMemo(
    () => buildRows(orderBook?.bids || []),
    [orderBook?.bids],
  );

  const hasDepth = asks.length > 0 || bids.length > 0;

  return (
    <div className="order-book-panel">
      <div className="order-book-toolbar">
        <div>
          <Text className="order-book-caption">
            {t('live.order_book.subtitle', 'Top of book and visible depth')}
          </Text>
        </div>
        <Segmented
          size="small"
          value={orderBook?.limit || 5}
          onChange={onDepthChange}
          options={[
            { label: t('live.order_book.depth_5', 'Top 5'), value: 5 },
            { label: t('live.order_book.depth_10', 'Top 10'), value: 10 },
          ]}
        />
      </div>

      {!hasDepth ? (
        <div className="order-book-empty">
          {t('live.order_book.empty', 'Waiting for order book depth...')}
        </div>
      ) : (
        <div className="order-book-stack">
          <div className="order-book-side">
            <div className="order-book-side-header ask">
              {t('live.order_book.asks', 'Asks')}
            </div>
            <div className="order-book-columns">
              <span>{t('live.order_book.price', 'Price')}</span>
              <span>{t('live.order_book.size', 'Size')}</span>
            </div>
            <div className="order-book-levels">
              {asks.map((row) => (
                <div key={row.key} className="order-book-level ask">
                  <div className="order-book-bar ask" style={{ width: `${row.sizeRatio * 100}%` }} />
                  <span>{formatPrice(row.price)}</span>
                  <span>{formatSize(row.size)}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="order-book-side">
            <div className="order-book-side-header bid">
              {t('live.order_book.bids', 'Bids')}
            </div>
            <div className="order-book-columns">
              <span>{t('live.order_book.price', 'Price')}</span>
              <span>{t('live.order_book.size', 'Size')}</span>
            </div>
            <div className="order-book-levels">
              {bids.map((row) => (
                <div key={row.key} className="order-book-level bid">
                  <div className="order-book-bar bid" style={{ width: `${row.sizeRatio * 100}%` }} />
                  <span>{formatPrice(row.price)}</span>
                  <span>{formatSize(row.size)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
