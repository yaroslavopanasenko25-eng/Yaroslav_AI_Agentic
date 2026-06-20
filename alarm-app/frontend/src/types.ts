export type Theme = 'dark' | 'light';
export type Language = 'uk' | 'en';
export type Tab = 'dashboard' | 'analysis' | 'safety';
export type AlarmStatus = 'active' | 'warning' | 'clear' | 'occupied';
export type ShelterType = 'bomb_shelter' | 'metro' | 'basement';

export interface Region {
  id: string;
  nameUk: string;
  nameEn: string;
  status: AlarmStatus;
}

export interface ThreatData {
  type: 'missiles' | 'drones' | 'aircraft';
  total: number;
  destroyed: number;
  hit: number;
  lost: number;
}

export interface AlarmEvent {
  id: string;
  date: string;
  startTime: string;
  duration: number;
  regions: string[];
  threats: ThreatData[];
}

export interface Shelter {
  id: string;
  nameUk: string;
  nameEn?: string;
  lat: number;
  lng: number;
  city: string;
  capacity?: number;
  type: ShelterType;
  kind?: string;
}

export interface SafetyTip {
  id: string;
  icon: string;
  titleUk: string;
  titleEn: string;
  descUk: string;
  descEn: string;
}

export interface AppSettings {
  theme: Theme;
  language: Language;
  dyslexiaMode: boolean;
  setTheme: (t: Theme) => void;
  setLanguage: (l: Language) => void;
  setDyslexiaMode: (v: boolean) => void;
}
