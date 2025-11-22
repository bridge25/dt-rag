/**
 * Utility function to merge CSS class names with Tailwind CSS support
 *
 * @CODE:FRONTEND-001
 */

import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
