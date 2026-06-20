"use client";
import { apiFetch } from "@/lib/api";

export async function requestNotificationPermission(): Promise<boolean> {
  if (!("Notification" in window)) return false;
  const permission = await Notification.requestPermission();
  return permission === "granted";
}

export async function subscribeToPush(): Promise<boolean> {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) return false;
  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(
        process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY || ""
      ).buffer as ArrayBuffer,
    });
    await apiFetch("/api/v1/notifications/subscribe", {
      method: "POST",
      json: { subscription: subscription.toJSON() },
    });
    return true;
  } catch {
    return false;
  }
}

export async function unsubscribeFromPush(): Promise<boolean> {
  if (!("serviceWorker" in navigator)) return false;
  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    if (subscription) {
      await apiFetch("/api/v1/notifications/unsubscribe", {
        method: "POST",
        json: { endpoint: subscription.endpoint },
      });
      await subscription.unsubscribe();
    }
    return true;
  } catch {
    return false;
  }
}

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)));
}
