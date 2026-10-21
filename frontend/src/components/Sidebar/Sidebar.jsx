import React, { useState } from 'react';
import { PlusCircle, MessageSquare, Search, Trash2, User, X, Building2, PanelLeftClose, PanelLeft, Plus } from 'lucide-react';

export default function Sidebar({
  historyItems,
  currentSessionId,
  onSelectSession,
  onNewAnalysis,
  onDeleteSession,
  isOpen,
  onClose,
  isCollapsed,
  onToggleCollapse,
  currentUser,
  onOpenAuth,
  onLogout,
}) {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredHistory = historyItems.filter((item) => {
    const text = `${item.title} ${item.location} ${item.cuisine}`.toLowerCase();
    return text.includes(searchTerm.toLowerCase());
  });

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 left-0 bottom-0 z-50 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800/80 text-slate-700 dark:text-slate-300 flex flex-col transition-all duration-300 ease-in-out lg:static lg:translate-x-0 ${isOpen ? 'translate-x-0 w-72' : '-translate-x-full'
          } ${isCollapsed ? 'lg:w-16' : 'lg:w-64'}`}
      >
        {/* Top Header & Brand */}
        <div className={`p-3.5 border-b border-slate-200 dark:border-slate-800/80 flex items-center ${isCollapsed ? 'lg:justify-center' : 'justify-between'}`}>
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-500 flex items-center justify-center shadow-md shadow-indigo-500/20 text-white font-bold text-base shrink-0">
              <Building2 className="w-5 h-5" />
            </div>
            {!isCollapsed && (
              <div className="min-w-0">
                <h1 className="font-bold text-slate-900 dark:text-white text-base tracking-tight leading-none flex items-center gap-1.5">
                  <span className="truncate">BizAdvisor</span>
                  <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
                </h1>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 font-medium truncate mt-0.5">
                  AI Business Advisor
                </p>
              </div>
            )}
          </div>

          {/* Desktop Collapse Toggle Button */}
          {!isCollapsed && (
            <button
              onClick={onToggleCollapse}
              title="Collapse Sidebar"
              className="hidden lg:flex p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
            >
              <PanelLeftClose className="w-4 h-4" />
            </button>
          )}

          {/* Mobile Close Button */}
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 lg:hidden cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Action Button: New Analysis */}
        <div className="p-3 pb-2">
          <button
            onClick={() => {
              onNewAnalysis();
              if (isOpen) onClose();
            }}
            title={isCollapsed ? 'New Analysis' : undefined}
            className={`w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl transition-all shadow-md shadow-indigo-600/20 flex items-center justify-center gap-2 group cursor-pointer text-xs ${isCollapsed ? 'lg:px-0 lg:w-10 lg:h-10 lg:mx-auto' : 'px-3'
              }`}
          >
            <Plus className="w-4 h-4 shrink-0 transition-transform group-hover:rotate-90" />
            {!isCollapsed && <span className="truncate">New Analysis</span>}
          </button>
        </div>

        {/* Search Bar */}
        {!isCollapsed ? (
          <div className="px-3 py-1.5">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500" />
              <input
                type="text"
                placeholder="Search history..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-slate-100 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-800 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </div>
        ) : (
          <div className="px-2 py-1.5 hidden lg:flex justify-center">
            <button
              onClick={onToggleCollapse}
              title="Search / Expand Sidebar"
              className="p-2 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg cursor-pointer"
            >
              <Search className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* History List */}
        <div className="flex-1 overflow-y-auto px-2 py-1.5 space-y-1">
          {!isCollapsed && (
            <div className="px-2.5 py-1 text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
              Recent Analyses
            </div>
          )}

          {filteredHistory.length === 0 ? (
            !isCollapsed && (
              <div className="px-3 py-6 text-center text-xs text-slate-400 dark:text-slate-500">
                {searchTerm ? 'No matching analyses.' : 'No recent analyses.'}
              </div>
            )
          ) : (
            filteredHistory.map((item) => {
              const isActive = currentSessionId === item.id;
              return (
                <div
                  key={item.id}
                  onClick={() => {
                    onSelectSession(item.id);
                    if (isOpen) onClose();
                  }}
                  title={isCollapsed ? `${item.title} (${item.opportunity_score || 'N/A'})` : undefined}
                  className={`group relative flex items-center ${isCollapsed ? 'lg:justify-center lg:p-2' : 'justify-between p-2'
                    } rounded-xl cursor-pointer text-xs transition-all ${isActive
                      ? 'bg-indigo-50 dark:bg-slate-800/90 text-indigo-950 dark:text-white font-medium border border-indigo-200 dark:border-slate-700 shadow-xs'
                      : 'hover:bg-slate-100 dark:hover:bg-slate-800/50 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                    }`}
                >
                  <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-2.5 min-w-0 pr-5'}`}>
                    <MessageSquare className={`w-4 h-4 shrink-0 ${isActive ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400 dark:text-slate-500'}`} />
                    {!isCollapsed && (
                      <div className="truncate">
                        <div className="truncate font-medium text-slate-800 dark:text-slate-200 text-xs">{item.title}</div>
                        <div className="text-[10px] text-slate-400 dark:text-slate-500 truncate mt-0.5">
                          ₹{item.approx_cost ? Number(item.approx_cost).toLocaleString('en-IN') : 'N/A'} · Score:{' '}
                          <span className="text-emerald-600 dark:text-emerald-400 font-semibold">{item.opportunity_score || 'N/A'}</span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Delete Item Button (Expanded View) */}
                  {!isCollapsed && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteSession(item.id);
                      }}
                      title="Delete entry"
                      className="opacity-0 group-hover:opacity-100 p-1 hover:text-rose-500 dark:hover:text-rose-400 text-slate-400 transition-opacity cursor-pointer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* User Profile Footer */}
        <div className={`p-2.5 border-t border-slate-200 dark:border-slate-800/80 bg-slate-50 dark:bg-slate-950/40 flex items-center ${isCollapsed ? 'justify-center' : 'justify-between'}`}>
          <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-2.5 min-w-0'}`}>
            <div
              title={currentUser ? currentUser.username : 'Sign In'}
              onClick={currentUser ? undefined : onOpenAuth}
              className={`w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 flex items-center justify-center text-xs font-bold text-slate-700 dark:text-slate-300 shrink-0 ${!currentUser ? 'cursor-pointer hover:border-indigo-500' : ''}`}
            >
              <User className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
            </div>
            {!isCollapsed && (
              <div className="min-w-0 flex-1">
                {currentUser ? (
                  <>
                    <div className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">{currentUser.username}</div>
                    <div className="text-[10px] text-slate-500 dark:text-slate-400 truncate">{currentUser.email || 'Authenticated User'}</div>
                  </>
                ) : (
                  <button
                    onClick={onOpenAuth}
                    className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline cursor-pointer text-left"
                  >
                    Sign In / Register
                  </button>
                )}
              </div>
            )}
          </div>

          {!isCollapsed && currentUser && (
            <button
              onClick={onLogout}
              title="Sign Out"
              className="text-[11px] font-medium text-slate-500 hover:text-rose-600 dark:text-slate-400 dark:hover:text-rose-400 px-2 py-1 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors cursor-pointer"
            >
              Logout
            </button>
          )}

          {isCollapsed && (
            <button
              onClick={onToggleCollapse}
              title="Expand Sidebar"
              className="hidden lg:flex mt-2 p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
            >
              <PanelLeft className="w-4 h-4" />
            </button>
          )}
        </div>
      </aside>
    </>
  );
}
