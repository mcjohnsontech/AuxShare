import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { loadEnv } from 'vite'

// Check the actual built HTML without executing JavaScript, just like a link
// crawler. Pass a deployment URL to also check routing and image delivery.
const env = { ...loadEnv('production', process.cwd(), ''), ...process.env }
const siteUrl = env.VITE_SITE_URL.replace(/\/+$/, '')
const deployment = process.argv[2]?.replace(/\/+$/, '')
const imagePath = '/playlist-sharing-preview.jpg'

function checkHtml(html, label) {
  assert(!html.includes('__SITE_URL__'), `${label}: unresolved site URL`)
  for (const key of ['og:image', 'og:image:secure_url', 'twitter:image']) {
    assert(html.includes(`${key}" content="${siteUrl}${imagePath}"`), `${label}: missing absolute ${key}`)
  }
  assert(html.includes('content="summary_large_image"'), `${label}: missing large preview card`)
  assert(html.includes('property="og:image:width" content="1200"'), `${label}: incorrect width`)
  assert(html.includes('property="og:image:height" content="630"'), `${label}: incorrect height`)
  assert(html.includes('property="og:image:type" content="image/jpeg"'), `${label}: incorrect image type`)
}

checkHtml(await readFile(resolve('dist/index.html'), 'utf8'), 'Production HTML')
const image = await readFile(resolve(`dist${imagePath}`))
assert(image[0] === 0xff && image[1] === 0xd8, 'Preview is not a JPEG')
assert(image.length < 500_000, 'Preview image should remain under 500 KB')
await readFile(resolve('dist/fonts/InterVariable.woff2'))
const robots = await readFile(resolve('dist/robots.txt'), 'utf8')
assert(/User-agent: facebookexternalhit[\s\S]*?Allow: \//.test(robots), 'Link crawlers must be allowed to read shared pages')

if (deployment) {
  for (const path of ['/', '/join/preview-check']) {
    const response = await fetch(`${deployment}${path}`, { headers: { 'User-Agent': 'facebookexternalhit/1.1' } })
    assert.equal(response.status, 200, `${path}: crawler cannot load page`)
    checkHtml(await response.text(), path)
  }
  const response = await fetch(`${deployment}${imagePath}`)
  assert.equal(response.status, 200, 'Preview image is not publicly accessible')
  assert(response.headers.get('content-type')?.includes('image/jpeg'), 'Image route returned the wrong content type')
  const deliveredImage = Buffer.from(await response.arrayBuffer())
  assert(deliveredImage[0] === 0xff && deliveredImage[1] === 0xd8, 'Image URL returned HTML instead of an image')
}

console.log(`Link preview verified: static crawler-readable metadata, 1200×630 JPEG (${Math.round(image.length / 1024)} KB), and bundled font${deployment ? ', plus public page and image routes' : ''}.`)
