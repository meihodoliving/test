/*
 * Room gallery lightbox — click / tap a photo in a room page's 客室ギャラリー
 * (#gallery .gallery-grid) to view it full-screen. Arrows, swipe and the
 * keyboard (← → Esc) move between photos; × or the backdrop closes it.
 * Styles live in styles.css under "Room gallery lightbox".
 */
(function () {
    'use strict';

    var LABELS = {
        ja: { open: '写真を拡大表示', close: '閉じる', prev: '前の写真', next: '次の写真' },
        en: { open: 'View larger photo', close: 'Close', prev: 'Previous photo', next: 'Next photo' },
        'zh-cn': { open: '放大查看照片', close: '关闭', prev: '上一张', next: '下一张' },
        'zh-tw': { open: '放大檢視照片', close: '關閉', prev: '上一張', next: '下一張' }
    };

    function init() {
        var items = Array.prototype.slice.call(
            document.querySelectorAll('#gallery .gallery-grid .gallery-item')
        ).filter(function (item) { return item.querySelector('img'); });
        if (!items.length) return;

        var lang = (document.documentElement.lang || 'ja').toLowerCase();
        var t = LABELS[lang] || LABELS[lang.split('-')[0]] || LABELS.ja;
        var photos = items.map(function (item) {
            var img = item.querySelector('img');
            return { src: img.currentSrc || img.src, alt: img.alt };
        });
        var current = 0;
        var lastFocus = null;

        var box = document.createElement('div');
        box.className = 'rg-lightbox';
        box.setAttribute('role', 'dialog');
        box.setAttribute('aria-modal', 'true');
        box.setAttribute('aria-label', t.open);
        box.hidden = true;
        box.innerHTML =
            '<figure class="rg-lightbox__stage"><img class="rg-lightbox__img" alt="" decoding="async"></figure>' +
            '<button type="button" class="rg-lightbox__btn rg-lightbox__close" aria-label="' + t.close + '">&times;</button>' +
            '<button type="button" class="rg-lightbox__btn rg-lightbox__nav rg-lightbox__prev" aria-label="' + t.prev + '">&#8249;</button>' +
            '<button type="button" class="rg-lightbox__btn rg-lightbox__nav rg-lightbox__next" aria-label="' + t.next + '">&#8250;</button>' +
            '<div class="rg-lightbox__count" aria-live="polite"></div>';
        document.body.appendChild(box);

        var bigImg = box.querySelector('.rg-lightbox__img');
        var count = box.querySelector('.rg-lightbox__count');
        var closeBtn = box.querySelector('.rg-lightbox__close');
        if (photos.length < 2) box.classList.add('rg-lightbox--single');

        function preload(i) {
            var p = photos[(i + photos.length) % photos.length];
            var im = new Image();
            im.src = p.src;
        }

        function show(i) {
            current = (i + photos.length) % photos.length;
            bigImg.src = photos[current].src;
            bigImg.alt = photos[current].alt;
            count.textContent = (current + 1) + ' / ' + photos.length;
            if (photos.length > 1) { preload(current + 1); preload(current - 1); }
        }

        function open(i) {
            lastFocus = document.activeElement;
            show(i);
            box.hidden = false;
            document.documentElement.classList.add('rg-lightbox-open');
            closeBtn.focus();
        }

        function close() {
            box.hidden = true;
            document.documentElement.classList.remove('rg-lightbox-open');
            if (lastFocus && lastFocus.focus) lastFocus.focus();
        }

        items.forEach(function (item, i) {
            item.classList.add('rg-zoomable');
            item.setAttribute('role', 'button');
            item.setAttribute('tabindex', '0');
            item.setAttribute('aria-label', t.open + ' (' + (i + 1) + ' / ' + photos.length + ')');
            item.addEventListener('click', function () { open(i); });
            item.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(i); }
            });
        });

        closeBtn.addEventListener('click', close);
        box.querySelector('.rg-lightbox__prev').addEventListener('click', function () { show(current - 1); });
        box.querySelector('.rg-lightbox__next').addEventListener('click', function () { show(current + 1); });
        // A click on the dark backdrop (not the photo or a button) closes.
        box.addEventListener('click', function (e) {
            if (e.target === box || e.target.classList.contains('rg-lightbox__stage')) close();
        });

        document.addEventListener('keydown', function (e) {
            if (box.hidden) return;
            if (e.key === 'Escape') close();
            else if (e.key === 'ArrowLeft') show(current - 1);
            else if (e.key === 'ArrowRight') show(current + 1);
            else if (e.key === 'Tab') {
                // Keep focus inside the dialog.
                var f = Array.prototype.filter.call(box.querySelectorAll('button'), function (b) {
                    return b.offsetParent !== null;
                });
                var first = f[0], last = f[f.length - 1];
                if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
                else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
            }
        });

        // Horizontal swipe changes photo; pinch (2+ fingers) is left alone.
        var startX = null, startY = null;
        box.addEventListener('touchstart', function (e) {
            if (e.touches.length !== 1) { startX = null; return; }
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        }, { passive: true });
        box.addEventListener('touchmove', function (e) {
            if (e.touches.length !== 1) startX = null;
        }, { passive: true });
        box.addEventListener('touchend', function (e) {
            if (startX === null || photos.length < 2) return;
            var dx = e.changedTouches[0].clientX - startX;
            var dy = e.changedTouches[0].clientY - startY;
            startX = null;
            if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) {
                show(dx < 0 ? current + 1 : current - 1);
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
