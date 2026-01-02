import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";

const GA_TRACKING_ID = process.env.NEXT_PUBLIC_GA_ID || '';

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
    <html lang="zh-TW" suppressHydrationWarning>
      <head>
        {GA_TRACKING_ID && (
          <Script
            src={`https://www.googletagmanager.com/gtag/js?id=${GA_TRACKING_ID}`}
            strategy="afterInteractive"
          />
        )}
        {GA_TRACKING_ID && (
          <Script id="google-analytics" strategy="afterInteractive">
            {`
              window.dataLayer = window.dataLayer || [];
              function gtag(){dataLayer.push(arguments);}
              gtag('js', new Date());
              gtag('config', '${GA_TRACKING_ID}', {
                page_path: window.location.pathname,
              });
            `}
          </Script>
        )}

        {/* Google AdSense - 廣告營利 */}
        <Script
          async
          src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7077085475180219"
          crossOrigin="anonymous"
          strategy="afterInteractive"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
