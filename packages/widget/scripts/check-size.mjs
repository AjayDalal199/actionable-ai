import { readFileSync } from "node:fs"
import { dirname, resolve } from "node:path"
import { fileURLToPath } from "node:url"
import { gzipSync } from "node:zlib"

// One script on every customer page. Fail the build above 80 KB gzipped.
const limit = 80 * 1024
const file = resolve(
  dirname(fileURLToPath(import.meta.url)),
  "../../../backend/app/widget/widget.js",
)
const gzip = gzipSync(readFileSync(file)).length
if (gzip > limit) {
  console.error(`widget.js is ${gzip} bytes gzipped; budget is ${limit}`)
  process.exit(1)
}
console.log(`widget.js gzip ${gzip}`)
