import { readFileSync } from 'node:fs'
import { runStagingShippingMappingSmoke } from './shipping-mapping-smoke-entrypoint'

function readRequiredEnv(name: string) {
  const value = process.env[name]

  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`)
  }

  return value
}

const fixturePath = process.env.OMS_SHIPPING_MAPPING_FIXTURE_PATH ?? 'tests/fixtures/mapping/shipping-execute.json'
const input = JSON.parse(readFileSync(fixturePath, 'utf8')) as {
  channelId: number
  inputConditions: Record<string, string>
}

const env = {
  OMS_BASE_URL: readRequiredEnv('OMS_BASE_URL'),
  OMS_IAM_BASE_URL: readRequiredEnv('OMS_IAM_BASE_URL'),
  OMS_IAM_CLIENT_ID: readRequiredEnv('OMS_IAM_CLIENT_ID'),
  OMS_TENANT_ID: readRequiredEnv('OMS_TENANT_ID'),
  OMS_MERCHANT_NO: readRequiredEnv('OMS_MERCHANT_NO'),
  OMS_USERNAME: readRequiredEnv('OMS_USERNAME'),
  OMS_PASSWORD: readRequiredEnv('OMS_PASSWORD')
}

runStagingShippingMappingSmoke(env, input)
  .then((result) => {
    console.log(JSON.stringify(result, null, 2))
  })
  .catch((error: unknown) => {
    const message = error instanceof Error ? error.message : String(error)
    console.error(message)
    process.exitCode = 1
  })
