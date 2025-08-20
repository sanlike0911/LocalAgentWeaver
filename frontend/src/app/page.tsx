export default function Home() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-800 mb-4">
          LocalAgentWeaver
        </h1>
        <p className="text-gray-600 mb-8">
          AI Agent Platform for Local LLM Integration
        </p>
        <div className="space-y-4">
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
            ✅ Frontend is running successfully!
          </div>
          <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded">
            🚀 Backend API: <a href="http://localhost:8000/docs" className="underline">http://localhost:8000/docs</a>
          </div>
        </div>
      </div>
    </div>
  )
}