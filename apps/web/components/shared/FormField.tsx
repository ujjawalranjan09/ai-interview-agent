"use client";
import { InputHTMLAttributes, TextareaHTMLAttributes, SelectHTMLAttributes } from "react";

interface FormFieldProps {
  label: string;
  id: string;
  error?: string;
  required?: boolean;
  children: React.ReactNode;
}

export function FormField({ label, id, error, required, children }: FormFieldProps) {
  return (
    <div className="space-y-2">
      <label htmlFor={id} className="text-sm font-medium">
        {label}
        {required && <span className="ml-1 text-destructive" aria-hidden="true">*</span>}
        {required && <span className="sr-only">(required)</span>}
      </label>
      {children}
      {error && (
        <p id={`${id}-error`} role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}
