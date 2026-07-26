type Props = {
  file: { name: string; type: string; size: number; url?: string }
}

const typeIcons: Record<string, string> = {
  'application/pdf': '📄',
  'image/': '🖼️',
  'video/': '🎬',
  'audio/': '🎵',
  'text/csv': '📊',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '📊',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '📝',
  'application/vnd.ms-excel': '📊',
}

function getIcon(mime: string) {
  for (const [key, icon] of Object.entries(typeIcons)) {
    if (mime.startsWith(key)) return icon
  }
  return '📎'
}

function formatSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

export function FilePreview({ file }: Props) {
  const isImage = file.type.startsWith('image/')
  const isVideo = file.type.startsWith('video/')
  const isAudio = file.type.startsWith('audio/')

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-700 dark:bg-navy-900">
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-lg dark:bg-slate-800">
          {getIcon(file.type)}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-slate-800 dark:text-slate-200">{file.name}</p>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">{formatSize(file.size)}</p>
        </div>
      </div>
      {isImage && file.url && (
        <div className="mt-3">
          <img src={file.url} alt={file.name} className="max-h-64 rounded-lg object-contain" />
        </div>
      )}
      {isVideo && file.url && (
        <div className="mt-3">
          <video src={file.url} controls className="max-h-64 w-full rounded-lg" />
        </div>
      )}
      {isAudio && file.url && (
        <div className="mt-3">
          <audio src={file.url} controls className="w-full" />
        </div>
      )}
    </div>
  )
}
