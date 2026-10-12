export async function request(path: string, token: string, body?: object, key?: string) {
  const headers: Record<string, string> = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
  if (key) headers['Idempotency-Key'] = key
  const response = await fetch(path, { method: body ? 'POST' : 'GET', headers, body: body ? JSON.stringify(body) : undefined })
  if (!response.ok) throw new Error(`请求失败：${response.status}`)
  return response.json()
}
