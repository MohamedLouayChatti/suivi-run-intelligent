const INITIAL_RETRY_MS = 1_000
const MAX_RETRY_MS = 30_000

interface SseEvent {
  event: string
  data: string
}

interface ConnectSseOptions {
  buildUrl: () => string
  getAuthToken: () => Promise<string | null>
  onEvent: (event: SseEvent) => void
  onConnectionChange?: (connected: boolean) => void
}

/**
 * Generic fetch-based SSE client, shared by every module under src/services/sse/*.
 *
 * Native `EventSource` can't send an `Authorization` header, and every backend route
 * (including the stream endpoints) expects header-based Bearer auth like the rest of
 * the API — so streams are read by hand from a `fetch` response body instead.
 *
 * Reconnects with exponential backoff on drop/error; `close()` stops that loop for good
 * (component unmount, sign-out).
 */
function connectSse(options: ConnectSseOptions): () => void {
  let closed = false
  let controller: AbortController | null = null
  let retryMs = INITIAL_RETRY_MS
  let retryTimeout: ReturnType<typeof setTimeout> | null = null

  function wait(ms: number): Promise<void> {
    return new Promise((resolve) => {
      retryTimeout = setTimeout(resolve, ms)
    })
  }

  async function run(): Promise<void> {
    while (!closed) {
      controller = new AbortController()
      try {
        const token = await options.getAuthToken()
        const response = await fetch(options.buildUrl(), {
          method: "GET",
          headers: {
            Accept: "text/event-stream",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          signal: controller.signal,
        })

        if (!response.ok || !response.body) {
          throw new Error(`SSE connection failed with status ${response.status}`)
        }

        options.onConnectionChange?.(true)
        retryMs = INITIAL_RETRY_MS
        await readStream(response.body, options.onEvent)

        if (closed) return
      } catch (error) {
        if (closed || (error instanceof DOMException && error.name === "AbortError")) {
          return
        }
      }

      options.onConnectionChange?.(false)
      if (closed) return
      await wait(retryMs)
      retryMs = Math.min(retryMs * 2, MAX_RETRY_MS)
    }
  }

  void run()

  return () => {
    closed = true
    controller?.abort()
    if (retryTimeout) clearTimeout(retryTimeout)
  }
}

async function readStream(body: ReadableStream<Uint8Array>, onEvent: (event: SseEvent) => void): Promise<void> {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) return
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n")

    let boundary = buffer.indexOf("\n\n")
    while (boundary !== -1) {
      const parsed = parseEventBlock(buffer.slice(0, boundary))
      buffer = buffer.slice(boundary + 2)
      if (parsed) onEvent(parsed)
      boundary = buffer.indexOf("\n\n")
    }
  }
}

/** One `event:`/`data:` block. Lines starting with `:` are comments (the backend's keep-alive pings) — ignored. */
function parseEventBlock(block: string): SseEvent | null {
  let eventName = "message"
  const dataLines: string[] = []

  for (const line of block.split("\n")) {
    if (line.startsWith(":")) continue
    if (line.startsWith("event:")) {
      eventName = line.slice("event:".length).trim()
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trimStart())
    }
  }

  if (dataLines.length === 0) return null
  return { event: eventName, data: dataLines.join("\n") }
}

export { connectSse }
export type { SseEvent, ConnectSseOptions }
