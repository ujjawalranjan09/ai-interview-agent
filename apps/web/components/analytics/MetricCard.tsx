"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface MetricCardProps {
  value: number;
  label: string;
  icon: string;
  decimals?: number;
}

export function MetricCard({ value, label, icon, decimals = 0 }: MetricCardProps) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const duration = 1000;
    const steps = 60;
    const increment = value / steps;
    let current = 0;
    const interval = setInterval(() => {
      current += increment;
      if (current >= value) {
        setDisplay(value);
        clearInterval(interval);
      } else {
        setDisplay(current);
      }
    }, duration / steps);
    return () => clearInterval(interval);
  }, [value]);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {label}
        </CardTitle>
        <span className="text-2xl">{icon}</span>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {Intl.NumberFormat().format(Number(display.toFixed(decimals)))}
        </div>
      </CardContent>
    </Card>
  );
}
