#!/usr/bin/env python3
"""Generate zh-cn/index.html from ja/index.html — same structure, Simplified Chinese copy."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "ja" / "index.html"
DST = ROOT / "zh-cn" / "index.html"

text = SRC.read_text(encoding="utf-8")

text = text.replace('<html lang="ja">', '<html lang="zh-CN">')
text = text.replace(
    '<title>鳴鳳堂 - 本格的な日本を体験</title>',
    '<title>鸣凤堂 · 在阿苏感受地道日本文化与自然</title>',
)

# Paths ja → zh-cn (before other edits)
text = text.replace('href="/ja/', 'href="/zh-cn/')

text = text.replace(
    '<p class="overlay-text">静かに己の心を見つめるひと時を。</p>',
    '<p class="overlay-text">静下来，与自己相处的一段时光。</p>',
)

repl_nav = [
    ('alt="ホーム"', 'alt="首页"'),
    ('<span>ホーム</span>', '<span>首页</span>'),
    ('alt="体験"', 'alt="体验"'),
    ('<span>体験</span>', '<span>体验</span>'),
    ('alt="宿泊"', 'alt="住宿"'),
    ('<span>宿泊</span>', '<span>住宿</span>'),
    ('alt="食事"', 'alt="餐饮"'),
    ('<span>食事</span>', '<span>餐饮</span>'),
    ('alt="撮影利用"', 'alt="拍摄与场地"'),
    ('<span>撮影利用</span>', '<span>拍摄与场地</span>'),
    ('alt="アクセス"', 'alt="交通指南"'),
    ('<span>アクセス</span>', '<span>交通指南</span>'),
]
for a, b in repl_nav:
    text = text.replace(a, b)

text = text.replace('alt="鳴鳳堂 ヒーロー画像"', 'alt="鸣凤堂 主视觉"')

text = text.replace(
    '<div class="catchphrase-line">阿蘇に息づく自然、</div>',
    '<div class="catchphrase-line">阿苏大地的自然生机，</div>',
)
text = text.replace(
    '<div class="catchphrase-line">五感を満たす美食、</div>',
    '<div class="catchphrase-line">慰藉五感的料理，</div>',
)
text = text.replace(
    '<div class="catchphrase-line">日常を忘れる体験、</div>',
    '<div class="catchphrase-line">令人忘却日常的沉浸体验，</div>',
)
text = text.replace(
    '<div class="catchphrase-line">和の心溢れる場所。</div>',
    '<div class="catchphrase-line">与和风心境相遇的空间。</div>',
)

text = text.replace(
    '<p>雄大な阿蘇山麓に広がる文化リゾート、鳴鳳堂。</p>',
    '<p>坐落于雄伟的阿苏山麓，鸣凤堂是一座融合文化与自然的度假胜地。</p>',
)
text = text.replace(
    '<p>56,000㎡の敷地に広がる日本建築の空間で、弓道・試し切り・空手などの武道から、<br>\n'
    '                        茶道・華道・盆石などの文化芸術まで、心を磨く体験が満載です。</p>',
    '<p>占地约56,000平方米的和风建筑群中，从弓道、试斩、空手等武道，到茶道、花道、盆石等传统艺术，<br>'
    '                        您可以尽情体验涵养身心的丰富项目。</p>',
)
text = text.replace(
    '<p>自然と伝統に包まれながら、日常から離れ、心身を癒やす特別な時間をお過ごしください。</p>',
    '<p>在自然与传统的环抱中远离喧嚣，度过疗愈身心的珍贵时光。</p>',
)

text = text.replace(
    '<h2 class="section-title">本格的な侍体験と日本文化を阿蘇で体感</h2>',
    '<h2 class="section-title">在阿苏沉浸体验武士文化与日本传统文化</h2>',
)
text = text.replace(
    '<p class="section-subtitle">阿蘇の大自然に囲まれた『鳴鳳堂』では、弓道・空手・剣道・試し切りなどの武道体験や、和太鼓・茶道・盆石・華道・滝行などの伝統文化体験が楽しめます。武道着を着て"侍体験コース"にも挑戦でき、家族旅行やカップルでの思い出作りにも人気のプログラムです。</p>',
    '<p class="section-subtitle">鸣凤堂坐落于阿苏群山之间，这里提供弓道、空手、剑道、试斩等武道课程，以及太鼓、茶道、盆石、花道、瀑布修行等传统体验。身着武道衣参加「武士体验课程」尤为热门，亦是家庭出游与情侣旅行的口碑之选。</p>',
)

_exp_pairs = [
    ('<h3>弓道</h3>', '<h3>弓道</h3>'),  # keep kanji
    (
        '<p>日本の伝統武道である弓道を通じて、精神統一と集中力を養います。</p>',
        '<p>通过日本传统武道弓道，锻炼专注与心平气和。</p>',
    ),
    ('alt="弓道体験 - 日本の伝統武道"', 'alt="弓道体验——日本传统武道"'),
    ('<h3>試し切り</h3>', '<h3>试斩</h3>'),
    (
        '<p>日本刀を使った試し切りで、武士の心構えと礼儀作法を学びます。</p>',
        '<p>使用日本刀的试斩课程，了解武士的心境与礼仪。</p>',
    ),
    ('alt="試し切り体験 - 日本刀の試し切り"', 'alt="试斩体验——日本刀试斩"'),
    ('<h3>剣道</h3>', '<h3>剑道</h3>'),
    (
        '<p>竹刀を用いた剣道で、礼儀作法と精神力を鍛えます。</p>',
        '<p>以竹剑修习剑道，锤炼礼节与精神力量。</p>',
    ),
    ('alt="剣道体験 - 竹刀を使った武道"', 'alt="剑道体验——竹剑武道"'),
    ('<h3>空手</h3>', '<h3>空手道</h3>'),
    (
        '<p>沖縄発祥の空手で、基本動作と型を学び、心身を鍛えます。</p>',
        '<p>源自冲绳的空手道，学习基本动作与型，强健身心。</p>',
    ),
    ('alt="空手体験 - 沖縄発祥の武道"', 'alt="空手道体验——冲绳发源的武道"'),
    ('<h3>盆石</h3>', '<h3>盆石</h3>'),
    (
        '<p>白砂と小石で山水の景を表す日本の伝統芸術を体験します。</p>',
        '<p>以白砂与细石呈现山水意境的日本传统艺术体验。</p>',
    ),
    ('alt="盆石体験 - 白砂と小石で山水を表現"', 'alt="盆石体验——砂与石的山水意境"'),
    ('<h3>茶道</h3>', '<h3>茶道</h3>'),
    (
        '<p>伝統的な茶道を通じて、日本の美意識と精神文化を学びます。</p>',
        '<p>在传统茶道中体会日本的审美意识与礼仪精神。</p>',
    ),
    ('alt="茶道体験 - 伝統的な茶道"', 'alt="茶道体验——传统茶事"'),
    ('<h3>華道</h3>', '<h3>花道</h3>'),
    (
        '<p>生け花を通じて、自然の美しさと日本の美意識を表現します。</p>',
        '<p>通过插花表现自然之美与日本美学。</p>',
    ),
    ('alt="華道体験 - 生け花の芸術"', 'alt="花道体验——插花艺术"'),
    ('<h3>和太鼓</h3>', '<h3>和太鼓</h3>'),
    (
        '<p>和太鼓の躍動感あるリズムを体験し、日本の伝統音楽を楽しみます。</p>',
        '<p>感受和太鼓的律动节奏，领略日本传统打击乐的魅力。</p>',
    ),
    ('alt="和太鼓体験 - 躍動感あるリズム"', 'alt="和太鼓体验——澎湃节奏"'),
]
for _o, _n in _exp_pairs:
    text = text.replace(_o, _n)

_footer_exp = [
    ('<li><a href="#">弓道</a></li>', '<li><a href="#">弓道</a></li>'),
    ('<li><a href="#">試し切り</a></li>', '<li><a href="#">试斩</a></li>'),
    ('<li><a href="#">剣道</a></li>', '<li><a href="#">剑道</a></li>'),
    ('<li><a href="#">空手</a></li>', '<li><a href="#">空手道</a></li>'),
    ('<li><a href="#">茶道</a></li>', '<li><a href="#">茶道</a></li>'),
    ('<li><a href="#">盆石</a></li>', '<li><a href="#">盆石</a></li>'),
    ('<li><a href="#">和太鼓</a></li>', '<li><a href="#">和太鼓</a></li>'),
    ('<li><a href="#">華道</a></li>', '<li><a href="#">花道</a></li>'),
]
for _o, _n in _footer_exp:
    text = text.replace(_o, _n)

text = text.replace('<div class="card-button">詳細を見る</div>', '<div class="card-button">了解详情</div>')

text = text.replace('<h2 class="section-title">宿泊</h2>', '<h2 class="section-title">住宿</h2>')
text = text.replace(
    '<p class="section-subtitle">一棟貸し切りのプライベートな空間です。阿蘇の自然に囲まれた静寂な空間で、心安らぐひとときをお過ごしください。</p>',
    '<p class="section-subtitle">整栋包租的私密空间。在阿苏自然环绕的静谧中，放松身心。</p>',
)
text = text.replace('alt="清静舎 外観"', 'alt="清静舍 外观"')
text = text.replace('<h3>清静舎</h3>', '<h3>清静舍</h3>')
text = text.replace('alt="迎賓館 外観"', 'alt="迎宾馆 外观"')
text = text.replace('<h3>迎賓館</h3>', '<h3>迎宾馆</h3>')
text = text.replace('alt="鴻臚館 外観"', 'alt="鸿胪馆 外观"')
text = text.replace('<h3>鴻臚館</h3>', '<h3>鸿胪馆</h3>')
text = text.replace('alt="文心館 外観"', 'alt="文心馆 外观"')
text = text.replace('<h3>文心館</h3>', '<h3>文心馆</h3>')
text = text.replace('alt="江戸館 外観"', 'alt="江户馆 外观"')
text = text.replace('<h3>江戸館</h3>', '<h3>江户馆</h3>')
text = text.replace('alt="檜の間 外観"', 'alt="桧木之间 外观"')
text = text.replace('<h3>檜の間</h3>', '<h3>桧木之间</h3>')

text = text.replace('<h2 class="section-title">料亭 鳴鳳堂</h2>', '<h2 class="section-title">料亭 鸣凤堂</h2>')
text = text.replace(
    '<p class="section-subtitle">四季折々の食材を活かした本格的な会席料理をお楽しみいただけます。</p>',
    '<p class="section-subtitle">严选四季食材，呈现正宗怀石料理。</p>',
)
text = text.replace('alt="料亭 鳴鳳堂 外観"', 'alt="料亭鸣凤堂 外观"')
text = text.replace('<h3>本格的な会席料理</h3>', '<h3>正宗怀石料理</h3>')
text = text.replace(
    '<p>阿蘇の豊かな自然から生まれる四季折々の食材を活かし、伝統的な技法で仕上げた本格的な会席料理をご提供いたします。</p>',
    '<p>选用阿苏丰饶自然孕育的时令食材，以传统技法烹调正宗怀石料理。</p>',
)
text = text.replace(
    '<p>地元の新鮮な野菜、天草直送の魚介類、そして熊本の特産品をふんだんに使用した、心に残る特別な食体験をお楽しみください。</p>',
    '<p>新鲜在地蔬菜、天草直送的渔获与熊本特产汇聚一席，为您留下难忘的用餐记忆。</p>',
)
text = text.replace('<span>四季の食材</span>', '<span>时令食材</span>')
text = text.replace('<span>新鮮な魚介類</span>', '<span>新鲜海产</span>')
text = text.replace('<span>地元野菜</span>', '<span>在地蔬菜</span>')
text = text.replace('<span>厳選日本酒</span>', '<span>精选日本酒</span>')
text = text.replace(
    '<a href="/zh-cn/restaurant/" class="btn btn-primary">詳細を見る</a>',
    '<a href="/zh-cn/restaurant/" class="btn btn-primary">了解详情</a>',
)

text = text.replace('<h2 class="section-title">撮影利用</h2>', '<h2 class="section-title">拍摄与场地租赁</h2>')
text = text.replace(
    '<p class="section-subtitle">鳴鳳堂の空間を、様々な撮影ロケ地としてご活用いただけます。</p>',
    '<p class="section-subtitle">鸣凤堂的空间可作为各类影视与摄影外景地。</p>',
)
text = text.replace('alt="撮影利用 外観"', 'alt="拍摄场地 外观"')
text = text.replace('<h3>伝統的な空間での撮影</h3>', '<h3>在传统建筑空间中拍摄</h3>')
text = text.replace(
    '<p>鳴鳳堂の美しい日本建築と庭園を背景に、特別な撮影をお楽しみいただけます。結婚式、記念写真、商品撮影など、様々な用途でご利用ください。</p>',
    '<p>以优美的日本建筑与庭园为背景，记录婚礼、纪念写真、商品拍摄等多种场景。</p>',
)
text = text.replace(
    '<p>阿蘇の雄大な自然に囲まれた静寂な空間で、心に残る特別な一枚を撮影していただけます。</p>',
    '<p>在阿苏壮阔自然与静谧氛围中，留下值得珍藏的画面。</p>',
)
text = text.replace('<span>写真撮影</span>', '<span>平面摄影</span>')
text = text.replace('<span>動画撮影</span>', '<span>视频拍摄</span>')
text = text.replace('<span>結婚式</span>', '<span>婚礼</span>')
text = text.replace('<span>商品撮影</span>', '<span>商业拍摄</span>')
text = text.replace(
    '<a href="/zh-cn/location/" class="btn btn-primary">詳細を見る</a>',
    '<a href="/zh-cn/location/" class="btn btn-primary">了解详情</a>',
)

text = text.replace('<h2 class="section-title">アクセス</h2>', '<h2 class="section-title">交通指南</h2>')
text = text.replace(
    '<p class="section-subtitle">鳴鳳堂へのアクセス情報。お車・電車・空港からのルートをご案内します。</p>',
    '<p class="section-subtitle">前往鸣凤堂的交通方式：自驾、铁路与机场接驳。</p>',
)
text = text.replace('<h4>住所</h4>', '<h4>地址</h4>')
text = text.replace('<h4>最寄り駅</h4>', '<h4>最近车站</h4>')
text = text.replace('<h4>空港から</h4>', '<h4>从机场</h4>')
text = text.replace('<p>熊本空港から車で約35分</p>', '<p>从熊本机场驾车约35分钟</p>')
text = text.replace(
    'title="鳴鳳堂の場所 - 熊本県阿蘇市永草1943-28"',
    'title="鸣凤堂位置——熊本县阿苏市永草1943-28"',
)
text = text.replace(
    'aria-label="鳴鳳堂の場所を示すGoogleマップ"',
    'aria-label="Google地图显示鸣凤堂位置"',
)
text = text.replace(
    '<a href="https://www.google.com/maps/search/?api=1&query=熊本県阿蘇市永草1943-28" target="_blank" class="btn btn-primary map-button">Googleマップで開く</a>',
    '<a href="https://www.google.com/maps/search/?api=1&query=熊本県阿蘇市永草1943-28" target="_blank" class="btn btn-primary map-button">在 Google 地图中打开</a>',
)

text = text.replace('<p>熊本県阿蘇市永草1943-28</p>', '<p>熊本县阿苏市永草1943-28</p>')
text = text.replace('<p>市ノ川駅／阿蘇駅</p>', '<p>市之川站／阿苏站</p>')
text = text.replace('<li>熊本県阿蘇市永草1943-28</li>', '<li>熊本县阿苏市永草1943-28</li>')

text = text.replace('<h2 class="section-title">提携サービス</h2>', '<h2 class="section-title">合作服务</h2>')
text = text.replace(
    '<p class="section-subtitle">鳴鳳堂と提携するサービスをご紹介します。滞在をより快適にするための特別なご案内です。</p>',
    '<p class="section-subtitle">以下为与鸣凤堂合作的配套服务，让您的旅程更加舒适。</p>',
)
text = text.replace('alt="レストラン 山水家"', 'alt="餐厅 山水家"')
text = text.replace('<h3>レストラン 山水家</h3>', '<h3>餐厅 山水家</h3>')
text = text.replace(
    '<p>地元食材を活かした本格的な和食を楽しめる提携レストランです。</p>',
    '<p>合作餐厅，提供善用在地食材的和食料理。</p>',
)
text = text.replace('alt="マッサージ ここりらく"', 'alt="按摩 心之楽"')
text = text.replace('<h3>マッサージ ここりらく</h3>', '<h3>按摩 心之楽</h3>')
text = text.replace(
    '<p>リラクゼーションマッサージで心と体を癒す、滞在中に利用できる提携サービスです。</p>',
    '<p>入住期间可预约休闲按摩，舒缓身心。</p>',
)
text = text.replace('<a href="#" class="btn btn-primary">詳細を見る</a>', '<a href="#" class="btn btn-primary">了解详情</a>')

text = text.replace(
    '<p>阿蘇の火山地帯で、本格的な日本の心を体験してください。</p>',
    '<p>在阿苏火山地带，感受地道的日本之心。</p>',
)
text = text.replace('<h4>体験メニュー</h4>', '<h4>体验项目</h4>')
text = text.replace('<h4>お問い合わせ情報</h4>', '<h4>联系方式</h4>')
text = text.replace('<span class="btn-text">宿泊予約</span>', '<span class="btn-text">住宿预订</span>')
text = text.replace('<span class="btn-text">体験予約</span>', '<span class="btn-text">体验预订</span>')

text = text.replace(
    """        <div class="language-buttons">
            <button class="lang-btn" data-lang="jp">JP</button>
            <a href="../en/index.html" class="lang-btn" data-lang="en">EN</a>
            <button class="lang-btn" data-lang="traditional">繁</button>
            <button class="lang-btn" data-lang="simplified">簡</button>
        </div>""",
    """        <div class="language-buttons">
            <a href="/ja/index.html" class="lang-btn" data-lang="jp">JP</a>
            <a href="/en/index.html" class="lang-btn" data-lang="en">EN</a>
            <a href="/zh-tw/index.html" class="lang-btn" data-lang="zh-tw">繁</a>
            <a href="/zh-cn/index.html" class="lang-btn" data-lang="zh-cn">簡</a>
        </div>""",
)

text = text.replace(
    "return path === '/' || path === '/index.html' || path === '/ja/' || path === '/ja/index.html'\n"
    "                    || path === '/en/' || path === '/en/index.html'\n"
    "                    || path.endsWith('/ja/index.html') || path.endsWith('/en/index.html');",
    "return path === '/' || path === '/index.html' || path === '/ja/' || path === '/ja/index.html'\n"
    "                    || path === '/en/' || path === '/en/index.html'\n"
    "                    || path === '/zh-cn/' || path === '/zh-cn/index.html'\n"
    "                    || path.endsWith('/ja/index.html') || path.endsWith('/en/index.html')\n"
    "                    || path.endsWith('/zh-cn/index.html');",
)

# Overlay script: Japanese comments → English (same behavior as ja; keeps bundle readable)
_js_comment_pairs = [
    ("// テキスト表示までの遅延（ミリ秒）", "// Delay before overlay text (ms)"),
    ("// テキスト表示時間（ミリ秒）", "// Overlay text visible duration (ms)"),
    ("// フェードアウト時間（ミリ秒）", "// Fade-out duration (ms)"),
    ("// テキストを初期状態に設定", "// Reset text state"),
    ("// 0.5秒後にテキストを表示", "// Show text after delay"),
    ("// 2.5秒後にテキストをフェードアウト", "// Fade text out after display"),
    ("// テキストフェードアウト後にオーバーレイ全体をフェードアウト", "// Fade entire overlay after text"),
    ("// フェードアウト完了後に削除", "// Remove overlay after fade completes"),
]
for ja_c, en_c in _js_comment_pairs:
    text = text.replace(ja_c, en_c)

DST.parent.mkdir(parents=True, exist_ok=True)
DST.write_text(text, encoding="utf-8")
print(f"Wrote {DST}")
