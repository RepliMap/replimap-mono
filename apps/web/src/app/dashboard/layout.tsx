import { Header } from "@/components/header";
import { RequireAuth } from "@/components/auth-components";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <Header />
      <RequireAuth>{children}</RequireAuth>
    </>
  );
}
