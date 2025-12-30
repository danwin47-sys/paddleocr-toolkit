import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PaddleOCR Toolkit - 智慧文件辨識中心",
  description: "基於 AI 的先進文件辨識與校正系統 (Gemini/Claude)",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-TW">
      <body>{children}</body>
    </html>
  );
}
