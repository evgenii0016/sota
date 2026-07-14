import { useState } from 'react'
import type { FormEvent } from 'react'
import { askAssistant } from '../api/client'
import { ApiError } from '../api/types'

interface AssistantMessage {
  role: 'user' | 'assistant'
  text: string
}

interface AssistantPanelProps {
  taskId: string
  draftPartA: string
  draftPartB: string
}

export function AssistantPanel({ taskId, draftPartA, draftPartB }: AssistantPanelProps) {
  const [messages, setMessages] = useState<AssistantMessage[]>([])
  const [input, setInput] = useState('')
  const [usesLeft, setUsesLeft] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const limitReached = usesLeft === 0

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const message = input.trim()
    if (!message || loading || limitReached) {
      return
    }

    setLoading(true)
    setError(null)
    setMessages((prev) => [...prev, { role: 'user', text: message }])
    setInput('')

    try {
      const history = messages.map((item) => ({ role: item.role, text: item.text }))
      const response = await askAssistant(taskId, {
        message,
        draft_solution: {
          part_a: draftPartA,
          part_b: draftPartB,
        },
        history,
      })
      setUsesLeft(response.uses_left)
      setMessages((prev) => [...prev, { role: 'assistant', text: response.reply }])
    } catch (err) {
      if (err instanceof ApiError && err.code === 'assistant_limit_exceeded') {
        setUsesLeft(0)
        setError('Лимит обращений исчерпан.')
      } else {
        setError(err instanceof ApiError ? err.message : 'Не удалось получить ответ помощника.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <aside className="assistant-panel">
      <header className="assistant-panel__header">
        <h2>ИИ-помощник</h2>
        <p className="assistant-panel__disclaimer">
          Помощник объясняет теорию и задаёт наводящие вопросы, но не подсказывает ответ и следующий шаг.
        </p>
        {usesLeft !== null && <p className="assistant-panel__uses">Осталось обращений: {usesLeft}</p>}
      </header>

      <div className="assistant-panel__messages" aria-live="polite">
        {messages.length === 0 && (
          <p className="muted">Задайте вопрос по условию или по своему черновику решения.</p>
        )}
        {messages.map((message, index) => (
          <div key={`${message.role}-${index}`} className={`assistant-message assistant-message--${message.role}`}>
            <strong>{message.role === 'user' ? 'Вы' : 'Помощник'}</strong>
            <p>{message.text}</p>
          </div>
        ))}
      </div>

      <form className="assistant-panel__form" onSubmit={handleSubmit}>
        <textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          rows={3}
          placeholder="Например: зачем проверять ОДЗ?"
          disabled={loading || limitReached}
          maxLength={4000}
        />
        {error && <p className="field-error">{error}</p>}
        <button type="submit" className="btn btn-primary btn-sm" disabled={loading || limitReached || !input.trim()}>
          {loading ? 'Отправка…' : 'Спросить'}
        </button>
      </form>
    </aside>
  )
}
