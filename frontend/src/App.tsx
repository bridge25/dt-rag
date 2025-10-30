import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-surface flex flex-col items-center justify-center">
      <div className="flex gap-8 mb-8">
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="h-24 hover:filter hover:drop-shadow-lg transition" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="h-24 hover:filter hover:drop-shadow-lg transition" alt="React logo" />
        </a>
      </div>
      <h1 className="text-4xl font-bold mb-8 text-primary">Vite + React + Tailwind</h1>
      <div className="bg-white p-8 rounded-lg shadow-lg border border-border">
        <button
          onClick={() => setCount((count) => count + 1)}
          className="bg-primary hover:bg-primary-dark text-white font-semibold py-2 px-4 rounded transition"
        >
          count is {count}
        </button>
        <p className="mt-4 text-gray-600">
          Edit <code className="bg-gray-100 px-2 py-1 rounded">src/App.tsx</code> and save to test HMR
        </p>
      </div>
      <p className="mt-8 text-gray-500">
        Click on the Vite and React logos to learn more
      </p>
    </div>
  )
}

export default App
