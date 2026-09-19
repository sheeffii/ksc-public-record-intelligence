import { NextResponse } from "next/server";

/** Liveness for the container healthcheck. Touches nothing. */
export function GET() {
  return NextResponse.json({ status: "ok" });
}
