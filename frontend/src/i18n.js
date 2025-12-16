import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// English imports
import appEn from './locales/en/app.json';
import navEn from './locales/en/nav.json';
import commonEn from './locales/en/common.json';
import authEn from './locales/en/auth.json';
import homeEn from './locales/en/home.json';
import aiInsightEn from './locales/en/ai_insight.json';
import configFormEn from './locales/en/config_form.json';
import performanceEn from './locales/en/performance.json';
import tradeLogEn from './locales/en/trade_log.json';
import strategyPlotEn from './locales/en/strategy_plot.json';
import maintainEn from './locales/en/maintain.json';
import datasourceEn from './locales/en/datasource.json';
import historyEn from './locales/en/history.json';
import walkforwardEn from './locales/en/walkforward.json';
import liveEn from './locales/en/live.json';
import settingsEn from './locales/en/settings.json';

// Chinese imports
import appZh from './locales/zh/app.json';
import navZh from './locales/zh/nav.json';
import commonZh from './locales/zh/common.json';
import authZh from './locales/zh/auth.json';
import homeZh from './locales/zh/home.json';
import aiInsightZh from './locales/zh/ai_insight.json';
import configFormZh from './locales/zh/config_form.json';
import performanceZh from './locales/zh/performance.json';
import tradeLogZh from './locales/zh/trade_log.json';
import strategyPlotZh from './locales/zh/strategy_plot.json';
import maintainZh from './locales/zh/maintain.json';
import datasourceZh from './locales/zh/datasource.json';
import historyZh from './locales/zh/history.json';
import walkforwardZh from './locales/zh/walkforward.json';
import liveZh from './locales/zh/live.json';
import settingsZh from './locales/zh/settings.json';

const en = {
  app: appEn,
  nav: navEn,
  common: commonEn,
  auth: authEn,
  home: homeEn,
  ai_insight: aiInsightEn,
  config_form: configFormEn,
  performance: performanceEn,
  trade_log: tradeLogEn,
  strategy_plot: strategyPlotEn,
  maintain: maintainEn,
  datasource: datasourceEn,
  history: historyEn,
  walkforward: walkforwardEn?.walkforward ?? walkforwardEn,
  live: liveEn,
  settings: settingsEn
};

const zh = {
  app: appZh,
  nav: navZh,
  common: commonZh,
  auth: authZh,
  home: homeZh,
  ai_insight: aiInsightZh,
  config_form: configFormZh,
  performance: performanceZh,
  trade_log: tradeLogZh,
  strategy_plot: strategyPlotZh,
  maintain: maintainZh,
  datasource: datasourceZh,
  history: historyZh,
  walkforward: walkforwardZh?.walkforward ?? walkforwardZh,
  live: liveZh,
  settings: settingsZh
};

i18n
  // detect user language
  // learn more: https://github.com/i18next/i18next-browser-languagedetector
  .use(LanguageDetector)
  // pass the i18n instance to react-i18next.
  .use(initReactI18next)
  // init i18next
  // for all options read: https://www.i18next.com/overview/configuration-options
  .init({
    debug: true,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false, // not needed for react as it escapes by default
    },
    resources: {
      en: {
        translation: en
      },
      zh: {
        translation: zh
      },
      // Support zh-CN, zh-TW, etc. mapping to zh
      'zh-CN': {
        translation: zh
      },
      'zh-TW': {
        translation: zh
      }
    }
  });

export default i18n;
