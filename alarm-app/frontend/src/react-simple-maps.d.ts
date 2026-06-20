declare module 'react-simple-maps' {
  import type { ComponentType, ReactNode, SVGProps, MouseEvent } from 'react';

  export interface ProjectionConfig {
    center?: [number, number];
    scale?: number;
    rotate?: [number, number, number];
    parallels?: [number, number];
    precision?: number;
  }

  export interface ComposableMapProps {
    projection?: string;
    projectionConfig?: ProjectionConfig;
    width?: number;
    height?: number;
    style?: React.CSSProperties;
    className?: string;
    children?: ReactNode;
  }

  export interface ZoomableGroupProps {
    center?: [number, number];
    zoom?: number;
    minZoom?: number;
    maxZoom?: number;
    translateExtent?: [[number, number], [number, number]];
    onMoveStart?: (event: unknown) => void;
    onMove?: (event: unknown) => void;
    onMoveEnd?: (event: unknown) => void;
    children?: ReactNode;
  }

  export interface GeographyProps extends SVGProps<SVGPathElement> {
    geography: GeoFeature;
    style?: {
      default?: React.CSSProperties;
      hover?: React.CSSProperties;
      pressed?: React.CSSProperties;
    };
    onMouseEnter?: (event: React.MouseEvent<SVGPathElement>) => void;
    onMouseLeave?: (event: React.MouseEvent<SVGPathElement>) => void;
    onClick?: (event: React.MouseEvent<SVGPathElement>) => void;
  }

  export interface GeoFeature {
    rsmKey: string;
    properties: Record<string, string | number>;
    type: string;
    geometry: unknown;
  }

  export interface GeographiesChildProps {
    geographies: GeoFeature[];
    outline: unknown;
    borders: unknown;
  }

  export interface GeographiesProps {
    geography: string | object;
    children: (props: GeographiesChildProps) => ReactNode;
  }

  export interface MarkerProps {
    coordinates: [number, number];
    children?: ReactNode;
    style?: React.CSSProperties;
  }

  export const ComposableMap: ComponentType<ComposableMapProps>;
  export const ZoomableGroup: ComponentType<ZoomableGroupProps>;
  export const Geographies: ComponentType<GeographiesProps>;
  export const Geography: ComponentType<GeographyProps>;
  export const Marker: ComponentType<MarkerProps>;
  export const Annotation: ComponentType<unknown>;
  export const Graticule: ComponentType<unknown>;
  export const Sphere: ComponentType<unknown>;
}
