import { useTranslation } from 'react-i18next';
import { FileCode, Play, BarChart2, Rocket, ArrowRight } from 'lucide-react';

/**
 * Workflow section showing the 4-step process
 */
export function WorkflowSection() {
    const { t } = useTranslation();

    const steps = [
        {
            icon: FileCode,
            number: '01',
            titleKey: 'landing.workflow.step1.title',
            descriptionKey: 'landing.workflow.step1.description',
        },
        {
            icon: Play,
            number: '02',
            titleKey: 'landing.workflow.step2.title',
            descriptionKey: 'landing.workflow.step2.description',
        },
        {
            icon: BarChart2,
            number: '03',
            titleKey: 'landing.workflow.step3.title',
            descriptionKey: 'landing.workflow.step3.description',
        },
        {
            icon: Rocket,
            number: '04',
            titleKey: 'landing.workflow.step4.title',
            descriptionKey: 'landing.workflow.step4.description',
        },
    ];

    return (
        <section id="workflow" className="landing-section">
            <div className="landing-container">
                {/* Section Header */}
                <div className="landing-section-header">
                    <span className="landing-section-badge">
                        {t('landing.workflow.badge')}
                    </span>
                    <h2 className="landing-section-title">
                        {t('landing.workflow.title')}
                    </h2>
                    <p className="landing-section-description">
                        {t('landing.workflow.description')}
                    </p>
                </div>

                {/* Workflow Steps */}
                <div className="landing-workflow-steps">
                    {/* Connection Line */}
                    <div className="landing-workflow-line" />

                    {steps.map((step, index) => {
                        const Icon = step.icon;
                        const isLast = index === steps.length - 1;

                        return (
                            <div
                                key={step.number}
                                className="landing-workflow-step landing-animate-fade-in"
                                style={{ animationDelay: `${index * 0.15}s` }}
                            >
                                {/* Card */}
                                <div className="landing-workflow-card">
                                    {/* Number */}
                                    <div className="landing-workflow-number">
                                        {step.number}
                                    </div>

                                    {/* Icon */}
                                    <div className="landing-workflow-icon">
                                        <Icon />
                                    </div>

                                    {/* Content */}
                                    <h3 className="landing-workflow-title">
                                        {t(step.titleKey)}
                                    </h3>
                                    <p className="landing-workflow-description">
                                        {t(step.descriptionKey)}
                                    </p>
                                </div>

                                {/* Arrow */}
                                {!isLast && (
                                    <div className="landing-workflow-arrow">
                                        <ArrowRight />
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>
        </section>
    );
}

export default WorkflowSection;
