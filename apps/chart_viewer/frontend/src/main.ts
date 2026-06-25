import './style.css';
import {
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  createChart,
  type CandlestickData,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from 'lightweight-charts';

type Timeframe = '1m' | '5m' | '30m' | '1h';

type ApiBar = {
  time: number;
  timestamp_et: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
};

const API_BASE = 'http://127.0.0.1:8000';

document.querySelector<HTMLDivElement>('#app')!.innerHTML = `
  <div class="shell">
    <header class="topbar">
      <div>
        <div class="eyebrow">SPY Research</div>
        <h1>Local Chart Viewer</h1>
      </div>

      <div class="controls">
        <label>
          Timeframe
          <select id="timeframe">
            <option value="1m">1m</option>
            <option value="5m" selected>5m</option>
            <option value="30m">30m</option>
            <option value="1h">1h</option>
          </select>
        </label>

        <label>
          Bars
          <input id="limit" type="number" min="100" max="100000" step="100" value="5000" />
        </label>

        <button id="reload">Reload</button>
      </div>
    </header>

    <main class="main">
      <section class="chart-panel">
        <div id="chart"></div>
      </section>

      <aside class="info-panel">
        <h2>Selected bar</h2>
        <pre id="bar-info">Move crosshair over a candle.</pre>

        <h2>Status</h2>
        <pre id="status">Starting...</pre>
      </aside>
    </main>
  </div>
`;

const chartEl = document.querySelector<HTMLDivElement>('#chart')!;
const timeframeEl = document.querySelector<HTMLSelectElement>('#timeframe')!;
const limitEl = document.querySelector<HTMLInputElement>('#limit')!;
const reloadEl = document.querySelector<HTMLButtonElement>('#reload')!;
const statusEl = document.querySelector<HTMLPreElement>('#status')!;
const barInfoEl = document.querySelector<HTMLPreElement>('#bar-info')!;

let latestBars: ApiBar[] = [];

const chart: IChartApi = createChart(chartEl, {
  autoSize: true,
  layout: {
    background: { type: ColorType.Solid, color: '#070b10' },
    textColor: '#d6dde8',
  },
  grid: {
    vertLines: { color: '#16202d' },
    horzLines: { color: '#16202d' },
  },
  crosshair: {
    mode: CrosshairMode.Normal,
  },
  rightPriceScale: {
    borderColor: '#304050',
  },
  timeScale: {
    borderColor: '#304050',
    timeVisible: true,
    secondsVisible: false,
  },
});

const candleSeries: ISeriesApi<'Candlestick'> = chart.addSeries(CandlestickSeries, {
  upColor: '#22c55e',
  downColor: '#ef4444',
  borderVisible: false,
  wickUpColor: '#22c55e',
  wickDownColor: '#ef4444',
});

function setStatus(message: string): void {
  statusEl.textContent = message;
}

function formatBar(bar: ApiBar): string {
  return [
    `time ET: ${bar.timestamp_et}`,
    `open:    ${bar.open}`,
    `high:    ${bar.high}`,
    `low:     ${bar.low}`,
    `close:   ${bar.close}`,
    `volume:  ${bar.volume ?? 'n/a'}`,
  ].join('\n');
}

function toCandleData(bars: ApiBar[]): CandlestickData[] {
  const byTime = new Map<number, CandlestickData>();

  for (const bar of bars) {
    const time = Number(bar.time);
    const open = Number(bar.open);
    const high = Number(bar.high);
    const low = Number(bar.low);
    const close = Number(bar.close);

    if (
      !Number.isFinite(time) ||
      !Number.isFinite(open) ||
      !Number.isFinite(high) ||
      !Number.isFinite(low) ||
      !Number.isFinite(close)
    ) {
      continue;
    }

    // If duplicate chart times exist, keep the later bar.
    byTime.set(time, {
      time: time as UTCTimestamp,
      open,
      high,
      low,
      close,
    });
  }

  return [...byTime.values()].sort((a, b) => Number(a.time) - Number(b.time));
}

async function loadBars(): Promise<void> {
  const timeframe = timeframeEl.value as Timeframe;
  const limit = Number(limitEl.value || 5000);

  setStatus(`Loading ${timeframe} bars...`);

  const url = `${API_BASE}/api/bars?timeframe=${encodeURIComponent(timeframe)}&limit=${limit}`;
  const res = await fetch(url);

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API error ${res.status}: ${detail}`);
  }

  latestBars = (await res.json()) as ApiBar[];

  const candleData = toCandleData(latestBars);
  candleSeries.setData(candleData);
  chart.timeScale().fitContent();

  setStatus(
    [
      `Loaded ${latestBars.length} bars`,
      `timeframe: ${timeframe}`,
      `first: ${latestBars[0]?.timestamp_et ?? 'n/a'}`,
      `last:  ${latestBars.at(-1)?.timestamp_et ?? 'n/a'}`,
    ].join('\n'),
  );
}

chart.subscribeCrosshairMove((param) => {
  if (!param.time) {
    barInfoEl.textContent = 'Move crosshair over a candle.';
    return;
  }

  const unixTime = Number(param.time);
  const bar = latestBars.find((item) => item.time === unixTime);

  if (!bar) {
    barInfoEl.textContent = `time: ${String(param.time)}`;
    return;
  }

  barInfoEl.textContent = formatBar(bar);
});

reloadEl.addEventListener('click', () => {
  loadBars().catch((err) => {
    console.error(err);
    setStatus(String(err));
  });
});

timeframeEl.addEventListener('change', () => {
  loadBars().catch((err) => {
    console.error(err);
    setStatus(String(err));
  });
});

loadBars().catch((err) => {
  console.error(err);
  setStatus(String(err));
});