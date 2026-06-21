import { useAppSettings } from '../App';

const MAP_URL_UK = 'https://alerts.in.ua/';
const MAP_URL_EN = 'https://alerts.in.ua/en';

export default function Dashboard() {
  const { language } = useAppSettings();
  const mapUrl = language === 'en' ? MAP_URL_EN : MAP_URL_UK;

  return (
    <div className="dashboard-fullpage">
      <div className="dashboard-map-card dashboard-embed-card">
        <iframe
          src={mapUrl}
          title="alerts.in.ua — карта тривог України"
          className="alerts-in-ua-iframe"
          allow="fullscreen"
          referrerPolicy="no-referrer-when-downgrade"
        />
        <a
          className="alerts-in-ua-link"
          href={mapUrl}
          target="_blank"
          rel="noopener noreferrer"
        >
          alerts.in.ua ↗
        </a>
      </div>
    </div>
  );
}
