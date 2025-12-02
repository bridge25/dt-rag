/**
 * Clean Architecture - Main Entry Point
 *
 * This module exports all layers of the clean architecture:
 *
 * ## Architecture Overview
 *
 * ```
 * ┌─────────────────────────────────────────────────────────┐
 * │                   Presentation Layer                    │
 * │  (React Components, Hooks, Stores)                      │
 * │                         ↓                               │
 * ├─────────────────────────────────────────────────────────┤
 * │                    Domain Layer                         │
 * │  (Entities, Use Cases, Repository Interfaces)          │
 * │                         ↓                               │
 * ├─────────────────────────────────────────────────────────┤
 * │                     Data Layer                          │
 * │  (Repository Impl, Data Sources, Mappers)              │
 * └─────────────────────────────────────────────────────────┘
 * ```
 *
 * ## Key Principles
 *
 * 1. **Dependency Rule**: Dependencies point inward only
 *    - Presentation → Domain → Data
 *    - Domain knows nothing about Presentation or Data implementation
 *
 * 2. **Separation of Concerns**:
 *    - Domain: Business logic (pure, framework-agnostic)
 *    - Data: External communication (API, storage)
 *    - Presentation: UI logic (React-specific)
 *
 * 3. **Testability**:
 *    - Each layer can be tested independently
 *    - Mock implementations for repositories
 *
 * @CODE:CLEAN-ARCHITECTURE-MAIN
 */

// Domain Layer (innermost)
export * from './domain';

// Data Layer (implements domain interfaces)
export * from './data';

// Presentation Layer (uses domain through use cases)
export * from './presentation';

// Shared utilities and configuration
export * from './shared';
