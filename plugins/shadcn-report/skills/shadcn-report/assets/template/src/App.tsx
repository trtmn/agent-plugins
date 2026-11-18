/**
 * STARTER REPORT — replace the REPORT data and reshape the sections to fit the
 * story. Keep the data in one object at the top so the layout stays readable.
 */
import { Moon, Sun } from "lucide-react"
import { Area, AreaChart, Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"

import { Kpi } from "@/components/report/kpi"
import { Reveal } from "@/components/report/reveal"
import { useTheme } from "@/components/theme-provider"
import { Badge } from "@/components/ui/badge"
import { BorderBeam } from "@/components/ui/border-beam"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"
import { Separator } from "@/components/ui/separator"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useStaticMode } from "@/lib/static-mode"

const REPORT = {
  title: "Quarterly Operations Report",
  subtitle: "Q3 2026 · prepared for the leadership team",
  generated: "2026-11-18",
  tags: ["Draft", "Internal"],
  summary:
    "Revenue grew steadily through the quarter while support load fell after the September release. Two risks need a decision before Q4 planning.",
  kpis: [
    { label: "Revenue", value: 482300, prefix: "$", delta: 12.4, hint: "vs Q2" },
    { label: "Active accounts", value: 1284, delta: 4.1, hint: "vs Q2" },
    { label: "Avg. resolution", value: 3.2, suffix: "h", decimals: 1, delta: -18.0, invertDelta: true, hint: "vs Q2" },
    { label: "Churn", value: 1.9, suffix: "%", decimals: 1, delta: 0.3, invertDelta: true, hint: "vs Q2" },
  ],
  monthly: [
    { month: "Jul", revenue: 148000, cost: 96000 },
    { month: "Aug", revenue: 159500, cost: 99000 },
    { month: "Sep", revenue: 174800, cost: 101500 },
  ],
  byRegion: [
    { region: "NA", accounts: 612 },
    { region: "EMEA", accounts: 401 },
    { region: "APAC", accounts: 211 },
    { region: "LATAM", accounts: 60 },
  ],
  findings: [
    { item: "Support backlog cleared", owner: "Support", status: "Done" },
    { item: "EMEA pricing review", owner: "Finance", status: "At risk" },
    { item: "Data retention policy", owner: "Legal", status: "Blocked" },
  ],
}

const trendConfig = {
  revenue: { label: "Revenue", color: "var(--chart-1)" },
  cost: { label: "Cost", color: "var(--chart-2)" },
} satisfies ChartConfig

const regionConfig = {
  accounts: { label: "Accounts", color: "var(--chart-1)" },
} satisfies ChartConfig

const STATUS_VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  Done: "secondary",
  "At risk": "outline",
  Blocked: "destructive",
}

function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const dark =
    theme === "dark" ||
    (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches)
  return (
    <Button
      variant="ghost"
      size="icon"
      className="print-hidden"
      aria-label="Toggle dark mode"
      onClick={() => setTheme(dark ? "light" : "dark")}
    >
      {dark ? <Sun /> : <Moon />}
    </Button>
  )
}

export function App() {
  const isStatic = useStaticMode()

  return (
    <div className="min-h-svh bg-background text-foreground">
      <main className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-10 sm:px-8">
        {/* Header */}
        <header className="flex flex-col gap-3">
          <div className="flex items-start justify-between gap-4">
            <div className="flex flex-col gap-2">
              <div className="flex flex-wrap gap-2">
                {REPORT.tags.map((t) => (
                  <Badge key={t} variant="outline">
                    {t}
                  </Badge>
                ))}
              </div>
              <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
                {REPORT.title}
              </h1>
              <p className="text-muted-foreground">{REPORT.subtitle}</p>
            </div>
            <ThemeToggle />
          </div>
          <Separator />
        </header>

        {/* Executive summary — the one card that gets the animated border */}
        <Reveal>
          <Card className="relative overflow-hidden print-avoid-break">
            <CardHeader>
              <CardTitle>Executive summary</CardTitle>
            </CardHeader>
            <CardContent className="text-pretty leading-relaxed">
              {REPORT.summary}
            </CardContent>
            {!isStatic && <BorderBeam size={120} duration={10} />}
          </Card>
        </Reveal>

        {/* KPI row */}
        <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {REPORT.kpis.map((k, i) => (
            <Reveal key={k.label} delay={0.05 * i}>
              <Kpi {...k} />
            </Reveal>
          ))}
        </section>

        {/* Charts */}
        <Reveal>
          <Card className="print-avoid-break">
            <CardHeader>
              <CardTitle>Performance</CardTitle>
              <CardDescription>Monthly revenue vs. cost, and accounts by region</CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="trend">
                <TabsList className="print-hidden">
                  <TabsTrigger value="trend">Trend</TabsTrigger>
                  <TabsTrigger value="region">By region</TabsTrigger>
                </TabsList>
                <TabsContent value="trend">
                  <ChartContainer config={trendConfig} className="aspect-auto h-72 w-full">
                    <AreaChart data={REPORT.monthly} margin={{ left: 12, right: 12 }}>
                      <CartesianGrid vertical={false} />
                      <XAxis dataKey="month" tickLine={false} axisLine={false} tickMargin={8} />
                      <YAxis
                        tickLine={false}
                        axisLine={false}
                        width={56}
                        tickFormatter={(v: number) => `$${Math.round(v / 1000)}k`}
                      />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <ChartLegend content={<ChartLegendContent />} />
                      <Area
                        dataKey="revenue"
                        type="monotone"
                        fill="var(--color-revenue)"
                        fillOpacity={0.25}
                        stroke="var(--color-revenue)"
                        isAnimationActive={!isStatic}
                      />
                      <Area
                        dataKey="cost"
                        type="monotone"
                        fill="var(--color-cost)"
                        fillOpacity={0.15}
                        stroke="var(--color-cost)"
                        isAnimationActive={!isStatic}
                      />
                    </AreaChart>
                  </ChartContainer>
                </TabsContent>
                <TabsContent value="region">
                  <ChartContainer config={regionConfig} className="aspect-auto h-72 w-full">
                    <BarChart data={REPORT.byRegion}>
                      <CartesianGrid vertical={false} />
                      <XAxis dataKey="region" tickLine={false} axisLine={false} tickMargin={8} />
                      <ChartTooltip content={<ChartTooltipContent hideLabel />} />
                      <Bar
                        dataKey="accounts"
                        fill="var(--color-accounts)"
                        radius={6}
                        isAnimationActive={!isStatic}
                      />
                    </BarChart>
                  </ChartContainer>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </Reveal>

        {/* Findings table */}
        <Reveal>
          <Card className="print-avoid-break">
            <CardHeader>
              <CardTitle>Open items</CardTitle>
              <CardDescription>Status as of {REPORT.generated}</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Item</TableHead>
                    <TableHead>Owner</TableHead>
                    <TableHead className="text-right">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {REPORT.findings.map((f) => (
                    <TableRow key={f.item}>
                      <TableCell className="font-medium">{f.item}</TableCell>
                      <TableCell>{f.owner}</TableCell>
                      <TableCell className="text-right">
                        <Badge variant={STATUS_VARIANT[f.status] ?? "outline"}>{f.status}</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </Reveal>

        <footer className="pb-4 text-xs text-muted-foreground">
          Generated {REPORT.generated}
        </footer>
      </main>
    </div>
  )
}

export default App
