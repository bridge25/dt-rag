"use client"

/**
 * i18n Context and Provider
 * Lightweight internationalization solution for Norade Frontend
 *
 * @CODE:FRONTEND-REDESIGN-001-I18N
 */

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from "react"

import en from "./translations/en.json"
import ko from "./translations/ko.json"

// Supported languages
export type Language = "en" | "ko"

// Translation dictionaries
const translations: Record<Language, typeof en> = {
  en,
  ko,
}

// Language display names
export const LANGUAGE_NAMES: Record<Language, string> = {
  en: "English",
  ko: "한국어",
}

// Language flags (emoji)
export const LANGUAGE_FLAGS: Record<Language, string> = {
  en: "🇺🇸",
  ko: "🇰🇷",
}

// Context type
interface I18nContextType {
  language: Language
  setLanguage: (lang: Language) => void
  t: (key: string, params?: Record<string, string | number>) => string
}

// Create context
const I18nContext = createContext<I18nContextType | null>(null)

// Storage key
const LANGUAGE_STORAGE_KEY = "norade-language"

// Get nested value from object by dot notation key
function getNestedValue(obj: Record<string, unknown>, key: string): string | undefined {
  const keys = key.split(".")
  let result: unknown = obj

  for (const k of keys) {
    if (result && typeof result === "object" && k in result) {
      result = (result as Record<string, unknown>)[k]
    } else {
      return undefined
    }
  }

  return typeof result === "string" ? result : undefined
}

// Provider props
interface I18nProviderProps {
  children: ReactNode
  defaultLanguage?: Language
}

// Provider component
export function I18nProvider({
  children,
  defaultLanguage = "en",
}: I18nProviderProps) {
  const [language, setLanguageState] = useState<Language>(defaultLanguage)
  const [isClient, setIsClient] = useState(false)

  // Load language from localStorage on mount (client-side only)
  useEffect(() => {
    setIsClient(true)
    const stored = localStorage.getItem(LANGUAGE_STORAGE_KEY) as Language | null
    if (stored && (stored === "en" || stored === "ko")) {
      setLanguageState(stored)
    }
  }, [])

  // Set language and persist to localStorage
  const setLanguage = useCallback((lang: Language) => {
    setLanguageState(lang)
    if (typeof window !== "undefined") {
      localStorage.setItem(LANGUAGE_STORAGE_KEY, lang)
      document.documentElement.lang = lang
    }
  }, [])

  // Translation function - works in SSR with default language
  const t = useCallback(
    (key: string, params?: Record<string, string | number>): string => {
      // Use current language (or default during SSR)
      const currentLang = isClient ? language : defaultLanguage
      const translation = getNestedValue(
        translations[currentLang] as unknown as Record<string, unknown>,
        key
      )

      if (!translation) {
        // Fallback to English
        const fallback = getNestedValue(
          translations.en as unknown as Record<string, unknown>,
          key
        )
        if (!fallback) {
          // Only warn on client to avoid SSR noise
          if (isClient) {
            console.warn(`Missing translation for key: ${key}`)
          }
          return key
        }
        return interpolate(fallback, params)
      }

      return interpolate(translation, params)
    },
    [language, isClient, defaultLanguage]
  )

  // Always render children - use default language during SSR
  return (
    <I18nContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </I18nContext.Provider>
  )
}

// Interpolate params into translation string
function interpolate(
  str: string,
  params?: Record<string, string | number>
): string {
  if (!params) return str
  return str.replace(/\{\{(\w+)\}\}/g, (_, key) => {
    return params[key]?.toString() ?? `{{${key}}}`
  })
}

// Hook to use i18n
export function useTranslation() {
  const context = useContext(I18nContext)
  if (!context) {
    throw new Error("useTranslation must be used within an I18nProvider")
  }
  return context
}

// Hook for just the translation function (shorter alias)
export function useT() {
  const { t } = useTranslation()
  return t
}
