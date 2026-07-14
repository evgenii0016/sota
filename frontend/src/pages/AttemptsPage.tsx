import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getTaskAttempts } from '../api/client'
import type { Task13AttemptView, Task13Score } from '../api/types'
import { ApiError } from '../api/types'
import { scoreLabel } from '../utils/gradeDisplay'

function formatAttemptTime(value?: string | null): string {
  if (!value) {
    return 'Время неизвестно'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function attemptScore(attempt: Task13AttemptView): Task13Score | null {
  return attempt.score ?? null
}

export function AttemptsPage() {
  const { taskId = '' } = useParams()
  const [attempts, setAttempts] = useState<Task13AttemptView[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    getTaskAttempts(taskId)
      .then((items) => {
        if (!cancelled) {
          setAttempts(items)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Не удалось загрузить историю решений.')
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [taskId])

  if (loading) {
    return <p className="page-status">Загрузка истории решений…</p>
  }

  if (error) {
    return (
      <section className="page">
        <h1>История решений</h1>
        <p className="alert alert-error">{error}</p>
        <Link to="/" className="btn btn-primary">
          На главную
        </Link>
      </section>
    )
  }

  return (
    <section className="page">
      <h1>История решений</h1>
      <p className="page-lead">Выберите попытку, чтобы посмотреть результат и комментарии проверяющего.</p>

      {attempts.length === 0 ? (
        <p className="muted">Для этого варианта ещё нет отправленных решений.</p>
      ) : (
        <ol className="attempt-history">
          {attempts.map((attempt, index) => {
            const score = attemptScore(attempt)
            return (
              <li key={attempt.id} className={score === null ? 'attempt-history__item' : `attempt-history__item attempt-history__item--score-${score}`}>
                <div>
                  <p className="attempt-history__title">Попытка {index + 1}</p>
                  <p className="attempt-history__meta">{formatAttemptTime(attempt.created_at)}</p>
                </div>
                <div className="attempt-history__actions">
                  {score !== null && <span className="attempt-history__score">{scoreLabel(score)}</span>}
                  <Link to={`/result/${attempt.id}`} className="btn btn-secondary btn-sm">
                    Открыть результат
                  </Link>
                </div>
              </li>
            )
          })}
        </ol>
      )}

      <div className="form-actions">
        <Link to={`/solve/${taskId}`} className="btn btn-secondary">
          Решить снова
        </Link>
        <Link to="/" className="btn btn-primary">
          На главную
        </Link>
      </div>
    </section>
  )
}
