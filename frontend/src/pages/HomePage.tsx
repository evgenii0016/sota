import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { createTask13Batch } from '../api/client'
import type { Task13View } from '../api/types'
import { ApiError } from '../api/types'
import { TaskCondition } from '../components/TaskCondition'
import {
  appendBatchToHistory,
  formatBatchTimestamp,
  loadBatchHistory,
  removeBatchFromHistory,
  type Task13BatchRecord,
  type Task13TaskResult,
} from '../utils/taskBatchStorage'

function TaskGrid({
  tasks,
  results,
}: {
  tasks: Task13View[]
  results: Record<string, Task13TaskResult>
}) {
  return (
    <ul className="task-grid">
      {tasks.map((task, index) => {
        const result = results[task.id]
        const cardClass = result
          ? `task-card task-card--score-${result.score}`
          : 'task-card'
        return (
          <li key={task.id} className={cardClass}>
            <div className="task-card__header">
              <p className="task-card__label">Вариант {index + 1}</p>
              {result ? (
                <span className="task-card__score" aria-label={`Результат: ${result.score} из 2`}>
                  {result.score}/2
                </span>
              ) : (
                <span className="task-card__status">Не решён</span>
              )}
            </div>
            <div className="task-card__body">
              <TaskCondition task={task} compact />
            </div>
            <div className="task-card__actions">
              <Link to={`/solve/${task.id}`} className="btn btn-secondary task-card__action">
                {result ? 'Решить снова' : 'Решать'}
              </Link>
              {result && (
                <Link to={`/tasks/${task.id}/attempts`} className="btn btn-secondary task-card__action">
                  История решений
                </Link>
              )}
            </div>
          </li>
        )
      })}
    </ul>
  )
}

export function HomePage() {
  const [history, setHistory] = useState<Task13BatchRecord[]>(() => loadBatchHistory())
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(() => loadBatchHistory()[0]?.id ?? null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const selectedBatch = useMemo(
    () => history.find((batch) => batch.id === selectedBatchId) ?? history[0] ?? null,
    [history, selectedBatchId],
  )
  const tasks = selectedBatch?.tasks ?? []

  function refreshHistory(nextSelectedId?: string | null) {
    const nextHistory = loadBatchHistory()
    setHistory(nextHistory)
    if (nextSelectedId !== undefined) {
      setSelectedBatchId(nextSelectedId)
      return
    }
    setSelectedBatchId((currentId) => {
      if (currentId && nextHistory.some((batch) => batch.id === currentId)) {
        return currentId
      }
      return nextHistory[0]?.id ?? null
    })
  }

  async function handleGenerate() {
    setLoading(true)
    setError(null)
    const previousSelectedId = selectedBatchId

    try {
      const response = await createTask13Batch(3)
      const record = appendBatchToHistory(response.tasks)
      refreshHistory(record.id)
    } catch (err) {
      setSelectedBatchId(previousSelectedId)
      setError(err instanceof ApiError ? err.message : 'Не удалось сгенерировать задания')
    } finally {
      setLoading(false)
    }
  }

  function handleSelectBatch(batchId: string) {
    setSelectedBatchId(batchId)
  }

  function handleRemoveBatch(batchId: string) {
    removeBatchFromHistory(batchId)
    refreshHistory(selectedBatchId === batchId ? null : selectedBatchId)
  }

  return (
    <section className="page">
      <h1>Выбор варианта</h1>
      <p className="page-lead">
        Сгенерируйте три независимых задания и выберите одно для решения.
      </p>

      <button type="button" className="btn btn-primary" onClick={handleGenerate} disabled={loading}>
        {loading ? 'Генерация…' : tasks.length > 0 ? 'Сгенерировать новые варианты' : 'Сгенерировать 3 варианта'}
      </button>

      {error && <p className="alert alert-error">{error}</p>}

      {loading && <p className="page-status">Подбираем новые уравнения…</p>}

      {!loading && tasks.length > 0 && selectedBatch && (
        <section className="batch-current" aria-labelledby="current-batch-title">
          <div className="batch-current__header">
            <h2 id="current-batch-title" className="batch-current__title">
              Текущий набор
            </h2>
            <p className="batch-current__meta">
              {formatBatchTimestamp(selectedBatch.createdAt)} · {tasks.length}{' '}
              {tasks.length === 1 ? 'вариант' : tasks.length < 5 ? 'варианта' : 'вариантов'}
            </p>
          </div>
          <TaskGrid tasks={tasks} results={selectedBatch.results} />
        </section>
      )}

      {history.length > 0 && (
        <section className="batch-history" aria-labelledby="batch-history-title">
          <h2 id="batch-history-title" className="batch-history__title">
            История наборов
          </h2>
          <ul className="batch-history__list">
            {history.map((batch) => {
              const isSelected = batch.id === selectedBatch?.id
              return (
                <li key={batch.id} className={isSelected ? 'batch-history__item batch-history__item--active' : 'batch-history__item'}>
                  <div className="batch-history__summary">
                    <p className="batch-history__time">{formatBatchTimestamp(batch.createdAt)}</p>
                    <p className="batch-history__count">
                      {batch.tasks.length}{' '}
                      {batch.tasks.length === 1 ? 'вариант' : batch.tasks.length < 5 ? 'варианта' : 'вариантов'}
                    </p>
                  </div>
                  <div className="batch-history__actions">
                    {!isSelected && (
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleSelectBatch(batch.id)}
                      >
                        Показать
                      </button>
                    )}
                    {isSelected && <span className="batch-history__badge">Открыт</span>}
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleRemoveBatch(batch.id)}
                      aria-label={`Удалить набор от ${formatBatchTimestamp(batch.createdAt)}`}
                    >
                      Удалить
                    </button>
                  </div>
                </li>
              )
            })}
          </ul>
        </section>
      )}
    </section>
  )
}
