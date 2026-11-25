import './globals.css';
import type { Metadata } from 'next';
export const metadata: Metadata = { title: 'GPU Health Review Dashboard', description: 'Synthetic GPU telemetry review and anomaly investigation.' };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }
