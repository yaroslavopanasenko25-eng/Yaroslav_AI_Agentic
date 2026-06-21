/** Map GeoJSON `region` property → app region slug */
export const GEO_REGION_TO_SLUG: Record<string, string> = {
  'Автономна Республіка Крим': 'crimea',
  'Вінницька область': 'vinnytsia',
  'Волинська область': 'volyn',
  'Дніпропетровська область': 'dnipro',
  'Донецька область': 'donetsk',
  'Житомирська область': 'zhytomyr',
  'Закарпатська область': 'zakarpattia',
  'Запорізька область': 'zaporizhzhia',
  'Івано-Франківська область': 'ivano-frankivsk',
  'Кіровоградська область': 'kirovohrad',
  'Луганська область': 'luhansk',
  'Львівська область': 'lviv',
  'Миколаївська область': 'mykolaiv',
  'Одеська область': 'odesa',
  'Полтавська область': 'poltava',
  'Рівненська область': 'rivne',
  'Сумська область': 'sumy',
  'Тернопільська область': 'ternopil',
  'Харківська область': 'kharkiv',
  'Хмельницька область': 'khmelnytskyi',
  'Черкаська область': 'cherkasy',
  'Чернівецька область': 'chernivtsi',
  'Чернігівська область': 'chernihiv',
  'Херсонська область': 'kherson',
  'Київська область': 'kyiv-oblast',
  'Севастополь': 'crimea',
};

/** alerts.in.ua-style oblast fills */
export const STATUS_FILL: Record<string, string> = {
  active:   '#c43838',
  warning:  '#d4882a',
  clear:    '#243b55',
  occupied: '#4a1414',
};

export const STATUS_STROKE: Record<string, string> = {
  active:   '#d85050',
  warning:  '#e8a040',
  clear:    '#8aa0bc',
  occupied: '#6a2828',
};

/** Per-region label tints like alerts.in.ua (clear oblasts) */
export const LABEL_COLOR_BY_SLUG: Record<string, string> = {
  volyn: '#8aafd0',
  rivne: '#7a9ec8',
  zhytomyr: '#9ab4cc',
  'kyiv-oblast': '#c8a878',
  'kyiv-city': '#e0c890',
  chernihiv: '#a0b8d0',
  sumy: '#98aac8',
  kharkiv: '#f0b0b0',
  poltava: '#a8b8d0',
  cherkasy: '#b0a878',
  kirovohrad: '#e8a898',
  dnipro: '#f0a8a8',
  donetsk: '#c89898',
  luhansk: '#b88888',
  zaporizhzhia: '#f0a898',
  kherson: '#d0a898',
  mykolaiv: '#c8a890',
  odesa: '#90a8c8',
  vinnytsia: '#88a8c8',
  khmelnytskyi: '#98b0c8',
  ternopil: '#88b0c0',
  lviv: '#88b8c8',
  'ivano-frankivsk': '#80b0c0',
  zakarpattia: '#78a8b8',
  chernivtsi: '#80a8c0',
  crimea: '#a87878',
};

export const STATUS_LABEL_FILL: Record<string, string> = {
  active:   '#ffd8d8',
  warning:  '#ffd0b8',
  clear:    '#8aa0b8',
  occupied: '#b89898',
};

export const SHORT_LABEL_UK: Record<string, string> = {
  crimea: 'Крим',
  volyn: 'Волинська',
  vinnytsia: 'Вінницька',
  dnipro: 'Дніпропетровська',
  donetsk: 'Донецька',
  zhytomyr: 'Житомирська',
  zakarpattia: 'Закарпатська',
  zaporizhzhia: 'Запорізька',
  'ivano-frankivsk': 'Івано-Франківська',
  'kyiv-oblast': 'Київська',
  kirovohrad: 'Кіровоградська',
  luhansk: 'Луганська',
  lviv: 'Львівська',
  mykolaiv: 'Миколаївська',
  odesa: 'Одеська',
  poltava: 'Полтавська',
  rivne: 'Рівненська',
  sumy: 'Сумська',
  ternopil: 'Тернопільська',
  kharkiv: 'Харківська',
  kherson: 'Херсонська',
  khmelnytskyi: 'Хмельницька',
  cherkasy: 'Черкаська',
  chernivtsi: 'Чернівецька',
  chernihiv: 'Чернігівська',
  'kyiv-city': 'м. Київ',
};

export const KYIV_CITY_COORDS: [number, number] = [30.52, 50.45];

/** Offset threat icons from oblast centroid (lon, lat) */
export const THREAT_ICON_OFFSET: Record<string, [number, number]> = {
  zaporizhzhia: [0.4, -0.15],
  luhansk: [0.5, 0.1],
  donetsk: [0.3, 0.05],
  kharkiv: [0.35, 0.05],
  dnipro: [0.2, -0.1],
};

export function labelColor(slug: string, status: string): string {
  if (status === 'active' || status === 'warning') {
    return STATUS_LABEL_FILL[status];
  }
  return LABEL_COLOR_BY_SLUG[slug] ?? STATUS_LABEL_FILL.clear;
}
