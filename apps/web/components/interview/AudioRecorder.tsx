"use client";

import { useState, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

interface AudioRecorderProps {
  onUpload: (blob: Blob) => void;
  isUploading?: boolean;
}

export function AudioRecorder({ onUpload, isUploading }: AudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const isRecordingRef = useRef(false);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
          ? "audio/webm;codecs=opus"
          : "audio/webm",
      });

      chunksRef.current = [];
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: mediaRecorder.mimeType });
        onUpload(blob);
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      isRecordingRef.current = true;
      setDuration(0);

      timerRef.current = setInterval(() => {
        setDuration((d) => {
          if (d >= 300 && isRecordingRef.current) {
            // Auto-stop at 5 minutes
            mediaRecorderRef.current?.stop();
            setIsRecording(false);
            isRecordingRef.current = false;
            return d;
          }
          return d + 1;
        });
      }, 1000);
    } catch {
      toast.error("Microphone permission denied. Please allow microphone access.");
    }
  }, [onUpload]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecordingRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      isRecordingRef.current = false;
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  }, []);

  const formatDuration = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  return (
    <div className="flex flex-col items-center gap-4">
      {isRecording && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span className="h-3 w-3 rounded-full bg-red-500 animate-pulse" />
          Recording {formatDuration(duration)}
        </div>
      )}
      <div className="flex gap-2">
        {!isRecording ? (
          <Button
            type="button"
            onClick={startRecording}
            disabled={isUploading}
            variant="outline"
          >
            {isUploading ? "Processing..." : "Start Recording"}
          </Button>
        ) : (
          <Button type="button" onClick={stopRecording} variant="destructive">
            Stop Recording
          </Button>
        )}
      </div>
    </div>
  );
}
