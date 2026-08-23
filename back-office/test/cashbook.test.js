/* node --test back-office/test/cashbook.test.js */
const test = require('node:test');
const assert = require('node:assert');
const CB = require('../cashbook/cashbook.js');

// xlsx リーダーが返す形のセル（色つき）
const cell = (v, tone) => ({ v, tone: tone || 'black', color: null });

const HEADER = ['日付', '摘要', '入金', '出金', '残高'];

test('見出し行から列を見つける', () => {
  const m = CB.guessColumns(HEADER);
  assert.strictEqual(m.date, 0);
  assert.strictEqual(m.description, 1);
  assert.strictEqual(m.inflow, 2);
  assert.strictEqual(m.outflow, 3);
  assert.strictEqual(m.balance, 4);
});

test('見出しが表の途中にあっても見つける', () => {
  const rows = [
    ['5月 資金表', '', '', '', ''],
    ['', '', '', '', ''],
    HEADER,
    [cell('2026/05/02'), cell('現金売上'), cell(85000), cell(''), cell(85000)]
  ];
  const r = CB.readFundTable(rows);
  assert.strictEqual(r.entries.length, 1);
  assert.strictEqual(r.entries[0].description, '現金売上');
  assert.strictEqual(r.entries[0].inflow, 85000);
});

test('日付か金額の無い行は読み飛ばす', () => {
  const rows = [
    HEADER,
    [cell('2026/05/02'), cell('現金売上'), cell(85000), cell(''), cell('')],
    [cell(''), cell('小計'), cell(''), cell(''), cell('')],
    [cell('2026/05/03'), cell('備考のみ'), cell(''), cell(''), cell('')]
  ];
  const r = CB.readFundTable(rows);
  assert.strictEqual(r.entries.length, 1);
  assert.strictEqual(r.skipped, 2);
});

test('集計に入れなかった行は、行番号と理由つきで返す', () => {
  const rows = [
    HEADER,
    [cell('2026/05/02'), cell('現金売上'), cell(85000), cell(''), cell('')],
    [cell('2026/05/15'), cell('ATM引き出し'), cell(''), cell(0), cell('')]
  ];
  const r = CB.readFundTable(rows);
  assert.strictEqual(r.entries.length, 1);
  assert.strictEqual(r.skippedRows.length, 1, '金額0の行を黙って捨てない');
  assert.strictEqual(r.skippedRows[0].description, 'ATM引き出し');
  assert.strictEqual(r.skippedRows[0].date, '2026-05-15');
  assert.ok(r.skippedRows[0].reason.includes('0'));
});

test('行の色を拾う（摘要セル優先）', () => {
  const rows = [
    HEADER,
    [cell('2026/05/07'), cell('売上入金 阿蘇観光', 'blue'), cell(330000), cell(''), cell('')],
    [cell('2026/05/23'), cell('現金返済', 'red'), cell(''), cell(30000), cell('')],
    [cell('2026/05/10'), cell('消耗品購入'), cell(''), cell(12340), cell('')]
  ];
  const r = CB.readFundTable(rows);
  assert.deepStrictEqual(r.entries.map(e => e.tone), ['blue', 'red', 'black']);
});

test('色は目安どまり — 通帳未確認なら confident:false', () => {
  const e = { description: '売上入金', tone: 'blue', inflow: 330000, outflow: 0, date: '2026-05-07' };
  const v = CB.classify(e, {});
  assert.strictEqual(v.decision, 'bank');
  assert.strictEqual(v.confident, false, '色だけの判定は確定扱いにしてはいけない');
});

test('通帳に同じ動きがあれば銀行取引として確定する', () => {
  const e = { description: '売上入金 阿蘇観光', tone: 'black', inflow: 330000, outflow: 0, date: '2026-05-07' };
  const bank = [{ date: '2026-05-07', description: 'ﾌﾘｺﾐ ｱｿｶﾝｺｳ(ｶ', amount: 330000 }];
  const [r] = CB.classifyAll([e], bank, []);
  assert.strictEqual(r.decision, 'bank', '黒字でも通帳にあれば銀行取引');
  assert.strictEqual(r.confident, true);
  assert.ok(r.reason.includes('通帳'));
});

test('見出しに「会計処理」列があれば済みかどうかを読み取る', () => {
  const HEADER = ['日付', '摘要', '入金', '出金', '残高', '勘定科目', '会計処理'];
  const rows = [
    HEADER,
    [cell('2026/05/02'), cell('売上'), cell(85000), cell(''), cell(''), cell('売上高'), cell('済み')],
    [cell('2026/05/10'), cell('消耗品購入'), cell(''), cell(12340), cell(''), cell('雑費'), cell('')]
  ];
  const r = CB.readFundTable(rows);
  assert.strictEqual(r.entries[0].alreadyProcessed, true);
  assert.strictEqual(r.entries[1].alreadyProcessed, false);
});

test('会計処理が済みの行は、色や科目にかかわらず作業対象から外す', () => {
  // 実際の資金表は、本部勘定・消費税引当のような高額科目でも色は付いていないことが多い。
  // 会計処理済みの印があれば、そちらを優先して確定扱いにする。
  const e = {
    description: '本部勘定（委託料）', account: '本部勘定（委託料）', tone: 'black',
    inflow: 0, outflow: 1697856, date: '2026-05-10', alreadyProcessed: true
  };
  const [r] = CB.classifyAll([e], [], []);
  assert.strictEqual(r.decision, 'exclude');
  assert.strictEqual(r.confident, true);
  assert.strictEqual(r.source, 'processed');
});

test('会計処理済みでも、ツール側で確定した判断のほうが優先される', () => {
  const e = {
    description: 'X', tone: 'black', inflow: 0, outflow: 1000, date: '2026-05-10',
    alreadyProcessed: true, decision: 'cash', confirmed: true, reason: '現金で確認済み'
  };
  const [r] = CB.classifyAll([e], [], []);
  assert.strictEqual(r.decision, 'cash');
  assert.strictEqual(r.source, 'confirmed');
});

test('摘要の見出しが空欄でも、文字量から列を推測する', () => {
  // 実際の資金表で見られる形：勘定科目の隣が無題（全角スペースのみ）で、そこに摘要が入っている
  const HEADER = ['日付', '収入', '支出', '残高', '勘定科目', '　', '税10%'];
  const rows = [
    HEADER,
    [cell('2026/05/02'), cell(96381), cell(''), cell(''), cell('借入金'), cell('増元家'), cell('')],
    [cell('2026/05/10'), cell(''), cell(12340), cell(''), cell('雑費'), cell('スマレジ月額使用料'), cell('')]
  ];
  const r = CB.readFundTable(rows);
  assert.strictEqual(r.columns.description, 5, '見出しが空欄でも G 列（5）を摘要と推測する');
  assert.strictEqual(r.entries[0].description, '増元家');
  assert.strictEqual(r.entries[1].description, 'スマレジ月額使用料');
});

test('列の対応をあらかじめ指定したときは、空欄の摘要でも推測で上書きしない', () => {
  const HEADER = ['日付', '収入', '支出', '残高', '勘定科目', '　'];
  const rows = [
    HEADER,
    [cell('2026/05/02'), cell(96381), cell(''), cell(''), cell('借入金'), cell('増元家')]
  ];
  const explicit = { date: 0, inflow: 1, outflow: 2, balance: 3, account: 4, description: -1 };
  const r = CB.readFundTable(rows, { columns: explicit });
  assert.strictEqual(r.entries[0].description, '', '摘要なしという明示的な指定は尊重する');
});

test('浄化槽点検のような口座振替は、ルールで除外できる', () => {
  const e = { description: '浄化槽点検', tone: 'black', inflow: 0, outflow: 16500, date: '2026-05-18' };
  const rules = [{ id: 'r1', kind: 'exclude', keyword: '浄化槽', note: '口座振替' }];
  const [r] = CB.classifyAll([e], [], rules);
  assert.strictEqual(r.decision, 'exclude', '黒字でも口座振替なら現金出納帳から外す');
  assert.strictEqual(r.confident, true);
  assert.ok(r.reason.includes('浄化槽'));
});

test('ルールは色や通帳より優先される', () => {
  const e = { description: '浄化槽点検', tone: 'blue', inflow: 0, outflow: 16500, date: '2026-05-18' };
  const bank = [{ date: '2026-05-18', description: 'ｼﾞﾖｳｶｿｳ', amount: -16500 }];
  const rules = [{ id: 'r1', kind: 'exclude', keyword: '浄化槽' }];
  const [r] = CB.classifyAll([e], bank, rules);
  assert.strictEqual(r.source, 'rule');
});

test('人が確定した判断は、あとから機械に覆されない', () => {
  const e = {
    description: '外注労務費', tone: 'blue', inflow: 0, outflow: 55000, date: '2026-05-20',
    decision: 'cash', confirmed: true, reason: '現金払いと確認済み'
  };
  const bank = [{ date: '2026-05-20', description: 'ｹﾞｼﾞﾕﾝﾌﾘｺﾐ', amount: -55000 }];
  const [r] = CB.classifyAll([e], bank, []);
  assert.strictEqual(r.decision, 'cash');
  assert.strictEqual(r.source, 'confirmed');
});

test('長いキーワードのルールが優先される', () => {
  const e = { description: '浄化槽点検 追加清掃', tone: 'black', inflow: 0, outflow: 8000, date: '2026-05-18' };
  const rules = [
    { id: 'a', kind: 'exclude', keyword: '浄化槽' },
    { id: 'b', kind: 'cash', keyword: '浄化槽点検 追加清掃' }
  ];
  const [r] = CB.classifyAll([e], [], rules);
  assert.strictEqual(r.ruleId, 'b');
  assert.strictEqual(r.decision, 'cash');
});

test('通帳の1明細を2行に重複して当てない', () => {
  const es = [
    { id: 'a', description: '支払A', tone: 'black', inflow: 0, outflow: 10000, date: '2026-05-10' },
    { id: 'b', description: '支払B', tone: 'black', inflow: 0, outflow: 10000, date: '2026-05-10' }
  ];
  const bank = [{ date: '2026-05-10', description: 'ｼﾊﾗｲ', amount: -10000 }];
  const r = CB.classifyAll(es, bank, []);
  assert.strictEqual(r.filter(x => x.source === 'bank').length, 1);
});

test('ATM引き出しを2件に分割する', () => {
  const atm = { id: 'atm', date: '2026-05-15', description: 'ATM引き出し', inflow: 0, outflow: 100000, tone: 'black' };
  const r = CB.splitEntry(atm, [
    { amount: 70000, description: '現金引き出し', account: '現金' },
    { amount: 30000, description: '◯◯商店へ現金返済', account: '借入金返済' }
  ]);
  assert.ok(r.ok, r.error);
  assert.strictEqual(r.entries.length, 2);
  assert.strictEqual(r.entries[0].outflow, 70000);
  assert.strictEqual(r.entries[1].description, '◯◯商店へ現金返済');
  assert.strictEqual(r.entries[1].splitOf, 'atm');
  assert.ok(r.entries.every(e => e.confirmed === false), '分割後は必ず確認に回す');
});

test('内訳の合計が元と合わない分割は拒否する', () => {
  const atm = { id: 'atm', date: '2026-05-15', description: 'ATM引き出し', inflow: 0, outflow: 100000 };
  const r = CB.splitEntry(atm, [{ amount: 70000 }, { amount: 25000 }]);
  assert.strictEqual(r.ok, false);
  assert.ok(r.error.includes('¥5,000'), '差額を具体的に示す: ' + r.error);
});

// ---- 5月分の実績値で検算する ------------------------------------------
// 期首 149,744 → 月末 156,756、現金純増減 +7,012

const MAY = [
  { id: '1', line: 1, date: '2026-05-02', description: '現金売上',          inflow: 85000,  outflow: 0,      tone: 'black' },
  { id: '2', line: 2, date: '2026-05-07', description: '売上入金 阿蘇観光',  inflow: 330000, outflow: 0,      tone: 'blue'  },
  { id: '3', line: 3, date: '2026-05-10', description: '消耗品購入',        inflow: 0,      outflow: 12340,  tone: 'black' },
  { id: '4', line: 4, date: '2026-05-12', description: '電気料金',          inflow: 0,      outflow: 42800,  tone: 'blue'  },
  { id: '5', line: 5, date: '2026-05-18', description: '浄化槽点検',        inflow: 0,      outflow: 16500,  tone: 'black' },
  { id: '6', line: 6, date: '2026-05-20', description: '外注労務費',        inflow: 0,      outflow: 55000,  tone: 'black' },
  { id: '7', line: 7, date: '2026-05-23', description: '現金返済',          inflow: 0,      outflow: 30000,  tone: 'red'   },
  { id: '8', line: 8, date: '2026-05-28', description: '家賃',              inflow: 0,      outflow: 180000, tone: 'blue'  },
  { id: '9', line: 9, date: '2026-05-30', description: '現金売上',          inflow: 19352,  outflow: 0,      tone: 'black' }
];

const MAY_BANK = [
  { date: '2026-05-07', description: 'ﾌﾘｺﾐ ｱｿｶﾝｺｳ(ｶ', amount: 330000 },
  { date: '2026-05-12', description: 'ﾃﾞﾝｷﾘｮｳｷﾝ',      amount: -42800 },
  { date: '2026-05-18', description: 'ｼﾞﾖｳｶｿｳﾃﾝｹﾝ',    amount: -16500 },
  { date: '2026-05-28', description: 'ﾔﾁﾝ',            amount: -180000 }
];

test('検算式：現金純増減 ＝ 資金表の増減 − 通帳の動き', () => {
  const classified = CB.classifyAll(MAY, MAY_BANK, []);
  const r = CB.reconcile({ entries: classified, bankTxs: MAY_BANK, targetNet: 7012 });

  assert.strictEqual(r.fundNet, 97712, '資金表の増減（現金＋預金の合算）');
  assert.strictEqual(r.bankNet, 90700, '通帳の動き');
  assert.strictEqual(r.expectedCashNet, 7012, '差し引いた現金純増減が目標値と一致する');
  assert.strictEqual(r.targetGap, 0);
});

test('仕分けが正しければ、現金合計と検算値が一致する', () => {
  const classified = CB.classifyAll(MAY, MAY_BANK, []).map(e => ({ ...e, confirmed: true }));
  const r = CB.reconcile({ entries: classified, bankTxs: MAY_BANK });
  assert.strictEqual(r.cashNet, 7012);
  assert.strictEqual(r.gap, 0);
  assert.ok(r.balanced);
});

test('仕分けに漏れがあれば差異として出る', () => {
  // 浄化槽点検を現金のまま残すと、通帳側と二重に引かれて差異が出る
  const broken = CB.classifyAll(MAY, [], []).map(e => ({ ...e, confirmed: true }));
  const r = CB.reconcile({ entries: broken, bankTxs: MAY_BANK });
  assert.notStrictEqual(r.gap, 0);
  assert.strictEqual(r.balanced, false);
});

test('現金出納帳は期首から残高を積み上げる', () => {
  const classified = CB.classifyAll(MAY, MAY_BANK, []).map(e => ({ ...e, confirmed: true }));
  const book = CB.buildCashbook(classified, 149744);
  assert.strictEqual(book.opening, 149744);
  assert.strictEqual(book.closing, 156756, '5月末残高が確定値と一致する');
  assert.deepStrictEqual(book.rows.map(r => r.description),
    ['現金売上', '消耗品購入', '外注労務費', '現金返済', '現金売上'],
    '銀行取引は出納帳に入らない');
  assert.strictEqual(book.rows[0].balance, 234744);
});

test('未確定の行は既定では出納帳に載らない', () => {
  const classified = CB.classifyAll(MAY, MAY_BANK, []);   // 確定処理をしていない
  assert.strictEqual(CB.buildCashbook(classified, 149744).rows.length, 0);
  assert.strictEqual(CB.buildCashbook(classified, 149744, { includeUnconfirmed: true }).rows.length, 5);
});

test('分割した親は集計に二重計上されない', () => {
  const atm = { id: 'atm', line: 10, date: '2026-05-15', description: 'ATM引き出し', inflow: 0, outflow: 100000, tone: 'black', decision: 'cash', confirmed: true };
  const parts = CB.splitEntry(atm, [
    { amount: 70000, description: '現金引き出し' },
    { amount: 30000, description: '現金返済' }
  ]).entries.map(e => ({ ...e, decision: 'cash', confirmed: true }));
  const book = CB.buildCashbook([atm].concat(parts), 0);
  assert.strictEqual(book.totalOut, 100000, '親と子で200,000にならないこと');
  assert.strictEqual(book.rows.length, 2);
});

test('出納帳のCSVは前月繰越と合計を含む', () => {
  const classified = CB.classifyAll(MAY, MAY_BANK, []).map(e => ({ ...e, confirmed: true }));
  const rows = CB.cashbookToRows(CB.buildCashbook(classified, 149744));
  assert.deepStrictEqual(rows[0], ['日付', '摘要', '科目', '入金', '出金', '残高']);
  assert.deepStrictEqual(rows[1], ['', '前月繰越', '', '', '', 149744]);
  assert.deepStrictEqual(rows[rows.length - 1], ['', '合計', '', 104352, 97340, 156756]);
});
