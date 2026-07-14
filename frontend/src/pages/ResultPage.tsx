import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { getAttempt } from '../api/client'
import type { Task13GradeResponse } from '../api/types'
import { ApiError, attemptToGrade } from '../api/types'
import { SCORE_CRITERIA, scoreLabel } from '../utils/gradeDisplay'
import { SECTION_LABELS } from '../utils/sectionLabels'
import { saveTaskResult } from '../utils/taskBatchStorage'

interface ResultLocationState {
  grade?: Task13GradeResponse
  taskId?: string
}

export function ResultPage() {
  const { attemptId = '' } = useParams()
  const location = useLocation()
  const state = (location.state ?? {}) as ResultLocationState
  const [grade, setGrade] = useState<Task13GradeResponse | null>(state.grade ?? null)
  const [taskId, setTaskId] = useState<string | undefined>(state.taskId)
  const [loading, setLoading] = useState(!state.grade)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (state.grade) {
      setGrade(state.grade)
      setTaskId(state.taskId)
      if (state.taskId) {
        saveTaskResult(state.taskId, {
          score: state.grade.score,
          attemptId: state.grade.attempt_id ?? attemptId,
        })
      }
      setLoading(false)
      return
    }

    let cancelled = false
    setLoading(true)
    setError(null)

    getAttempt(attemptId)
      .then((attempt) => {
        if (cancelled) {
          return
        }
        const mapped = attemptToGrade(attempt)
        if (!mapped) {
          setError('Результат проверки недоступен для этого типа задания.')
          return
        }
        setGrade(mapped)
        setTaskId(attempt.task_id)
        saveTaskResult(attempt.task_id, {
          score: mapped.score,
          attemptId: attempt.id,
        })
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Не удалось загрузить результат.')
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
  }, [attemptId, state.grade, state.taskId])

  if (loading) {
    return <p className="page-status">Загрузка результата…</p>
  }

  if (error || !grade) {
    return (
      <section className="page">
        <h1>Результат проверки</h1>
        <p className="alert alert-error">{error ?? 'Данные оценки недоступны.'}</p>
        <p className="muted">Попытка: {attemptId}</p>
        <Link to="/" className="btn btn-primary">
          На главную
        </Link>
      </section>
    )
  }

  return (
    <section className="page">
      <h1>Результат проверки</h1>
      <p className={`score score--${grade.score}`}>{scoreLabel(grade.score)}</p>
      <p className="score-criteria">{SCORE_CRITERIA[grade.score]}</p>

      <ul className="score-details">
        <li>Пункт а: {grade.part_a_correct ? 'верно' : 'ошибка'}</li>
        <li>Пункт б: {grade.part_b_correct ? 'верно' : 'ошибка'}</li>
        <li>Обоснованность: {grade.justified ? 'да' : 'нет'}</li>
        {(grade.justified_part_a != null || grade.justified_part_b != null) && (
          <li>
            Детали: а — {grade.justified_part_a ? 'обоснован' : 'не обоснован'};
            б — {grade.justified_part_b ? 'обоснован' : 'не обоснован'}
          </li>
        )}
      </ul>

      {grade.method_errors && grade.method_errors.length > 0 && (
        <section className="method-errors">
          <h2>Методические ошибки</h2>
          <ul>
            {grade.method_errors.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      )}

      {grade.comments.length > 0 && (
        <section className="comments">
          <h2>Замечания</h2>
          <ul>
            {grade.comments.map((comment, index) => (
              <li key={`${comment.section}-${index}`} className={comment.ok ? 'ok' : 'fail'}>
                <strong>{SECTION_LABELS[comment.section] ?? comment.section}</strong>
                {comment.text && <span>{comment.text}</span>}
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="form-actions">
        {taskId && (
          <Link to={`/solve/${taskId}`} className="btn btn-secondary">
            Попробовать снова
          </Link>
        )}
        {taskId && (
          <Link to={`/tasks/${taskId}/attempts`} className="btn btn-secondary">
            История решений
          </Link>
        )}
        <Link to="/" className="btn btn-primary">
          Другой вариант
        </Link>
      </div>
    </section>
  )
}
