/**
 * MH-14/AISV-05 (D-03): đánh dấu các cụm từ dùng chung giữa đoạn nộp và đoạn
 * nguồn. Hàm thuần — không đụng DOM, không sinh HTML: trả về các đoạn văn bản
 * thường kèm cờ `match`, component bọc đoạn khớp trong <mark> bằng React text
 * node (T-04-31, không bao giờ render HTML thô từ nội dung trích xuất).
 */
export interface HighlightSegment {
  text: string
  match: boolean
}

// Từ = chuỗi chữ cái/chữ số Unicode (tiếng Việt có dấu nằm trọn trong \p{L}).
const TOKEN_RE = /[\p{L}\p{N}]+|[^\p{L}\p{N}]+/gu
const WORD_RE = /^[\p{L}\p{N}]+$/u

function normalizeWord(word: string): string {
  return word.normalize('NFC').toLowerCase()
}

function words(text: string): string[] {
  return (text.normalize('NFC').match(/[\p{L}\p{N}]+/gu) ?? []).map(normalizeWord)
}

/**
 * Tách `text` thành các đoạn liên tiếp; một từ được đánh dấu khi nó thuộc ít
 * nhất một chuỗi `n` từ liên tiếp cũng xuất hiện liên tiếp, đúng thứ tự, trong
 * `other` (so sánh sau NFC + chữ thường). Dấu cách/dấu câu nằm giữa hai từ được
 * đánh dấu cũng được đánh dấu để vùng tô liền mạch; các đoạn cùng cờ kề nhau
 * được gộp. Rỗng hoặc không khớp -> một đoạn không đánh dấu.
 */
export function highlightOverlap(text: string, other: string, n = 3): HighlightSegment[] {
  if (!text) return [{ text: text ?? '', match: false }]
  const tokens = text.match(TOKEN_RE) ?? [text]
  const otherWords = words(other ?? '')
  if (n < 1 || otherWords.length < n) return [{ text, match: false }]

  const grams = new Set<string>()
  for (let i = 0; i + n <= otherWords.length; i += 1) {
    grams.add(otherWords.slice(i, i + n).join('\u0001'))
  }

  const wordIdx: number[] = []
  const textWords: string[] = []
  tokens.forEach((tok, i) => {
    if (WORD_RE.test(tok)) {
      wordIdx.push(i)
      textWords.push(normalizeWord(tok))
    }
  })
  const marked = new Array<boolean>(textWords.length).fill(false)
  for (let i = 0; i + n <= textWords.length; i += 1) {
    if (grams.has(textWords.slice(i, i + n).join('\u0001'))) {
      for (let k = i; k < i + n; k += 1) marked[k] = true
    }
  }

  const tokenMatch = new Array<boolean>(tokens.length).fill(false)
  wordIdx.forEach((tokenPos, w) => {
    tokenMatch[tokenPos] = marked[w]
  })
  // Dấu phân cách giữa hai từ cùng được đánh dấu -> đánh dấu luôn.
  for (let w = 0; w + 1 < wordIdx.length; w += 1) {
    if (marked[w] && marked[w + 1]) {
      for (let t = wordIdx[w] + 1; t < wordIdx[w + 1]; t += 1) tokenMatch[t] = true
    }
  }

  const segments: HighlightSegment[] = []
  tokens.forEach((tok, i) => {
    const last = segments[segments.length - 1]
    if (last && last.match === tokenMatch[i]) {
      last.text += tok
    } else {
      segments.push({ text: tok, match: tokenMatch[i] })
    }
  })
  return segments.length > 0 ? segments : [{ text, match: false }]
}

export type TinHieu = 'NGUYEN_VAN' | 'SUA_NHE' | 'NGU_NGHIA'

// Hậu tố do Web API ghi (_TIN_HIEU_NHAN); kết quả lưu trước khi có SUA_NHE chỉ mang hai hậu tố còn lại.
const HAU_TO_TIN_HIEU = new Map<string, TinHieu>([
  ['trùng nguyên văn', 'NGUYEN_VAN'],
  ['trùng sửa nhẹ', 'SUA_NHE'],
  ['trùng ngữ nghĩa', 'NGU_NGHIA'],
])

/**
 * 04-06: vi_tri lưu dạng "Câu a–b · trùng nguyên văn|trùng sửa nhẹ|trùng ngữ
 * nghĩa" (không có hậu tố khi bộ giả lập không trả tín hiệu).
 */
export function parseViTri(viTri: string | null): { viTri: string; tinHieu: TinHieu | null } {
  if (!viTri) return { viTri: '', tinHieu: null }
  const sep = viTri.lastIndexOf(' · ')
  if (sep < 0) return { viTri, tinHieu: null }
  const suffix = viTri.slice(sep + 3).trim()
  const tinHieu = HAU_TO_TIN_HIEU.get(suffix) ?? null
  return tinHieu ? { viTri: viTri.slice(0, sep), tinHieu } : { viTri, tinHieu: null }
}
