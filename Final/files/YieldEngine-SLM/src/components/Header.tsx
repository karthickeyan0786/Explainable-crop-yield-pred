import React from 'react';
import { NavTab } from '../types';

interface HeaderProps {
  currentTab: NavTab;
  onToggleMobileMenu: () => void;
  isDark: boolean;
  onToggleTheme: () => void;
}

const TAB_TITLES: Record<NavTab, string> = {
  'dashboard': 'Main Dashboard',
  'prediction': 'Crop Yield Prediction Tool',
  'explainable-ai': 'Explainable AI & SHAP Attribution',
  'decision-support': 'Agronomic Decision Support System',
  'what-if': 'What-If Scenario Simulation Lab',
  'eda': 'Exploratory Data Analysis (EDA)',
  'dataset': 'Dataset Overview & Model Performance'
};

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  onToggleMobileMenu,
  isDark,
  onToggleTheme,
}) => {
  return (
    <header className="bg-surface-container-lowest dark:bg-surface-container-lowest border-b border-outline-variant flex justify-between items-center w-full px-4 md:px-8 py-4 z-30 sticky top-0">
      <div className="flex items-center">
        {/* Mobile Menu Toggle */}
        <button 
          onClick={onToggleMobileMenu}
          className="md:hidden mr-4 text-primary p-2 hover:bg-surface-container-high transition-colors"
          aria-label="Toggle Navigation Menu"
        >
          <span className="material-symbols-outlined">menu</span>
        </button>
        <h1 className="font-headline-md text-headline-md font-bold text-primary dark:text-primary-fixed md:hidden text-lg">
          Yield Engine v2.4
        </h1>
        <h1 className="hidden md:block font-headline-md text-headline-md font-bold text-primary dark:text-primary-fixed">
          {TAB_TITLES[currentTab]}
        </h1>
      </div>

      <div className="flex items-center space-x-3">
        <div className="hidden sm:flex items-center space-x-2 border border-outline-variant px-3 py-1 text-xs font-data-mono bg-surface-container-low text-on-surface-variant">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>ENGINE ONLINE v2.4</span>
        </div>

        {/* Theme Toggle Button */}
        <button
          id="theme-toggle"
          onClick={onToggleTheme}
          className="text-on-surface-variant hover:bg-surface-container-high transition-colors duration-150 p-2 cursor-pointer active:opacity-80 rounded-none border border-outline-variant flex items-center justify-center"
          aria-label="Toggle Theme"
          title={isDark ? "Switch to Light Mode" : "Switch to Field & Logic Dark"}
        >
          {isDark ? (
            <span className="material-symbols-outlined text-[20px]">light_mode</span>
          ) : (
            <span className="material-symbols-outlined text-[20px]">dark_mode</span>
          )}
        </button>

        <button 
          className="text-on-surface-variant hover:bg-surface-container-high transition-colors p-2 rounded-none border border-outline-variant"
          title="System Notifications"
        >
          <span className="material-symbols-outlined text-[20px]">notifications</span>
        </button>
        
        <button 
          className="text-on-surface-variant hover:bg-surface-container-high transition-colors p-2 rounded-none border border-outline-variant"
          title="Settings & Configuration"
        >
          <span className="material-symbols-outlined text-[20px]">settings</span>
        </button>
      </div>
    </header>
  );
};
