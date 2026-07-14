import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { AttemptsPage } from './pages/AttemptsPage'
import { HomePage } from './pages/HomePage'
import { ResultPage } from './pages/ResultPage'
import { SolvePage } from './pages/SolvePage'
import './styles/global.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="solve/:taskId" element={<SolvePage />} />
          <Route path="result/:attemptId" element={<ResultPage />} />
          <Route path="tasks/:taskId/attempts" element={<AttemptsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
