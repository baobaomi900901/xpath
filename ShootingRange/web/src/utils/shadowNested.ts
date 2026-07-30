const LAYER_COUNT = 4;

function createLayerStyles(accent: string) {
  return `
    :host {
      display: block;
      width: 100%;
      min-height: 120px;
      font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
    }
    .layer {
      padding: 14px;
      border: 2px solid ${accent};
      border-radius: 8px;
      background: #fff;
      margin: 4px 0;
    }
    .badge {
      display: inline-block;
      margin-bottom: 8px;
      padding: 2px 8px;
      border-radius: 999px;
      background: ${accent}22;
      color: ${accent};
      font-size: 12px;
      font-weight: 600;
    }
    h3 { margin: 0 0 8px; font-size: 16px; color: #1f2937; }
    .marker { margin: 0 0 10px; color: #64748b; font-size: 13px; }
    label { display: block; margin-bottom: 10px; font-size: 14px; font-weight: 600; }
    input {
      display: block;
      margin-top: 6px;
      width: 100%;
      max-width: 260px;
      padding: 8px 10px;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      font-size: 14px;
    }
    button {
      padding: 8px 14px;
      border: none;
      border-radius: 8px;
      background: ${accent};
      color: #fff;
      font-size: 14px;
      cursor: pointer;
    }
    .child-host { margin-top: 12px; }
    .result {
      margin-top: 10px;
      padding: 8px 10px;
      background: #f8fafc;
      border-radius: 8px;
      font-size: 13px;
      color: #475569;
    }
  `;
}

function defineNestedShadowStack(prefix: string, mode: 'open' | 'closed', accent: string) {
  for (let level = LAYER_COUNT; level >= 1; level -= 1) {
    const tagName = `${prefix}-l${level}`;
    if (customElements.get(tagName)) continue;

    const childTag = level < LAYER_COUNT ? `${prefix}-l${level + 1}` : null;
    const isInnermost = level === LAYER_COUNT;
    const modeLabel = mode === 'open' ? 'Open' : 'Closed';

    customElements.define(
      tagName,
      class extends HTMLElement {
        constructor() {
          super();
          const shadow = this.attachShadow({ mode });
          shadow.innerHTML = `
            <style>${createLayerStyles(accent)}</style>
            <div class="layer" id="${prefix}-layer-${level}-panel">
              <div class="badge">${modeLabel} · Layer ${level}</div>
              <h3 id="${prefix}-layer-${level}-title">${modeLabel} Shadow 第 ${level} 层</h3>
              <p class="marker" id="${prefix}-layer-${level}-marker">marker-${prefix}-l${level}</p>
              <label for="${prefix}-layer-${level}-input">第 ${level} 层输入框</label>
              <input id="${prefix}-layer-${level}-input" type="text" placeholder="在第 ${level} 层输入" />
              <div style="margin-top:10px">
                <button id="${prefix}-layer-${level}-btn" type="button">第 ${level} 层按钮</button>
              </div>
              ${isInnermost ? `<p class="result" id="${prefix}-layer-${level}-result">等待操作…</p>` : '<div class="child-host"></div>'}
            </div>
          `;

          if (childTag) {
            shadow.querySelector('.child-host')?.appendChild(document.createElement(childTag));
          }

          if (isInnermost) {
            shadow.getElementById(`${prefix}-layer-${level}-btn`)?.addEventListener('click', () => {
              const input = shadow.getElementById(`${prefix}-layer-${level}-input`) as HTMLInputElement | null;
              const result = shadow.getElementById(`${prefix}-layer-${level}-result`);
              if (result) {
                result.textContent = input?.value ? `已输入：${input.value}` : '请先输入内容';
              }
            });
          }
        }
      },
    );
  }
}

let registered = false;

export function ensureShadowNestedElements() {
  if (registered) return;
  defineNestedShadowStack('open-nested', 'open', '#2563eb');
  defineNestedShadowStack('closed-nested', 'closed', '#7c3aed');
  registered = true;
}

export function mountShadowRoot(host: HTMLElement, tagName: string, elementId: string) {
  host.innerHTML = '';
  const element = document.createElement(tagName);
  element.id = elementId;
  host.appendChild(element);
  return element;
}

export function isShadowMounted(elementId: string) {
  const element = document.getElementById(elementId);
  return !!element && element.clientHeight > 0;
}
