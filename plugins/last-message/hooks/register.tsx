import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

const last = atom({ plugin: 'last-message', key: 'text' } as const, null)

export const register: Register = on => {
  on('prompt.submit', async ($, e, next) => {
    const text = e.text.trim()
    // Only the person's own prompts: not task notifications, peers or schedules.
    const isPerson = e.origin?.kind === 'composer' || e.origin?.kind === 'bridge'
    if (isPerson && text && !text.startsWith('/')) {
      await update($, last, () => text)
    }
    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const text = await read($, last)
    if (text === null || e.props.hasSurvey) {
      return next(e)
    }

    const { Box, Text } = $.ui.resolve(e)

    return (
      <Box>
        <Text bold color="black" backgroundColor="yellow" wrap="truncate-end">
          {' > '}
          {text.replace(/\s+/g, ' ')}{' '}
        </Text>
      </Box>
    )
  })
}
