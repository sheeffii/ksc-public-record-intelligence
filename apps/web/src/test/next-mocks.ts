import { vi } from "vitest";

/**
 * Shared mocks for next/navigation. Call `mockPathname("/x")` before rendering
 * components that read the current route.
 */
export const navigationState = { pathname: "/" };
export const routerRefresh = vi.fn();
export const routerPush = vi.fn();

export function mockPathname(pathname: string) {
  navigationState.pathname = pathname;
}

vi.mock("next/navigation", () => ({
  usePathname: () => navigationState.pathname,
  useRouter: () => ({ refresh: routerRefresh, push: routerPush, replace: vi.fn(), back: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

export const setLocaleMock = vi.fn(async () => {});
vi.mock("@/i18n/actions", () => ({
  setLocale: (...args: unknown[]) => setLocaleMock(...(args as [])),
}));
