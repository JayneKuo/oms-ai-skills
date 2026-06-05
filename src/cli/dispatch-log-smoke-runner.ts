import { runStagingDispatchLogSmoke } from './dispatch-log-smoke-entrypoint'

function readRequiredEnv(name: string) {
  const value = process.env[name]

  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`)
  }

  return value
}

const eventId = readRequiredEnv('OMS_DISPATCH_EVENT_ID')
const env = {
  OMS_BASE_URL: readRequiredEnv('OMS_BASE_URL'),
  OMS_IAM_BASE_URL: readRequiredEnv('OMS_IAM_BASE_URL'),
  OMS_IAM_CLIENT_ID: readRequiredEnv('OMS_IAM_CLIENT_ID'),
  OMS_TENANT_ID: readRequiredEnv('OMS_TENANT_ID'),
  OMS_MERCHANT_NO: readRequiredEnv('OMS_MERCHANT_NO'),
  OMS_USERNAME: readRequiredEnv('OMS_USERNAME'),
  OMS_PASSWORD: readRequiredEnv('OMS_PASSWORD')
}

runStagingDispatchLogSmoke(env, eventId)
  .then((result) => {
    console.log(JSON.stringify(result, null, 2))
  })
  .catch((error: unknown) => {
    const message = error instanceof Error ? error.message : String(error)
    console.error(message)
    process.exitCode = 1
  })
