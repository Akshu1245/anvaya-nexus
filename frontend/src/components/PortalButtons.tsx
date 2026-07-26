/**
 * Shared portal button classNames — navy / teal / gold government look
 * with hover-lift + active press via `.btn-portal` in styles.css.
 */

const base =
  'btn-portal inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:pointer-events-none disabled:opacity-55'

/** Primary teal CTA (Search, Send, Confirm) */
export const btnPrimary = `${base} bg-teal-700 text-white shadow-sm ring-1 ring-teal-800/30 hover:bg-teal-600 hover:shadow-md focus-visible:outline-teal-400 active:bg-teal-800`

/** Secondary navy action (Preview, Load briefing/trends) */
export const btnSecondary = `${base} bg-navy-800 text-white shadow-sm ring-1 ring-navy-900/40 hover:bg-navy-700 hover:shadow-md focus-visible:outline-teal-300 active:bg-navy-900`

/** Danger / emergency (destructive or emergency tel CTAs) */
export const btnDanger = `${base} bg-red-700 text-white shadow-sm ring-1 ring-red-900/30 hover:bg-red-600 hover:shadow-md focus-visible:outline-red-300 active:bg-red-800`

/** Outline secondary (Open Case 360, Related, Clear) — gold accent rim */
export const btnOutline = `${base} border-2 border-navy-800/80 bg-white text-navy-900 shadow-sm ring-1 ring-[#c9a227]/35 hover:border-teal-700 hover:bg-teal-50 hover:text-teal-900 hover:shadow-md focus-visible:outline-teal-500 active:bg-teal-100`
