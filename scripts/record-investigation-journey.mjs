/**
 * Focused investigation journey: login as invented officer → quick actions →
 * FIR search → Case 360 tabs → analytics → reports → evidence → logout.
 */
import { chromium } from 'playwright'
import fs from 'node:fs'
import path from 'node:path'

const BASE = process.env.ANVAYA_BASE_URL || 'https://appsail-50044124045.development.catalystappsail.in'
const OUT = process.env.WORKFLOW_OUT || '/opt/cursor/artifacts/workflow-record'
const PERSONA = {
  officer_id: 'KSP/MYS/INV/7731',
  password: 'NexusWalkthru2026!',
}

fs.mkdirSync(path.join(OUT, 'screens-journey'), { recursive: true })
const steps = []
let n = 0

async function shot(page, name, note) {
  n += 1
  const file = `screens-journey/${String(n).padStart(2, '0')}-${name}.png`
  await page.screenshot({ path: path.join(OUT, file), fullPage: false })
  steps.push({ step: n, name, note, url: page.url(), screenshot: file })
  console.log(`[${n}] ${name}`)
}

async function main() {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] })
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    recordVideo: { dir: path.join(OUT, 'video-journey-raw'), size: { width: 1440, height: 900 } },
  })
  const page = await context.newPage()
  page.setDefaultTimeout(25000)

  // Login
  await page.goto(`${BASE}/auth/login`, { waitUntil: 'domcontentloaded' })
  await page.fill('#officer-id', PERSONA.officer_id)
  await page.fill('#login-password', PERSONA.password)
  await page.getByRole('button', { name: /Sign In/i }).click()
  await page.waitForURL(/\/app/, { timeout: 20000 }).catch(() => {})
  await page.waitForTimeout(1500)
  await shot(page, 'home', 'AI Home after login as Ananya Krishnamurthy')

  // Quick action: Pending Investigations card
  const pending = page.getByText(/Pending Investigations|unresolved chain/i)
  if (await pending.count()) {
    await pending.first().click()
    await page.waitForTimeout(5000)
    await shot(page, 'pending-investigations', 'Quick card: unresolved chain snatching')
  }

  // Confirm Search records if shown
  const searchRec = page.getByRole('button', { name: /Search records|ದಾಖಲೆಗಳನ್ನು ಹುಡುಕಿ/i })
  if (await searchRec.count()) {
    await searchRec.first().click()
    await page.waitForTimeout(5000)
    await shot(page, 'search-confirmed', 'Confirmed Search records')
  }

  // Open Case 360
  const open360 = page.getByRole('button', { name: /Open Case 360|Case 360/i })
  if (await open360.count()) {
    await open360.first().click()
    await page.waitForTimeout(2500)
    await shot(page, 'case-360-open', 'Case 360 opened')
  }

  // Case view tabs from chat result
  for (const label of ['Related cases', 'Relationship graph', 'Verification priorities', 'Record assurance', 'Grounded brief']) {
    const tab = page.getByRole('button', { name: new RegExp(label, 'i') })
    if (await tab.count()) {
      await tab.first().click().catch(() => {})
      await page.waitForTimeout(1200)
      await shot(page, `tab-${label.toLowerCase().replace(/\s+/g, '-')}`, `Case view tab: ${label}`)
    }
  }

  // Prepare brief / PDF
  for (const label of [/Prepare brief/i, /Download.*PDF|PDF/i, /Preview/i, /Dossier/i]) {
    const btn = page.getByRole('button', { name: label })
    if (await btn.count()) {
      await btn.first().click().catch(() => {})
      await page.waitForTimeout(2000)
      await shot(page, 'brief-pdf', `Clicked ${label}`)
      await page.keyboard.press('Escape').catch(() => {})
      break
    }
  }

  // New chat + FIR Search pill
  await page.goto(`${BASE}/app`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(1000)
  const firPill = page.getByRole('button', { name: /FIR Search/i })
  if (await firPill.count()) {
    await firPill.first().click()
    await page.waitForTimeout(1500)
    await shot(page, 'fir-search-pill', 'FIR Search quick action')
  }

  const caseSummary = page.getByText(/Case Summary|SYN-FIR/i)
  if (await caseSummary.count()) {
    await caseSummary.first().click()
    await page.waitForTimeout(5000)
    await shot(page, 'case-summary-card', 'Case Summary quick card')
  }

  // Chat: send me PDF
  const composer = page.locator('textarea, [contenteditable="true"]').first()
  if (await composer.count()) {
    await composer.click()
    await composer.fill('send me PDF')
    const send = page.locator('button').filter({ has: page.locator('svg') }).last()
    // Prefer explicit send near composer
    const sendBtn = page.getByRole('button', { name: /send/i })
    if (await sendBtn.count()) await sendBtn.first().click()
    else await page.keyboard.press('Enter')
    await page.waitForTimeout(5000)
    await shot(page, 'send-me-pdf', 'Chat assist: send me PDF')
  }

  // Form-first legacy search with demo query
  await page.goto(`${BASE}/dashboard/search`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(1200)
  const demo = page.getByRole('button', { name: /Try demo query|demo query/i })
  if (await demo.count()) {
    await demo.first().click()
    await page.waitForTimeout(1000)
    await shot(page, 'demo-query-loaded', 'Loaded prepared demo query')
  }
  // Offence chips
  const chip = page.getByRole('button', { name: /Chain snatching/i })
  if (await chip.count()) await chip.first().click().catch(() => {})
  await page.waitForTimeout(500)
  const searchBtn = page.getByRole('button', { name: /Search records/i })
  if (await searchBtn.count()) {
    await searchBtn.first().click()
    await page.waitForTimeout(5000)
    await shot(page, 'form-search-results', 'Form-first Search records results')
  }
  const open2 = page.getByRole('button', { name: /Open Case 360/i })
  if (await open2.count()) {
    await open2.first().click()
    await page.waitForTimeout(2500)
    await shot(page, 'form-case-360', 'Case 360 from form search')
    for (const label of ['Related', 'Graph', 'Network', 'Priorities', 'Prepare brief']) {
      const b = page.getByRole('button', { name: new RegExp(label, 'i') })
      if (await b.count()) {
        await b.first().click().catch(() => {})
        await page.waitForTimeout(1500)
        await shot(page, `drawer-${label.toLowerCase().replace(/\s+/g, '-')}`, `Drawer action: ${label}`)
      }
    }
  }

  // Remaining modules briefly
  for (const [p, name] of [
    ['/app/dashboard', 'module-dashboard'],
    ['/app/analytics', 'module-analytics'],
    ['/app/reports', 'module-reports'],
    ['/app/evidence', 'module-evidence'],
    ['/app/settings', 'module-settings'],
  ]) {
    await page.goto(`${BASE}${p}`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(1200)
    await shot(page, name, p)
  }

  // Logout
  await page.getByRole('button', { name: /Logout|Log out/i }).first().click().catch(() => {})
  await page.waitForTimeout(1200)
  await shot(page, 'logged-out', 'Back at login')

  fs.writeFileSync(path.join(OUT, 'journey-log.json'), JSON.stringify({ persona: PERSONA.officer_id, steps }, null, 2))
  await context.close()
  await browser.close()

  const raw = path.join(OUT, 'video-journey-raw')
  if (fs.existsSync(raw)) {
    const vids = fs.readdirSync(raw).filter((f) => f.endsWith('.webm'))
    if (vids[0]) fs.renameSync(path.join(raw, vids[0]), path.join(OUT, 'anvaya-investigation-journey.webm'))
  }
  console.log('Journey done:', steps.length, 'steps')
}

main().catch((e) => { console.error(e); process.exit(1) })
