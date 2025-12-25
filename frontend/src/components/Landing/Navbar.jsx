import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../hooks/useAuth';
import { useLogtoConfig } from '../../contexts/LogtoConfigContext';
import { TrendingUp, Menu, X, Globe } from 'lucide-react';

/**
 * Landing page navbar with navigation links and language switcher
 */
export function Navbar() {
    const [isOpen, setIsOpen] = useState(false);
    const { t, i18n } = useTranslation();
    const isZh = i18n.language?.startsWith('zh');
    const { signIn, loginEnabled } = useAuth();
    const { config } = useLogtoConfig();
    const navigate = useNavigate();

    const navLinks = [
        { name: t('landing.nav.features'), href: '#features' },
        { name: t('landing.nav.workflow'), href: '#workflow' },
        { name: t('landing.nav.roadmap'), href: '#roadmap' },
        { name: t('landing.nav.docs'), href: '#docs' },
    ];

    const toggleLanguage = () => {
        i18n.changeLanguage(isZh ? 'en' : 'zh');
    };

    const handleLogin = () => {
        if (!loginEnabled) {
            navigate('/strategy');
            return;
        }
        const redirectUri = config?.redirectUri;
        if (redirectUri) {
            signIn(redirectUri);
        }
    };

    const handleGetStarted = () => {
        if (!loginEnabled) {
            navigate('/strategy');
            return;
        }
        const redirectUri = config?.redirectUri;
        if (redirectUri) {
            signIn(redirectUri);
        }
    };

    const scrollToSection = (e, href) => {
        e.preventDefault();
        const element = document.querySelector(href);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
        }
        setIsOpen(false);
    };

    return (
        <nav className="landing-navbar">
            <div className="landing-container">
                <div className="landing-navbar-inner">
                    {/* Logo */}
                    <a href="/" className="landing-navbar-logo">
                        <div className="landing-navbar-logo-icon">
                            <TrendingUp />
                        </div>
                        <span className="landing-navbar-logo-text">
                            Backtrader<span className="landing-text-gradient">Pro</span>
                        </span>
                    </a>

                    {/* Desktop Navigation */}
                    <div className="landing-navbar-nav">
                        {navLinks.map((link) => (
                            <a
                                key={link.href}
                                href={link.href}
                                className="landing-navbar-link"
                                onClick={(e) => scrollToSection(e, link.href)}
                            >
                                {link.name}
                            </a>
                        ))}
                    </div>

                    {/* Desktop CTA */}
                    <div className="landing-navbar-actions">
                        <button
                            className="landing-btn landing-btn-ghost landing-btn-sm landing-lang-switcher"
                            onClick={toggleLanguage}
                        >
                            <Globe />
                            <span>{isZh ? t('common.language.short.en', 'EN') : t('common.language.short.zh', '中')}</span>
                        </button>
                        <button
                            className="landing-btn landing-btn-ghost landing-btn-sm"
                            onClick={handleLogin}
                        >
                            {t('landing.nav.login')}
                        </button>
                        <button
                            className="landing-btn landing-btn-hero landing-btn-sm"
                            onClick={handleGetStarted}
                        >
                            {t('landing.nav.getStarted')}
                        </button>
                    </div>

                    {/* Mobile Menu Button */}
                    <button
                        className="landing-mobile-menu-btn"
                        onClick={() => setIsOpen(!isOpen)}
                    >
                        {isOpen ? <X /> : <Menu />}
                    </button>
                </div>

                {/* Mobile Navigation */}
                <div className={`landing-mobile-menu ${isOpen ? 'open' : ''}`}>
                    <div className="landing-mobile-nav">
                        {navLinks.map((link) => (
                            <a
                                key={link.href}
                                href={link.href}
                                className="landing-navbar-link"
                                onClick={(e) => scrollToSection(e, link.href)}
                            >
                                {link.name}
                            </a>
                        ))}
                    </div>
                    <div className="landing-mobile-actions">
                        <button
                            className="landing-btn landing-btn-ghost landing-btn-sm landing-lang-switcher"
                            onClick={toggleLanguage}
                        >
                            <Globe />
                            <span>{isZh ? t('common.language.short.en', 'EN') : t('common.language.short.zh', '中')}</span>
                        </button>
                        <button
                            className="landing-btn landing-btn-ghost landing-btn-sm"
                            onClick={handleLogin}
                        >
                            {t('landing.nav.login')}
                        </button>
                        <button
                            className="landing-btn landing-btn-hero landing-btn-sm"
                            onClick={handleGetStarted}
                        >
                            {t('landing.nav.getStarted')}
                        </button>
                    </div>
                </div>
            </div>
        </nav>
    );
}

export default Navbar;
