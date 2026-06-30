import type { GeoIntelResult } from '../types';
import QuickScanResult from './QuickScanResult';

interface ResultCardProps {
  result: GeoIntelResult;
}

export default function ResultCard({ result }: ResultCardProps) {
  return <QuickScanResult result={result} />;
}
