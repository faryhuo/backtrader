import { useTranslation } from 'react-i18next';
import { useSiteConfig } from '../../contexts/SiteConfigContext';
import { TrendingUp, Github, Twitter, Mail } from 'lucide-react';

/**
 * Footer with logo, links, and social icons
 */
export function Footer() {
    const { t } = useTranslation();
    const { config } = useSiteConfig();

    const footerLinks = {
        product: [
            { key: 'landing.footer.product.features', href: '#features' },
            { key: 'landing.footer.product.workflow', href: '#workflow' },
            { key: 'landing.footer.product.roadmap', href: '#roadmap' },
            { key: 'landing.footer.product.changelog', href: '#' },
        ],
        resources: [
            { key: 'landing.footer.resources.docs', href: config.links.docs || '#docs' },
            { key: 'landing.footer.resources.api', href: '#' },
            { key: 'landing.footer.resources.templates', href: '#' },
            { key: 'landing.footer.resources.tutorials', href: '#' },
        ],
    };

    return (
        <footer className="landing-footer">
            <div className="landing-container">
                <div className="landing-footer-grid">
                    {/* Brand */}
                    <div className="landing-footer-brand">
                        <a href="/" className="landing-footer-logo">
                            <div className="landing-footer-logo-icon">
                                <TrendingUp />
                            </div>
                            <span className="landing-footer-logo-text">
                                {config.site.title.includes(' ')
                                    ? config.site.title
                                    : <>Backtrader<span className="landing-text-gradient">Pro</span></>
                                }
                            </span>
                        </a>
                        <p className="landing-footer-description">
                            {t('landing.footer.description')}
                        </p>
                        <div className="landing-footer-social">
                            {config.links.github && (
                                <a href={config.links.github} target="_blank" rel="noopener noreferrer" className="landing-footer-social-link">
                                    <Github />
                                </a>
                            )}
                            {config.links.twitter && (
                                <a href={config.links.twitter} target="_blank" rel="noopener noreferrer" className="landing-footer-social-link">
                                    <Twitter />
                                </a>
                            )}
                            {config.links.email && (
                                <a href={`mailto:${config.links.email}`} className="landing-footer-social-link">
                                    <Mail />
                                </a>
                            )}
                            {/* Always show icons with fallback */}
                            {!config.links.github && !config.links.twitter && !config.links.email && (
                                <>
                                    <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="landing-footer-social-link">
                                        <Github />
                                    </a>
                                    <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="landing-footer-social-link">
                                        <Twitter />
                                    </a>
                                    <a href="mailto:contact@example.com" className="landing-footer-social-link">
                                        <Mail />
                                    </a>
                                </>
                            )}
                        </div>
                    </div>

                    {/* Product Links */}
                    <div>
                        <h4 className="landing-footer-column-title">{t('landing.footer.product')}</h4>
                        <div className="landing-footer-links">
                            {footerLinks.product.map((link) => (
                                <a key={link.key} href={link.href} className="landing-footer-link">
                                    {t(link.key)}
                                </a>
                            ))}
                        </div>
                    </div>

                    {/* Resources Links */}
                    <div>
                        <h4 className="landing-footer-column-title">{t('landing.footer.resources')}</h4>
                        <div className="landing-footer-links">
                            {footerLinks.resources.map((link) => (
                                <a key={link.key} href={link.href} className="landing-footer-link">
                                    {t(link.key)}
                                </a>
                            ))}
                        </div>
                    </div>


                </div>

                {/* Bottom */}
                <div className="landing-footer-bottom">
                    <p className="landing-footer-copyright">
                        {t('landing.footer.copyright')}
                    </p>
                    <div className="landing-footer-legal">
                        <a href="#privacy" className="landing-footer-legal-link">
                            {t('landing.footer.privacy')}
                        </a>
                        <a href="#terms" className="landing-footer-legal-link">
                            {t('landing.footer.terms')}
                        </a>
                    </div>
                </div>
            </div>
        </footer>
    );
}

export default Footer;
