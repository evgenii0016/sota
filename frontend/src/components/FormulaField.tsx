import { createElement, useEffect, useRef, useState } from 'react'
import type { MathfieldElement } from 'mathlive'
import 'mathlive'
import 'mathlive/static.css'

interface FormulaFieldProps {
  id: string
  value: string
  onChange: (value: string) => void
  multiline?: boolean
  placeholder?: string
  maxLength?: number
  ariaLabel: string
  error?: string | null
}

function normalizeMathValue(raw: string): string {
  return raw
    .replace(/\\pi/g, 'π')
    .replace(/\\in/g, '∈')
    .replace(/\\mathbb\{Z\}/g, 'ℤ')
    .replace(/\s+/g, ' ')
    .trim()
}

function configureMathField(field: MathfieldElement) {
  field.mathVirtualKeyboardPolicy = 'auto'
}

export function FormulaField({
  id,
  value,
  onChange,
  multiline = false,
  placeholder,
  maxLength,
  ariaLabel,
  error,
}: FormulaFieldProps) {
  const mathRef = useRef<MathfieldElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [mathReady, setMathReady] = useState(!multiline)
  const insertRef = useRef<MathfieldElement>(null)

  useEffect(() => {
    if (multiline) {
      return
    }

    const field = mathRef.current
    if (!field) {
      return
    }

    configureMathField(field)

    const handleInput = () => {
      onChange(normalizeMathValue(field.getValue('latex-expanded')))
    }

    field.addEventListener('input', handleInput)
    setMathReady(true)

    return () => {
      field.removeEventListener('input', handleInput)
    }
  }, [multiline, onChange])

  useEffect(() => {
    if (multiline || !mathReady) {
      return
    }

    const field = mathRef.current
    if (field && field.value !== value) {
      field.value = value
    }
  }, [multiline, mathReady, value])

  useEffect(() => {
    if (!multiline) {
      return
    }

    const field = insertRef.current
    if (!field) {
      return
    }

    configureMathField(field)
  }, [multiline])

  function insertFormula() {
    const field = insertRef.current
    const textarea = textareaRef.current
    if (!field || !textarea) {
      return
    }

    const latex = normalizeMathValue(field.getValue('latex-expanded'))
    if (!latex) {
      return
    }

    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const next = `${value.slice(0, start)}${latex}${value.slice(end)}`
    onChange(next)
    field.value = ''

    requestAnimationFrame(() => {
      textarea.focus()
      const cursor = start + latex.length
      textarea.setSelectionRange(cursor, cursor)
    })
  }

  if (multiline) {
    return (
      <div className="formula-field">
        <textarea
          ref={textareaRef}
          id={id}
          className={error ? 'field-invalid' : undefined}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          rows={12}
          placeholder={placeholder}
          maxLength={maxLength}
          aria-label={ariaLabel}
        />
        <div className="formula-field__insert">
          <label htmlFor={`${id}-math`}>Вставьте формулу</label>
          {createElement('math-field', {
            ref: insertRef,
            id: `${id}-math`,
            'aria-label': 'Вставка формулы в решение',
          })}
          <button type="button" className="btn btn-secondary btn-sm" onClick={insertFormula}>
            Вставить в решение
          </button>
        </div>
        {error && <p className="field-error">{error}</p>}
      </div>
    )
  }

  if (!mathReady) {
    return (
      <input
        id={id}
        className={error ? 'field-invalid' : undefined}
        type="text"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        maxLength={maxLength}
        aria-label={ariaLabel}
      />
    )
  }

  return (
    <div className="formula-field">
      {createElement('math-field', {
        ref: mathRef,
        id,
        className: error ? 'field-invalid' : undefined,
        'aria-label': ariaLabel,
      })}
      {error && <p className="field-error">{error}</p>}
    </div>
  )
}
