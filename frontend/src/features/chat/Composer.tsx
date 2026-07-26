import { useRef, useState, useCallback, useEffect, type DragEvent } from 'react'
import { FilePreview } from './MessageContent/FilePreview'

type Props = {
  input: string
  onInputChange: (value: string) => void
  onSend: (text: string, files?: File[]) => void
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

  // Read contents of text/CSV/JSON files if attached
  const readFileContents = async (files: File[]): Promise<string> => {
    let summary = ''
    for (const f of files) {
      if (f.type.includes('text') || f.name.endsWith('.csv') || f.name.endsWith('.json') || f.name.endsWith('.txt')) {
        try {
          const text = await f.text()
          summary += `\n\n--- Attached File: ${f.name} (${Math.round(f.size / 1024)} KB) ---\n${text.slice(0, 4000)}`
        } catch {
          summary += `\n\n[Attached File: ${f.name} (${Math.round(f.size / 1024)} KB)]`
        }
      } else {
        summary += `\n\n[Attached File: ${f.name} (${Math.round(f.size / 1024)} KB, type: ${f.type || 'document'})]`
      }
    }
    return summary
  }

  const handleSendAction = useCallback(async () => {
    const trimmed = input.trim()
    if (!trimmed && attachedFiles.length === 0) return

    let finalPrompt = trimmed
    if (attachedFiles.length > 0) {
      const fileContext = await readFileContents(attachedFiles)
      finalPrompt = (trimmed ? trimmed : 'Analyzing attached file(s)...') + fileContext
    }

    onSend(finalPrompt, attachedFiles)
    setAttachedFiles([])
  }, [input, attachedFiles, onSend])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void handleSendAction()
    }
  }, [handleSendAction])

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
      className={`relative rounded-2xl border transition-all ${
        isRecording
          ? 'border-red-400 bg-red-50/20 shadow-lg shadow-red-500/10 dark:border-red-500 dark:bg-red-950/20'
          : dragging
          ? 'border-teal-400 bg-teal-50 dark:border-teal-500 dark:bg-teal-900/20'
          : 'border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900'
      }`}
    >
      {/* Drop overlay */}
      {dragging && (
        <div className="absolute inset-0 z-10 flex items-center justify-center rounded-2xl border-2 border-dashed border-teal-400 bg-teal-50/90 text-sm font-semibold text-teal-700 dark:bg-teal-900/80 dark:text-teal-300">
          📁 Drop files to attach to conversation
        </div>
      )}

      {/* Live recording indicator header */}
      {isRecording && (
        <div className="flex items-center justify-between border-b border-red-200 bg-red-50/80 px-4 py-2 text-xs font-semibold text-red-700 dark:border-red-900/40 dark:bg-red-950/50 dark:text-red-300 rounded-t-2xl animate-pulse">
          <div className="flex items-center gap-2">
            <span className="flex h-2.5 w-2.5 rounded-full bg-red-600 animate-ping" />
            <span className="material-icons-outlined" style={{ fontSize: 16 }}>mic</span>
            <span>Recording... Speak now (Real-time transcript updates below)</span>
          </div>
          <button
            onClick={onVoiceToggle}
            className="rounded px-2 py-0.5 bg-red-600 text-white font-bold text-[10px] hover:bg-red-700 transition-colors"
          >
            DONE / STOP
          </button>
        </div>
      )}

      {/* Attached file previews */}
      {attachedFiles.length > 0 && (
        <div className="flex flex-wrap gap-2 border-b border-slate-200 p-3 dark:border-slate-700">
          {attachedFiles.map((file, i) => (
            <div key={i} className="relative group">
              <FilePreview file={{ name: file.name, type: file.type, size: file.size, url: URL.createObjectURL(file) }} />
              <button
                onClick={() => setAttachedFiles((prev) => prev.filter((_, j) => j !== i))}
                className="absolute -right-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs font-bold text-white hover:bg-red-600 shadow"
                title="Remove attachment"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input row */}
      <div className="flex items-end gap-2 p-2.5">
        <div className="flex items-center gap-1">
          {/* Voice Mic Button */}
          <button
            type="button"
            onClick={onVoiceToggle}
            className={`flex h-9 w-9 items-center justify-center rounded-xl transition-all ${
              isRecording
                ? 'bg-red-600 text-white shadow-md animate-pulse'
                : 'text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'
            }`}
            aria-label={isRecording ? 'Stop recording' : 'Start voice input'}
            title={isRecording ? 'Click to stop recording' : 'Voice input (Real-time speech to text)'}
            disabled={isBusy}
          >
            <span className="material-icons-outlined" style={{ fontSize: 20 }}>
              {isRecording ? 'mic' : 'mic_none'}
            </span>
          </button>

          {/* File Attachment Button */}
          <button
            type="button"
            onClick={handleFilePick}
            className="flex h-9 w-9 items-center justify-center rounded-xl text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors"
            aria-label="Attach file"
            title="Attach documents, CSV, FIR files, images"
            disabled={isBusy}
          >
            <span className="material-icons-outlined" style={{ fontSize: 20 }}>attach_file</span>
          </button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleFilesChosen}
            className="hidden"
            accept=".pdf,.png,.jpg,.jpeg,.webp,.csv,.xlsx,.docx,.txt,.json,.mp3,.wav,.mp4"
          />
        </div>

        {/* Text Area */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isRecording ? 'Listening... Spoken words appear here in real-time...' : 'Ask in English, ಕನ್ನಡ, or हिन्दी...'}
          rows={1}
          className="max-h-[200px] min-h-[38px] flex-1 resize-none bg-transparent px-2 py-1.5 text-sm text-slate-800 outline-none placeholder:text-slate-400 dark:text-slate-100 dark:placeholder:text-slate-500"
          disabled={isBusy}
        />

        {/* Send Button */}
        <button
          type="button"
          onClick={() => void handleSendAction()}
          disabled={isBusy || (!input.trim() && attachedFiles.length === 0)}
          className={`flex h-9 w-9 items-center justify-center rounded-xl transition-all ${
            input.trim() || attachedFiles.length > 0
              ? 'bg-[#003087] text-white shadow-md hover:bg-blue-900 dark:bg-amber-500 dark:text-slate-900 dark:hover:bg-amber-400'
              : 'bg-slate-100 text-slate-300 dark:bg-slate-800 dark:text-slate-600'
          }`}
          aria-label="Send message"
          title="Send"
        >
          <span className="material-icons-outlined" style={{ fontSize: 18 }}>send</span>
        </button>
      </div>
    </div>
  )
}
