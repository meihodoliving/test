(function () {
  var langs = [
    { code: 'ja', label: '日本語', short: 'JP' },
    { code: 'en', label: 'English', short: 'EN' },
    { code: 'zh-cn', label: '简体中文', short: '简' },
    { code: 'zh-tw', label: '繁體中文', short: '繁' }
  ];

  var path = window.location.pathname;
  var match = path.match(/^\/(ja|en|zh-cn|zh-tw|zh-hans|zh-hant)(\/|$)/);
  var currentCode = match ? match[1] : 'ja';

  // Normalise zh-hans → zh-cn, zh-hant → zh-tw for display purposes
  if (currentCode === 'zh-hans') currentCode = 'zh-cn';
  if (currentCode === 'zh-hant') currentCode = 'zh-tw';

  var current = langs.find(function (l) { return l.code === currentCode; }) || langs[0];

  // Set the visible label
  var labelEl = document.getElementById('lang-current');
  if (labelEl) labelEl.textContent = current.short;

  // Build dropdown links
  var dropdown = document.getElementById('lang-dropdown');
  if (dropdown) {
    dropdown.innerHTML = '';
    langs.forEach(function (lang) {
      if (lang.code === currentCode) return;

      var targetPath;
      if (match) {
        targetPath = path.replace('/' + match[1], '/' + lang.code);
      } else {
        // Root /index.html is treated as ja
        targetPath = '/' + lang.code + '/';
      }

      var li = document.createElement('li');
      li.setAttribute('role', 'none');
      var a = document.createElement('a');
      a.href = targetPath;
      a.textContent = lang.label;
      a.className = 'lang-option';
      a.setAttribute('role', 'menuitem');
      li.appendChild(a);
      dropdown.appendChild(li);
    });
  }

  // Toggle open/close
  var btn = document.getElementById('lang-btn');
  var dd = document.getElementById('lang-dropdown');

  if (!btn || !dd) return;

  btn.addEventListener('click', function (e) {
    e.stopPropagation();
    var isOpen = dd.classList.toggle('open');
    btn.setAttribute('aria-expanded', String(isOpen));
  });

  document.addEventListener('click', function () {
    dd.classList.remove('open');
    btn.setAttribute('aria-expanded', 'false');
  });

  dd.addEventListener('click', function (e) {
    e.stopPropagation();
  });

  // Keyboard: Escape closes
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      dd.classList.remove('open');
      btn.setAttribute('aria-expanded', 'false');
      btn.focus();
    }
  });
})();
