export interface FormattedPartA {
  lead: string
  equation: string
}

export interface FormattedPartB {
  lead: string
  interval: string
}

export function formatPartA(partAPrompt: string): FormattedPartA {
  const prefix = 'Решите уравнение '
  if (partAPrompt.startsWith(prefix)) {
    const equation = partAPrompt.slice(prefix.length).replace(/\.$/, '')
    return { lead: 'Решите уравнение', equation }
  }
  return { lead: partAPrompt, equation: '' }
}

export function formatPartB(partBPrompt: string, intervalDisplay?: string | null): FormattedPartB {
  if (intervalDisplay) {
    return {
      lead: 'Найдите корни этого уравнения, принадлежащие отрезку',
      interval: intervalDisplay,
    }
  }

  const match = partBPrompt.match(/^Найдите корни этого уравнения, принадлежащие отрезку (.+)\.$/)
  if (match) {
    return {
      lead: 'Найдите корни этого уравнения, принадлежащие отрезку',
      interval: match[1],
    }
  }

  return { lead: partBPrompt, interval: '' }
}

/** Разбивает уравнение на строки по слагаемым для наглядного вывода. */
export function splitEquationLines(equation: string): string[] {
  const trimmed = equation.trim()
  if (!trimmed) {
    return []
  }

  const body = trimmed.replace(/\s*=\s*0\s*$/, '').trim()
  const terms = body.split(/(?=[+-])/).map((term) => term.trim()).filter(Boolean)

  if (terms.length <= 1) {
    return [trimmed]
  }

  return [
    ...terms.map((term) => term.replace(/^\+/, '').replace(/^-/, '− ')),
    '= 0',
  ]
}
