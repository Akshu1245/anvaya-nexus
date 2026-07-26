import { useState, useCallback } from 'react'

export type UploadedFile = {
  id: string
  name: string
  type: string
  size: number
  url?: string
  status: 'uploading' | 'complete' | 'error'
  error?: string
}

const uid = () => Math.random().toString(36).slice(2)

export function useFileUpload() {
  const [files, setFiles] = useState<UploadedFile[]>([])

  const addFiles = useCallback(async (newFiles: File[], investigationId?: string) => {
    const entries: UploadedFile[] = newFiles.map((f) => ({
      id: uid(),
      name: f.name,
      type: f.type,
      size: f.size,
      url: URL.createObjectURL(f),
      status: 'complete' as const,
    }))
    setFiles((prev) => [...prev, ...entries])
    return entries
  }, [])

  const removeFile = useCallback((id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id))
  }, [])

  const clearFiles = useCallback(() => {
    setFiles([])
  }, [])

  return { files, addFiles, removeFile, clearFiles }
}
