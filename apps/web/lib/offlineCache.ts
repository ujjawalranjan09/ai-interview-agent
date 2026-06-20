"use client";

const CACHE_PREFIX = "aia_";
const CACHE_EXPIRY_MS = 24 * 60 * 60 * 1000;

interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

function isExpired(entry: CacheEntry<any>): boolean {
  return Date.now() - entry.timestamp > CACHE_EXPIRY_MS;
}

function safeGetItem<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(CACHE_PREFIX + key);
    if (!raw) return null;
    const entry: CacheEntry<T> = JSON.parse(raw);
    if (isExpired(entry)) {
      localStorage.removeItem(CACHE_PREFIX + key);
      return null;
    }
    return entry.data;
  } catch {
    return null;
  }
}

function safeSetItem<T>(key: string, data: T): void {
  try {
    const entry: CacheEntry<T> = { data, timestamp: Date.now() };
    localStorage.setItem(CACHE_PREFIX + key, JSON.stringify(entry));
  } catch {
    // localStorage full or unavailable
  }
}

export function cacheInterviews(interviews: any[]): void {
  safeSetItem("interviews", interviews);
}

export function getCachedInterviews(): any[] | null {
  return safeGetItem<any[]>("interviews");
}

export function cacheReport(interviewId: string, report: any): void {
  safeSetItem(`report_${interviewId}`, report);
}

export function getCachedReport(interviewId: string): any | null {
  return safeGetItem<any>(`report_${interviewId}`);
}

export function clearAllCache(): void {
  try {
    const keys = Object.keys(localStorage).filter(k => k.startsWith(CACHE_PREFIX));
    keys.forEach(k => localStorage.removeItem(k));
  } catch {
    // ignore
  }
}
