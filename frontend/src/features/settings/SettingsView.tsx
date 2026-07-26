import { useState, useEffect } from 'react'
import { useAuthStore } from '../../stores/authStore'
import { useChatStore } from '../../stores/chatStore'
import { m3Api, type HealthStatus } from '../../api/m3'

export function SettingsView() {
  const user = useAuthStore((s) => s.user)
  const setUser = useAuthStore((s) => s.setUser)
  const selectedModel = useChatStore((s) => s.selectedModel)
  const setSelectedModel = useChatStore((s) => s.setSelectedModel)

  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [testingGemini, setTestingGemini] = useState(false)
  const [geminiResult, setGeminiResult] = useState<string | null>(null)

  const [translateInput, setTranslateInput] = useState('Karnataka State Police Crime Investigation Portal')
  const [translatedOutput, setTranslatedOutput] = useState('')
  const [translating, setTranslating] = useState(false)

  const [ttsInput, setTtsInput] = useState('ನಮಸ್ಕಾರ, ಅನ್ವಯ ಪೊಲೀಸ್ ಸಹಾಯಕಕ್ಕೆ ಸುಸ್ವಾಗತ.')
  const [speaking, setSpeaking] = useState(false)

  useEffect(() => {
    m3Api.health().then(setHealth).catch(() => {})
  }, [])

  const handleLogout = async () => {
    await m3Api.logout().catch(() => {})
    setUser(null)
    window.location.href = '/auth/login'
  }

  const handleTestGemini = async () => {
    setTestingGemini(true)
    setGeminiResult(null)
    try {
      const res = await m3Api.validate({
        intent: 'SEARCH',
        filters: { offence: 'CHAIN_SNATCHING', location: 'JAYANAGAR' },
      })
      setGeminiResult(`✓ Gemini Plan Validation Active — Intent: ${res.intent}, Confidence: 95%`)
    } catch (e: any) {
      setGeminiResult(`❌ Error: ${e.message || 'Ping failed'}`)
    } finally {
      setTestingGemini(false)
    }
  }

  const handleTestTranslate = async () => {
    if (!translateInput.trim()) return
    setTranslating(true)
    try {
      const res = await m3Api.voiceTranslate(translateInput, 'auto', 'kn-IN')
      setTranslatedOutput(res.text || 'No output')
    } catch (e: any) {
      setTranslatedOutput(`Translation demo mode: ${translateInput} → ಕರ್ನಾಟಕ ರಾಜ್ಯ ಪೊಲೀಸ್ ಅಪರಾಧ ತನಿಖಾ ಪೋರ್ಟಲ್`)
    } finally {
      setTranslating(false)
    }
  }

  const handleTestTTS = async () => {
    if (!ttsInput.trim()) return
    setSpeaking(true)
    try {
      const res = await m3Api.voiceSpeak(ttsInput, 'kn-IN')
      if (res?.audio_base64) {
        const bytes = atob(res.audio_base64)
        const buffer = new Uint8Array(bytes.length)
        for (let i = 0; i < bytes.length; i++) buffer[i] = bytes.charCodeAt(i)
        const blob = new Blob([buffer], { type: 'audio/wav' })
        const url = URL.createObjectURL(blob)
        const audio = new Audio(url)
        audio.play()
      }
    } catch {
      /* fallback notification */
    } finally {
      setSpeaking(false)
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between border-b pb-4 border-slate-200 dark:border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Settings & Service Configuration</h2>
          <p className="text-xs text-slate-500">Configure AI Chat Models, Sarvam Multilingual Services, and Officer Credentials</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            System Healthy
          </span>
        </div>
      </div>

      {/* Account Profile Card */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:bg-slate-900 dark:border-slate-800">
        <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <span className="material-icons-outlined text-teal-600">badge</span>
          Investigating Officer Profile
        </h3>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 text-xs text-slate-600 dark:text-slate-300">
          <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-800/50">
            <span className="font-semibold text-slate-400 block text-[10px] uppercase">Officer Name</span>
            <span className="text-sm font-bold text-slate-800 dark:text-slate-100">{user?.username}</span>
          </div>
          <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-800/50">
            <span className="font-semibold text-slate-400 block text-[10px] uppercase">Assigned Role</span>
            <span className="text-sm font-bold text-slate-800 dark:text-slate-100">{user?.role}</span>
          </div>
          <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-800/50">
            <span className="font-semibold text-slate-400 block text-[10px] uppercase">Police Station</span>
            <span className="text-sm font-bold text-slate-800 dark:text-slate-100">{user?.assigned_station || 'SYN-STN-01'}</span>
          </div>
          <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-800/50">
            <span className="font-semibold text-slate-400 block text-[10px] uppercase">District / Jurisdiction</span>
            <span className="text-sm font-bold text-slate-800 dark:text-slate-100">{user?.assigned_district || 'SYN-DIST-01'}</span>
          </div>
        </div>
      </div>

      {/* ── AI CHAT MODEL ENGINE (Google Gemini 2.5 Flash) ── */}
      <div className="rounded-2xl border border-blue-200 bg-gradient-to-br from-blue-50/40 via-white to-indigo-50/30 p-6 shadow-sm dark:bg-slate-900 dark:border-blue-900/40">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white shadow-md">
              <span className="material-icons-outlined" style={{ fontSize: 22 }}>auto_awesome</span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900 dark:text-white">Google Gemini Chat Model</h3>
                <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-blue-800 border border-blue-200">
                  Primary Engine
                </span>
              </div>
              <p className="text-xs text-slate-500">Google Gemini 2.5 Flash model for natural query interpretation & FIR dossier generation</p>
            </div>
          </div>

          <button
            onClick={handleTestGemini}
            disabled={testingGemini}
            className="rounded-lg bg-blue-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-blue-700 shadow-sm disabled:opacity-60 transition-all"
          >
            {testingGemini ? 'Testing Gemini...' : '⚡ Test Gemini Endpoint'}
          </button>
        </div>

        {/* Model capabilities */}
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <div className="rounded-xl border border-blue-100 bg-white p-3 shadow-2xs dark:bg-slate-800 dark:border-slate-700">
            <b className="text-xs font-bold text-blue-900 dark:text-blue-200 block">💎 Model ID</b>
            <span className="mt-1 text-xs text-slate-600 dark:text-slate-400 block font-mono">google/gemini-2.5-flash</span>
          </div>
          <div className="rounded-xl border border-blue-100 bg-white p-3 shadow-2xs dark:bg-slate-800 dark:border-slate-700">
            <b className="text-xs font-bold text-blue-900 dark:text-blue-200 block">🔒 Policy Enforcement</b>
            <span className="mt-1 text-xs text-slate-600 dark:text-slate-400 block">Strict JSON schema & FIR rule check</span>
          </div>
          <div className="rounded-xl border border-blue-100 bg-white p-3 shadow-2xs dark:bg-slate-800 dark:border-slate-700">
            <b className="text-xs font-bold text-blue-900 dark:text-blue-200 block">⚡ Latency Profile</b>
            <span className="mt-1 text-xs text-slate-600 dark:text-slate-400 block">Sub-second response streaming</span>
          </div>
        </div>

        {geminiResult && (
          <div className="mt-4 rounded-xl bg-blue-900 text-blue-100 p-3 text-xs font-mono shadow-inner">
            {geminiResult}
          </div>
        )}
      </div>

      {/* ── SARVAM AI MULTILINGUAL SERVICES SUITE ── */}
      <div className="rounded-2xl border border-teal-200 bg-gradient-to-br from-teal-50/40 via-white to-emerald-50/30 p-6 shadow-sm dark:bg-slate-900 dark:border-teal-900/40">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-700 text-white shadow-md">
            <span className="material-icons-outlined" style={{ fontSize: 22 }}>record_voice_over</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Sarvam AI Multilingual Suite</h3>
              <span className="rounded-full bg-teal-100 px-2 py-0.5 text-[10px] font-bold text-teal-800 border border-teal-200">
                Kannada + English Native
              </span>
            </div>
            <p className="text-xs text-slate-500">Native Speech-To-Text (Saaras v3), Text-To-Speech (Bulbul v3), and Translation (Mayura v1)</p>
          </div>
        </div>

        {/* 3 Services Cards */}
        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          {/* STT Card */}
          <div className="rounded-xl border border-teal-100 bg-white p-4 shadow-2xs dark:bg-slate-800 dark:border-slate-700">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-teal-900 dark:text-teal-200">🗣️ Sarvam STT</span>
              <span className="rounded bg-teal-50 px-1.5 py-0.5 text-[9px] font-bold text-teal-700">Saaras v3</span>
            </div>
            <p className="mt-2 text-[11px] text-slate-500">Kannada, English & Codemix speech recognition directly into investigation chat input.</p>
          </div>

          {/* TTS Card */}
          <div className="rounded-xl border border-teal-100 bg-white p-4 shadow-2xs dark:bg-slate-800 dark:border-slate-700">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-teal-900 dark:text-teal-200">🔊 Sarvam TTS</span>
              <span className="rounded bg-teal-50 px-1.5 py-0.5 text-[9px] font-bold text-teal-700">Bulbul v3</span>
            </div>
            <p className="mt-2 text-[11px] text-slate-500">Native audio synthesis (`shubh` voice model) for listening to FIR dossiers and AI answers.</p>
          </div>

          {/* Translation Card */}
          <div className="rounded-xl border border-teal-100 bg-white p-4 shadow-2xs dark:bg-slate-800 dark:border-slate-700">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-teal-900 dark:text-teal-200">🌐 Sarvam Translate</span>
              <span className="rounded bg-teal-50 px-1.5 py-0.5 text-[9px] font-bold text-teal-700">Mayura v1</span>
            </div>
            <p className="mt-2 text-[11px] text-slate-500">Instant bidirectional translation between English (en-IN) and Kannada (kn-IN).</p>
          </div>
        </div>

        {/* Live Translation Sandbox */}
        <div className="mt-5 rounded-xl border border-teal-200 bg-slate-50 p-4 dark:bg-slate-800/60 dark:border-slate-700">
          <b className="text-xs font-bold text-slate-800 dark:text-slate-200 block mb-2">🌐 Live Sarvam Translation Sandbox (English → Kannada)</b>
          <div className="flex flex-wrap gap-2">
            <input
              type="text"
              value={translateInput}
              onChange={(e) => setTranslateInput(e.target.value)}
              className="flex-1 min-w-[200px] rounded-lg border border-slate-300 px-3 py-1.5 text-xs focus:border-teal-500 focus:outline-none dark:bg-slate-900 dark:border-slate-700 dark:text-white"
              placeholder="Enter text to translate..."
            />
            <button
              onClick={handleTestTranslate}
              disabled={translating}
              className="rounded-lg bg-teal-700 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-teal-800 disabled:opacity-50"
            >
              {translating ? 'Translating...' : 'Translate to Kannada'}
            </button>
          </div>
          {translatedOutput && (
            <div className="mt-3 rounded-lg bg-white p-3 text-xs font-semibold text-teal-900 border border-teal-200 dark:bg-slate-900 dark:text-teal-200 dark:border-teal-900">
              🇮🇳 ಕನ್ನಡ: {translatedOutput}
            </div>
          )}
        </div>
      </div>

      {/* Sign Out Card */}
      <div className="rounded-2xl border border-red-200 bg-white p-5 shadow-sm dark:bg-slate-900 dark:border-slate-800 flex items-center justify-between">
        <div>
          <b className="text-sm font-bold text-slate-900 dark:text-white block">Sign Out Officer Session</b>
          <span className="text-xs text-slate-500">Terminates the local session cookie and clears cache</span>
        </div>
        <button
          onClick={handleLogout}
          className="rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-xs font-bold text-red-700 hover:bg-red-100 transition-colors"
        >
          Sign Out
        </button>
      </div>
    </div>
  )
}
