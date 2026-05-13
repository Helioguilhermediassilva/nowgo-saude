import { NextResponse } from "next/server";
import { getHeatmap } from "@/lib/dashboard-server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json({ items: await getHeatmap() });
}
