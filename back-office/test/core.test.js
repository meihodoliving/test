/* node --test back-office/test/ */
const test = require('node:test');
const assert = require('node:assert');
const C = require('../core.js');

test('金額のゆれを吸収する', () => {
  assert.strictEqual(C.parseAmount('¥1,234'), 1234);
  assert.strictEqual(C.parseAmount('1,234円'), 1234);
  assert.strictEqual(C.parseAmount('▲5,000'), -5000);
  assert.strictEqual(C.parseAmount('(2,000)'), -2000);
  assert.strictEqual(C.parseAmount('１２３'), 123);
  assert.strictEqual(C.parseAmount(''), null);
  assert.strictEqual(C.parseAmount('   '), null);
  assert.strictEqual(C.parseAmount('お預り'), null);
  assert.strictEqual(C.parseAmount(0), 0);
});

test('日付のゆれを吸収する', () => {
  assert.strictEqual(C.parseDate('2026/4/1'), '2026-04-01');
  assert.strictEqual(C.parseDate('2026-04-01'), '2026-04-01');
  assert.strictEqual(C.parseDate('20260401'), '2026-04-01');
  assert.strictEqual(C.parseDate('2026年4月1日'), '2026-04-01');
  assert.strictEqual(C.parseDate('4/1', 2026), '2026-04-01');
  assert.strictEqual(C.parseDate('R8.4.1'), '2026-04-01');
  assert.strictEqual(C.parseDate('2026/2/30'), null, '存在しない日付は null');
  assert.strictEqual(C.parseDate('摘要'), null);
});

test('締日・支払サイトから期日を出す', () => {
  // 月末締め翌月末払い
  const t1 = { closingDay: 31, monthOffset: 1, payDay: 31 };
  assert.strictEqual(C.calcDueDate('2026-04-10', t1), '2026-05-31');
  assert.strictEqual(C.calcDueDate('2026-04-30', t1), '2026-05-31');
  // 20日締め翌月10日払い。21日以降は次の締めに送られる
  const t2 = { closingDay: 20, monthOffset: 1, payDay: 10 };
  assert.strictEqual(C.calcDueDate('2026-04-20', t2), '2026-05-10');
  assert.strictEqual(C.calcDueDate('2026-04-21', t2), '2026-06-10');
  // 月末払いは短い月でも溢れない
  assert.strictEqual(C.calcDueDate('2026-01-15', t1), '2026-02-28');
  // 年をまたぐ
  assert.strictEqual(C.calcDueDate('2026-12-05', t1), '2027-01-31');
  // 当月払い
  assert.strictEqual(C.calcDueDate('2026-04-05', { closingDay: 31, monthOffset: 0, payDay: 25 }), '2026-04-25');
});

test('土日を外す', () => {
  assert.strictEqual(C.shiftBusinessDay('2026-05-31'), '2026-05-29'); // 日曜 → 前の金曜
  assert.strictEqual(C.shiftBusinessDay('2026-05-31', 'after'), '2026-06-01');
  assert.strictEqual(C.shiftBusinessDay('2026-05-29'), '2026-05-29'); // 平日は動かさない
});

test('CSV を RFC4180 で読む', () => {
  const rows = C.parseCSV('a,b,c\r\n1,"2,5",3\r\n"改\n行",x,"引用""符"');
  assert.deepStrictEqual(rows[0], ['a', 'b', 'c']);
  assert.deepStrictEqual(rows[1], ['1', '2,5', '3']);
  assert.deepStrictEqual(rows[2], ['改\n行', 'x', '引用"符']);
  assert.strictEqual(C.parseCSV('﻿a,b\n1,2')[0][0], 'a', 'BOM を落とす');
  assert.strictEqual(C.parseCSV('a\tb\n1\t2')[1].length, 2, 'タブ区切りも読む');
});

test('銀行 CSV：入金/出金 2列型', () => {
  const csv = [
    '日付,摘要,お預入額,お引出額,残高',
    '2026/04/30,ﾌﾘｺﾐ ｱｿｶﾝｺｳ(ｶ,330000,,1330000',
    '2026/05/01,ﾃﾞﾝｷﾘｮｳｷﾝ,,42800,1287200',
    '合計,,,,'
  ].join('\n');
  const r = C.parseBankCSV(csv);
  assert.strictEqual(r.rows.length, 2);
  assert.strictEqual(r.rows[0].amount, 330000);
  assert.strictEqual(r.rows[1].amount, -42800);
  assert.strictEqual(r.rows[0].balance, 1330000);
  assert.strictEqual(r.skipped, 1, '日付の無い合計行は読み飛ばす');
});

test('銀行 CSV：符号付き1列型／見出しなし', () => {
  const r = C.parseBankCSV('2026/04/30,ｱｿｶﾝｺｳ,330000\n2026/05/01,ﾃﾞﾝｷ,-42800');
  assert.strictEqual(r.rows.length, 2);
  assert.strictEqual(r.rows[0].amount, 330000);
  assert.strictEqual(r.rows[1].amount, -42800);
});

test('取引先名の表記ゆれを吸収する', () => {
  assert.ok(C.nameSimilarity('株式会社阿蘇観光', '阿蘇観光') > 0.9);
  assert.ok(C.nameSimilarity('ｱｿｶﾝｺｳ(ｶ', 'アソカンコウ') > 0.8, '半角カナ＋カ)略記');
  assert.ok(C.nameSimilarity('阿蘇観光', '熊本電力') < 0.3);
  assert.strictEqual(C.nameSimilarity('', '阿蘇観光'), 0);
});

const entries = [
  { id: 'e1', kind: 'AR', partyName: '株式会社阿蘇観光', partyKana: 'アソカンコウ', amount: 330000, dueDate: '2026-04-30', status: 'open' },
  { id: 'e2', kind: 'AR', partyName: '肥後トラベル', amount: 330000, dueDate: '2026-06-30', status: 'open' },
  { id: 'e3', kind: 'AP', partyName: '熊本電力', partyKana: 'クマモトデンリョク', amount: 42800, dueDate: '2026-05-01', status: 'open' },
  { id: 'e4', kind: 'AR', partyName: '決済済みの分', amount: 330000, dueDate: '2026-04-30', status: 'settled' }
];

test('入金は債権、出金は債務にしか当たらない', () => {
  const inflow = { date: '2026-04-30', description: 'ｱｿｶﾝｺｳ', amount: 330000 };
  assert.strictEqual(C.scoreMatch(entries[2], inflow).score, 0, '入金が買掛に当たってはいけない');
  const outflow = { date: '2026-05-01', description: 'ﾃﾞﾝｷ', amount: -42800 };
  assert.strictEqual(C.scoreMatch(entries[0], outflow).score, 0);
});

test('決済済みは候補に出さない', () => {
  const tx = { date: '2026-04-30', description: '決済済みの分', amount: 330000 };
  assert.strictEqual(C.scoreMatch(entries[3], tx).score, 0);
});

test('自動消込：名前と期日で同額を撃ち分ける', () => {
  const txs = [
    { date: '2026-04-30', description: 'ﾌﾘｺﾐ ｱｿｶﾝｺｳ(ｶ', amount: 330000 },
    { date: '2026-05-01', description: 'ｸﾏﾓﾄﾃﾞﾝﾘｮｸ', amount: -42800 }
  ];
  const r = C.autoMatch(entries, txs);
  assert.strictEqual(r.auto.length, 2, `自動消込されるはず: ${JSON.stringify(r.review)}`);
  assert.strictEqual(r.auto[0].entryId, 'e1', '肥後トラベルではなく阿蘇観光に当たる');
  assert.strictEqual(r.auto[1].entryId, 'e3');
  assert.strictEqual(r.review.length, 0);
});

test('カナ未登録でも、金額と期日が一致し候補が一意なら自動消込する', () => {
  const noKana = [{ id: 'n1', kind: 'AP', partyName: '熊本電力', amount: 42800, dueDate: '2026-05-01', status: 'open' }];
  const r = C.autoMatch(noKana, [{ date: '2026-05-01', description: 'ｸﾏﾓﾄﾃﾞﾝﾘｮｸ', amount: -42800 }]);
  assert.strictEqual(r.auto.length, 1, '漢字とカナは照合できないが、金額＋期日＋一意性で確定できる');
  assert.deepStrictEqual(r.auto[0].reasons, ['金額が完全一致', '期日どおり']);
});

test('金額が一致していても期日から離れていれば人に回す', () => {
  const e = [{ id: 'd1', kind: 'AR', partyName: 'A社', amount: 42800, dueDate: '2026-05-01', status: 'open' }];
  const r = C.autoMatch(e, [{ date: '2026-05-20', description: 'ﾌﾘｺﾐ', amount: 42800 }]);
  assert.strictEqual(r.auto.length, 0);
  assert.strictEqual(r.review[0].candidates.length, 1, '候補としては提示する');
});

test('自動消込：判別できないものは人に回す', () => {
  const ambiguous = [
    { id: 'a1', kind: 'AR', partyName: 'A社', amount: 100000, dueDate: '2026-04-30', status: 'open' },
    { id: 'a2', kind: 'AR', partyName: 'B社', amount: 100000, dueDate: '2026-04-30', status: 'open' }
  ];
  const r = C.autoMatch(ambiguous, [{ date: '2026-04-30', description: 'ﾌﾘｺﾐ', amount: 100000 }]);
  assert.strictEqual(r.auto.length, 0, '同額・同期日で名前の手がかりが無ければ自動消込しない');
  assert.strictEqual(r.review[0].candidates.length, 2);
});

test('自動消込：ひとつの債権を二重に消さない', () => {
  const one = [{ id: 'x1', kind: 'AR', partyName: '阿蘇観光', amount: 50000, dueDate: '2026-04-30', status: 'open' }];
  const r = C.autoMatch(one, [
    { date: '2026-04-30', description: 'ｱｿｶﾝｺｳ', amount: 50000 },
    { date: '2026-04-30', description: 'ｱｿｶﾝｺｳ', amount: 50000 }
  ]);
  assert.strictEqual(r.auto.length, 1);
  assert.strictEqual(r.review.length, 1);
});

test('振込手数料の差引に誤差許容で追随する', () => {
  const e = [{ id: 'f1', kind: 'AR', partyName: '阿蘇観光', amount: 330000, dueDate: '2026-04-30', status: 'open' }];
  const tx = [{ date: '2026-04-30', description: 'ｱｿｶﾝｺｳ', amount: 329120 }]; // 手数料 880 円引き
  assert.strictEqual(C.autoMatch(e, tx).auto.length, 0, '既定では当てない');
  const r = C.autoMatch(e, tx, { amountTolerance: 880 });
  assert.strictEqual(r.auto.length, 1, '許容差を設定すれば当たる');
});

test('滞留集計', () => {
  const s = C.summarize(entries, '2026-05-15');
  assert.strictEqual(s.arOpen, 660000);
  assert.strictEqual(s.arCount, 2);
  assert.strictEqual(s.arOverdue, 330000, '4/30 期日は超過');
  assert.strictEqual(s.apOverdue, 42800);
  const aging = C.agingBuckets(entries, 'AR', '2026-05-15');
  assert.strictEqual(aging[0].label, '期日前');
  assert.strictEqual(aging[0].total, 330000, '6/30 期日は期日前');
  assert.strictEqual(aging[1].total, 330000, '4/30 期日は 1-30 日');
});

test('資金繰り：期日超過は最初の期間に寄せる', () => {
  const r = C.projectCashflow({
    entries: [{ id: 'o1', kind: 'AR', amount: 100000, dueDate: '2026-01-01', status: 'open', partyName: '古い債権' }],
    openingBalance: 500000, asOf: '2026-05-15', unit: 'week', periods: 2
  });
  assert.strictEqual(r.periods[0].inflow, 100000);
  assert.strictEqual(r.periods[0].closing, 600000);
});

test('資金繰り：固定費と残高推移、資金ショート検知', () => {
  const r = C.projectCashflow({
    entries: [{ id: 'p1', kind: 'AP', amount: 800000, dueDate: '2026-06-30', status: 'open', partyName: '仕入' }],
    recurring: [{ id: 'r1', kind: 'out', name: '給与', amount: 1200000, dayOfMonth: 25 }],
    openingBalance: 1000000, asOf: '2026-05-01', unit: 'month', periods: 3, alertThreshold: 300000
  });
  assert.strictEqual(r.periods.length, 3);
  assert.strictEqual(r.periods[0].outflow, 1200000, '5月は給与のみ');
  assert.strictEqual(r.periods[0].closing, -200000);
  assert.ok(r.periods[0].shortage, '資金ショートを検知する');
  assert.strictEqual(r.periods[1].outflow, 2000000, '6月は給与＋仕入');
  assert.strictEqual(r.ending, -3400000);
  assert.strictEqual(r.min.balance, -3400000);
});

test('定期支払の発生日：月末指定は短い月でも溢れない', () => {
  const occ = C.recurringOccurrences({ kind: 'out', amount: 1, dayOfMonth: 31 }, '2026-01-01', '2026-04-30');
  assert.deepStrictEqual(occ, ['2026-01-31', '2026-02-28', '2026-03-31', '2026-04-30']);
});

test('督促リストは取引先ごとにまとまる', () => {
  const r = C.buildReminders([
    { id: 'r1', kind: 'AR', partyName: '阿蘇観光', amount: 100000, dueDate: '2026-03-31', status: 'open', docNo: 'INV-001' },
    { id: 'r2', kind: 'AR', partyName: '阿蘇観光', amount: 50000, dueDate: '2026-04-30', status: 'open' },
    { id: 'r3', kind: 'AR', partyName: '肥後トラベル', amount: 20000, dueDate: '2026-06-30', status: 'open' }
  ], '2026-05-15', '鳴鳳堂');
  assert.strictEqual(r.length, 1, '期日前の肥後トラベルは含まない');
  assert.strictEqual(r[0].total, 150000);
  assert.ok(r[0].body.includes('INV-001'));
  assert.ok(r[0].body.includes('合計 ¥150,000'));
});

test('CSV 往復で欠落しない', () => {
  const src = [{ id: 's1', kind: 'AR', partyName: '阿蘇観光', partyKana: 'アソカンコウ', docNo: 'INV-1', issueDate: '2026-04-01', dueDate: '2026-05-31', amount: 330000, status: 'open', settledDate: null, memo: '4月分' }];
  const back = C.rowsToEntries(C.parseCSV(C.toCSV(C.entriesToRows(src))));
  assert.strictEqual(back.errors.length, 0);
  assert.strictEqual(back.entries.length, 1);
  const e = back.entries[0];
  assert.strictEqual(e.kind, 'AR');
  assert.strictEqual(e.partyName, '阿蘇観光');
  assert.strictEqual(e.amount, 330000);
  assert.strictEqual(e.dueDate, '2026-05-31');
  assert.strictEqual(e.memo, '4月分');
});

test('取込エラーは行番号つきで返す', () => {
  const rows = C.parseCSV('区分,取引先,取引先カナ,請求番号,発生日,期日,金額,状態,決済日,摘要\n売掛,A,,,,2026-05-31,かたかな,未決済,,\n');
  const r = C.rowsToEntries(rows);
  assert.strictEqual(r.entries.length, 0);
  assert.strictEqual(r.errors[0].line, 2);
});

test('見込み案件は予測に含めつつ、確定ベースの残高は別に持つ', () => {
  const r = C.projectCashflow({
    entries: [
      { id: 'c1', kind: 'AR', amount: 100000, dueDate: '2026-05-10', status: 'open', partyName: '確定分', certainty: 'confirmed' },
      { id: 'e1', kind: 'AR', amount: 500000, dueDate: '2026-05-10', status: 'open', partyName: '見込み分', certainty: 'estimate' }
    ],
    openingBalance: 0, asOf: '2026-05-01', unit: 'month', periods: 1
  });
  assert.strictEqual(r.periods[0].inflow, 600000, '見込みも合算した予測残高');
  assert.strictEqual(r.periods[0].closing, 600000);
  assert.strictEqual(r.periods[0].confirmedInflow, 100000, '確定分だけの内訳');
  assert.strictEqual(r.periods[0].confirmedClosing, 100000);
  assert.strictEqual(r.ending, 600000);
  assert.strictEqual(r.confirmedEnding, 100000);
});

test('certainty を省略した既存データは確定として扱う（後方互換）', () => {
  const r = C.projectCashflow({
    entries: [{ id: 'x1', kind: 'AP', amount: 30000, dueDate: '2026-05-10', status: 'open', partyName: '既存分' }],
    openingBalance: 0, asOf: '2026-05-01', unit: 'month', periods: 1
  });
  assert.strictEqual(r.periods[0].confirmedOutflow, 30000);
  assert.strictEqual(r.confirmedEnding, r.ending);
});

test('固定費・定期入出金は見込みではなく確定として数える', () => {
  const r = C.projectCashflow({
    entries: [],
    recurring: [{ id: 'rec1', kind: 'out', name: '給与', amount: 200000, dayOfMonth: 25 }],
    openingBalance: 0, asOf: '2026-05-01', unit: 'month', periods: 1
  });
  assert.strictEqual(r.periods[0].confirmedOutflow, 200000);
  assert.strictEqual(r.confirmedEnding, -200000);
});

test('本部への資金不足報告：確定ベースでショートするときは金額と時期を示す', () => {
  const proj = C.projectCashflow({
    entries: [
      { id: 'a1', kind: 'AP', amount: 900000, dueDate: '2026-05-15', status: 'open', partyName: '仕入先', certainty: 'confirmed' },
      { id: 'a2', kind: 'AR', amount: 400000, dueDate: '2026-06-20', status: 'open', partyName: '見込み顧客', certainty: 'estimate' }
    ],
    openingBalance: 300000, asOf: '2026-05-01', unit: 'month', periods: 2, alertThreshold: 100000
  });
  const report = C.buildShortageReport(proj, { companyName: '鳴鳳堂', recipient: '本部' });
  assert.strictEqual(report.hasShortage, true);
  assert.ok(report.requestAmount > 0, '依頼額が算出される');
  assert.ok(report.body.includes('本部 御中'));
  assert.ok(report.body.includes('確定分のみ'), '確定ベースであることを明記する');
  assert.ok(report.body.includes('見積り中の案件を含めた場合'), '見込みを含めた参考値も出す');
  assert.ok(!report.body.includes('見込み顧客'), '見込み分の内訳は資金不足の根拠に混ぜない');
});

test('本部への資金不足報告：問題が無ければその旨を伝える', () => {
  const proj = C.projectCashflow({
    entries: [{ id: 'ok1', kind: 'AR', amount: 500000, dueDate: '2026-05-10', status: 'open', partyName: '順調', certainty: 'confirmed' }],
    openingBalance: 1000000, asOf: '2026-05-01', unit: 'month', periods: 2, alertThreshold: 100000
  });
  const report = C.buildShortageReport(proj);
  assert.strictEqual(report.hasShortage, false);
  assert.ok(report.body.includes('下回る見込みはありません'));
});

test('確度つきの CSV が往復する', () => {
  const src = [
    { id: 'e1', kind: 'AR', certainty: 'estimate', partyName: '見込み先', amount: 200000, status: 'open' },
    { id: 'c1', kind: 'AP', certainty: 'confirmed', partyName: '確定先', amount: 50000, status: 'open' }
  ];
  const back = C.rowsToEntries(C.parseCSV(C.toCSV(C.entriesToRows(src))));
  assert.strictEqual(back.errors.length, 0);
  assert.strictEqual(back.entries[0].certainty, 'estimate');
  assert.strictEqual(back.entries[1].certainty, 'confirmed');
});

test('税込計算は切り捨て', () => {
  assert.strictEqual(C.withTax(1000, 10), 1100);
  assert.strictEqual(C.withTax(1111, 10), 1222);
  assert.strictEqual(C.withTax(1000, 0), 1000);
});
