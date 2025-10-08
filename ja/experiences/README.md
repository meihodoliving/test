# 体験ページ共通コンポーネント

## 概要
弓道ページを基準として、各体験ページで統一されたデザインとUIを実現するための共通コンポーネントです。

## ファイル構成
```
/ja/experiences/
├── components.css          # 共通コンポーネントスタイル
├── kyudo/                  # 弓道ページ（基準デザイン）
├── iaido/                  # 居合道ページ
├── kendo/                  # 剣道ページ
├── karate/                 # 空手ページ
├── bonseki/                # 盆石ページ
├── chado/                  # 茶道ページ
├── kado/                   # 華道ページ
├── taiko/                  # 和太鼓ページ
└── README.md              # このファイル
```

## 共通コンポーネント

### 1. Experience Hero Component
```html
<section class="experience-hero">
    <div class="experience-hero-content">
        <h1 class="experience-title">
            <span class="japanese">[日本語タイトル]</span>
            <span class="english">[English Title]</span>
        </h1>
        <p class="experience-subtitle">[体験の説明文]</p>
    </div>
</section>
```

### 2. Breadcrumb Component
```html
<div class="breadcrumb">
    <div class="breadcrumb-content">
        <nav class="breadcrumb-list">
            <a href="/">ホーム</a>
            <span class="breadcrumb-separator">></span>
            <a href="/ja/experiences/">体験</a>
            <span class="breadcrumb-separator">></span>
            <span>[現在のページ名]</span>
        </nav>
    </div>
</div>
```

### 3. Experience Detail Component
```html
<section class="experience-detail">
    <div class="detail-content">
        <div class="detail-grid">
            <div class="detail-text">
                <h2>[見出し]</h2>
                <p>[説明文1]</p>
                <p>[説明文2]</p>
                <p>[説明文3]</p>
            </div>
            <div class="detail-image">
                <img src="[画像URL]" alt="[代替テキスト]" loading="lazy">
            </div>
        </div>
    </div>
</section>
```

### 4. Feature Grid Component
```html
<section class="features-section">
    <div class="container">
        <div class="section-header">
            <h2 class="section-title">[特徴のタイトル]</h2>
            <p class="section-subtitle">[特徴の説明]</p>
        </div>
        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-[アイコン名]"></i>
                </div>
                <h3>[特徴のタイトル]</h3>
                <p>[特徴の説明]</p>
            </div>
            <!-- 4つのfeature-cardを繰り返し -->
        </div>
    </div>
</section>
```

### 5. Info Card Component
```html
<section class="info-section">
    <div class="info-content">
        <div class="section-header">
            <h2 class="section-title">[情報のタイトル]</h2>
            <p class="section-subtitle">[情報の説明]</p>
        </div>
        <div class="info-card">
            <table>
                <thead>
                    <tr>
                        <th>[列1ヘッダー]</th>
                        <th>[列2ヘッダー]</th>
                        <th>[列3ヘッダー]</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>[データ1]</td>
                        <td>[データ2]</td>
                        <td>[データ3]</td>
                    </tr>
                    <!-- 必要な行数を繰り返し -->
                </tbody>
            </table>
        </div>
    </div>
</section>
```

### 6. CTA Section Component
```html
<section class="cta-section">
    <div class="cta-content">
        <h2>[CTAのタイトル]</h2>
        <p>[CTAの説明文]</p>
        <div class="cta-buttons">
            <a href="#contact" class="btn-cta btn-cta-primary">
                <i class="fas fa-calendar-alt"></i>
                今すぐ予約する
            </a>
            <a href="/ja/experiences/" class="btn-cta btn-cta-secondary">
                <i class="fas fa-arrow-left"></i>
                他の体験を見る
            </a>
        </div>
    </div>
</section>
```

## デザイン統一要素

### カラーパレット
- **Primary Color**: #8B7355 (生成り)
- **Secondary Color**: #2F4F4F (深緑)
- **Accent Color**: #D4AF37 (金)
- **Dark Color**: #1C1C1C (墨色)
- **Light Color**: #F8F6F1 (和紙)
- **Text Primary**: #2C2C2C (墨色)
- **Text Secondary**: #5A5A5A (グレー)
- **Border Color**: #E8E4D9 (薄い生成り)

### タイポグラフィ
- **日本語フォント**: Noto Serif JP
- **英語フォント**: Inter
- **見出しサイズ**: 2.5rem - 3.5rem
- **本文サイズ**: 1.05rem - 1.1rem
- **行間**: 1.8 - 2.0

### 余白・スペーシング
- **セクション間**: 120px
- **要素間**: 2rem - 3rem
- **カード内パディング**: 3rem 2.5rem
- **ボタンパディング**: 20px 40px

### 角丸・影
- **角丸**: 24px (カード), 30px (ボタン)
- **影**: 0 15px 40px rgba(139, 115, 85, 0.08)
- **ホバー影**: 0 25px 60px rgba(139, 115, 85, 0.15)

## レスポンシブ対応

### ブレイクポイント
- **デスクトップ**: ≥1200px
- **タブレット**: ≥768px
- **モバイル**: <768px

### レスポンシブルール
- **グリッド**: 3列 → 2列 → 1列
- **フォントサイズ**: デスクトップ基準から段階的に縮小
- **余白**: デスクトップ基準から段階的に縮小

## 使用方法

### 新しい体験ページを作成する場合
1. `components.css`を読み込む
2. 上記のコンポーネントを順番に配置
3. 各コンポーネント内のテキストと画像を差し替え
4. 必要に応じてアイコンを変更

### カスタマイズ時の注意点
- カラーパレットは変更しない
- 余白・角丸・影の値は統一を保つ
- フォントファミリーは変更しない
- レスポンシブ対応を維持する

## アクセシビリティ
- すべての画像にalt属性を設定
- ボタンとリンクに適切なフォーカス表示
- コントラスト比はWCAG AA基準を満たす
- キーボードナビゲーションに対応

## パフォーマンス
- 画像の遅延読み込み（loading="lazy"）
- 最小限のCSS（共通化により）
- 外部ライブラリの最小使用
- 軽量なJavaScript実装






