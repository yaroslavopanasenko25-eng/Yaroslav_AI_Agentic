import { useState, useCallback } from 'react';
import { ComposableMap, Geographies, Geography, Marker } from 'react-simple-maps';
import type { Region } from '../types';

const GEO_URL = '/countries.geojson';

const STATUS_COLOR: Record<string, string> = {
  active:   '#FF453A',
  warning:  '#FF9F0A',
  clear:    '#2a2a3e',
  occupied: '#3d3d55',
};

interface Props {
  regions: Region[];
  language: 'uk' | 'en';
}

interface TooltipState {
  visible: boolean;
  x: number;
  y: number;
  name: string;
  status: string;
}

// Region center coordinates [lon, lat] for Ukraine oblasts
const REGION_CENTERS: Record<string, [number, number]> = {
  'vinnytsia':       [28.47, 49.23],
  'volyn':           [24.42, 51.24],
  'dnipro':          [35.04, 48.46],
  'donetsk':         [37.80, 48.01],
  'zhytomyr':        [28.66, 50.25],
  'zakarpattia':     [22.29, 48.62],
  'zaporizhzhia':    [35.18, 47.84],
  'ivano-frankivsk': [24.71, 48.92],
  'kyiv-oblast':     [31.00, 50.30],
  'kirovohrad':      [32.26, 48.51],
  'luhansk':         [39.33, 48.57],
  'lviv':            [23.99, 49.84],
  'mykolaiv':        [31.99, 46.97],
  'odesa':           [30.73, 46.48],
  'poltava':         [34.55, 49.59],
  'rivne':           [26.25, 50.62],
  'sumy':            [34.80, 51.00],
  'ternopil':        [25.59, 49.55],
  'kharkiv':         [36.23, 49.99],
  'kherson':         [33.22, 46.64],
  'khmelnytskyi':    [26.99, 49.42],
  'cherkasy':        [32.06, 49.44],
  'chernivtsi':      [25.93, 48.29],
  'chernihiv':       [31.30, 51.49],
  'kyiv-city':       [30.52, 50.45],
  'crimea':          [34.10, 45.30],
};

const STATUS_LABEL_UK: Record<string, string> = {
  active:   '🔴 Тривога',
  warning:  '🟠 Попередження',
  clear:    '🟢 Спокійно',
  occupied: '⚫ Окуповано',
};
const STATUS_LABEL_EN: Record<string, string> = {
  active:   '🔴 Alarm',
  warning:  '🟠 Warning',
  clear:    '🟢 Clear',
  occupied: '⚫ Occupied',
};

const MARKER_SIZE: Record<string, number> = {
  active: 7, warning: 6, clear: 5, occupied: 4,
};

export default function UkraineMap({ regions, language }: Props) {
  const [tooltip, setTooltip] = useState<TooltipState>({
    visible: false, x: 0, y: 0, name: '', status: '',
  });

  const getRegionData = useCallback(
    (id: string) => regions.find(r => r.id === id),
    [regions],
  );

  const handleMouseMove = useCallback((evt: React.MouseEvent) => {
    setTooltip(prev =>
      prev.visible ? { ...prev, x: evt.clientX + 12, y: evt.clientY - 10 } : prev,
    );
  }, []);

  return (
    <div className="ukraine-map-wrap" onMouseMove={handleMouseMove}>
      <ComposableMap
        projection="geoMercator"
        projectionConfig={{ center: [31.5, 48.5], scale: 2600 }}
        style={{ width: '100%', height: '100%' }}
      >
        <Geographies geography={GEO_URL}>
          {({ geographies }) =>
            geographies
              .filter(geo => geo.properties.ADMIN === 'Ukraine' || geo.properties.name === 'Ukraine')
              .map(geo => (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill="rgba(40,40,60,0.9)"
                  stroke="rgba(100,100,160,0.4)"
                  strokeWidth={0.8}
                  style={{
                    default: { outline: 'none' },
                    hover:   { outline: 'none' },
                    pressed: { outline: 'none' },
                  }}
                />
              ))
          }
        </Geographies>

        {/* Region markers */}
        {Object.entries(REGION_CENTERS).map(([id, coords]) => {
          const region = getRegionData(id);
          if (!region) return null;
          const color = STATUS_COLOR[region.status];
          const size = MARKER_SIZE[region.status] || 5;
          const name = language === 'uk' ? region.nameUk : region.nameEn;
          const statusLabel = language === 'uk'
            ? STATUS_LABEL_UK[region.status]
            : STATUS_LABEL_EN[region.status];

          return (
            <Marker
              key={id}
              coordinates={coords}
            >
              <circle
                r={size}
                fill={color}
                fillOpacity={region.status === 'active' ? 0.9 : 0.75}
                stroke="rgba(255,255,255,0.3)"
                strokeWidth={1}
                style={{
                  cursor: 'pointer',
                  filter: region.status === 'active' ? `drop-shadow(0 0 6px ${color})` : 'none',
                }}
                onMouseEnter={e => setTooltip({
                  visible: true,
                  x: (e as React.MouseEvent).clientX + 12,
                  y: (e as React.MouseEvent).clientY - 10,
                  name,
                  status: statusLabel,
                })}
                onMouseLeave={() => setTooltip(prev => ({ ...prev, visible: false }))}
              />
              {region.status === 'active' && (
                <circle
                  r={size + 3}
                  fill="none"
                  stroke={color}
                  strokeWidth={1.5}
                  strokeOpacity={0.5}
                  style={{ animation: 'alarmRing 2s ease-out infinite', pointerEvents: 'none' }}
                />
              )}
            </Marker>
          );
        })}
      </ComposableMap>

      {tooltip.visible && (
        <div
          className="region-tooltip"
          style={{ left: tooltip.x, top: tooltip.y, position: 'fixed' }}
        >
          <strong>{tooltip.name}</strong>
          <span style={{ marginLeft: 8, opacity: 0.8, fontSize: '12px' }}>
            {tooltip.status}
          </span>
        </div>
      )}

      <style>{`
        @keyframes alarmRing {
          0%   { r: 7px; opacity: 0.8; }
          100% { r: 18px; opacity: 0; }
        }
      `}</style>
    </div>
  );
}
