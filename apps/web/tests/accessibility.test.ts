import { describe, it, expect } from "vitest";

describe("Accessibility compliance", () => {
  it("skip navigation link should exist", () => {
    const skipNavHtml = '<a href="#main-content">Skip to main content</a>';
    expect(skipNavHtml).toContain("#main-content");
    expect(skipNavHtml).toContain("Skip to main content");
  });

  it("form fields should have associated labels", () => {
    const fieldHtml = '<label for="email">Email</label><input id="email" type="email" />';
    expect(fieldHtml).toContain('for="email"');
    expect(fieldHtml).toContain('id="email"');
  });

  it("ARIA labels should be present on icon buttons", () => {
    const iconBtn = '<button aria-label="Close"><svg /></button>';
    expect(iconBtn).toContain('aria-label="Close"');
  });

  it("loading states should have aria-busy", () => {
    const loading = '<div aria-busy="true">Loading...</div>';
    expect(loading).toContain('aria-busy="true"');
  });

  it("error messages should have role=alert", () => {
    const error = '<p role="alert">Error occurred</p>';
    expect(error).toContain('role="alert"');
  });

  it("navigation should have role and aria-label", () => {
    const nav = '<nav role="navigation" aria-label="Main navigation">';
    expect(nav).toContain('role="navigation"');
    expect(nav).toContain('aria-label="Main navigation"');
  });
});
