import { ApiError } from "@/lib/api";
import { toast } from "sonner";

export function handleApiError(error: unknown) {
  if (error instanceof ApiError) {
    toast.error(error.message);
  } else if (error instanceof TypeError && error.message === "Failed to fetch") {
    toast.error("Network error. Please check your connection.");
  } else {
    toast.error("Something went wrong. Please try again.");
  }
}
