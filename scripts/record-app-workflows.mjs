/**
 * ANVAYA NEXUS — live workflow recorder
 * Invents an officer persona, registers (or logs in), walks every major surface,
 * captures screenshots + a Playwright video, and writes a JSON step log.
 */
import { chromium } from 'playwright'
import fs from 'node:fs'
import path from 'node:path'

const BASE = process.env.ANVAYA_BASE_URL || 'https://appsail-50044124045.development.catalystappsail.in'
const OUT = process.env.WORKFLOW_OUT || '/opt/cursor/artifacts/workflow-record'
const DOCS_OUT = process.env.WORKFLOW_DOCS || '/workspace/docs/workflow-recording'

const PERSONA = {
  officer_id: 'KSP/MYS/INV/7731',
  full_name: 'Ananya Krishnamurthy',
  role: 'INVESTIGATOR',
  station: 'Nazarbad PS',
  district: 'Mysuru',
  password: 'NexusWalkthru2026!',
  idea: 'Junior Investigating Officer at Nazarbad PS (Mysuru) starting a night shift: clear unresolved chain-snatching FIRs, open Case 360, check trends, prepare a brief, then ask Chat Assist for a PDF dossier.',
}

fs.mkdirSync(OUT, { recursive: true })
fs.mkdirSync(path.join(OUT, 'screens'), { recursive: true })
fs.mkdirSync(DOCS_OUT, { recursive: true })

const steps = []
let stepN = 0

async function shot(page, name, note) {
  stepN += 1
  const file = `screens/${String(stepN).padStart(2, '0')}-${name}.png`
  const full = path.join(OUT, file)
  await page.screenshot({ path: full, fullPage: false })
  const entry = {
    step: stepN,
    name,
    note,
    url: page.url(),
    screenshot: file,
    at: new Date().toISOString(),
  }
  steps.push(entry)
  console.log(`[${stepN}] ${name} — ${page.url()}`)
  return entry
}

async function safeClick(page, locator, timeout = 8000) {
  try {
    await locator.first().waitFor({ state: 'visible', timeout })
    await locator.first().click({ timeout })
    return true
  } catch {
    return false
  }
}

async function fillIfVisible(page, selector, value) {
  const el = page.locator(selector).first()
  if (await el.count()) {
    await el.fill(value)
    return true
  }
  return false
}

async function main() {
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  })
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    recordVideo: { dir: path.join(OUT, 'video-raw'), size: { width: 1440, height: 900 } },
    locale: 'en-IN',
  })
  const page = await context.newPage()
  page.setDefaultTimeout(20000)

  // ── 0. Health check via API ──────────────────────────────────────────────
  try {
    const health = await page.request.get(`${BASE}/api/health`)
    const body = await health.json()
    fs.writeFileSync(path.join(OUT, 'health.json'), JSON.stringify(body, null, 2))
    steps.push({ step: 0, name: 'api-health', note: `status=${body?.data?.status} db=${body?.data?.database}`, url: `${BASE}/api/health`, at: new Date().toISOString() })
  } catch (e) {
    steps.push({ step: 0, name: 'api-health', note: `FAILED: ${e.message}`, at: new Date().toISOString() })
  }

  // ── 1. Landing ───────────────────────────────────────────────────────────
  await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(1200)
  await shot(page, 'landing', 'Public landing — KSP / ANVAYA portal entry')

  // Language toggle if present
  const knBtn = page.getByRole('button', { name: /ಕನ್ನಡ|Kannada|English/i })
  if (await knBtn.count()) {
    await knBtn.first().click().catch(() => {})
    await page.waitForTimeout(600)
    await shot(page, 'landing-kannada', 'Landing chrome toggled to Kannada (or back)')
    // toggle back if now English button
    const enBtn = page.getByRole('button', { name: /English|ಕನ್ನಡ/i })
    if (await enBtn.count()) await enBtn.first().click().catch(() => {})
  }

  // ── 2. Login page ────────────────────────────────────────────────────────
  await page.goto(`${BASE}/auth/login`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(800)
  await shot(page, 'login', 'Officer Sign-In page with demo credentials hint')

  // ── 3. Register invented persona ─────────────────────────────────────────
  await page.goto(`${BASE}/auth/register`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(800)
  await shot(page, 'register-empty', 'New Officer Registration form')

  await fillIfVisible(page, '#reg-officer-id', PERSONA.officer_id)
  await fillIfVisible(page, '#reg-full-name', PERSONA.full_name)
  // Role: INVESTIGATOR is default; click to be sure
  const invRole = page.getByText('Investigating Officer', { exact: false })
  if (await invRole.count()) await invRole.first().click().catch(() => {})
  await fillIfVisible(page, '#reg-password', PERSONA.password)
  await fillIfVisible(page, '#reg-confirm', PERSONA.password)
  await fillIfVisible(page, '#reg-station', PERSONA.station)
  await fillIfVisible(page, '#reg-district', PERSONA.district)
  await shot(page, 'register-filled', `Filled registration for ${PERSONA.officer_id} / ${PERSONA.full_name}`)

  let registered = false
  const regBtn = page.getByRole('button', { name: /Register & Sign In|Register/i })
  if (await regBtn.count()) {
    await regBtn.first().click()
    await page.waitForTimeout(2500)
    if (page.url().includes('/app')) {
      registered = true
      await shot(page, 'register-success', 'Registration succeeded — landed in /app')
    } else {
      // likely already registered — capture error then login
      await shot(page, 'register-result', 'Registration did not navigate to /app (may already exist)')
    }
  }

  if (!registered) {
    await page.goto(`${BASE}/auth/login`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(600)
    await fillIfVisible(page, '#officer-id', PERSONA.officer_id)
    await fillIfVisible(page, '#login-password', PERSONA.password)
    await shot(page, 'login-filled', 'Login with invented officer credentials')
    const loginBtn = page.getByRole('button', { name: /Sign In/i })
    await loginBtn.first().click()
    await page.waitForTimeout(2500)
    // Fallback demo credentials if persona login fails
    if (!page.url().includes('/app')) {
      await shot(page, 'login-failed-persona', 'Persona login failed — falling back to demo credentials')
      await fillIfVisible(page, '#officer-id', 'investigator.demo')
      await fillIfVisible(page, '#login-password', 'ANVAYA-DEMO-ONLY-2026')
      await loginBtn.first().click()
      await page.waitForTimeout(2500)
    }
    await shot(page, 'app-home-after-login', 'Authenticated AI Home after sign-in')
  }

  // Ensure we are in app
  if (!page.url().includes('/app')) {
    await page.goto(`${BASE}/app`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(1500)
    await shot(page, 'app-home', 'Forced navigate to /app')
  }

  // ── 4. AI Home / Chat assist ─────────────────────────────────────────────
  await page.waitForTimeout(1000)
  await shot(page, 'ai-home', 'AI Home — conversation assist surface')

  // Try composer query
  const composer = page.locator('textarea, [contenteditable="true"], input[placeholder*="Ask"]').first()
  if (await composer.count()) {
    await composer.click().catch(() => {})
    await composer.fill('Open case SYN-CASE-0001').catch(async () => {
      await page.keyboard.type('Open case SYN-CASE-0001')
    })
    await shot(page, 'chat-query-typed', 'Typed chat assist query: Open case SYN-CASE-0001')
    // Send if button exists
    const send = page.getByRole('button', { name: /Send|Ask|Submit/i })
    if (await send.count()) {
      await send.first().click().catch(() => {})
      await page.waitForTimeout(4000)
      await shot(page, 'chat-query-result', 'Chat assist response after case open query')
    }
  }

  // Search records path if visible
  const searchRecords = page.getByRole('button', { name: /Search records|ದಾಖಲೆಗಳನ್ನು ಹುಡುಕಿ/i })
  if (await searchRecords.count()) {
    await searchRecords.first().click().catch(() => {})
    await page.waitForTimeout(3000)
    await shot(page, 'search-records', 'Search records confirmation executed')
  }

  const openCase = page.getByRole('button', { name: /Open Case 360/i })
  if (await openCase.count()) {
    await openCase.first().click().catch(() => {})
    await page.waitForTimeout(2000)
    await shot(page, 'case-360', 'Case 360 drawer / case detail overlay')
    const prepare = page.getByRole('button', { name: /Prepare brief|Preview|PDF/i })
    if (await prepare.count()) {
      await prepare.first().click().catch(() => {})
      await page.waitForTimeout(2000)
      await shot(page, 'prepare-brief', 'Prepare brief / PDF preview modal')
      await page.keyboard.press('Escape').catch(() => {})
    }
    await page.keyboard.press('Escape').catch(() => {})
  }

  // ── 5. Navigate all sidebar sections ─────────────────────────────────────
  const routes = [
    { path: '/app/dashboard', name: 'dashboard', note: 'Shift Briefing / Dashboard overview' },
    { path: '/app/analytics', name: 'analytics', note: 'Crime Trends / Analytics (descriptive only)' },
    { path: '/app/reports', name: 'reports', note: 'Reports console — dossiers & briefs' },
    { path: '/app/evidence', name: 'evidence', note: 'Evidence repository / chain of custody' },
    { path: '/app/settings', name: 'settings', note: 'Settings — locale, preferences' },
    { path: '/app/supervisor', name: 'supervisor', note: 'Supervisor panel (may be role-gated)' },
    { path: '/app/search', name: 'search-alias', note: 'Search alias route under AppShell' },
  ]

  for (const r of routes) {
    await page.goto(`${BASE}${r.path}`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(1500)
    await shot(page, r.name, r.note)
  }

  // Settings: language toggle
  await page.goto(`${BASE}/app/settings`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(800)
  const langToggle = page.getByRole('button', { name: /ಕನ್ನಡ|Language|Kannada/i })
  if (await langToggle.count()) {
    await langToggle.first().click().catch(() => {})
    await page.waitForTimeout(800)
    await shot(page, 'settings-kannada', 'Settings language switched toward Kannada')
  }

  // Top bar language if present
  await page.goto(`${BASE}/app`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(800)
  const topLang = page.locator('button', { hasText: /Language|ಕನ್ನಡ|EN/ })
  if (await topLang.count()) {
    await topLang.first().click().catch(() => {})
    await page.waitForTimeout(700)
    await shot(page, 'topbar-language', 'TopBar language switcher exercised')
  }

  // Command palette
  await page.keyboard.press('Control+k').catch(() => {})
  await page.waitForTimeout(600)
  await shot(page, 'command-palette', 'Command palette (Ctrl+K) if enabled')
  await page.keyboard.press('Escape').catch(() => {})

  // ── 6. Legacy dashboard routes (still in router) ─────────────────────────
  const legacy = [
    { path: '/dashboard', name: 'legacy-dashboard' },
    { path: '/dashboard/search', name: 'legacy-search' },
    { path: '/dashboard/analytics', name: 'legacy-analytics' },
    { path: '/dashboard/reports', name: 'legacy-reports' },
    { path: '/dashboard/health', name: 'legacy-health' },
  ]
  for (const r of legacy) {
    await page.goto(`${BASE}${r.path}`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(1200)
    await shot(page, r.name, `Legacy AuthenticatedLayout route ${r.path}`)
  }

  // Form-first search on legacy search if filters exist
  await page.goto(`${BASE}/dashboard/search`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(1000)
  const offence = page.locator('input, select').filter({ hasText: /offence|Offence/i })
  // Try common filter fields by label/placeholder
  const offenceInput = page.getByPlaceholder(/offence|Offence|Chain/i)
  if (await offenceInput.count()) {
    await offenceInput.first().fill('Chain snatching').catch(() => {})
  } else {
    // try labeling
    const labelled = page.locator('label:has-text("Offence") + * input, label:has-text("Offence") + input')
    if (await labelled.count()) await labelled.first().fill('Chain snatching').catch(() => {})
  }
  const statusInput = page.getByPlaceholder(/status|Status|UNRESOLVED/i)
  if (await statusInput.count()) await statusInput.first().fill('UNRESOLVED').catch(() => {})
  await shot(page, 'legacy-search-filters', 'Legacy Search with FIR filters attempted')
  const searchBtn = page.getByRole('button', { name: /Search records|ದಾಖಲೆಗಳನ್ನು ಹುಡುಕಿ|Search/i })
  if (await searchBtn.count()) {
    await searchBtn.first().click().catch(() => {})
    await page.waitForTimeout(3500)
    await shot(page, 'legacy-search-results', 'Legacy Search results list')
    if (await page.getByRole('button', { name: /Open Case 360/i }).count()) {
      await page.getByRole('button', { name: /Open Case 360/i }).first().click()
      await page.waitForTimeout(2000)
      await shot(page, 'legacy-case-360', 'Case 360 from legacy search')
      await page.keyboard.press('Escape').catch(() => {})
    }
  }

  // ── 7. Logout ────────────────────────────────────────────────────────────
  await page.goto(`${BASE}/app`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(800)
  const logout = page.getByRole('button', { name: /Log out|Logout|Sign out/i })
  if (await logout.count()) {
    await logout.first().click().catch(() => {})
    await page.waitForTimeout(1500)
    await shot(page, 'logout', 'Logged out — back to login/public')
  } else {
    // try text link
    const logout2 = page.locator('button, a').filter({ hasText: /log\s*out|sign\s*out/i })
    if (await logout2.count()) {
      await logout2.first().click().catch(() => {})
      await page.waitForTimeout(1500)
      await shot(page, 'logout', 'Logged out via secondary control')
    } else {
      await shot(page, 'logout-skipped', 'Logout control not found — session left active')
    }
  }

  // Persist logs
  const log = {
    base_url: BASE,
    persona: {
      officer_id: PERSONA.officer_id,
      full_name: PERSONA.full_name,
      role: PERSONA.role,
      station: PERSONA.station,
      district: PERSONA.district,
      idea: PERSONA.idea,
      // password intentionally omitted from committed docs; kept only in artifacts if needed
    },
    registered_attempt: true,
    steps,
    captured_at: new Date().toISOString(),
  }
  fs.writeFileSync(path.join(OUT, 'workflow-log.json'), JSON.stringify(log, null, 2))
  fs.writeFileSync(path.join(DOCS_OUT, 'workflow-log.json'), JSON.stringify(log, null, 2))

  await context.close()
  await browser.close()

  // Move video to stable name
  const rawDir = path.join(OUT, 'video-raw')
  if (fs.existsSync(rawDir)) {
    const vids = fs.readdirSync(rawDir).filter((f) => f.endsWith('.webm'))
    if (vids.length) {
      const dest = path.join(OUT, 'anvaya-full-workflow.webm')
      fs.renameSync(path.join(rawDir, vids[0]), dest)
      console.log('Video saved:', dest)
    }
  }

  console.log(`Done. ${steps.length} steps. Screens in ${path.join(OUT, 'screens')}`)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
