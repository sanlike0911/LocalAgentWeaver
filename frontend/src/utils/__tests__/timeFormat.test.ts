import { formatResponseTime } from '../timeFormat';

describe('formatResponseTime', () => {
  test('1秒未満の場合、小数点で表示される', () => {
    expect(formatResponseTime(500)).toBe('（応答時間：0.5秒）');
    expect(formatResponseTime(123)).toBe('（応答時間：0.1秒）');
    expect(formatResponseTime(999)).toBe('（応答時間：1.0秒）');
  });

  test('1分未満の場合、秒のみで表示される', () => {
    expect(formatResponseTime(1000)).toBe('（応答時間：1秒）');
    expect(formatResponseTime(5500)).toBe('（応答時間：5秒）');
    expect(formatResponseTime(59999)).toBe('（応答時間：59秒）');
  });

  test('1時間未満の場合、分秒で表示される', () => {
    expect(formatResponseTime(60000)).toBe('（応答時間：1分0秒）');
    expect(formatResponseTime(65000)).toBe('（応答時間：1分5秒）');
    expect(formatResponseTime(125000)).toBe('（応答時間：2分5秒）');
    expect(formatResponseTime(3599000)).toBe('（応答時間：59分59秒）');
  });

  test('1時間以上の場合、時分秒で表示される', () => {
    expect(formatResponseTime(3600000)).toBe('（応答時間：1時間0分0秒）');
    expect(formatResponseTime(3665000)).toBe('（応答時間：1時間1分5秒）');
    expect(formatResponseTime(7325000)).toBe('（応答時間：2時間2分5秒）');
  });

  test('境界値のテスト', () => {
    expect(formatResponseTime(999.9)).toBe('（応答時間：1.0秒）');
    expect(formatResponseTime(1000)).toBe('（応答時間：1秒）');
    expect(formatResponseTime(59999)).toBe('（応答時間：59秒）');
    expect(formatResponseTime(60000)).toBe('（応答時間：1分0秒）');
    expect(formatResponseTime(3599999)).toBe('（応答時間：59分59秒）');
    expect(formatResponseTime(3600000)).toBe('（応答時間：1時間0分0秒）');
  });

  test('0の場合の処理', () => {
    expect(formatResponseTime(0)).toBe('（応答時間：0.0秒）');
  });
});