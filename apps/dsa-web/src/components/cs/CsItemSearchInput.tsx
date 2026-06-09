import type React from 'react';
import { useCallback, useEffect, useId, useRef, useState } from 'react';
import { csApi } from '../../api/cs';
import { getParsedApiError } from '../../api/error';
import type { CsGoodIdItem } from '../../types/cs';
import { cn } from '../../utils/cn';

const INPUT_CLASS =
  'input-surface input-focus-glow h-10 w-full min-w-0 rounded-xl border bg-transparent px-3 text-sm transition-all focus:outline-none disabled:cursor-not-allowed disabled:opacity-60';

const DEBOUNCE_MS = 280;
const MIN_SEARCH_LEN = 1;

export type CsItemSearchInputProps = {
  value: string;
  onChange: (value: string) => void;
  selectedItem: CsGoodIdItem | null;
  onSelect: (item: CsGoodIdItem | null) => void;
  disabled?: boolean;
  hasError?: boolean;
  placeholder?: string;
  ariaLabel?: string;
  inputId?: string;
  onSubmit?: () => void;
};

export const CsItemSearchInput: React.FC<CsItemSearchInputProps> = ({
  value,
  onChange,
  selectedItem,
  onSelect,
  disabled = false,
  hasError = false,
  placeholder = '名称 / 皮肤，搜索并选择饰品',
  ariaLabel,
  inputId,
  onSubmit,
}) => {
  const listboxId = useId();
  const rootRef = useRef<HTMLDivElement | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const requestIdRef = useRef(0);

  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [items, setItems] = useState<CsGoodIdItem[]>([]);
  const [total, setTotal] = useState(0);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);

  const runSearch = useCallback(async (term: string) => {
    const trimmed = term.trim();
    if (trimmed.length < MIN_SEARCH_LEN) {
      setItems([]);
      setTotal(0);
      setOpen(false);
      return;
    }

    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    setLoading(true);
    setSearchError(null);

    try {
      const response = await csApi.searchItems({ search: trimmed, pageSize: 20 });
      if (requestId !== requestIdRef.current) {
        return;
      }
      setItems(response.items);
      setTotal(response.total);
      setOpen(response.items.length > 0);
      setHighlightedIndex(response.items.length > 0 ? 0 : -1);
    } catch (err) {
      if (requestId !== requestIdRef.current) {
        return;
      }
      setItems([]);
      setTotal(0);
      setOpen(false);
      setSearchError(getParsedApiError(err).message);
    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    debounceRef.current = setTimeout(() => {
      void runSearch(value);
    }, DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [runSearch, value]);

  useEffect(() => {
    const handlePointerDown = (event: MouseEvent) => {
      const target = event.target;
      if (target instanceof Node && rootRef.current?.contains(target)) {
        return;
      }
      setOpen(false);
    };
    document.addEventListener('mousedown', handlePointerDown);
    return () => document.removeEventListener('mousedown', handlePointerDown);
  }, []);

  const pickItem = useCallback(
    (item: CsGoodIdItem) => {
      onSelect(item);
      onChange(item.name);
      setOpen(false);
      setHighlightedIndex(-1);
    },
    [onChange, onSelect],
  );

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const next = event.target.value;
    onChange(next);
    if (selectedItem && next.trim() !== selectedItem.name.trim()) {
      onSelect(null);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      if (open && items.length > 0 && highlightedIndex >= 0 && highlightedIndex < items.length) {
        event.preventDefault();
        pickItem(items[highlightedIndex]);
        return;
      }
      if (!open || items.length === 0) {
        onSubmit?.();
        return;
      }
    }
    if (!open || items.length === 0) {
      return;
    }
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setHighlightedIndex((idx) => (idx + 1) % items.length);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setHighlightedIndex((idx) => (idx <= 0 ? items.length - 1 : idx - 1));
    } else if (event.key === 'Escape') {
      setOpen(false);
    }
  };

  const showHint = !loading && open && total > items.length;

  return (
    <div ref={rootRef} className="relative min-w-0 flex-1 cs-item-search">
      <input
        id={inputId}
        data-testid="cs-home-query"
        className={cn(INPUT_CLASS, hasError && 'border-danger/50')}
        value={value}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onFocus={() => {
          if (items.length > 0) {
            setOpen(true);
          }
        }}
        disabled={disabled}
        placeholder={placeholder}
        aria-label={ariaLabel}
        role="combobox"
        aria-expanded={open}
        aria-controls={listboxId}
        aria-autocomplete="list"
        autoComplete="off"
      />
      {loading ? (
        <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-text">
          搜索中…
        </span>
      ) : null}
      {open && items.length > 0 ? (
        <ul
          id={listboxId}
          role="listbox"
          className="absolute left-0 right-0 top-11 z-[120] max-h-72 overflow-y-auto rounded-xl border border-subtle bg-elevated py-1 shadow-2xl"
        >
          {items.map((item, index) => {
            const active = index === highlightedIndex;
            return (
              <li key={item.goodId} role="option" aria-selected={active}>
                <button
                  type="button"
                  className={cn(
                    'flex w-full flex-col gap-0.5 px-3 py-2 text-left text-sm transition-colors hover:bg-hover',
                    active && 'bg-hover',
                  )}
                  onMouseEnter={() => setHighlightedIndex(index)}
                  onClick={() => pickItem(item)}
                >
                  <span className="font-medium text-foreground">{item.name}</span>
                  {item.marketHashName ? (
                    <span className="text-[11px] text-muted-text">{item.marketHashName}</span>
                  ) : null}
                </button>
              </li>
            );
          })}
          {showHint ? (
            <li className="border-t border-subtle px-3 py-2 text-xs text-muted-text">
              共 {total} 条，仅显示前 {items.length} 条，请输入更完整名称缩小范围
            </li>
          ) : null}
        </ul>
      ) : null}
      {searchError ? (
        <p className="absolute left-0 top-11 z-[120] mt-1 text-xs text-danger">{searchError}</p>
      ) : null}
    </div>
  );
};
