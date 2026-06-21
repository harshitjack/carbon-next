/**
 * App — Main application layout with ARIA landmarks.
 *
 * Accessibility features:
 *   - role="banner" on header
 *   - <nav aria-label="Main navigation">
 *   - id="main-content" tabIndex={-1} as skip-link target
 *   - role="contentinfo" on footer
 *   - Error boundary wraps the entire app
 */

import { useEffect } from 'react';
import { ErrorBoundary } from './components/shared/ErrorBoundary';
import { SkipLink } from './components/shared/SkipLink';
import { LoadingSpinner } from './components/shared/LoadingSpinner';
import { CarbonForm } from './components/Calculator/CarbonForm';
import { ResultsDisplay } from './components/Calculator/ResultsDisplay';
import { InsightsList } from './components/Insights/InsightsList';
import { HistoryChart } from './components/History/HistoryChart';
import { HistoryTable } from './components/History/HistoryTable';
import { useCarbonStore } from './store/carbonStore';

const NavLink = ({
  icon,
  label,
  active,
  onClick,
}: {
  icon: string;
  label: string;
  active: boolean;
  onClick: () => void;
}) => (
  <button
    onClick={onClick}
    aria-current={active ? 'page' : undefined}
    className={`
      flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
      focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-slate-950
      ${
        active
          ? 'bg-slate-800 text-slate-50 shadow-sm'
          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
      }
    `}
  >
    <span aria-hidden="true">{icon}</span>
    {label}
  </button>
);

function AppContent() {
  const step = useCarbonStore(s => s.step);
  const setStep = useCarbonStore(s => s.setStep);
  const result = useCarbonStore(s => s.result);
  const insights = useCarbonStore(s => s.insights);
  const history = useCarbonStore(s => s.history);
  const isLoadingHistory = useCarbonStore(s => s.isLoadingHistory);
  const fetchHistory = useCarbonStore(s => s.fetchHistory);
  const reset = useCarbonStore(s => s.reset);

  const handleHistoryClick = () => {
    setStep('history');
    fetchHistory();
  };

  // Focus main content area on step change (for keyboard/screen reader users)
  useEffect(() => {
    const main = document.getElementById('main-content');
    if (main) main.focus();
  }, [step]);

  // Ambient cursor glow using requestAnimationFrame for high performance
  useEffect(() => {
    let rafId: number;
    const updateMousePosition = (ev: MouseEvent) => {
      if (rafId) cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(() => {
        document.documentElement.style.setProperty('--x', `${ev.clientX}px`);
        document.documentElement.style.setProperty('--y', `${ev.clientY}px`);
      });
    };
    window.addEventListener('mousemove', updateMousePosition);
    return () => {
      window.removeEventListener('mousemove', updateMousePosition);
      if (rafId) cancelAnimationFrame(rafId);
    };
  }, []);

  return (
    <div className="min-h-screen relative overflow-x-hidden selection:bg-primary-500/30 selection:text-primary-200">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-slate-950 -z-10 pointer-events-none" />
      <div className="cursor-glow" />
      
      {/* Skip Link */}
      <SkipLink />

      {/* ------------------------------------------------------------------ */}
      {/* Header / Navigation                                                  */}
      {/* ------------------------------------------------------------------ */}
      <header
        role="banner"
        className="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-md border-b border-slate-800 shadow-sm"
      >
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          {/* Logo */}
          <button
            onClick={reset}
            aria-label="Carbon Footprint Platform — return to calculator"
            className="flex items-center gap-3 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded-lg p-1"
          >
            <div className="w-8 h-8 rounded bg-primary-600 flex items-center justify-center" aria-hidden="true">
              <span className="text-white text-sm font-bold">ET</span>
            </div>
            <div className="text-left">
              <span className="block text-sm font-bold text-slate-100 tracking-tight leading-tight">
                EcoTracker
              </span>
              <span className="block text-xs text-slate-400 font-medium leading-tight tracking-wide">
                Carbon Platform
              </span>
            </div>
          </button>

          {/* Navigation */}
          <nav aria-label="Main navigation">
            <ul className="flex items-center gap-2 list-none m-0 p-0">
              <li>
                <NavLink
                  icon="🌿"
                  label="Footprint"
                  active={step === 'form' || step === 'results'}
                  onClick={() => setStep(result ? 'results' : 'form')}
                />
              </li>
              <li>
                <NavLink icon="📈" label="Timeline" active={step === 'history'} onClick={handleHistoryClick} />
              </li>
            </ul>
          </nav>
        </div>
      </header>

      {/* ------------------------------------------------------------------ */}
      {/* Hero Banner (only on form step)                                      */}
      {/* ------------------------------------------------------------------ */}
      {step === 'form' && (
        <div className="relative py-16 px-4 overflow-hidden">
          <div className="max-w-3xl mx-auto text-center relative z-10 animate-fade-in space-y-6">
            <h1 className="text-5xl sm:text-6xl font-black tracking-tight text-slate-50">
              Understand Your <br className="hidden sm:block" />
              <span className="text-primary-600">
                Emissions Impact
              </span>
            </h1>
            <p className="text-slate-400 text-lg sm:text-xl max-w-2xl mx-auto font-medium">
              Monitor your CO₂ output across lifestyle categories and get personalised AI-driven strategies to cut emissions.
            </p>
            <div className="flex flex-wrap justify-center gap-4 sm:gap-6 pt-4 text-sm font-medium text-slate-300">
              <span className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-900/50 border border-slate-800 shadow-sm backdrop-blur-md">
                <span className="w-1.5 h-1.5 rounded-full bg-primary-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]" aria-hidden="true" />
                Peer-reviewed data
              </span>
              <span className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-900/50 border border-slate-800 shadow-sm backdrop-blur-md">
                <span className="w-1.5 h-1.5 rounded-full bg-secondary-500 shadow-[0_0_8px_rgba(6,182,212,0.8)]" aria-hidden="true" />
                OpenRouter AI insights
              </span>
              <span className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-900/50 border border-slate-800 shadow-sm backdrop-blur-md">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-500" aria-hidden="true" />
                Anonymous &amp; secure
              </span>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Main Content                                                         */}
      {/* ------------------------------------------------------------------ */}
      <main
        id="main-content"
        tabIndex={-1}
        aria-label="Main content"
        className="max-w-4xl mx-auto px-4 sm:px-6 py-8 focus:outline-none"
      >
        {step === 'form' && <CarbonForm />}

        {step === 'results' && result && (
          <div className="space-y-8">
            {/* Back button */}
            <button
              onClick={() => setStep('form')}
              aria-label="Back to calculator form"
              className="
                flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200
                focus:outline-none focus:ring-2 focus:ring-primary-500 rounded-md px-2 py-1
                transition-colors duration-150
              "
            >
              <span aria-hidden="true">←</span> Back to Calculator
            </button>
            <ResultsDisplay result={result} />
            {insights && <InsightsList insightsResponse={insights} />}
          </div>
        )}

        {step === 'history' && (
          <div className="space-y-8">
            <div>
              <h1 className="text-3xl font-black text-slate-50 mb-2 tracking-tight">Telemetry History</h1>
              <p className="text-slate-400 text-sm">
                Track your footprint timeline to measure the impact of your actions.
              </p>
            </div>
            {isLoadingHistory ? (
              <div className="flex justify-center py-16">
                <LoadingSpinner label="Loading your history..." size="lg" />
              </div>
            ) : (
              <>
                <HistoryChart history={history} />
                <HistoryTable history={history} />
              </>
            )}
          </div>
        )}
      </main>

      {/* ------------------------------------------------------------------ */}
      {/* Footer                                                               */}
      {/* ------------------------------------------------------------------ */}
      <footer role="contentinfo" className="border-t border-slate-800/50 bg-slate-950 mt-16 py-10 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 mb-8">
            <div>
              <h2 className="text-sm font-semibold text-slate-300 mb-3 tracking-wide">Data Sources</h2>
              <ul className="text-xs text-slate-500 space-y-2 list-none">
                <li>UK DEFRA 2023 — Transport & Home Energy factors</li>
                <li>US EPA 2023 — Electricity grid emissions</li>
                <li>ICAO Carbon Calculator — Aviation emissions</li>
                <li>Our World in Data 2023 — Diet emissions & global average</li>
                <li>IPCC AR6 / SR1.5 — Consumption & Paris target</li>
              </ul>
            </div>
            <div>
              <h2 className="text-sm font-semibold text-slate-300 mb-3 tracking-wide">About</h2>
              <p className="text-xs text-slate-500 leading-relaxed">
                This tooling provides estimates for educational purposes based on peer-reviewed
                emission factors. Individual results may vary based on local grid mix, vehicle
                efficiency, and personal circumstances.
              </p>
            </div>
          </div>
          <div className="border-t border-slate-800/50 pt-6 flex flex-col sm:flex-row justify-between items-center gap-4 text-xs text-slate-600">
            <span>© 2026 EcoTracker Network</span>
            <span className="flex items-center gap-2">
              Powered by{' '}
              <span aria-label="Google Gemini AI" className="font-medium text-slate-400">
                Gemini
              </span>{' '}
              <span className="text-slate-700">|</span>{' '}
              <span aria-label="Google Cloud" className="font-medium text-slate-400">
                Google Cloud
              </span>
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <AppContent />
    </ErrorBoundary>
  );
}
