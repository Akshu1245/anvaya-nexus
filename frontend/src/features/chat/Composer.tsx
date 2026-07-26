import { useRef, useState, useCallback, useEffect, type DragEvent } from 'react'
import { FilePreview } from './MessageContent/FilePreview'

type Props = {
  input: string
  onInputChange: (value: string) => void
  onSend: (text: string) => void
  onVoiceToggle: () => void
  isRecording: boolean
  isBusy: boolean
  onNewTopic: () => void
  onFileDrop?: (files: File[]) => void
}

export function Composer({ input, onInputChange, onSend, onVoiceToggle, isRecording, isBusy, onNewTopic, onFileDrop }: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [attachedFiles, setAttachedFiles] = useState<File[]>([])

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px'
    }
  }, [input])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (input.trim() || attachedFiles.length) {
        onSend(input)
        setAttachedFiles([])
      }
    }
  }, [input, attachedFiles, onSend])

  const handleFilePick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFilesChosen = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (files.length) {
      setAttachedFiles((prev) => [...prev, ...files])
      onFileDrop?.(files)
    }
    e.target.value = ''
  }, [onFileDrop])

  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault()
    setDragging(true)
  }, [])

  const handleDragLeave = useCallback(() => {
    setDragging(false)
  }, [])

  const handleDrop = useCallback((e: DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const files = Array.from(e.dataTransfer.files)
    if (files.length) {
      setAttachedFiles((prev) => [...prev, ...files])
      onFileDrop?.(files)
    }
  }, [onFileDrop])

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`relative rounded-xl border transition-all ${
        dragging
          ? 'border-teal-400 bg-teal-50 dark:border-teal-500 dark:bg-teal-900/20'
          : 'border-slate-200 bg-white dark:border-slate-600 dark:bg-navy-900'
      }`}
    >
      {dragging && (
        <div className="absolute inset-0 z-10 flex items-center justify-center rounded-xl border-2 border-dashed border-teal-400 bg-teal-50/90 text-sm font-semibold text-teal-700 dark:bg-teal-900/80 dark:text-teal-300">
          Drop files here
        </div>
      )}

      {attachedFiles.length > 0 && (
        <div className="flex flex-wrap gap-2 border-b border-slate-200 p-3 dark:border-slate-600">
          {attachedFiles.map((file, i) => (
            <div key={i} className="relative">
              <FilePreview file={{ name: file.name, type: file.type, size: file.size, url: URL.createObjectURL(file) }} />
              <button
                onClick={() => setAttachedFiles((prev) => prev.filter((_, j) => j !== i))}
                className="absolute -right-1.5 -top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] text-white hover:bg-red-600"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-end gap-2 p-2">
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={onVoiceToggle}
            className={`flex h-8 w-8 items-center justify-center rounded-lg transition-colors ${
              isRecording ? 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400' : 'text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
            aria-label={isRecording ? 'Stop recording' : 'Start voice input'}
            disabled={isBusy}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/><path d="M19 10v2a7 7 0 01-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
          </button>
          <button
            type="button"
            onClick={handleFilePick}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            aria-label="Attach file"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/></svg>
          </button>
          <input ref={fileInputRef} type="file" multiple onChange={handleFilesChosen} className="hidden" accept=".pdf,.png,.jpg,.jpeg,.webp,.csv,.xlsx,.docx,.mp3,.wav,.mp4" />
        </div>

        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask in English, ಕನ್ನಡ, or हिन्दी..."
          rows={1}
          className="max-h-[200px] min-h-[36px] flex-1 resize-none bg-transparent px-1 py-1.5 text-sm text-slate-800 outline-none placeholder:text-slate-400 dark:text-slate-200 dark:placeholder:text-slate-500"
          disabled={isBusy}
        />

        <button
          type="button"
          onClick={() => { onSend(input); setAttachedFiles([]) }}
          disabled={!input.trim() && !attachedFiles.length}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-teal-600 text-white transition-colors hover:bg-teal-700 disabled:opacity-40 dark:bg-teal-600 dark:hover:bg-teal-500"
          aria-label="Send message"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </div>
    </div>
  )
}
