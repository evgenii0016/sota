import katex from 'katex'
import 'katex/dist/katex.min.css'
import { useMemo } from 'react'
import { normalizeEquationLatex } from '../utils/normalizeEquationLatex'

interface LatexBlockProps {
  latex: string
  className?: string
}

export function LatexBlock({ latex, className }: LatexBlockProps) {
  const html = useMemo(() => {
    const normalized = normalizeEquationLatex(latex)

    try {
      return katex.renderToString(normalized, {
        displayMode: true,
        throwOnError: true,
        strict: 'ignore',
      })
    } catch {
      return katex.renderToString(normalized, {
        displayMode: true,
        throwOnError: false,
        errorColor: '#b42318',
        strict: 'ignore',
      })
    }
  }, [latex])

  return (
    <div
      className={className ? `latex-block ${className}` : 'latex-block'}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
