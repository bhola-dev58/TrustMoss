'use client';

import React from 'react';
import {
  Radio,
  Database,
  BookOpen,
  Gauge,
  Zap,
  Shield,
  X,
  ChevronLeft,
  ChevronRight,
  Cpu,
} from 'lucide-react';

export const NAV_ITEMS = [
  {
    id: 'agent',
    label: 'Agent HUD',
    sublabel: 'Live WebRTC & Tracing',
    icon: Radio,
    badge: 'LIVE',
    badgeColor: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  },
  {
    id: 'database',
    label: 'Postgres & Redis',
    sublabel: 'Storage & Cache Hub',
    icon: Database,
    badge: 'ONLINE',
    badgeColor: 'bg-[#FF8C00]/15 text-[#FFC107] border-[#FF8C00]/30',
  },
  {
    id: 'catalog',
    label: 'CRISPE Catalog',
    sublabel: '7 Surface Prompt Spec',
    icon: BookOpen,
    badge: 'v2.4',
    badgeColor: 'bg-sky-500/15 text-sky-400 border-sky-500/30',
  },
  {
    id: 'scalability',
    label: 'k6 Benchmarks',
    sublabel: 'Sub-45ms SLA Testing',
    icon: Gauge,
    badge: '<45ms',
    badgeColor: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  },
  {
    id: 'attack',
    label: 'Attack Lab',
    sublabel: 'OWASP Stress Matrix',
    icon: Zap,
    badge: '8 Vectors',
    badgeColor: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
  },
];

export default function SidebarNavigation({
  activeTab,
  onSelectTab,
  isOpen,
  onClose,
  isCollapsed,
  onToggleCollapse,
}) {
  return (
    <>
      {/* Mobile Drawer Overlay Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-black/75 backdrop-blur-sm z-40 lg:hidden transition-opacity duration-300"
          aria-hidden="true"
        />
      )}

      {/* Sliding Sidebar Container */}
      <aside
        data-testid="sidebar-navigation"
        className={`fixed lg:sticky top-0 left-0 z-50 lg:z-20 h-screen bg-[#1E1E1E] border-r border-[#333333] shadow-2xl flex flex-col transition-all duration-300 ease-in-out font-sans ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        } ${isCollapsed ? 'lg:w-20' : 'w-72 lg:w-64'}`}
      >
        {/* Toggle Button Linked on the Right Border - Icon Only */}
        <button
          onClick={isOpen ? onClose : onToggleCollapse}
          className="absolute top-5 -right-3.5 z-50 w-7 h-7 rounded-full bg-[#1E1E1E] border border-[#333333] hover:border-[#FF8C00] text-[#9AA0A6] hover:text-[#FF8C00] shadow-md hover:shadow-lg hover:shadow-[#FF8C00]/25 flex items-center justify-center cursor-pointer transition-all hover:scale-110"
          title={isCollapsed || !isOpen ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-label={isCollapsed || !isOpen ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed || !isOpen ? (
            <ChevronRight className="w-3.5 h-3.5" />
          ) : (
            <ChevronLeft className="w-3.5 h-3.5" />
          )}
        </button>

        {/* Sidebar Header */}
        <div className="p-4 border-b border-[#333333] flex items-center justify-between bg-[#242424]">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="p-2 bg-gradient-to-br from-[#FF8C00]/20 to-[#FFC107]/20 border border-[#FF8C00]/40 rounded-xl shadow-inner shadow-[#FF8C00]/20 shrink-0">
              <Shield className="w-5 h-5 text-[#FF8C00]" />
            </div>
            {(!isCollapsed || isOpen) && (
              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="text-sm font-bold tracking-tight text-[#FFFFFF]">
                    Trust<span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FF8C00] to-[#FFC107]">Moss</span>
                  </span>
                  <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-[#FF8C00]/15 text-[#FFC107] border border-[#FF8C00]/30">
                    GATEWAY
                  </span>
                </div>
                <p className="text-[10px] text-[#9AA0A6] truncate">Zero-Trust AI Gateway</p>
              </div>
            )}
          </div>
        </div>

        {/* Navigation Category Label */}
        {(!isCollapsed || isOpen) && (
          <div className="px-4 pt-4 pb-2">
            <span className="text-[10px] font-bold font-mono uppercase tracking-wider text-[#9AA0A6]">
              Console Navigation
            </span>
          </div>
        )}

        {/* Navigation Items List */}
        <nav aria-label="Sidebar Navigation" className="flex-1 px-3 py-2 space-y-1.5 overflow-y-auto no-scrollbar">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;

            return (
              <button
                key={item.id}
                onClick={() => {
                  onSelectTab(item.id);
                  if (onClose) onClose();
                }}
                title={item.label}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all group cursor-pointer ${
                  isActive
                    ? item.id === 'attack'
                      ? 'bg-rose-600 text-[#FFFFFF] shadow-lg shadow-rose-950/40 font-bold'
                      : 'bg-gradient-to-r from-[#FF8C00] to-[#FFC107] text-[#121212] shadow-md shadow-[#FF8C00]/25 font-bold'
                    : 'text-[#9AA0A6] hover:text-[#FFFFFF] hover:bg-[#242424]'
                }`}
              >
                <div
                  className={`p-1.5 rounded-lg shrink-0 transition-colors ${
                    isActive
                      ? item.id === 'attack'
                        ? 'bg-rose-700/60 text-white'
                        : 'bg-[#121212]/15 text-[#121212]'
                      : 'bg-[#121212] border border-[#333333] text-[#9AA0A6] group-hover:text-[#FFFFFF] group-hover:border-[#FF8C00]/40'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </div>

                {(!isCollapsed || isOpen) && (
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <span className="text-xs truncate block">{item.label}</span>
                      <span
                        className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border shrink-0 ${
                          isActive
                            ? 'bg-black/20 text-current border-transparent'
                            : item.badgeColor
                        }`}
                      >
                        {item.badge}
                      </span>
                    </div>
                    <span
                      className={`text-[10px] block truncate ${
                        isActive ? 'opacity-85' : 'text-[#9AA0A6]/70'
                      }`}
                    >
                      {item.sublabel}
                    </span>
                  </div>
                )}
              </button>
            );
          })}
        </nav>

        {/* Sidebar Footer System Health Widget */}
        {(!isCollapsed || isOpen) ? (
          <div className="p-3.5 m-3 bg-[#121212] border border-[#333333] rounded-xl space-y-2">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-[#FFFFFF] font-semibold flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-[#FF8C00]" />
                Moss Engine
              </span>
              <span className="text-emerald-400 font-mono font-bold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                ONLINE
              </span>
            </div>
            <div className="flex items-center justify-between text-[10px] text-[#9AA0A6] font-mono border-t border-[#333333] pt-2">
              <span>SLA Target:</span>
              <span className="text-[#FFC107]">&lt;45ms Ingress</span>
            </div>
            <div className="flex items-center justify-between text-[10px] text-[#9AA0A6] font-mono">
              <span>Guardrails:</span>
              <span className="text-[#FFFFFF]">5-Stage Active</span>
            </div>
          </div>
        ) : (
          <div className="p-3 flex justify-center border-t border-[#333333]">
            <div
              title="Moss Engine Online (<45ms SLA)"
              className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"
            />
          </div>
        )}
      </aside>
    </>
  );
}
