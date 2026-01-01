import { type NextRequest, NextResponse } from "next/server"

// Force dynamic rendering
export const dynamic = 'force-dynamic'

// Temporary storage for 2FA status
// In production, use Redis or a database
const twoFAStatus: Record<string, boolean> = {}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const sessionId = searchParams.get("session") || "default"

    return NextResponse.json({
      requires2fa: twoFAStatus[sessionId] || false,
    })
  } catch (error) {
    console.log("[v0] Error checking 2FA status:", error)
    return NextResponse.json({
      requires2fa: false,
    })
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { sessionId = "default", requires2fa } = body

    twoFAStatus[sessionId] = requires2fa

    return NextResponse.json({ success: true })
  } catch (error) {
    console.log("[v0] Error setting 2FA status:", error)
    return NextResponse.json({ success: true })
  }
}
