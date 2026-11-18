import { useEffect, useState } from "react"
import { flushSync } from "react-dom"

/**
 * "Static mode" renders final values with no animation. Magic UI effects
 * (NumberTicker, BlurFade) start hidden / at 0 and only animate when scrolled
 * into view, so without this a printed page, PDF, or full-page screenshot shows
 * zeros and blank sections.
 *
 * Static mode is on when:
 *   - the URL has ?static  (use for screenshots / headless capture)
 *   - the user prefers reduced motion
 *   - the page is being printed (flips on `beforeprint`)
 */
function initialStatic(): boolean {
  if (typeof window === "undefined") return true
  return (
    new URLSearchParams(window.location.search).has("static") ||
    window.matchMedia("(prefers-reduced-motion: reduce)").matches ||
    window.matchMedia("print").matches
  )
}

export function useStaticMode(): boolean {
  const [isStatic, setStatic] = useState(initialStatic)

  useEffect(() => {
    // flushSync so the DOM has final values before the print snapshot is taken.
    const before = () => flushSync(() => setStatic(true))
    const after = () => setStatic(initialStatic())
    window.addEventListener("beforeprint", before)
    window.addEventListener("afterprint", after)
    return () => {
      window.removeEventListener("beforeprint", before)
      window.removeEventListener("afterprint", after)
    }
  }, [])

  return isStatic
}
