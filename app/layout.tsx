import type React from "react"
import type { Metadata, Viewport } from "next"
import { Inter } from "next/font/google"
import Script from "next/script"
import "./globals.css"

const inter = Inter({ subsets: ["latin", "cyrillic"] })

export const metadata: Metadata = {
  title: "Market - Telegram Web App",
  description: "NFT Marketplace для Telegram",
  generator: "v0.app",
  icons: {
    icon: [
      {
        url: "/icon-light-32x32.png",
        media: "(prefers-color-scheme: light)",
      },
      {
        url: "/icon-dark-32x32.png",
        media: "(prefers-color-scheme: dark)",
      },
      {
        url: "/icon.svg",
        type: "image/svg+xml",
      },
    ],
    apple: "/apple-icon.png",
  },
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#0a0a0f",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <head>
        <Script 
          src="https://telegram.org/js/telegram-web-app.js" 
          strategy="beforeInteractive"
        />
        {/* Suppress React DevTools warnings in development */}
        {process.env.NODE_ENV === "development" && (
          <Script
            id="suppress-react-errors"
            strategy="beforeInteractive"
            dangerouslySetInnerHTML={{
              __html: `
                // Suppress removeChild errors from React DevTools
                const originalRemoveChild = Node.prototype.removeChild;
                Node.prototype.removeChild = function(child) {
                  try {
                    return originalRemoveChild.call(this, child);
                  } catch (e) {
                    if (e.name === 'NotFoundError' && e.message.includes('removeChild')) {
                      console.warn('Suppressed removeChild error:', e);
                      return child;
                    }
                    throw e;
                  }
                };
              `,
            }}
          />
        )}
      </head>
      <body className={`${inter.className} antialiased`} suppressHydrationWarning>
        {children}
      </body>
    </html>
  )
}
