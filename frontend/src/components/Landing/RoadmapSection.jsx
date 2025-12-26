import { useTranslation } from 'react-i18next';
import { Shield, Calendar, Users, Cpu, TrendingUp, Clock, DollarSign, Filter } from 'lucide-react';

/**
 * Roadmap section with priority-based feature cards
 */
export function RoadmapSection() {
    const { t } = useTranslation();

    const roadmapItems = [
        // P0 - 安全性与可运营性
        {
            priority: 'P0',
            titleKey: 'landing.roadmap.risk.title',
            descriptionKey: 'landing.roadmap.risk.description',
            icon: Shield,
            statusKey: 'landing.status.planned',
            statusType: 'planned',
        },
        // P1 - 体验与分析能力增强
        {
            priority: 'P1',
            titleKey: 'landing.roadmap.advancedOrders.title',
            descriptionKey: 'landing.roadmap.advancedOrders.description',
            icon: TrendingUp,
            statusKey: 'landing.status.planned',
            statusType: 'planned',
        },
        {
            priority: 'P1',
            titleKey: 'landing.roadmap.multiTimeframe.title',
            descriptionKey: 'landing.roadmap.multiTimeframe.description',
            icon: Clock,
            statusKey: 'landing.status.planned',
            statusType: 'planned',
        },
        {
            priority: 'P1',
            titleKey: 'landing.roadmap.costSlippage.title',
            descriptionKey: 'landing.roadmap.costSlippage.description',
            icon: DollarSign,
            statusKey: 'landing.status.planned',
            statusType: 'planned',
        },
        {
            priority: 'P1',
            titleKey: 'landing.roadmap.filters.title',
            descriptionKey: 'landing.roadmap.filters.description',
            icon: Filter,
            statusKey: 'landing.status.planned',
            statusType: 'planned',
        },
        {
            priority: 'P1',
            titleKey: 'landing.roadmap.scheduler.title',
            descriptionKey: 'landing.roadmap.scheduler.description',
            icon: Calendar,
            statusKey: 'landing.status.planned',
            statusType: 'planned',
        },
        // P2 - 多租户与平台化
        {
            priority: 'P2',
            titleKey: 'landing.roadmap.team.title',
            descriptionKey: 'landing.roadmap.team.description',
            icon: Users,
            statusKey: 'landing.status.planned',
            statusType: 'planned',
        },
        {
            priority: 'P2',
            titleKey: 'landing.roadmap.ml.title',
            descriptionKey: 'landing.roadmap.ml.description',
            icon: Cpu,
            statusKey: 'landing.status.planned',
            statusType: 'planned',
        },
    ];

    return (
        <section id="roadmap" className="landing-section">
            {/* Background */}
            <div className="landing-hero-bg landing-grid-pattern" style={{ opacity: 0.2 }} />

            <div className="landing-container">
                {/* Section Header */}
                <div className="landing-section-header">
                    <span className="landing-section-badge">
                        {t('landing.roadmap.badge')}
                    </span>
                    <h2 className="landing-section-title">
                        {t('landing.roadmap.title')}
                    </h2>
                    <p className="landing-section-description">
                        {t('landing.roadmap.description')}
                    </p>
                </div>

                {/* Priority Legend */}
                <div className="landing-roadmap-legend">
                    <div className="landing-roadmap-legend-item">
                        <div className="landing-roadmap-legend-dot landing-roadmap-legend-dot-p0" />
                        <span className="landing-roadmap-legend-text">
                            P0 - {t('landing.priority.p0')}
                        </span>
                    </div>
                    <div className="landing-roadmap-legend-item">
                        <div className="landing-roadmap-legend-dot landing-roadmap-legend-dot-p1" />
                        <span className="landing-roadmap-legend-text">
                            P1 - {t('landing.priority.p1')}
                        </span>
                    </div>
                    <div className="landing-roadmap-legend-item">
                        <div className="landing-roadmap-legend-dot landing-roadmap-legend-dot-p2" />
                        <span className="landing-roadmap-legend-text">
                            P2 - {t('landing.priority.p2')}
                        </span>
                    </div>
                </div>

                {/* Roadmap Grid */}
                <div className="landing-roadmap-grid">
                    {roadmapItems.map((item) => {
                        const Icon = item.icon;
                        return (
                            <div
                                key={item.titleKey}
                                className="landing-roadmap-card landing-animate-fade-in"
                            >
                                {/* Priority Badge */}
                                <div className={`landing-roadmap-priority landing-roadmap-priority-${item.priority.toLowerCase()}`}>
                                    {item.priority}
                                </div>

                                {/* Icon */}
                                <div className="landing-roadmap-icon">
                                    <Icon />
                                </div>

                                {/* Content */}
                                <h3 className="landing-roadmap-title">
                                    {t(item.titleKey)}
                                </h3>
                                <p className="landing-roadmap-description">
                                    {t(item.descriptionKey)}
                                </p>

                                {/* Status */}
                                <div className={`landing-roadmap-status landing-roadmap-status-${item.statusType}`}>
                                    {t(item.statusKey)}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </section>
    );
}

export default RoadmapSection;
