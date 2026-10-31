import { resolve } from "node:path"
import { defineConfig } from "vite"

export default defineConfig({
  build: {
    lib: {
      entry: resolve(import.meta.dirname, "src/index.ts"),
      name: "A2I",
      formats: ["iife"],
      fileName: () => "widget.js",
    },
    outDir: resolve(import.meta.dirname, "../../backend/app/widget"),
    emptyOutDir: true,
    cssCodeSplit: false,
    minify: true,
    rollupOptions: {
      output: {
        exports: "named",
      },
    },
  },
})
