import { useCallback, useRef } from 'react'
import { m3Api, type HealthStatus } from '../api/m3'
import { useAuthStore } from '../stores/authStore'

type VoiceHook = {
  isRecording: boolean
  startRecording: (lang: string) => void
  stopRecording: () => void
  startPushToTalk: (lang: string) => () => void
  startBrowserSpeech: (lang: string, onResult: (text: string) => void) => void
  speakText: (text: string, langCode: string) => Promise<void>
  isVoiceAvailable: (health: HealthStatus | null) => boolean
}

export function useVoice(
  setIsRecording: (v: boolean) => void,
  onTranscript: (text: string) => void,
): VoiceHook {
  const authStore = useAuthStore()
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const speechCtor =
    typeof window !== 'undefined'
      ? (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
      : null

  const startRecording = useCallback(
    async (lang: string) => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
          ? 'audio/webm;codecs=opus'
          : 'audio/webm'
        const recorder = new MediaRecorder(stream, { mimeType })
        audioChunksRef.current = []
        setIsRecording(true)

        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) audioChunksRef.current.push(e.data)
        }

        recorder.onstop = async () => {
          setIsRecording(false)
          stream.getTracks().forEach((t) => t.stop())
          const audioBlob = new Blob(audioChunksRef.current, { type: mimeType })
          authStore.setBusy('transcribing')
          try {
            const result = await m3Api
              .voiceTranscribe(audioBlob, lang)
              .catch(() => null)
            if (result?.text) onTranscript(result.text)
          } finally {
            authStore.setBusy('')
          }
        }

        mediaRecorderRef.current = recorder
        recorder.start()
      } catch {
        authStore.setError('Microphone access denied. Type your question instead.')
      }
    },
    [setIsRecording, onTranscript, authStore],
  )

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop()
  }, [])

  const startPushToTalk = useCallback(
    (lang: string) => {
      let stopped = false
      startRecording(lang)
      return () => {
        if (!stopped) {
          stopped = true
          stopRecording()
        }
      }
    },
    [startRecording, stopRecording],
  )

  const startBrowserSpeech = useCallback(
    (lang: string, onResult: (text: string) => void) => {
      if (!speechCtor) return
      const recognition = new speechCtor()
      recognition.lang = lang
      recognition.interimResults = false
      recognition.onresult = (event: any) => {
        const transcript = event.results?.[0]?.[0]?.transcript || ''
        onResult(transcript)
      }
      recognition.onerror = () =>
        authStore.setError('Voice input unavailable. Type instead.')
      recognition.start()
    },
    [speechCtor, authStore],
  )

  const speakText = useCallback(
    async (text: string, langCode: string) => {
      authStore.setBusy('speaking')
      try {
        const data = await m3Api.voiceSpeak(text, langCode)
        if (!data?.audio_base64) return
        const bytes = atob(data.audio_base64)
        const buffer = new Uint8Array(bytes.length)
        for (let i = 0; i < bytes.length; i++) buffer[i] = bytes.charCodeAt(i)
        const blob = new Blob([buffer], { type: 'audio/wav' })
        const url = URL.createObjectURL(blob)
        const audio = new Audio(url)
        audio.play()
        audio.onended = () => URL.revokeObjectURL(url)
      } catch {
        /* ignore audio errors */
      } finally {
        authStore.setBusy('')
      }
    },
    [authStore],
  )

  const isVoiceAvailable = useCallback(
    (health: HealthStatus | null) =>
      Boolean(health?.voice_enabled) || Boolean(speechCtor),
    [speechCtor],
  )

  return {
    isRecording: false,
    startRecording,
    stopRecording,
    startPushToTalk,
    startBrowserSpeech,
    speakText,
    isVoiceAvailable,
  }
}
