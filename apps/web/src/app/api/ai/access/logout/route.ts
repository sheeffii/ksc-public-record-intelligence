import { NextResponse } from "next/server";
import { AI_ACCESS_COOKIE, aiWebOrigin, sameOriginMutation } from "@/lib/ai-access";

export function POST(request: Request) {
  if (!sameOriginMutation(request)) {
    return NextResponse.json({ detail: "Origin rejected" }, { status: 403 });
  }
  const response = NextResponse.redirect(new URL("/ai", aiWebOrigin(request)), { status: 303 });
  response.cookies.delete(AI_ACCESS_COOKIE);
  response.headers.set("cache-control", "no-store");
  return response;
}
