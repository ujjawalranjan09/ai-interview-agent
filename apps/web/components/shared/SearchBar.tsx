"use client";
import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Search, X, Loader2, User, FileText, HelpCircle, FolderOpen } from "lucide-react";
import { useSearch } from "@/hooks/useSearch";

interface SearchResult {
  id: string;
  title: string;
  subtitle?: string;
  type: string;
  link: string;
}

const typeIcons: Record<string, React.ReactNode> = {
  candidate: <User className="h-4 w-4" />,
  interview: <FileText className="h-4 w-4" />,
  question: <HelpCircle className="h-4 w-4" />,
  bank: <FolderOpen className="h-4 w-4" />,
};

export function SearchBar() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [debounced, setDebounced] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(query), 300);
    return () => clearTimeout(timer);
  }, [query]);

  const { data, isLoading } = useSearch(debounced);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const results = data ? Object.entries(data).filter(([k]) => k !== "total") : [];
  const total = (data?.total as number) || 0;

  return (
    <div className="relative w-full max-w-md" ref={dropdownRef}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          ref={inputRef}
          type="text"
          placeholder="Search candidates, interviews, questions..."
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          className="flex h-10 w-full rounded-md border border-input bg-background pl-10 pr-10 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        />
        {query && (
          <button
            onClick={() => {
              setQuery("");
              setDebounced("");
            }}
            className="absolute right-3 top-1/2 -translate-y-1/2"
          >
            <X className="h-4 w-4 text-muted-foreground" />
          </button>
        )}
      </div>

      {isOpen && query.length >= 2 && (
        <div className="absolute top-full mt-1 w-full rounded-md border border-border bg-popover shadow-md z-50 max-h-96 overflow-y-auto">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : total === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-muted-foreground">
              No results found for &ldquo;{query}&rdquo;
            </div>
          ) : (
            results.map(([type, items]) =>
              (items as SearchResult[]).length > 0 ? (
                <div key={type}>
                  <div className="px-4 py-2 text-xs font-semibold uppercase text-muted-foreground bg-muted/50">
                    {type}
                  </div>
                  {(items as SearchResult[]).map((item) => (
                    <button
                      key={item.id}
                      className="flex w-full items-center gap-3 px-4 py-2.5 text-left hover:bg-accent transition-colors"
                      onClick={() => {
                        router.push(item.link);
                        setIsOpen(false);
                        setQuery("");
                      }}
                    >
                      <span className="flex-shrink-0 text-muted-foreground">
                        {typeIcons[item.type] || <FileText className="h-4 w-4" />}
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="text-sm font-medium truncate">{item.title}</div>
                        {item.subtitle && (
                          <div className="text-xs text-muted-foreground truncate">{item.subtitle}</div>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              ) : null
            )
          )}
        </div>
      )}
    </div>
  );
}
