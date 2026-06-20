import { describe, it, expect } from "vitest";
import { ApiError } from "../api";

describe("ApiError", () => {
  it("creates error with status", () => {
    const err = new ApiError("Not found", 404);
    expect(err).toBeInstanceOf(Error);
    expect(err.message).toBe("Not found");
    expect(err.status).toBe(404);
  });

  it("creates error with different status", () => {
    const err = new ApiError("Server error", 500);
    expect(err.status).toBe(500);
  });
});
