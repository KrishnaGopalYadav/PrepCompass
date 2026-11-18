import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PrepCompass — Your preparation command centre",
  description: "Plan. Prepare. Progress. Your personal civil services study companion.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
