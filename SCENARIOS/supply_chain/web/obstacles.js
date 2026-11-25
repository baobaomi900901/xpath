'use strict';
globalThis.InventoryObstacles = Object.freeze({
  bind(root, enabled) {
    // References belong to the application closure, never stable DOM selector aliases.
    const elements = new Map([...root.querySelectorAll('[id]')].map(element => [element.id, element]));
    if (enabled) {
      const identifiers = new Map();
      for (const [previous, element] of elements) {
        const next = 'sc-' + crypto.randomUUID();
        identifiers.set(previous, next);
        element.id = next;
      }
      const references = ['for', 'list', 'headers', 'aria-labelledby', 'aria-describedby', 'aria-controls',
        'aria-owns', 'aria-activedescendant', 'aria-details', 'aria-errormessage'];
      for (const element of root.querySelectorAll('[for],[list],[headers],[aria-labelledby],[aria-describedby],[aria-controls],[aria-owns],[aria-activedescendant],[aria-details],[aria-errormessage],[href]')) {
        for (const attribute of references) {
          if (!element.hasAttribute(attribute)) continue;
          const tokens = element.getAttribute(attribute).trim().split(/\s+/);
          element.setAttribute(attribute, tokens.map(token => identifiers.get(token) || token).join(' '));
        }
        const href = element.getAttribute('href');
        if (href && href.startsWith('#') && identifiers.has(href.slice(1))) {
          element.setAttribute('href', '#' + identifiers.get(href.slice(1)));
        }
      }
    }
    return logicalId => elements.get(logicalId);
  }
});
