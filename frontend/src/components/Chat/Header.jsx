import React from 'react';
import { Menu, PanelLeft, Sun, Moon, RefreshCw, Building2 } from 'lucide-react';

export default function Header({
  isSidebarCollapsed,
  onToggleSidebarCollapse,
  onToggleMobileSidebar,
  theme,
  onToggleTheme,
  onNewAnalysis,
  currentTitle,
}) {
  return (
    <header className="sticky top-0 z-30 h-16 bg-white/90 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800/80 px-4 lg:px-6 flex items-center justify-between transition-colors duration-200">
      {/* Left section: Mobile Menu, Sidebar Collapse Toggle & Title */}
      <div className="flex items-center gap-3 min-w-0">
        {/* Mobile menu drawer button */}
        <button
          onClick={onToggleMobileSidebar}
          title="Open Menu"
          aria-label="Open Menu"
          className="p-2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 lg:hidden cursor-pointer transition-colors"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Desktop Sidebar Collapse Toggle Button */}
        <button
          onClick={onToggleSidebarCollapse}
          title={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-label={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          className="hidden lg:flex p-2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
        >
          <PanelLeft className={`w-5 h-5 transition-transform duration-200 ${isSidebarCollapsed ? 'rotate-180 text-indigo-600 dark:text-indigo-400' : ''}`} />
        </button>

        <div className="flex items-center gap-2.5 min-w-0">
          {isSidebarCollapsed && (
            <div className="hidden lg:flex w-7 h-7 rounded-lg bg-indigo-600 items-center justify-center text-white font-bold text-xs shrink-0 shadow-xs">
              <Building2 className="w-4 h-4" />
            </div>
          )}
          <div className="min-w-0">
            <h2 className="font-bold text-slate-900 dark:text-slate-100 text-sm sm:text-base tracking-tight truncate flex items-center gap-2">
              {currentTitle || 'BizAdvisor'}
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 hidden sm:block truncate">Business Intelligence Assistant</p>
          </div>
        </div>
      </div>

      {/* Right section: Theme Toggle, AI Status, Reset */}
      <div className="flex items-center gap-2 sm:gap-3 shrink-0">
        {/* AI Ready Status Badge */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700/60 text-xs font-medium text-emerald-600 dark:text-emerald-400">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span>AI Ready</span>
        </div>

        {/* Light / Dark Mode Toggle Button */}
        <button
          onClick={onToggleTheme}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
          aria-label={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
          className="p-2 rounded-xl text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition-all duration-200 cursor-pointer flex items-center gap-1.5 text-xs font-semibold shadow-xs"
        >
          {theme === 'dark' ? (
            <>
              <Sun className="w-4 h-4 text-amber-400" />
              <span className="hidden md:inline">Light</span>
            </>
          ) : (
            <>
              <Moon className="w-4 h-4 text-indigo-600" />
              <span className="hidden md:inline">Dark</span>
            </>
          )}
        </button>

        {/* Reset / New Analysis Button */}
        <button
          onClick={onNewAnalysis}
          title="Reset conversation"
          className="p-2 text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors hidden sm:flex items-center gap-1.5 text-xs font-medium cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span className="hidden md:inline">Reset</span>
        </button>
      </div>
    </header>
  );
}
