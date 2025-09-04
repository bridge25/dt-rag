import { AppLayout } from '@/components/layout/AppLayout'

export default function TestingPage() {
  return (
    <AppLayout currentPage="testing">
      <div className="p-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-12">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Testing Suite</h1>
            <p className="text-gray-600 mb-8">테스트 및 검증 도구</p>
            <div className="bg-yellow-100 border border-yellow-300 rounded-lg p-4">
              <p className="text-yellow-700">🚧 구현 대기중: 4개의 스모크 테스트 실행</p>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}