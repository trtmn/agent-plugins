import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { NumberTicker } from "@/components/ui/number-ticker"
import { useStaticMode } from "@/lib/static-mode"
import { cn } from "@/lib/utils"

export type KpiProps = {
  label: string
  value: number
  prefix?: string
  suffix?: string
  decimals?: number
  /** Change vs. previous period, e.g. 12.4 for +12.4%. */
  delta?: number
  /** Set true when a negative delta is good (costs, latency, churn). */
  invertDelta?: boolean
  hint?: string
  className?: string
}

/** A stat tile: animated with NumberTicker on screen, exact text in print. */
export function Kpi({
  label,
  value,
  prefix,
  suffix,
  decimals = 0,
  delta,
  invertDelta = false,
  hint,
  className,
}: KpiProps) {
  const isStatic = useStaticMode()
  const good = delta === undefined ? null : invertDelta ? delta < 0 : delta > 0
  const DeltaIcon =
    delta === undefined || delta === 0
      ? Minus
      : delta > 0
        ? ArrowUpRight
        : ArrowDownRight

  return (
    <Card className={cn("print-avoid-break", className)}>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-1">
        <div className="text-3xl font-semibold tracking-tight tabular-nums">
          {prefix}
          {isStatic ? (
            value.toLocaleString(undefined, {
              minimumFractionDigits: decimals,
              maximumFractionDigits: decimals,
            })
          ) : (
            <NumberTicker value={value} decimalPlaces={decimals} />
          )}
          {suffix}
        </div>
        {(delta !== undefined || hint) && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            {delta !== undefined && (
              <span
                className={cn(
                  "inline-flex items-center gap-0.5 font-medium tabular-nums",
                  good === true && "text-emerald-600 dark:text-emerald-400",
                  good === false && "text-rose-600 dark:text-rose-400"
                )}
              >
                <DeltaIcon className="size-3.5" aria-hidden />
                {delta > 0 ? "+" : ""}
                {delta.toFixed(1)}%
              </span>
            )}
            {hint && <span>{hint}</span>}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
