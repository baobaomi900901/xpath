function VerifyXpath(xpath) {
  const el = document.evaluate(xpath, document, null, XPathResult.ANY_TYPE, null);
  const result = [];
  let item = el.iterateNext();
  while (item) {
    result.push(item);
    item = el.iterateNext();
  }
  return result;
}

// 在浏览器中直接挂载到 window 对象
if (typeof window !== 'undefined') {
  window.VerifyXpath = VerifyXpath;
}
