import './style.css';
import {
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  HistogramSeries,
  LineSeries,
  createChart,
  type CandlestickData,
  type HistogramData,
  type IChartApi,
  type ISeriesApi,
  type LineData,
  type Time,
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
  volume?: number | null;

  session_date?: string | null;
  minute_from_open?: number | null;
  bar_index_in_session?: number | null;

  prev_day_high?: number | null;
  prev_day_low?: number | null;
  prev_day_close?: number | null;

  or30_high?: number | null;
  or30_low?: number | null;
  or30_complete?: boolean | number | null;

  or60_high?: number | null;
  or60_low?: number | null;
  or60_complete?: boolean | number | null;

  vwap?: number | null;
  dist_to_vwap_pts?: number | null;

  session_range_so_far_pts?: number | null;
  close_location_in_session_range?: number | null;

  atr14_pts?: number | null;
  relative_volume_20?: number | null;
};

type FeatureBarsResponse = {
  meta: {
    timeframe: Timeframe;
    rows: number;
    features_available: boolean;
    feature_columns: string[];
    source_path: string;
  };
  bars: ApiBar[];
};

type OverlayKey =
  | 'volume'
  | 'vwap'
  | 'prevDay'
  | 'or30'
  | 'or60';

const API_BASE = 'http://127.0.0.1:8000';
const EXCHANGE_TIMEZONE = 'America/New_York';

const etAxisFormatter = new Intl.DateTimeFormat('en-US', {
  timeZone: EXCHANGE_TIMEZONE,
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
});

const etFullFormatter = new Intl.DateTimeFormat('en-CA', {
  timeZone: EXCHANGE_TIMEZONE,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false,
});

function chartTimeToUnixSeconds(time: Time): number | null {
  if (typeof time === 'number') {
    return time;
  }

  if (typeof time === 'string') {
    const parsed = Date.parse(`${time}T00:00:00Z`);
    return Number.isFinite(parsed) ? Math.floor(parsed / 1000) : null;
  }

  const parsed = Date.UTC(time.year, time.month - 1, time.day);
  return Number.isFinite(parsed) ? Math.floor(parsed / 1000) : null;
}

function formatExchangeAxisTime(time: Time): string {
  const unixSeconds = chartTimeToUnixSeconds(time);
  if (unixSeconds === null) {
    return String(time);
  }

  return etAxisFormatter
    .format(new Date(unixSeconds * 1000))
    .replace(',', '');
}

function formatExchangeFullTime(time: Time): string {
  const unixSeconds = chartTimeToUnixSeconds(time);
  if (unixSeconds === null) {
    return String(time);
  }

  return `${etFullFormatter.format(new Date(unixSeconds * 1000))} ET`;
}

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

    <div class="overlaybar">
      <label class="check"><input id="overlay-volume" type="checkbox" checked /> Volume</label>
      <label class="check"><input id="overlay-vwap" type="checkbox" checked /> VWAP</label>
      <label class="check"><input id="overlay-prevday" type="checkbox" checked /> Prev day H/L/C</label>
      <label class="check"><input id="overlay-or30" type="checkbox" checked /> OR30</label>
      <label class="check"><input id="overlay-or60" type="checkbox" /> OR60</label>
    </div>

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

const overlayInputs: Record<OverlayKey, HTMLInputElement> = {
  volume: document.querySelector<HTMLInputElement>('#overlay-volume')!,
  vwap: document.querySelector<HTMLInputElement>('#overlay-vwap')!,
  prevDay: document.querySelector<HTMLInputElement>('#overlay-prevday')!,
  or30: document.querySelector<HTMLInputElement>('#overlay-or30')!,
  or60: document.querySelector<HTMLInputElement>('#overlay-or60')!,
};

let latestBars: ApiBar[] = [];
let latestMeta: FeatureBarsResponse['meta'] | null = null;

const chart: IChartApi = createChart(chartEl, {
  autoSize: true,
  localization: {
    timeFormatter: formatExchangeFullTime,
  },
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
    scaleMargins: {
      top: 0.08,
      bottom: 0.24,
    },
  },
  timeScale: {
    borderColor: '#304050',
    timeVisible: true,
    secondsVisible: false,
    tickMarkFormatter: formatExchangeAxisTime,
  },
});

const candleSeries: ISeriesApi<'Candlestick'> = chart.addSeries(CandlestickSeries, {
  upColor: '#22c55e',
  downColor: '#ef4444',
  borderVisible: false,
  wickUpColor: '#22c55e',
  wickDownColor: '#ef4444',
});

const volumeSeries: ISeriesApi<'Histogram'> = chart.addSeries(HistogramSeries, {
  priceFormat: {
    type: 'volume',
  },
  priceScaleId: 'volume',
});

chart.priceScale('volume').applyOptions({
  scaleMargins: {
    top: 0.82,
    bottom: 0,
  },
});

const lineSeries = {
  vwap: chart.addSeries(LineSeries, {
    color: '#facc15',
    lineWidth: 2,
    title: 'VWAP',
  }),
  prevDayHigh: chart.addSeries(LineSeries, {
    color: '#60a5fa',
    lineWidth: 1,
    lineStyle: 2,
    title: 'PDH',
  }),
  prevDayLow: chart.addSeries(LineSeries, {
    color: '#60a5fa',
    lineWidth: 1,
    lineStyle: 2,
    title: 'PDL',
  }),
  prevDayClose: chart.addSeries(LineSeries, {
    color: '#93c5fd',
    lineWidth: 1,
    lineStyle: 1,
    title: 'PDC',
  }),
  or30High: chart.addSeries(LineSeries, {
    color: '#fb923c',
    lineWidth: 1,
    title: 'OR30 High',
  }),
  or30Low: chart.addSeries(LineSeries, {
    color: '#fb923c',
    lineWidth: 1,
    title: 'OR30 Low',
  }),
  or60High: chart.addSeries(LineSeries, {
    color: '#c084fc',
    lineWidth: 1,
    title: 'OR60 High',
  }),
  or60Low: chart.addSeries(LineSeries, {
    color: '#c084fc',
    lineWidth: 1,
    title: 'OR60 Low',
  }),
};

function setStatus(message: string): void {
  statusEl.textContent = message;
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function fmt(value: unknown, digits = 2): string {
  if (value === null || value === undefined || value === '') {
    return 'n/a';
  }

  if (typeof value === 'number') {
    if (!Number.isFinite(value)) {
      return 'n/a';
    }
    return value.toFixed(digits);
  }

  return String(value);
}

function boolLabel(value: unknown): string {
  if (value === true || value === 1) {
    return 'yes';
  }
  if (value === false || value === 0) {
    return 'no';
  }
  return 'n/a';
}

function formatBar(bar: ApiBar): string {
  return [
    `time ET: ${bar.timestamp_et}`,
    `session: ${fmt(bar.session_date, 0)}`,
    `minute from open: ${fmt(bar.minute_from_open, 0)}`,
    '',
    `open:    ${fmt(bar.open)}`,
    `high:    ${fmt(bar.high)}`,
    `low:     ${fmt(bar.low)}`,
    `close:   ${fmt(bar.close)}`,
    `volume:  ${fmt(bar.volume, 0)}`,
    '',
    `VWAP:       ${fmt(bar.vwap)}`,
    `dist VWAP:  ${fmt(bar.dist_to_vwap_pts)}`,
    `ATR14:      ${fmt(bar.atr14_pts)}`,
    `rel vol20:  ${fmt(bar.relative_volume_20)}`,
    '',
    `PDH: ${fmt(bar.prev_day_high)}`,
    `PDL: ${fmt(bar.prev_day_low)}`,
    `PDC: ${fmt(bar.prev_day_close)}`,
    '',
    `OR30 high: ${fmt(bar.or30_high)}`,
    `OR30 low:  ${fmt(bar.or30_low)}`,
    `OR30 done: ${boolLabel(bar.or30_complete)}`,
    '',
    `OR60 high: ${fmt(bar.or60_high)}`,
    `OR60 low:  ${fmt(bar.or60_low)}`,
    `OR60 done: ${boolLabel(bar.or60_complete)}`,
    '',
    `session range so far: ${fmt(bar.session_range_so_far_pts)}`,
    `close location:       ${fmt(bar.close_location_in_session_range)}`,
  ].join('\n');
}

function dedupeSorted<T extends { time: UTCTimestamp }>(rows: T[]): T[] {
  const byTime = new Map<number, T>();

  for (const row of rows) {
    byTime.set(Number(row.time), row);
  }

  return [...byTime.values()].sort((a, b) => Number(a.time) - Number(b.time));
}

function toCandleData(bars: ApiBar[]): CandlestickData[] {
  const rows: CandlestickData[] = [];

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

    rows.push({
      time: time as UTCTimestamp,
      open,
      high,
      low,
      close,
    });
  }

  return dedupeSorted(rows);
}

function toVolumeData(bars: ApiBar[]): HistogramData[] {
  const rows: HistogramData[] = [];

  for (const bar of bars) {
    const time = Number(bar.time);
    const volume = Number(bar.volume);

    if (!Number.isFinite(time) || !Number.isFinite(volume)) {
      continue;
    }

    rows.push({
      time: time as UTCTimestamp,
      value: volume,
      color: Number(bar.close) >= Number(bar.open)
        ? 'rgba(34, 197, 94, 0.35)'
        : 'rgba(239, 68, 68, 0.35)',
    });
  }

  return dedupeSorted(rows);
}

function toLineData(bars: ApiBar[], key: keyof ApiBar): LineData[] {
  const rows: LineData[] = [];

  for (const bar of bars) {
    const time = Number(bar.time);
    const rawValue = bar[key];

    if (!Number.isFinite(time) || !isFiniteNumber(rawValue)) {
      continue;
    }

    rows.push({
      time: time as UTCTimestamp,
      value: rawValue,
    });
  }

  return dedupeSorted(rows);
}

function updateOverlayData(): void {
  volumeSeries.setData(overlayInputs.volume.checked ? toVolumeData(latestBars) : []);

  lineSeries.vwap.setData(
    overlayInputs.vwap.checked ? toLineData(latestBars, 'vwap') : [],
  );

  lineSeries.prevDayHigh.setData(
    overlayInputs.prevDay.checked ? toLineData(latestBars, 'prev_day_high') : [],
  );
  lineSeries.prevDayLow.setData(
    overlayInputs.prevDay.checked ? toLineData(latestBars, 'prev_day_low') : [],
  );
  lineSeries.prevDayClose.setData(
    overlayInputs.prevDay.checked ? toLineData(latestBars, 'prev_day_close') : [],
  );

  lineSeries.or30High.setData(
    overlayInputs.or30.checked ? toLineData(latestBars, 'or30_high') : [],
  );
  lineSeries.or30Low.setData(
    overlayInputs.or30.checked ? toLineData(latestBars, 'or30_low') : [],
  );

  lineSeries.or60High.setData(
    overlayInputs.or60.checked ? toLineData(latestBars, 'or60_high') : [],
  );
  lineSeries.or60Low.setData(
    overlayInputs.or60.checked ? toLineData(latestBars, 'or60_low') : [],
  );
}

async function loadBars(): Promise<void> {
  const timeframe = timeframeEl.value as Timeframe;
  const limit = Number(limitEl.value || 5000);

  setStatus(`Loading ${timeframe} bars...`);

  const url = `${API_BASE}/api/feature-bars?timeframe=${encodeURIComponent(timeframe)}&limit=${limit}`;
  const res = await fetch(url);

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API error ${res.status}: ${detail}`);
  }

  const payload = (await res.json()) as FeatureBarsResponse;
  latestMeta = payload.meta;
  latestBars = payload.bars;

  const candleData = toCandleData(latestBars);
  candleSeries.setData(candleData);
  updateOverlayData();
  chart.timeScale().fitContent();

  const first = latestBars[0]?.timestamp_et ?? 'n/a';
  const last = latestBars.at(-1)?.timestamp_et ?? 'n/a';

  setStatus(
    [
      `Loaded ${latestBars.length} bars`,
      `timeframe: ${latestMeta.timeframe}`,
      `features: ${latestMeta.features_available ? 'yes' : 'no'}`,
      `feature columns: ${latestMeta.feature_columns.length}`,
      `first: ${first}`,
      `last:  ${last}`,
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

for (const input of Object.values(overlayInputs)) {
  input.addEventListener('change', updateOverlayData);
}

loadBars().catch((err) => {
  console.error(err);
  setStatus(String(err));
});
