import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Dashboard } from './pages/Dashboard'
import { AuditDetail } from './pages/AuditDetail'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <div className="min-h-screen bg-slate-950 text-slate-50">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/audits/:id" element={<AuditDetail />} />
        </Routes>
      </BrowserRouter>
    </div>
  </StrictMode>,
)
