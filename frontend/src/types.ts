export interface GeoIntelResult {
  ip: string;
  continent: string;
  country: string;
  region: string;
  city: string;
  lat: number;
  lon: number;
  isp: string;
  org: string;
  asn: string;
}

export interface DnsResult {
  A?: string[];
  AAAA?: string[];
  MX?: string[];
  NS?: string[];
  TXT?: string[];
  SOA?: string[];
  CNAME?: string[];
  PTR?: string[];
}

export interface WhoisResult {
  domain_name?: string[];
  registrar?: string;
  whois_server?: string;
  creation_date?: string;
  expiration_date?: string;
  updated_date?: string;
  name_servers?: string[];
  status?: string[];
  emails?: string[];
  org?: string;
  country?: string;
  city?: string;
  error?: string;
}

export interface SslResult {
  subject?: string;
  issuer?: string;
  serial?: string;
  version?: number;
  not_before?: string;
  not_after?: string;
  sans?: string[];
  fingerprint?: string;
  error?: string;
}

export interface HttpResult {
  status_code: number;
  server: string;
  content_type: string;
  security: Record<string, string>;
  all_headers: Record<string, string>;
  final_url: string;
  error?: string;
}

export interface ReverseDnsResult {
  hostname?: string;
  aliases?: string[];
  ips?: string[];
  error?: string;
}

export interface ScanType {
  id: string;
  name: string;
  description: string;
  icon: string;
}

export interface FullScanResult {
  target: string;
  resolved_ip: string;
  results: {
    quick?: GeoIntelResult;
    dns?: DnsResult;
    whois?: WhoisResult;
    ssl?: SslResult;
    http?: HttpResult;
    reverse?: ReverseDnsResult;
    rdap?: Record<string, unknown>;
    subdomains?: Record<string, unknown>;
    email?: Record<string, unknown>;
    web?: Record<string, unknown>;
    files?: Record<string, unknown>;
    ports?: Record<string, unknown>;
    connectivity?: Record<string, unknown>;
    zone_transfer?: Record<string, unknown>;
  };
  errors?: Record<string, string> | null;
}

export type ScanResult =
  | GeoIntelResult
  | DnsResult
  | WhoisResult
  | SslResult
  | HttpResult
  | ReverseDnsResult
  | Record<string, unknown>;
