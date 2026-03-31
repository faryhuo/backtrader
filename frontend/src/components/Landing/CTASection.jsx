import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useLogtoConfig } from '../../contexts/LogtoConfigContext';
import { useSiteConfig } from '../../contexts/SiteConfigContext';
import { ArrowRight, Github, BookOpen } from 'lucide-react';

/**
 * Call-to-action section with buttons and trust badges
 */
export function CTASection() {
    const { t } = useTranslation();
    const { config } = useSiteConfig();
    const { config: logtoConfig } = useLogtoConfig();
    const { signIn, loginEnabled, authProvider } = useAuth();
    const navigate = useNavigate();

    const handleGetStarted = () => {
        if (!loginEnabled) {
            navigate('/strategy');
            return;
        }
        if (authProvider === 'system') {
            navigate('/login');
            return;
        }
        const redirectUri = logtoConfig?.redirectUri;
        if (redirectUri) {
            signIn(redirectUri);
        }
    };

    const handleDocsClick = (e) => {
        e.preventDefault();
        if (config.links.docs) {
            window.open(config.links.docs, '_blank');
        }
    };

    const handleGithubClick = () => {
        if (config.links.github) {
            window.open(config.links.github, '_blank');
        }
    };

    return (
        <section id="docs" className="landing-cta">
            {/* Background */}
            <div className="landing-cta-bg" />
            <div className="landing-cta-orb" />

            <div className="landing-container">
                <div className="landing-cta-content">
                    {/* Headline */}
                    <h2 className="landing-cta-title">
                        {t('landing.cta.title')}
                    </h2>

                    {/* Description */}
                    <p className="landing-cta-description">
                        {t('landing.cta.description')}
                    </p>

                    {/* CTA Buttons */}
                    <div className="landing-cta-buttons">
                        <button className="landing-btn landing-btn-hero landing-btn-xl" onClick={handleGetStarted}>
                            {t('landing.cta.button')}
                            <ArrowRight />
                        </button>
                        {config.links.docs && (
                            <button className="landing-btn landing-btn-glass landing-btn-xl" onClick={handleDocsClick}>
                                <BookOpen />
                                {t('landing.cta.docs', 'View Docs')}
                            </button>
                        )}
                        {config.links.github && (
                            <button
                                className="landing-btn landing-btn-outline landing-btn-xl"
                                onClick={handleGithubClick}
                            >
                                <Github />
                                {t('landing.cta.github', 'GitHub')}
                            </button>
                        )}
                    </div>

                    {/* Trust Badge */}
                    <div className="landing-cta-trust">
                        <div className="landing-cta-avatars">
                            {['A', 'B', 'C', 'D'].map((letter) => (
                                <div key={letter} className="landing-cta-avatar">
                                    {letter}
                                </div>
                            ))}
                        </div>
                        <span className="landing-cta-trust-text">
                            {t('landing.cta.note')}
                        </span>
                    </div>
                </div>
            </div>
        </section>
    );
}

export default CTASection;
