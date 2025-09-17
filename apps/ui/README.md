# Dynamic Taxonomy RAG Frontend v1.8.1

A high-performance, accessible React/TypeScript frontend for the Dynamic Taxonomy RAG system, featuring advanced tree visualization, document search, and human-in-the-loop classification management.

## 🚀 Features

### Core Features
- **Tree Visualization**: Virtual scrolling tree component with 10,000+ node support
- **Advanced Search**: Hybrid BM25 + Vector search with real-time results
- **HITL Queue**: Human-in-the-loop classification review and approval workflow
- **Version Management**: Taxonomy version comparison and rollback functionality
- **Real-time Updates**: WebSocket-based live data synchronization

### Performance
- **Virtual Scrolling**: Handles large datasets with p95 < 200ms rendering
- **60 FPS**: Smooth animations and interactions
- **Memory Optimized**: < 100MB memory usage for large tree structures
- **Responsive**: Mobile-first design with cross-browser compatibility

### Accessibility
- **WCAG 2.1 AAA**: Complete accessibility compliance
- **Keyboard Navigation**: Full keyboard support with logical focus management
- **Screen Reader**: Comprehensive ARIA labels and live regions
- **High Contrast**: Support for high contrast and reduced motion preferences

## 🛠 Technology Stack

### Frontend Framework
- **Next.js 14**: App Router with React Server Components
- **React 18**: Concurrent features and Suspense
- **TypeScript 5**: Advanced type safety and patterns

### State Management
- **Zustand**: Lightweight state management with persistence
- **TanStack Query**: Server state management and caching
- **TanStack Virtual**: High-performance virtual scrolling

### UI/UX
- **Tailwind CSS**: Utility-first styling with custom design system
- **Framer Motion**: Smooth animations and transitions
- **Radix UI**: Accessible primitive components
- **Lucide React**: Modern icon system

### Performance
- **Virtual Scrolling**: TanStack Virtual for large datasets
- **Code Splitting**: Dynamic imports and lazy loading
- **Memoization**: React.memo and useMemo optimization
- **Bundle Analysis**: Webpack Bundle Analyzer integration

## 📦 Installation

### Prerequisites
- Node.js 18+
- npm/yarn/pnpm
- Backend API running on port 8000

### Setup
```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

### Environment Variables
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

## 🏗 Architecture

### Project Structure
```
src/
├── app/                    # Next.js app router pages
├── components/             # React components
│   ├── tree/              # Tree visualization components
│   ├── search/            # Search interface components
│   ├── hitl/              # Human-in-the-loop components
│   ├── layout/            # Layout and navigation
│   └── ui/                # Base UI components
├── stores/                # Zustand state stores
├── types/                 # TypeScript type definitions
├── lib/                   # Utility functions
└── providers/             # React context providers
```

### Component Architecture
- **TreePanel**: Main tree visualization with virtual scrolling
- **SearchInterface**: Comprehensive search with filters and facets
- **HITLQueue**: Classification review and batch operations
- **AppLayout**: Responsive layout with navigation

### State Management
- **Taxonomy Store**: Tree data, expansion state, selection
- **Search Store**: Query state, results, filters, saved searches
- **Performance Store**: Metrics and optimization data

## 🎯 Key Components

### TreePanel
```typescript
<TreePanel
  className="min-h-[600px]"
  showVersionDropdown={true}
  showMetrics={true}
  showFilters={true}
  maxHeight={800}
/>
```

**Features:**
- Virtual scrolling for 10,000+ nodes
- Keyboard navigation (WASD, arrows, home/end)
- Search and filtering with real-time updates
- Version comparison and diff visualization
- Performance metrics and optimization

### SearchInterface
```typescript
<SearchInterface
  onResultSelect={handleResultSelect}
  autoFocus={true}
  showFilters={true}
  showSavedSearches={true}
/>
```

**Features:**
- Hybrid search (BM25 + Vector similarity)
- Real-time suggestions and autocomplete
- Advanced filtering and faceting
- Saved searches and search history
- Result highlighting and export

### HITLQueue
```typescript
<HITLQueue
  queueItems={queueItems}
  onApprove={handleApprove}
  onReject={handleReject}
  onBatchOperation={handleBatchOperation}
/>
```

**Features:**
- Classification review workflow
- Batch approval/rejection operations
- Inline editing and corrections
- Confidence-based filtering
- Reviewer assignment and tracking

## 🔧 Performance Optimization

### Virtual Scrolling
- **TanStack Virtual**: High-performance windowing
- **Dynamic Heights**: Automatic size calculation
- **Overscan**: Configurable buffer for smooth scrolling
- **Memory Management**: Automatic cleanup and garbage collection

### Rendering Optimization
- **React.memo**: Component memoization
- **useMemo/useCallback**: Hook optimization
- **Code Splitting**: Dynamic imports for large components
- **Bundle Analysis**: Webpack optimization

### State Management
- **Zustand**: Minimal re-renders
- **Selectors**: Granular subscriptions
- **Persistence**: Local storage integration
- **DevTools**: Redux DevTools integration

## ♿ Accessibility Features

### WCAG 2.1 AAA Compliance
- **Keyboard Navigation**: Complete keyboard support
- **Screen Readers**: Comprehensive ARIA implementation
- **Focus Management**: Logical focus flow
- **Color Contrast**: AAA contrast ratios
- **Text Scaling**: Support for 200% zoom

### Keyboard Shortcuts
- **Navigation**: Arrow keys, Home/End, Tab
- **Tree Operations**: Enter/Space (expand), Ctrl+E (expand all)
- **Search**: Ctrl+F (focus search), Escape (clear)
- **HITL**: A (approve), R (reject), E (edit)

### Screen Reader Support
- **Live Regions**: Dynamic content announcements
- **Role Attributes**: Semantic HTML roles
- **Landmarks**: Navigation landmarks
- **Descriptions**: Detailed element descriptions

## 📊 Performance Metrics

### Target Performance
- **Rendering**: p95 < 200ms for 10,000+ nodes
- **Frame Rate**: 60 FPS during interactions
- **Memory Usage**: < 100MB for large datasets
- **Load Time**: < 3s initial page load
- **Bundle Size**: < 1MB gzipped

### Monitoring
- **Core Web Vitals**: LCP, FID, CLS tracking
- **Performance API**: Custom metrics collection
- **Error Tracking**: Comprehensive error monitoring
- **User Analytics**: Usage pattern analysis

## 🧪 Testing

### Test Coverage
```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run e2e tests
npm run test:e2e
```

### Testing Strategy
- **Unit Tests**: Component testing with React Testing Library
- **Integration Tests**: Store and API integration
- **E2E Tests**: Full user workflow testing
- **Accessibility Tests**: Automated a11y testing

## 🚀 Deployment

### Production Build
```bash
# Build optimized bundle
npm run build

# Analyze bundle size
npm run analyze

# Start production server
npm start
```

### Docker Support
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3001
CMD ["npm", "start"]
```

### Environment Configuration
- **Development**: Hot reload, source maps, DevTools
- **Staging**: Production build, error tracking
- **Production**: Optimized bundle, CDN integration

## 📚 Documentation

### API Integration
- **REST API**: Complete endpoint documentation
- **WebSocket**: Real-time data subscription
- **Authentication**: JWT token management
- **Error Handling**: Comprehensive error responses

### Component Library
- **Storybook**: Interactive component documentation
- **Type Definitions**: Complete TypeScript coverage
- **Usage Examples**: Implementation guides
- **Best Practices**: Performance and accessibility guidelines

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

### Code Standards
- **TypeScript**: Strict mode enabled
- **ESLint**: Airbnb configuration
- **Prettier**: Consistent formatting
- **Husky**: Pre-commit hooks

### Review Process
- **Code Review**: Required for all PRs
- **Testing**: 100% test coverage for new features
- **Accessibility**: WCAG 2.1 compliance verification
- **Performance**: Lighthouse score > 90

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 📞 Support

- **Documentation**: [docs.dt-rag.com](https://docs.dt-rag.com)
- **Issues**: [GitHub Issues](https://github.com/dt-rag/frontend/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dt-rag/frontend/discussions)
- **Email**: frontend-team@dt-rag.com

---

**Dynamic Taxonomy RAG Frontend v1.8.1** - Built with ❤️ for high-performance document classification and search.