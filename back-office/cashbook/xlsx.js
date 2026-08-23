/*!
 * 最小限の .xlsx リーダー（外部ライブラリなし）
 *
 * なぜ自作するか：資金表の判定に使う「文字色」は、CSV に書き出すと失われる。
 * 色を読むには .xlsx（実体は ZIP + XML）を直接開くしかない。
 * 必要なのは「値」と「色」と「日付」だけなので、数式や書式の再現はしない。
 *
 * 展開には DecompressionStream('deflate-raw') を使う（Chrome / Safari 16.4+ / Node 20+）。
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.BOXlsx = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // ------------------------------------------------------------ ZIP

  function u16(b, o) { return b[o] | (b[o + 1] << 8); }
  function u32(b, o) { return (b[o] | (b[o + 1] << 8) | (b[o + 2] << 16) | (b[o + 3] << 24)) >>> 0; }

  // 末尾から End Of Central Directory を探す
  function findEOCD(bytes) {
    var max = Math.min(bytes.length, 66000);
    for (var i = bytes.length - 22; i >= bytes.length - max && i >= 0; i--) {
      if (u32(bytes, i) === 0x06054b50) return i;
    }
    return -1;
  }

  function inflateRaw(bytes) {
    var ds = new DecompressionStream('deflate-raw');
    var stream = new Blob([bytes]).stream().pipeThrough(ds);
    return new Response(stream).arrayBuffer().then(function (buf) {
      return new Uint8Array(buf);
    });
  }

  /**
   * ZIP を展開して { ファイル名: Uint8Array } を返す。
   * 格納方式は無圧縮(0)と deflate(8) のみ対応（xlsx はこの2つしか使わない）。
   */
  function unzip(arrayBuffer) {
    var bytes = new Uint8Array(arrayBuffer);
    var eocd = findEOCD(bytes);
    if (eocd < 0) throw new Error('ZIP形式として読めません（.xlsx ファイルか確認してください）');

    var count = u16(bytes, eocd + 10);
    var cdOffset = u32(bytes, eocd + 16);
    var files = {};
    var jobs = [];
    var p = cdOffset;

    for (var i = 0; i < count; i++) {
      if (u32(bytes, p) !== 0x02014b50) break;
      var method = u16(bytes, p + 10);
      var compSize = u32(bytes, p + 20);
      var nameLen = u16(bytes, p + 28);
      var extraLen = u16(bytes, p + 30);
      var commentLen = u16(bytes, p + 32);
      var localOffset = u32(bytes, p + 42);
      var name = new TextDecoder('utf-8').decode(bytes.subarray(p + 46, p + 46 + nameLen));

      // ローカルヘッダから実データの開始位置を求める
      var lhNameLen = u16(bytes, localOffset + 26);
      var lhExtraLen = u16(bytes, localOffset + 28);
      var dataStart = localOffset + 30 + lhNameLen + lhExtraLen;
      var data = bytes.subarray(dataStart, dataStart + compSize);

      if (method === 0) {
        files[name] = data;
      } else if (method === 8) {
        jobs.push((function (n, d) {
          return inflateRaw(d).then(function (out) { files[n] = out; });
        })(name, data));
      }
      p += 46 + nameLen + extraLen + commentLen;
    }

    return Promise.all(jobs).then(function () { return files; });
  }

  function text(files, name) {
    if (!files[name]) return null;
    return new TextDecoder('utf-8').decode(files[name]);
  }

  function parseXml(str) {
    if (!str) return null;
    var doc = new DOMParser().parseFromString(str, 'application/xml');
    if (doc.getElementsByTagName('parsererror').length) return null;
    return doc;
  }

  // ------------------------------------------------------------ 色

  // Excel の既定インデックスパレット（レガシー56色）
  var INDEXED = [
    '000000', 'FFFFFF', 'FF0000', '00FF00', '0000FF', 'FFFF00', 'FF00FF', '00FFFF',
    '000000', 'FFFFFF', 'FF0000', '00FF00', '0000FF', 'FFFF00', 'FF00FF', '00FFFF',
    '800000', '008000', '000080', '808000', '800080', '008080', 'C0C0C0', '808080',
    '9999FF', '993366', 'FFFFCC', 'CCFFFF', '660066', 'FF8080', '0066CC', 'CCCCFF',
    '000080', 'FF00FF', 'FFFF00', '00FFFF', '800080', '800000', '008080', '0000FF',
    '00CCFF', 'CCFFFF', 'CCFFCC', 'FFFF99', '99CCFF', 'FF99CC', 'CC99FF', 'FFCC99',
    '3366FF', '33CCCC', '99CC00', 'FFCC00', 'FF9900', 'FF6600', '666699', '969696',
    '003366', '339966', '003300', '333300', '993300', '993366', '333399', '333333'
  ];

  // theme の色番号 → clrScheme の並び。xlsx では 0/1 と 2/3 が入れ替わる。
  var THEME_ORDER = ['lt1', 'dk1', 'lt2', 'dk2', 'accent1', 'accent2', 'accent3',
                     'accent4', 'accent5', 'accent6', 'hlink', 'folHlink'];

  function applyTint(hex, tint) {
    if (!tint) return hex;
    var rgb = [parseInt(hex.substr(0, 2), 16), parseInt(hex.substr(2, 2), 16), parseInt(hex.substr(4, 2), 16)];
    var out = rgb.map(function (c) {
      var v = tint < 0 ? c * (1 + tint) : c * (1 - tint) + 255 * tint;
      return Math.max(0, Math.min(255, Math.round(v)));
    });
    return out.map(function (c) { return ('0' + c.toString(16)).slice(-2).toUpperCase(); }).join('');
  }

  function resolveColor(el, theme) {
    if (!el) return null;
    if (el.getAttribute('auto') === '1') return null;      // 自動＝既定色（黒扱い）
    var rgb = el.getAttribute('rgb');
    var tint = parseFloat(el.getAttribute('tint') || '0') || 0;
    if (rgb) {
      var hex = rgb.length === 8 ? rgb.slice(2) : rgb;      // 先頭2桁は不透明度
      return '#' + applyTint(hex.toUpperCase(), tint);
    }
    var idx = el.getAttribute('indexed');
    if (idx != null && INDEXED[+idx]) return '#' + applyTint(INDEXED[+idx], tint);
    var th = el.getAttribute('theme');
    if (th != null && theme) {
      var key = THEME_ORDER[+th];
      if (key && theme[key]) return '#' + applyTint(theme[key], tint);
    }
    return null;
  }

  function parseTheme(doc) {
    if (!doc) return null;
    var scheme = doc.getElementsByTagName('a:clrScheme')[0] || doc.getElementsByTagName('clrScheme')[0];
    if (!scheme) return null;
    var out = {};
    var names = ['dk1', 'lt1', 'dk2', 'lt2', 'accent1', 'accent2', 'accent3', 'accent4', 'accent5', 'accent6', 'hlink', 'folHlink'];
    names.forEach(function (n) {
      var el = scheme.getElementsByTagName('a:' + n)[0] || scheme.getElementsByTagName(n)[0];
      if (!el) return;
      var srgb = el.getElementsByTagName('a:srgbClr')[0] || el.getElementsByTagName('srgbClr')[0];
      var sys = el.getElementsByTagName('a:sysClr')[0] || el.getElementsByTagName('sysClr')[0];
      if (srgb) out[n] = (srgb.getAttribute('val') || '').toUpperCase();
      else if (sys) out[n] = (sys.getAttribute('lastClr') || '').toUpperCase();
    });
    return out;
  }

  /**
   * 色を「青／赤／黒／その他」に分類する。
   * 資金表の一次判定（青=銀行振込、黒・赤=現金）に使う。
   */
  function classifyColor(hex) {
    if (!hex) return 'black';                       // 色指定なし＝既定の黒
    var r = parseInt(hex.substr(1, 2), 16) / 255;
    var g = parseInt(hex.substr(3, 2), 16) / 255;
    var b = parseInt(hex.substr(5, 2), 16) / 255;
    var max = Math.max(r, g, b), min = Math.min(r, g, b);
    var l = (max + min) / 2;
    var d = max - min;
    if (d < 0.12) return l < 0.45 ? 'black' : 'other';   // 彩度がほぼ無い＝黒か灰
    var h;
    if (max === r) h = 60 * (((g - b) / d) % 6);
    else if (max === g) h = 60 * ((b - r) / d + 2);
    else h = 60 * ((r - g) / d + 4);
    if (h < 0) h += 360;
    if (h >= 190 && h <= 265) return 'blue';
    if (h >= 330 || h <= 20) return 'red';
    return 'other';
  }

  // ------------------------------------------------------------ 日付

  var DATE_FMT_IDS = [14, 15, 16, 17, 18, 19, 20, 21, 22, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36,
                      45, 46, 47, 50, 51, 52, 53, 54, 55, 56, 57, 58];

  function isDateFormat(id, code) {
    if (DATE_FMT_IDS.indexOf(id) >= 0) return true;
    if (!code) return false;
    var stripped = code.replace(/\[[^\]]*\]/g, '').replace(/"[^"]*"/g, '');
    return /[ymdhs]/i.test(stripped) && !/^[#0.,%\s]*$/.test(stripped);
  }

  function serialToYmd(serial, date1904) {
    var base = date1904 ? Date.UTC(1904, 0, 1) : Date.UTC(1899, 11, 30);
    var ms = base + Math.round(serial) * 86400000;
    var d = new Date(ms);
    function p(n) { return (n < 10 ? '0' : '') + n; }
    return d.getUTCFullYear() + '-' + p(d.getUTCMonth() + 1) + '-' + p(d.getUTCDate());
  }

  // ------------------------------------------------------------ 本体

  function colToIndex(ref) {
    var m = /^([A-Z]+)/.exec(ref || '');
    if (!m) return 0;
    var n = 0;
    for (var i = 0; i < m[1].length; i++) n = n * 26 + (m[1].charCodeAt(i) - 64);
    return n - 1;
  }

  function childText(parent, tag) {
    var el = parent.getElementsByTagName(tag)[0];
    return el ? el.textContent : null;
  }

  /**
   * .xlsx を読み、シートごとに二次元のセル配列を返す。
   * 各セル: { v: 値, t: 'n'|'s'|'d', color: '#RRGGBB'|null, tone: 'blue'|'red'|'black'|'other', fill: '#RRGGBB'|null }
   */
  function read(arrayBuffer) {
    return unzip(arrayBuffer).then(function (files) {
      var theme = parseTheme(parseXml(text(files, 'xl/theme/theme1.xml')));

      // 共有文字列
      var shared = [];
      var ssDoc = parseXml(text(files, 'xl/sharedStrings.xml'));
      if (ssDoc) {
        var sis = ssDoc.getElementsByTagName('si');
        for (var i = 0; i < sis.length; i++) {
          var ts = sis[i].getElementsByTagName('t');
          var s = '';
          for (var j = 0; j < ts.length; j++) s += ts[j].textContent;
          shared.push(s);
        }
      }

      // 書式（文字色・塗り・表示形式）
      var fonts = [], fills = [], xfs = [], numFmts = {};
      var stDoc = parseXml(text(files, 'xl/styles.xml'));
      if (stDoc) {
        var fmtEls = stDoc.getElementsByTagName('numFmt');
        for (var f = 0; f < fmtEls.length; f++) {
          numFmts[fmtEls[f].getAttribute('numFmtId')] = fmtEls[f].getAttribute('formatCode');
        }
        var fontsRoot = stDoc.getElementsByTagName('fonts')[0];
        if (fontsRoot) {
          var fontEls = fontsRoot.getElementsByTagName('font');
          for (var k = 0; k < fontEls.length; k++) {
            fonts.push(resolveColor(fontEls[k].getElementsByTagName('color')[0], theme));
          }
        }
        var fillsRoot = stDoc.getElementsByTagName('fills')[0];
        if (fillsRoot) {
          var fillEls = fillsRoot.getElementsByTagName('fill');
          for (var m = 0; m < fillEls.length; m++) {
            var pf = fillEls[m].getElementsByTagName('patternFill')[0];
            var none = !pf || pf.getAttribute('patternType') === 'none';
            fills.push(none ? null : resolveColor(pf.getElementsByTagName('fgColor')[0], theme));
          }
        }
        var cellXfs = stDoc.getElementsByTagName('cellXfs')[0];
        if (cellXfs) {
          var xfEls = cellXfs.getElementsByTagName('xf');
          for (var x = 0; x < xfEls.length; x++) {
            xfs.push({
              fontId: +(xfEls[x].getAttribute('fontId') || 0),
              fillId: +(xfEls[x].getAttribute('fillId') || 0),
              numFmtId: +(xfEls[x].getAttribute('numFmtId') || 0)
            });
          }
        }
      }

      // ブック（シート名と実体の対応）
      var wbDoc = parseXml(text(files, 'xl/workbook.xml'));
      var relDoc = parseXml(text(files, 'xl/_rels/workbook.xml.rels'));
      var date1904 = false;
      var rels = {};
      if (relDoc) {
        var rs = relDoc.getElementsByTagName('Relationship');
        for (var r = 0; r < rs.length; r++) {
          rels[rs[r].getAttribute('Id')] = rs[r].getAttribute('Target');
        }
      }
      var sheetDefs = [];
      if (wbDoc) {
        var pr = wbDoc.getElementsByTagName('workbookPr')[0];
        if (pr && (pr.getAttribute('date1904') === '1' || pr.getAttribute('date1904') === 'true')) date1904 = true;
        var shEls = wbDoc.getElementsByTagName('sheet');
        for (var s2 = 0; s2 < shEls.length; s2++) {
          var rid = shEls[s2].getAttribute('r:id') || shEls[s2].getAttribute('id');
          var target = rels[rid] || ('worksheets/sheet' + (s2 + 1) + '.xml');
          if (target.charAt(0) === '/') target = target.slice(1);
          else if (target.indexOf('xl/') !== 0) target = 'xl/' + target;
          sheetDefs.push({ name: shEls[s2].getAttribute('name') || ('シート' + (s2 + 1)), path: target });
        }
      }
      if (!sheetDefs.length) sheetDefs.push({ name: 'シート1', path: 'xl/worksheets/sheet1.xml' });

      var sheets = sheetDefs.map(function (def) {
        var doc = parseXml(text(files, def.path));
        var rows = [];
        if (!doc) return { name: def.name, rows: rows };
        var rowEls = doc.getElementsByTagName('row');
        for (var i2 = 0; i2 < rowEls.length; i2++) {
          var cells = [];
          var cEls = rowEls[i2].getElementsByTagName('c');
          for (var c2 = 0; c2 < cEls.length; c2++) {
            var cel = cEls[c2];
            var col = colToIndex(cel.getAttribute('r'));
            var t = cel.getAttribute('t');
            var sIdx = +(cel.getAttribute('s') || 0);
            var xf = xfs[sIdx] || { fontId: 0, fillId: 0, numFmtId: 0 };
            var raw = t === 'inlineStr' ? (childText(cel, 't') || '') : childText(cel, 'v');
            var value = null, kind = t || 'n';

            if (raw == null || raw === '') { value = null; }
            else if (t === 's') { value = shared[+raw] != null ? shared[+raw] : ''; kind = 's'; }
            else if (t === 'inlineStr' || t === 'str') { value = raw; kind = 's'; }
            else if (t === 'b') { value = raw === '1'; kind = 'b'; }
            else {
              var num = parseFloat(raw);
              if (isDateFormat(xf.numFmtId, numFmts[xf.numFmtId])) {
                value = serialToYmd(num, date1904); kind = 'd';
              } else { value = num; kind = 'n'; }
            }

            var color = fonts[xf.fontId] || null;
            cells[col] = {
              v: value, t: kind, raw: raw,
              color: color, tone: classifyColor(color),
              fill: fills[xf.fillId] || null
            };
          }
          for (var z = 0; z < cells.length; z++) if (!cells[z]) cells[z] = null;
          rows.push(cells);
        }
        return { name: def.name, rows: rows };
      });

      return { sheets: sheets, date1904: date1904 };
    });
  }

  return {
    read: read,
    unzip: unzip,
    classifyColor: classifyColor,
    serialToYmd: serialToYmd,
    isDateFormat: isDateFormat,
    resolveColorFor: resolveColor,
    supported: typeof DecompressionStream !== 'undefined'
  };
});
