import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getTask13, gradeTask13 } from '../api/client'
import type { Task13CircleDiagram, Task13View } from '../api/types'
import { ApiError } from '../api/types'
import { AssistantPanel } from '../components/AssistantPanel'
import { FormulaField } from '../components/FormulaField'
import { TaskCondition } from '../components/TaskCondition'
import { UnitCircleEditor } from '../components/UnitCircleEditor'
import { validateTask13Submission } from '../utils/validation'

export function SolvePage() {
  const { taskId = '' } = useParams()
  const navigate = useNavigate()
  const [task, setTask] = useState<Task13View | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [solutionPartA, setSolutionPartA] = useState('')
  const [answerPartB, setAnswerPartB] = useState('')
  const [circleDiagram, setCircleDiagram] = useState<Task13CircleDiagram>({})
  const [circleOpen, setCircleOpen] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    getTask13(taskId)
      .then((loaded) => {
        if (!cancelled) {
          setTask(loaded)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Задание не найдено')
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

  const hasCircleData = useMemo(() => {
    return (circleDiagram.points?.length ?? 0) > 0 || (circleDiagram.arcs?.length ?? 0) > 0
  }, [circleDiagram])

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)

    const validationErrors = validateTask13Submission(solutionPartA, answerPartB)
    if (validationErrors.length > 0) {
      setFieldErrors(Object.fromEntries(validationErrors.map((item) => [item.field, item.message])))
      return
    }
    setFieldErrors({})

    setSubmitting(true)
    try {
      const result = await gradeTask13(taskId, {
        solution_part_a: solutionPartA.trim(),
        answer_part_b: answerPartB.trim(),
        circle_diagram: hasCircleData ? circleDiagram : null,
      })
      const attemptId = result.attempt_id
      if (!attemptId) {
        throw new Error('Сервер не вернул идентификатор попытки')
      }
      navigate(`/result/${attemptId}`, { state: { grade: result, taskId } })
    } catch (err) {
      if (err instanceof ApiError && err.code === 'validation_error' && err.field) {
        setFieldErrors({ [err.field]: err.message })
      } else {
        setError(err instanceof ApiError ? err.message : 'Не удалось отправить решение')
      }
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return <p className="page-status">Загрузка задания…</p>
  }

  if (error && !task) {
    return (
      <section className="page">
        <p className="alert alert-error">{error}</p>
        <Link to="/" className="btn btn-secondary">
          На главную
        </Link>
      </section>
    )
  }

  if (!task) {
    return null
  }

  return (
    <div className="solve-layout">
      <section className="page blank-sheet">
        <header className="blank-sheet__header">
          <p>Бланк ответов № 2 · ЕГЭ по математике (профиль)</p>
          <h1>Задание 13</h1>
        </header>

        <article className="blank-sheet__condition">
          <h2 className="blank-sheet__section-title">Условие</h2>
          <TaskCondition task={task} />
        </article>

        <form className="blank-sheet__form" onSubmit={handleSubmit}>
          <section className="answer-section" aria-labelledby="answer-part-a-title">
            <div className="answer-section__header">
              <h3 id="answer-part-a-title" className="answer-section__title">
                <span className="answer-section__marker">а)</span> Решение
              </h3>
              <p className="answer-section__hint">
                Запишите ход решения: преобразования, замены, все серии корней с параметром k ∈ ℤ.
              </p>
            </div>
            <FormulaField
              id="solution-part-a"
              value={solutionPartA}
              onChange={setSolutionPartA}
              multiline
              maxLength={16000}
              ariaLabel="Решение пункта а"
              placeholder={'Например: замена t = sin x, …\nx = −π/2 + 2πk, k ∈ Z;\nx = π/6 + 2πn, n ∈ Z'}
              error={fieldErrors.solution_part_a}
            />
          </section>

          <section className="answer-section" aria-labelledby="answer-part-b-title">
            <div className="answer-section__header">
              <h3 id="answer-part-b-title" className="answer-section__title">
                <span className="answer-section__marker">б)</span> Ответ
              </h3>
              <p className="answer-section__hint">
                Только корни на отрезке {task.interval_display ?? 'из условия'}. Точные значения в радианах,
                через «;» или в фигурных скобках.
              </p>
            </div>
            <FormulaField
              id="answer-part-b"
              value={answerPartB}
              onChange={setAnswerPartB}
              maxLength={512}
              ariaLabel="Ответ пункта б"
              placeholder="−π/2; π/6"
              error={fieldErrors.answer_part_b}
            />
          </section>

          <details className="collapsible" open={circleOpen} onToggle={(event) => setCircleOpen(event.currentTarget.open)}>
            <summary>Рисунок на окружности (необязательно)</summary>
            <p className="muted">Рисунок не обязателен и не влияет на балл (MVP).</p>
            <UnitCircleEditor value={circleDiagram} onChange={setCircleDiagram} />
          </details>

          {error && <p className="alert alert-error">{error}</p>}

          <div className="form-actions">
            <Link to="/" className="btn btn-secondary">
              Другой вариант
            </Link>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Проверка…' : 'Отправить на проверку'}
            </button>
          </div>
        </form>
      </section>

      <AssistantPanel taskId={taskId} draftPartA={solutionPartA} draftPartB={answerPartB} />
    </div>
  )
}
