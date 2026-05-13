import { NextResponse } from "next/server";
import { getRegionDetail } from "@/lib/dashboard-server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ code: string }> },
) {
  const { code } = await params;
  const detail = await getRegionDetail(decodeURIComponent(code));
  if (!detail) {
    return NextResponse.json({ error: "region not found" }, { status: 404 });
  }
  return NextResponse.json(detail);
}
