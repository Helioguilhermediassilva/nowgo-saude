import { NextResponse } from "next/server";
import { getTopics } from "@/lib/dashboard-server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json({ items: await getTopics() });
}
