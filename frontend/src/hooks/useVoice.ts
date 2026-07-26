import { useCallback, useRef, useState } from 'react'
import { m3Api, type HealthStatus } from '../api/m3'
import { useAuthStore } from '../stores/authStore'

type VoiceHook = {
  isRecording: boolean
  startRecording: (lang: string) => void
  stopRecording: () => void
  startPushToTalk: (lang: string) => () => void
  startBrowserSpeech: (lang: string, onResult: (text: string, isFinal?: boolean) => void) => void
  speakText: (text: string, langCode: string) => Promise<void>
  isVoiceAvailable: (health: HealthStatus | null) => boolean
}

export function useVoice(
  setIsRecordingStore: (v: boolean) => void,
  onTranscript: (text: string) => void,
): VoiceHook {
  const authStore = useAuthStore()
  const [isRecording, setIsRecordingState] = useState(false)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const recognitionRef = useRef<any>(null)

  const speechCtor =
    typeof window !== 'undefined'
      ? (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
      : null

  const setRecording = useCallback(
    (recording: boolean) => {
      setIsRecordingState(recording)
      setIsRecordingStore(recording)
    },
    [setIsRecordingStore],
  )

  const startBrowserSpeech = useCallback(
    (lang: string, onResult: (text: string, isFinal?: boolean) => void) => {
      if (!speechCtor) {
        authStore.setError('Voice recognition not supported in this browser. Please use Chrome/Edge or type your question.')
        return
      }

      try {
        if (recognitionRef.current) {
          try { recognitionRef.current.stop() } catch {}
        }

        const recognition = new speechCtor()
        recognition.lang = lang === 'kn' ? 'kn-IN' : (lang === 'hi' ? 'hi-IN' : 'en-IN')
        recognition.continuous = true
        recognition.interimResults = true

        recognition.onstart = () => {
          setRecording(true)
        }

        recognition.onresult = (event: any) => {
          let interimTranscript = ''
          let finalTranscript = ''

          for (let i = event.resultIndex; i < event.results.length; ++i) {
            const transcript = event.results[i][0].transcript
            if (event.results[i].isFinal) {
              finalTranscript += transcript + ' '
            } else {
              interimTranscript += transcript
            }
          }

          const combined = (finalTranscript + interimTranscript).trim()
          if (combined) {
            onResult(combined, false)
          }
        }

        recognition.onerror = (event: any) => {
          if (event.error !== 'no-speech' && event.error !== 'aborted') {
            authStore.setError(`Voice recognition note: ${event.error || 'silence detected'}. Try speaking or typing.`)
          }
        }

        recognition.onend = () => {
          if (recognitionRef.current === recognition && mediaRecorderRef.current?.state !== 'recording') {
            try { recognition.start() } catch { setRecording(false) }
          } else {
            setRecording(false)
          }
        }

        recognitionRef.current = recognition
        recognition.start()
      } catch (e) {
        setRecording(false)
        authStore.setError('Unable to start microphone. Please check permissions.')
      }
    },
    [speechCtor, setRecording, authStore],
  )

  const startRecording = useCallback(
    async (lang: string) => {
      // Prefer real-time browser speech recognition for instant input bar rendering
      if (speechCtor) {
        startBrowserSpeech(lang, (text) => onTranscript(text))
        return
      }

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
          ? 'audio/webm;codecs=opus'
          : 'audio/webm'
        const recorder = new MediaRecorder(stream, { mimeType })
        audioChunksRef.current = []
        setRecording(true)

        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) audioChunksRef.current.push(e.data)
        }

        recorder.onstop = async () => {
          setRecording(false)
          stream.getTracks().forEach((t) => t.stop())
          const audioBlob = new Blob(audioChunksRef.current, { type: mimeType })
          authStore.setBusy('transcribing')
          try {
            const result = await m3Api.voiceTranscribe(audioBlob, lang).catch(() => null)
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
    [speechCtor, startBrowserSpeech, setRecording, onTranscript, authStore],
  )

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop() } catch {}
      recognitionRef.current = null
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try { mediaRecorderRef.current.stop() } catch {}
    }
    setRecording(false)
  }, [setRecording])

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
    isRecording,
    startRecording,
    stopRecording,
    startPushToTalk,
    startBrowserSpeech,
    speakText,
    isVoiceAvailable,
  }
}
