"use client";

import { useRef, useState, useCallback, useEffect } from "react";

type WSStatus = "connecting" | "connected" | "disconnected";

interface WSMessage {
  type: string;
  [key: string]: unknown;
}

interface Suggestion {
  id: string;
  text: string;
  category: string;
  confidence: number;
}

export function useCopilotWS(interviewId: string, token: string | null) {
  const [status, setStatus] = useState<WSStatus>("disconnected");
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const connectRef = useRef<(() => void) | null>(null);

  const connect = useCallback(() => {
    if (!interviewId || !token) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/copilot/${interviewId}?token=${token}`;

    setStatus("connecting");
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
      reconnectAttempts.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WSMessage;

        switch (data.type) {
          case "suggestions_loading":
            setIsLoadingSuggestions(true);
            break;
          case "suggestions":
            setSuggestions(data.suggestions as Suggestion[]);
            setIsLoadingSuggestions(false);
            break;
          case "suggestion_dismissed":
            {
              const dismissedId = data.suggestion_id as string;
              setSuggestions((prev) => prev.filter((s) => s.id !== dismissedId));
            }
            break;
          default:
            break;
        }
      } catch (e) {
        console.error("Failed to parse WS message:", e);
      }
    };

    ws.onclose = () => {
      setStatus("disconnected");
      wsRef.current = null;

      if (reconnectAttempts.current < maxReconnectAttempts) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttempts.current++;
          connectRef.current?.();
        }, delay);
      }
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [interviewId, token]);

  connectRef.current = connect;

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((message: WSMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const requestSuggestions = useCallback(() => {
    sendMessage({ type: "get_suggestions" });
  }, [sendMessage]);

  const dismissSuggestion = useCallback(
    (suggestionId: string) => {
      sendMessage({ type: "dismiss_suggestion", suggestion_id: suggestionId });
    },
    [sendMessage]
  );

  const sendPing = useCallback(() => {
    sendMessage({ type: "ping" });
  }, [sendMessage]);

  return {
    status,
    suggestions,
    isLoadingSuggestions,
    sendMessage,
    requestSuggestions,
    dismissSuggestion,
    sendPing,
  };
}
