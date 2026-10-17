import { useEffect, useRef } from 'react';
import PageLayout from '../components/PageLayout';

const CHART_DATA = [
  { label: '数据一', value: 120, color: '#1677ff' },
  { label: '数据二', value: 200, color: '#52c41a' },
  { label: '数据三', value: 150, color: '#faad14' },
];
const CHART_DESCRIPTION = CHART_DATA.map(({ label, value }) => `${label}：${value}`).join('，');

export default function CanvasTestPage() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const draw = () => {
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      if (!width || !height) return;

      const pixelRatio = window.devicePixelRatio || 1;
      canvas.width = Math.round(width * pixelRatio);
      canvas.height = Math.round(height * pixelRatio);

      const context = canvas.getContext('2d');
      if (!context) return;
      context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
      context.fillStyle = '#fff';
      context.fillRect(0, 0, width, height);

      const left = 48;
      const top = 32;
      const plotWidth = width - left - 24;
      const plotHeight = height - top - 44;
      const baseline = top + plotHeight;
      const maxValue = 250;

      context.font = '13px system-ui, sans-serif';
      context.lineWidth = 1;
      context.textAlign = 'right';
      context.textBaseline = 'middle';

      for (let value = 0; value <= maxValue; value += 50) {
        const y = baseline - (value / maxValue) * plotHeight;
        context.strokeStyle = '#f0f0f0';
        context.beginPath();
        context.moveTo(left, y);
        context.lineTo(left + plotWidth, y);
        context.stroke();
        context.fillStyle = '#595959';
        context.fillText(String(value), left - 10, y);
      }

      context.strokeStyle = '#8c8c8c';
      context.beginPath();
      context.moveTo(left, top);
      context.lineTo(left, baseline);
      context.lineTo(left + plotWidth, baseline);
      context.stroke();
      context.fillText('数值', left - 10, 14);

      const columnWidth = plotWidth / CHART_DATA.length;
      const barWidth = Math.min(88, columnWidth * 0.5);
      context.textAlign = 'center';

      CHART_DATA.forEach(({ label, value, color }, index) => {
        const centerX = left + columnWidth * (index + 0.5);
        const barHeight = (value / maxValue) * plotHeight;
        const barTop = baseline - barHeight;

        context.fillStyle = color;
        context.fillRect(centerX - barWidth / 2, barTop, barWidth, barHeight);
        context.fillStyle = '#262626';
        context.fillText(String(value), centerX, barTop - 14);
        context.fillText(label, centerX, baseline + 24);
      });
    };

    draw();
    const observer = new ResizeObserver(draw);
    observer.observe(canvas);
    window.addEventListener('resize', draw);
    return () => {
      observer.disconnect();
      window.removeEventListener('resize', draw);
    };
  }, []);

  return (
    <PageLayout title="Canvas 柱状图" subtitle="使用原生 Canvas 绘制 3 个数据列，展示名称、数值与坐标刻度。">
      <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, overflow: 'hidden' }}>
        <canvas
          id="canvas-bar-chart"
          ref={canvasRef}
          role="img"
          aria-label={`柱状图，${CHART_DESCRIPTION}`}
          style={{ display: 'block', width: '100%', height: 360 }}
        >
          {CHART_DESCRIPTION}
        </canvas>
      </div>
    </PageLayout>
  );
}
