import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

const DEFAULT_SITE_URL = 'https://auxshare.netlify.app'

// Replace __SITE_URL__ in index.html, robots.txt and sitemap.xml with the
// deployment origin. Set VITE_SITE_URL at build time to use a custom domain.
function siteUrlPlugin(siteUrl) {
  return {
    name: 'auxshare-site-url',
    transformIndexHtml(html) {
      return html.replaceAll('__SITE_URL__', siteUrl)
    },
    writeBundle(options) {
      const outDir = options.dir || resolve(process.cwd(), 'dist')
      for (const file of ['robots.txt', 'sitemap.xml']) {
        const path = resolve(outDir, file)
        if (!existsSync(path)) continue
        const contents = readFileSync(path, 'utf8').replaceAll('__SITE_URL__', siteUrl)
        writeFileSync(path, contents)
      }
    },
  }
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const siteUrl = (env.VITE_SITE_URL || DEFAULT_SITE_URL).replace(/\/+$/, '')

  return {
    plugins: [
      vue(),
      ...(mode === 'development' ? [vueDevTools()] : []),
      siteUrlPlugin(siteUrl),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    build: {
      sourcemap: false,
      chunkSizeWarningLimit: 700,
    },
  }
})
