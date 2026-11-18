import type { ReactNode } from "react"

import { BlurFade } from "@/components/ui/blur-fade"
import { useStaticMode } from "@/lib/static-mode"

/** BlurFade on screen; a plain div when printing / static / reduced-motion. */
export function Reveal({
  children,
  delay = 0,
  className,
}: {
  children: ReactNode
  delay?: number
  className?: string
}) {
  const isStatic = useStaticMode()
  if (isStatic) return <div className={className}>{children}</div>
  return (
    <BlurFade inView delay={delay} className={className}>
      {children}
    </BlurFade>
  )
}
