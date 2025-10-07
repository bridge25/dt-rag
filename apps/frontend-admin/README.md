# DT-RAG Frontend Admin

Frontend admin interface for Dynamic Taxonomy RAG System v1.8.1

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: React 18
- **Tree Visualization**: react-arborist

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Environment Variables

Copy the example environment file and configure your settings:

```bash
cp .env.example .env.local
```

Edit `.env.local` with your configuration:

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8001/api/v1

# API Key (obtain from backend admin)
NEXT_PUBLIC_API_KEY=your-actual-api-key-here
```

**Important**:
- Never commit `.env.local` to Git
- The `.env.local` file is already in `.gitignore`
- Contact your backend team to obtain a valid API key

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

## Build

```bash
npm run build
npm start
```

## Project Structure

```
apps/frontend-admin/
├── app/                    # Next.js App Router pages
│   ├── admin/             # Admin pages (taxonomy, etc.)
│   ├── agent-factory/     # Agent creation
│   ├── chat/              # Chat interface
│   └── dashboard/         # Dashboard
├── src/
│   ├── components/        # Reusable components
│   ├── services/          # API clients
│   ├── hooks/             # Custom React hooks
│   ├── types/             # TypeScript types
│   └── constants/         # Constants
└── public/                # Static assets
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend API base URL |
| `NEXT_PUBLIC_API_KEY` | Yes | API authentication key |
| `NODE_ENV` | No | Environment (development/production) |
