import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

const goal = atom({ plugin: 'current-goal', key: 'text' } as const, null)

const CLEAR = /^(clear|off|none|reset|stop|cancel)$/i

export const register: Register = on => {
  // `/goal <condition>` sets it; `/goal clear` (and friends) drops it.
  on('command.run', { command: 'goal' }, async ($, e, next) => {
    const result = await next(e)
    const args = e.args.trim()
    if (CLEAR.test(args)) {
      await update($, goal, () => null)
    } else if (args) {
      await update($, goal, () => args)
    }
    return result
  })

  // A goal the model proposed (approved by the person, or set directly).
  on('tool.call', { tool: 'ProposeGoal' }, async ($, e, next) => {
    const result = await next(e)
    if (!('deny' in result && result.deny) && e.input.condition) {
      await update($, goal, () => e.input.condition)
    }
    return result
  })

  // Drawn under whatever else fills the band (e.g. the last-message mod).
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const text = await read($, goal)
    const below = await next(e)
    if (text === null || e.props.hasSurvey) {
      return below
    }

    const { Box, Text } = $.ui.resolve(e)
    const line = (
      <Text color="blueBright" wrap="truncate-end">
        {' ◎ Goal: '}
        {text.replace(/\s+/g, ' ')}
      </Text>
    )

    return below ? (
      <Box flexDirection="column">
        {below}
        {line}
      </Box>
    ) : (
      <Box>{line}</Box>
    )
  })
}
