/**
 * Ethereal Glass Design System Utilities
 * Centralized constants and helper functions for glass morphism effects
 *
 * @CODE:ETHEREAL-GLASS-UTILS-001
 */

/**
 * Color Palette - Ethereal Glass Theme
 */
export const EtherealColors = {
  space: {
    DEFAULT: "#0b1121",
    light: "#0f172a",
  },
  neon: {
    cyan: "#00f7ff",
    blue: "#00f3ff",
    purple: "#bc13fe",
    gold: "#ffd700",
    green: "#0aff0a",
  },
  glass: {
    surface: "rgba(30, 41, 59, 0.4)",
    border: "rgba(255, 255, 255, 0.1)",
    highlight: "rgba(255, 255, 255, 0.15)",
  },
  glow: {
    common: "rgba(156, 163, 175, 0.3)",
    rare: "rgba(0, 247, 255, 0.4)",
    epic: "rgba(188, 19, 254, 0.4)",
    legendary: "rgba(255, 215, 0, 0.5)",
  },
}

/**
 * Shadow Definitions - Ethereal Glow Effects
 */
export const EtherealShadows = {
  "ethereal-sm": "0 0 10px rgba(0, 247, 255, 0.15)",
  "ethereal-md": "0 0 20px rgba(0, 247, 255, 0.25)",
  "ethereal-lg": "0 0 40px rgba(0, 247, 255, 0.35)",
  "ethereal-gold": "0 0 30px rgba(255, 215, 0, 0.4)",
  "ethereal-purple": "0 0 25px rgba(188, 19, 254, 0.3)",
}

/**
 * Animation Durations and Timings
 */
export const EtherealAnimations = {
  duration: {
    fast: "200ms",
    normal: "300ms",
    slow: "400ms",
  },
  timing: {
    easeIn: "ease-in-out",
    easeOut: "ease-out",
    linear: "linear",
  },
  keyframes: {
    glowPulse: "2s ease-in-out infinite",
    energyBeam: "2s linear infinite",
    float: "6s ease-in-out infinite",
  },
}

/**
 * Rarity Types and Classifications
 */
export type Rarity = "common" | "rare" | "epic" | "legendary"

export const RarityConfig: Record<Rarity, {
  className: string
  color: string
  shadowClass: string
}> = {
  common: {
    className: "rarity-common",
    color: "#9ca3af",
    shadowClass: "shadow-gray-500/20",
  },
  rare: {
    className: "rarity-rare",
    color: "#00f7ff",
    shadowClass: "shadow-ethereal-sm",
  },
  epic: {
    className: "rarity-epic",
    color: "#bc13fe",
    shadowClass: "shadow-ethereal-purple",
  },
  legendary: {
    className: "rarity-legendary",
    color: "#ffd700",
    shadowClass: "shadow-ethereal-gold",
  },
}

/**
 * Glass Morphism Utility Classes
 */
export const GlassClasses = {
  card: "bg-glass-surface backdrop-blur-xl border border-glass-border rounded-2xl transition-all duration-300",
  cardHover: "hover:border-ethereal-cyan/30 hover:-translate-y-1 hover:shadow-[0_8px_32px_rgba(0,247,255,0.15)]",
  button: "glow-button relative transition-all duration-300 font-medium rounded-lg border border-white/20 text-white",
  buttonHover: "hover:brightness-110 active:brightness-90",
  panel: "bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl shadow-[0_8px_32px_rgba(0,0,0,0.3)]",
  node: "rounded-full bg-gradient-to-br from-white/20 to-white/5 border border-white/20 backdrop-blur-lg transition-all duration-300",
  nodeHover: "hover:border-cyan-400/50 hover:shadow-[0_0_40px_rgba(56,189,248,0.4)] hover:scale-110",
}

/**
 * Helper function to get rarity-specific styling
 */
export function getRarityStyle(rarity: Rarity) {
  return RarityConfig[rarity]
}

/**
 * Helper function to combine glass classes
 */
export function mergeGlassClasses(...classes: (string | undefined)[]): string {
  return classes.filter(Boolean).join(" ")
}

/**
 * CSS Variable setters for dynamic glow colors
 */
export function getGlowCSSVariable(rarity: Rarity): Record<string, string> {
  return {
    "--glow-color": RarityConfig[rarity].color,
  }
}
