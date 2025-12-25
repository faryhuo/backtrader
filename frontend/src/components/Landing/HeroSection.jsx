import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useLogtoConfig } from '../../contexts/LogtoConfigContext';
import { useSiteConfig } from '../../contexts/SiteConfigContext';
import { ArrowRight, Github, Sparkles } from 'lucide-react';

/**
 * Hero section with headline, stats, and CTA buttons
 */
export function HeroSection() {
    const { t } = useTranslation();
    const { config } = useSiteConfig();
    const { config: logtoConfig } = useLogtoConfig();
    const { signIn, loginEnabled } = useAuth();
    const navigate = useNavigate();

    const handleGetStarted = () => {
        if (!loginEnabled) {
            navigate('/strategy');
            return;
        }
        const redirectUri = logtoConfig?.redirectUri;
        if (redirectUri) {
            signIn(redirectUri);
        }
    };

    const openGitHub = (e) => {
        e.preventDefault();
        if (config.links.github) {
            window.open(config.links.github, '_blank');
        }
    };

    return (
        <section className="landing-hero">
            {/* Background Effects */}
            <div className="landing-hero-bg landing-grid-pattern" />
            <div className="landing-hero-orb landing-hero-orb-1" />
            <div className="landing-hero-orb landing-hero-orb-2" />

            {/* Floating Elements */}
            <div className="landing-hero-floating landing-hero-floating-1" />
            <div className="landing-hero-floating landing-hero-floating-2" />
            <div className="landing-hero-floating landing-hero-floating-3" />

            <div className="landing-hero-content">
                {/* Badge */}
                <div className="landing-hero-badge landing-animate-fade-in">
                    <Sparkles className="landing-hero-badge-icon" />
                    <span className="landing-hero-badge-text">
                        {t('landing.hero.badge')}
                    </span>
                </div>

                {/* Headline */}
                <h1 className="landing-hero-title landing-animate-fade-in" style={{ animationDelay: '0.1s' }}>
                    {t('landing.hero.title1')}
                    <br />
                    <span className="landing-text-gradient">{t('landing.hero.title2')}</span>
                </h1>

                {/* Subheadline */}
                <p className="landing-hero-description landing-animate-fade-in" style={{ animationDelay: '0.2s' }}>
                    {t('landing.hero.description')}
                </p>

                {/* CTA Buttons */}
                <div className="landing-hero-cta landing-animate-fade-in" style={{ animationDelay: '0.3s' }}>
                    <button className="landing-btn landing-btn-hero landing-btn-xl" onClick={handleGetStarted}>
                        {t('landing.hero.cta.start')}
                        <ArrowRight />
                    </button>
                    <button className="landing-btn landing-btn-glass landing-btn-xl" onClick={openGitHub}>
                        <Github />
                        GitHub
                    </button>
                </div>

                {/* Stats - from config */}
                <div className="landing-hero-stats landing-animate-fade-in" style={{ animationDelay: '0.4s' }}>
                    <div className="landing-hero-stat">
                        <div className="landing-hero-stat-value landing-text-gradient">
                            {config.stats.strategies}
                        </div>
                        <div className="landing-hero-stat-label">{t('landing.hero.stats.strategies')}</div>
                    </div>
                    <div className="landing-hero-stat">
                        <div className="landing-hero-stat-value landing-text-gradient">
                            {config.stats.backtests}
                        </div>
                        <div className="landing-hero-stat-label">{t('landing.hero.stats.backtests')}</div>
                    </div>
                    <div className="landing-hero-stat">
                        <div className="landing-hero-stat-value landing-text-gradient">
                            {config.stats.users}
                        </div>
                        <div className="landing-hero-stat-label">{t('landing.hero.stats.users')}</div>
                    </div>
                </div>
            </div>

            {/* Bottom Gradient */}
            <div className="landing-hero-bottom-gradient" />
        </section>
    );
}

export default HeroSection;
