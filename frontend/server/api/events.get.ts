import { readFile } from 'fs/promises'
import { join } from 'path'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const equipmentId = query.equipment as string | undefined

  try {
    const filePath = join(process.cwd(), 'server', 'data', 'events.json')
    const raw = await readFile(filePath, 'utf-8')
    const events = JSON.parse(raw)

    if (equipmentId) {
      return events.filter((e: any) => e.equipment_id === equipmentId)
    }

    return events
  } catch (err: any) {
    throw createError({
      statusCode: 500,
      statusMessage: `Failed to read events: ${err.message}`
    })
  }
})
