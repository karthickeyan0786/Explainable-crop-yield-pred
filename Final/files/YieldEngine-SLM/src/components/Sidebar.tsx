import React from 'react';
import { NavTab } from '../types';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

interface NavItem {
  id: NavTab;
  label: string;
  icon: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
  { id: 'prediction', label: 'Prediction', icon: 'analytics' },
  { id: 'explainable-ai', label: 'Explainable AI', icon: 'psychology' },
  { id: 'decision-support', label: 'Decision Support', icon: 'lightbulb' },
  { id: 'what-if', label: 'What-If Simulation', icon: 'rule' },
  { id: 'eda', label: 'EDA', icon: 'insights' },
  { id: 'dataset', label: 'Dataset', icon: 'database' }
];

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  mobileOpen,
  onCloseMobile
}) => {
  const sidebarContent = (
    <div className="flex flex-col h-full">
      <div className="px-6 py-5 mb-4 border-b border-outline-variant">
        <h2 className="font-headline-md text-headline-md text-primary dark:text-primary-fixed truncate">
          Yield Engine v2.4
        </h2>
        <p className="font-label-caps text-label-caps text-on-surface-variant mt-1 uppercase tracking-wider">
          Analysis Ready
        </p>
      </div>

      <ul className="flex-1 px-4 space-y-1.5 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const isActive = currentTab === item.id;
          return (
            <li key={item.id}>
              <button
                onClick={() => {
                  onSelectTab(item.id);
                  onCloseMobile();
                }}
                className={`w-full text-left flex items-center px-4 py-3 font-medium border-l-4 transition-all cursor-pointer select-none rounded-none ${
                  isActive
                    ? 'bg-primary text-on-primary font-bold border-primary dark:bg-primary-container dark:text-on-primary-container dark:border-primary-fixed'
                    : 'text-on-surface-variant border-transparent hover:bg-surface-container-high'
                }`}
              >
                <span 
                  className="material-symbols-outlined mr-3 text-[20px]"
                  style={isActive ? { fontVariationSettings: "'FILL' 1" } : undefined}
                >
                  {item.icon}
                </span>
                <span className="font-label-caps text-label-caps uppercase tracking-wider">
                  {item.label}
                </span>
              </button>
            </li>
          );
        })}
      </ul>

      <div className="px-4 mt-auto space-y-1 border-t border-outline-variant pt-4 pb-4">
        <a 
          href="#documentation" 
          onClick={(e) => { e.preventDefault(); alert('Yield Engine v2.4 Agronomic Model Documentation & SHAP Attribution Manual v2.4'); }}
          className="flex items-center px-4 py-2 text-on-surface-variant hover:bg-surface-container-high transition-all"
        >
          <span className="material-symbols-outlined mr-3 text-[18px]">description</span>
          <span className="font-label-caps text-label-caps uppercase tracking-wider">Documentation</span>
        </a>
        <a 
          href="#support" 
          onClick={(e) => { e.preventDefault(); alert('Yield Engine Technical Support - Contact: ag-support@yieldengine.ai'); }}
          className="flex items-center px-4 py-2 text-on-surface-variant hover:bg-surface-container-high transition-all"
        >
          <span className="material-symbols-outlined mr-3 text-[18px]">help</span>
          <span className="font-label-caps text-label-caps uppercase tracking-wider">Support</span>
        </a>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <nav className="hidden md:flex flex-col bg-surface dark:bg-surface border-r border-outline-variant h-full w-64 fixed left-0 top-0 z-40">
        {sidebarContent}
      </nav>

      {/* Mobile Drawer Backdrop & Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div 
            className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity" 
            onClick={onCloseMobile}
          />
          <nav className="relative flex flex-col w-64 max-w-xs bg-surface dark:bg-surface h-full z-50 border-r border-outline-variant shadow-2xl">
            <button 
              onClick={onCloseMobile}
              className="absolute top-4 right-4 p-2 text-on-surface-variant"
            >
              <span className="material-symbols-outlined">close</span>
            </button>
            {sidebarContent}
          </nav>
        </div>
      )}
    </>
  );
};
