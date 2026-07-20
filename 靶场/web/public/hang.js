(function () {
  var DEFAULT_HANG_MS = 30000;
  var hangMs = parseInt(new URLSearchParams(location.search).get('delay'), 10);
  if (isNaN(hangMs) || hangMs < 0) {
    hangMs = DEFAULT_HANG_MS;
  }

  var elapsedEl = document.getElementById('elapsed');
  var elapsedTextEl = document.getElementById('elapsed-text');
  var start = Date.now();
  var lastSecond = -1;

  function tick() {
    var elapsed = Math.floor((Date.now() - start) / 1000);
    if (elapsed !== lastSecond) {
      lastSecond = elapsed;
      if (elapsedEl) elapsedEl.textContent = String(elapsed);
      if (elapsedTextEl) elapsedTextEl.textContent = String(elapsed);
      document.title = '页面加载中…（' + elapsed + ' 秒）';
    }
  }

  while (Date.now() - start < hangMs) {
    tick();
  }

  while (true) {
    tick();
  }
})();
