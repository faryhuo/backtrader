import { useTranslation } from 'react-i18next';
import { Shield, GitBranch, BarChart3, Calendar, Users, Activity, Cpu, Zap } from 'lucide-react';

/**
 * Roadmap section with priority-based feature cards
 */
export function RoadmapSection() {
    const { t } = useTranslation();

    const roadmapItems = [
        {
            priority: 'P0',
            titleKey: 'landing.roadmap.item5.title',
            descriptionKey: 'landing.roadmap.item5.description',
            icon: Shield,
            statusKey: 'landing.status.planned',
            statusType: 'planned',
        },
        {
            priority: 'P0',
            titleKey: 'landing.roadmap.item6.title',
            descriptionKey: 'landing.roadmap.item6.description',
            icon: GitBranch,
            statusKey: 'landing.status.in_dev',
            statusType: 'dev',
        },
        {
            priority: 'P1',
            titleKey: 'landing.roadmap.item1.title',
            descriptionKey: 'landing.roadmap.item1.description',
            icon: BarChart3,
            statusKey: 'landing.status.done',
            statusType: 'done',
        },
        {
            priority: 'P1',
            titleKey: 'landing.roadmap.item7.title',
            descriptionKey: 'landing.roadmap.item7.description',
            icon: Calendar,
            statusKey: 'landing.status.planned',
            statusType: 'planned',
        },
        {
            priority: 'P2',
            titleKey: 'landing.roadmap.item8.title',
            descriptionKey: 'landing.roadmap.item8.description',
            icon: Users,
            statusKey: 'landing.status.planned',
            statusType: 'planned',
        },
        {
            priority: 'P2',
            titleKey: 'landing.roadmap.item2.title',
            descriptionKey: 'landing.roadmap.item2.description',
            icon: Activity,
            statusKey: 'landing.status.done',
            statusType: 'done',
        },
        {
            priority: 'P2',
            titleKey: 'landing.roadmap.item3.title',
            descriptionKey: 'landing.roadmap.item3.description',
            icon: Cpu,
            statusKey: 'landing.status.done',
            statusType: 'done',
        },
        {
            priority: 'P2',
            titleKey: 'landing.roadmap.item4.title',
            descriptionKey: 'landing.roadmap.item4.description',
            icon: Zap,
            statusKey: 'landing.status.done',
            statusType: 'done',
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
