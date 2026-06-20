const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// ─── Mock Data ─────────────────────────────────────────────────────────────────

const REGIONS = [
  { id: 'vinnytsia',       nameUk: 'Вінницька',        nameEn: 'Vinnytsia',       status: 'clear' },
  { id: 'volyn',           nameUk: 'Волинська',         nameEn: 'Volyn',           status: 'clear' },
  { id: 'dnipro',          nameUk: 'Дніпропетровська', nameEn: 'Dnipropetrovsk',  status: 'warning' },
  { id: 'donetsk',         nameUk: 'Донецька',          nameEn: 'Donetsk',         status: 'active' },
  { id: 'zhytomyr',        nameUk: 'Житомирська',       nameEn: 'Zhytomyr',        status: 'clear' },
  { id: 'zakarpattia',     nameUk: 'Закарпатська',      nameEn: 'Zakarpattia',     status: 'clear' },
  { id: 'zaporizhzhia',    nameUk: 'Запорізька',        nameEn: 'Zaporizhzhia',    status: 'active' },
  { id: 'ivano-frankivsk', nameUk: 'Івано-Франківська', nameEn: 'Ivano-Frankivsk', status: 'clear' },
  { id: 'kyiv-oblast',     nameUk: 'Київська',          nameEn: 'Kyiv Oblast',     status: 'warning' },
  { id: 'kirovohrad',      nameUk: 'Кіровоградська',   nameEn: 'Kirovohrad',      status: 'clear' },
  { id: 'luhansk',         nameUk: 'Луганська',         nameEn: 'Luhansk',         status: 'occupied' },
  { id: 'lviv',            nameUk: 'Львівська',         nameEn: 'Lviv',            status: 'clear' },
  { id: 'mykolaiv',        nameUk: 'Миколаївська',      nameEn: 'Mykolaiv',        status: 'clear' },
  { id: 'odesa',           nameUk: 'Одеська',           nameEn: 'Odesa',           status: 'clear' },
  { id: 'poltava',         nameUk: 'Полтавська',        nameEn: 'Poltava',         status: 'clear' },
  { id: 'rivne',           nameUk: 'Рівненська',        nameEn: 'Rivne',           status: 'clear' },
  { id: 'sumy',            nameUk: 'Сумська',           nameEn: 'Sumy',            status: 'active' },
  { id: 'ternopil',        nameUk: 'Тернопільська',     nameEn: 'Ternopil',        status: 'clear' },
  { id: 'kharkiv',         nameUk: 'Харківська',        nameEn: 'Kharkiv',         status: 'active' },
  { id: 'kherson',         nameUk: 'Херсонська',        nameEn: 'Kherson',         status: 'warning' },
  { id: 'khmelnytskyi',    nameUk: 'Хмельницька',       nameEn: 'Khmelnytskyi',    status: 'clear' },
  { id: 'cherkasy',        nameUk: 'Черкаська',         nameEn: 'Cherkasy',        status: 'clear' },
  { id: 'chernivtsi',      nameUk: 'Чернівецька',       nameEn: 'Chernivtsi',      status: 'clear' },
  { id: 'chernihiv',       nameUk: 'Чернігівська',      nameEn: 'Chernihiv',       status: 'warning' },
  { id: 'kyiv-city',       nameUk: 'м. Київ',           nameEn: 'Kyiv City',       status: 'warning' },
  { id: 'crimea',          nameUk: 'АР Крим',           nameEn: 'AR Crimea',       status: 'occupied' },
];

const HISTORY = Array.from({ length: 14 }, (_, i) => {
  const date = new Date();
  date.setDate(date.getDate() - i);
  const dateStr = date.toISOString().split('T')[0];
  const alarmsCount = Math.floor(Math.random() * 8) + 1;
  const regions = REGIONS
    .filter(r => r.status !== 'occupied')
    .sort(() => Math.random() - 0.5)
    .slice(0, alarmsCount)
    .map(r => r.id);

  const missiles = { type: 'missiles', total: Math.floor(Math.random() * 20) + 2, destroyed: 0, hit: 0, lost: 0 };
  missiles.destroyed = Math.floor(missiles.total * (0.5 + Math.random() * 0.4));
  missiles.hit = Math.floor((missiles.total - missiles.destroyed) * 0.6);
  missiles.lost = missiles.total - missiles.destroyed - missiles.hit;

  const drones = { type: 'drones', total: Math.floor(Math.random() * 50) + 5, destroyed: 0, hit: 0, lost: 0 };
  drones.destroyed = Math.floor(drones.total * (0.6 + Math.random() * 0.3));
  drones.hit = Math.floor((drones.total - drones.destroyed) * 0.5);
  drones.lost = drones.total - drones.destroyed - drones.hit;

  return {
    id: `alarm-${i}`,
    date: dateStr,
    startTime: `${String(Math.floor(Math.random() * 24)).padStart(2,'0')}:${String(Math.floor(Math.random() * 60)).padStart(2,'0')}`,
    duration: Math.floor(Math.random() * 180) + 20,
    regions,
    threats: [missiles, drones],
  };
});

const SHELTERS = [
  { id: 's1',  nameUk: 'Укриття метро Хрещатик',    nameEn: 'Khreshchatyk Metro Shelter',   lat: 50.4482, lng: 30.5234, city: 'Kyiv',       capacity: 2000, type: 'metro' },
  { id: 's2',  nameUk: 'Укриття метро Арсенальна',   nameEn: 'Arsenalna Metro Shelter',       lat: 50.4503, lng: 30.5427, city: 'Kyiv',       capacity: 1500, type: 'metro' },
  { id: 's3',  nameUk: 'Підвал ЖК Центральний',      nameEn: 'Central Residential Basement',  lat: 50.4511, lng: 30.5191, city: 'Kyiv',       capacity: 200,  type: 'basement' },
  { id: 's4',  nameUk: 'Бомбосховище №12',            nameEn: 'Bomb Shelter #12',              lat: 49.9935, lng: 36.2304, city: 'Kharkiv',    capacity: 500,  type: 'bomb_shelter' },
  { id: 's5',  nameUk: 'Метро Університет Харків',    nameEn: 'Universytet Metro Kharkiv',     lat: 49.9972, lng: 36.2354, city: 'Kharkiv',    capacity: 1200, type: 'metro' },
  { id: 's6',  nameUk: 'Підземний паркінг ТРЦ Магнус',nameEn: 'Magnus Mall Underground',       lat: 48.4659, lng: 35.0435, city: 'Dnipro',     capacity: 800,  type: 'basement' },
  { id: 's7',  nameUk: 'Укриття Оперний театр',       nameEn: 'Opera House Shelter',           lat: 49.8397, lng: 24.0297, city: 'Lviv',       capacity: 600,  type: 'bomb_shelter' },
  { id: 's8',  nameUk: 'Підвал міської ради',         nameEn: 'City Council Basement',         lat: 47.8388, lng: 35.1396, city: 'Zaporizhzhia',capacity: 350, type: 'basement' },
  { id: 's9',  nameUk: 'Укриття вокзалу Одеса',       nameEn: 'Odesa Train Station Shelter',   lat: 46.4854, lng: 30.7327, city: 'Odesa',      capacity: 1000, type: 'bomb_shelter' },
  { id: 's10', nameUk: 'Підземний переход Захисний',  nameEn: 'Zakhysnyi Underground Passage', lat: 49.5904, lng: 34.5401, city: 'Poltava',    capacity: 400,  type: 'basement' },
];

const SAFETY_TIPS = {
  alarm: [
    { id: 'a1', icon: '🏃', titleUk: 'Негайно йдіть до укриття', titleEn: 'Go to shelter immediately', descUk: 'Якщо є повітряна тривога — негайно перейдіть до найближчого бомбосховища або підвалу.', descEn: 'If an air alarm sounds, immediately proceed to the nearest bomb shelter or basement.' },
    { id: 'a2', icon: '📵', titleUk: 'Тримайтеся подалі від вікон', titleEn: 'Stay away from windows', descUk: 'Не стійте біля вікон та скляних дверей. Ударна хвиля може розбити скло.', descEn: 'Do not stand near windows or glass doors. A blast wave can shatter glass.' },
    { id: 'a3', icon: '📱', titleUk: 'Повідомте рідних', titleEn: 'Notify your family', descUk: 'Повідомте близьким, де ви знаходитесь. Використовуйте месенджери для збереження ефіру.', descEn: 'Let your family know where you are. Use messengers to preserve call capacity.' },
    { id: 'a4', icon: '🧳', titleUk: 'Візьміть тривожну валізу', titleEn: 'Take your emergency bag', descUk: 'Документи, вода, ліки, ліхтарик, заряджений телефон. Тривожна валіза завжди готова.', descEn: 'Documents, water, medicines, flashlight, charged phone. Emergency bag always ready.' },
  ],
  after: [
    { id: 'p1', icon: '✅', titleUk: 'Дочекайтеся відбою', titleEn: 'Wait for the all-clear', descUk: 'Не виходьте до офіційного відбою тривоги. Загроза може тривати.', descEn: 'Do not leave until the official all-clear signal. The threat may continue.' },
    { id: 'p2', icon: '🔍', titleUk: 'Перевірте своє оточення', titleEn: 'Check your surroundings', descUk: 'Після відбою огляньте приміщення на предмет ушкоджень. Не торкайтеся підозрілих предметів.', descEn: 'After the all-clear, inspect the premises for damage. Do not touch suspicious objects.' },
    { id: 'p3', icon: '🆘', titleUk: 'Зателефонуйте 101/112 при потребі', titleEn: 'Call 101/112 if needed', descUk: 'При пожежі або травмах — одразу дзвоніть на 101 (пожежна) або 112 (екстрена служба).', descEn: 'In case of fire or injuries — immediately call 101 (fire) or 112 (emergency services).' },
  ],
  general: [
    { id: 'g1', icon: '💊', titleUk: 'Аптечка першої допомоги', titleEn: 'First aid kit', descUk: 'Завжди майте вдома аптечку: бинти, джгути, знеболювальне, антисептик, серцеві ліки.', descEn: 'Always have a first aid kit: bandages, tourniquets, painkillers, antiseptic, heart medications.' },
    { id: 'g2', icon: '💧', titleUk: 'Запас води та їжі', titleEn: 'Water and food supply', descUk: 'Зберігайте запас питної води на 3–5 днів (3 л/добу на людину) та консерви/сухарі.', descEn: 'Store drinking water for 3–5 days (3L/day per person) and canned goods/crackers.' },
    { id: 'g3', icon: '🔦', titleUk: 'Автономне живлення', titleEn: 'Backup power', descUk: 'Павербанк, ліхтарик, резервна зарядка. Переконайтеся що пристрої завжди заряджені.', descEn: 'Powerbank, flashlight, backup charger. Ensure devices are always charged.' },
    { id: 'g4', icon: '📋', titleUk: 'Документи під рукою', titleEn: 'Documents at hand', descUk: 'Паспорт, документи на нерухомість, медичні довідки — зберігайте в одному місці у водонепроникному пакеті.', descEn: 'Passport, property documents, medical records — store in one place in a waterproof bag.' },
  ],
};

// ─── Routes ────────────────────────────────────────────────────────────────────

app.get('/api/regions', (req, res) => {
  res.json({ regions: REGIONS, updatedAt: new Date().toISOString() });
});

app.get('/api/alarms/history', (req, res) => {
  res.json({ history: HISTORY });
});

app.get('/api/shelters', (req, res) => {
  res.json({ shelters: SHELTERS });
});

app.get('/api/safety-tips', (req, res) => {
  res.json(SAFETY_TIPS);
});

app.post('/api/ai/chat', (req, res) => {
  const { message } = req.body;
  const responses = [
    'Якщо оголошено повітряну тривогу, негайно спускайтеся до укриття або підвалу.',
    'Найближче укриття можна знайти в додатку або на сайті місцевих органів влади.',
    'Тривожна валіза повинна містити: документи, воду, ліки, ліхтарик і заряджений телефон.',
    'Під час ракетної атаки тримайтеся від вікон і зовнішніх стін.',
    'Після відбою тривоги зачекайте 15–20 хвилин, перш ніж виходити.',
    'Підпишіться на офіційний Telegram канал вашого регіону для своєчасних сповіщень.',
    'Дзвоніть 112 у надзвичайних ситуаціях. 101 — пожежна охорона.',
  ];
  setTimeout(() => {
    res.json({ reply: responses[Math.floor(Math.random() * responses.length)] });
  }, 600);
});

const PORT = 3001;
app.listen(PORT, () => console.log(`Server running on http://localhost:${PORT}`));
