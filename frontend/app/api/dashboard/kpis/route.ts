import { NextResponse } from "next/server";
import { getKpis } from "@/lib/mock-data";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json({ items: getKpis() });
}
