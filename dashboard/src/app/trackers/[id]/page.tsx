"use client";

import { useParams } from "next/navigation";
import { TrackerDetail } from "@/components/trackers/TrackerDetail";

export default function TrackerDetailPage() {
  const params = useParams();
  const id = params?.id as string;
  return <TrackerDetail trackerId={id} />;
}
