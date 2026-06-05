import { generateWave1OpenApiSlice } from '../reference/generate-openapi-slice'

type FileOps = {
  readFile: (path: string) => string
  writeFile: (path: string, text: string) => void
}

export function createOpenApiSliceGenerator(fileOps: FileOps) {
  return (sourcePath: string, outputPath: string) => {
    const source = JSON.parse(fileOps.readFile(sourcePath))
    const slice = generateWave1OpenApiSlice(source)
    fileOps.writeFile(outputPath, JSON.stringify(slice, null, 2))
  }
}
