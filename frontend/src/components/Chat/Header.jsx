import React from 'react';
import { Menu, PanelLeft, Sun, Moon, RefreshCw, Compass } from 'lucide-react';

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
    <header className="sticky top-0 z-30 h-15 bg-[#F3EEE3]/95 dark:bg-[#111111]/95 backdrop-blur-md border-b border-[#DDD4C3] dark:border-[#2F2B25] px-4 sm:px-6 flex items-center justify-between transition-colors duration-200">
      {/* Left: Navigation toggle & Title */}
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={onToggleMobileSidebar}
          title="Open Menu"
          aria-label="Open Menu"
          className="p-2 text-[#6B665E] hover:text-[#111111] dark:text-[#A69E92] dark:hover:text-white rounded-lg hover:bg-[#E6DED0] dark:hover:bg-[#22201D] lg:hidden cursor-pointer transition-colors"
        >
          <Menu className="w-5 h-5" />
        </button>

        <button
          onClick={onToggleSidebarCollapse}
          title={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-label={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          className="hidden lg:flex p-2 text-[#6B665E] hover:text-[#111111] dark:text-[#A69E92] dark:hover:text-white rounded-lg hover:bg-[#E6DED0] dark:hover:bg-[#22201D] cursor-pointer transition-colors"
        >
          <PanelLeft
            className={`w-4 h-4 transition-transform duration-200 ${
              isSidebarCollapsed ? 'rotate-180 text-[#D9541E]' : ''
            }`}
          />
        </button>

        <div className="flex items-center gap-2.5 min-w-0">
          {isSidebarCollapsed && (
            <div className="hidden lg:flex w-7 h-7 rounded-md bg-[#D9541E] items-center justify-center text-white shrink-0">
              <Compass className="w-4 h-4" />
            </div>
          )}
          <div className="min-w-0">
            <h2 className="font-heading font-bold text-[#111111] dark:text-[#F3EEE3] text-sm sm:text-base tracking-tight truncate">
              {currentTitle || 'BizAdvisor'}
            </h2>
            <p className="text-[11px] text-[#6B665E] dark:text-[#A69E92] hidden sm:block truncate">
              Hospitality Market & Financial Advisory
            </p>
          </div>
        </div>
      </div>

      {/* Right: Engine status, Theme toggle, New Analysis */}
      <div className="flex items-center gap-2 sm:gap-2.5 shrink-0">
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#E6DED0]/70 dark:bg-[#1E1C19] border border-[#D4C9B6] dark:border-[#2F2B25] text-[11px] font-semibold text-[#254C3B] dark:text-[#4C9A77]">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#254C3B] dark:bg-[#4C9A77]" />
          <span>AI Ready</span>
        </div>

        <button
          onClick={onToggleTheme}
          title={`Switch to ${theme === 'dark' ? 'Cream Editorial' : 'Ink Dark'} Mode`}
          aria-label={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
          className="px-2.5 py-1.5 rounded-lg text-[#111111] dark:text-[#F3EEE3] bg-white dark:bg-[#1A1917] hover:bg-[#EAE3D5] dark:hover:bg-[#24221E] border border-[#DDD4C3] dark:border-[#2F2B25] transition-colors cursor-pointer flex items-center gap-1.5 text-xs font-medium"
        >
          {theme === 'dark' ? (
            <>
              <Sun className="w-3.5 h-3.5 text-[#D9541E]" />
              <span className="hidden md:inline">Cream</span>
            </>
          ) : (
            <>
              <Moon className="w-3.5 h-3.5 text-[#111111]" />
              <span className="hidden md:inline">Ink</span>
            </>
          )}
        </button>

        <button
          onClick={onNewAnalysis}
          title="Reset conversation"
          className="px-2.5 py-1.5 text-[#6B665E] hover:text-[#111111] dark:text-[#A69E92] dark:hover:text-white rounded-lg hover:bg-[#E6DED0] dark:hover:bg-[#22201D] border border-transparent hover:border-[#D4C9B6] dark:hover:border-[#2F2B25] transition-colors hidden sm:flex items-center gap-1.5 text-xs font-medium cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span className="hidden md:inline">Reset</span>
        </button>
      </div>
    </header>
  );
}
