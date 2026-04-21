#!/usr/bin/env python3
"""Generate en/index.html from root index.html — same structure, English copy, correct paths."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "index.html"
DST = ROOT / "en" / "index.html"

text = SRC.read_text(encoding="utf-8")

# Structural / path fixes for files under en/
text = text.replace('<html lang="en">', '<html lang="en">')  # keep English
text = text.replace(
    '<title>鳴鳳堂 - 本格的な日本を体験</title>',
    '<title>Meihodo — Experience authentic Japan in Aso</title>',
)
text = text.replace(
    '<link rel="stylesheet" href="styles.css">',
    '<link rel="stylesheet" href="../styles.css">',
)

# Navigation — Japanese site paths → English site paths
text = text.replace('href="/index.html"', 'href="/en/index.html"', 2)  # nav left + center — careful count
# Root index has two /index.html for nav - we replaced 2 - verify
text = text.replace('href="/ja/experiences/"', 'href="/en/experiences/"')
text = text.replace('href="/ja/accommodations/"', 'href="/en/accommodations/"')
text = text.replace('href="/ja/restaurant/"', 'href="/en/restaurant/"')
text = text.replace('href="/ja/location/"', 'href="/en/location/"')

# Experience cards
text = text.replace('href="/ja/experiences/', 'href="/en/experiences/')
# Accommodations
text = text.replace('href="/ja/seiseikan/"', 'href="/en/seiseikan/"')
text = text.replace('href="/ja/geihinkan/"', 'href="/en/geihinkan/"')
text = text.replace('href="/ja/korokan/"', 'href="/en/korokan/"')
text = text.replace('href="/ja/bunshinkan/"', 'href="/en/bunshinkan/"')
text = text.replace('href="/ja/edokan/"', 'href="/en/edokan/"')
text = text.replace('href="/ja/hinokinoma/"', 'href="/en/hinokinoma/"')

# Overlay
text = text.replace(
    '<p class="overlay-text">静かに己の心を見つめるひと時を。</p>',
    '<p class="overlay-text">A quiet moment to turn inward and reflect.</p>',
)

# Nav labels & alts
repl_nav = [
    ('alt="ホーム"', 'alt="Home"'),
    ('<span>ホーム</span>', '<span>Home</span>'),
    ('alt="体験"', 'alt="Experiences"'),
    ('<span>体験</span>', '<span>Experiences</span>'),
    ('alt="宿泊"', 'alt="Stay"'),
    ('<span>宿泊</span>', '<span>Stay</span>'),
    ('alt="食事"', 'alt="Dining"'),
    ('<span>食事</span>', '<span>Dining</span>'),
    ('alt="撮影利用"', 'alt="Photo shoots"'),
    ('<span>撮影利用</span>', '<span>Photo shoots</span>'),
    ('alt="アクセス"', 'alt="Access"'),
    ('<span>アクセス</span>', '<span>Access</span>'),
]
for a, b in repl_nav:
    text = text.replace(a, b)

# Hero image alt
text = text.replace(
    'alt="鳴鳳堂 ヒーロー画像"',
    'alt="Meihodo — hero image"',
)

# Philosophy catchphrase
text = text.replace(
    '<div class="catchphrase-line">阿蘇に息づく自然、</div>',
    '<div class="catchphrase-line">Nature breathes in Aso,</div>',
)
text = text.replace(
    '<div class="catchphrase-line">五感を満たす美食、</div>',
    '<div class="catchphrase-line">feasts that awaken the senses,</div>',
)
text = text.replace(
    '<div class="catchphrase-line">日常を忘れる体験、</div>',
    '<div class="catchphrase-line">experiences that carry you from the everyday,</div>',
)
text = text.replace(
    '<div class="catchphrase-line">和の心溢れる場所。</div>',
    '<div class="catchphrase-line">a place where the heart of Japan endures.</div>',
)

text = text.replace(
    '<p>雄大な阿蘇山麓に広がる文化リゾート、鳴鳳堂。</p>',
    '<p>Set at the foot of majestic Mt. Aso, Meihodo is a cultural resort shaped by tradition and landscape.</p>',
)
text = text.replace(
    '<p>56,000㎡の敷地に広がる日本建築の空間で、弓道・試し切り・空手などの武道から、<br>\n'
    '                        茶道・華道・盆石などの文化芸術まで、心を磨く体験が満載です。</p>',
    '<p>Across 56,000 square meters of Japanese architecture, forge mind and spirit—<br>'
    '                        from kyūdō, tameshigiri, karate and other martial arts to chadō, kadō, bonseki and classical arts.</p>',
)
text = text.replace(
    '<p>自然と伝統に包まれながら、日常から離れ、心身を癒やす特別な時間をお過ごしください。</p>',
    '<p>Surrounded by nature and tradition, gift yourself time away from routine to restore body and mind.</p>',
)

# Experiences header
text = text.replace(
    '<h2 class="section-title">本格的な侍体験と日本文化を阿蘇で体感</h2>',
    '<h2 class="section-title">Samurai spirit and Japanese culture—experienced in Aso</h2>',
)
text = text.replace(
    '<p class="section-subtitle">阿蘇の大自然に囲まれた『鳴鳳堂』では、弓道・空手・剣道・試し切りなどの武道体験や、和太鼓・茶道・盆石・華道・滝行などの伝統文化体験が楽しめます。武道着を着て"侍体験コース"にも挑戦でき、家族旅行やカップルでの思い出作りにも人気のプログラムです。</p>',
    '<p class="section-subtitle">Surrounded by Aso’s wilderness, Meihodo offers martial arts—from kyūdō, karate, kendo and tameshigiri—to taiko, tea ceremony, bonseki, kadō and more. Train in full gear with our samurai immersion course—a favorite with families and couples alike.</p>',
)

# Experience cards (order: titles & unique lines before bare names used in footer)
_exp_pairs = [
    ('<h3>弓道</h3>', '<h3>Kyūdō</h3>'),
    (
        '<p>日本の伝統武道である弓道を通じて、精神統一と集中力を養います。</p>',
        '<p>Through kyūdō—Japanese archery—cultivate focus and a calm mind.</p>',
    ),
    ('alt="弓道体験 - 日本の伝統武道"', 'alt="Kyūdō — Japanese archery"'),
    ('<h3>試し切り</h3>', '<h3>Tameshigiri</h3>'),
    (
        '<p>日本刀を使った試し切りで、武士の心構えと礼儀作法を学びます。</p>',
        '<p>Study tameshigiri with the katana—manners, posture and the samurai spirit.</p>',
    ),
    ('alt="試し切り体験 - 日本刀の試し切り"', 'alt="Tameshigiri — test cutting with the katana"'),
    ('<h3>剣道</h3>', '<h3>Kendō</h3>'),
    (
        '<p>竹刀を用いた剣道で、礼儀作法と精神力を鍛えます。</p>',
        '<p>Train kendō with the shinai—etiquette, resilience and inner strength.</p>',
    ),
    ('alt="剣道体験 - 竹刀を使った武道"', 'alt="Kendō — bamboo sword"'),
    ('<h3>空手</h3>', '<h3>Karate</h3>'),
    (
        '<p>沖縄発祥の空手で、基本動作と型を学び、心身を鍛えます。</p>',
        '<p>Okinawan karate—basics, kata and conditioning for body and mind.</p>',
    ),
    ('alt="空手体験 - 沖縄発祥の武道"', 'alt="Karate — Okinawan martial art"'),
    ('<h3>盆石</h3>', '<h3>Bonseki</h3>'),
    (
        '<p>白砂と小石で山水の景を表す日本の伝統芸術を体験します。</p>',
        '<p>Create miniature landscapes in sand and stone—a classical Japanese art.</p>',
    ),
    ('alt="盆石体験 - 白砂と小石で山水を表現"', 'alt="Bonseki — sand landscape"'),
    ('<h3>茶道</h3>', '<h3>Tea ceremony</h3>'),
    (
        '<p>伝統的な茶道を通じて、日本の美意識と精神文化を学びます。</p>',
        '<p>Experience sadō and discover Japanese aesthetics and hospitality of quiet grace.</p>',
    ),
    ('alt="茶道体験 - 伝統的な茶道"', 'alt="Tea ceremony — sadō"'),
    ('<h3>華道</h3>', '<h3>Kadō (ikebana)</h3>'),
    (
        '<p>生け花を通じて、自然の美しさと日本の美意識を表現します。</p>',
        '<p>Express nature’s beauty through ikebana.</p>',
    ),
    ('alt="華道体験 - 生け花の芸術"', 'alt="Kadō — flower arrangement"'),
    ('<h3>和太鼓</h3>', '<h3>Taiko</h3>'),
    (
        '<p>和太鼓の躍動感あるリズムを体験し、日本の伝統音楽を楽しみます。</p>',
        '<p>Feel the drive of taiko and the energy of Japanese percussion.</p>',
    ),
    ('alt="和太鼓体験 - 躍動感あるリズム"', 'alt="Taiko — Japanese drums"'),
]
for _o, _n in _exp_pairs:
    text = text.replace(_o, _n)

# Footer experience links (same names as cards)
_footer_exp = [
    ('<li><a href="#">弓道</a></li>', '<li><a href="#">Kyūdō</a></li>'),
    ('<li><a href="#">試し切り</a></li>', '<li><a href="#">Tameshigiri</a></li>'),
    ('<li><a href="#">剣道</a></li>', '<li><a href="#">Kendō</a></li>'),
    ('<li><a href="#">空手</a></li>', '<li><a href="#">Karate</a></li>'),
    ('<li><a href="#">茶道</a></li>', '<li><a href="#">Tea ceremony</a></li>'),
    ('<li><a href="#">盆石</a></li>', '<li><a href="#">Bonseki</a></li>'),
    ('<li><a href="#">和太鼓</a></li>', '<li><a href="#">Taiko</a></li>'),
    ('<li><a href="#">華道</a></li>', '<li><a href="#">Kadō</a></li>'),
]
for _o, _n in _footer_exp:
    text = text.replace(_o, _n)

text = text.replace('<div class="card-button">詳細を見る</div>', '<div class="card-button">Learn more</div>')

# Accommodations
text = text.replace(
    '<h2 class="section-title">宿泊</h2>',
    '<h2 class="section-title">Stay</h2>',
)
text = text.replace(
    '<p class="section-subtitle">一棟貸し切りのプライベートな空間です。阿蘇の自然に囲まれた静寂な空間で、心安らぐひとときをお過ごしください。</p>',
    '<p class="section-subtitle">Private villas—each reserved entirely for your party. Unwind in quiet surroundings embraced by Aso’s nature.</p>',
)
text = text.replace('alt="清静舎 外観"', 'alt="Seiseikan exterior"')
text = text.replace('<h3>清静舎</h3>', '<h3>Seiseikan</h3>')
text = text.replace('alt="迎賓館 外観"', 'alt="Geihinkan exterior"')
text = text.replace('<h3>迎賓館</h3>', '<h3>Geihinkan</h3>')
text = text.replace('alt="鴻臚館 外観"', 'alt="Kōrokan exterior"')
text = text.replace('<h3>鴻臚館</h3>', '<h3>Kōrokan</h3>')
text = text.replace('alt="文心館 外観"', 'alt="Bunshinkan exterior"')
text = text.replace('<h3>文心館</h3>', '<h3>Bunshinkan</h3>')
text = text.replace('alt="江戸館 外観"', 'alt="Edokan exterior"')
text = text.replace('<h3>江戸館</h3>', '<h3>Edokan</h3>')
text = text.replace('alt="檜の間 外観"', 'alt="Hinokinoma exterior"')
text = text.replace('<h3>檜の間</h3>', '<h3>Hinokinoma</h3>')

# Restaurant
text = text.replace(
    '<h2 class="section-title">料亭 鳴鳳堂</h2>',
    '<h2 class="section-title">Ryotei Meihodo</h2>',
)
text = text.replace(
    '<p class="section-subtitle">四季折々の食材を活かした本格的な会席料理をお楽しみいただけます。</p>',
    '<p class="section-subtitle">Seasonal kaiseki crafted with ingredients from Aso and beyond.</p>',
)
text = text.replace('alt="料亭 鳴鳳堂 外観"', 'alt="Ryotei Meihodo exterior"')
text = text.replace(
    '<h3>本格的な会席料理</h3>',
    '<h3>Authentic kaiseki</h3>',
)
text = text.replace(
    '<p>阿蘇の豊かな自然から生まれる四季折々の食材を活かし、伝統的な技法で仕上げた本格的な会席料理をご提供いたします。</p>',
    '<p>We serve kaiseki shaped by the seasons—prepared with traditional technique and ingredients born from Aso’s rich land.</p>',
)
text = text.replace(
    '<p>地元の新鮮な野菜、天草直送の魚介類、そして熊本の特産品をふんだんに使用した、心に残る特別な食体験をお楽しみください。</p>',
    '<p>Enjoy fresh local vegetables, seafood from Amakusa waters, and Kumamoto specialties in a meal to remember.</p>',
)
text = text.replace('<span>四季の食材</span>', '<span>Seasonal ingredients</span>')
text = text.replace('<span>新鮮な魚介類</span>', '<span>Fresh seafood</span>')
text = text.replace('<span>地元野菜</span>', '<span>Local produce</span>')
text = text.replace('<span>厳選日本酒</span>', '<span>Selected sake</span>')
text = text.replace(
    '<a href="/en/restaurant/" class="btn btn-primary">詳細を見る</a>',
    '<a href="/en/restaurant/" class="btn btn-primary">Learn more</a>',
)

# Location / filming
text = text.replace(
    '<h2 class="section-title">撮影利用</h2>',
    '<h2 class="section-title">Filming &amp; photo shoots</h2>',
)
text = text.replace(
    '<p class="section-subtitle">鳴鳳堂の空間を、様々な撮影ロケ地としてご活用いただけます。</p>',
    '<p class="section-subtitle">Use Meihodo’s spaces as a distinctive on-location set for photography and film.</p>',
)
text = text.replace('alt="撮影利用 外観"', 'alt="Filming — exterior"')
text = text.replace(
    '<h3>伝統的な空間での撮影</h3>',
    '<h3>Shoot in classical Japanese spaces</h3>',
)
text = text.replace(
    '<p>鳴鳳堂の美しい日本建築と庭園を背景に、特別な撮影をお楽しみいただけます。結婚式、記念写真、商品撮影など、様々な用途でご利用ください。</p>',
    '<p>Set weddings, portraits or product work against our architecture and gardens—crafted for memorable visuals.</p>',
)
text = text.replace(
    '<p>阿蘇の雄大な自然に囲まれた静寂な空間で、心に残る特別な一枚を撮影していただけます。</p>',
    '<p>In the stillness beneath Aso’s peaks, capture images that stay with you.</p>',
)
text = text.replace('<span>写真撮影</span>', '<span>Photography</span>')
text = text.replace('<span>動画撮影</span>', '<span>Video</span>')
text = text.replace('<span>結婚式</span>', '<span>Weddings</span>')
text = text.replace('<span>商品撮影</span>', '<span>Commercial</span>')
text = text.replace(
    '<a href="/en/location/" class="btn btn-primary">詳細を見る</a>',
    '<a href="/en/location/" class="btn btn-primary">Learn more</a>',
)

# Access
text = text.replace(
    '<h2 class="section-title">アクセス</h2>',
    '<h2 class="section-title">Access</h2>',
)
text = text.replace(
    '<p class="section-subtitle">鳴鳳堂へのアクセス情報。お車・電車・空港からのルートをご案内します。</p>',
    '<p class="section-subtitle">How to reach Meihodo—by car, train or from the airport.</p>',
)
text = text.replace('<h4>住所</h4>', '<h4>Address</h4>')
text = text.replace('<h4>最寄り駅</h4>', '<h4>Nearest stations</h4>')
text = text.replace('<h4>空港から</h4>', '<h4>From the airport</h4>')
text = text.replace(
    '<p>熊本空港から車で約35分</p>',
    '<p>About 35 minutes by car from Kumamoto Airport</p>',
)
text = text.replace(
    'title="鳴鳳堂の場所 - 熊本県阿蘇市永草1943-28"',
    'title="Meihodo — Nagakusa 1943-28, Aso, Kumamoto"',
)
text = text.replace(
    'aria-label="鳴鳳堂の場所を示すGoogleマップ"',
    'aria-label="Google Map — Meihodo location"',
)
text = text.replace(
    '<a href="https://www.google.com/maps/search/?api=1&query=熊本県阿蘇市永草1943-28" target="_blank" class="btn btn-primary map-button">Googleマップで開く</a>',
    '<a href="https://www.google.com/maps/search/?api=1&query=熊本県阿蘇市永草1943-28" target="_blank" class="btn btn-primary map-button">Open in Google Maps</a>',
)

# Access & footer visible address lines (romanized)
text = text.replace(
    '<p>熊本県阿蘇市永草1943-28</p>',
    '<p>1943-28 Nagakusa, Aso City, Kumamoto</p>',
)
text = text.replace(
    '<p>市ノ川駅／阿蘇駅</p>',
    '<p>Ichinokawa Station / Aso Station</p>',
)
text = text.replace(
    '<li>熊本県阿蘇市永草1943-28</li>',
    '<li>1943-28 Nagakusa, Aso City, Kumamoto</li>',
)

# Partnership
text = text.replace(
    '<h2 class="section-title">提携サービス</h2>',
    '<h2 class="section-title">Partner services</h2>',
)
text = text.replace(
    '<p class="section-subtitle">鳴鳳堂と提携するサービスをご紹介します。滞在をより快適にするための特別なご案内です。</p>',
    '<p class="section-subtitle">Partners who extend your stay—dining, wellness and more.</p>',
)
text = text.replace('alt="レストラン 山水家"', 'alt="Restaurant Sansuika"')
text = text.replace(
    '<h3>レストラン 山水家</h3>',
    '<h3>Restaurant Sansuika</h3>',
)
text = text.replace(
    '<p>地元食材を活かした本格的な和食を楽しめる提携レストランです。</p>',
    '<p>Partner restaurant serving Japanese cuisine centered on local ingredients.</p>',
)
text = text.replace('alt="マッサージ ここりらく"', 'alt="Massage Kokoriraku"')
text = text.replace(
    '<h3>マッサージ ここりらく</h3>',
    '<h3>Massage Kokoriraku</h3>',
)
text = text.replace(
    '<p>リラクゼーションマッサージで心と体を癒す、滞在中に利用できる提携サービスです。</p>',
    '<p>Relaxation massage available during your stay.</p>',
)
text = text.replace(
    '<a href="#" class="btn btn-primary">詳細を見る</a>',
    '<a href="#" class="btn btn-primary">Learn more</a>',
)

# Footer
text = text.replace(
    '<p>阿蘇の火山地帯で、本格的な日本の心を体験してください。</p>',
    '<p>Experience the heart of Japan in the volcanic landscape of Aso.</p>',
)
text = text.replace('<h4>体験メニュー</h4>', '<h4>Experiences</h4>')
text = text.replace('<h4>お問い合わせ情報</h4>', '<h4>Contact</h4>')

# Fixed buttons
text = text.replace('<span class="btn-text">宿泊予約</span>', '<span class="btn-text">Book stay</span>')
text = text.replace('<span class="btn-text">体験予約</span>', '<span class="btn-text">Book experiences</span>')

# Language switcher — JP links to Japanese top
text = text.replace(
    '<button class="lang-btn" data-lang="jp">JP</button>',
    '<a href="/ja/index.html" class="lang-btn" data-lang="jp">JP</a>',
    1,
)
text = text.replace(
    '<a href="en/index.html" class="lang-btn" data-lang="en">EN</a>',
    '<a href="/en/index.html" class="lang-btn" data-lang="en">EN</a>',
)

# Initial load overlay — treat English home
text = text.replace(
    "return path === '/' || path === '/index.html' || path === '/ja/' || path === '/ja/index.html';",
    "return path === '/' || path === '/index.html' || path === '/ja/' || path === '/ja/index.html' "
    "|| path === '/en/' || path === '/en/index.html' || path.endsWith('/en/index.html');",
)

DST.parent.mkdir(parents=True, exist_ok=True)
DST.write_text(text, encoding="utf-8")
print(f"Wrote {DST} ({len(text)} chars)")
