import { useState, useEffect, useRef } from 'react';
import { MapContainer, Marker, Popup, ZoomControl, Polyline, useMap } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import L from 'leaflet';
import { useTranslation } from 'react-i18next';
import { useAppSettings } from '../App';
import type { Shelter } from '../types';
import 'leaflet/dist/leaflet.css';

// Fix leaflet default icon
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl:       'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl:     'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const SHELTER_ICON = L.divIcon({
  html: `<div style="width:32px;height:32px;background:rgba(10,132,255,0.9);border-radius:50%;border:2.5px solid rgba(255,255,255,0.9);display:flex;align-items:center;justify-content:center;font-size:15px;box-shadow:0 2px 12px rgba(10,132,255,0.5),0 0 0 4px rgba(10,132,255,0.15)">🛡️</div>`,
  className: '',
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

const USER_ICON = L.divIcon({
  html: `<div style="width:18px;height:18px;background:#0A84FF;border-radius:50%;border:3px solid #fff;box-shadow:0 0 0 5px rgba(10,132,255,0.25)"></div>`,
  className: '',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

// ── Tile layers ───────────────────────────────────────────────────────────────
type TileMode = 'dark' | 'street' | 'satellite' | 'topo';

const TILES: Record<TileMode, { url: string; label: string; labelUk: string; attribution: string }> = {
  dark: {
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    label: 'Dark', labelUk: 'Темна',
    attribution: '&copy; CartoDB',
  },
  street: {
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    label: 'Street', labelUk: 'Вулиці',
    attribution: '&copy; OpenStreetMap',
  },
  satellite: {
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    label: 'Satellite', labelUk: 'Супутник',
    attribution: '&copy; Esri',
  },
  topo: {
    url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    label: 'Topo', labelUk: 'Топо',
    attribution: '&copy; OpenTopoMap',
  },
};

// Imperatively swap tile layer when tileMode changes
function TileLayerSwitcher({ mode }: { mode: TileMode }) {
  const map = useMap();
  const layerRef = useRef<L.TileLayer | null>(null);

  useEffect(() => {
    if (layerRef.current) {
      map.removeLayer(layerRef.current);
    }
    const t = TILES[mode];
    layerRef.current = L.tileLayer(t.url, { attribution: t.attribution, maxZoom: 19 });
    layerRef.current.addTo(map);
  }, [mode, map]);

  return null;
}

// ── Mock shelters ─────────────────────────────────────────────────────────────
const MOCK_SHELTERS: Shelter[] = [
  { id:'s1',  nameUk:'Метро Хрещатик',      nameEn:'Khreshchatyk Metro',    lat:50.4482, lng:30.5234, city:'Kyiv',         capacity:2000, type:'metro'       },
  { id:'s2',  nameUk:'Метро Арсенальна',     nameEn:'Arsenalna Metro',       lat:50.4503, lng:30.5427, city:'Kyiv',         capacity:1500, type:'metro'       },
  { id:'s3',  nameUk:'Бомбосховище ЖК',      nameEn:'Residential Shelter',   lat:50.4511, lng:30.5191, city:'Kyiv',         capacity:200,  type:'bomb_shelter'},
  { id:'s4',  nameUk:'Бомбосховище №12',     nameEn:'Bomb Shelter #12',      lat:49.9935, lng:36.2304, city:'Kharkiv',      capacity:500,  type:'bomb_shelter'},
  { id:'s5',  nameUk:'Метро Університет',    nameEn:'Universytet Metro',     lat:49.9972, lng:36.2354, city:'Kharkiv',      capacity:1200, type:'metro'       },
  { id:'s6',  nameUk:'Паркінг ТРЦ Магнус',  nameEn:'Magnus Mall Parking',   lat:48.4659, lng:35.0435, city:'Dnipro',       capacity:800,  type:'basement'    },
  { id:'s7',  nameUk:'Оперний театр',        nameEn:'Opera House',           lat:49.8397, lng:24.0297, city:'Lviv',         capacity:600,  type:'bomb_shelter'},
  { id:'s8',  nameUk:'Підвал міської ради',  nameEn:'City Council Basement', lat:47.8388, lng:35.1396, city:'Zaporizhzhia', capacity:350,  type:'basement'    },
  { id:'s9',  nameUk:'Укриття вокзалу',      nameEn:'Train Station Shelter', lat:46.4854, lng:30.7327, city:'Odesa',        capacity:1000, type:'bomb_shelter'},
  { id:'s10', nameUk:'Підземний перехід',    nameEn:'Underground Passage',   lat:49.5904, lng:34.5401, city:'Poltava',      capacity:400,  type:'basement'    },
];

const TIPS = {
  alarm: [
    { id:'a1', icon:'🏃', titleUk:'Негайно йдіть до укриття',   titleEn:'Go to shelter immediately', descUk:'Якщо оголошено тривогу — перейдіть до найближчого бомбосховища або підвалу.', descEn:'If an alarm sounds, proceed to the nearest bomb shelter or basement.' },
    { id:'a2', icon:'🪟', titleUk:'Тримайтеся від вікон',        titleEn:'Stay away from windows',    descUk:'Не стійте біля вікон. Ударна хвиля може розбити скло і поранити.', descEn:'Stay away from windows. A blast wave can shatter glass and cause injury.' },
    { id:'a3', icon:'📱', titleUk:'Повідомте рідних',            titleEn:'Notify your family',        descUk:'Повідомте рідним де ви. Використовуйте месенджери, щоб не перевантажувати мережу.', descEn:'Let family know your location. Use messengers to keep the network free.' },
    { id:'a4', icon:'🧳', titleUk:'Тривожна валіза',             titleEn:'Emergency bag',             descUk:'Документи, вода, ліки, ліхтарик, заряджений телефон — завжди готові.', descEn:'Documents, water, medicines, flashlight, charged phone — always ready.' },
  ],
  after: [
    { id:'p1', icon:'✅', titleUk:'Дочекайтеся відбою',           titleEn:'Wait for all-clear',       descUk:'Не виходьте до офіційного відбою. Загроза може тривати.', descEn:'Do not leave until the official all-clear. The threat may continue.' },
    { id:'p2', icon:'🔍', titleUk:'Перевірте оточення',           titleEn:'Check surroundings',       descUk:'Огляньте приміщення. Не торкайтеся підозрілих предметів.', descEn:'Inspect the premises. Do not touch suspicious objects.' },
    { id:'p3', icon:'🆘', titleUk:'Дзвоніть 101/112 при потребі', titleEn:'Call 101/112 if needed',   descUk:'101 — пожежна, 103 — швидка, 112 — єдина екстрена допомога.', descEn:'101 — fire, 103 — ambulance, 112 — unified emergency service.' },
  ],
  general: [
    { id:'g1', icon:'💊', titleUk:'Аптечка першої допомоги',      titleEn:'First aid kit',            descUk:'Бинти, джгути, знеболювальне, антисептик, серцеві ліки.', descEn:'Bandages, tourniquets, painkillers, antiseptic, heart medications.' },
    { id:'g2', icon:'💧', titleUk:'Запас води та їжі',            titleEn:'Water & food supply',      descUk:'3 л/добу на людину на 3–5 днів. Консерви та сухарі.', descEn:'3L/day per person for 3–5 days. Canned goods and crackers.' },
    { id:'g3', icon:'🔦', titleUk:'Автономне живлення',           titleEn:'Backup power',             descUk:'Павербанк, ліхтарик, резервна зарядка. Завжди заряджені.', descEn:'Powerbank, flashlight, backup charger. Always charged.' },
    { id:'g4', icon:'📋', titleUk:'Документи під рукою',          titleEn:'Documents at hand',        descUk:'Паспорт і медичні довідки у водонепроникному пакеті.', descEn:'Passport and medical records in a waterproof bag.' },
  ],
};

export default function Safety() {
  const { t } = useTranslation();
  const { language } = useAppSettings();
  const [shelters, setShelters] = useState<Shelter[]>([]);
  const [tileMode, setTileMode] = useState<TileMode>('dark');
  const [userLocation, setUserLocation] = useState<[number, number] | null>(null);
  const [routeTarget, setRouteTarget] = useState<Shelter | null>(null);
  const [locating, setLocating] = useState(false);

  useEffect(() => {
    fetch('/shelters.json')
      .then(r => r.json())
      .then((data: Shelter[]) => setShelters(data))
      .catch(() => setShelters(MOCK_SHELTERS));
  }, []);

  const locateUser = () => {
    if (!navigator.geolocation) return;
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      pos => {
        setUserLocation([pos.coords.latitude, pos.coords.longitude]);
        setLocating(false);
      },
      () => setLocating(false),
      { timeout: 8000 },
    );
  };

  const openDirections = (shelter: Shelter) => {
    const origin = userLocation ? `${userLocation[0]},${userLocation[1]}` : '';
    const dest = `${shelter.lat},${shelter.lng}`;
    const url = origin
      ? `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${dest}`
      : `https://www.google.com/maps/search/?api=1&query=${dest}`;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  const typeLabel = (shelter: Shelter) => {
    if (shelter.kind) return shelter.kind;
    return language === 'uk'
      ? ({ metro:'Метро', basement:'Підвал', bomb_shelter:'Бомбосховище' }[shelter.type] || shelter.type)
      : ({ metro:'Metro', basement:'Basement', bomb_shelter:'Bomb Shelter' }[shelter.type] || shelter.type);
  };

  const renderTips = (tips: typeof TIPS.alarm, label: string) => (
    <div className="tips-section">
      <div className="tips-category-label">{label}</div>
      <div className="tips-grid">
        {tips.map(tip => (
          <div key={tip.id} className="glass-card tip-card">
            <div className="tip-icon">{tip.icon}</div>
            <div className="tip-content">
              <div className="tip-title">{language === 'uk' ? tip.titleUk : tip.titleEn}</div>
              <div className="tip-desc">{language === 'uk' ? tip.descUk : tip.descEn}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="page safety-page">
      <div className="safety-layout">
        {/* Left: title + tips */}
        <div className="safety-tips-col">
          <div className="safety-tips-header">
            <h1 className="page-title">{t('safety')}</h1>
            <p className="page-subtitle">{language === 'uk' ? 'Правила безпеки та карта укриттів' : 'Safety rules and shelter map'}</p>
          </div>
          {renderTips(TIPS.alarm,   t('duringAlarm'))}
          {renderTips(TIPS.after,   t('afterAlarm'))}
          {renderTips(TIPS.general, t('general'))}
        </div>

        {/* Right: map — no gap above card */}
        <div className="glass-card safety-map-col">
          {/* Map header */}
          <div className="shelter-map-header">
            <span className="section-title" style={{ padding: 0, marginBottom: 0 }}>{t('shelterMap')}</span>
            <div className="shelter-map-controls">
              {/* Tile switcher */}
              <div className="tile-switcher">
                {(Object.keys(TILES) as TileMode[]).map(mode => (
                  <button
                    key={mode}
                    className={`tile-btn${tileMode === mode ? ' active' : ''}`}
                    onClick={() => setTileMode(mode)}
                  >
                    {language === 'uk' ? TILES[mode].labelUk : TILES[mode].label}
                  </button>
                ))}
              </div>
              {/* Locate me button */}
              <button className="locate-btn" onClick={locateUser} disabled={locating} title={language === 'uk' ? 'Моє місцезнаходження' : 'My location'}>
                {locating ? '…' : '📍'}
              </button>
            </div>
          </div>

          {/* Map */}
          <div className="shelter-map-wrap">
            <MapContainer
              center={[49.0, 31.0]}
              zoom={6}
              style={{ height: '100%', width: '100%' }}
              zoomControl={false}
              attributionControl={false}
            >
              <TileLayerSwitcher mode={tileMode} />
              <ZoomControl position="bottomright" />

              {/* Clustered shelter markers */}
              <MarkerClusterGroup
                chunkedLoading
                maxClusterRadius={60}
                showCoverageOnHover={false}
              >
                {shelters.map(shelter => (
                  <Marker key={shelter.id} position={[shelter.lat, shelter.lng]} icon={SHELTER_ICON}>
                    <Popup className="shelter-popup">
                      <div className="shelter-popup-inner">
                        <div className="shelter-popup-name">{language === 'uk' ? shelter.nameUk : (shelter.nameEn || shelter.nameUk)}</div>
                        <div className="shelter-popup-meta">{shelter.city} · {typeLabel(shelter)}</div>
                        {shelter.capacity ? (
                          <div className="shelter-popup-capacity">{t('capacity')}: <strong>{shelter.capacity} {t('persons')}</strong></div>
                        ) : null}
                        <div className="shelter-popup-actions">
                          <button
                            className="shelter-route-btn"
                            onClick={() => { setRouteTarget(shelter); locateUser(); }}
                          >
                            {language === 'uk' ? '🗺 Маршрут' : '🗺 Route'}
                          </button>
                          <button
                            className="shelter-directions-btn"
                            onClick={() => openDirections(shelter)}
                          >
                            {language === 'uk' ? '↗ Відкрити' : '↗ Open Maps'}
                          </button>
                        </div>
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MarkerClusterGroup>

              {/* User location */}
              {userLocation && (
                <Marker position={userLocation} icon={USER_ICON}>
                  <Popup>{language === 'uk' ? 'Ви тут' : 'You are here'}</Popup>
                </Marker>
              )}

              {/* Route line */}
              {userLocation && routeTarget && (
                <Polyline
                  positions={[userLocation, [routeTarget.lat, routeTarget.lng]]}
                  pathOptions={{
                    color: '#0A84FF',
                    weight: 3,
                    opacity: 0.85,
                    dashArray: '8 6',
                  }}
                />
              )}
            </MapContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
