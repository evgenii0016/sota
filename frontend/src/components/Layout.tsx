import { Link, Outlet } from 'react-router-dom'

export function Layout() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/" className="app-logo">
          ЕГЭ · Задание 13
        </Link>
        <p className="app-tagline">Тригонометрические уравнения</p>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}
