/** Normalize assistant chat markdown for cleaner in-bubble rendering. */
export function normalizeChatAssistantMarkdown(md: string): string {
  if (!md.trim()) {
    return '';
  }

  return md
    .replace(/^[-*_]{3,}\s*$/gm, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}
