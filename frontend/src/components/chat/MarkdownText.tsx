import React from 'react'

type MarkdownTextProps = {
  content: string
  className?: string
}

export function MarkdownText({ content, className = '' }: MarkdownTextProps) {
  if (!content) return null

  const lines = content.split('\n')
  const blocks: React.ReactNode[] = []
  let currentList: { type: 'ul' | 'ol'; items: string[] } | null = null

  const flushList = (keyPrefix: number) => {
    if (!currentList) return
    const Tag = currentList.type
    blocks.push(
      <Tag
        key={`list-${keyPrefix}`}
        className={`my-2 space-y-1 pl-5 ${currentList.type === 'ul' ? 'list-disc' : 'list-decimal'} text-slate-900 dark:text-slate-100 font-medium`}
      >
        {currentList.items.map((item, idx) => (
          <li key={idx} className="leading-relaxed">
            {renderInline(item)}
          </li>
        ))}
      </Tag>,
    )
    currentList = null
  }

  const renderInline = (text: string): React.ReactNode => {
    const parts: React.ReactNode[] = []
    const regex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g
    let lastIndex = 0
    let match: RegExpExecArray | null

    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.slice(lastIndex, match.index))
      }
      const raw = match[0]
      if (raw.startsWith('**') && raw.endsWith('**')) {
        parts.push(
          <strong key={match.index} className="font-bold text-slate-950 dark:text-white">
            {raw.slice(2, -2)}
          </strong>,
        )
      } else if (raw.startsWith('*') && raw.endsWith('*')) {
        parts.push(<em key={match.index} className="italic">{raw.slice(1, -1)}</em>)
      } else if (raw.startsWith('`') && raw.endsWith('`')) {
        parts.push(
          <code
            key={match.index}
            className="rounded bg-teal-50 px-1.5 py-0.5 font-mono text-xs font-semibold text-teal-900 border border-teal-200/60 dark:bg-teal-950/60 dark:text-teal-200 dark:border-teal-800/60"
          >
            {raw.slice(1, -1)}
          </code>,
        )
      }
      lastIndex = regex.lastIndex
    }
    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex))
    }
    return parts.length ? parts : text
  }

  lines.forEach((line, index) => {
    const trimmed = line.trim()
    if (!trimmed) {
      flushList(index)
      return
    }

    if (trimmed.startsWith('### ')) {
      flushList(index)
      blocks.push(
        <h3 key={index} className="mb-1.5 mt-3 text-base font-bold text-slate-950 dark:text-white">
          {renderInline(trimmed.slice(4))}
        </h3>,
      )
      return
    }
    if (trimmed.startsWith('## ')) {
      flushList(index)
      blocks.push(
        <h2 key={index} className="mb-2 mt-4 text-lg font-bold text-slate-950 dark:text-white">
          {renderInline(trimmed.slice(3))}
        </h2>,
      )
      return
    }

    if (/^[-*]\s+/.test(trimmed)) {
      const itemText = trimmed.replace(/^[-*]\s+/, '')
      if (currentList && currentList.type === 'ul') {
        currentList.items.push(itemText)
      } else {
        flushList(index)
        currentList = { type: 'ul', items: [itemText] }
      }
      return
    }

    if (/^\d+\.\s+/.test(trimmed)) {
      const itemText = trimmed.replace(/^\d+\.\s+/, '')
      if (currentList && currentList.type === 'ol') {
        currentList.items.push(itemText)
      } else {
        flushList(index)
        currentList = { type: 'ol', items: [itemText] }
      }
      return
    }

    flushList(index)
    blocks.push(
      <p key={index} className="mb-2 leading-relaxed text-slate-900 dark:text-slate-100 font-medium">
        {renderInline(trimmed)}
      </p>,
    )
  })

  flushList(lines.length)

  return <div className={`prose-sm max-w-none ${className}`}>{blocks}</div>
}
