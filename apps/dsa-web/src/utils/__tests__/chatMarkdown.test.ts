import { describe, expect, it } from 'vitest';
import { normalizeChatAssistantMarkdown } from '../chatMarkdown';

describe('normalizeChatAssistantMarkdown', () => {
  it('removes markdown horizontal rules', () => {
    const input = '# Title\n---\n**结论：** 500万\n---\n正文';
    expect(normalizeChatAssistantMarkdown(input)).toBe('# Title\n\n**结论：** 500万\n\n正文');
  });

  it('collapses excessive blank lines', () => {
    const input = '段落一\n\n\n\n段落二';
    expect(normalizeChatAssistantMarkdown(input)).toBe('段落一\n\n段落二');
  });
});
