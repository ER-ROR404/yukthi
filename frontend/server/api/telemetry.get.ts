import { readFile } from 'fs/promises'
import { join } from 'path'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const equipment = (query.equipment as string) || 'CHILLER-01'
  const maxPoints = query.limit ? parseInt(query.limit as string) : 0

  try {
    const filePath = join(process.cwd(), 'server', 'data', `telemetry_${equipment}.json`)
    const raw = await readFile(filePath, 'utf-8')
    const data = JSON.parse(raw)

    if (maxPoints > 0 && data.length > maxPoints) {
      const step = Math.ceil(data.length / maxPoints)
      return data.filter((_: any, idx: number) => idx % step === 0)
    }

    return data
  } catch (err: any) {
    throw createError({
      statusCode: 404,
      statusMessage: `Telemetry data for ${equipment} not found: ${err.message}`
    })
  }
})
