type Props = { content: string }

function escapeHtml(str: string) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function renderInline(text: string): string {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code class="rounded bg-slate-100 px-1 text-[11px] font-mono text-pink-600 dark:bg-slate-800 dark:text-pink-400">$1</code>')
    .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" class="text-teal-600 underline hover:text-teal-700 dark:text-teal-400">$1</a>')
}

function renderTable(block: string): string {
  const lines = block.split('\n').filter(Boolean)
  if (lines.length < 2) return escapeHtml(block)
  const headers = lines[0].split('|').filter(Boolean).map((h) => h.trim())
  const body = lines.slice(2).filter((l) => !l.includes('---'))
  let html = '<div class="overflow-x-auto"><table class="w-full border-collapse text-xs"><thead><tr>'
  for (const h of headers) html += `<th class="border border-slate-200 bg-slate-50 px-3 py-1.5 text-left font-semibold text-slate-700 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300">${escapeHtml(h)}</th>`
  html += '</tr></thead><tbody>'
  for (const row of body) {
    const cells = row.split('|').filter(Boolean).map((c) => c.trim())
    html += '<tr>'
    for (const cell of cells) html += `<td class="border border-slate-200 px-3 py-1.5 text-slate-600 dark:border-slate-600 dark:text-slate-400">${escapeHtml(cell)}</td>`
    html += '</tr>'
  }
  html += '</tbody></table></div>'
  return html
}

export function MarkdownRenderer({ content }: Props) {
  if (!content) return null

  const blocks = content.split(/\n\n+/)
  const html = blocks.map((block) => {
    const trimmed = block.trim()
    if (trimmed.startsWith('|') && trimmed.includes('|')) return renderTable(trimmed)
    if (trimmed.startsWith('- ')) {
      const items = trimmed.split('\n').map((l) => l.replace(/^- /, '').trim()).filter(Boolean)
      return `<ul class="list-disc space-y-1 pl-5 text-sm text-slate-700 dark:text-slate-300">${items.map((i) => `<li>${renderInline(i)}</li>`).join('')}</ul>`
    }
    if (/^\d+\. /.test(trimmed)) {
      const items = trimmed.split('\n').map((l) => l.replace(/^\d+\. /, '').trim()).filter(Boolean)
      return `<ol class="list-decimal space-y-1 pl-5 text-sm text-slate-700 dark:text-slate-300">${items.map((i) => `<li>${renderInline(i)}</li>`).join('')}</ol>`
    }
    return `<p class="text-sm text-slate-700 dark:text-slate-300">${renderInline(trimmed)}</p>`
  }).join('\n')

  return <div className="space-y-2" dangerouslySetInnerHTML={{ __html: html }} />
}
