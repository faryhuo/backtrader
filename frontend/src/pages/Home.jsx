import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { SiteConfigProvider } from '../contexts/SiteConfigContext';
import {
    Navbar,
    HeroSection,
    FeaturesSection,
    WorkflowSection,
    RoadmapSection,
    CTASection,
    Footer
} from '../components/Landing';
import './landing.css';

/**
 * Home/Landing Page
 *
 * Landing page for the Backtrader Pro platform.
 * Displays features, workflow, roadmap, and CTA sections.
 * Automatically redirects authenticated users to the app.
 */
export function Home() {
    const { isAuthenticated, loginEnabled } = useAuth();
    const navigate = useNavigate();

    // Redirect to main app if already authenticated
    useEffect(() => {
        if (loginEnabled && isAuthenticated) {
            navigate('/strategy');
        }
    }, [isAuthenticated, loginEnabled, navigate]);

    return (
        <SiteConfigProvider>
            <div className="landing-page">
                <Navbar />
                <main>
                    <HeroSection />
                    <FeaturesSection />
                    <WorkflowSection />
                    <RoadmapSection />
                    <CTASection />
                </main>
                <Footer />
            </div>
        </SiteConfigProvider>
    );
}

export default Home;