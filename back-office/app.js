/*!
 * 鳴鳳堂 バックオフィス — 画面制御
 * 計算は core.js に集約。ここは DOM と localStorage の担当。
 */
(function () {
  'use strict';

  var C = window.BOCore;
  var STORAGE_KEY = 'meihodo.backoffice.v1';

  // ------------------------------------------------------------ 小道具

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  var seq = 0;
  function uid(prefix) {
    seq++;
    return (prefix || 'id') + '-' + Date.now().toString(36) + '-' + seq.toString(36);
  }

  function today() { return C.ymd(new Date()); }

  function download(filename, text, mime) {
    // Excel が UTF-8 と解釈できるよう CSV には BOM を付ける
    var body = (mime || '').indexOf('csv') >= 0 ? '﻿' + text : text;
    var blob = new Blob([body], { type: (mime || 'text/plain') + ';charset=utf-8' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  // 文字コードを判定しながらテキストファイルを読む（銀行 CSV は Shift_JIS が多い）
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
        var text = String(fr.result || '');
        if (text.indexOf('�') >= 0) read('shift_jis');   // 化けていれば読み直す
        else resolve(text);
      };
      fr.readAsText(file, 'utf-8');
    });
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    var ta = document.createElement('textarea');
    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); } catch (e) { /* 失敗しても致命的ではない */ }
    document.body.removeChild(ta);
    return Promise.resolve();
  }

  // ------------------------------------------------------------ 状態

  function defaultState() {
    return {
      version: 1,
      settings: {
        companyName: '鳴鳳堂',
        openingBalance: 0,
        balanceAsOf: today(),
        alertThreshold: 1000000,
        taxRate: 10,
        amountTolerance: 0,
        autoThreshold: C.MATCH_DEFAULTS.autoThreshold,
        cashflowUnit: 'week'
      },
      parties: [],
      entries: [],
      recurring: [],
      bankTx: []
    };
  }

  var state = defaultState();
  var ui = {
    selected: Object.create(null),
    filters: { kind: '', status: 'open', text: '' },
    dueTouched: false,     // 期日を手入力で上書きしたか
    parsedBank: null,      // 読み込んだ明細
    bankColumns: null,
    match: null            // 照合結果
  };

  function load() {
    var raw;
    try { raw = localStorage.getItem(STORAGE_KEY); } catch (e) {
      flash('このブラウザではデータを保存できません（プライベートモードの可能性があります）。', true);
      return;
    }
    if (!raw) return;
    try {
      var parsed = JSON.parse(raw);
      state = Object.assign(defaultState(), parsed);
      state.settings = Object.assign(defaultState().settings, parsed.settings || {});
    } catch (e) {
      flash('保存データを読み込めませんでした。バックアップから復元してください。', true);
    }
  }

  var saveTimer = null;
  function save() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(function () {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        setSaveState('保存済み ' + new Date().toLocaleTimeString('ja-JP'), true);
      } catch (e) {
        setSaveState('保存できません', false);
        flash('保存に失敗しました。容量が上限に達している可能性があります。バックアップを書き出してください。', true);
      }
    }, 200);
  }

  function setSaveState(text, ok) {
    var el = $('#save-state');
    if (!el) return;
    el.textContent = text;
    el.classList.toggle('is-saved', !!ok);
  }

  function flash(msg, isError) {
    var el = $('#data-msg');
    if (el) el.textContent = msg;
    if (isError) console.warn(msg);
  }

  function commit() { save(); render(); }

  // ------------------------------------------------------------ タブ

  function initTabs() {
    $('#tabs').addEventListener('click', function (ev) {
      var btn = ev.target.closest('.tab');
      if (!btn) return;
      $$('.tab').forEach(function (t) { t.classList.toggle('is-active', t === btn); });
      $$('.panel').forEach(function (p) {
        p.classList.toggle('is-active', p.id === 'panel-' + btn.dataset.tab);
      });
    });
  }

  // ------------------------------------------------------------ 描画

  function render() {
    renderDashboard();
    renderEntries();
    renderCashflow();
    renderReminders();
    renderSettings();
    renderParties();
    renderRecurring();
    renderBankHistory();
    renderPartyDatalist();
  }

  // ------------------------------------------- ダッシュボード

  function renderDashboard() {
    var t = today();
    var s = C.summarize(state.entries, t);
    var proj = projection('week', 13);
    var projected = proj.periods.length ? proj.periods[3] : null;

    var kpis = [
      {
        label: '現預金残高（' + (state.settings.balanceAsOf || '—') + '時点）',
        value: C.yen(state.settings.openingBalance),
        note: proj.min.label ? '最低見込 ' + C.yen(proj.min.balance) + '（' + proj.min.label + '）' : '',
        alert: proj.min.balance < 0
      },
      {
        label: '売掛残高（未回収）',
        value: C.yen(s.arOpen),
        note: s.arCount + '件／7日以内の入金予定 ' + C.yen(s.arDue7)
      },
      {
        label: '買掛残高（未払）',
        value: C.yen(s.apOpen),
        note: s.apCount + '件／7日以内の支払予定 ' + C.yen(s.apDue7)
      },
      {
        label: '入金遅れ',
        value: C.yen(s.arOverdue),
        note: s.arOverdueCount + '件が期日超過',
        alert: s.arOverdueCount > 0
      }
    ];

    $('#kpi-grid').innerHTML = kpis.map(function (k) {
      return '<div class="kpi ' + (k.alert ? 'kpi--alert' : '') + '">' +
        '<div class="kpi__label">' + esc(k.label) + '</div>' +
        '<div class="kpi__value">' + esc(k.value) + '</div>' +
        '<div class="kpi__note">' + esc(k.note || '') + '</div></div>';
    }).join('');

    // 今週やること：期日超過の回収 → 直近の支払 の順
    var in7 = C.addDays(t, 7);
    var todos = [];
    state.entries.forEach(function (e) {
      if (e.status === 'settled' || !e.dueDate) return;
      if (e.kind === 'AR' && e.dueDate < t) {
        todos.push({ sort: 0, when: (C.daysBetween(e.dueDate, t) || 0) + '日超過', text: '【入金確認】' + (e.partyName || '—') + ' ' + C.yen(e.amount) + '（期日 ' + e.dueDate + '）' });
      } else if (e.kind === 'AP' && e.dueDate <= in7) {
        var d = C.daysBetween(t, e.dueDate);
        todos.push({ sort: d < 0 ? 1 : 2, when: d < 0 ? Math.abs(d) + '日遅延' : (d === 0 ? '本日' : 'あと' + d + '日'), text: '【支払】' + (e.partyName || '—') + ' ' + C.yen(e.amount) + '（期日 ' + e.dueDate + '）' });
      } else if (e.kind === 'AR' && e.dueDate <= in7) {
        var d2 = C.daysBetween(t, e.dueDate);
        todos.push({ sort: 3, when: d2 === 0 ? '本日' : 'あと' + d2 + '日', text: '【入金予定】' + (e.partyName || '—') + ' ' + C.yen(e.amount) });
      }
    });
    todos.sort(function (a, b) { return a.sort - b.sort; });
    $('#todo-list').innerHTML = todos.length
      ? todos.slice(0, 20).map(function (x) {
          return '<div class="todo"><span class="todo__when">' + esc(x.when) + '</span><span>' + esc(x.text) + '</span></div>';
        }).join('')
      : '<p class="empty">期日超過も直近の支払もありません。</p>';

    // 次の4週の資金繰り
    $('#mini-cashflow').innerHTML = tableHtml(
      ['週', '入金', '出金', '期末残高'],
      proj.periods.slice(0, 4).map(function (p) {
        return {
          cls: p.shortage ? 'cf-short' : (p.alert ? 'cf-warn' : ''),
          cells: [esc(p.label), { num: C.yen(p.inflow) }, { num: C.yen(p.outflow) }, { num: C.yen(p.closing) }]
        };
      }),
      '取引を登録すると予測が表示されます。'
    );

    var aging = C.agingBuckets(state.entries, 'AR', t);
    $('#aging-ar').innerHTML = tableHtml(
      ['滞留期間', '件数', '金額'],
      aging.map(function (b) {
        return {
          cls: b.total > 0 && b.label === '91日以上' ? 'cf-short' : '',
          cells: [esc(b.label), { num: b.count + '件' }, { num: C.yen(b.total) }]
        };
      }),
      'データがありません。'
    );

    var parties = C.byParty(state.entries, 'AR').slice(0, 10);
    $('#party-ar').innerHTML = tableHtml(
      ['取引先', '件数', '残高', '最古の期日'],
      parties.map(function (p) {
        return { cells: [esc(p.party), { num: p.count + '件' }, { num: C.yen(p.total) }, esc(p.oldestDue || '—')] };
      }),
      '売掛の登録がありません。'
    );
  }

  // 表を組み立てる小さなヘルパー。cells は文字列 or {num:...} 。
  function tableHtml(headers, rows, emptyMsg) {
    if (!rows.length) return '<p class="empty">' + esc(emptyMsg || 'データがありません。') + '</p>';
    var head = '<tr>' + headers.map(function (h, i) {
      return '<th' + (i > 0 ? ' class="num"' : '') + '>' + esc(h) + '</th>';
    }).join('') + '</tr>';
    var body = rows.map(function (r) {
      return '<tr class="' + (r.cls || '') + '">' + r.cells.map(function (c) {
        return typeof c === 'object' && c !== null && 'num' in c
          ? '<td class="num">' + esc(c.num) + '</td>'
          : '<td>' + c + '</td>';
      }).join('') + '</tr>';
    }).join('');
    return '<div class="table-wrap"><table><thead>' + head + '</thead><tbody>' + body + '</tbody></table></div>';
  }

  // ------------------------------------------- 債権・債務

  function filteredEntries() {
    var t = today();
    var f = ui.filters;
    var q = C.normalizeName(f.text);
    return state.entries.filter(function (e) {
      if (f.kind && e.kind !== f.kind) return false;
      if (f.status === 'open' && e.status === 'settled') return false;
      if (f.status === 'settled' && e.status !== 'settled') return false;
      if (f.status === 'overdue' && !(e.status !== 'settled' && e.dueDate && e.dueDate < t)) return false;
      if (q) {
        var hay = C.normalizeName([e.partyName, e.partyKana, e.docNo, e.memo].join(' '));
        if (hay.indexOf(q) < 0) return false;
      }
      return true;
    }).sort(function (a, b) {
      var x = a.dueDate || '9999-12-31', y = b.dueDate || '9999-12-31';
      return x < y ? -1 : (x > y ? 1 : 0);
    });
  }

  function renderEntries() {
    var t = today();
    var in7 = C.addDays(t, 7);
    var list = filteredEntries();

    var rows = list.map(function (e) {
      var overdue = e.status !== 'settled' && e.dueDate && e.dueDate < t;
      var soon = e.status !== 'settled' && e.dueDate && e.dueDate >= t && e.dueDate <= in7;
      var cls = e.status === 'settled' ? 'is-settled' : (overdue ? 'is-overdue' : (soon ? 'is-soon' : ''));
      return '<tr class="' + cls + '">' +
        '<td><input type="checkbox" class="sel" data-id="' + esc(e.id) + '"' + (ui.selected[e.id] ? ' checked' : '') + '></td>' +
        '<td>' + esc(e.dueDate || '—') + (overdue ? ' <span class="hint">(' + (C.daysBetween(e.dueDate, t) || 0) + '日超過)</span>' : '') + '</td>' +
        '<td><span class="tag tag--' + (e.kind === 'AR' ? 'ar">売掛' : 'ap">買掛') + '</span></td>' +
        '<td>' + esc(e.partyName || '—') + (e.partyKana ? '<br><span class="hint">' + esc(e.partyKana) + '</span>' : '') + '</td>' +
        '<td>' + esc(e.docNo || '') + '</td>' +
        '<td class="num ' + (e.kind === 'AR' ? 'amount-in' : 'amount-out') + '">' + esc(C.yen(e.amount)) + '</td>' +
        '<td>' + (e.status === 'settled'
          ? '<span class="tag tag--done">決済済 ' + esc(e.settledDate || '') + '</span>'
          : '未決済') + '</td>' +
        '<td>' + esc(e.memo || '') + '</td>' +
        '<td class="num">' +
          (e.status === 'settled'
            ? '<button class="btn btn--sm" data-act="reopen" data-id="' + esc(e.id) + '">戻す</button>'
            : '<button class="btn btn--sm" data-act="settle" data-id="' + esc(e.id) + '">消込</button>') +
          ' <button class="btn btn--sm" data-act="edit" data-id="' + esc(e.id) + '">編集</button>' +
        '</td></tr>';
    }).join('');

    $('#entry-table').innerHTML = list.length
      ? '<table><thead><tr><th></th><th>期日</th><th>区分</th><th>取引先</th><th>請求番号</th>' +
        '<th class="num">金額</th><th>状態</th><th>摘要</th><th class="num">操作</th></tr></thead><tbody>' + rows + '</tbody></table>'
      : '<p class="empty">該当する取引がありません。</p>';

    var n = Object.keys(ui.selected).filter(function (k) { return ui.selected[k]; }).length;
    $('#sel-count').textContent = n + '件選択中';
  }

  function renderPartyDatalist() {
    $('#party-list').innerHTML = state.parties.map(function (p) {
      return '<option value="' + esc(p.name) + '">' + esc(p.kana || '') + '</option>';
    }).join('');
  }

  function findParty(name) {
    var key = C.normalizeName(name);
    if (!key) return null;
    for (var i = 0; i < state.parties.length; i++) {
      if (C.normalizeName(state.parties[i].name) === key) return state.parties[i];
    }
    return null;
  }

  // 取引先と発生日が揃ったら、支払サイトから期日を埋める（手入力済みなら触らない）
  function autofillDue(force) {
    var party = findParty($('#f-party').value);
    var issue = $('#f-issue').value;
    var note = $('#due-auto-note');
    if (party && party.kana && !$('#f-kana').value) $('#f-kana').value = party.kana;
    if (!party || !issue) { note.textContent = ''; return; }
    var terms = { closingDay: party.closingDay, monthOffset: party.monthOffset, payDay: party.payDay };
    var due = C.calcDueDate(issue, terms);
    if (!due) { note.textContent = ''; return; }
    if (force || !$('#f-due').value || !ui.dueTouched) $('#f-due').value = due;
    note.textContent = '（' + termsLabel(party) + ' → ' + due + '）';
  }

  function termsLabel(p) {
    var closing = p.closingDay === 31 ? '月末締め' : p.closingDay + '日締め';
    var month = p.monthOffset === 0 ? '当月' : (p.monthOffset === 2 ? '翌々月' : '翌月');
    var day = p.payDay === 31 ? '末日' : p.payDay + '日';
    return closing + month + day + '払い';
  }

  function initEntryForm() {
    $('#f-issue').value = today();

    ['#f-party', '#f-issue'].forEach(function (sel) {
      $(sel).addEventListener('change', function () { autofillDue(false); });
    });
    $('#f-party').addEventListener('blur', function () { autofillDue(false); });
    // 手で期日を触ったら、以後この入力については自動計算で上書きしない
    $('#f-due').addEventListener('input', function () { ui.dueTouched = true; });

    $('#entry-form').addEventListener('submit', function (ev) {
      ev.preventDefault();
      var id = $('#f-id').value;
      var payload = {
        kind: $('#f-kind').value,
        partyName: $('#f-party').value.trim(),
        partyKana: $('#f-kana').value.trim(),
        docNo: $('#f-docno').value.trim(),
        issueDate: $('#f-issue').value,
        dueDate: $('#f-due').value,
        amount: Math.abs(Number($('#f-amount').value) || 0),
        memo: $('#f-memo').value.trim()
      };
      if (!payload.amount) { $('#f-hint').textContent = '金額を入力してください。'; return; }

      if (id) {
        var e = state.entries.find(function (x) { return x.id === id; });
        if (e) Object.assign(e, payload);
        $('#f-hint').textContent = '更新しました。';
      } else {
        state.entries.push(Object.assign({
          id: uid('e'), status: 'open', settledDate: null, source: 'manual'
        }, payload));
        $('#f-hint').textContent = '登録しました。';
      }

      // 未登録の取引先は、カナだけでもマスタに残しておく（次回の照合精度が上がる）
      if (payload.partyName && !findParty(payload.partyName)) {
        state.parties.push({
          id: uid('p'), name: payload.partyName, kana: payload.partyKana,
          type: payload.kind === 'AR' ? 'customer' : 'vendor',
          closingDay: 31, monthOffset: 1, payDay: 31
        });
      }
      resetEntryForm(true);
      commit();
    });

    $('#f-reset').addEventListener('click', function () { resetEntryForm(false); });
  }

  function resetEntryForm(keepKind) {
    var kind = $('#f-kind').value;
    $('#f-id').value = '';
    $('#f-party').value = ''; $('#f-kana').value = ''; $('#f-docno').value = '';
    $('#f-amount').value = ''; $('#f-due').value = ''; $('#f-memo').value = '';
    $('#f-issue').value = today();
    ui.dueTouched = false;
    if (keepKind) $('#f-kind').value = kind;
    $('#f-submit').textContent = '登録する';
    $('#due-auto-note').textContent = '';
  }

  function initEntryList() {
    $('#entry-table').addEventListener('change', function (ev) {
      var cb = ev.target.closest('.sel');
      if (!cb) return;
      ui.selected[cb.dataset.id] = cb.checked;
      renderEntries();
    });

    $('#entry-table').addEventListener('click', function (ev) {
      var btn = ev.target.closest('button[data-act]');
      if (!btn) return;
      var e = state.entries.find(function (x) { return x.id === btn.dataset.id; });
      if (!e) return;
      if (btn.dataset.act === 'settle') { e.status = 'settled'; e.settledDate = today(); commit(); }
      else if (btn.dataset.act === 'reopen') { e.status = 'open'; e.settledDate = null; commit(); }
      else if (btn.dataset.act === 'edit') {
        $('#f-id').value = e.id;
        $('#f-kind').value = e.kind;
        $('#f-party').value = e.partyName || '';
        $('#f-kana').value = e.partyKana || '';
        $('#f-docno').value = e.docNo || '';
        $('#f-issue').value = e.issueDate || '';
        $('#f-due').value = e.dueDate || '';
        ui.dueTouched = true;
        $('#f-amount').value = e.amount;
        $('#f-memo').value = e.memo || '';
        $('#f-submit').textContent = '更新する';
        $('#entry-form').scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });

    $('#sel-all').addEventListener('change', function (ev) {
      filteredEntries().forEach(function (e) { ui.selected[e.id] = ev.target.checked; });
      renderEntries();
    });

    ['#q-kind', '#q-status', '#q-text'].forEach(function (sel) {
      $(sel).addEventListener('input', function () {
        ui.filters.kind = $('#q-kind').value;
        ui.filters.status = $('#q-status').value;
        ui.filters.text = $('#q-text').value;
        renderEntries();
      });
    });
    $('#q-clear').addEventListener('click', function () {
      $('#q-kind').value = ''; $('#q-status').value = 'open'; $('#q-text').value = '';
      ui.filters = { kind: '', status: 'open', text: '' };
      renderEntries();
    });

    function selectedIds() {
      return Object.keys(ui.selected).filter(function (k) { return ui.selected[k]; });
    }

    $('#bulk-settle').addEventListener('click', function () {
      var ids = selectedIds();
      state.entries.forEach(function (e) {
        if (ids.indexOf(e.id) >= 0) { e.status = 'settled'; e.settledDate = e.settledDate || today(); }
      });
      ui.selected = Object.create(null);
      commit();
    });
    $('#bulk-reopen').addEventListener('click', function () {
      var ids = selectedIds();
      state.entries.forEach(function (e) {
        if (ids.indexOf(e.id) >= 0) { e.status = 'open'; e.settledDate = null; }
      });
      ui.selected = Object.create(null);
      commit();
    });
    $('#bulk-delete').addEventListener('click', function () {
      var ids = selectedIds();
      if (!ids.length) return;
      if (!confirm(ids.length + '件を削除します。よろしいですか？')) return;
      state.entries = state.entries.filter(function (e) { return ids.indexOf(e.id) < 0; });
      ui.selected = Object.create(null);
      commit();
    });
    $('#export-entries').addEventListener('click', function () {
      download('債権債務_' + today() + '.csv', C.toCSV(C.entriesToRows(filteredEntries())), 'text/csv');
    });
  }

  // ------------------------------------------- 銀行CSV消込

  function txKey(tx) {
    return [tx.date, Math.round(tx.amount), C.normalizeName(tx.description)].join('|');
  }

  function importedKeys() {
    var set = Object.create(null);
    state.bankTx.forEach(function (t) { set[txKey(t)] = true; });
    return set;
  }

  function initReconcile() {
    $('#bank-file').addEventListener('change', function (ev) {
      var file = ev.target.files && ev.target.files[0];
      if (!file) return;
      $('#bank-file-name').textContent = file.name;
      readTextFile(file, $('#bank-encoding').value).then(function (text) {
        $('#bank-text').value = text;
        parseBank();
      }).catch(function () {
        $('#bank-parse-msg').textContent = 'ファイルを読み込めませんでした。';
      });
    });

    $('#bank-parse').addEventListener('click', parseBank);
    $('#m-rerun').addEventListener('click', function () {
      state.settings.amountTolerance = Number($('#m-tolerance').value) || 0;
      save();
      runMatch();
    });
    $('#commit-match').addEventListener('click', commitMatch);
    $('#cancel-match').addEventListener('click', function () {
      ui.parsedBank = null; ui.match = null;
      $('#match-card').hidden = true;
      $('#bank-parse-msg').textContent = '';
    });
  }

  function parseBank() {
    var text = $('#bank-text').value;
    if (!text.trim()) { $('#bank-parse-msg').textContent = 'CSVを貼り付けるか、ファイルを選択してください。'; return; }
    var res;
    try {
      res = C.parseBankCSV(text, { columns: ui.bankColumns || undefined });
    } catch (e) {
      $('#bank-parse-msg').textContent = 'CSVを解析できませんでした。';
      return;
    }
    var known = importedKeys();
    var fresh = res.rows.filter(function (r) { return !known[txKey(r)]; });
    var dup = res.rows.length - fresh.length;

    ui.parsedBank = fresh;
    ui.bankColumns = res.columns;
    $('#bank-parse-msg').textContent =
      res.rows.length + '件を読み込みました' +
      (dup ? '（うち' + dup + '件は取込済みのため除外）' : '') +
      (res.skipped ? '／' + res.skipped + '行は日付か金額が読めず読み飛ばしました' : '');

    renderColumnMap(res);
    if (!fresh.length) {
      $('#match-card').hidden = true;
      return;
    }
    runMatch();
  }

  // 列の推定結果を見せて、間違っていれば直せるようにする
  function renderColumnMap(res) {
    var labels = { date: '日付', description: '摘要', inflow: '入金', outflow: '出金', amount: '金額（符号付き）', balance: '残高' };
    var width = 0;
    (res.header ? [res.header] : []).concat([[]]).forEach(function (r) { width = Math.max(width, r.length); });
    C.parseCSV($('#bank-text').value).slice(0, 3).forEach(function (r) { width = Math.max(width, r.length); });

    $('#bank-columns').innerHTML = Object.keys(labels).map(function (key) {
      var opts = ['<option value="-1">（なし）</option>'];
      for (var i = 0; i < width; i++) {
        var head = res.header && res.header[i] ? res.header[i] : ('列' + (i + 1));
        opts.push('<option value="' + i + '"' + (res.columns[key] === i ? ' selected' : '') + '>' + esc(head) + '</option>');
      }
      return '<label>' + esc(labels[key]) + '<select data-col="' + key + '">' + opts.join('') + '</select></label>';
    }).join('');

    $$('#bank-columns select').forEach(function (sel) {
      sel.addEventListener('change', function () {
        var cols = {};
        $$('#bank-columns select').forEach(function (s) { cols[s.dataset.col] = Number(s.value); });
        ui.bankColumns = cols;
        parseBank();
      });
    });
  }

  function matchOptions() {
    return {
      amountTolerance: Number(state.settings.amountTolerance) || 0,
      autoThreshold: Number(state.settings.autoThreshold) || C.MATCH_DEFAULTS.autoThreshold
    };
  }

  function runMatch() {
    if (!ui.parsedBank) return;
    var open = state.entries.filter(function (e) { return e.status !== 'settled'; });
    ui.match = C.autoMatch(open, ui.parsedBank, matchOptions());
    $('#m-tolerance').value = state.settings.amountTolerance || 0;
    $('#match-card').hidden = false;
    renderMatch();
  }

  function renderMatch() {
    var m = ui.match;
    if (!m) return;
    var autoSum = m.auto.reduce(function (a, x) { return a + Math.abs(x.tx.amount); }, 0);

    $('#match-summary').innerHTML =
      '<div><div class="hint">読み込んだ明細</div><b>' + (m.auto.length + m.review.length) + '</b> 件</div>' +
      '<div><div class="hint">自動確定できる</div><b>' + m.auto.length + '</b> 件（' + esc(C.yen(autoSum)) + '）</div>' +
      '<div><div class="hint">要確認</div><b>' + m.review.length + '</b> 件</div>' +
      '<div><div class="hint">手作業の削減見込</div><b>' +
        (m.auto.length + m.review.length ? Math.round(m.auto.length / (m.auto.length + m.review.length) * 100) : 0) +
        '</b> %</div>';

    $('#auto-count').textContent = m.auto.length;
    $('#review-count').textContent = m.review.length;

    $('#auto-table').innerHTML = m.auto.length ? (
      '<table><thead><tr><th></th><th>入出金日</th><th>摘要</th><th class="num">金額</th>' +
      '<th>消込先</th><th class="num">確度</th><th>根拠</th></tr></thead><tbody>' +
      m.auto.map(function (a) {
        return '<tr>' +
          '<td><input type="checkbox" class="auto-sel" data-index="' + a.index + '" checked></td>' +
          '<td>' + esc(a.tx.date) + '</td>' +
          '<td>' + esc(a.tx.description) + '</td>' +
          '<td class="num ' + (a.tx.amount > 0 ? 'amount-in' : 'amount-out') + '">' + esc(C.yen(a.tx.amount)) + '</td>' +
          '<td>' + esc(a.entry.partyName || '—') + '<br><span class="hint">期日 ' + esc(a.entry.dueDate || '—') +
            ' / ' + esc(C.yen(a.entry.amount)) + (a.entry.docNo ? ' / ' + esc(a.entry.docNo) : '') + '</span></td>' +
          '<td class="num"><span class="score ' + scoreClass(a.score) + '">' + a.score + '</span></td>' +
          '<td class="match-reasons">' + esc(a.reasons.join('、')) + '</td></tr>';
      }).join('') + '</tbody></table>'
    ) : '<p class="empty">自動確定できる明細はありませんでした。</p>';

    $('#review-table').innerHTML = m.review.length ? (
      '<table><thead><tr><th>入出金日</th><th>摘要</th><th class="num">金額</th>' +
      '<th>消込先を選ぶ</th><th>操作</th></tr></thead><tbody>' +
      m.review.map(function (r) {
        var opts = ['<option value="">（消込まない）</option>'].concat(r.candidates.map(function (c) {
          return '<option value="' + esc(c.entryId) + '">' +
            esc((c.entry.partyName || '—') + ' / ' + C.yen(c.entry.amount) + ' / 期日' + (c.entry.dueDate || '—') + '（確度' + c.score + '）') +
            '</option>';
        }));
        return '<tr>' +
          '<td>' + esc(r.tx.date) + '</td>' +
          '<td>' + esc(r.tx.description) + '</td>' +
          '<td class="num ' + (r.tx.amount > 0 ? 'amount-in' : 'amount-out') + '">' + esc(C.yen(r.tx.amount)) + '</td>' +
          '<td><select class="review-sel" data-index="' + r.index + '">' + opts.join('') + '</select>' +
            (r.candidates.length ? '' : '<br><span class="hint">該当する債権債務が見つかりません</span>') + '</td>' +
          '<td><button class="btn btn--sm" data-new-entry="' + r.index + '">新規登録する</button></td>' +
          '</tr>';
      }).join('') + '</tbody></table>'
    ) : '<p class="empty">要確認の明細はありません。</p>';

    // 候補が無い明細から、その場で債権債務を起こせるようにする
    $$('#review-table button[data-new-entry]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var r = ui.match.review.find(function (x) { return x.index === Number(btn.dataset.newEntry); });
        if (!r) return;
        $$('.tab').forEach(function (t) { t.classList.toggle('is-active', t.dataset.tab === 'entries'); });
        $$('.panel').forEach(function (p) { p.classList.toggle('is-active', p.id === 'panel-entries'); });
        $('#f-kind').value = r.tx.amount > 0 ? 'AR' : 'AP';
        $('#f-party').value = r.tx.description;
        $('#f-issue').value = r.tx.date;
        $('#f-due').value = r.tx.date;
        $('#f-amount').value = Math.abs(r.tx.amount);
        $('#f-memo').value = '銀行明細から起票';
        $('#entry-form').scrollIntoView({ behavior: 'smooth', block: 'center' });
      });
    });
  }

  function scoreClass(n) { return n >= 85 ? 'score--high' : (n >= 65 ? 'score--mid' : 'score--low'); }

  function commitMatch() {
    if (!ui.match) return;
    var pairs = [];
    $$('#auto-table .auto-sel').forEach(function (cb) {
      if (!cb.checked) return;
      var a = ui.match.auto.find(function (x) { return x.index === Number(cb.dataset.index); });
      if (a) pairs.push({ tx: a.tx, entryId: a.entryId });
    });
    $$('#review-table .review-sel').forEach(function (sel) {
      if (!sel.value) return;
      var r = ui.match.review.find(function (x) { return x.index === Number(sel.dataset.index); });
      if (r) pairs.push({ tx: r.tx, entryId: sel.value });
    });

    if (!pairs.length) { $('#commit-msg').textContent = '消込む明細が選択されていません。'; return; }

    var used = Object.create(null);
    var done = 0;
    pairs.forEach(function (p) {
      if (used[p.entryId]) return;            // 同じ債権を二重に消さない
      var e = state.entries.find(function (x) { return x.id === p.entryId; });
      if (!e || e.status === 'settled') return;
      used[p.entryId] = true;
      e.status = 'settled';
      e.settledDate = p.tx.date;
      e.settledAmount = Math.abs(p.tx.amount);
      state.bankTx.push({
        id: uid('b'), date: p.tx.date, description: p.tx.description,
        amount: p.tx.amount, entryId: e.id, partyName: e.partyName, importedAt: today()
      });
      done++;
    });

    // 明細に残高欄があれば、最終行の残高を現預金残高として取り込む
    var last = ui.parsedBank && ui.parsedBank.length ? ui.parsedBank[ui.parsedBank.length - 1] : null;
    if (last && last.balance != null) {
      state.settings.openingBalance = last.balance;
      state.settings.balanceAsOf = last.date;
    }

    $('#commit-msg').textContent = done + '件を消込みました。' +
      (last && last.balance != null ? '現預金残高を ' + C.yen(last.balance) + '（' + last.date + '時点）に更新しました。' : '');
    ui.parsedBank = null; ui.match = null;
    $('#match-card').hidden = true;
    $('#bank-text').value = '';
    $('#bank-file-name').textContent = '';
    commit();
  }

  function renderBankHistory() {
    var rows = state.bankTx.slice().sort(function (a, b) { return a.date < b.date ? 1 : -1; }).slice(0, 100);
    $('#bank-history').innerHTML = tableHtml(
      ['入出金日', '摘要', '金額', '消込先'],
      rows.map(function (t) {
        return {
          cells: [
            esc(t.date), esc(t.description),
            { num: C.yen(t.amount) },
            esc(t.partyName || '—')
          ]
        };
      }),
      'まだ消込の履歴がありません。'
    );
  }

  // ------------------------------------------- 資金繰り

  function projection(unit, periods) {
    return C.projectCashflow({
      entries: state.entries,
      recurring: state.recurring,
      openingBalance: state.settings.openingBalance,
      asOf: state.settings.balanceAsOf || today(),
      unit: unit || state.settings.cashflowUnit,
      periods: periods,
      alertThreshold: state.settings.alertThreshold
    });
  }

  function renderCashflow() {
    $('#cf-unit').value = state.settings.cashflowUnit;
    $('#cf-opening').value = state.settings.openingBalance;
    $('#cf-asof').value = state.settings.balanceAsOf || today();
    $('#cf-threshold').value = state.settings.alertThreshold;

    var p = projection(state.settings.cashflowUnit);

    var alertEl = $('#cf-alert');
    if (p.min.balance < 0) {
      alertEl.className = 'cf-alert cf-alert--danger';
      alertEl.textContent = '資金ショートの見込みがあります：' + p.min.label + ' に残高 ' + C.yen(p.min.balance) +
        '。入金の前倒し、支払の調整、資金調達の検討が必要です。';
    } else if (p.min.balance < p.threshold) {
      alertEl.className = 'cf-alert';
      alertEl.textContent = '警戒水準（' + C.yen(p.threshold) + '）を下回る期間があります：' +
        p.min.label + ' に残高 ' + C.yen(p.min.balance) + '。';
    } else {
      alertEl.className = 'cf-alert cf-alert--ok';
      alertEl.textContent = '予測期間中、残高は警戒水準を上回って推移する見込みです（最低 ' +
        C.yen(p.min.balance) + '／' + (p.min.label || '—') + '）。';
    }

    $('#cf-table').innerHTML =
      '<table><thead><tr><th>期間</th><th class="num">期首残高</th><th class="num">入金</th>' +
      '<th class="num">出金</th><th class="num">収支</th><th class="num">期末残高</th><th>内訳</th></tr></thead><tbody>' +
      p.periods.map(function (x) {
        var items = x.items.slice().sort(function (a, b) { return a.date < b.date ? -1 : 1; });
        return '<tr class="' + (x.shortage ? 'cf-short' : (x.alert ? 'cf-warn' : '')) + '">' +
          '<td>' + esc(x.label) + '</td>' +
          '<td class="num">' + esc(C.yen(x.opening)) + '</td>' +
          '<td class="num amount-in">' + esc(C.yen(x.inflow)) + '</td>' +
          '<td class="num amount-out">' + esc(C.yen(x.outflow)) + '</td>' +
          '<td class="num">' + esc(C.yen(x.net)) + '</td>' +
          '<td class="num">' + esc(C.yen(x.closing)) + '</td>' +
          '<td>' + (items.length
            ? '<details class="cf-items"><summary>' + items.length + '件</summary><ul>' +
              items.map(function (i) {
                return '<li>' + esc(i.date) + ' ' + (i.type === 'in' ? '入 ' : '出 ') +
                  esc(i.name || '—') + ' ' + esc(C.yen(i.amount)) + (i.fixed ? '（固定）' : '') + '</li>';
              }).join('') + '</ul></details>'
            : '<span class="hint">—</span>') + '</td></tr>';
      }).join('') + '</tbody></table>';
  }

  function initCashflow() {
    $('#cf-unit').addEventListener('change', function () {
      state.settings.cashflowUnit = $('#cf-unit').value; commit();
    });
    ['#cf-opening', '#cf-asof', '#cf-threshold'].forEach(function (sel) {
      $(sel).addEventListener('change', function () {
        state.settings.openingBalance = Number($('#cf-opening').value) || 0;
        state.settings.balanceAsOf = $('#cf-asof').value || today();
        state.settings.alertThreshold = Number($('#cf-threshold').value) || 0;
        commit();
      });
    });
    $('#cf-print').addEventListener('click', function () { window.print(); });

    $('#rec-form').addEventListener('submit', function (ev) {
      ev.preventDefault();
      state.recurring.push({
        id: uid('r'),
        kind: $('#r-kind').value,
        name: $('#r-name').value.trim(),
        amount: Math.abs(Number($('#r-amount').value) || 0),
        dayOfMonth: Math.min(31, Math.max(1, Number($('#r-day').value) || 25)),
        startDate: $('#r-start').value || null,
        endDate: $('#r-end').value || null
      });
      $('#rec-form').reset();
      $('#r-day').value = 25;
      commit();
    });

    $('#rec-table').addEventListener('click', function (ev) {
      var btn = ev.target.closest('button[data-del-rec]');
      if (!btn) return;
      state.recurring = state.recurring.filter(function (r) { return r.id !== btn.dataset.delRec; });
      commit();
    });
  }

  function renderRecurring() {
    $('#rec-table').innerHTML = state.recurring.length ? (
      '<table><thead><tr><th>区分</th><th>名称</th><th class="num">金額</th><th>毎月</th><th>期間</th><th></th></tr></thead><tbody>' +
      state.recurring.map(function (r) {
        return '<tr><td>' + (r.kind === 'in' ? '収入' : '支出') + '</td>' +
          '<td>' + esc(r.name) + '</td>' +
          '<td class="num ' + (r.kind === 'in' ? 'amount-in' : 'amount-out') + '">' + esc(C.yen(r.amount)) + '</td>' +
          '<td>' + (r.dayOfMonth >= 31 ? '末日' : r.dayOfMonth + '日') + '</td>' +
          '<td>' + esc((r.startDate || '—') + ' 〜 ' + (r.endDate || '')) + '</td>' +
          '<td class="num"><button class="btn btn--sm btn--danger" data-del-rec="' + esc(r.id) + '">削除</button></td></tr>';
      }).join('') + '</tbody></table>'
    ) : '<p class="empty">固定費・定期入出金はまだ登録されていません。</p>';
  }

  // ------------------------------------------- 督促

  function renderReminders() {
    var list = C.buildReminders(state.entries, today(), state.settings.companyName);
    $('#reminder-list').innerHTML = list.length ? list.map(function (g, i) {
      return '<div class="reminder">' +
        '<div class="reminder__head">' +
        '<div><strong>' + esc(g.partyName) + '</strong> ' +
        '<span class="reminder__days">最長 ' + g.maxOverdue + '日超過</span> ' +
        '<span class="hint">' + g.items.length + '件</span></div>' +
        '<div><strong>' + esc(C.yen(g.total)) + '</strong> ' +
        '<button class="btn btn--sm" data-copy="' + i + '">文面をコピー</button></div>' +
        '</div>' +
        '<textarea data-body="' + i + '" rows="12">' + esc(g.body) + '</textarea>' +
        '</div>';
    }).join('') : '<p class="empty">期日を過ぎた売掛はありません。</p>';

    $$('#reminder-list button[data-copy]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var ta = $('#reminder-list textarea[data-body="' + btn.dataset.copy + '"]');
        copyText(ta.value).then(function () {
          btn.textContent = 'コピーしました';
          setTimeout(function () { btn.textContent = '文面をコピー'; }, 1600);
        });
      });
    });
  }

  // ------------------------------------------- 設定・マスタ・データ

  function renderSettings() {
    var s = state.settings;
    $('#s-company').value = s.companyName || '';
    $('#s-opening').value = s.openingBalance || 0;
    $('#s-asof').value = s.balanceAsOf || today();
    $('#s-threshold').value = s.alertThreshold || 0;
    $('#s-tax').value = s.taxRate;
    $('#s-tolerance').value = s.amountTolerance || 0;
    $('#s-threshold-match').value = s.autoThreshold;
  }

  function renderParties() {
    $('#party-table').innerHTML = state.parties.length ? (
      '<table><thead><tr><th>名称</th><th>カナ</th><th>区分</th><th>支払条件</th><th class="num">未決済残高</th><th></th></tr></thead><tbody>' +
      state.parties.map(function (p) {
        var bal = state.entries.reduce(function (a, e) {
          if (e.status === 'settled') return a;
          return C.normalizeName(e.partyName) === C.normalizeName(p.name) ? a + (Number(e.amount) || 0) : a;
        }, 0);
        return '<tr><td>' + esc(p.name) + '</td>' +
          '<td>' + esc(p.kana || '') + (p.kana ? '' : '<span class="hint">未登録</span>') + '</td>' +
          '<td>' + (p.type === 'customer' ? '得意先' : (p.type === 'vendor' ? '仕入先' : '両方')) + '</td>' +
          '<td>' + esc(termsLabel(p)) + '</td>' +
          '<td class="num">' + esc(C.yen(bal)) + '</td>' +
          '<td class="num"><button class="btn btn--sm" data-edit-party="' + esc(p.id) + '">編集</button> ' +
          '<button class="btn btn--sm btn--danger" data-del-party="' + esc(p.id) + '">削除</button></td></tr>';
      }).join('') + '</tbody></table>'
    ) : '<p class="empty">取引先が登録されていません。取引を登録すると自動で追加されます。</p>';
  }

  function initSettings() {
    $('#settings-form').addEventListener('submit', function (ev) {
      ev.preventDefault();
      var s = state.settings;
      s.companyName = $('#s-company').value.trim() || '鳴鳳堂';
      s.openingBalance = Number($('#s-opening').value) || 0;
      s.balanceAsOf = $('#s-asof').value || today();
      s.alertThreshold = Number($('#s-threshold').value) || 0;
      s.taxRate = Number($('#s-tax').value) || 0;
      s.amountTolerance = Number($('#s-tolerance').value) || 0;
      s.autoThreshold = Math.min(100, Math.max(0, Number($('#s-threshold-match').value) || C.MATCH_DEFAULTS.autoThreshold));
      $('#s-msg').textContent = '保存しました。';
      commit();
    });

    $('#party-form').addEventListener('submit', function (ev) {
      ev.preventDefault();
      var id = $('#p-id').value;
      var payload = {
        name: $('#p-name').value.trim(),
        kana: $('#p-kana').value.trim(),
        type: $('#p-type').value,
        closingDay: Number($('#p-closing').value),
        monthOffset: Number($('#p-offset').value),
        payDay: Number($('#p-payday').value)
      };
      if (!payload.name) return;
      var existing = id ? state.parties.find(function (p) { return p.id === id; }) : findParty(payload.name);
      if (existing) Object.assign(existing, payload);
      else state.parties.push(Object.assign({ id: uid('p') }, payload));
      $('#party-form').reset();
      $('#p-id').value = '';
      commit();
    });
    $('#p-reset').addEventListener('click', function () {
      $('#party-form').reset(); $('#p-id').value = '';
    });

    $('#party-table').addEventListener('click', function (ev) {
      var edit = ev.target.closest('button[data-edit-party]');
      var del = ev.target.closest('button[data-del-party]');
      if (edit) {
        var p = state.parties.find(function (x) { return x.id === edit.dataset.editParty; });
        if (!p) return;
        $('#p-id').value = p.id; $('#p-name').value = p.name; $('#p-kana').value = p.kana || '';
        $('#p-type').value = p.type; $('#p-closing').value = p.closingDay;
        $('#p-offset').value = p.monthOffset; $('#p-payday').value = p.payDay;
        $('#party-form').scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else if (del) {
        if (!confirm('取引先を削除します。登録済みの取引は残ります。よろしいですか？')) return;
        state.parties = state.parties.filter(function (x) { return x.id !== del.dataset.delParty; });
        commit();
      }
    });

    // --- データの保管
    $('#backup-export').addEventListener('click', function () {
      download('バックオフィス_バックアップ_' + today() + '.json', JSON.stringify(state, null, 2), 'application/json');
      flash('バックアップを書き出しました。');
    });

    $('#backup-import').addEventListener('change', function (ev) {
      var file = ev.target.files && ev.target.files[0];
      if (!file) return;
      readTextFile(file, 'utf-8').then(function (text) {
        var parsed;
        try { parsed = JSON.parse(text); } catch (e) { flash('JSONとして読み込めませんでした。', true); return; }
        if (!parsed || !Array.isArray(parsed.entries)) { flash('このファイルはバックアップではないようです。', true); return; }
        if (!confirm('現在のデータを、読み込んだバックアップで置き換えます。よろしいですか？')) return;
        state = Object.assign(defaultState(), parsed);
        state.settings = Object.assign(defaultState().settings, parsed.settings || {});
        flash('バックアップを読み込みました（取引 ' + state.entries.length + '件）。');
        commit();
      });
      ev.target.value = '';
    });

    $('#csv-export-all').addEventListener('click', function () {
      download('債権債務_全件_' + today() + '.csv', C.toCSV(C.entriesToRows(state.entries)), 'text/csv');
    });

    $('#csv-import').addEventListener('change', function (ev) {
      var file = ev.target.files && ev.target.files[0];
      if (!file) return;
      readTextFile(file, 'auto').then(function (text) {
        var res = C.rowsToEntries(C.parseCSV(text), 'csv');
        if (!res.entries.length) {
          flash('取り込める行がありませんでした。' + (res.errors.length ? res.errors[0].line + '行目：' + res.errors[0].reason : ''), true);
          return;
        }
        state.entries = state.entries.concat(res.entries);
        flash(res.entries.length + '件を取り込みました。' +
          (res.errors.length ? res.errors.length + '行は読み飛ばしました（' + res.errors.slice(0, 3).map(function (e) { return e.line + '行目'; }).join('、') + ' ほか）。' : ''));
        commit();
      });
      ev.target.value = '';
    });

    $('#load-sample').addEventListener('click', function () {
      if (state.entries.length && !confirm('サンプルデータを追加します。既存のデータはそのまま残ります。よろしいですか？')) return;
      loadSample();
      flash('サンプルデータを読み込みました。動作を確認したら「全データを消去」で初期化できます。');
      commit();
    });

    $('#wipe').addEventListener('click', function () {
      if (!confirm('すべてのデータを消去します。元に戻せません。バックアップは書き出しましたか？')) return;
      state = defaultState();
      ui.selected = Object.create(null);
      flash('データを消去しました。');
      commit();
    });
  }

  // ------------------------------------------- サンプル

  function loadSample() {
    var t = new Date();
    function rel(days) { return C.addDays(C.ymd(t), days); }

    state.settings.openingBalance = 4200000;
    state.settings.balanceAsOf = C.ymd(t);
    state.settings.alertThreshold = 1500000;

    var parties = [
      { name: '株式会社阿蘇観光', kana: 'アソカンコウ', type: 'customer', closingDay: 31, monthOffset: 1, payDay: 31 },
      { name: '肥後トラベル株式会社', kana: 'ヒゴトラベル', type: 'customer', closingDay: 20, monthOffset: 1, payDay: 10 },
      { name: '九州インバウンド合同会社', kana: 'キユウシユウインバウンド', type: 'customer', closingDay: 31, monthOffset: 2, payDay: 25 },
      { name: '阿蘇食材センター', kana: 'アソシヨクザイセンター', type: 'vendor', closingDay: 31, monthOffset: 1, payDay: 25 },
      { name: '熊本リネンサービス', kana: 'クマモトリネン', type: 'vendor', closingDay: 20, monthOffset: 1, payDay: 20 },
      { name: '南阿蘇酒販', kana: 'ミナミアソシユハン', type: 'vendor', closingDay: 31, monthOffset: 1, payDay: 31 }
    ];
    parties.forEach(function (p) {
      if (!findParty(p.name)) state.parties.push(Object.assign({ id: uid('p') }, p));
    });

    var samples = [
      { kind: 'AR', party: '株式会社阿蘇観光', kana: 'アソカンコウ', doc: 'INV-2601', issue: rel(-75), due: rel(-45), amount: 682000, memo: '団体宿泊 3月分' },
      { kind: 'AR', party: '株式会社阿蘇観光', kana: 'アソカンコウ', doc: 'INV-2618', issue: rel(-40), due: rel(-8), amount: 451000, memo: '団体宿泊 4月分' },
      { kind: 'AR', party: '肥後トラベル株式会社', kana: 'ヒゴトラベル', doc: 'INV-2620', issue: rel(-30), due: rel(6), amount: 330000, memo: '体験プラン送客' },
      { kind: 'AR', party: '九州インバウンド合同会社', kana: 'キユウシユウインバウンド', doc: 'INV-2625', issue: rel(-12), due: rel(35), amount: 1210000, memo: '海外旅行会社 5月分' },
      { kind: 'AR', party: '肥後トラベル株式会社', kana: 'ヒゴトラベル', doc: 'INV-2631', issue: rel(-3), due: rel(28), amount: 275000, memo: '茶道体験' },
      { kind: 'AP', party: '阿蘇食材センター', kana: 'アソシヨクザイセンター', doc: '', issue: rel(-35), due: rel(-2), amount: 386400, memo: '食材 4月分' },
      { kind: 'AP', party: '熊本リネンサービス', kana: 'クマモトリネン', doc: '', issue: rel(-25), due: rel(4), amount: 128700, memo: 'リネン 4月分' },
      { kind: 'AP', party: '南阿蘇酒販', kana: 'ミナミアソシユハン', doc: '', issue: rel(-20), due: rel(11), amount: 97240, memo: '酒類仕入' },
      { kind: 'AP', party: '阿蘇食材センター', kana: 'アソシヨクザイセンター', doc: '', issue: rel(-5), due: rel(26), amount: 412800, memo: '食材 5月分' }
    ];
    samples.forEach(function (s) {
      state.entries.push({
        id: uid('e'), kind: s.kind, partyName: s.party, partyKana: s.kana, docNo: s.doc,
        issueDate: s.issue, dueDate: s.due, amount: s.amount,
        status: 'open', settledDate: null, memo: s.memo, source: 'sample'
      });
    });

    [
      { kind: 'out', name: '給与', amount: 2350000, dayOfMonth: 25 },
      { kind: 'out', name: '家賃・地代', amount: 480000, dayOfMonth: 27 },
      { kind: 'out', name: '借入返済（元利）', amount: 315000, dayOfMonth: 10 },
      { kind: 'out', name: '水道光熱費', amount: 268000, dayOfMonth: 28 },
      { kind: 'in', name: 'OTA入金（じゃらん・楽天等）', amount: 1850000, dayOfMonth: 15 }
    ].forEach(function (r) {
      state.recurring.push(Object.assign({ id: uid('r'), startDate: null, endDate: null }, r));
    });
  }

  // ------------------------------------------------------------ 起動

  function init() {
    if (!C) {
      document.body.innerHTML = '<p style="padding:2rem">core.js を読み込めませんでした。ファイル一式が同じフォルダにあるか確認してください。</p>';
      return;
    }
    $('#today-label').textContent = new Date().toLocaleDateString('ja-JP', {
      year: 'numeric', month: 'long', day: 'numeric', weekday: 'short'
    });
    load();
    initTabs();
    initEntryForm();
    initEntryList();
    initReconcile();
    initCashflow();
    initSettings();
    render();
    setSaveState(state.entries.length ? '読み込み済み' : '新規', true);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
