import React, { useState, useEffect } from 'react';
import { NavTab, FarmInput, PredictionResult, DEFAULT_FARM_INPUT } from './types';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { DashboardView } from './components/DashboardView';
import { PredictionView } from './components/PredictionView';
import { ExplainableAiView } from './components/ExplainableAiView';
import { DecisionSupportView } from './components/DecisionSupportView';
import { WhatIfSimulationView } from './components/WhatIfSimulationView';
import { EdaView } from './components/EdaView';
import { DatasetView } from './components/DatasetView';

export default function App() {
  const [currentTab, setCurrentTab] = useState<NavTab>('dashboard');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const [isDark, setIsDark] = useState<boolean>(() => {
    return localStorage.getItem('theme') === 'dark';
  });

  // Application data state. `prediction` starts as null -- there is no fake
  // initial result. The Dashboard/Explainable AI/Decision Support/What-If
  // pages all show an empty state until a real prediction has been made.
  const [farmInput, setFarmInput] = useState<FarmInput>(DEFAULT_FARM_INPUT);
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);

  useEffect(() => {
    const root = document.documentElement;
    if (isDark) {
      root.classList.add('dark');
      root.classList.remove('light');
      localStorage.setItem('theme', 'dark');
    } else {
      root.classList.remove('dark');
      root.classList.add('light');
      localStorage.setItem('theme', 'light');
    }
  }, [isDark]);

  const toggleTheme = () => setIsDark((prev) => !prev);

  return (
    <div className="bg-background text-on-background font-body-lg min-h-screen flex antialiased">
      <Sidebar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        mobileOpen={mobileMenuOpen}
        onCloseMobile={() => setMobileMenuOpen(false)}
      />

      <main className="flex-1 md:ml-64 flex flex-col min-h-screen">
        <Header
          currentTab={currentTab}
          onToggleMobileMenu={() => setMobileMenuOpen((prev) => !prev)}
          isDark={isDark}
          onToggleTheme={toggleTheme}
        />

        <div className="flex-1 p-4 md:p-8 max-w-[1440px] mx-auto w-full">
          {currentTab === 'dashboard' && (
            <DashboardView
              farmInput={farmInput}
              prediction={prediction}
              onNavigateTab={setCurrentTab}
            />
          )}

          {currentTab === 'prediction' && (
            <PredictionView
              farmInput={farmInput}
              onUpdateFarmInput={setFarmInput}
              onUpdatePrediction={setPrediction}
              onNavigateTab={setCurrentTab}
            />
          )}

          {currentTab === 'explainable-ai' && (
            <ExplainableAiView prediction={prediction} onNavigateTab={setCurrentTab} />
          )}

          {currentTab === 'decision-support' && (
            <DecisionSupportView prediction={prediction} onNavigateTab={setCurrentTab} />
          )}

          {currentTab === 'what-if' && (
            <WhatIfSimulationView farmInput={farmInput} basePrediction={prediction} />
          )}

          {currentTab === 'eda' && <EdaView />}

          {currentTab === 'dataset' && <DatasetView />}
        </div>
      </main>
    </div>
  );
}
