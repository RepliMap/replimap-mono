import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

// Whitelist approach: ONLY dashboard requires auth
// Landing page, docs, pricing, etc. - all public
const isProtectedRoute = createRouteMatcher(["/dashboard(.*)"]);

// Paths that should completely bypass Clerk
const BYPASS_PATHS = ["/sitemap.xml", "/robots.txt"];

export default clerkMiddleware(async (auth, req) => {
  const pathname = req.nextUrl.pathname;

  // Bypass Clerk entirely for sitemap and robots
  if (BYPASS_PATHS.includes(pathname)) {
    return NextResponse.next();
  }

  if (isProtectedRoute(req)) {
    await auth.protect();
  }
});

export const config = {
  matcher: [
    // Skip Next.js internals and static files
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    // Always run for API routes
    "/(api|trpc)(.*)",
  ],
};
