"use client"

/**
 * Language Switcher Component
 * Allows users to switch between English and Korean
 *
 * @CODE:FRONTEND-REDESIGN-001-I18N
 */

import { useState, useRef, useEffect } from "react"
import { Globe, Check, ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"
import {
  useTranslation,
  LANGUAGE_NAMES,
  LANGUAGE_FLAGS,
  type Language,
} from "@/lib/i18n"

interface LanguageSwitcherProps {
  className?: string
  variant?: "default" | "compact"
}

const LANGUAGES: Language[] = ["en", "ko"]

export function LanguageSwitcher({
  className,
  variant = "default",
}: LanguageSwitcherProps) {
  const { language, setLanguage, t } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const handleSelect = (lang: Language) => {
    setLanguage(lang)
    setIsOpen(false)
  }

  if (variant === "compact") {
    return (
      <div ref={dropdownRef} className={cn("relative", className)}>
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className={cn(
            "flex items-center justify-center gap-1.5 px-2 py-1.5",
            "bg-white/5 border border-white/10 rounded-lg",
            "text-sm text-white/70",
            "transition-all duration-200",
            "hover:bg-white/10 hover:border-cyan-400/30",
            isOpen && "border-cyan-400/50"
          )}
        >
          <span className="text-base">{LANGUAGE_FLAGS[language]}</span>
          <ChevronDown
            className={cn(
              "w-3 h-3 transition-transform duration-200",
              isOpen && "rotate-180"
            )}
          />
        </button>

        {isOpen && (
          <div
            className={cn(
              "absolute bottom-full mb-2 left-0 z-50",
              "w-32",
              "bg-slate-900/95 backdrop-blur-xl",
              "border border-white/10 rounded-lg",
              "shadow-[0_4px_16px_rgba(0,0,0,0.3)]",
              "overflow-hidden",
              "animate-in fade-in slide-in-from-bottom-2 duration-200"
            )}
          >
            {LANGUAGES.map((lang) => (
              <button
                key={lang}
                type="button"
                onClick={() => handleSelect(lang)}
                className={cn(
                  "w-full flex items-center gap-2 px-3 py-2",
                  "text-sm text-left",
                  "hover:bg-white/5 transition-colors",
                  language === lang && "bg-cyan-500/10 text-cyan-300"
                )}
              >
                <span>{LANGUAGE_FLAGS[lang]}</span>
                <span className="flex-1">{LANGUAGE_NAMES[lang]}</span>
                {language === lang && (
                  <Check className="w-4 h-4 text-cyan-400" />
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div ref={dropdownRef} className={cn("relative", className)}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center gap-2 px-3 py-2 w-full",
          "bg-white/5 border border-white/10 rounded-xl",
          "text-sm text-white/70",
          "transition-all duration-200",
          "hover:bg-white/10 hover:border-cyan-400/30",
          isOpen && "border-cyan-400/50"
        )}
      >
        <Globe className="w-4 h-4 text-cyan-400" />
        <span className="flex-1 text-left">
          {LANGUAGE_FLAGS[language]} {LANGUAGE_NAMES[language]}
        </span>
        <ChevronDown
          className={cn(
            "w-4 h-4 transition-transform duration-200",
            isOpen && "rotate-180"
          )}
        />
      </button>

      {isOpen && (
        <div
          className={cn(
            "absolute bottom-full mb-2 left-0 right-0 z-50",
            "bg-slate-900/95 backdrop-blur-xl",
            "border border-white/10 rounded-xl",
            "shadow-[0_8px_32px_rgba(0,0,0,0.4)]",
            "overflow-hidden",
            "animate-in fade-in slide-in-from-bottom-2 duration-200"
          )}
        >
          <div className="px-3 py-2 border-b border-white/5">
            <span className="text-xs font-medium text-white/40 uppercase tracking-wider">
              {t("common.language")}
            </span>
          </div>
          {LANGUAGES.map((lang) => (
            <button
              key={lang}
              type="button"
              onClick={() => handleSelect(lang)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5",
                "text-sm text-left",
                "hover:bg-white/5 transition-colors",
                language === lang && "bg-cyan-500/10"
              )}
            >
              <span className="text-lg">{LANGUAGE_FLAGS[lang]}</span>
              <span
                className={cn(
                  "flex-1",
                  language === lang ? "text-cyan-300" : "text-white/70"
                )}
              >
                {LANGUAGE_NAMES[lang]}
              </span>
              {language === lang && (
                <Check className="w-4 h-4 text-cyan-400" />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
