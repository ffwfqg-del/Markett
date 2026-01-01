"use client"

import { useEffect, useState } from "react"

interface SplashScreenProps {
  onFinish: () => void
}

export function SplashScreen({ onFinish }: SplashScreenProps) {
  const [isVisible, setIsVisible] = useState(true)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    
    // Simple timeout - show for 1.5 seconds then fade out
    const timer = setTimeout(() => {
      setIsVisible(false)
      // Give time for fade out animation
      setTimeout(() => onFinish(), 300)
    }, 1500)

    return () => {
      clearTimeout(timer)
    }
  }, [onFinish])

  if (!mounted || !isVisible) {
    return null
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-background">
      {/* Animated background gradient */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-gradient-to-r from-pink-600/30 via-purple-600/30 to-blue-600/30 blur-[120px] animate-pulse" />
      </div>

      {/* Logo */}
      <div className="relative flex flex-col items-center">
        {/* MARKET text with gradient */}
        <h1 className="text-5xl sm:text-6xl font-black tracking-tight">
          <span className="bg-gradient-to-r from-pink-500 via-rose-400 to-pink-500 bg-clip-text text-transparent">
            MAR
          </span>
          <span className="bg-gradient-to-r from-blue-400 via-cyan-400 to-blue-400 bg-clip-text text-transparent">
            KET
          </span>
        </h1>

        {/* Simple loading indicator */}
        <div className="mt-6 text-sm text-muted-foreground">
          Loading...
        </div>
      </div>
    </div>
  )
}
