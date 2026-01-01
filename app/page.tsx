"use client"

import { useState, useCallback, useEffect } from "react"
import { AuthProvider } from "@/contexts/auth-context"
import { Header } from "@/components/header"
import { BottomNav } from "@/components/bottom-nav"
import { AuthModal } from "@/components/auth-modal"
import { AccessDeniedModal } from "@/components/access-denied-modal"
import { MarketPage } from "@/components/pages/market-page"
import { GiftsPage } from "@/components/pages/gifts-page"
import { SeasonsPage } from "@/components/pages/seasons-page"
import { PartnersPage } from "@/components/pages/partners-page"
import { ProfilePage } from "@/components/pages/profile-page"
import { ErrorBoundary } from "@/components/error-boundary"

export type TabType = "market" | "gifts" | "seasons" | "partners" | "profile"

function AppContent() {
  const [activeTab, setActiveTab] = useState<TabType>("market")
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    // Delay mounting to avoid SSR conflicts
    const timer = setTimeout(() => {
      setMounted(true)
    }, 0)

    // Initialize Telegram WebApp after a delay
    const telegramTimer = setTimeout(() => {
      if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
        try {
          window.Telegram.WebApp.ready()
          window.Telegram.WebApp.expand()
        } catch (e) {
          console.warn('Telegram WebApp init error:', e)
        }
      }
    }, 100)

    // Global error handler for removeChild errors
    const handleError = (event: ErrorEvent) => {
      if (event.error?.message?.includes('removeChild') || 
          event.error?.name === 'NotFoundError') {
        event.preventDefault()
        console.warn('Suppressed removeChild error:', event.error)
        return false
      }
    }

    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      if (event.reason?.message?.includes('removeChild') ||
          event.reason?.name === 'NotFoundError') {
        event.preventDefault()
        console.warn('Suppressed removeChild promise rejection:', event.reason)
        return false
      }
    }

    window.addEventListener('error', handleError)
    window.addEventListener('unhandledrejection', handleUnhandledRejection)

    return () => {
      clearTimeout(timer)
      clearTimeout(telegramTimer)
      window.removeEventListener('error', handleError)
      window.removeEventListener('unhandledrejection', handleUnhandledRejection)
    }
  }, [])

  const handleTabChange = useCallback((tab: TabType) => {
    setActiveTab(tab)
  }, [])

  const renderPage = () => {
    // Use conditional rendering instead of switch for safer unmounting
    if (activeTab === "market") return <MarketPage key="market" />
    if (activeTab === "gifts") return <GiftsPage key="gifts" />
    if (activeTab === "seasons") return <SeasonsPage key="seasons" />
    if (activeTab === "partners") return <PartnersPage key="partners" />
    if (activeTab === "profile") return <ProfilePage key="profile" />
    return <MarketPage key="market-default" />
  }

  if (!mounted) {
    return (
      <div className="h-[100dvh] bg-background flex items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    )
  }

  return (
    <div className="h-[100dvh] bg-background text-foreground flex flex-col overflow-hidden">
      <Header />
      <main className="flex-1 overflow-y-auto pb-24 hide-scrollbar">
        <div key={activeTab} className="min-h-full">{renderPage()}</div>
      </main>
      <BottomNav activeTab={activeTab} setActiveTab={handleTabChange} />
      <AuthModal />
      <AccessDeniedModal />
    </div>
  )
}

export default function Home() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ErrorBoundary>
  )
}
