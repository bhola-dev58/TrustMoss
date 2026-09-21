import './globals.css';

export const metadata = {
  title: 'TrustMoss — Real-Time Voice & Agent Reliability Gateway',
  description:
    'Real-time trust layer for voice and text AI agents with sub-15ms Moss contextual retrieval, LiveKit WebRTC gateway, and tri-state circuit breaker.',
  keywords: ['AI Safety', 'Moss', 'LiveKit', 'Guardrails', 'Groundedness', 'Circuit Breaker'],
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-[#121212] text-[#FFFFFF] antialiased font-sans selection:bg-[#FF8C00]/30 selection:text-[#FFC107]">
        {children}
      </body>

    </html>
  );
}
