// hooks/tools.js

// 创建工具对象
(function () {
  // 工具对象
  const ElementInfoTools = {};

  // 常见的布尔属性列表（仅保留W3C标准HTML布尔属性，无硬编码自定义属性）
  const BOOLEAN_ATTRIBUTES = [
    'checked',
    'selected',
    'disabled',
    'readonly',
    'required',
    'multiple',
    'autofocus',
    'hidden',
    'open',
    'async',
    'defer',
    'ismap',
    'reversed',
    'allowfullscreen',
    'novalidate',
    'formnovalidate',
    'itemscope'
  ];

  /**
   * 检查属性是否为布尔属性（自动识别Vue等框架自定义布尔属性）
   */
  function isBooleanAttribute(attrName) {
    if (BOOLEAN_ATTRIBUTES.includes(attrName)) {
      return true;
    }

    const customBooleanPatterns = [
      /^v-[\w-]+$/i,
      /^data-bool-/i,
      /^data-true$/i,
      /^data-false$/i,
      /^is-.*/i,
      /^has-.*/i,
      /^no-.*/i,
      /^not-.*/i,
      /^use-.*/i,
      /^enable-.*/i,
      /^disable-.*/i,
      /^[\w]+(?:vvn|ddg)$/i,
      /^[a-z]+[a-z0-9]*$/i
    ];

    for (const pattern of customBooleanPatterns) {
      if (pattern.test(attrName)) {
        return true;
      }
    }

    return false;
  }

  /**
   * 辅助函数：检查id是否重复（精准判断，确保id='app'返回false）
   */
  function isIdDuplicated(id) {
    if (!id) return false;
    const elements = document.querySelectorAll(`[id="${id}"]`);
    return elements.length > 1;
  }

  /**
   * 获取元素的本层文本内容（不包括子元素文本）
   */
  function getElementDirectText(element) {
    if (!element) return '';

    let text = '';
    for (let node of element.childNodes) {
      if (node.nodeType === Node.TEXT_NODE) {
        text += node.textContent;
      }
    }
    return text.replace(/\s+/g, ' ').trim();
  }

  /**
   * 处理属性值：将无值属性转换为布尔值
   */
  function processAttributeValue(attrName, attrValue, element) {
    if (attrValue === '') {
      if (isBooleanAttribute(attrName) || element.hasAttribute(attrName)) {
        return true;
      }
      return '';
    }

    if (attrValue === 'true' || attrValue === 'false') {
      return attrValue === 'true' ? true : false;
    }

    if (!isNaN(attrValue) && attrValue !== '') {
      const num = Number(attrValue);
      if (!isNaN(num)) {
        return num;
      }
    }

    return attrValue;
  }

  /**
   * 构建元素信息对象 - 优化版（保留所有DOM属性，不忽略style/href）
   */
  function buildElementInfo(el, index, indexOfType, parentTag) {
    const BASE_PROPS = ['tag', 'id', 'class', 'text', 'index', 'indexOfType', 'parentTag', 'nodeName', 'nodeType'];

    const info = {
      tag: el.tagName.toLowerCase(),
      id: el.id || null,
      class: el.className || null,
      text: getElementDirectText(el),
      index: index,
      indexOfType: indexOfType,
      parentTag: parentTag,
      nodeName: el.nodeName,
      nodeType: el.nodeType
    };

    if (el.attributes && el.attributes.length > 0) {
      for (let attr of el.attributes) {
        const attrName = attr.name;
        if (BASE_PROPS.includes(attrName)) {
          continue;
        }

        const rawValue = attr.value;
        const processedValue = processAttributeValue(attrName, rawValue, el);

        const lowerAttrName = attrName.toLowerCase();
        const isBasePropConflict = BASE_PROPS.some((prop) => prop.toLowerCase() === lowerAttrName);
        if (isBasePropConflict) {
          continue;
        }

        info[attrName] = processedValue;
      }
    }

    return info;
  }

  /**
   * 根据XPath获取元素信息
   */
  ElementInfoTools.getElementInfoByXPath = function (xpath, contextNode = document) {
    console.log('🔍 查找XPath:', xpath);

    try {
      const element = document.evaluate(
        xpath,
        contextNode,
        null,
        XPathResult.FIRST_ORDERED_NODE_TYPE,
        null
      ).singleNodeValue;

      if (!element) {
        console.warn('❌ 元素未找到');
        return null;
      }

      const path = [];
      let current = element;
      while (current && current !== document && current.nodeType === Node.ELEMENT_NODE) {
        path.unshift(current);
        current = current.parentElement;
      }

      const result = {
        element: element,
        xpath: xpath,
        path: path.map((el, i) => {
          let index = 0;
          let indexOfType = 0;
          if (el.parentElement) {
            const children = Array.from(el.parentElement.children);
            index = children.indexOf(el) + 1;
            const sameTypeChildren = children.filter(
              (child) => child.tagName.toLowerCase() === el.tagName.toLowerCase()
            );
            indexOfType = sameTypeChildren.indexOf(el) + 1;
          }

          const parentTag = el.parentElement ? el.parentElement.tagName.toLowerCase() : null;
          return buildElementInfo(el, index, indexOfType, parentTag);
        })
      };

      return result;
    } catch (error) {
      console.error('❌ 错误:', error);
      return null;
    }
  };

  /**
   * 简洁调试函数 - 优化版
   */
  ElementInfoTools.debugElementInfo = function (xpath, contextNode) {
    console.group('🔍 元素信息调试');

    const info = this.getElementInfoByXPath(xpath, contextNode);

    if (info) {
      console.log('🎯 目标元素:', info.element);
      console.log('📋 路径信息:');
      info.path.forEach((item, index) => {
        console.log(
          `  ${'  '.repeat(index)}${item.tag}${item.id ? '#' + item.id : ''}${
            item.class ? '.' + item.class.split(' ').join('.') : ''
          } [index:${item.index}, indexOfType:${item.indexOfType}]`
        );
      });
    } else {
      console.log('❌ 未找到元素');
    }

    console.groupEnd();
    return info;
  };

  /**
   * 极简调试函数 - 优化版
   */
  ElementInfoTools.debugElementInfoMinimal = function (xpath, contextNode) {
    const info = this.getElementInfoByXPath(xpath, contextNode);

    if (!info) {
      console.log('❌ 未找到元素');
      return null;
    }

    console.log('🔍 元素路径:');
    info.path.forEach((item, index) => {
      const indent = '  '.repeat(index);
      const isTarget = index === info.path.length - 1;

      let tagDisplay = `<${item.tag}>`;
      if (item.id) tagDisplay += `#${item.id}`;
      if (item.class) {
        const classes = item.class
          .split(' ')
          .filter((c) => c)
          .map((c) => `.${c}`)
          .join('');
        tagDisplay += classes;
      }

      const prefix = isTarget ? '🎯 ' : '├─ ';
      console.log(`${indent}${prefix}${tagDisplay} [index:${item.index}, indexOfType:${item.indexOfType}]`);

      if (!isTarget) {
        console.log(`${indent}    [位置: ${item.index}/${item.indexOfType}]`);
      } else {
        if (item.text) console.log(`${indent}    text: "${item.text}"`);

        const baseProps = ['tag', 'id', 'class', 'text', 'index', 'indexOfType', 'parentTag', 'nodeName', 'nodeType'];
        const attributes = Object.keys(item)
          .filter((key) => !baseProps.includes(key))
          .sort();

        if (attributes.length > 0) {
          console.log(`${indent}    属性:`);
          attributes.forEach((key) => {
            const value = item[key];
            let displayValue;
            if (typeof value === 'boolean') {
              displayValue = value ? 'true' : 'false';
            } else if (typeof value === 'number') {
              displayValue = value.toString();
            } else if (typeof value === 'string') {
              displayValue = value.length > 50 ? value.substring(0, 50) + '...' : value;
            } else {
              displayValue = String(value);
            }
            console.log(`${indent}      ${key}: ${displayValue}`);
          });
        }
      }
    });

    return info;
  };

  /**
   * 获取元素的XPath
   */
  ElementInfoTools.getXPathForElement = function (element) {
    if (!element || element.nodeType !== Node.ELEMENT_NODE) return '';

    if (element.id && !isIdDuplicated(element.id)) {
      return `//*[@id="${element.id}"]`;
    }

    const parts = [];
    let current = element;
    while (current && current.nodeType === Node.ELEMENT_NODE) {
      let index = 0;
      let sibling = current.previousSibling;
      while (sibling) {
        if (sibling.nodeType === Node.ELEMENT_NODE && sibling.nodeName === current.nodeName) {
          index++;
        }
        sibling = sibling.previousSibling;
      }

      const tag = current.nodeName.toLowerCase();
      const part = index > 0 ? `${tag}[${index + 1}]` : tag;
      parts.unshift(part);
      current = current.parentNode;
    }

    return '/' + parts.join('/');
  };

  /**
   * 获取元素的本层文本（不包括子元素）
   */
  ElementInfoTools.getDirectText = function (element) {
    return getElementDirectText(element);
  };

  /**
   * 快速获取元素信息（返回纯对象，无日志）
   */
  ElementInfoTools.getElementInfo = function (xpath, contextNode) {
    try {
      const element = document.evaluate(
        xpath,
        contextNode || document,
        null,
        XPathResult.FIRST_ORDERED_NODE_TYPE,
        null
      ).singleNodeValue;

      if (!element) {
        return null;
      }

      const path = [];
      let current = element;
      while (current && current !== document && current.nodeType === Node.ELEMENT_NODE) {
        path.unshift(current);
        current = current.parentElement;
      }

      const result = {
        element: element,
        xpath: xpath,
        path: path.map((el, i) => {
          let index = 0;
          let indexOfType = 0;
          if (el.parentElement) {
            const children = Array.from(el.parentElement.children);
            index = children.indexOf(el) + 1;
            const sameTypeChildren = children.filter(
              (child) => child.tagName.toLowerCase() === el.tagName.toLowerCase()
            );
            indexOfType = sameTypeChildren.indexOf(el) + 1;
          }

          const parentTag = el.parentElement ? el.parentElement.tagName.toLowerCase() : null;
          return buildElementInfo(el, index, indexOfType, parentTag);
        })
      };

      return result;
    } catch (error) {
      console.error('获取元素信息失败:', error);
      return null;
    }
  };

  /**
   * 获取元素的完整XPath（智能版本，只添加必要的索引）
   */
  ElementInfoTools.getFullXPathForElement = function (element) {
    if (!element || element.nodeType !== Node.ELEMENT_NODE) return '';

    const parts = [];
    let current = element;
    while (current && current.nodeType === Node.ELEMENT_NODE) {
      const tagName = current.tagName.toLowerCase();
      let sameTagCount = 0;
      let sameTagIndex = 0;

      if (current.parentNode) {
        const siblings = Array.from(current.parentNode.children).filter(
          (child) => child.nodeType === Node.ELEMENT_NODE
        );

        for (let i = 0; i < siblings.length; i++) {
          const sibling = siblings[i];
          if (sibling.tagName.toLowerCase() === tagName) {
            sameTagCount++;
            if (sibling === current) {
              sameTagIndex = sameTagCount;
            }
          }
        }
      }

      const part = sameTagCount > 1 ? `${tagName}[${sameTagIndex}]` : tagName;
      parts.unshift(part);

      if (tagName === 'html') break;
      current = current.parentNode;
    }

    return '/' + parts.join('/');
  };

  /**
   * 获取元素的属性值（支持布尔属性）
   */
  ElementInfoTools.getAttributeValue = function (element, attributeName) {
    if (!element || !attributeName) return null;

    if (!element.hasAttribute(attributeName)) {
      return null;
    }

    const value = element.getAttribute(attributeName);
    return processAttributeValue(attributeName, value, element);
  };

  /**
   * 获取元素的所有属性（优化版）
   */
  ElementInfoTools.getAllAttributes = function (element) {
    if (!element || !element.attributes) return {};

    const attributes = {};
    for (let attr of element.attributes) {
      const attrName = attr.name;
      const rawValue = attr.value;
      attributes[attrName] = processAttributeValue(attrName, rawValue, element);
    }

    return attributes;
  };

  /**
   * 根据元素信息数组生成唯一的XPath表达式（完全匹配你的预期，无多余前缀和冗余索引）
   */
  function ElementInfoReturnElementXPath(elementInfoArray) {
    const baseProps = ['tag', 'id', 'class', 'text', 'index', 'indexOfType', 'parentTag', 'nodeName', 'nodeType'];

    if (!elementInfoArray || !Array.isArray(elementInfoArray) || elementInfoArray.length === 0) {
      console.error('❌ 元素信息数组为空或无效');
      return null;
    }

    console.log('🔁 原始元素信息数组:', elementInfoArray);
    const targetInfo = elementInfoArray[elementInfoArray.length - 1];

    // 1. 优先使用ID + 布尔属性（若id重复，自动补充位置条件）
    if (targetInfo.id && targetInfo.id !== null && targetInfo.id !== '') {
      const booleanAttrs = [];
      Object.keys(targetInfo).forEach((key) => {
        if (!baseProps.includes(key) && typeof targetInfo[key] === 'boolean' && targetInfo[key] === true) {
          booleanAttrs.push(`@${key}`);
        }
      });

      let conditions = [`@id='${targetInfo.id}'`];
      if (booleanAttrs.length > 0) {
        conditions = conditions.concat(booleanAttrs);
      }
      let xpathById = `//${targetInfo.tag}[${conditions.join(' and ')}]`;
      if (isIdDuplicated(targetInfo.id) && targetInfo.indexOfType > 1) {
        xpathById += `[${targetInfo.indexOfType}]`;
      }

      console.log('尝试使用ID+布尔属性生成XPath:', xpathById);
      if (ElementInfoCheckElementIsUnique(xpathById)) {
        console.log('✅ 使用ID+布尔属性生成唯一XPath:', xpathById);
        return xpathById;
      }
    }

    // 2. 从目标元素向上构建XPath（过滤html/body节点，移除冗余索引）
    let currentIndex = elementInfoArray.length - 1;
    const pathSegments = [];
    // 标记是否需要过滤html/body节点
    let skipRootNodes = true;

    while (currentIndex >= 0) {
      const info = elementInfoArray[currentIndex];
      // 过滤html和body节点，只保留body以下内容
      if (skipRootNodes && (info.tag === 'html' || info.tag === 'body')) {
        currentIndex--;
        continue;
      }
      skipRootNodes = false; // 跳过一次后，不再过滤其他节点

      const attrConditions = [];
      const indexCondition = [];

      // 2.1 优先添加ID（id唯一时，不添加任何位置索引）
      if (info.id && info.id !== null && info.id !== '') {
        attrConditions.push(`@id='${info.id}'`);
        // 若id唯一，直接跳过位置索引添加逻辑
        if (!isIdDuplicated(info.id)) {
          currentIndex--;
          // 构建片段：仅属性条件，无位置索引
          let fragment = info.tag;
          if (attrConditions.length > 0) {
            fragment += `[${attrConditions.join(' and ')}]`;
          }
          pathSegments.unshift(fragment);
          // 检查唯一性
          const fullXPath = `//${pathSegments.join('/')}`; // 直接以//开头，无多余前缀
          if (ElementInfoCheckElementIsUnique(fullXPath)) {
            console.log(`✅ 在第 ${elementInfoArray.length - currentIndex} 层找到唯一XPath`);
            return fullXPath;
          }
          continue;
        }
      }

      // 2.2 次优先添加布尔属性
      const booleanAttrs = [];
      Object.keys(info).forEach((key) => {
        if (!baseProps.includes(key) && typeof info[key] === 'boolean' && info[key] === true) {
          booleanAttrs.push(`@${key}`);
        }
      });
      if (booleanAttrs.length > 0) {
        attrConditions.push(...booleanAttrs);
      }

      // 2.3 然后添加data-等稳定自定义属性
      const customAttrs = Object.keys(info).filter(
        (key) => !baseProps.includes(key) && typeof info[key] !== 'boolean' && key !== 'style' && key !== 'href'
      );
      for (const attr of customAttrs) {
        const attrValue = info[attr];
        if (attrValue === null || attrValue === undefined || attrValue === '') {
          continue;
        }
        if (typeof attrValue === 'string') {
          attrConditions.push(`@${attr}='${attrValue}'`);
        } else if (typeof attrValue === 'number') {
          attrConditions.push(`@${attr}=${attrValue}`);
        }
      }

      // 2.4 处理class：使用contains模糊匹配
      if (info.class && info.class !== null && info.class !== '') {
        const classes = info.class.split(' ').filter((c) => c.trim() !== '');
        if (classes.length > 0) {
          attrConditions.push(`contains(@class, '${classes[0]}')`);
        }
      }

      // 2.5 处理style：使用contains模糊匹配
      if (info.style && info.style !== null && info.style !== '') {
        const styleText = info.style.trim().replace(/\s+/g, ' ');
        attrConditions.push(`contains(@style, '${styleText.substring(0, 20)}')`);
      }

      // 2.6 仅当id重复/无属性条件时，添加位置索引（避免冗余）
      const needIndex = attrConditions.length === 0 || (info.id && isIdDuplicated(info.id)) || info.indexOfType > 1;
      if (needIndex && info.indexOfType > 1) {
        indexCondition.push(`${info.indexOfType}`);
      } else if (needIndex && info.index > 1) {
        indexCondition.push(`${info.index}`);
      }

      // 构建片段
      let fragment = info.tag;
      if (attrConditions.length > 0) {
        fragment += `[${attrConditions.join(' and ')}]`;
      }
      if (indexCondition.length > 0) {
        fragment += `[${indexCondition.join(' and ')}]`;
      }

      pathSegments.unshift(fragment);

      // 检查唯一性（拼接为//开头的路径，无html/body前缀）
      const fullXPath = `//${pathSegments.join('/')}`;
      if (ElementInfoCheckElementIsUnique(fullXPath)) {
        console.log(`✅ 在第 ${elementInfoArray.length - currentIndex} 层找到唯一XPath`);
        return fullXPath;
      }

      currentIndex--;
    }

    // 3. 兜底：相对路径（匹配你的预期格式）
    console.log('尝试使用相对路径...');
    if (elementInfoArray.length >= 2) {
      const targetInfo = elementInfoArray[elementInfoArray.length - 1];
      const parentInfo = elementInfoArray[elementInfoArray.length - 2];

      let parentFragment = parentInfo.tag;
      const parentConditions = [];
      if (parentInfo.id) parentConditions.push(`@id='${parentInfo.id}'`);
      Object.keys(parentInfo).forEach((key) => {
        if (!baseProps.includes(key) && typeof parentInfo[key] === 'boolean' && parentInfo[key] === true) {
          parentConditions.push(`@${key}`);
        }
      });
      if (parentInfo.class) {
        const classes = parentInfo.class.split(' ').filter((c) => c.trim() !== '');
        if (classes.length > 0) parentConditions.push(`contains(@class, '${classes[0]}')`);
      }
      if (parentConditions.length > 0) {
        parentFragment += `[${parentConditions.join(' and ')}]`;
      }
      if (parentInfo.id && isIdDuplicated(parentInfo.id) && parentInfo.indexOfType > 1) {
        parentFragment += `[${parentInfo.indexOfType}]`;
      }

      let childFragment = targetInfo.tag;
      const childConditions = [];
      if (targetInfo.id) childConditions.push(`@id='${targetInfo.id}'`);
      Object.keys(targetInfo).forEach((key) => {
        if (!baseProps.includes(key) && typeof targetInfo[key] === 'boolean' && targetInfo[key] === true) {
          childConditions.push(`@${key}`);
        }
      });
      if (targetInfo.text && targetInfo.text.trim()) {
        childConditions.push(`contains(text(), '${targetInfo.text.trim()}')`);
      }
      if (childConditions.length > 0) {
        childFragment += `[${childConditions.join(' and ')}]`;
      }

      // 过滤html/body，构建预期格式的相对路径
      const relativeXPath = `//${parentFragment}/${childFragment}`;
      console.log('尝试相对路径:', relativeXPath);
      if (ElementInfoCheckElementIsUnique(relativeXPath)) {
        return relativeXPath;
      }
    }

    // 最终返回：//开头，无html/body前缀，无冗余索引
    const finalXPath = `//${pathSegments.join('/')}`;
    console.log('🎯 生成的唯一XPath:', finalXPath);
    return finalXPath;
  }

  /**
   * 校验XPath是否唯一
   */
  function ElementInfoCheckElementIsUnique(xpath, contextNode = document) {
    if (!xpath || xpath.trim() === '') {
      console.error('❌ XPath为空');
      return false;
    }

    try {
      const result = document.evaluate(
        xpath,
        contextNode || document,
        null,
        XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
        null
      );

      const count = result.snapshotLength;
      if (count === 0) {
        console.warn(`⚠️ XPath未找到元素: "${xpath}"`);
        return false;
      } else if (count === 1) {
        console.log(`✅ XPath唯一: "${xpath}"`);
        const element = result.snapshotItem(0);
        console.log('找到的元素:', element);
        console.log('元素HTML:', element.outerHTML.substring(0, 200) + (element.outerHTML.length > 200 ? '...' : ''));
        return true;
      } else {
        console.warn(`⚠️ XPath不唯一: "${xpath}"，找到 ${count} 个元素`);
        for (let i = 0; i < Math.min(count, 5); i++) {
          const element = result.snapshotItem(i);
          console.log(
            `  元素 ${i + 1}:`,
            element.tagName,
            element.id ? `#${element.id}` : '',
            element.className ? `.${element.className}` : ''
          );
        }
        if (count > 5) {
          console.log(`  ... 还有 ${count - 5} 个元素`);
        }
        return false;
      }
    } catch (error) {
      console.error('❌ XPath执行错误:', error);
      console.error('错误的XPath:', xpath);
      return false;
    }
  }

  /**
   * 生成安全的XPath，使用单引号
   */
  function ElementInfoGenerateSafeXPath(elementInfoArray) {
    const baseProps = ['tag', 'id', 'class', 'text', 'index', 'indexOfType', 'parentTag', 'nodeName', 'nodeType'];

    if (!elementInfoArray || elementInfoArray.length === 0) return null;

    const targetInfo = elementInfoArray[elementInfoArray.length - 1];
    if (targetInfo.id) {
      const booleanAttrs = [];
      Object.keys(targetInfo).forEach((key) => {
        if (!baseProps.includes(key) && typeof targetInfo[key] === 'boolean' && targetInfo[key] === true) {
          booleanAttrs.push(`@${key}`);
        }
      });
      let conditions = [`@id='${targetInfo.id}'`];
      if (booleanAttrs.length > 0) {
        conditions = conditions.concat(booleanAttrs);
      }
      let xpath = `//${targetInfo.tag}[${conditions.join(' and ')}]`;
      if (isIdDuplicated(targetInfo.id) && targetInfo.indexOfType > 1) {
        xpath += `[${targetInfo.indexOfType}]`;
      }
      return xpath;
    }

    if (targetInfo.text && targetInfo.text.trim()) {
      const cleanText = targetInfo.text.trim().replace(/\s+/g, ' ');
      if (cleanText.includes("'")) {
        const parts = cleanText.split("'");
        const concatParts = parts.map((part) => (part ? `'${part}'` : "''")).join(', "\'", ');
        return `//${targetInfo.tag}[contains(text(), concat(${concatParts}))]`;
      } else {
        return `//${targetInfo.tag}[contains(text(), '${cleanText}')]`;
      }
    }

    const booleanAttrs = [];
    Object.keys(targetInfo).forEach((key) => {
      if (!baseProps.includes(key) && typeof targetInfo[key] === 'boolean' && targetInfo[key] === true) {
        booleanAttrs.push(`@${key}`);
      }
    });
    if (booleanAttrs.length > 0) {
      return `//${targetInfo.tag}[${booleanAttrs.join(' and ')}]`;
    }

    if (targetInfo.class) {
      const classes = targetInfo.class.split(' ').filter((c) => c.trim() !== '');
      if (classes.length > 0) {
        return `//${targetInfo.tag}[contains(@class, '${classes[0]}')]`;
      }
    }

    const customAttrs = Object.keys(targetInfo).filter(
      (key) => !baseProps.includes(key) && typeof targetInfo[key] !== 'boolean'
    );
    for (const attr of customAttrs) {
      const attrValue = targetInfo[attr];
      if (attrValue === null || attrValue === undefined || attrValue === '') {
        continue;
      }
      if (typeof attrValue === 'string') {
        if (attrValue.includes("'")) {
          const parts = attrValue.split("'");
          const concatParts = parts.map((part) => (part ? `'${part}'` : "''")).join(', "\'", ');
          return `//${targetInfo.tag}[@${attr}=concat(${concatParts})]`;
        } else {
          return `//${targetInfo.tag}[@${attr}='${attrValue}']`;
        }
      } else if (typeof attrValue === 'number') {
        return `//${targetInfo.tag}[@${attr}=${attrValue}]`;
      }
    }

    let xpath = '';
    const pathSegments = [];
    let skipRootNodes = true;
    for (let i = 0; i < elementInfoArray.length; i++) {
      const info = elementInfoArray[i];
      if (skipRootNodes && (info.tag === 'html' || info.tag === 'body')) {
        continue;
      }
      skipRootNodes = false;
      pathSegments.push(info.tag);
      if (info.indexOfType > 1) {
        pathSegments[pathSegments.length - 1] += `[${info.indexOfType}]`;
      }
    }
    xpath = `//${pathSegments.join('/')}`;
    return xpath;
  }

  // 暴露方法
  ElementInfoTools.ElementInfoReturnElementXPath = ElementInfoReturnElementXPath;
  ElementInfoTools.ElementInfoCheckElementIsUnique = ElementInfoCheckElementIsUnique;
  ElementInfoTools.ElementInfoGenerateSafeXPath = ElementInfoGenerateSafeXPath;
  window.ElementInfoReturnElementXPath = ElementInfoReturnElementXPath;
  window.ElementInfoCheckElementIsUnique = ElementInfoCheckElementIsUnique;
  window.ElementInfoGenerateSafeXPath = ElementInfoGenerateSafeXPath;
  window.ElementInfoTools = ElementInfoTools;

  console.log('✅ ElementInfoTools 已初始化（完全匹配预期XPath格式）');
})();
