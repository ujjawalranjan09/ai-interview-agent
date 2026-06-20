/// <reference types="vitest/globals" />
import "@testing-library/jest-dom";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  useParams: () => ({}),
  usePathname: () => "/",
}));
