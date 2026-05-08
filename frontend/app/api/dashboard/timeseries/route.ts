import { NextResponse } from "next/server";
import { getTimeSeries } from "@/lib/mock-data";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const hours = Math.max(1, Math.min(168, Number(searchParams.get("hours") ?? 24)));
  return NextResponse.json({ items: getTimeSeries(hours) });
}
