import { NextResponse } from "next/server";
import {
  AI_ACCESS_COOKIE,
  aiAccessRequired,
  aiApiRequest,
  aiWebOrigin,
  sameOriginMutation,
} from "@/lib/ai-access";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  if (!sameOriginMutation(request)) {
    return NextResponse.json({ detail: "Origin rejected" }, { status: 403 });
  }
  const form = await request.formData();
  const value = form.get("token");
  const token = typeof value === "string" ? value.trim() : "";
  const destination = new URL("/ai", aiWebOrigin(request));
  if (!token || token.length > 4096) {
    destination.searchParams.set("access", "invalid");
    return NextResponse.redirect(destination, { status: 303 });
  }
  try {
    const response = await aiApiRequest("/runs?limit=1", token);
    if (!response.ok) {
      destination.searchParams.set("access", "invalid");
      return NextResponse.redirect(destination, { status: 303 });
    }
  } catch {
    destination.searchParams.set("access", "unavailable");
    return NextResponse.redirect(destination, { status: 303 });
  }
  const response = NextResponse.redirect(destination, { status: 303 });
  response.cookies.set(AI_ACCESS_COOKIE, token, {
    httpOnly: true,
    secure: aiAccessRequired(),
    sameSite: "strict",
    maxAge: 8 * 60 * 60,
    path: "/",
  });
  response.headers.set("cache-control", "no-store");
  return response;
}
