// This layout will wrap all marketing pages (landing, pricing, etc.)
// Add Header and Footer components here once generated from v0

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      {/* TODO: Add <Header /> component */}
      <div className="min-h-screen">
        {children}
      </div>
      {/* TODO: Add <Footer /> component */}
    </>
  );
}
