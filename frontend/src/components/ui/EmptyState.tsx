import { type ReactNode } from 'react'

type EmptyStateProps = {
  icon?: ReactNode
  title: string
  description?: string
  action?: ReactNode
  size?: 'sm' | 'md' | 'lg'
}

const sizeStyles = {
  sm: { wrapper: 'py-8', iconBox: 'h-8 w-8', iconSize: 14, titleClass: 'text-xs', descClass: 'text-[11px]' },
  md: { wrapper: 'py-12', iconBox: 'h-10 w-10', iconSize: 18, titleClass: 'text-sm', descClass: 'text-xs' },
  lg: { wrapper: 'py-20', iconBox: 'h-14 w-14', iconSize: 24, titleClass: 'text-base', descClass: 'text-sm' },
}

export function EmptyState({ icon, title, description, action, size = 'md' }: EmptyStateProps) {
  const s = sizeStyles[size]
  return (
    <div className={`flex flex-col items-center justify-center px-4 text-center ${s.wrapper}`}>
      {icon !== undefined ? (
        <div className={`mb-3 flex items-center justify-center rounded-xl bg-slate-100 text-slate-400 ${s.iconBox}`}>
          {icon}
        </div>
      ) : (
        <div className={`mb-3 flex items-center justify-center rounded-xl bg-slate-100 text-slate-400 ${s.iconBox}`}>
          <svg width={s.iconSize} height={s.iconSize} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        </div>
      )}
      <p className={`font-medium text-slate-600 ${s.titleClass}`}>{title}</p>
      {description && <p className={`mt-1 text-slate-400 ${s.descClass}`}>{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function SkeletonLine({ width = '100%', height = 4, className = '' }: { width?: string; height?: number; className?: string }) {
  return (
    <div
      className={`rounded bg-gradient-to-r from-slate-100 via-slate-200 to-slate-100 bg-[length:200%_100%] animate-shimmer ${className}`}
      style={{ width, height }}
    />
  )
}

export function SkeletonCard({ lines = 3 }: { lines?: number }) {
  return (
    <div className="rounded-xl border border-slate-200 p-4">
      <SkeletonLine width="40%" height={16} />
      <div className="mt-3 flex gap-2">
        <SkeletonLine width="96px" height={20} className="rounded-full" />
        <SkeletonLine width="64px" height={20} className="rounded-full" />
      </div>
      {Array.from({ length: lines }).map((_, i) => (
        <SkeletonLine key={i} width={`${50 + Math.random() * 40}%`} height={12} className="mt-3" />
      ))}
    </div>
  )
}

export function SkeletonList({ count = 3 }: { count?: number }) {
  return (
    <div className="grid gap-3" role="status" aria-live="polite" aria-label="Loading…">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  )
}

export function Badge({ children, variant = 'default' }: { children: ReactNode; variant?: 'default' | 'teal' | 'amber' | 'red' | 'purple' | 'slate' }) {
  const variants = {
    default: 'bg-slate-100 text-slate-700 ring-slate-200',
    teal: 'bg-teal-50 text-teal-800 ring-teal-200',
    amber: 'bg-amber-50 text-amber-900 ring-amber-200',
    red: 'bg-red-50 text-red-800 ring-red-200',
    purple: 'bg-purple-50 text-purple-800 ring-purple-200',
    slate: 'bg-slate-50 text-slate-600 ring-slate-200',
  }
  return (
    <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ring-1 ${variants[variant]}`}>
      {children}
    </span>
  )
}

export function Chip({ children, active, onClick }: { children: ReactNode; active?: boolean; onClick?: () => void }) {
  const base = 'rounded-full px-3 py-1 text-xs font-medium transition-all'
  if (onClick) {
    return (
      <button
        type="button"
        onClick={onClick}
        className={`${base} ${
          active
            ? 'bg-navy-900 text-white ring-1 ring-navy-800'
            : 'border border-slate-300 text-slate-600 hover:border-teal-500 hover:bg-teal-50 hover:text-teal-800'
        }`}
      >
        {children}
      </button>
    )
  }
  return (
    <span className={`${base} bg-slate-100 text-slate-700 ring-1 ring-slate-200`}>
      {children}
    </span>
  )
}
