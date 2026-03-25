/**
 * SymbolSearchModal — browsable search dialog for Binance trading pairs.
 */
import { useEffect, useMemo, useState } from 'react';
import {
  Input,
  Modal,
  Table,
  Typography,
  Tag,
} from 'antd';
import {
  SearchOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { api } from '../../services/api';
import './SymbolSearchModal.css';

// Mapping from base asset symbol to human-readable description
const ASSET_DESCRIPTIONS = {
  BTC: 'Bitcoin',
  ETH: 'Ethereum',
  BNB: 'BNB',
  SOL: 'Solana',
  XRP: 'Ripple',
  DOGE: 'Dogecoin',
  ADA: 'Cardano',
  AVAX: 'Avalanche',
  DOT: 'Polkadot',
  MATIC: 'Polygon',
  LINK: 'Chainlink',
  UNI: 'Uniswap',
  LTC: 'Litecoin',
  ATOM: 'Cosmos',
  XLM: 'Stellar',
  ALGO: 'Algorand',
  VET: 'VeChain',
  FIL: 'Filecoin',
  TRX: 'Tron',
  ETC: 'Ethereum Classic',
  XMR: 'Monero',
  AAVE: 'Aave',
  MKR: 'Maker',
  COMP: 'Compound',
  SNX: 'Synthetix',
  SUSHI: 'SushiSwap',
  CAKE: 'PancakeSwap',
  SHIB: 'Shiba Inu',
  PEPE: 'Pepe',
  WIF: 'dogwifhat',
  FLOKI: 'FLOKI',
  ARB: 'Arbitrum',
  OP: 'Optimism',
  INJ: 'Injective',
  SUI: 'Sui',
  APT: 'Aptos',
  SEI: 'Sei',
  TIA: 'Celestia',
  NEAR: 'NEAR Protocol',
  KAS: 'Kaspa',
  RENDER: 'Render Token',
  GRASS: 'Grass',
  PYTH: 'Pyth Network',
  JUP: 'Jupiter',
  W: 'Wormhole',
  ZK: 'zkSync',
  NOT: 'Notcoin',
  GOAT: ' Goat CEO',
  PNUT: 'Peanut the Squirrel',
  RAY: 'Raydium',
  JTO: 'Jito',
  BMATIC: 'BNB Pegged Matic',
  FDUSD: 'First Digital USD',
  USDT: 'Tether USD',
  USDC: 'USD Coin',
  BUSD: 'Binance USD',
};

const { Text } = Typography;

const FALLBACK_SYMBOLS = [
  { symbol: 'BTC/USDT', baseAsset: 'BTC', quoteAsset: 'USDT' },
  { symbol: 'ETH/USDT', baseAsset: 'ETH', quoteAsset: 'USDT' },
  { symbol: 'BNB/USDT', baseAsset: 'BNB', quoteAsset: 'USDT' },
  { symbol: 'SOL/USDT', baseAsset: 'SOL', quoteAsset: 'USDT' },
  { symbol: 'XRP/USDT', baseAsset: 'XRP', quoteAsset: 'USDT' },
  { symbol: 'DOGE/USDT', baseAsset: 'DOGE', quoteAsset: 'USDT' },
  { symbol: 'ADA/USDT', baseAsset: 'ADA', quoteAsset: 'USDT' },
  { symbol: 'AVAX/USDT', baseAsset: 'AVAX', quoteAsset: 'USDT' },
  { symbol: 'DOT/USDT', baseAsset: 'DOT', quoteAsset: 'USDT' },
  { symbol: 'MATIC/USDT', baseAsset: 'MATIC', quoteAsset: 'USDT' },
  { symbol: 'LINK/USDT', baseAsset: 'LINK', quoteAsset: 'USDT' },
  { symbol: 'UNI/USDT', baseAsset: 'UNI', quoteAsset: 'USDT' },
  { symbol: 'LTC/USDT', baseAsset: 'LTC', quoteAsset: 'USDT' },
  { symbol: 'ATOM/USDT', baseAsset: 'ATOM', quoteAsset: 'USDT' },
  { symbol: 'XLM/USDT', baseAsset: 'XLM', quoteAsset: 'USDT' },
  { symbol: 'FIL/USDT', baseAsset: 'FIL', quoteAsset: 'USDT' },
  { symbol: 'TRX/USDT', baseAsset: 'TRX', quoteAsset: 'USDT' },
  { symbol: 'ETC/USDT', baseAsset: 'ETC', quoteAsset: 'USDT' },
  { symbol: 'AAVE/USDT', baseAsset: 'AAVE', quoteAsset: 'USDT' },
  { symbol: 'SHIB/USDT', baseAsset: 'SHIB', quoteAsset: 'USDT' },
  { symbol: 'ARB/USDT', baseAsset: 'ARB', quoteAsset: 'USDT' },
  { symbol: 'OP/USDT', baseAsset: 'OP', quoteAsset: 'USDT' },
  { symbol: 'INJ/USDT', baseAsset: 'INJ', quoteAsset: 'USDT' },
  { symbol: 'SUI/USDT', baseAsset: 'SUI', quoteAsset: 'USDT' },
  { symbol: 'APT/USDT', baseAsset: 'APT', quoteAsset: 'USDT' },
  { symbol: 'NEAR/USDT', baseAsset: 'NEAR', quoteAsset: 'USDT' },
  { symbol: 'KAS/USDT', baseAsset: 'KAS', quoteAsset: 'USDT' },
  { symbol: 'PEPE/USDT', baseAsset: 'PEPE', quoteAsset: 'USDT' },
  { symbol: 'WIF/USDT', baseAsset: 'WIF', quoteAsset: 'USDT' },
  { symbol: 'JUP/USDT', baseAsset: 'JUP', quoteAsset: 'USDT' },
  { symbol: 'TIA/USDT', baseAsset: 'TIA', quoteAsset: 'USDT' },
  { symbol: 'RENDER/USDT', baseAsset: 'RENDER', quoteAsset: 'USDT' },
];

const SymbolSearchModal = ({ open, onClose, onSelect }) => {
  const { t } = useTranslation();
  const [allSymbols, setAllSymbols] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');

  useEffect(() => {
    if (!open) return;
    const load = async () => {
      setLoading(true);
      try {
        const data = await api.getSymbols();
        const list = Array.isArray(data?.symbols) && data.symbols.length > 0
          ? data.symbols
          : FALLBACK_SYMBOLS;
        setAllSymbols(list);
      } catch {
        setAllSymbols(FALLBACK_SYMBOLS);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [open]);

  const filteredSymbols = useMemo(() => {
    if (!searchText.trim()) return allSymbols;
    const q = searchText.trim().toUpperCase();
    return allSymbols.filter(
      (s) =>
        s.symbol.toUpperCase().includes(q) ||
        (ASSET_DESCRIPTIONS[s.baseAsset] || '').toUpperCase().includes(q) ||
        s.baseAsset.toUpperCase().includes(q)
    );
  }, [searchText, allSymbols]);

  const handleSelect = (record) => {
    onSelect(record.symbol);
    setSearchText('');
    onClose();
  };

  const columns = [
    {
      title: t('live.form.symbol_search.col_symbol', 'Symbol'),
      dataIndex: 'symbol',
      key: 'symbol',
      render: (text) => (
        <Tag color="blue" style={{ fontWeight: 600, fontSize: 13 }}>
          {text}
        </Tag>
      ),
    },
    {
      title: t('live.form.symbol_search.col_description', 'Description'),
      dataIndex: 'baseAsset',
      key: 'description',
      render: (baseAsset) => ASSET_DESCRIPTIONS[baseAsset] || '—',
    },
    {
      title: t('live.form.symbol_search.col_quote', 'Quote'),
      dataIndex: 'quoteAsset',
      key: 'quoteAsset',
      render: (qa) => (
        <Tag color={qa === 'USDT' ? 'green' : 'cyan'}>{qa}</Tag>
      ),
    },
  ];

  return (
    <Modal
      open={open}
      onCancel={() => {
        setSearchText('');
        onClose();
      }}
      footer={null}
      title={
        <span>
          <ThunderboltOutlined style={{ color: '#67e8f9', marginRight: 8 }} />
          {t('live.form.symbol_search.title', 'Search Trading Pairs')}
        </span>
      }
      width={580}
      bodyStyle={{ padding: '0 0 16px 0' }}
      className="symbol-search-modal"
      destroyOnClose
    >
      <div className="symbol-search-header">
        <Input
          prefix={<SearchOutlined style={{ color: '#64748b' }} />}
          placeholder={t('live.form.symbol_search.placeholder', 'Search by symbol or name…')}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          allowClear
          autoFocus
          size="large"
          className="symbol-search-input"
        />
        <Text type="secondary" className="symbol-search-count">
          {filteredSymbols.length} {t('live.form.symbol_search.pairs_found', 'pairs found')}
        </Text>
      </div>

      <Table
        className="symbol-search-table"
        columns={columns}
        dataSource={filteredSymbols}
        rowKey="symbol"
        size="small"
        loading={loading}
        pagination={{
          pageSize: 20,
          showSizeChanger: false,
          showTotal: (total) => `${total} ${t('live.form.symbol_search.total', 'total')}`,
        }}
        onRow={(record) => ({
          onClick: () => handleSelect(record),
          style: { cursor: 'pointer' },
        })}
        scroll={{ y: 420 }}
      />
    </Modal>
  );
};

export default SymbolSearchModal;
