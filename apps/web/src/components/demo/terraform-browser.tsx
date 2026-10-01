"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { cn } from "@/lib/utils"

export interface BrowserFile {
  name: string
  content: string
  lineCount: number
}

export interface BrowserReference {
  file: string
  line: number
  label: string
  code: string
}

interface TerraformBrowserProps {
  files: BrowserFile[]
  references: BrowserReference[]
  defaultFile: string
  importsFile: string
}

const FOCUS_RING =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"

function readFileParam(names: string[]): string | null {
  try {
    const wanted = new URLSearchParams(window.location.search).get("file")
    return wanted && names.includes(wanted) ? wanted : null
  } catch {
    return null
  }
}

/**
 * File list + code viewer. All file contents arrive as props (read at build
 * time by the server component), so switching files never touches the network.
 * The selected file lives in `?file=` so links are shareable.
 */
export function TerraformBrowser({
  files,
  references,
  defaultFile,
  importsFile,
}: TerraformBrowserProps) {
  const names = files.map((f) => f.name)
  const [selected, setSelected] = useState(defaultFile)
  const listRef = useRef<HTMLUListElement>(null)
  const viewerRef = useRef<HTMLPreElement>(null)

  // Pick up ?file= after hydration (static export: no request-time params).
  useEffect(() => {
    const fromUrl = readFileParam(names)
    if (fromUrl) setSelected(fromUrl)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const select = useCallback(
    (name: string) => {
      setSelected(name)
      if (viewerRef.current) viewerRef.current.scrollTop = 0
      try {
        const url = new URL(window.location.href)
        if (name === defaultFile) url.searchParams.delete("file")
        else url.searchParams.set("file", name)
        window.history.replaceState(null, "", url.toString())
      } catch {
        // History API unavailable; selection still works.
      }
    },
    [defaultFile]
  )

  const onListKeyDown = (e: React.KeyboardEvent<HTMLUListElement>) => {
    const buttons = Array.from(
      listRef.current?.querySelectorAll<HTMLButtonElement>("button[data-file]") ?? []
    )
    const i = buttons.indexOf(document.activeElement as HTMLButtonElement)
    if (i === -1) return
    const move = (n: number) => {
      e.preventDefault()
      buttons[(n + buttons.length) % buttons.length]?.focus()
    }
    if (e.key === "ArrowDown") move(i + 1)
    else if (e.key === "ArrowUp") move(i - 1)
    else if (e.key === "Home") move(0)
    else if (e.key === "End") move(buttons.length - 1)
  }

  const current = files.find((f) => f.name === selected) ?? files[0]
  const highlighted = new Set(
    references.filter((r) => r.file === current.name).map((r) => r.line)
  )
  const lines = current.content.replace(/\n$/, "").split("\n")
  const gutter = String(lines.length).length

  return (
    <div>
      <div className="rounded-lg border border-emerald-500/30 bg-card p-4 mb-4">
        <p className="text-sm font-medium text-foreground mb-2">
          Where the graph becomes code: real cross-resource references in these files
        </p>
        <ul className="space-y-2 text-sm text-muted-foreground">
          {references.map((r) => (
            <li key={`${r.file}:${r.line}`}>
              {r.label},{" "}
              <button
                type="button"
                onClick={() => select(r.file)}
                className={cn(
                  "font-mono text-emerald-400 underline underline-offset-4 hover:text-emerald-300 rounded-sm",
                  FOCUS_RING
                )}
              >
                {r.file}:{r.line}
              </button>
              <code className="mt-1 block max-w-full overflow-x-auto whitespace-nowrap rounded bg-muted/60 px-2 py-1 font-mono text-xs text-foreground">
                {r.code}
              </code>
            </li>
          ))}
        </ul>
        <p className="text-sm text-muted-foreground mt-3">
          Those lines are highlighted in the viewer. Then see{" "}
          <button
            type="button"
            onClick={() => select(importsFile)}
            className={cn(
              "font-mono text-emerald-400 underline underline-offset-4 hover:text-emerald-300 rounded-sm",
              FOCUS_RING
            )}
          >
            {importsFile}
          </button>
          : one <code className="font-mono text-foreground">import</code> block per resource, so
          Terraform adopts what already exists instead of recreating it.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-[13rem_minmax(0,1fr)]">
        <nav aria-label="Generated Terraform files">
          <ul
            ref={listRef}
            onKeyDown={onListKeyDown}
            className="max-h-48 md:max-h-[34rem] overflow-y-auto rounded-lg border border-border bg-card p-1 space-y-0.5"
          >
            {files.map((f) => {
              const active = f.name === current.name
              return (
                <li key={f.name}>
                  <button
                    type="button"
                    data-file={f.name}
                    aria-current={active ? "true" : undefined}
                    onClick={() => select(f.name)}
                    className={cn(
                      "flex w-full items-center justify-between gap-2 rounded-md px-3 py-1.5 text-left font-mono text-sm transition-colors",
                      FOCUS_RING,
                      active
                        ? "bg-emerald-500/15 text-emerald-300"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    )}
                  >
                    <span className="truncate">{f.name}</span>
                    <span className="shrink-0 text-xs text-muted-foreground">{f.lineCount}</span>
                  </button>
                </li>
              )
            })}
          </ul>
        </nav>

        <div className="min-w-0">
          <div className="flex items-center justify-between gap-3 rounded-t-lg border border-b-0 border-border bg-muted/50 px-4 py-2">
            <h3 className="font-mono text-sm text-foreground truncate">{current.name}</h3>
            <a
              href={`/demo/terraform/${current.name}`}
              className={cn(
                "shrink-0 text-xs text-emerald-400 underline underline-offset-4 hover:text-emerald-300 rounded-sm",
                FOCUS_RING
              )}
            >
              Raw file
            </a>
          </div>
          <pre
            ref={viewerRef}
            tabIndex={0}
            aria-label={`Contents of ${current.name}`}
            className={cn(
              "h-[26rem] md:h-[34rem] overflow-auto rounded-b-lg border border-border bg-card py-3 font-mono text-[13px] leading-6 text-foreground",
              FOCUS_RING
            )}
          >
            <code className="block w-max min-w-full">
              {lines.map((line, i) => {
                const n = i + 1
                const hl = highlighted.has(n)
                return (
                  <span
                    key={n}
                    className={cn(
                      "flex px-4",
                      hl && "bg-emerald-500/15 shadow-[inset_2px_0_0] shadow-emerald-400"
                    )}
                  >
                    <span
                      aria-hidden="true"
                      className="mr-4 shrink-0 select-none text-right text-muted-foreground/60"
                      style={{ minWidth: `${gutter}ch` }}
                    >
                      {n}
                    </span>
                    <span className="whitespace-pre">{line || " "}</span>
                  </span>
                )
              })}
            </code>
          </pre>
        </div>
      </div>
    </div>
  )
}
