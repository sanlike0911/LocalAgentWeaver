/**
 * 経過時間を「TIME（応答時間：X秒）」形式でフォーマットする
 * @param durationMs ミリ秒単位の経過時間
 * @returns フォーマットされた時間文字列
 */
export function formatResponseTime(durationMs: number): string {
  const seconds = durationMs / 1000;

  // 1秒未満は小数点表示
  if (seconds < 1) {
    return `TIME（応答時間：${seconds.toFixed(1)}秒）`;
  }
  
  // 1分未満は秒のみ
  if (seconds < 60) {
    return `TIME（応答時間：${Math.floor(seconds)}秒）`;
  }
  
  // 1時間未満は分秒
  if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `TIME（応答時間：${minutes}分${remainingSeconds}秒）`;
  }
  
  // 1時間以上は時分秒
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `TIME（応答時間：${hours}時間${minutes}分${remainingSeconds}秒）`;
}