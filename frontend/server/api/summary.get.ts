import { readFile } from 'fs/promises'
import { join } from 'path'

export default defineEventHandler(async () => {
  try {
    const filePath = join(process.cwd(), 'server', 'data', 'summary.json')
    const raw = await readFile(filePath, 'utf-8')
    return JSON.parse(raw)
  } catch (err: any) {
    throw createError({
      statusCode: 500,
      statusMessage: `Failed to read summary data: ${err.message}`
    })
  }
})
