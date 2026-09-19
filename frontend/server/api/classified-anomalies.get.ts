import { readFile } from 'fs/promises'
import { join } from 'path'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const equipmentId = query.equipment as string | undefined
  const category = query.category as string | undefined
  const severity = query.severity as string | undefined
  const limit = query.limit ? parseInt(query.limit as string) : 500

  try {
    const filePath = join(process.cwd(), 'server', 'data', 'classified_anomalies.json')
    const raw = await readFile(filePath, 'utf-8')
    let records = JSON.parse(raw)

    if (equipmentId && equipmentId !== 'ALL') {
      records = records.filter((r: any) => r.equipment_id === equipmentId)
    }

    if (category && category !== 'ALL') {
      records = records.filter((r: any) => r.category === category)
    }

    if (severity && severity !== 'ALL') {
      records = records.filter((r: any) => r.severity === severity)
    }

    return records.slice(0, limit)
  } catch (err: any) {
    throw createError({
      statusCode: 500,
      statusMessage: `Failed to read classified anomalies: ${err.message}`
    })
  }
})
