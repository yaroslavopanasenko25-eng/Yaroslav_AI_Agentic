import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppSettings } from '../App';
import type { Region } from '../types';
import UkraineMap from './UkraineMap';

const FALLBACK_REGIONS: Region[] = [
  { id: 'vinnytsia',       nameUk: 'Вінницька',         nameEn: 'Vinnytsia',        status: 'clear'    },
  { id: 'volyn',           nameUk: 'Волинська',          nameEn: 'Volyn',            status: 'clear'    },
  { id: 'dnipro',          nameUk: 'Дніпропетровська',  nameEn: 'Dnipropetrovsk',   status: 'warning'  },
  { id: 'donetsk',         nameUk: 'Донецька',           nameEn: 'Donetsk',          status: 'active'   },
  { id: 'zhytomyr',        nameUk: 'Житомирська',        nameEn: 'Zhytomyr',         status: 'clear'    },
  { id: 'zakarpattia',     nameUk: 'Закарпатська',       nameEn: 'Zakarpattia',      status: 'clear'    },
  { id: 'zaporizhzhia',    nameUk: 'Запорізька',         nameEn: 'Zaporizhzhia',     status: 'active'   },
  { id: 'ivano-frankivsk', nameUk: 'Івано-Франківська',  nameEn: 'Ivano-Frankivsk',  status: 'clear'    },
  { id: 'kyiv-oblast',     nameUk: 'Київська',           nameEn: 'Kyiv Oblast',      status: 'warning'  },
  { id: 'kirovohrad',      nameUk: 'Кіровоградська',    nameEn: 'Kirovohrad',       status: 'clear'    },
  { id: 'luhansk',         nameUk: 'Луганська',          nameEn: 'Luhansk',          status: 'occupied' },
  { id: 'lviv',            nameUk: 'Львівська',          nameEn: 'Lviv',             status: 'clear'    },
  { id: 'mykolaiv',        nameUk: 'Миколаївська',       nameEn: 'Mykolaiv',         status: 'clear'    },
  { id: 'odesa',           nameUk: 'Одеська',            nameEn: 'Odesa',            status: 'clear'    },
  { id: 'poltava',         nameUk: 'Полтавська',         nameEn: 'Poltava',          status: 'clear'    },
  { id: 'rivne',           nameUk: 'Рівненська',         nameEn: 'Rivne',            status: 'clear'    },
  { id: 'sumy',            nameUk: 'Сумська',            nameEn: 'Sumy',             status: 'active'   },
  { id: 'ternopil',        nameUk: 'Тернопільська',      nameEn: 'Ternopil',         status: 'clear'    },
  { id: 'kharkiv',         nameUk: 'Харківська',         nameEn: 'Kharkiv',          status: 'active'   },
  { id: 'kherson',         nameUk: 'Херсонська',         nameEn: 'Kherson',          status: 'warning'  },
  { id: 'khmelnytskyi',    nameUk: 'Хмельницька',        nameEn: 'Khmelnytskyi',     status: 'clear'    },
  { id: 'cherkasy',        nameUk: 'Черкаська',          nameEn: 'Cherkasy',         status: 'clear'    },
  { id: 'chernivtsi',      nameUk: 'Чернівецька',        nameEn: 'Chernivtsi',       status: 'clear'    },
  { id: 'chernihiv',       nameUk: 'Чернігівська',       nameEn: 'Chernihiv',        status: 'warning'  },
  { id: 'kyiv-city',       nameUk: 'м. Київ',            nameEn: 'Kyiv City',        status: 'warning'  },
  { id: 'crimea',          nameUk: 'АР Крим',            nameEn: 'AR Crimea',        status: 'occupied' },
];

export default function Dashboard() {
  const { t } = useTranslation();
  const { language } = useAppSettings();
  const [regions, setRegions] = useState<Region[]>([]);
  const [updatedAt, setUpdatedAt] = useState('');

  useEffect(() => {
    fetch('/api/regions')
      .then(r => r.json())
      .then(data => {
        setRegions(data.regions);
        setUpdatedAt(new Date(data.updatedAt).toLocaleTimeString(
          language === 'uk' ? 'uk-UA' : 'en-US',
          { hour: '2-digit', minute: '2-digit' },
        ));
      })
      .catch(() => {
        setRegions(FALLBACK_REGIONS);
        setUpdatedAt(new Date().toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' }));
      });
  }, [language]);

  const active  = regions.filter(r => r.status === 'active').length;
  const warning = regions.filter(r => r.status === 'warning').length;

  return (
    <div className="dashboard-fullpage">
      <div className="glass-card dashboard-map-card">
        {/* Floating header */}
        <div className="dashboard-overlay-header">
          <div>
            <div className="dashboard-map-title">{t('ukraineAlarmMap')}</div>
            <div className="dashboard-map-time">{t('lastUpdated')}: {updatedAt || '—'}</div>
          </div>
          <div style={{ display: 'flex', gap: 6 }}>
            {active > 0 && (
              <span className="status-badge active">
                <span className="dot" />
                {active} {language === 'uk' ? 'тривог' : 'alarms'}
              </span>
            )}
            {warning > 0 && (
              <span className="status-badge warning">
                {warning} {language === 'uk' ? 'попереджень' : 'warnings'}
              </span>
            )}
          </div>
        </div>

        {/* Map fills card */}
        <UkraineMap regions={regions} language={language} />

        {/* Legend */}
        <div className="map-legend">
          <div className="legend-item"><span className="legend-dot active" />{language === 'uk' ? 'Тривога' : 'Alarm'}</div>
          <div className="legend-item"><span className="legend-dot warning" />{language === 'uk' ? 'Попередження' : 'Warning'}</div>
          <div className="legend-item"><span className="legend-dot clear" />{language === 'uk' ? 'Спокійно' : 'Clear'}</div>
          <div className="legend-item"><span className="legend-dot occupied" />{language === 'uk' ? 'Окуповано' : 'Occupied'}</div>
        </div>

        <div className="map-timestamp">map.ukrainealarm.com · {updatedAt}</div>
      </div>
    </div>
  );
}
