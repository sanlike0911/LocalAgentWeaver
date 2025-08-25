import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Header from '@/components/Header'
import { ThemeProvider } from '@/components/ThemeProvider'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'LocalAgentWeaver',
  description: 'AI Agent Platform for Local LLM Integration',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body
        className={`${inter.className} min-h-screen bg-background text-foreground`}
      >
        <ThemeProvider>
          <Header />
          <main
            id="main"
            className="min-h-[calc(100vh-56px)] focus:outline-none"
          >
            {children}
          </main>
        </ThemeProvider>
      </body>
    </html>
  )
}