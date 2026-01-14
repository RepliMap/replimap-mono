import { SignUp } from "@clerk/nextjs";

// Force dynamic rendering - Clerk components require runtime
export const dynamic = "force-dynamic";

export default function SignUpPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <SignUp
        appearance={{
          elements: {
            rootBox: "mx-auto",
            card: "bg-[#030712] border border-slate-800 shadow-2xl",
          },
        }}
      />
    </div>
  );
}
