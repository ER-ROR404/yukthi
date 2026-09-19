import { readFile } from 'fs/promises'
import { join } from 'path'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const equipmentId = query.equipment as string | undefined
  const parameter = query.parameter as string | undefined
  const status = query.status as string | undefined
  const minScore = query.min_score ? parseFloat(query.min_score as string) : 0
  const limit = query.limit ? parseInt(query.limit as string) : 500

  try {
    const filePath = join(process.cwd(), 'server', 'data', 'parameter_anomalies.json')
    const raw = await readFile(filePath, 'utf-8')
    let records = JSON.parse(raw)

    if (equipmentId && equipmentId !== 'ALL') {
      records = records.filter((r: any) => r.equipment_id === equipmentId)
    }

    if (parameter && parameter !== 'ALL') {
      records = records.filter((r: any) => r.parameter.toLowerCase().includes(parameter.toLowerCase()))
    }

    if (status && status !== 'ALL') {
      records = records.filter((r: any) => r.status.toUpperCase() === status.toUpperCase())
    }

    if (minScore > 0) {
      records = records.filter((r: any) => r.anomaly_score >= minScore)
    }

    return records.slice(0, limit)
  } catch (err: any) {
    throw createError({
      statusCode: 500,
      statusMessage: `Failed to read parameter anomalies: ${err.message}`
    })
  }
})
