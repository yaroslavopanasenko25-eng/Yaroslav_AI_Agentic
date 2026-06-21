import { useState, useCallback, useMemo, useEffect } from 'react';
import { geoMercator, geoPath, geoCentroid } from 'd3-geo';
import type { FeatureCollection, Feature, Geometry } from 'geojson';
import type { Region, MapThreat } from '../types';
import {
  GEO_REGION_TO_SLUG,
  STATUS_FILL,
  SHORT_LABEL_UK,
  KYIV_CITY_COORDS,
  THREAT_ICON_OFFSET,
  labelColor,
} from './ukraineOblastMap';

const GEO_URL = '/ukraine-oblasts.geojson';
const MAP_W = 900;
const MAP_H = 580;
const BORDER = '#8aa0bc';

interface Props {
  regions: Region[];
  threats?: MapThreat[];
  language: 'uk' | 'en';
}

interface TooltipState {
  visible: boolean;
  x: number;
  y: number;
  name: string;
  status: string;
}

const STATUS_LABEL_UK: Record<string, string> = {
  active: 'Тривога', warning: 'Часткова', clear: 'Спокійно', occupied: 'Окуповано',
};
const STATUS_LABEL_EN: Record<string, string> = {
  active: 'Alarm', warning: 'Partial', clear: 'Clear', occupied: 'Occupied',
};

const PAINT_ORDER: Record<string, number> = {
  clear: 0, warning: 1, active: 2, occupied: 3,
};

function ThreatIcon({ x, y, type }: { x: number; y: number; type: string }) {
  return (
    <g transform={`translate(${x},${y})`}>
      <circle r={6} fill="#e88830" stroke="#ffcc66" strokeWidth={1} />
      <text textAnchor="middle" y={3} fontSize={7} fill="#fff" pointerEvents="none">
        {type.includes('artillery') ? '💥' : '⚠'}
      </text>
    </g>
  );
}

export default function UkraineMap({ regions, threats = [], language }: Props) {
  const [geoData, setGeoData] = useState<FeatureCollection | null>(null);
  const [tooltip, setTooltip] = useState<TooltipState>({
    visible: false, x: 0, y: 0, name: '', status: '',
  });
  const [hoveredSlug, setHoveredSlug] = useState<string | null>(null);

  useEffect(() => {
    fetch(GEO_URL)
      .then(r => r.json())
      .then((data: FeatureCollection) => setGeoData(data))
      .catch(() => setGeoData(null));
  }, []);

  const regionBySlug = useMemo(
    () => Object.fromEntries(regions.map(r => [r.id, r])),
    [regions],
  );

  const threatBySlug = useMemo(
    () => Object.fromEntries(threats.map(t => [t.slug, t])),
    [threats],
  );

  const getStatus = useCallback(
    (slug: string): string => {
      const s = regionBySlug[slug]?.status;
      if (s === 'active' || s === 'warning' || s === 'clear' || s === 'occupied') return s;
      return 'clear';
    },
    [regionBySlug],
  );

  const { projection, pathGen } = useMemo(() => {
    const p = geoMercator();
    if (geoData) p.fitSize([MAP_W, MAP_H], geoData);
    return { projection: p, pathGen: geoPath().projection(p) };
  }, [geoData]);

  const features = useMemo(() => {
    if (!geoData) return [];
    return geoData.features
      .map(f => {
        const name = String(f.properties?.region ?? '');
        const slug = GEO_REGION_TO_SLUG[name];
        if (!slug) return null;
        const status = getStatus(slug);
        const d = pathGen(f as Feature<Geometry>);
        if (!d) return null;
        const c = geoCentroid(f as Feature<Geometry>);
        const pt = projection(c);
        return { slug, status, d, labelPt: pt, feature: f };
      })
      .filter(Boolean)
      .sort((a, b) => (PAINT_ORDER[a!.status] ?? 0) - (PAINT_ORDER[b!.status] ?? 0)) as Array<{
        slug: string; status: string; d: string;
        labelPt: [number, number] | null; feature: Feature;
      }>;
  }, [geoData, pathGen, projection, getStatus]);

  const showTooltip = (slug: string, evt: React.MouseEvent) => {
    const region = regionBySlug[slug];
    if (!region) return;
    const level = region.level;
    const base = language === 'uk' ? STATUS_LABEL_UK[region.status] : STATUS_LABEL_EN[region.status];
    setTooltip({
      visible: true,
      x: evt.clientX + 12,
      y: evt.clientY - 10,
      name: language === 'uk' ? region.nameUk : region.nameEn,
      status: level && level !== 'N' ? `${base} (${level})` : base,
    });
  };

  const kyivCity = regionBySlug['kyiv-city'];
  const kyivPt = projection(KYIV_CITY_COORDS);

  if (regions.length === 0 || !geoData) {
    return (
      <div className="ukraine-map-wrap oblast-map map-loading">
        {language === 'uk' ? 'Завантаження карти…' : 'Loading map…'}
      </div>
    );
  }

  return (
    <div className="ukraine-map-wrap oblast-map" onMouseMove={e => {
      if (tooltip.visible) setTooltip(prev => ({ ...prev, x: e.clientX + 12, y: e.clientY - 10 }));
    }}>
      <svg
        viewBox={`0 0 ${MAP_W} ${MAP_H}`}
        className="ukraine-svg-map"
        role="img"
        aria-label={language === 'uk' ? 'Карта тривог України' : 'Ukraine alarm map'}
      >
        {/* Dark sea background — NOT red */}
        <rect x={0} y={0} width={MAP_W} height={MAP_H} fill="#0a1018" />

        {features.map(({ slug, status, d }) => {
          const fill = STATUS_FILL[status] ?? STATUS_FILL.clear;
          const isHovered = hoveredSlug === slug;
          return (
            <path
              key={slug}
              d={d}
              fill={fill}
              stroke={isHovered ? '#c8d8f0' : BORDER}
              strokeWidth={isHovered ? 1.2 : 0.85}
              strokeLinejoin="round"
              style={{ cursor: 'pointer', transition: 'fill 0.3s ease' }}
              onMouseEnter={e => { setHoveredSlug(slug); showTooltip(slug, e); }}
              onMouseLeave={() => { setHoveredSlug(null); setTooltip(prev => ({ ...prev, visible: false })); }}
            />
          );
        })}

        {features.map(({ slug, status, labelPt }) => {
          if (!labelPt) return null;
          const label = language === 'uk' ? SHORT_LABEL_UK[slug] : (regionBySlug[slug]?.nameEn ?? slug);
          return (
            <text
              key={`lbl-${slug}`}
              x={labelPt[0]}
              y={labelPt[1]}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize={slug === 'crimea' ? 8 : 9}
              fontWeight={500}
              fill={labelColor(slug, status)}
              pointerEvents="none"
              fontFamily="Segoe UI, system-ui, sans-serif"
            >
              {label}
            </text>
          );
        })}

        {features.map(({ slug, labelPt }) => {
          const threat = threatBySlug[slug];
          if (!threat || !labelPt) return null;
          const off = THREAT_ICON_OFFSET[slug] ?? [0, 0];
          const px = projection([labelPt[0], labelPt[1]]);
          // labelPt is already projected; apply offset in screen space
          return (
            <ThreatIcon
              key={`threat-${slug}`}
              x={labelPt[0] + off[0] * 8}
              y={labelPt[1] + off[1] * 8}
              type={threat.type}
            />
          );
        })}

        {kyivCity && kyivPt && (
          <g
            style={{ cursor: 'pointer' }}
            onMouseEnter={e => showTooltip('kyiv-city', e)}
            onMouseLeave={() => setTooltip(prev => ({ ...prev, visible: false }))}
          >
            <circle
              cx={kyivPt[0]}
              cy={kyivPt[1]}
              r={6}
              fill={STATUS_FILL[kyivCity.status]}
              stroke={BORDER}
              strokeWidth={1}
            />
            <text
              x={kyivPt[0]}
              y={kyivPt[1] - 10}
              textAnchor="middle"
              fontSize={8}
              fill={labelColor('kyiv-city', kyivCity.status)}
              pointerEvents="none"
            >
              {language === 'uk' ? 'м. Київ' : 'Kyiv'}
            </text>
          </g>
        )}
      </svg>

      {tooltip.visible && (
        <div className="region-tooltip" style={{ left: tooltip.x, top: tooltip.y, position: 'fixed' }}>
          <strong>{tooltip.name}</strong>
          <span style={{ marginLeft: 8, opacity: 0.75, fontSize: 12 }}>{tooltip.status}</span>
        </div>
      )}
    </div>
  );
}
