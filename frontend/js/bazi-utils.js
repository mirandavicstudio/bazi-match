/**
 * 八字匹配工具函数（纯函数，可独立测试）
 * ====================================
 * 从 app.js 提取的纯函数，不依赖 Vue
 */

/**
 * 获取维度图标
 */
export function getDimIcon(name) {
  const map = {
    '地支合冲': '⚡',
    '五行互补': '🌿',
    '天干合': '☯️',
    '日主关系': '💑',
    '纳音配对': '🎵',
    '生肖配对': '🐉',
  };
  return map[name] || '📌';
}

/**
 * 获取维度描述
 */
export function getDimDesc(name) {
  const map = {
    '地支合冲': '地支六合、三合、冲克关系',
    '五行互补': '双方五行旺衰互补程度',
    '天干合': '天干五合、相生关系',
    '日主关系': '日干生克制化与十神关系',
    '纳音配对': '六十甲子纳音五行配对',
    '生肖配对': '十二生肖三合六合配对',
  };
  return map[name] || '';
}

/**
 * 获取评分徽章样式
 */
export function getScoreBadgeClass(score) {
  if (score >= 80) return 'bg-gradient-to-br from-emerald-400 to-emerald-600 text-white';
  if (score >= 60) return 'bg-gradient-to-br from-amber-400 to-orange-500 text-white';
  if (score >= 40) return 'bg-gradient-to-br from-orange-400 to-red-500 text-white';
  return 'bg-gradient-to-br from-gray-400 to-gray-500 text-white';
}

/**
 * 获取命中项标签样式
 */
export function getHitTagClass(hit) {
  // 先检查合冲克（优先级高于五行）
  if (hit.includes('合') || hit.includes('三合')) return 'bg-indigo-50 text-indigo-700 border-indigo-200';
  if (hit.includes('冲') || hit.includes('克')) return 'bg-rose-50 text-rose-700 border-rose-200';
  // 再检查五行
  if (hit.includes('金')) return 'bg-amber-50 text-amber-700 border-amber-200';
  if (hit.includes('木')) return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  if (hit.includes('水')) return 'bg-sky-50 text-sky-700 border-sky-200';
  if (hit.includes('火')) return 'bg-red-50 text-red-700 border-red-200';
  if (hit.includes('土')) return 'bg-yellow-50 text-yellow-700 border-yellow-200';
  return 'bg-gray-50 text-gray-700 border-gray-200';
}

/**
 * 获取命中项前缀
 */
export function getHitPrefix(hit) {
  if (hit.includes('合') || hit.includes('三合')) return '✓';
  if (hit.includes('冲') || hit.includes('克')) return '⚠';
  return '•';
}

/**
 * 获取五行对应 emoji
 */
export function getWuxingEmoji(wx) {
  const map = {
    '金': '🥇',
    '木': '🌳',
    '水': '💧',
    '火': '🔥',
    '土': '⛰️',
  };
  return map[wx] || '⚪';
}

/**
 * 获取评分颜色类
 */
export function scoreColor(score) {
  if (score >= 85) return 'text-rose-500';
  if (score >= 70) return 'text-orange-500';
  if (score >= 55) return 'text-yellow-600';
  if (score >= 40) return 'text-blue-500';
  return 'text-gray-500';
}

/**
 * 获取评分颜色类（兼容旧方法名）
 */
export function getScoreColor(score) {
  return scoreColor(score);
}

/**
 * 获取维度条颜色类
 */
export function getDimBarClass(score) {
  if (score >= 70) return 'bg-gradient-to-t from-green-400 to-green-600';
  if (score >= 40) return 'bg-gradient-to-t from-yellow-400 to-yellow-600';
  return 'bg-gradient-to-t from-red-400 to-red-600';
}

/**
 * 获取维度条颜色类（兼容旧方法名）
 */
export function dimBarColorClass(score) {
  return getDimBarClass(score);
}

/**
 * 获取某年某月的最大天数
 * @param {number} year - 年份
 * @param {number} month - 月份 (1-12)
 * @returns {number} 该月天数
 */
export function getMaxDay(year, month) {
  if ([1, 3, 5, 7, 8, 10, 12].includes(month)) return 31;
  if ([4, 6, 9, 11].includes(month)) return 30;
  // 闰年判断
  if (year % 400 === 0) return 29;
  if (year % 100 === 0) return 28;
  if (year % 4 === 0) return 29;
  return 28;
}
