import { ReactNode } from "react";
import { RequireAuth } from "@/components/auth-components";

export default function CheckoutLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <RequireAuth>{children}</RequireAuth>;
}
