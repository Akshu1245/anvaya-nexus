import { useEffect, useId, useRef, type ReactNode } from 'react'

export type PortalModalVariant = 'drawer' | 'modal'

type PortalModalProps = {
  title: string
  onClose: () => void
  children: ReactNode
  variant?: PortalModalVariant
  /** Optional labelled-by override; defaults to generated title id */
  labelledBy?: string
}

/**
 * Elevated portal overlay: centred modal or full-height right drawer (Case 360).
 * Escape closes; close button receives initial focus (simple focus trap).
 */
export function PortalModal({
  title,
  onClose,
  children,
  variant = 'modal',
  labelledBy,
}: PortalModalProps) {
  const titleId = useId()
  const labelId = labelledBy ?? titleId
  const closeRef = useRef<HTMLButtonElement>(null)
  const panelRef = useRef<HTMLElement>(null)
  const isDrawer = variant === 'drawer'

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null
    closeRef.current?.focus()

    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        onClose()
        return
      }
      if (event.key !== 'Tab' || !panelRef.current) return
      const focusable = Array.from(
        panelRef.current.querySelectorAll<HTMLElement>(
          'button,[href],input,select,textarea,[tabindex]:not([tabindex="-1"])',
        ),
      ).filter((node) => !node.hasAttribute('disabled') && node.tabIndex !== -1)
      if (!focusable.length) {
        event.preventDefault()
        closeRef.current?.focus()
        return
      }
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', onKey)
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = previousOverflow
      previous?.focus?.()
    }
  }, [onClose])

  return (
    <div
      className={`fixed inset-0 z-50 flex bg-slate-950/50 p-3 ${
        isDrawer ? 'justify-end' : 'items-center justify-center'
      }`}
      role="presentation"
      onMouseDown={onClose}
    >
      <section
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelId}
        className={`portal-modal-enter flex flex-col overflow-hidden bg-white shadow-2xl ring-1 ring-navy-900/10 ${
          isDrawer
            ? 'h-full w-full max-w-2xl translate-x-0 rounded-2xl sm:rounded-l-2xl sm:rounded-r-none'
            : 'max-h-[90vh] w-full max-w-2xl scale-100 rounded-2xl'
        }`}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="flex shrink-0 items-start justify-between gap-4 border-b border-slate-200 bg-gradient-to-r from-navy-950 to-teal-900 px-5 py-4 text-white">
          <h2 id={titleId} className="text-lg font-semibold leading-snug tracking-tight">
            {title}
          </h2>
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            className="btn-portal shrink-0 rounded-lg border border-white/25 bg-white/10 px-3 py-1.5 text-sm font-semibold text-white hover:bg-white/20"
            aria-label="Close"
          >
            Close
          </button>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-5">{children}</div>
      </section>
    </div>
  )
}
