import { NextResponse } from "next/server";
import { getUnitDetail } from "@/lib/dashboard-server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const detail = await getUnitDetail(decodeURIComponent(id));
  if (!detail) {
    return NextResponse.json({ error: "unit not found" }, { status: 404 });
  }
  return NextResponse.json(detail);
}
