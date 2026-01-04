(function () {
  function findElementByXPath(xpath, contextNode) {
    try {
      const result = document.evaluate(xpath, contextNode || document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
      return result.singleNodeValue;
    } catch (error) {
      console.error('[iframe.js] XPath 查询失败:', error);
      return null;
    }
  }

  /**
   * 简化版：只验证元素是否存在（XPath 已包含文本条件）
   * @param {string} iframeXPath - iframe 的 XPath
   * @param {string} elementXPath - 要验证元素的 XPath
   * @returns {Promise<boolean>} 验证结果
   */
  window.validateElementInIframe = function (iframeXPath, elementXPath) {
    return new Promise((resolve) => {
      console.log('[iframe.js] 开始验证...');

      const iframe = findElementByXPath(iframeXPath, document);

      if (!iframe || !(iframe instanceof HTMLIFrameElement)) {
        console.error(`[iframe.js] 未找到 iframe: ${iframeXPath}`);
        resolve(false);
        return;
      }

      console.log(`[iframe.js] 找到 iframe`);

      let attemptCount = 0;
      const maxAttempts = 30;
      const attemptInterval = 200;

      function checkIframeContent() {
        attemptCount++;

        if (attemptCount > maxAttempts) {
          console.error(`[iframe.js] 已达到最大尝试次数，验证失败`);
          resolve(false);
          return;
        }

        console.log(`[iframe.js] 尝试检查 (${attemptCount}/${maxAttempts})`);

        try {
          const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document;

          if (!iframeDoc || iframeDoc.readyState !== 'complete') {
            setTimeout(checkIframeContent, attemptInterval);
            return;
          }

          // 直接使用 XPath 查找，如果找到了就说明元素存在且满足 XPath 的所有条件（包括文本条件）
          const targetElement = findElementByXPath(elementXPath, iframeDoc);

          if (targetElement) {
            console.log('[iframe.js] 验证成功！找到匹配的元素');
            console.log('[iframe.js] 元素文本:', targetElement.textContent.trim());
            resolve(true);
          } else {
            setTimeout(checkIframeContent, attemptInterval);
          }
        } catch (error) {
          console.error(`[iframe.js] 检查出错: ${error.message}`);
          setTimeout(checkIframeContent, attemptInterval);
        }
      }

      if (iframe.contentDocument && iframe.contentDocument.readyState === 'complete') {
        setTimeout(checkIframeContent, 300);
      } else {
        const onLoad = () => {
          iframe.removeEventListener('load', onLoad);
          setTimeout(() => {
            checkIframeContent();
          }, 500);
        };

        iframe.addEventListener('load', onLoad);

        setTimeout(() => {
          iframe.removeEventListener('load', onLoad);
          checkIframeContent();
        }, 10000);
      }
    });
  };

  console.log('[iframe.js] 加载完成 - 简化版');
})();
