import { useState } from 'react'
import { InvestigationDashboard } from './components/InvestigationDashboard'
import { InvestigationDetail } from './components/InvestigationDetail'
import { Header } from './components/Header'

type AppView = 'dashboard' | 'detail'

export default function App() {
  const [currentView, setCurrentView] = useState<AppView>('dashboard')
  const [investigationId, setInvestigationId] = useState<string | null>(null)

  const handleInvestigationCreated = (id: string) => {
    setInvestigationId(id)
    setCurrentView('detail')
  }

  const handleBackToDashboard = () => {
    setCurrentView('dashboard')
    setInvestigationId(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <Header />
      <main className="container mx-auto px-4 py-8">
        {currentView === 'dashboard' ? (
          <InvestigationDashboard onInvestigationCreated={handleInvestigationCreated} />
        ) : investigationId ? (
          <InvestigationDetail
            investigationId={investigationId}
            onBack={handleBackToDashboard}
          />
        ) : null}
      </main>
    </div>
  )
}
