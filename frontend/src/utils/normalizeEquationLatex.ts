/**
 * Repairs LaTeX corrupted by JSON/JS escape processing:
 * \right → CR+ight, \frac → FF+rac, etc.
 */
export function normalizeEquationLatex(latex: string): string {
  if (!latex) {
    return latex
  }

  let normalized = latex
    .replace(/\r(?=ight\b)/g, '\\r')
    .replace(/\f(?=rac\b)/g, '\\f')
    .replace(/\t(?=an\b)/g, '\\t')
    .replace(/\t(?=heta\b)/g, '\\t')
    .replace(/\t(?=imes\b)/g, '\\t')
    .replace(/\n(?=eq\b)/g, '\\n')
    .replace(/(^|[^\\])sin(?=[({\\])/g, '$1\\sin')
    .replace(/(^|[^\\])cos(?=[({\\])/g, '$1\\cos')
    .replace(/(^|[^\\])tan(?=[({\\])/g, '$1\\tan')

  if (/\\\\[a-zA-Z]/.test(normalized)) {
    normalized = normalized.replace(/\\\\([a-zA-Z])/g, '\\$1')
  }

  return normalized
}
