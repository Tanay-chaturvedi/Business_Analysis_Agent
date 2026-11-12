import React, { useState } from 'react';
import { MessageSquare, Search, Trash2, User, X, Compass, PanelLeftClose, PanelLeft, Plus, LogOut } from 'lucide-react';

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
          className="fixed inset-0 bg-[#111111]/60 backdrop-blur-xs z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Ink Black Sidebar Container */}
      <aside
        className={`fixed top-0 left-0 bottom-0 z-50 bg-[#111111] dark:bg-[#0B0B0A] border-r border-white/10 text-[#E6DED0] flex flex-col transition-all duration-200 ease-in-out lg:static lg:translate-x-0 ${
          isOpen ? 'translate-x-0 w-72' : '-translate-x-full'
        } ${isCollapsed ? 'lg:w-16' : 'lg:w-64'}`}
      >
        {/* Top Header & Brand */}
        <div
          className={`p-4 border-b border-white/10 flex items-center ${
            isCollapsed ? 'lg:justify-center' : 'justify-between'
          }`}
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="h-8 w-8 rounded-lg bg-[#D9541E] flex items-center justify-center text-white font-bold shrink-0">
              <Compass className="w-4 h-4" />
            </div>
            {!isCollapsed && (
              <div className="min-w-0">
                <h1 className="font-heading font-bold text-white text-[15px] tracking-tight leading-none truncate">
                  BizAdvisor
                </h1>
                <p className="text-[10px] text-[#A69E92] font-medium tracking-wide uppercase truncate mt-1">
                  Business Intelligence
                </p>
              </div>
            )}
          </div>

          {!isCollapsed && (
            <button
              onClick={onToggleCollapse}
              title="Collapse Sidebar"
              className="hidden lg:flex p-1.5 rounded-md text-[#A69E92] hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
            >
              <PanelLeftClose className="w-4 h-4" />
            </button>
          )}

          <button
            onClick={onClose}
            className="p-1.5 rounded-md text-[#A69E92] hover:text-white hover:bg-white/10 lg:hidden cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Primary Action: New Analysis */}
        <div className="p-3 pb-2">
          <button
            onClick={() => {
              onNewAnalysis();
              if (isOpen) onClose();
            }}
            title={isCollapsed ? 'New Analysis' : undefined}
            className={`w-full py-2.5 editorial-btn-primary font-semibold rounded-lg flex items-center justify-center gap-2 group cursor-pointer text-xs ${
              isCollapsed ? 'lg:px-0 lg:w-10 lg:h-10 lg:mx-auto' : 'px-3'
            }`}
          >
            <Plus className="w-4 h-4 shrink-0" />
            {!isCollapsed && <span className="truncate">New Analysis</span>}
          </button>
        </div>

        {/* Search History */}
        {!isCollapsed ? (
          <div className="px-3 py-1.5">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[#8C857B]" />
              <input
                type="text"
                placeholder="Search analyses..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-[#1C1B19] border border-white/12 rounded-lg pl-8 pr-3 py-1.5 text-xs text-[#F3EEE3] placeholder-[#8C857B] focus:outline-none focus:border-[#D9541E] transition-colors"
              />
            </div>
          </div>
        ) : (
          <div className="px-2 py-1.5 hidden lg:flex justify-center">
            <button
              onClick={onToggleCollapse}
              title="Search / Expand Sidebar"
              className="p-2 text-[#A69E92] hover:text-white hover:bg-white/10 rounded-lg cursor-pointer"
            >
              <Search className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Recent Analyses List */}
        <div className="flex-1 overflow-y-auto px-2 py-2 space-y-0.5">
          {!isCollapsed && (
            <div className="px-2.5 py-1.5 text-[10px] font-semibold text-[#8C857B] uppercase tracking-[0.08em]">
              Recent Analyses
            </div>
          )}

          {filteredHistory.length === 0 ? (
            !isCollapsed && (
              <div className="px-3 py-6 text-center text-xs text-[#8C857B]">
                {searchTerm ? 'No matching analyses.' : 'No recent analyses yet.'}
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
                  className={`group relative flex items-center ${
                    isCollapsed ? 'lg:justify-center lg:p-2' : 'justify-between px-2.5 py-2'
                  } rounded-lg cursor-pointer text-xs transition-colors ${
                    isActive
                      ? 'bg-white/[0.09] text-white border-l-2 border-[#D9541E] font-medium'
                      : 'text-[#C8C1B6] hover:bg-white/[0.05] hover:text-white'
                  }`}
                >
                  <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-2.5 min-w-0 pr-5'}`}>
                    <MessageSquare
                      className={`w-3.5 h-3.5 shrink-0 ${
                        isActive ? 'text-[#D9541E]' : 'text-[#8C857B]'
                      }`}
                    />
                    {!isCollapsed && (
                      <div className="truncate">
                        <div className="truncate font-medium text-[#F3EEE3] text-xs">{item.title}</div>
                        <div className="text-[10px] text-[#8C857B] truncate mt-0.5 tabular-nums">
                          {item.approx_cost ? `₹${Number(item.approx_cost).toLocaleString('en-IN')}` : 'N/A'} · Score:{' '}
                          <span className="text-[#E6DED0] font-semibold">{item.opportunity_score ?? 'N/A'}</span>
                        </div>
                      </div>
                    )}
                  </div>

                  {!isCollapsed && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteSession(item.id);
                      }}
                      title="Delete entry"
                      className="opacity-0 group-hover:opacity-100 p-1 hover:text-[#E06C5B] text-[#8C857B] transition-opacity cursor-pointer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* User Profile & Logout Footer */}
        <div
          className={`p-3 border-t border-white/10 bg-[#0C0C0B] flex ${
            isCollapsed ? 'flex-col items-center gap-2' : 'items-center justify-between gap-2'
          }`}
        >
          <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-2.5 min-w-0'}`}>
            <div
              title={currentUser ? currentUser.username : 'Sign In'}
              onClick={currentUser ? undefined : onOpenAuth}
              className={`w-8 h-8 rounded-lg bg-[#22201D] border border-white/12 flex items-center justify-center text-xs font-bold text-[#F3EEE3] shrink-0 ${
                !currentUser ? 'cursor-pointer hover:border-[#D9541E]' : ''
              }`}
            >
              {currentUser?.username ? (
                <span className="uppercase text-[#D9541E]">{currentUser.username.slice(0, 2)}</span>
              ) : (
                <User className="w-4 h-4 text-[#D9541E]" />
              )}
            </div>
            {!isCollapsed && (
              <div className="min-w-0 flex-1">
                {currentUser ? (
                  <>
                    <div className="text-xs font-semibold text-white truncate">{currentUser.username}</div>
                    <div className="text-[10px] text-[#8C857B] truncate">{currentUser.email || 'Authenticated'}</div>
                  </>
                ) : (
                  <button
                    onClick={onOpenAuth}
                    className="text-xs font-semibold text-[#D9541E] hover:underline cursor-pointer text-left"
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
              className="flex items-center gap-1 text-[11px] font-medium text-[#A69E92] hover:text-white px-2 py-1.5 rounded-md hover:bg-white/10 transition-colors cursor-pointer shrink-0"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Logout</span>
            </button>
          )}

          {isCollapsed && (
            <button
              onClick={onToggleCollapse}
              title="Expand Sidebar"
              className="hidden lg:flex p-1.5 rounded-md text-[#A69E92] hover:text-white hover:bg-white/10 cursor-pointer"
            >
              <PanelLeft className="w-4 h-4" />
            </button>
          )}
        </div>
      </aside>
    </>
  );
}
