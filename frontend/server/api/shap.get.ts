import { readFile } from 'fs/promises'
import { join } from 'path'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const equipment = query.equipment as string | undefined

  try {
    const filePath = join(process.cwd(), 'server', 'data', 'shap_samples.json')
    const raw = await readFile(filePath, 'utf-8')
    const samples = JSON.parse(raw)

    if (equipment) {
      return samples.filter((s: any) => s.equipment_id === equipment)
    }

    return samples
  } catch (err: any) {
    throw createError({
      statusCode: 500,
      statusMessage: `Failed to read SHAP samples: ${err.message}`
    })
  }
})
