"use client";
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Calendar, Clock, Plus, X, Loader2 } from "lucide-react";
import { useAvailability, useSetAvailability, useScheduledInterviews } from "@/hooks/useScheduling";

const dayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

export default function SchedulingPage() {
  const { data: availability, isLoading: availLoading } = useAvailability();
  const { data: scheduled } = useScheduledInterviews();
  const setAvail = useSetAvailability();
  const [slots, setSlots] = useState<Array<{ day_of_week: number; start_time: string; end_time: string }>>([]);
  const [isEditing, setIsEditing] = useState(false);

  const addSlot = () => {
    setSlots([...slots, { day_of_week: 1, start_time: "09:00", end_time: "17:00" }]);
  };

  const removeSlot = (index: number) => {
    setSlots(slots.filter((_, i) => i !== index));
  };

  const handleSave = async () => {
    try {
      await setAvail.mutateAsync({ slots });
      toast.success("Availability saved");
      setIsEditing(false);
    } catch {
      toast.error("Failed to save availability");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Interview Scheduling</h1>
        <p className="text-muted-foreground">Manage your availability and scheduled interviews</p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Your Availability</CardTitle>
              <CardDescription>Set your weekly availability for interviews</CardDescription>
            </div>
            <Button variant="outline" onClick={() => { setIsEditing(!isEditing); if (!isEditing) setSlots(availability || []); }}>
              {isEditing ? "Cancel" : "Edit"}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {availLoading ? (
            <div className="flex justify-center py-4">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : isEditing ? (
            <div className="space-y-3">
              {slots.map((slot, i) => (
                <div key={i} className="flex items-center gap-3">
                  <select
                    value={slot.day_of_week}
                    onChange={(e) => {
                      const updated = [...slots];
                      updated[i] = { ...updated[i], day_of_week: parseInt(e.target.value) };
                      setSlots(updated);
                    }}
                    className="flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    {dayNames.map((name, d) => (
                      <option key={d} value={d}>{name}</option>
                    ))}
                  </select>
                  <input
                    type="time"
                    value={slot.start_time}
                    onChange={(e) => {
                      const updated = [...slots];
                      updated[i] = { ...updated[i], start_time: e.target.value };
                      setSlots(updated);
                    }}
                    className="flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                  />
                  <span className="text-muted-foreground">to</span>
                  <input
                    type="time"
                    value={slot.end_time}
                    onChange={(e) => {
                      const updated = [...slots];
                      updated[i] = { ...updated[i], end_time: e.target.value };
                      setSlots(updated);
                    }}
                    className="flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                  />
                  <Button variant="ghost" size="icon" onClick={() => removeSlot(i)}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              <Button variant="outline" onClick={addSlot} className="w-full">
                <Plus className="mr-2 h-4 w-4" /> Add Time Slot
              </Button>
              <Button onClick={handleSave} disabled={setAvail.isPending} className="w-full">
                {setAvail.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                Save Availability
              </Button>
            </div>
          ) : (
            <div className="space-y-2">
              {availability?.length ? (
                availability.map((slot: any) => (
                  <div key={slot.id} className="flex items-center gap-2 text-sm">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">{dayNames[slot.day_of_week]}</span>
                    <Clock className="h-4 w-4 text-muted-foreground ml-2" />
                    <span>{slot.start_time} - {slot.end_time}</span>
                    <span className="text-xs text-muted-foreground">({slot.timezone})</span>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No availability set yet. Click Edit to add time slots.</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Scheduled Interviews</CardTitle>
          <CardDescription>Your upcoming and past scheduled interviews</CardDescription>
        </CardHeader>
        <CardContent>
          {scheduled?.items?.length ? (
            <div className="space-y-3">
              {scheduled.items.map((s: any) => (
                <div key={s.id} className="flex items-center justify-between rounded-lg border p-3">
                  <div>
                    <p className="text-sm font-medium">
                      {new Date(s.scheduled_at).toLocaleDateString()} at {new Date(s.scheduled_at).toLocaleTimeString()}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {s.duration_minutes} min &middot; {s.status}
                    </p>
                  </div>
                  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    s.status === "scheduled" ? "bg-blue-100 text-blue-800" :
                    s.status === "completed" ? "bg-green-100 text-green-800" :
                    s.status === "cancelled" ? "bg-red-100 text-red-800" :
                    "bg-gray-100 text-gray-800"
                  }`}>
                    {s.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No scheduled interviews yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
