import { useTranslation } from 'react-i18next';
import {
    LineChart,
    Brain,
    Layers,
    Zap,
    Shield,
    GitBranch,
    BarChart3,
    Radio,
    FileText,
    ClipboardList,
    PieChart
} from 'lucide-react';

/**
 * Features section with grid of feature cards
 */
export function FeaturesSection() {
    const { t } = useTranslation();

    const features = [
        {
            icon: LineChart,
            titleKey: 'landing.features.backtest.title',
            descriptionKey: 'landing.features.backtest.description',
            statusKey: 'landing.status.live',
            statusType: 'live',
        },
        {
            icon: Brain,
            titleKey: 'landing.features.ai.title',
            descriptionKey: 'landing.features.ai.description',
            statusKey: 'landing.status.live',
            statusType: 'live',
        },
        {
            icon: Layers,
            titleKey: 'landing.features.portfolio.title',
            descriptionKey: 'landing.features.portfolio.description',
            statusKey: 'landing.status.live',
            statusType: 'live',
        },
        {
            icon: BarChart3,
            titleKey: 'landing.features.optimization.title',
            descriptionKey: 'landing.features.optimization.description',
            statusKey: 'landing.status.live',
            statusType: 'live',
        },
        {
            icon: Radio,
            titleKey: 'landing.features.live.title',
            descriptionKey: 'landing.features.live.description',
            statusKey: 'landing.status.live',
            statusType: 'live',
        },
        {
            icon: GitBranch,
            titleKey: 'landing.features.versioning.title',
            descriptionKey: 'landing.features.versioning.description',
            statusKey: 'landing.status.live',
            statusType: 'live',
        },
        {
            icon: FileText,
            titleKey: 'landing.features.report.title',
            descriptionKey: 'landing.features.report.description',
            statusKey: 'landing.status.live',
            statusType: 'live',
        },
        {
            icon: PieChart,
            titleKey: 'landing.features.pyfolio.title',
            descriptionKey: 'landing.features.pyfolio.description',
            statusKey: 'landing.status.live',
            statusType: 'live',
        },
        {
            icon: ClipboardList,
            titleKey: 'landing.features.taskcenter.title',
            descriptionKey: 'landing.features.taskcenter.description',
            statusKey: 'landing.status.live',
            statusType: 'live',
        },
        {
            icon: Zap,
            titleKey: 'landing.features.realtime.title',
            descriptionKey: 'landing.features.realtime.description',
            statusKey: 'landing.status.live',
            statusType: 'live',
        },
        {
            icon: Shield,
            titleKey: 'landing.features.security.title',
            descriptionKey: 'landing.features.security.description',
            statusKey: 'landing.status.live',
            statusType: 'live',
        },
    ];

    return (
        <section id="features" className="landing-section">
            {/* Background */}
            <div className="landing-hero-bg landing-grid-pattern" style={{ opacity: 0.2 }} />

            <div className="landing-container">
                {/* Section Header */}
                <div className="landing-section-header">
                    <span className="landing-section-badge">
                        {t('landing.features.badge')}
                    </span>
                    <h2 className="landing-section-title">
                        {t('landing.features.title')}
                    </h2>
                    <p className="landing-section-description">
                        {t('landing.features.description')}
                    </p>
                </div>

                {/* Features Grid */}
                <div className="landing-features-grid">
                    {features.map((feature, index) => {
                        const Icon = feature.icon;
                        return (
                            <div
                                key={feature.titleKey}
                                className="landing-feature-card landing-animate-fade-in"
                                style={{ animationDelay: `${index * 0.1}s` }}
                            >
                                {/* Status Badge */}
                                <div className={`landing-feature-status landing-feature-status-${feature.statusType}`}>
                                    {t(feature.statusKey)}
                                </div>

                                {/* Icon */}
                                <div className="landing-feature-icon">
                                    <Icon />
                                </div>

                                {/* Content */}
                                <h3 className="landing-feature-title">
                                    {t(feature.titleKey)}
                                </h3>
                                <p className="landing-feature-description">
                                    {t(feature.descriptionKey)}
                                </p>
                            </div>
                        );
                    })}
                </div>
            </div>
        </section>
    );
}

export default FeaturesSection;
