/*!
 * 鳴鳳堂 バックオフィス — コアロジック（DOM 非依存・副作用なし）
 *
 * ここには「計算」だけを置く。画面描画と localStorage は app.js の担当。
 * 分けている理由は、この層だけ Node で自動テストできるようにするため。
 *   node --test back-office/test/
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.BOCore = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // ---------------------------------------------------------------- 文字列

  // 全角英数字・記号 → 半角
  function toHalfWidth(s) {
    return String(s == null ? '' : s)
      .replace(/[Ａ-Ｚａ-ｚ０-９]/g, function (c) {
        return String.fromCharCode(c.charCodeAt(0) - 0xfee0);
      })
      .replace(/[　]/g, ' ')
      .replace(/[－ー−―‐]/g, '-');
  }

  // 半角カタカナ → 全角カタカナ（銀行の摘要は半角カナで来ることが多い）
  var HANKAKU_KANA = 'ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜｦﾝｧｨｩｪｫｯｬｭｮ';
  var ZENKAKU_KANA = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲンァィゥェォッャュョ';
  var DAKUTEN = {
    'ｶﾞ': 'ガ', 'ｷﾞ': 'ギ', 'ｸﾞ': 'グ', 'ｹﾞ': 'ゲ', 'ｺﾞ': 'ゴ',
    'ｻﾞ': 'ザ', 'ｼﾞ': 'ジ', 'ｽﾞ': 'ズ', 'ｾﾞ': 'ゼ', 'ｿﾞ': 'ゾ',
    'ﾀﾞ': 'ダ', 'ﾁﾞ': 'ヂ', 'ﾂﾞ': 'ヅ', 'ﾃﾞ': 'デ', 'ﾄﾞ': 'ド',
    'ﾊﾞ': 'バ', 'ﾋﾞ': 'ビ', 'ﾌﾞ': 'ブ', 'ﾍﾞ': 'ベ', 'ﾎﾞ': 'ボ',
    'ﾊﾟ': 'パ', 'ﾋﾟ': 'ピ', 'ﾌﾟ': 'プ', 'ﾍﾟ': 'ペ', 'ﾎﾟ': 'ポ',
    'ｳﾞ': 'ヴ'
  };

  function kanaToZenkaku(s) {
    var out = String(s == null ? '' : s);
    Object.keys(DAKUTEN).forEach(function (k) {
      out = out.split(k).join(DAKUTEN[k]);
    });
    var res = '';
    for (var i = 0; i < out.length; i++) {
      var idx = HANKAKU_KANA.indexOf(out[i]);
      res += idx >= 0 ? ZENKAKU_KANA[idx] : out[i];
    }
    return res;
  }

  // カタカナ → ひらがな（表記ゆれを吸収して突き合わせるため）
  function toHiragana(s) {
    return String(s == null ? '' : s).replace(/[ァ-ヶ]/g, function (c) {
      return String.fromCharCode(c.charCodeAt(0) - 0x60);
    });
  }

  // 法人格・記号・空白を落として比較用のキーにする
  var LEGAL_FORMS = [
    '株式会社', '有限会社', '合同会社', '合資会社', '合名会社', '一般社団法人', '公益社団法人',
    '一般財団法人', '公益財団法人', '医療法人', '学校法人', '宗教法人', '社会福祉法人',
    'カブシキガイシャ', 'カブシキカイシャ', 'ユウゲンガイシャ', 'ユウゲンカイシャ',
    '(株)', '（株）', '(有)', '（有）', 'ｶ)', 'ｶ）', 'ﾕ)', 'ﾕ）', 'カ)', 'ユ)'
  ];

  function normalizeName(s) {
    var out = kanaToZenkaku(toHalfWidth(s));
    LEGAL_FORMS.forEach(function (w) { out = out.split(w).join(''); });
    out = toHiragana(out).toLowerCase();
    return out.replace(/[\s\-_.,、。・:：;；'"`()（）\[\]【】<>＜＞*＊/／\\]/g, '');
  }

  // bigram の Dice 係数（0..1）。1 文字語は完全一致のみ 1。
  function nameSimilarity(a, b) {
    var x = normalizeName(a), y = normalizeName(b);
    if (!x || !y) return 0;
    if (x === y) return 1;
    if (x.length < 2 || y.length < 2) return x === y ? 1 : 0;
    // 片方がもう片方を含む（例: 摘要 "アソカンコウ(カ" と取引先 "阿蘇観光"）
    if (x.indexOf(y) >= 0 || y.indexOf(x) >= 0) {
      return 0.9 + 0.1 * (Math.min(x.length, y.length) / Math.max(x.length, y.length));
    }
    var grams = Object.create(null), hit = 0, i;
    for (i = 0; i < x.length - 1; i++) {
      var g = x.substr(i, 2);
      grams[g] = (grams[g] || 0) + 1;
    }
    for (i = 0; i < y.length - 1; i++) {
      var h = y.substr(i, 2);
      if (grams[h] > 0) { grams[h]--; hit++; }
    }
    return (2 * hit) / ((x.length - 1) + (y.length - 1));
  }

  // ---------------------------------------------------------------- 数値

  // "¥1,234"、"1,234円"、"▲1,234"、"(1,234)" などを数値に。空欄は null。
  function parseAmount(v) {
    if (typeof v === 'number') return isFinite(v) ? v : null;
    if (v == null) return null;
    var s = toHalfWidth(v).trim();
    if (!s) return null;
    var neg = /^[(（]/.test(s) || /^[▲△\-]/.test(s);
    s = s.replace(/[¥￥円,\s()（）▲△+\-]/g, '');
    if (!s || !/^\d+(\.\d+)?$/.test(s)) return null;
    var n = parseFloat(s);
    if (!isFinite(n)) return null;
    return neg ? -n : n;
  }

  function yen(n) {
    var v = Math.round(Number(n) || 0);
    return (v < 0 ? '-' : '') + '¥' + Math.abs(v).toLocaleString('ja-JP');
  }

  // 税抜金額から税込を求める（端数は切り捨て＝日本の商習慣の既定）
  function withTax(amount, rate) {
    var r = Number(rate);
    if (!isFinite(r) || r <= 0) return Math.round(Number(amount) || 0);
    return Math.floor((Number(amount) || 0) * (1 + r / 100));
  }

  // ---------------------------------------------------------------- 日付
  // 内部表現はすべて 'YYYY-MM-DD' 文字列。Date は計算のときだけ使い、
  // タイムゾーンずれを避けるためローカル時刻のコンストラクタのみ用いる。

  function pad2(n) { return (n < 10 ? '0' : '') + n; }

  function ymd(d) {
    return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate());
  }

  function toDate(s) {
    if (s instanceof Date) return new Date(s.getFullYear(), s.getMonth(), s.getDate());
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(s || ''));
    if (!m) return null;
    return new Date(+m[1], +m[2] - 1, +m[3]);
  }

  function isValidYmd(s) {
    var d = toDate(s);
    return !!d && ymd(d) === s;
  }

  // 銀行 CSV の日付表記をひととおり吸収する。
  // 年が無い "04/01" 形式は yearHint（既定は当年）を補う。
  function parseDate(v, yearHint) {
    if (v instanceof Date) return ymd(v);
    var s = toHalfWidth(v).trim();
    if (!s) return null;
    var m;
    // 2026-04-01 / 2026/4/1 / 2026.4.1 / 2026年4月1日
    m = /^(\d{4})\s*[-/.年]\s*(\d{1,2})\s*[-/.月]\s*(\d{1,2})/.exec(s);
    if (m) return safeYmd(+m[1], +m[2], +m[3]);
    // 20260401
    m = /^(\d{4})(\d{2})(\d{2})$/.exec(s);
    if (m) return safeYmd(+m[1], +m[2], +m[3]);
    // 04/01 （年なし）
    m = /^(\d{1,2})\s*[-/.月]\s*(\d{1,2})/.exec(s);
    if (m) {
      var y = yearHint || new Date().getFullYear();
      return safeYmd(y, +m[1], +m[2]);
    }
    // R8.4.1 / 令和8年4月1日
    m = /^(?:令和|R|r)\s*(\d{1,2})\s*[-/.年]\s*(\d{1,2})\s*[-/.月]\s*(\d{1,2})/.exec(s);
    if (m) return safeYmd(2018 + +m[1], +m[2], +m[3]);
    return null;
  }

  function safeYmd(y, mo, d) {
    if (mo < 1 || mo > 12 || d < 1 || d > 31) return null;
    var dt = new Date(y, mo - 1, d);
    if (dt.getFullYear() !== y || dt.getMonth() !== mo - 1 || dt.getDate() !== d) return null;
    return ymd(dt);
  }

  function addDays(s, n) {
    var d = toDate(s);
    if (!d) return null;
    d.setDate(d.getDate() + n);
    return ymd(d);
  }

  function endOfMonth(y, mo) { return new Date(y, mo, 0).getDate(); }

  // 月を跨いだうえで日を丸める。day=31 は月末扱い。
  function addMonthsClamped(s, months, day) {
    var d = toDate(s);
    if (!d) return null;
    var y = d.getFullYear(), mo = d.getMonth() + 1 + months;
    y += Math.floor((mo - 1) / 12);
    mo = ((mo - 1) % 12 + 12) % 12 + 1;
    var last = endOfMonth(y, mo);
    var dd = day == null ? d.getDate() : day;
    return safeYmd(y, mo, Math.min(dd, last));
  }

  function daysBetween(a, b) {
    var x = toDate(a), y = toDate(b);
    if (!x || !y) return null;
    return Math.round((y - x) / 86400000);
  }

  function startOfWeek(s) {           // 月曜はじまり
    var d = toDate(s);
    if (!d) return null;
    var w = (d.getDay() + 6) % 7;
    d.setDate(d.getDate() - w);
    return ymd(d);
  }

  /**
   * 締日・支払サイトから支払期日を計算する。
   * terms = { closingDay: 1..31（31=月末）, monthOffset: 0=当月/1=翌月/2=翌々月, payDay: 1..31（31=月末）}
   * 例）月末締め翌月末払い → { closingDay:31, monthOffset:1, payDay:31 }
   *     20日締め翌月10日払い → { closingDay:20, monthOffset:1, payDay:10 }
   */
  function calcDueDate(issueDate, terms) {
    var d = toDate(issueDate);
    if (!d) return null;
    var t = terms || {};
    var closing = Number(t.closingDay) || 31;
    var offset = t.monthOffset == null ? 1 : Number(t.monthOffset);
    var payDay = Number(t.payDay) || 31;

    // 締日をまたいでいたら次の締めに送る
    var carry = 0;
    var lastOfIssueMonth = endOfMonth(d.getFullYear(), d.getMonth() + 1);
    var effClosing = Math.min(closing, lastOfIssueMonth);
    if (d.getDate() > effClosing) carry = 1;

    return addMonthsClamped(issueDate, offset + carry, payDay);
  }

  // 土日を避ける（true=前倒し / 'after'=後ろ倒し）。祝日は持たないので前営業日近似。
  function shiftBusinessDay(s, mode) {
    var d = toDate(s);
    if (!d) return null;
    var dir = mode === 'after' ? 1 : -1;
    while (d.getDay() === 0 || d.getDay() === 6) d.setDate(d.getDate() + dir);
    return ymd(d);
  }

  // ---------------------------------------------------------------- CSV

  function stripBom(text) {
    return String(text || '').replace(/^﻿/, '');
  }

  function detectDelimiter(text) {
    var head = stripBom(text).split(/\r?\n/).slice(0, 5).join('\n');
    var counts = [[',', 0], ['\t', 0], [';', 0]];
    counts.forEach(function (c) {
      c[1] = (head.split(c[0]).length - 1);
    });
    counts.sort(function (a, b) { return b[1] - a[1]; });
    return counts[0][1] > 0 ? counts[0][0] : ',';
  }

  // RFC4180 準拠（引用符内の改行・"" エスケープに対応）
  function parseCSV(text, delimiter) {
    var src = stripBom(text);
    var d = delimiter || detectDelimiter(src);
    var rows = [], row = [], field = '', inQuotes = false, i = 0;
    while (i < src.length) {
      var c = src[i];
      if (inQuotes) {
        if (c === '"') {
          if (src[i + 1] === '"') { field += '"'; i += 2; continue; }
          inQuotes = false; i++; continue;
        }
        field += c; i++; continue;
      }
      if (c === '"') { inQuotes = true; i++; continue; }
      if (c === d) { row.push(field); field = ''; i++; continue; }
      if (c === '\r') { i++; continue; }
      if (c === '\n') { row.push(field); rows.push(row); row = []; field = ''; i++; continue; }
      field += c; i++;
    }
    if (field.length || row.length) { row.push(field); rows.push(row); }
    // 完全な空行は捨てる
    return rows.filter(function (r) {
      return r.some(function (v) { return String(v).trim() !== ''; });
    });
  }

  function toCSV(rows) {
    return rows.map(function (r) {
      return r.map(function (v) {
        var s = v == null ? '' : String(v);
        return /[",\r\n]/.test(s) ? '"' + s.split('"').join('""') + '"' : s;
      }).join(',');
    }).join('\r\n');
  }

  // 見出し行から列の役割を推測する。銀行ごとに表記が違うので別名辞書で吸収。
  var HEADER_ALIASES = {
    date:        ['日付', '取引日', '年月日', 'お取引日', '取引年月日', 'date', '計上日', '入出金日'],
    description: ['摘要', '内容', 'お取引内容', '取引内容', '記事', '備考', 'description', '摘要内容', 'お名前'],
    inflow:      ['入金', '入金額', 'お預り金額', 'お預入額', '預入', '入金金額', '貸方', 'credit', '入金(円)'],
    outflow:     ['出金', '出金額', 'お支払金額', 'お引出額', '引出', '出金金額', '借方', 'debit', '出金(円)'],
    amount:      ['金額', '取引金額', 'amount', '差引金額'],
    balance:     ['残高', '差引残高', 'balance', '残高(円)']
  };

  function guessColumns(headerRow) {
    var map = { date: -1, description: -1, inflow: -1, outflow: -1, amount: -1, balance: -1 };
    (headerRow || []).forEach(function (raw, idx) {
      var h = normalizeName(raw);
      if (!h) return;
      Object.keys(HEADER_ALIASES).forEach(function (key) {
        if (map[key] >= 0) return;
        var hit = HEADER_ALIASES[key].some(function (alias) {
          var a = normalizeName(alias);
          return a && (h === a || h.indexOf(a) >= 0);
        });
        if (hit) map[key] = idx;
      });
    });
    return map;
  }

  function looksLikeHeader(row) {
    // 日付として読める列がひとつも無ければ見出し行とみなす
    return !row.some(function (v) { return parseDate(v); });
  }

  /**
   * 見出し行が無い CSV の列を、値の型と出現率から推定する。
   * 日本の銀行 CSV でよくある並びを想定：
   *   数値列が 1 本 → 符号付き金額 / 2 本 → 金額・残高 / 3 本以上 → 入金・出金・残高
   */
  function inferColumns(body) {
    var map = { date: -1, description: -1, inflow: -1, outflow: -1, amount: -1, balance: -1 };
    var sample = body.slice(0, 20);
    if (!sample.length) return map;
    var width = sample.reduce(function (w, r) { return Math.max(w, r.length); }, 0);
    var stats = [];
    for (var i = 0; i < width; i++) {
      var dateHits = 0, numHits = 0, textLen = 0, filled = 0;
      sample.forEach(function (r) {
        var v = r[i];
        if (v == null || String(v).trim() === '') return;
        filled++;
        if (parseDate(v)) dateHits++;
        else if (parseAmount(v) != null) numHits++;
        else textLen += String(v).length;
      });
      stats.push({ index: i, dateHits: dateHits, numHits: numHits, textLen: textLen, filled: filled });
    }
    var dateCol = stats.filter(function (c) { return c.dateHits > 0 && c.dateHits >= c.filled * 0.6; })
      .sort(function (a, b) { return b.dateHits - a.dateHits || a.index - b.index; })[0];
    if (dateCol) map.date = dateCol.index;

    var numCols = stats.filter(function (c) {
      return c.index !== map.date && c.numHits > 0 && c.numHits >= c.filled * 0.6;
    });
    if (numCols.length === 1) map.amount = numCols[0].index;
    else if (numCols.length === 2) { map.amount = numCols[0].index; map.balance = numCols[1].index; }
    else if (numCols.length >= 3) {
      map.inflow = numCols[0].index;
      map.outflow = numCols[1].index;
      map.balance = numCols[numCols.length - 1].index;
    }

    var textCol = stats.filter(function (c) {
      return c.index !== map.date && c.textLen > 0 &&
        [map.inflow, map.outflow, map.amount, map.balance].indexOf(c.index) < 0;
    }).sort(function (a, b) { return b.textLen - a.textLen; })[0];
    if (textCol) map.description = textCol.index;
    return map;
  }

  /**
   * 銀行明細 CSV → 取引配列。
   * 入金/出金の 2 列型と、符号付き 1 列型（金額のみ）の両方に対応。
   */
  function parseBankCSV(text, options) {
    var opt = options || {};
    var rows = parseCSV(text, opt.delimiter);
    if (!rows.length) return { columns: {}, rows: [], skipped: 0 };
    var headerRow = looksLikeHeader(rows[0]) ? rows[0] : null;
    var body = headerRow ? rows.slice(1) : rows;
    var cols = opt.columns || guessColumns(headerRow || []);

    // 見出しが無い / 推測できない場合は、中身の型から位置を当てる
    if (body.length && (cols.date < 0 || (cols.inflow < 0 && cols.outflow < 0 && cols.amount < 0))) {
      var inferred = inferColumns(body);
      ['date', 'description', 'inflow', 'outflow', 'amount', 'balance'].forEach(function (k) {
        if (cols[k] < 0 && inferred[k] >= 0) cols[k] = inferred[k];
      });
    }

    var out = [], skipped = 0;
    body.forEach(function (r) {
      var date = parseDate(cols.date >= 0 ? r[cols.date] : null, opt.yearHint);
      if (!date) { skipped++; return; }
      var inflow = cols.inflow >= 0 ? parseAmount(r[cols.inflow]) : null;
      var outflow = cols.outflow >= 0 ? parseAmount(r[cols.outflow]) : null;
      var amount = null;
      if (inflow) amount = Math.abs(inflow);
      else if (outflow) amount = -Math.abs(outflow);
      else if (cols.amount >= 0) amount = parseAmount(r[cols.amount]);
      if (amount == null || amount === 0) { skipped++; return; }
      out.push({
        date: date,
        description: String(cols.description >= 0 ? (r[cols.description] || '') : '').trim(),
        amount: amount,
        balance: cols.balance >= 0 ? parseAmount(r[cols.balance]) : null
      });
    });
    return { columns: cols, header: headerRow, rows: out, skipped: skipped };
  }

  // ---------------------------------------------------------------- 消込

  var MATCH_DEFAULTS = {
    amountTolerance: 0,   // 円。振込手数料を差し引かれる場合は 880 など
    dateWindow: 45,       // 期日から前後何日まで候補にするか
    autoThreshold: 65,    // これ以上のスコアで自動消込（金額完全一致＋期日どおり＝70）
    autoGap: 15           // 2位との差がこれ以上あるときだけ自動消込（一意性の担保）
  };

  /**
   * 明細 1 行と債権債務 1 件の一致度を 0..100 で返す。
   * 金額一致を最重視し、取引先名・期日近接で補強する。
   */
  function scoreMatch(entry, tx, options) {
    var o = Object.assign({}, MATCH_DEFAULTS, options || {});
    var reasons = [];
    if (!entry || !tx) return { score: 0, reasons: reasons };
    if (entry.status === 'settled') return { score: 0, reasons: ['決済済み'] };

    // 入金は債権(AR)、出金は債務(AP) にしか当たらない
    var wantKind = tx.amount > 0 ? 'AR' : 'AP';
    if (entry.kind !== wantKind) return { score: 0, reasons: ['入出金の向きが不一致'] };

    var score = 0;
    var txAbs = Math.abs(tx.amount);
    var open = Number(entry.amount) || 0;
    var diff = Math.abs(txAbs - open);

    if (diff === 0) { score += 55; reasons.push('金額が完全一致'); }
    else if (diff <= o.amountTolerance) { score += 50; reasons.push('金額が誤差内（差 ' + yen(diff) + '）'); }
    else if (open > 0 && diff / open <= 0.01) { score += 25; reasons.push('金額が1%以内'); }
    else return { score: 0, reasons: ['金額が不一致'] };

    var sim = Math.max(
      nameSimilarity(tx.description, entry.partyName),
      entry.partyKana ? nameSimilarity(tx.description, entry.partyKana) : 0
    );
    if (sim >= 0.9) { score += 30; reasons.push('取引先名が一致'); }
    else if (sim >= 0.6) { score += 20; reasons.push('取引先名が類似'); }
    else if (sim >= 0.35) { score += 8; reasons.push('取引先名が一部一致'); }

    // 伝票番号が摘要に入っていれば決定打
    if (entry.docNo && normalizeName(tx.description).indexOf(normalizeName(entry.docNo)) >= 0) {
      score += 20; reasons.push('請求番号が摘要に含まれる');
    }

    var delta = entry.dueDate ? daysBetween(entry.dueDate, tx.date) : null;
    var gap = delta == null ? 999 : Math.abs(delta);
    if (gap <= 3) { score += 15; reasons.push('期日どおり'); }
    else if (gap <= 10) { score += 10; reasons.push('期日から' + gap + '日'); }
    else if (gap <= o.dateWindow) { score += 4; reasons.push('期日から' + gap + '日'); }
    else if (entry.dueDate) { score -= 10; reasons.push('期日から離れている（' + gap + '日）'); }

    return { score: Math.max(0, Math.min(100, score)), reasons: reasons };
  }

  // 明細 1 行に対する候補を、スコア降順で返す
  function suggestMatches(entries, tx, options) {
    var list = [];
    (entries || []).forEach(function (e) {
      var r = scoreMatch(e, tx, options);
      if (r.score > 0) list.push({ entryId: e.id, entry: e, score: r.score, reasons: r.reasons });
    });
    list.sort(function (a, b) { return b.score - a.score; });
    return list;
  }

  /**
   * 明細全体を走査し、自動消込してよいペアを決める。
   * 「スコアが閾値以上」かつ「2位と十分な差がある」かつ「その債権債務がまだ他に取られていない」
   * の 3 条件を満たすものだけを auto に入れる。残りは review に落として人が選ぶ。
   */
  function autoMatch(entries, txs, options) {
    var o = Object.assign({}, MATCH_DEFAULTS, options || {});
    var taken = Object.create(null);
    var auto = [], review = [];

    var scored = (txs || []).map(function (tx, i) {
      return { tx: tx, index: i, candidates: suggestMatches(entries, tx, o) };
    });
    // 確信度の高いものから確定させ、取り合いを防ぐ
    scored.sort(function (a, b) {
      return (b.candidates[0] ? b.candidates[0].score : 0) - (a.candidates[0] ? a.candidates[0].score : 0);
    });

    scored.forEach(function (s) {
      var free = s.candidates.filter(function (c) { return !taken[c.entryId]; });
      var top = free[0];
      var second = free[1];
      var unique = top && (!second || top.score - second.score >= o.autoGap);
      if (top && top.score >= o.autoThreshold && unique) {
        taken[top.entryId] = true;
        auto.push({ index: s.index, tx: s.tx, entryId: top.entryId, entry: top.entry, score: top.score, reasons: top.reasons });
      } else {
        review.push({ index: s.index, tx: s.tx, candidates: free.slice(0, 5) });
      }
    });

    auto.sort(function (a, b) { return a.index - b.index; });
    review.sort(function (a, b) { return a.index - b.index; });
    return { auto: auto, review: review };
  }

  // ---------------------------------------------------------------- 集計

  function summarize(entries, today) {
    var t = today || ymd(new Date());
    var s = {
      arOpen: 0, arCount: 0, apOpen: 0, apCount: 0,
      arOverdue: 0, arOverdueCount: 0, apOverdue: 0, apOverdueCount: 0,
      arDue7: 0, apDue7: 0
    };
    var in7 = addDays(t, 7);
    (entries || []).forEach(function (e) {
      if (e.status === 'settled') return;
      var amt = Number(e.amount) || 0;
      var overdue = e.dueDate && e.dueDate < t;
      var soon = e.dueDate && e.dueDate >= t && e.dueDate <= in7;
      if (e.kind === 'AR') {
        s.arOpen += amt; s.arCount++;
        if (overdue) { s.arOverdue += amt; s.arOverdueCount++; }
        if (soon) s.arDue7 += amt;
      } else if (e.kind === 'AP') {
        s.apOpen += amt; s.apCount++;
        if (overdue) { s.apOverdue += amt; s.apOverdueCount++; }
        if (soon) s.apDue7 += amt;
      }
    });
    return s;
  }

  // 取引先別の残高（与信・支払先の偏りを見るため）
  function byParty(entries, kind) {
    var map = Object.create(null);
    (entries || []).forEach(function (e) {
      if (e.kind !== kind || e.status === 'settled') return;
      var key = e.partyName || '(取引先未設定)';
      if (!map[key]) map[key] = { party: key, total: 0, count: 0, oldestDue: null };
      map[key].total += Number(e.amount) || 0;
      map[key].count++;
      if (e.dueDate && (!map[key].oldestDue || e.dueDate < map[key].oldestDue)) map[key].oldestDue = e.dueDate;
    });
    return Object.keys(map).map(function (k) { return map[k]; })
      .sort(function (a, b) { return b.total - a.total; });
  }

  // 滞留年齢表（0-30 / 31-60 / 61-90 / 91日以上）
  function agingBuckets(entries, kind, today) {
    var t = today || ymd(new Date());
    var buckets = [
      { label: '期日前', min: -Infinity, max: -1, total: 0, count: 0 },
      { label: '1-30日', min: 0, max: 30, total: 0, count: 0 },
      { label: '31-60日', min: 31, max: 60, total: 0, count: 0 },
      { label: '61-90日', min: 61, max: 90, total: 0, count: 0 },
      { label: '91日以上', min: 91, max: Infinity, total: 0, count: 0 }
    ];
    (entries || []).forEach(function (e) {
      if (e.kind !== kind || e.status === 'settled') return;
      var over = e.dueDate ? (daysBetween(e.dueDate, t) || 0) : 0;
      for (var i = 0; i < buckets.length; i++) {
        if (over >= buckets[i].min && over <= buckets[i].max) {
          buckets[i].total += Number(e.amount) || 0;
          buckets[i].count++;
          break;
        }
      }
    });
    return buckets;
  }

  /**
   * 資金繰り予測。
   * 期首残高に、未決済の債権(入)・債務(出)を期日で、固定費・定期入金を発生日で足し込み、
   * 各期間の期末残高を出す。期日超過の未決済分は最初の期間に寄せる（まだ回収/支払予定のため）。
   */
  function projectCashflow(input) {
    var o = input || {};
    var entries = o.entries || [];
    var recurring = o.recurring || [];
    var opening = Number(o.openingBalance) || 0;
    var asOf = o.asOf || ymd(new Date());
    var unit = o.unit === 'month' ? 'month' : 'week';
    var count = Number(o.periods) || (unit === 'month' ? 6 : 13);
    var threshold = Number(o.alertThreshold) || 0;

    var periods = [];
    var i;
    if (unit === 'week') {
      var cur = startOfWeek(asOf);
      for (i = 0; i < count; i++) {
        var end = addDays(cur, 6);
        periods.push({ start: cur, end: end, label: formatWeekLabel(cur, end) });
        cur = addDays(cur, 7);
      }
    } else {
      var d0 = toDate(asOf);
      for (i = 0; i < count; i++) {
        var y = d0.getFullYear(), mo = d0.getMonth() + 1 + i;
        y += Math.floor((mo - 1) / 12);
        mo = ((mo - 1) % 12 + 12) % 12 + 1;
        var s = safeYmd(y, mo, 1);
        var e2 = safeYmd(y, mo, endOfMonth(y, mo));
        periods.push({ start: i === 0 ? asOf : s, end: e2, label: y + '年' + mo + '月' });
      }
    }

    periods.forEach(function (p) {
      p.inflow = 0; p.outflow = 0; p.items = [];
      p.confirmedInflow = 0; p.confirmedOutflow = 0;   // 見込み(estimate)を除いた保守的な内訳
    });

    function bucketFor(date) {
      if (!date) return null;
      if (date < periods[0].start) return periods[0];   // 期日超過は初回期間へ
      for (var k = 0; k < periods.length; k++) {
        if (date >= periods[k].start && date <= periods[k].end) return periods[k];
      }
      return null;                                        // 予測期間より先は対象外
    }

    // certainty: 'confirmed'（既定・請求書等で確定） | 'estimate'（見積り・計画段階）
    entries.forEach(function (e) {
      if (e.status === 'settled') return;
      var p = bucketFor(e.dueDate);
      if (!p) return;
      var amt = Number(e.amount) || 0;
      var certainty = e.certainty === 'estimate' ? 'estimate' : 'confirmed';
      var item = { type: e.kind === 'AR' ? 'in' : 'out', name: e.partyName, amount: amt, date: e.dueDate, certainty: certainty };
      if (e.kind === 'AR') {
        p.inflow += amt;
        if (certainty === 'confirmed') p.confirmedInflow += amt;
        p.items.push(item);
      } else if (e.kind === 'AP') {
        p.outflow += amt;
        if (certainty === 'confirmed') p.confirmedOutflow += amt;
        p.items.push(item);
      }
    });

    // 固定費・定期入出金は性質上つねに確定扱い
    recurring.forEach(function (r) {
      var occ = recurringOccurrences(r, periods[0].start, periods[periods.length - 1].end);
      occ.forEach(function (date) {
        var p = bucketFor(date);
        if (!p) return;
        var amt = Number(r.amount) || 0;
        if (r.kind === 'in') {
          p.inflow += amt; p.confirmedInflow += amt;
          p.items.push({ type: 'in', name: r.name, amount: amt, date: date, fixed: true, certainty: 'confirmed' });
        } else {
          p.outflow += amt; p.confirmedOutflow += amt;
          p.items.push({ type: 'out', name: r.name, amount: amt, date: date, fixed: true, certainty: 'confirmed' });
        }
      });
    });

    var bal = opening, min = { balance: Infinity, label: null };
    var confirmedBal = opening, minConfirmed = { balance: Infinity, label: null };
    periods.forEach(function (p) {
      p.opening = bal;
      p.net = p.inflow - p.outflow;
      bal += p.net;
      p.closing = bal;
      p.alert = p.closing < threshold;
      p.shortage = p.closing < 0;
      if (p.closing < min.balance) min = { balance: p.closing, label: p.label, period: p };

      // 見込みを除いた、より保守的な残高（本部への報告はこちらを基準にする）
      p.confirmedOpening = confirmedBal;
      p.confirmedNet = p.confirmedInflow - p.confirmedOutflow;
      confirmedBal += p.confirmedNet;
      p.confirmedClosing = confirmedBal;
      p.confirmedAlert = p.confirmedClosing < threshold;
      p.confirmedShortage = p.confirmedClosing < 0;
      if (p.confirmedClosing < minConfirmed.balance) minConfirmed = { balance: p.confirmedClosing, label: p.label, period: p };
    });

    return {
      periods: periods, opening: opening, ending: bal, min: min, unit: unit, threshold: threshold,
      confirmedEnding: confirmedBal, minConfirmed: minConfirmed
    };
  }

  function formatWeekLabel(start, end) {
    var s = toDate(start), e = toDate(end);
    return (s.getMonth() + 1) + '/' + s.getDate() + '〜' + (e.getMonth() + 1) + '/' + e.getDate();
  }

  // 毎月 dayOfMonth（31=月末）に発生する定期入出金の、範囲内の発生日一覧
  function recurringOccurrences(r, from, to) {
    var out = [];
    if (!r || !from || !to) return out;
    var start = r.startDate && r.startDate > from ? r.startDate : from;
    var stop = r.endDate && r.endDate < to ? r.endDate : to;
    if (start > stop) return out;
    var d = toDate(start);
    var y = d.getFullYear(), mo = d.getMonth() + 1;
    for (var guard = 0; guard < 120; guard++) {
      var last = endOfMonth(y, mo);
      var day = Math.min(Number(r.dayOfMonth) || last, last);
      var date = safeYmd(y, mo, day);
      if (date > stop) break;
      if (date >= start) out.push(date);
      mo++;
      if (mo > 12) { mo = 1; y++; }
    }
    return out;
  }

  // ---------------------------------------------------------------- 督促

  // 期日超過の債権を取引先ごとにまとめ、督促メールの文面を作る
  function buildReminders(entries, today, companyName) {
    var t = today || ymd(new Date());
    var groups = Object.create(null);
    (entries || []).forEach(function (e) {
      if (e.kind !== 'AR' || e.status === 'settled') return;
      if (!e.dueDate || e.dueDate >= t) return;
      var key = e.partyName || '(取引先未設定)';
      if (!groups[key]) groups[key] = { partyName: key, items: [], total: 0, maxOverdue: 0 };
      groups[key].items.push(e);
      groups[key].total += Number(e.amount) || 0;
      groups[key].maxOverdue = Math.max(groups[key].maxOverdue, daysBetween(e.dueDate, t) || 0);
    });
    return Object.keys(groups).map(function (k) {
      var g = groups[k];
      g.items.sort(function (a, b) { return a.dueDate < b.dueDate ? -1 : 1; });
      g.body = reminderBody(g, companyName);
      return g;
    }).sort(function (a, b) { return b.maxOverdue - a.maxOverdue; });
  }

  function reminderBody(group, companyName) {
    var lines = [];
    lines.push(group.partyName + ' 御中');
    lines.push('');
    lines.push('平素より格別のお引き立てを賜り厚く御礼申し上げます。');
    lines.push('標記の件、下記のご請求分につきましてお支払期日を過ぎておりますので、ご確認をお願い申し上げます。');
    lines.push('');
    group.items.forEach(function (e) {
      lines.push('・' + (e.docNo ? '請求番号 ' + e.docNo + '／' : '') +
        '請求日 ' + (e.issueDate || '—') +
        '／お支払期日 ' + (e.dueDate || '—') +
        '／金額 ' + yen(e.amount));
    });
    lines.push('');
    lines.push('合計 ' + yen(group.total));
    lines.push('');
    lines.push('なお、行き違いにてご入金済みの場合は何卒ご容赦くださいますようお願い申し上げます。');
    lines.push('');
    lines.push(companyName || '鳴鳳堂');
    return lines.join('\n');
  }

  // ---------------------------------------------------------------- 本部への資金不足報告

  /**
   * 資金繰り予測から、本部へ出せる資金不足報告書を作る。
   * 見込み（estimate）を含めた数字は参考として示しつつ、依頼する資金移動額は
   * 見込みを除いた保守的な残高（confirmedClosing）を基準にする。
   * 確定分だけでも資金ショートするなら、それは見積り待ちにはできない実額の不足だから。
   */
  function buildShortageReport(projection, options) {
    var o = options || {};
    var companyName = o.companyName || '鳴鳳堂';
    var recipient = o.recipient || '本部';
    var threshold = projection.threshold || 0;

    var flagged = projection.periods.filter(function (p) { return p.confirmedAlert; });
    var worst = projection.minConfirmed;
    var requestAmount = worst && worst.balance < threshold ? Math.ceil((threshold - worst.balance) / 1000) * 1000 : 0;

    var lines = [];
    lines.push(recipient + ' 御中');
    lines.push('');
    lines.push(companyName + 'です。資金繰り予測の結果、下記のとおり資金移動をお願いしたく、ご報告いたします。');
    lines.push('');

    if (!flagged.length) {
      lines.push('確定済みの債権債務・固定費の範囲では、予測期間中は警戒水準（' + yen(threshold) + '）を');
      lines.push('下回る見込みはありません。');
    } else {
      lines.push('【資金不足の見込み】');
      lines.push('最も厳しい時期： ' + (worst.label || '—') + '（確定ベースの残高 ' + yen(worst.balance) + '）');
      if (requestAmount > 0) {
        lines.push('ご依頼したい資金移動額の目安： ' + yen(requestAmount) +
          '（警戒水準 ' + yen(threshold) + ' を確保するために必要な概算）');
      }
      lines.push('');
      lines.push('内訳（確定分のみ・見込みは含みません）');
      flagged.forEach(function (p) {
        lines.push('・' + p.label + '　残高見込み ' + yen(p.confirmedClosing) +
          (p.confirmedShortage ? '（資金ショート）' : '（警戒水準割れ）'));
      });
    }

    var estimateNote = projection.ending !== projection.confirmedEnding;
    if (estimateNote) {
      lines.push('');
      lines.push('【参考】見積り中の案件を含めた場合の予測期間末残高： ' + yen(projection.ending) +
        '（確定分のみでは ' + yen(projection.confirmedEnding) + '）');
    }

    lines.push('');
    lines.push('お手数をおかけしますが、ご確認のほどよろしくお願いいたします。');
    lines.push('');
    lines.push(companyName);

    return {
      hasShortage: flagged.length > 0,
      worst: worst,
      requestAmount: requestAmount,
      flaggedPeriods: flagged,
      body: lines.join('\n')
    };
  }

  // ---------------------------------------------------------------- 入出力

  var ENTRY_HEADERS = ['区分', '確度', '取引先', '取引先カナ', '請求番号', '発生日', '期日', '金額', '状態', '決済日', '摘要'];

  function entriesToRows(entries) {
    var rows = [ENTRY_HEADERS.slice()];
    (entries || []).forEach(function (e) {
      rows.push([
        e.kind === 'AR' ? '売掛' : '買掛',
        e.certainty === 'estimate' ? '見込み' : '確定',
        e.partyName || '', e.partyKana || '', e.docNo || '',
        e.issueDate || '', e.dueDate || '',
        Math.round(Number(e.amount) || 0),
        e.status === 'settled' ? '決済済' : '未決済',
        e.settledDate || '', e.memo || ''
      ]);
    });
    return rows;
  }

  // 取込用。列名は上の ENTRY_HEADERS を想定しつつ、無い列は空で通す。
  function rowsToEntries(rows, idPrefix) {
    if (!rows || !rows.length) return { entries: [], errors: [] };
    var header = rows[0].map(function (h) { return normalizeName(h); });
    var idx = {};
    ENTRY_HEADERS.forEach(function (h, i) {
      var key = normalizeName(h);
      var at = header.indexOf(key);
      idx[i] = at;
    });
    var hasHeader = Object.keys(idx).some(function (k) { return idx[k] >= 0; });
    var body = hasHeader ? rows.slice(1) : rows;
    var entries = [], errors = [];
    body.forEach(function (r, n) {
      function cell(i) {
        var at = hasHeader ? idx[i] : i;
        return at >= 0 ? r[at] : '';
      }
      var kindRaw = String(cell(0) || '').trim();
      var kind = /売|ar|受|入/i.test(kindRaw) ? 'AR' : (/買|ap|支|出/i.test(kindRaw) ? 'AP' : null);
      var amount = parseAmount(cell(7));
      var issueDate = parseDate(cell(5));
      var dueDate = parseDate(cell(6));
      if (!kind || amount == null) {
        errors.push({ line: n + (hasHeader ? 2 : 1), reason: !kind ? '区分が「売掛」「買掛」のどちらか判別できません' : '金額を読み取れません', row: r });
        return;
      }
      var statusRaw = String(cell(8) || '').trim();
      var certaintyRaw = String(cell(1) || '').trim();
      entries.push({
        id: (idPrefix || 'imp') + '-' + (n + 1) + '-' + Math.random().toString(36).slice(2, 7),
        kind: kind,
        certainty: /見込|estimate|見積/i.test(certaintyRaw) ? 'estimate' : 'confirmed',
        partyName: String(cell(2) || '').trim(),
        partyKana: String(cell(3) || '').trim(),
        docNo: String(cell(4) || '').trim(),
        issueDate: issueDate,
        dueDate: dueDate,
        amount: Math.abs(amount),
        status: /決済済|済|settled|paid/i.test(statusRaw) ? 'settled' : 'open',
        settledDate: parseDate(cell(9)),
        memo: String(cell(10) || '').trim(),
        source: 'csv'
      });
    });
    return { entries: entries, errors: errors };
  }

  return {
    // 文字列
    toHalfWidth: toHalfWidth, kanaToZenkaku: kanaToZenkaku, toHiragana: toHiragana,
    normalizeName: normalizeName, nameSimilarity: nameSimilarity,
    // 数値
    parseAmount: parseAmount, yen: yen, withTax: withTax,
    // 日付
    ymd: ymd, toDate: toDate, isValidYmd: isValidYmd, parseDate: parseDate, addDays: addDays,
    addMonthsClamped: addMonthsClamped, endOfMonth: endOfMonth, daysBetween: daysBetween,
    startOfWeek: startOfWeek, calcDueDate: calcDueDate, shiftBusinessDay: shiftBusinessDay,
    // CSV
    parseCSV: parseCSV, toCSV: toCSV, detectDelimiter: detectDelimiter,
    guessColumns: guessColumns, inferColumns: inferColumns, parseBankCSV: parseBankCSV, HEADER_ALIASES: HEADER_ALIASES,
    // 消込
    MATCH_DEFAULTS: MATCH_DEFAULTS, scoreMatch: scoreMatch, suggestMatches: suggestMatches, autoMatch: autoMatch,
    // 集計
    summarize: summarize, byParty: byParty, agingBuckets: agingBuckets,
    projectCashflow: projectCashflow, recurringOccurrences: recurringOccurrences,
    // 督促・本部報告・入出力
    buildReminders: buildReminders, reminderBody: reminderBody, buildShortageReport: buildShortageReport,
    ENTRY_HEADERS: ENTRY_HEADERS, entriesToRows: entriesToRows, rowsToEntries: rowsToEntries
  };
});
