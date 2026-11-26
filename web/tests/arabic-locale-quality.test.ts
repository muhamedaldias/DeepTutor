import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

function findLocalesRoot(): string {
  let dir = process.cwd()
  for (let i = 0; i < 8; i++) {
    const candidate = path.join(dir, 'locales', 'ar', 'app.json')
    if (fs.existsSync(candidate)) return path.join(dir, 'locales')
    dir = path.dirname(dir)
  }
  throw new Error('could not locate locales/ar/app.json')
}

const localesRoot = findLocalesRoot()
const readCatalog = (locale: string, name = 'app.json') =>
  JSON.parse(fs.readFileSync(path.join(localesRoot, locale, name), 'utf8')) as Record<
    string,
    string
  >

const arabic = readCatalog('ar')
const english = readCatalog('en')
const arabicScript = /[\u0600-\u06ff]/
const tokenPattern = /(\{\{[^}]+\}\}|<[^>]+>|\{[a-zA-Z_][a-zA-Z0-9_]*\}|%[sd])/g
const tokens = (value: string) => value.match(tokenPattern) ?? []
const brands = /^(DeepTutor|Hermes|Codex|OpenCode|Claude Code|ChatGPT|Bilibili|YouTube|GitHub|OpenAI|Anthropic|Google|Notion|Slack|Discord|Telegram|MCP|ACP|JSON|LaTeX|Markdown|PDF|CSV|API|URL|HTTP|HTTPS|HTML|CSS|esc|geogebra|gpt-4o|Grok CLI|Grok|Glob|RAG-Anything|RAG|Redis|markitdown|mermaid|Chroma|FAISS|Ollama|LM Studio|Qdrant|Milvus|Pinecone|Weaviate|Neo4j|PostgreSQL|SQLite|MySQL|MongoDB|Elasticsearch|Kubernetes|GraphQL|REST|SDK|CLI|IDE|Git|pip|uv|curl|wget|jq|YAML|TOML|XML|SVG|PNG|JPG|GIF|MP4|JSONL|TSV|DOCX|PPTX|XLSX|EPUB|MOBI|OCR|TTS|STT|ASR|LLM|GUI|UI|UX|CPU|GPU|RAM|SSH|VPN|DNS|IP|TCP|UDP|URI|JS|TS|React|Next\.js|Vue|Angular|Svelte|Tailwind|Playwright|Puppeteer|Selenium|npm|pnpm|Python|Docker|Linux|Windows|macOS|Android|iOS)$/i
const isPassThrough = (value: string) =>
  brands.test(value.trim()) ||
  value.includes('http') ||
  /\bURL\b/i.test(value) ||
  value.includes('placeholder') ||
  !/[A-Za-z]/.test(value.replace(tokenPattern, '')) ||
  (() => {
    const words = value.replace(tokenPattern, '').trim().split(/\s+/).map(w => w.replace(/^[()/.,\-×'"]+|[()/.,\-×'"]+$/g, '')).filter(Boolean)
    return words.length > 0 && value.length <= 60 && words.every(w => /^[A-Z0-9]/.test(w))
  })() ||
  (!/\s/.test(value) && /[*/._-]/.test(value) && !value.trimEnd().endsWith('...') && !value.includes(':'))

test('Arabic catalog has full key parity with English', () => {
  const enKeys = new Set(Object.keys(english))
  const extra = Object.keys(arabic).filter(key =>
    !enKeys.has(key) && !/_(zero|two|few|many)$/.test(key)
  )
  const missing = [...enKeys].filter(key => !Object.hasOwn(arabic, key))
  assert.deepEqual(missing, [], `missing: ${missing.slice(0, 20).join(', ')}`)
  assert.deepEqual(extra, [], `unexpected: ${extra.slice(0, 20).join(', ')}`)
})

test('Arabic values are translated and keep placeholders intact', () => {
  const offenders: string[] = []
  for (const [key, source] of Object.entries(english)) {
    const target = arabic[key]
    assert.equal(typeof target, 'string', `missing Arabic value for: ${key}`)
    if (target.includes('__UNTRANSLATED__')) offenders.push(`${key}: untranslated marker`)
    if (target === source) {
      if (!isPassThrough(source)) offenders.push(`${key}: unchanged English`)
    } else if (isPassThrough(source)) {
      if (!arabicScript.test(target)) offenders.push(`${key}: pass-through altered`)
    } else {
      if (!arabicScript.test(target)) offenders.push(`${key}: no Arabic script`)
      if (JSON.stringify(tokens(source)) !== JSON.stringify(tokens(target)))
        offenders.push(`${key}: placeholder drift`)
    }
  }
  assert.deepEqual(offenders, [], offenders.slice(0, 20).join('\n'))
})

test('every catalog names Arabic by its endonym', () => {
  for (const locale of fs.readdirSync(localesRoot).filter(name =>
    fs.existsSync(path.join(localesRoot, name, 'app.json'))
  )) {
    assert.equal(readCatalog(locale)['language.arabic'], 'العربية', locale)
  }
})
