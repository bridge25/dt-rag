/**
 * Health check API endpoint
 *
 * @CODE:FRONTEND-001
 */

export async function GET() {
  return Response.json({ status: "ok" }, { status: 200 })
}
