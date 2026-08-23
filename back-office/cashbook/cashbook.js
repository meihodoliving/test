/*!
 * 資金表 → 現金出納帳 変換ロジック（DOM 非依存・副作用なし）
 *
 * 前提となる業務ルール（申し送りより）:
 *  - 色分け（青=銀行振込／黒・赤=現金）は一次判定の目安にすぎない。必ず通帳で裏取りする
 *  - 口座振替（自動引落）は資金表に記載があっても現金出納帳からは除外する
 *  - ATM引き出しは使途に応じて複数の取引に分割することがある
 *  - 検算式：現金純増減 ＝ 資金表残高の増減 − 銀行通帳上の動き
 *  - 修正・再分類は「確認 → 確定」を経てから正式なものとして扱う
 *
 * したがってこのモジュールは「判定」までを行い、「確定」は人の操作に委ねる。
 */
(function (root, factory) {
  var api = factory(typeof require === 'function' ? require('../core.js') : root.BOCore);
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.BOCashbook = api;
})(typeof self !== 'undefined' ? self : this, function (C) {
  'use strict';

  // ------------------------------------------------------------ 列の推定

  var HEADERS = {
    date:        ['日付', '取引日', '年月日', '月日', 'date'],
    description: ['摘要', '内容', '取引内容', '相手先', '支払先', '品名', '備考', 'description'],
    inflow:      ['入金', '入金額', '収入', 'receipts', '入'],
    outflow:     ['出金', '出金額', '支出', '支払', 'payments', '出'],
    balance:     ['残高', '差引残高', '合計残高', 'balance'],
    account:     ['科目', '勘定科目', '経費科目', '費目', 'account'],
    amount:      ['金額', '取引金額', 'amount'],
    // 会計ソフトへの入力が済んでいるかの印。銀行分は API 連携で自動記帳されるため、
    // この列が意味を持つのは主に手入力が要る現金分。「済み」の行は当月の作業対象から外す。
    processed:   ['会計処理', '処理状況', '入力状況']
  };

  function guessColumns(headerRow) {
    var map = { date: -1, description: -1, inflow: -1, outflow: -1, balance: -1, account: -1, amount: -1, processed: -1 };
    (headerRow || []).forEach(function (raw, i) {
      var h = C.normalizeName(cellText(raw));
      if (!h) return;
      Object.keys(HEADERS).forEach(function (key) {
        if (map[key] >= 0) return;
        var hit = HEADERS[key].some(function (alias) {
          var a = C.normalizeName(alias);
          return a && (h === a || h.indexOf(a) >= 0);
        });
        if (hit) map[key] = i;
      });
    });
    return map;
  }

  // セルは xlsx リーダーの {v,...} か、CSV の素の文字列のどちらでも受ける
  function cellText(cell) {
    if (cell == null) return '';
    if (typeof cell === 'object') return cell.v == null ? '' : String(cell.v);
    return String(cell);
  }

  function cellTone(cell) {
    return (cell && typeof cell === 'object' && cell.tone) ? cell.tone : null;
  }

  // 行の色は、摘要セルの色を基本とし、無ければ行内で最初に色の付いたセルを採用する
  function rowTone(row, descIndex) {
    var primary = cellTone(row[descIndex]);
    if (primary && primary !== 'black') return primary;
    for (var i = 0; i < row.length; i++) {
      var t = cellTone(row[i]);
      if (t && t !== 'black' && t !== 'other') return t;
    }
    return primary || 'black';
  }

  // ------------------------------------------------------------ 取り込み

  var seq = 0;
  function uid(p) { seq++; return (p || 'r') + '-' + seq.toString(36); }

  function looksLikeHeader(row, cols) {
    if (cols && cols.date >= 0) {
      return !C.parseDate(cellText(row[cols.date]));
    }
    return !row.some(function (c) { return C.parseDate(cellText(c)); });
  }

  // 見出し名で摘要列が見つからないとき、他の列（日付・入金・出金・残高・科目など）
  // として既に使われていない列のうち、文字量が最も多いものを摘要とみなす。
  function inferDescriptionColumn(body, cols) {
    var claimed = {};
    Object.keys(cols).forEach(function (k) { if (cols[k] >= 0) claimed[cols[k]] = true; });
    var sample = (body || []).slice(0, 30);
    if (!sample.length) return -1;
    var width = sample.reduce(function (w, r) { return Math.max(w, r ? r.length : 0); }, 0);
    var best = { index: -1, textLen: 0 };
    for (var i = 0; i < width; i++) {
      if (claimed[i]) continue;
      var textLen = 0, numericHits = 0, filled = 0;
      sample.forEach(function (r) {
        var t = cellText(r && r[i]).trim();
        if (!t) return;
        filled++;
        if (C.parseAmount(t) != null || C.parseDate(t)) numericHits++;
        else textLen += t.length;
      });
      // 数値・日付ばかりの列は摘要ではない
      if (filled && numericHits / filled > 0.5) continue;
      if (textLen > best.textLen) best = { index: i, textLen: textLen };
    }
    return best.textLen > 0 ? best.index : -1;
  }

  /**
   * 資金表のシート → 取引の配列。
   * 金額が入金/出金の2列でも、符号付きの1列でも読める。
   */
  function readFundTable(rows, options) {
    var opt = options || {};
    if (!rows || !rows.length) return { columns: {}, entries: [], skipped: 0, header: null };

    var headerRow = null, body = rows;
    var cols = opt.columns;
    if (!cols) {
      // 先頭10行のうち、最も多くの列名が当たる行を見出しとみなす
      var best = { score: -1, index: -1, map: null };
      rows.slice(0, 10).forEach(function (r, i) {
        var m = guessColumns(r);
        var score = Object.keys(m).filter(function (k) { return m[k] >= 0; }).length;
        if (score > best.score) best = { score: score, index: i, map: m };
      });
      if (best.score >= 2) {
        headerRow = rows[best.index];
        cols = best.map;
        body = rows.slice(best.index + 1);
      } else {
        cols = guessColumns([]);
      }
      // 摘要の見出しが空欄の資金表がある（「勘定科目」の隣に無題の列で入力されている等）。
      // 見出し名で見つからなければ、中身の文字量から推測する。
      if (cols.description < 0) {
        var inferred = inferDescriptionColumn(body, cols);
        if (inferred >= 0) cols.description = inferred;
      }
    } else if (rows.length && looksLikeHeader(rows[0], cols)) {
      headerRow = rows[0];
      body = rows.slice(1);
    }

    var entries = [], skipped = 0, skippedRows = [];
    body.forEach(function (row, n) {
      if (!row || !row.length) return;
      var date = cols.date >= 0 ? C.parseDate(cellText(row[cols.date]), opt.yearHint) : null;
      var inflow = cols.inflow >= 0 ? C.parseAmount(cellText(row[cols.inflow])) : null;
      var outflow = cols.outflow >= 0 ? C.parseAmount(cellText(row[cols.outflow])) : null;
      if (inflow == null && outflow == null && cols.amount >= 0) {
        var a = C.parseAmount(cellText(row[cols.amount]));
        if (a != null) { if (a >= 0) inflow = a; else outflow = Math.abs(a); }
      }
      // 金額の無い行は集計に入れられないが、黙って捨てず理由を残す
      if (!date || (!inflow && !outflow)) {
        skipped++;
        var label = cols.description >= 0 ? cellText(row[cols.description]).trim() : '';
        if (label || date) {
          skippedRows.push({
            line: n + 1,
            date: date,
            description: label,
            reason: !date ? '日付を読み取れません' : '入金・出金がどちらも空、または0です'
          });
        }
        return;
      }

      var processedRaw = cols.processed >= 0 ? cellText(row[cols.processed]).trim() : '';
      entries.push({
        id: uid('f'),
        line: n + 1,
        date: date,
        description: cols.description >= 0 ? cellText(row[cols.description]).trim() : '',
        inflow: Math.abs(inflow || 0),
        outflow: Math.abs(outflow || 0),
        balance: cols.balance >= 0 ? C.parseAmount(cellText(row[cols.balance])) : null,
        account: cols.account >= 0 ? cellText(row[cols.account]).trim() : '',
        tone: cols.description >= 0 ? rowTone(row, cols.description) : rowTone(row, 0),
        color: (row[cols.description] && row[cols.description].color) || null,
        alreadyProcessed: /済/.test(processedRaw),
        decision: null,        // 'cash' | 'bank' | 'exclude'
        reason: '',
        confirmed: false,      // 人が確定したか
        splitOf: null,
        bankMatchId: null
      });
    });

    return { columns: cols, header: headerRow, entries: entries, skipped: skipped, skippedRows: skippedRows };
  }

  // ------------------------------------------------------------ ルール

  /**
   * 確定した判断をルールとして保存し、翌月以降は自動で当てる。
   * rule = { id, kind: 'cash'|'bank'|'exclude', keyword, note }
   */
  function matchRule(entry, rules) {
    var hay = C.normalizeName(entry.description + ' ' + (entry.account || ''));
    if (!hay) return null;
    var hit = null;
    (rules || []).forEach(function (r) {
      if (!r.keyword) return;
      var k = C.normalizeName(r.keyword);
      if (!k || hay.indexOf(k) < 0) return;
      // より長いキーワードを優先（具体的な指定を勝たせる）
      if (!hit || k.length > C.normalizeName(hit.keyword).length) hit = r;
    });
    return hit;
  }

  // ------------------------------------------------------------ 通帳との突合

  var MATCH_DEFAULTS = { amountTolerance: 0, dateWindow: 5 };

  /**
   * 通帳に同じ動きがあれば、その行は銀行取引（＝現金出納帳の対象外）。
   * 金額の一致を必須とし、日付の近さと摘要の類似で候補を絞る。
   */
  function findBankMatch(entry, bankTxs, options) {
    var o = Object.assign({}, MATCH_DEFAULTS, options || {});
    var amount = entry.inflow ? entry.inflow : -entry.outflow;
    var best = null;
    (bankTxs || []).forEach(function (tx, i) {
      if (tx.used) return;
      if ((amount > 0) !== (tx.amount > 0)) return;
      var diff = Math.abs(Math.abs(tx.amount) - Math.abs(amount));
      if (diff > o.amountTolerance) return;
      var gap = C.daysBetween(entry.date, tx.date);
      if (gap == null || Math.abs(gap) > o.dateWindow) return;
      var sim = C.nameSimilarity(entry.description, tx.description);
      var score = 60 - Math.abs(gap) * 4 + sim * 40 - (diff > 0 ? 10 : 0);
      if (!best || score > best.score) best = { index: i, tx: tx, score: score, gap: gap, sim: sim };
    });
    return best;
  }

  /**
   * 一次判定。優先順位は「人の確定 > 資金表の会計処理済み > ルール > 通帳一致 > 色」。
   * 色だけで決まったものは confident:false を返し、必ず確認に回す。
   */
  function classify(entry, context) {
    var ctx = context || {};
    if (entry.confirmed && entry.decision) {
      return { decision: entry.decision, reason: entry.reason || '確定済み', confident: true, source: 'confirmed' };
    }

    // 資金表の「会計処理」列に済みの印がある行は、すでに会計ソフトへの入力が
    // 終わっている（銀行分は API 連携で自動記帳されるため、この印は主に現金分の
    // 手入力完了を示す）。今月の作業対象からは外す。
    if (entry.alreadyProcessed) {
      return { decision: 'exclude', reason: '資金表の「会計処理」列で済みと記録済み', confident: true, source: 'processed' };
    }

    var rule = matchRule(entry, ctx.rules);
    if (rule) {
      return {
        decision: rule.kind,
        reason: '登録ルール「' + rule.keyword + '」に一致' + (rule.note ? '（' + rule.note + '）' : ''),
        confident: true, source: 'rule', ruleId: rule.id
      };
    }

    var bank = ctx.bankMatch;
    if (bank) {
      return {
        decision: 'bank',
        reason: '通帳に同じ動きあり（' + bank.tx.date + '／' + C.yen(bank.tx.amount) + '）',
        confident: true, source: 'bank'
      };
    }

    if (entry.tone === 'blue') {
      return { decision: 'bank', reason: '青字（銀行振込の目安）。通帳で未確認', confident: false, source: 'color' };
    }
    if (entry.tone === 'red' || entry.tone === 'black') {
      return {
        decision: 'cash',
        reason: (entry.tone === 'red' ? '赤字' : '黒字') + '（現金の目安）。通帳で未確認',
        confident: false, source: 'color'
      };
    }
    return { decision: null, reason: '色から判定できません', confident: false, source: 'none' };
  }

  /**
   * 全件に判定を付ける。通帳の明細は一度当たったら他の行には使わない。
   */
  function classifyAll(entries, bankTxs, rules, options) {
    var pool = (bankTxs || []).map(function (t) {
      return { date: t.date, description: t.description, amount: t.amount, used: false };
    });
    return (entries || []).map(function (e) {
      var bank = e.confirmed ? null : findBankMatch(e, pool, options);
      if (bank) pool[bank.index].used = true;
      var v = classify(e, { rules: rules, bankMatch: bank });
      return Object.assign({}, e, {
        decision: v.decision,
        reason: v.reason,
        confident: v.confident,
        source: v.source,
        ruleId: v.ruleId || null,
        bankMatch: bank ? { date: bank.tx.date, description: bank.tx.description, amount: bank.tx.amount } : null
      });
    });
  }

  // ------------------------------------------------------------ 分割

  /**
   * 1件を複数に分ける（ATM引き出し、経費科目の内訳など）。
   * 合計が元の金額と一致しない分割は受け付けない。
   */
  function splitEntry(entry, parts) {
    var isIn = entry.inflow > 0;
    var total = isIn ? entry.inflow : entry.outflow;
    var sum = (parts || []).reduce(function (a, p) { return a + Math.abs(Number(p.amount) || 0); }, 0);
    if (!parts || parts.length < 2) {
      return { ok: false, error: '分割するには2件以上が必要です', entries: null };
    }
    if (sum !== total) {
      return {
        ok: false,
        error: '内訳の合計 ' + C.yen(sum) + ' が元の金額 ' + C.yen(total) + ' と一致しません（差 ' + C.yen(total - sum) + '）',
        entries: null
      };
    }
    var made = parts.map(function (p, i) {
      return Object.assign({}, entry, {
        id: uid('s'),
        splitOf: entry.id,
        description: p.description || (entry.description + '（内訳' + (i + 1) + '）'),
        account: p.account || entry.account,
        inflow: isIn ? Math.abs(Number(p.amount) || 0) : 0,
        outflow: isIn ? 0 : Math.abs(Number(p.amount) || 0),
        decision: p.decision || entry.decision,
        reason: p.reason || '分割して再分類',
        confirmed: false,
        balance: null
      });
    });
    return { ok: true, error: null, entries: made };
  }

  // ------------------------------------------------------------ 検算

  /**
   * 申し送りの検算式をそのまま実装する。
   *   現金純増減 ＝ 資金表残高の増減 − 銀行通帳上の動き
   * これと「現金と判定した取引の合計」が一致すれば、仕分けに漏れがない。
   */
  function reconcile(input) {
    var o = input || {};
    var entries = o.entries || [];
    var bankTxs = o.bankTxs || [];

    // 分割元は集計から外す（分割後の子で数える）
    var splitParents = Object.create(null);
    entries.forEach(function (e) { if (e.splitOf) splitParents[e.splitOf] = true; });
    var live = entries.filter(function (e) { return !splitParents[e.id]; });

    var fundIn = 0, fundOut = 0;
    live.forEach(function (e) { fundIn += e.inflow || 0; fundOut += e.outflow || 0; });
    var fundNet = fundIn - fundOut;

    var bankNet = bankTxs.reduce(function (a, t) { return a + (Number(t.amount) || 0); }, 0);
    var expectedCashNet = fundNet - bankNet;

    var cashIn = 0, cashOut = 0, pending = 0, unresolved = 0;
    live.forEach(function (e) {
      if (e.decision === 'cash') {
        cashIn += e.inflow || 0;
        cashOut += e.outflow || 0;
        if (!e.confirmed) pending++;
      } else if (!e.decision) {
        unresolved++;
      } else if (!e.confirmed) {
        pending++;
      }
    });
    var cashNet = cashIn - cashOut;
    var gap = expectedCashNet - cashNet;

    return {
      fundIn: fundIn, fundOut: fundOut, fundNet: fundNet,
      bankNet: bankNet,
      expectedCashNet: expectedCashNet,
      cashIn: cashIn, cashOut: cashOut, cashNet: cashNet,
      gap: gap,
      balanced: gap === 0,
      pending: pending,
      unresolved: unresolved,
      target: o.targetNet == null ? null : Number(o.targetNet),
      targetGap: o.targetNet == null ? null : Number(o.targetNet) - expectedCashNet
    };
  }

  // ------------------------------------------------------------ 出納帳

  /**
   * 現金と確定した取引だけを日付順に並べ、期首残高から残高を積み上げる。
   * options.includeUnconfirmed が真なら未確定も含める（下書き確認用）。
   */
  function buildCashbook(entries, openingBalance, options) {
    var o = options || {};
    var splitParents = Object.create(null);
    (entries || []).forEach(function (e) { if (e.splitOf) splitParents[e.splitOf] = true; });

    var rows = (entries || []).filter(function (e) {
      if (splitParents[e.id]) return false;
      if (e.decision !== 'cash') return false;
      return o.includeUnconfirmed ? true : !!e.confirmed;
    }).sort(function (a, b) {
      if (a.date !== b.date) return a.date < b.date ? -1 : 1;
      return (a.line || 0) - (b.line || 0);
    });

    var bal = Number(openingBalance) || 0;
    var out = rows.map(function (e) {
      bal += (e.inflow || 0) - (e.outflow || 0);
      return {
        id: e.id, date: e.date, description: e.description, account: e.account,
        inflow: e.inflow || 0, outflow: e.outflow || 0, balance: bal,
        confirmed: !!e.confirmed, reason: e.reason
      };
    });

    return {
      rows: out,
      opening: Number(openingBalance) || 0,
      closing: bal,
      totalIn: out.reduce(function (a, r) { return a + r.inflow; }, 0),
      totalOut: out.reduce(function (a, r) { return a + r.outflow; }, 0)
    };
  }

  var CASHBOOK_HEADERS = ['日付', '摘要', '科目', '入金', '出金', '残高'];

  function cashbookToRows(book) {
    var rows = [CASHBOOK_HEADERS.slice()];
    rows.push(['', '前月繰越', '', '', '', Math.round(book.opening)]);
    book.rows.forEach(function (r) {
      rows.push([
        r.date, r.description, r.account || '',
        r.inflow || '', r.outflow || '', Math.round(r.balance)
      ]);
    });
    rows.push(['', '合計', '', Math.round(book.totalIn), Math.round(book.totalOut), Math.round(book.closing)]);
    return rows;
  }

  return {
    HEADERS: HEADERS,
    guessColumns: guessColumns,
    cellText: cellText,
    rowTone: rowTone,
    readFundTable: readFundTable,
    matchRule: matchRule,
    findBankMatch: findBankMatch,
    classify: classify,
    classifyAll: classifyAll,
    splitEntry: splitEntry,
    reconcile: reconcile,
    buildCashbook: buildCashbook,
    cashbookToRows: cashbookToRows,
    CASHBOOK_HEADERS: CASHBOOK_HEADERS,
    MATCH_DEFAULTS: MATCH_DEFAULTS
  };
});
