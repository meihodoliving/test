/*!
 * 資金表 → 現金出納帳 — 画面制御
 * 判定と検算は cashbook.js、xlsx の読み取りは xlsx.js、共通の変換は ../core.js。
 */
(function () {
  'use strict';

  var C = window.BOCore, CB = window.BOCashbook, X = window.BOXlsx;
  var KEY = 'meihodo.cashbook.v1';

  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
  var seq = 0;
  function uid(p) { seq++; return (p || 'x') + '-' + Date.now().toString(36) + '-' + seq.toString(36); }
  function today() { return C.ymd(new Date()); }
  function thisMonth() { return today().slice(0, 7); }

  function download(name, text, mime) {
    var body = (mime || '').indexOf('csv') >= 0 ? '﻿' + text : text;
    var blob = new Blob([body], { type: (mime || 'text/plain') + ';charset=utf-8' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url; a.download = name;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  function readTextFile(file, encoding) {
    return new Promise(function (resolve, reject) {
      function read(enc) {
        var fr = new FileReader();
        fr.onerror = function () { reject(fr.error); };
        fr.onload = function () { resolve(String(fr.result || '')); };
        fr.readAsText(file, enc);
      }
      if (encoding && encoding !== 'auto') return read(encoding);
      var fr = new FileReader();
      fr.onerror = function () { reject(fr.error); };
      fr.onload = function () {
        var t = String(fr.result || '');
        if (t.indexOf('�') >= 0) read('shift_jis'); else resolve(t);
      };
      fr.readAsText(file, 'utf-8');
    });
  }

  // ------------------------------------------------------------ 状態

  function emptyMonth(label) {
    return {
      label: label,
      openingBalance: 0,
      openingIsEstimate: true,
      targetNet: null,
      columns: null,
      sheetName: null,
      entries: [],
      skippedRows: [],
      bankTxs: [],
      sourceHasColor: false,
      updatedAt: null
    };
  }

  function defaultState() {
    var m = thisMonth();
    var s = { version: 1, currentMonth: m, months: {}, rules: [], settings: { amountTolerance: 0, dateWindow: 5 } };
    s.months[m] = emptyMonth(m);
    return s;
  }

  var state = defaultState();
  var ui = { filter: { status: 'review', text: '' }, splitting: null, pendingSheets: null };

  function month() {
    if (!state.months[state.currentMonth]) state.months[state.currentMonth] = emptyMonth(state.currentMonth);
    return state.months[state.currentMonth];
  }

  function load() {
    var raw;
    try { raw = localStorage.getItem(KEY); } catch (e) {
      msg('data-msg', 'このブラウザではデータを保存できません（プライベートモードの可能性）。');
      return;
    }
    if (!raw) return;
    try {
      var p = JSON.parse(raw);
      state = Object.assign(defaultState(), p);
      state.settings = Object.assign({ amountTolerance: 0, dateWindow: 5 }, p.settings || {});
      if (!state.months || !Object.keys(state.months).length) state = defaultState();
      if (!state.months[state.currentMonth]) state.currentMonth = Object.keys(state.months)[0];
    } catch (e) {
      msg('data-msg', '保存データを読み込めませんでした。バックアップから復元してください。');
    }
  }

  var timer = null;
  function save() {
    clearTimeout(timer);
    timer = setTimeout(function () {
      timer = null;
      try {
        month().updatedAt = today();
        localStorage.setItem(KEY, JSON.stringify(state));
        var el = $('#save-state');
        el.textContent = '保存済み ' + new Date().toLocaleTimeString('ja-JP');
        el.classList.add('is-saved');
      } catch (e) {
        $('#save-state').textContent = '保存できません';
        msg('data-msg', '保存に失敗しました。バックアップを書き出してください。');
      }
    }, 200);
  }

  // 遅延書き込みが残ったままタブを閉じられても失わないよう、離脱時に必ず吐き出す
  function flush() {
    if (!timer) return;
    clearTimeout(timer); timer = null;
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* 保存できない環境では何もしない */ }
  }

  function msg(id, text) { var el = document.getElementById(id); if (el) el.textContent = text; }
  function commit() { save(); render(); }

  // ------------------------------------------------------------ 判定

  function matchOptions() {
    return {
      amountTolerance: Number(state.settings.amountTolerance) || 0,
      dateWindow: Number(state.settings.dateWindow) || 5
    };
  }

  // 確定済みの判断は保持したまま、未確定分だけを付け直す
  function reclassify() {
    var m = month();
    m.entries = CB.classifyAll(m.entries, m.bankTxs, state.rules, matchOptions());
  }

  // ------------------------------------------------------------ 描画

  function render() {
    renderMonthSelect();
    renderMonthForm();
    renderFundPreview();
    renderBankPreview();
    renderSort();
    renderRecon();
    renderBook();
    renderRules();
    renderSettings();
  }

  function renderMonthSelect() {
    var keys = Object.keys(state.months).sort();
    $('#month-select').innerHTML = keys.map(function (k) {
      return '<option value="' + esc(k) + '"' + (k === state.currentMonth ? ' selected' : '') + '>' + esc(k) + '</option>';
    }).join('');
  }

  function renderMonthForm() {
    var m = month();
    $('#m-label').value = m.label || state.currentMonth;
    $('#m-opening').value = m.openingBalance || 0;
    $('#m-estimate').checked = !!m.openingIsEstimate;
    $('#m-target').value = m.targetNet == null ? '' : m.targetNet;
  }

  function toneChip(tone) {
    var label = { blue: '青', red: '赤', black: '黒', other: '他' }[tone] || '—';
    return '<span class="tone tone--' + (tone || 'other') + '">' + label + '</span>';
  }

  function verdictChip(d) {
    var map = { cash: ['cash', '現金'], bank: ['bank', '銀行'], exclude: ['exclude', '除外'] };
    var v = map[d] || ['none', '未判定'];
    return '<span class="verdict verdict--' + v[0] + '">' + v[1] + '</span>';
  }

  function renderFundPreview() {
    var m = month();
    if (!m.entries.length) {
      $('#fund-preview').innerHTML = '<p class="empty">資金表がまだ読み込まれていません。</p>';
      return;
    }
    var rows = m.entries.slice(0, 8).map(function (e) {
      return '<tr><td>' + esc(e.date) + '</td><td>' + toneChip(e.tone) + ' ' + esc(e.description) + '</td>' +
        '<td class="num">' + (e.inflow ? esc(C.yen(e.inflow)) : '') + '</td>' +
        '<td class="num">' + (e.outflow ? esc(C.yen(e.outflow)) : '') + '</td></tr>';
    }).join('');
    $('#fund-preview').innerHTML =
      '<p class="hint">' + m.entries.length + '件' +
      (m.sourceHasColor ? '（文字色を読み取りました）' : '（<strong>色の情報がありません</strong>。CSVから読んだ場合、判定は通帳とルールのみで行います）') +
      (m.sheetName ? '／シート「' + esc(m.sheetName) + '」' : '') + '</p>' +
      '<table><thead><tr><th>日付</th><th>摘要</th><th class="num">入金</th><th class="num">出金</th></tr></thead><tbody>' +
      rows + '</tbody></table>' +
      (m.entries.length > 8 ? '<p class="hint">…ほか ' + (m.entries.length - 8) + '件</p>' : '') +
      skippedHtml(m.skippedRows);
  }

  // 集計に入れなかった行は必ず見せる（金額0のATM行など、分割が要るものが混ざる）
  function skippedHtml(list) {
    if (!list || !list.length) return '';
    return '<div class="judge judge--warn" style="margin-top:1rem">' +
      '<strong>集計に入れていない行が ' + list.length + '件あります。</strong>' +
      '金額欄が空か0の行です。ATM引き出しのように内訳を分ける必要がある行が含まれていないか確認してください。' +
      '<ul style="margin:.5rem 0 0;padding-left:1.2rem">' +
      list.slice(0, 10).map(function (r) {
        return '<li>' + (r.date ? esc(r.date) + '　' : '') + esc(r.description || '(摘要なし)') +
          '　<span class="hint">' + esc(r.reason) + '</span></li>';
      }).join('') +
      (list.length > 10 ? '<li class="hint">…ほか ' + (list.length - 10) + '件</li>' : '') +
      '</ul></div>';
  }

  function renderBankPreview() {
    var m = month();
    if (!m.bankTxs.length) {
      $('#bank-preview').innerHTML = '<p class="empty">通帳がまだ読み込まれていません。</p>';
      return;
    }
    var net = m.bankTxs.reduce(function (a, t) { return a + t.amount; }, 0);
    $('#bank-preview').innerHTML =
      '<p class="hint">' + m.bankTxs.length + '件／通帳上の動き 合計 ' + esc(C.yen(net)) + '</p>' +
      '<table><thead><tr><th>日付</th><th>摘要</th><th class="num">金額</th></tr></thead><tbody>' +
      m.bankTxs.slice(0, 8).map(function (t) {
        return '<tr><td>' + esc(t.date) + '</td><td>' + esc(t.description) + '</td>' +
          '<td class="num ' + (t.amount > 0 ? 'amount-in' : 'amount-out') + '">' + esc(C.yen(t.amount)) + '</td></tr>';
      }).join('') + '</tbody></table>' +
      (m.bankTxs.length > 8 ? '<p class="hint">…ほか ' + (m.bankTxs.length - 8) + '件</p>' : '');
  }

  // 分割した親は一覧から隠す（子で見る）
  function liveEntries() {
    var m = month();
    var parents = Object.create(null);
    m.entries.forEach(function (e) { if (e.splitOf) parents[e.splitOf] = true; });
    return m.entries.filter(function (e) { return !parents[e.id]; });
  }

  function filteredEntries() {
    var f = ui.filter;
    var q = C.normalizeName(f.text);
    return liveEntries().filter(function (e) {
      if (f.status === 'review' && (e.confirmed || (e.confident && e.decision))) return false;
      if (f.status === 'cash' && e.decision !== 'cash') return false;
      if (f.status === 'bank' && e.decision !== 'bank') return false;
      if (f.status === 'exclude' && e.decision !== 'exclude') return false;
      if (f.status === 'none' && e.decision) return false;
      if (q && C.normalizeName(e.description + ' ' + (e.account || '')).indexOf(q) < 0) return false;
      return true;
    }).sort(function (a, b) {
      if (a.date !== b.date) return a.date < b.date ? -1 : 1;
      return (a.line || 0) - (b.line || 0);
    });
  }

  function renderSort() {
    var live = liveEntries();
    var confirmed = live.filter(function (e) { return e.confirmed; }).length;
    var confident = live.filter(function (e) { return !e.confirmed && e.confident && e.decision; }).length;
    var review = live.length - confirmed - confident;

    $('#sort-summary').innerHTML =
      '<div><div class="hint">資金表の行</div><b>' + live.length + '</b> 件</div>' +
      '<div><div class="hint">確定済み</div><b>' + confirmed + '</b> 件</div>' +
      '<div><div class="hint">裏取り済み（未確定）</div><b>' + confident + '</b> 件</div>' +
      '<div><div class="hint">要確認</div><b>' + review + '</b> 件</div>';

    $('#confirm-confident').disabled = confident === 0;

    var list = filteredEntries();
    if (!list.length) {
      $('#sort-table').innerHTML = '<p class="empty">該当する行がありません。</p>';
      return;
    }

    var body = list.map(function (e) {
      var needs = !e.confirmed && !(e.confident && e.decision);
      var amount = e.inflow ? C.yen(e.inflow) : C.yen(-e.outflow);
      var main =
        '<tr class="' + (needs ? 'needs-check' : '') + '">' +
        '<td>' + esc(e.date) + '</td>' +
        '<td>' + toneChip(e.tone) + ' ' + esc(e.description) +
          (e.splitOf ? ' <span class="hint">(分割)</span>' : '') +
          '<span class="why">' + esc(e.reason || '') + '</span></td>' +
        '<td class="num ' + (e.inflow ? 'amount-in' : 'amount-out') + '">' + esc(amount) + '</td>' +
        '<td>' + verdictChip(e.decision) +
          (e.confirmed ? ' <span class="confirmed-mark">確定</span>' : '') + '</td>' +
        '<td class="num">' +
          '<button class="btn btn--sm" data-set="cash" data-id="' + esc(e.id) + '">現金</button> ' +
          '<button class="btn btn--sm" data-set="bank" data-id="' + esc(e.id) + '">銀行</button> ' +
          '<button class="btn btn--sm" data-set="exclude" data-id="' + esc(e.id) + '">除外</button> ' +
          '<button class="btn btn--sm" data-split="' + esc(e.id) + '">分割</button>' +
          (e.confirmed ? ' <button class="btn btn--sm" data-unconfirm="' + esc(e.id) + '">確定解除</button>' : '') +
        '</td></tr>';

      if (ui.splitting === e.id) main += splitFormHtml(e);
      return main;
    }).join('');

    $('#sort-table').innerHTML =
      '<table><thead><tr><th>日付</th><th>摘要</th><th class="num">金額</th><th>判定</th><th class="num">操作</th></tr></thead>' +
      '<tbody>' + body + '</tbody></table>';
  }

  function splitFormHtml(e) {
    var total = e.inflow || e.outflow;
    return '<tr class="split-row"><td colspan="5">' +
      '<div class="split-form" data-for="' + esc(e.id) + '">' +
      '<div class="hint">' + esc(C.yen(total)) + ' を内訳に分けます。合計が元の金額と一致しないと保存できません。</div>' +
      '<div id="split-lines">' + splitLineHtml(e, 0) + splitLineHtml(e, 1) + '</div>' +
      '<div class="split-line">' +
        '<button class="btn btn--sm" id="split-add" type="button">行を足す</button>' +
        '<span class="split-total" id="split-total"></span>' +
        '<span class="spacer"></span>' +
        '<button class="btn btn--primary btn--sm" id="split-save" type="button">分割して保存</button> ' +
        '<button class="btn btn--sm" id="split-cancel" type="button">やめる</button>' +
      '</div></div></td></tr>';
  }

  function splitLineHtml(e, i) {
    return '<div class="split-line">' +
      '<input type="number" class="split-amount" step="1" min="0" placeholder="金額">' +
      '<input type="text" class="split-desc" placeholder="摘要（例: 現金引き出し）">' +
      '<input type="text" class="split-account" placeholder="科目">' +
      '<select class="split-decision">' +
        '<option value="cash">現金</option><option value="bank">銀行</option><option value="exclude">除外</option>' +
      '</select></div>';
  }

  function renderRecon() {
    var m = month();
    var r = CB.reconcile({ entries: m.entries, bankTxs: m.bankTxs, targetNet: m.targetNet });

    var lines = [
      ['資金表の増減（現金＋預金）', C.yen(r.fundNet), '入金 ' + C.yen(r.fundIn) + ' − 出金 ' + C.yen(r.fundOut)],
      ['銀行通帳上の動き', C.yen(r.bankNet), m.bankTxs.length + '件'],
      ['現金純増減（計算値）', C.yen(r.expectedCashNet), '上の差引き', true],
      ['現金と確定した取引の合計', C.yen(r.cashNet), '入金 ' + C.yen(r.cashIn) + ' − 出金 ' + C.yen(r.cashOut)],
      ['差異', C.yen(r.gap), r.balanced ? '一致' : '未仕分けか判定誤りがあります', true]
    ];

    var html = '<div class="recon-grid">' + lines.map(function (l) {
      return '<div class="recon-line' + (l[3] ? ' recon-line--total' : '') + '">' +
        '<span>' + esc(l[0]) + '<span class="recon-note"> ' + esc(l[2]) + '</span></span>' +
        '<span>' + esc(l[1]) + '</span></div>';
    }).join('') + '</div>';

    if (r.target != null) {
      html += '<div class="recon-grid" style="margin-top:1rem">' +
        '<div class="recon-line"><span>目標値（既知の現金純増減）</span><span>' + esc(C.yen(r.target)) + '</span></div>' +
        '<div class="recon-line"><span>計算値との差</span><span>' + esc(C.yen(r.targetGap)) + '</span></div></div>';
    }

    if (!m.entries.length) {
      html += '<div class="judge judge--warn">資金表がまだ読み込まれていません。</div>';
    } else if (r.unresolved) {
      html += '<div class="judge judge--warn">判定できていない行が ' + r.unresolved + ' 件あります。仕分けを終えてください。</div>';
    } else if (r.balanced && !r.pending) {
      html += '<div class="judge judge--ok">仕分けは検算と一致しています。現金出納帳を確定できます。</div>';
    } else if (r.balanced && r.pending) {
      html += '<div class="judge judge--warn">数字は合っていますが、未確定の行が ' + r.pending + ' 件あります。確認のうえ確定してください。</div>';
    } else {
      html += '<div class="judge judge--bad">差異 ' + C.yen(r.gap) + ' が残っています。' +
        '通帳に出ている取引を現金として残していないか、口座振替を除外し忘れていないかを確認してください。</div>';
    }
    $('#recon').innerHTML = html;
  }

  function renderBook() {
    var m = month();
    var includeUnconfirmed = $('#include-unconfirmed').checked;
    var book = CB.buildCashbook(m.entries, m.openingBalance, { includeUnconfirmed: includeUnconfirmed });

    $('#book-head').innerHTML = '<div class="book-head">' +
      '<div><div class="hint">前月繰越</div><b>' + esc(C.yen(book.opening)) + '</b>' +
        (m.openingIsEstimate ? ' <span class="estimate-flag">※逆算した推定値</span>' : '') + '</div>' +
      '<div><div class="hint">入金合計</div><b>' + esc(C.yen(book.totalIn)) + '</b></div>' +
      '<div><div class="hint">出金合計</div><b>' + esc(C.yen(book.totalOut)) + '</b></div>' +
      '<div><div class="hint">月末残高</div><b>' + esc(C.yen(book.closing)) + '</b></div></div>';

    if (!book.rows.length) {
      $('#book-table').innerHTML = '<p class="empty">現金と確定した取引がまだありません。仕分けで確定してください。</p>';
      return;
    }
    $('#book-table').innerHTML =
      '<table><thead><tr><th>日付</th><th>摘要</th><th>科目</th>' +
      '<th class="num">入金</th><th class="num">出金</th><th class="num">残高</th></tr></thead><tbody>' +
      '<tr><td></td><td>前月繰越</td><td></td><td class="num"></td><td class="num"></td>' +
      '<td class="num">' + esc(C.yen(book.opening)) + '</td></tr>' +
      book.rows.map(function (r) {
        return '<tr class="' + (r.confirmed ? '' : 'needs-check') + '">' +
          '<td>' + esc(r.date) + '</td><td>' + esc(r.description) +
          (r.confirmed ? '' : ' <span class="hint">(未確定)</span>') + '</td>' +
          '<td>' + esc(r.account || '') + '</td>' +
          '<td class="num amount-in">' + (r.inflow ? esc(C.yen(r.inflow)) : '') + '</td>' +
          '<td class="num amount-out">' + (r.outflow ? esc(C.yen(r.outflow)) : '') + '</td>' +
          '<td class="num">' + esc(C.yen(r.balance)) + '</td></tr>';
      }).join('') +
      '<tr><td></td><td><strong>合計</strong></td><td></td>' +
      '<td class="num"><strong>' + esc(C.yen(book.totalIn)) + '</strong></td>' +
      '<td class="num"><strong>' + esc(C.yen(book.totalOut)) + '</strong></td>' +
      '<td class="num"><strong>' + esc(C.yen(book.closing)) + '</strong></td></tr>' +
      '</tbody></table>';
  }

  function renderRules() {
    if (!state.rules.length) {
      $('#rule-table').innerHTML = '<p class="empty">ルールはまだありません。仕分けで判定を確定するときに登録できます。</p>';
      return;
    }
    $('#rule-table').innerHTML =
      '<table><thead><tr><th>含まれる語</th><th>判定</th><th>根拠</th><th class="num">操作</th></tr></thead><tbody>' +
      state.rules.map(function (r) {
        return '<tr><td>' + esc(r.keyword) + '</td><td>' + verdictChip(r.kind) + '</td>' +
          '<td>' + esc(r.note || '') + '</td>' +
          '<td class="num"><button class="btn btn--sm btn--danger" data-del-rule="' + esc(r.id) + '">削除</button></td></tr>';
      }).join('') + '</tbody></table>';
  }

  function renderSettings() {
    $('#s-tolerance').value = state.settings.amountTolerance;
    $('#s-window').value = state.settings.dateWindow;
  }

  // ------------------------------------------------------------ 読み込み

  function loadFundRows(rows, meta) {
    var m = month();
    var res = CB.readFundTable(rows, { columns: m.columns || undefined });
    if (!res.entries.length) {
      msg('fund-msg', '取引として読める行がありませんでした。列の対応を確認してください。');
      renderColumnMap(res, rows);
      return;
    }
    if (m.entries.length && !confirm('この月にはすでに ' + m.entries.length + '件の資金表が読み込まれています。置き換えますか？（確定した判断も消えます）')) {
      return;
    }
    m.columns = res.columns;
    m.entries = res.entries;
    m.sheetName = meta && meta.sheetName || null;
    m.sourceHasColor = !!(meta && meta.hasColor);
    reclassify();
    m.skippedRows = res.skippedRows || [];
    msg('fund-msg', res.entries.length + '件を読み込みました' +
      (res.skipped ? '／' + res.skipped + '行は集計に入れていません（下に一覧）' : ''));
    renderColumnMap(res, rows);
    commit();
  }

  function renderColumnMap(res, rows) {
    var labels = { date: '日付', description: '摘要', inflow: '入金', outflow: '出金', amount: '金額（符号付き）', balance: '残高', account: '科目' };
    var width = 0;
    (rows || []).slice(0, 12).forEach(function (r) { width = Math.max(width, r ? r.length : 0); });
    var header = res.header || [];

    $('#fund-columns').innerHTML = Object.keys(labels).map(function (key) {
      var opts = ['<option value="-1">（なし）</option>'];
      for (var i = 0; i < width; i++) {
        var h = header[i] != null ? CB.cellText(header[i]) : '';
        opts.push('<option value="' + i + '"' + (res.columns[key] === i ? ' selected' : '') + '>' +
          esc(h || ('列' + (i + 1))) + '</option>');
      }
      return '<label>' + esc(labels[key]) + '<select data-col="' + key + '">' + opts.join('') + '</select></label>';
    }).join('');

    $$('#fund-columns select').forEach(function (sel) {
      sel.addEventListener('change', function () {
        var cols = {};
        $$('#fund-columns select').forEach(function (s) { cols[s.dataset.col] = Number(s.value); });
        month().columns = cols;
        var res2 = CB.readFundTable(rows, { columns: cols });
        month().entries = res2.entries;
        reclassify();
        msg('fund-msg', res2.entries.length + '件を読み込み直しました。');
        commit();
      });
    });
  }

  function initLoad() {
    $('#month-form').addEventListener('submit', function (ev) {
      ev.preventDefault();
      var newLabel = $('#m-label').value || state.currentMonth;
      var m = month();
      if (newLabel !== state.currentMonth) {
        state.months[newLabel] = Object.assign({}, m, { label: newLabel });
        delete state.months[state.currentMonth];
        state.currentMonth = newLabel;
        m = month();
      }
      m.openingBalance = Number($('#m-opening').value) || 0;
      m.openingIsEstimate = $('#m-estimate').checked;
      var t = $('#m-target').value;
      m.targetNet = t === '' ? null : Number(t);
      msg('m-msg', '保存しました。');
      commit();
    });

    $('#month-select').addEventListener('change', function () {
      state.currentMonth = $('#month-select').value;
      ui.splitting = null;
      commit();
    });

    $('#month-new').addEventListener('click', function () {
      var label = prompt('追加する月を入力してください（例: 2026-06）', thisMonth());
      if (!label) return;
      if (!/^\d{4}-\d{2}$/.test(label)) { alert('YYYY-MM の形式で入力してください。'); return; }
      if (!state.months[label]) {
        var prev = Object.keys(state.months).sort().filter(function (k) { return k < label; }).pop();
        state.months[label] = emptyMonth(label);
        // 前月の月末残高を期首として引き継ぐ
        if (prev) {
          var pb = CB.buildCashbook(state.months[prev].entries, state.months[prev].openingBalance);
          state.months[label].openingBalance = pb.closing;
          state.months[label].openingIsEstimate = state.months[prev].openingIsEstimate;
        }
      }
      state.currentMonth = label;
      commit();
    });

    $('#fund-file').addEventListener('change', function (ev) {
      var file = ev.target.files && ev.target.files[0];
      if (!file) return;
      if (!X.supported) {
        msg('fund-msg', 'このブラウザでは .xlsx を開けません。Chrome か Edge の新しい版をお使いください。');
        return;
      }
      msg('fund-msg', '読み込み中…');
      file.arrayBuffer().then(function (buf) {
        return X.read(buf);
      }).then(function (wb) {
        if (!wb.sheets.length) { msg('fund-msg', 'シートが見つかりませんでした。'); return; }
        if (wb.sheets.length > 1) {
          ui.pendingSheets = wb.sheets;
          $('#sheet-picker').hidden = false;
          $('#sheet-select').innerHTML = wb.sheets.map(function (s, i) {
            return '<option value="' + i + '">' + esc(s.name) + '（' + s.rows.length + '行）</option>';
          }).join('');
          msg('fund-msg', 'シートを選んでください。');
          return;
        }
        $('#sheet-picker').hidden = true;
        loadFundRows(wb.sheets[0].rows, { sheetName: wb.sheets[0].name, hasColor: true });
      }).catch(function (err) {
        msg('fund-msg', '読み込めませんでした：' + (err && err.message ? err.message : err));
      });
      ev.target.value = '';
    });

    $('#sheet-apply').addEventListener('click', function () {
      if (!ui.pendingSheets) return;
      var s = ui.pendingSheets[Number($('#sheet-select').value) || 0];
      $('#sheet-picker').hidden = true;
      loadFundRows(s.rows, { sheetName: s.name, hasColor: true });
      ui.pendingSheets = null;
    });

    $('#fund-csv').addEventListener('change', function (ev) {
      var file = ev.target.files && ev.target.files[0];
      if (!file) return;
      readTextFile(file, 'auto').then(function (text) {
        loadFundRows(C.parseCSV(text), { sheetName: file.name, hasColor: false });
      });
      ev.target.value = '';
    });

    $('#bank-file').addEventListener('change', function (ev) {
      var file = ev.target.files && ev.target.files[0];
      if (!file) return;
      readTextFile(file, 'auto').then(function (text) {
        $('#bank-text').value = text;
        parseBank();
      });
      ev.target.value = '';
    });

    $('#bank-parse').addEventListener('click', parseBank);

    $('#run-classify').addEventListener('click', function () {
      reclassify();
      $$('.tab').forEach(function (t) { t.classList.toggle('is-active', t.dataset.tab === 'sort'); });
      $$('.panel').forEach(function (p) { p.classList.toggle('is-active', p.id === 'panel-sort'); });
      commit();
    });
  }

  function parseBank() {
    var text = $('#bank-text').value;
    if (!text.trim()) { msg('bank-msg', 'CSVを貼り付けるか、ファイルを選んでください。'); return; }
    var res = C.parseBankCSV(text);
    month().bankTxs = res.rows;
    reclassify();
    msg('bank-msg', res.rows.length + '件を読み込みました' + (res.skipped ? '／' + res.skipped + '行を読み飛ばしました' : ''));
    commit();
  }

  // ------------------------------------------------------------ 仕分け操作

  function findEntry(id) {
    return month().entries.filter(function (e) { return e.id === id; })[0];
  }

  function initSort() {
    ['#q-status', '#q-text'].forEach(function (sel) {
      $(sel).addEventListener('input', function () {
        ui.filter.status = $('#q-status').value;
        ui.filter.text = $('#q-text').value;
        renderSort();
      });
    });

    $('#confirm-confident').addEventListener('click', function () {
      var n = 0;
      month().entries.forEach(function (e) {
        if (!e.confirmed && e.confident && e.decision) { e.confirmed = true; n++; }
      });
      msg('data-msg', n + '件を確定しました。');
      commit();
    });

    $('#sort-table').addEventListener('click', function (ev) {
      var set = ev.target.closest('button[data-set]');
      var split = ev.target.closest('button[data-split]');
      var un = ev.target.closest('button[data-unconfirm]');

      if (set) {
        var e = findEntry(set.dataset.id);
        if (!e) return;
        e.decision = set.dataset.set;
        e.confirmed = true;
        e.confident = true;
        e.reason = '確認して確定（' + { cash: '現金', bank: '銀行取引', exclude: '除外' }[e.decision] + '）';
        offerRule(e);
        commit();
        return;
      }
      if (un) {
        var e2 = findEntry(un.dataset.unconfirm);
        if (!e2) return;
        e2.confirmed = false;
        reclassify();
        commit();
        return;
      }
      if (split) {
        ui.splitting = ui.splitting === split.dataset.split ? null : split.dataset.split;
        renderSort();
        bindSplitForm();
      }
    });
  }

  // 確定のたびに、同じ判断を次回も使うか尋ねる
  function offerRule(entry) {
    var key = (entry.description || '').trim();
    if (!key) return;
    var already = state.rules.some(function (r) { return C.normalizeName(r.keyword) === C.normalizeName(key); });
    if (already) return;
    if (!confirm('「' + key + '」を含む取引は、今後も同じ判定にしますか？\n（ルールとして保存すると翌月以降は自動で当たります）')) return;
    var note = prompt('判断の根拠を残しておけます（任意）', entry.decision === 'exclude' ? '口座振替のため対象外' : '');
    state.rules.push({ id: uid('rule'), keyword: key, kind: entry.decision, note: note || '' });
  }

  function bindSplitForm() {
    var form = $('.split-form');
    if (!form) return;
    var entry = findEntry(form.dataset.for);
    if (!entry) return;
    var total = entry.inflow || entry.outflow;

    function refresh() {
      var sum = $$('.split-amount', form).reduce(function (a, i) { return a + (Number(i.value) || 0); }, 0);
      var el = $('#split-total');
      el.textContent = '内訳合計 ' + C.yen(sum) + ' ／ 元の金額 ' + C.yen(total) +
        (sum === total ? '（一致）' : '（差 ' + C.yen(total - sum) + '）');
      el.className = 'split-total ' + (sum === total ? 'is-ok' : 'is-bad');
    }

    form.addEventListener('input', refresh);
    refresh();

    $('#split-add').addEventListener('click', function () {
      $('#split-lines').insertAdjacentHTML('beforeend', splitLineHtml(entry, 0));
      refresh();
    });
    $('#split-cancel').addEventListener('click', function () {
      ui.splitting = null;
      renderSort();
    });
    $('#split-save').addEventListener('click', function () {
      var parts = $$('.split-line', $('#split-lines')).map(function (line) {
        return {
          amount: Number($('.split-amount', line).value) || 0,
          description: $('.split-desc', line).value.trim(),
          account: $('.split-account', line).value.trim(),
          decision: $('.split-decision', line).value,
          reason: '分割して再分類'
        };
      }).filter(function (p) { return p.amount > 0; });

      var res = CB.splitEntry(entry, parts);
      if (!res.ok) { alert(res.error); return; }
      res.entries.forEach(function (child) {
        child.confirmed = true;
        child.confident = true;
        month().entries.push(child);
      });
      ui.splitting = null;
      msg('data-msg', '分割しました。元の行は集計から外れます。');
      commit();
    });
  }

  // ------------------------------------------------------------ 出納帳・ルール・データ

  function initBook() {
    $('#include-unconfirmed').addEventListener('change', renderBook);
    $('#book-print').addEventListener('click', function () { window.print(); });
    $('#book-csv').addEventListener('click', function () {
      var m = month();
      var book = CB.buildCashbook(m.entries, m.openingBalance, { includeUnconfirmed: $('#include-unconfirmed').checked });
      download('現金出納帳_' + m.label + '.csv', C.toCSV(CB.cashbookToRows(book)), 'text/csv');
    });
  }

  function initRules() {
    $('#rule-form').addEventListener('submit', function (ev) {
      ev.preventDefault();
      state.rules.push({
        id: uid('rule'),
        keyword: $('#r-keyword').value.trim(),
        kind: $('#r-kind').value,
        note: $('#r-note').value.trim()
      });
      $('#rule-form').reset();
      reclassify();
      commit();
    });

    $('#rule-table').addEventListener('click', function (ev) {
      var btn = ev.target.closest('button[data-del-rule]');
      if (!btn) return;
      state.rules = state.rules.filter(function (r) { return r.id !== btn.dataset.delRule; });
      reclassify();
      commit();
    });
  }

  function initData() {
    $('#settings-form').addEventListener('submit', function (ev) {
      ev.preventDefault();
      state.settings.amountTolerance = Number($('#s-tolerance').value) || 0;
      state.settings.dateWindow = Number($('#s-window').value) || 0;
      reclassify();
      msg('data-msg', '保存しました。');
      commit();
    });

    $('#backup-export').addEventListener('click', function () {
      download('現金出納帳_バックアップ_' + today() + '.json', JSON.stringify(state, null, 2), 'application/json');
      msg('data-msg', 'バックアップを書き出しました。');
    });

    $('#backup-import').addEventListener('change', function (ev) {
      var file = ev.target.files && ev.target.files[0];
      if (!file) return;
      readTextFile(file, 'utf-8').then(function (text) {
        var p;
        try { p = JSON.parse(text); } catch (e) { msg('data-msg', 'JSONとして読めませんでした。'); return; }
        if (!p || !p.months) { msg('data-msg', 'このファイルはバックアップではないようです。'); return; }
        if (!confirm('現在のデータを置き換えます。よろしいですか？')) return;
        state = Object.assign(defaultState(), p);
        msg('data-msg', '読み込みました。');
        commit();
      });
      ev.target.value = '';
    });

    $('#wipe').addEventListener('click', function () {
      if (!confirm('すべてのデータを消去します。元に戻せません。バックアップは書き出しましたか？')) return;
      state = defaultState();
      msg('data-msg', 'データを消去しました。');
      commit();
    });
  }

  function initTabs() {
    $('#tabs').addEventListener('click', function (ev) {
      var btn = ev.target.closest('.tab');
      if (!btn) return;
      $$('.tab').forEach(function (t) { t.classList.toggle('is-active', t === btn); });
      $$('.panel').forEach(function (p) { p.classList.toggle('is-active', p.id === 'panel-' + btn.dataset.tab); });
    });
  }

  // ------------------------------------------------------------ 起動

  function init() {
    if (!C || !CB || !X) {
      document.body.innerHTML = '<p style="padding:2rem">必要なファイルを読み込めませんでした。back-office 一式が揃っているか確認してください。</p>';
      return;
    }
    load();
    window.addEventListener('pagehide', flush);
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'hidden') flush();
    });
    initTabs(); initLoad(); initSort(); initBook(); initRules(); initData();
    render();
    $('#save-state').textContent = Object.keys(state.months).length + 'か月分';
    if (!X.supported) {
      msg('fund-msg', 'このブラウザは .xlsx の読み込みに対応していません（Chrome / Edge の新しい版が必要です）。');
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
