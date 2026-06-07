/**
 * 八字合盘匹配系统 - Vue 3 应用
 * ====================================
 * 功能：用户输入出生信息，从万人库中寻找八字最合的人
 * 作者：UI Designer 优化版本
 * 日期：2026-06-06
 */

const { createApp, ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } = Vue;

// ====== 应用主逻辑 ======
const app = createApp({
  setup() {
    // ====== 状态管理 ======
    const state = ref('input');           // 'input' | 'loading' | 'result'
    const progress = ref(0);             // 加载进度 0-100
    const matchedCount = ref(0);         // 已匹配人数
    const showDetail = ref(false);        // 是否显示详情弹窗
    const detailData = ref({});          // 当前查看的详情数据
    const detailTab = ref('overview');   // 详情弹窗 Tab：'overview' | 'comparison'
    const errorMessage = ref('');        // 错误消息
    const loading = ref(false);           // 加载状态
    const currentTipIndex = ref(0);     // 当前提示语索引
    
    // 定时器引用
    let progressTimer = null;
    let countTimer = null;
    let tipTimer = null;
    
    // ====== 滚轮选择器 Refs ======
    const wheelContainer = ref(null);
    const yearCol = ref(null);
    const monthCol = ref(null);
    const dayCol = ref(null);
    const yearScroll = ref(null);
    const monthScroll = ref(null);
    const dayScroll = ref(null);
    const hourCol = ref(null);
    const hourScroll = ref(null);

    // 滚轮状态
    const lunarMode = ref(false);
    const lunarDisplayText = ref('');

    // ====== 表单数据 ======
    const form = reactive({
      birthDate: '1995-06-15',
      birthHour: 12,
      gender: '男',
      topN: 5,
    });
    
    // ====== 常量数据 ======
    const shichenOptions = [
      '子时 (23:00-01:00)', '丑时 (01:00-03:00)', '寅时 (03:00-05:00)',
      '卯时 (05:00-07:00)', '辰时 (07:00-09:00)', '巳时 (09:00-11:00)',
      '午时 (11:00-13:00)', '未时 (13:00-15:00)', '申时 (15:00-17:00)',
      '酉时 (17:00-19:00)', '戌时 (19:00-21:00)', '亥时 (21:00-23:00)',
    ];
    
    const shichenValues = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22];
    
    const userBazi = ref(null);
    const matches = ref([]);
    const wuxingOrder = ['金', '木', '水', '火', '土'];
    const pillarLabels = ['年柱', '月柱', '日柱', '时柱'];
    
    // 提示语列表
    const tips = [
      '💡 提示：匹配结果仅供参考，真正的缘分需要用心经营',
      '🌸 提示：八字合盘源于传统文化，请理性看待结果',
      '✨ 提示：相似八字的人往往有相似的性格特点',
      '💑 提示：好的合盘不代表一定能在一起哦',
      '🏮 提示：缘分天注定，幸福靠经营',
      '📅 提示：准确的出生时间能让匹配更精准',
      '🎯 提示：系统会从多维度综合评估匹配度',
      '🌟 提示：最好的缘分是彼此珍惜和包容',
    ];
    
    // ====== 计算属性 ======
    const isFormValid = computed(() => {
      return form.birthDate && form.gender && form.topN >= 1 && form.topN <= 20;
    });
    
    const userBaziDisplay = computed(() => {
      if (!userBazi.value) return { pillars: [], dayMaster: '', wuxingDist: {}, pattern: '' };
      const b = userBazi.value;
      return {
        pillars: [
          [b.year_pillar[0], b.year_pillar[1]],
          [b.month_pillar[0], b.month_pillar[1]],
          [b.day_pillar[0], b.day_pillar[1]],
          [b.hour_pillar[0], b.hour_pillar[1]],
        ],
        dayMaster: b.day_master,
        wuxingDist: b.wuxing_dist,
        pattern: b.pattern || '',
      };
    });
    
    const currentTip = computed(() => {
      return tips[currentTipIndex.value];
    });
    
    // ====== 方法定义 ======
    
    /**
     * 获取维度图标
     */
    function getDimIcon(name) {
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
     * 获取维度图标背景色
     */
    function getDimIconBg(idx) {
      const classes = [
        'bg-rose-100 text-rose-600',
        'bg-emerald-100 text-emerald-600',
        'bg-sky-100 text-sky-600',
        'bg-amber-100 text-amber-600',
        'bg-violet-100 text-violet-600',
        'bg-teal-100 text-teal-600',
      ];
      return classes[idx % classes.length];
    }
    
    /**
     * 获取维度描述
     */
    function getDimDesc(name) {
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
    function getScoreBadgeClass(score) {
      if (score >= 80) return 'bg-gradient-to-br from-emerald-400 to-emerald-600 text-white';
      if (score >= 60) return 'bg-gradient-to-br from-amber-400 to-orange-500 text-white';
      if (score >= 40) return 'bg-gradient-to-br from-orange-400 to-red-500 text-white';
      return 'bg-gradient-to-br from-gray-400 to-gray-500 text-white';
    }
    
    /**
     * 获取命中项标签样式
     */
    function getHitTagClass(hit) {
      if (hit.includes('金')) return 'bg-amber-50 text-amber-700 border-amber-200';
      if (hit.includes('木')) return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      if (hit.includes('水')) return 'bg-sky-50 text-sky-700 border-sky-200';
      if (hit.includes('火')) return 'bg-red-50 text-red-700 border-red-200';
      if (hit.includes('土')) return 'bg-yellow-50 text-yellow-700 border-yellow-200';
      if (hit.includes('合') || hit.includes('三合')) return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      if (hit.includes('冲') || hit.includes('克')) return 'bg-rose-50 text-rose-700 border-rose-200';
      return 'bg-gray-50 text-gray-700 border-gray-200';
    }
    
    /**
     * 获取命中项前缀
     */
    function getHitPrefix(hit) {
      if (hit.includes('合') || hit.includes('三合')) return '✓';
      if (hit.includes('冲') || hit.includes('克')) return '⚠';
      return '•';
    }
    
    /**
     * 获取五行对应 emoji
     */
    function getWuxingEmoji(wx) {
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
    function scoreColor(score) {
      if (score >= 85) return 'text-rose-500';
      if (score >= 70) return 'text-orange-500';
      if (score >= 55) return 'text-yellow-600';
      if (score >= 40) return 'text-blue-500';
      return 'text-gray-500';
    }
    
    /**
     * 获取评分颜色类（兼容旧方法名）
     */
    function getScoreColor(score) {
      return scoreColor(score);
    }
    
    /**
     * 获取维度条颜色类（兼容旧方法名）
     */
    function dimBarColorClass(score) {
      return getDimBarClass(score);
    }
    function getDimBarClass(score) {
      if (score >= 70) return 'bg-gradient-to-t from-green-400 to-green-600';
      if (score >= 40) return 'bg-gradient-to-t from-yellow-400 to-yellow-600';
      return 'bg-gradient-to-t from-red-400 to-red-600';
    }
    
    /**
     * 开始匹配
     */
    async function startMatch() {
      if (!isFormValid.value) return;
      
      console.log('🚀 开始匹配流程');
      
      // 重置状态
      state.value = 'loading';
      progress.value = 0;
      matchedCount.value = 0;
      errorMessage.value = '';
      loading.value = true;
      
      // 启动进度条动画
      progressTimer = setInterval(() => {
        if (progress.value < 90) {
          progress.value += 1;
        }
      }, 30);
      
      // 启动匹配计数动画
      countTimer = setInterval(() => {
        if (matchedCount.value < 9500) {
          matchedCount.value += Math.floor(Math.random() * 200) + 50;
          if (matchedCount.value > 10000) matchedCount.value = 10000;
        }
      }, 100);
      
      // 启动提示语轮播
      tipTimer = setInterval(() => {
        currentTipIndex.value = (currentTipIndex.value + 1) % tips.length;
      }, 3000);
      
      // 解析日期
      const parts = form.birthDate.split('-');
      const by = parseInt(parts[0]);
      const bm = parseInt(parts[1]);
      const bd = parseInt(parts[2]);
      
      console.log('📤 发送请求:', { birth_year: by, birth_month: bm, birth_day: bd, birth_hour: form.birthHour, gender: form.gender, top_n: form.topN });
      
      try {
        // 发送匹配请求
        const resp = await axios.post('http://localhost:8000/api/match', {
          birth_year: by,
          birth_month: bm,
          birth_day: bd,
          birth_hour: form.birthHour,
          birth_minute: 0,
          gender: form.gender,
          top_n: form.topN,
        }, { timeout: 10000 });
        
        console.log('📥 收到响应:', resp.data);
        
        const data = resp.data;
        if (!data.success) throw new Error(data.message || '匹配失败');
        
        // 数据验证
        if (!data.user_bazi) {
          console.warn('⚠️ 后端返回的 user_bazi 为空');
        }
        if (!data.matches || !Array.isArray(data.matches)) {
          console.warn('⚠️ 后端返回的 matches 为空或格式错误');
          data.matches = [];
        }
        
        // 更新数据
        userBazi.value = data.user_bazi;
        matches.value = data.matches;
        progress.value = 100;
        matchedCount.value = 10000;
        
        // 清除定时器
        clearInterval(progressTimer);
        clearInterval(countTimer);
        clearInterval(tipTimer);
        loading.value = false;
        
        console.log('✅ 数据更新完成，准备切换状态');
        console.log('📊 userBazi:', userBazi.value);
        console.log('📊 matches 数量:', matches.value.length);
        
        // 延迟切换到结果页（让进度条走完）
        setTimeout(() => {
          console.log('🔄 切换到结果状态');
          state.value = 'result';
          console.log('✅ 状态已切换为 result');
        }, 500);
        
      } catch (err) {
        console.error('❌ 请求失败:', err);
        
        // 错误处理
        clearInterval(progressTimer);
        clearInterval(countTimer);
        clearInterval(tipTimer);
        loading.value = false;
        state.value = 'input';
        
        if (err.code === 'ECONNABORTED' || err.message.includes('timeout')) {
          errorMessage.value = '请求超时，请检查网络后重试';
        } else if (err.response) {
          const status = err.response.status;
          errorMessage.value = status >= 400 && status < 500 
            ? '请求参数错误，请检查输入信息' 
            : '服务器错误，请稍后重试';
        } else {
          errorMessage.value = '网络连接失败，请确保后端服务已启动';
        }
        
        // 5秒后自动清除错误消息
        setTimeout(() => {
          errorMessage.value = '';
        }, 5000);
      }
    }
    
    /**
     * 重置匹配
     */
    function resetMatch() {
      state.value = 'input';
      userBazi.value = null;
      matches.value = [];
      progress.value = 0;
      matchedCount.value = 0;
      // DOM 更新后重新初始化滚轮（从结果页切回时 DOM 会重新渲染）
      nextTick(() => {
        initWheelPicker();
        setInitialPositions();
      });
    }
    
    /**
     * 打开详情弹窗
     */
    function openDetail(m) {
      detailData.value = m;
      showDetail.value = true;
      document.body.classList.add('no-scroll');
    }
    
    /**
     * 关闭详情弹窗
     */
    function closeDetail() {
      showDetail.value = false;
      document.body.classList.remove('no-scroll');
    }
    
    /**
     * 切换详情弹窗 Tab
     */
    function switchDetailTab(tab) {
      detailTab.value = tab;
    }
    
    /**
     * 获取四柱对比数据（computed，避免模板中多次调用）
     * 返回 Person A 和 Person B 的四柱数据，包含十神标注
     */
    const comparisonData = computed(() => {
      const userData = userBazi.value;
      const matchData = detailData.value ? detailData.value.sizhu : null;
      
      if (!userData || !matchData) return { personA: null, personB: null };
      
      // 构建 Person A 的四柱数据
      const personA = {
        tiangan_list: userData.tiangan_list || [],
        dizhi_list: userData.dizhi_list || [],
        shishen_list: userData.shishen_list || [],
        minggua: userData.minggua || {},
        shengxiao: userData.shengxiao || '',
        pattern: userData.pattern || '',
      };
      
      // 构建 Person B 的四柱数据
      const personB = {
        tiangan_list: matchData.tiangan_list || [],
        dizhi_list: matchData.dizhi_list || [],
        shishen_list: matchData.shishen_list || [],
        minggua: matchData.minggua || {},
        shengxiao: matchData.shengxiao || '',
        pattern: matchData.pattern || '',
      };
      
      return { personA, personB };
    });
    
    /**
     * 格式化柱子显示（天干【十神】地支【十神】）
     */
    function formatPillar(tiangan, dizhi, shishenItem) {
      if (!shishenItem) return tiangan + '  ' + dizhi;
      const tg_shishen = shishenItem.gan_shishen || '';
      const dz_shishen = shishenItem.zhi_shishen || '';
      return tiangan + '【' + tg_shishen + '】' + dizhi + '【' + dz_shishen + '】';
    }
    
    /**
     * 获取天干五行颜色类名
     */
    function wuxingClassOf(gan) {
      if (!gan) return '';
      const m = { '甲':'mu','乙':'mu','丙':'huo','丁':'huo','戊':'tu','己':'tu','庚':'jin','辛':'jin','壬':'shui','癸':'shui' };
      return 'wx-' + (m[gan] || '');
    }

    /**
     * 键盘事件处理
     */
    function handleKeydown(e) {
      if (e.key === 'Escape' && showDetail.value) {
        closeDetail();
      }
    }

    /**
     * 后端健康检查
     */
    async function checkBackendHealth() {
      try {
        await axios.get('http://localhost:8000/api/health', { timeout: 3000 });
        console.log('✅ 后端服务连接正常');
      } catch (err) {
        console.warn('⚠️ 后端服务未启动或无法连接');
      }
    }

    // ====== 生命周期 ======
    onMounted(() => {
      document.addEventListener('keydown', handleKeydown);
      // 预加载：检查后端服务
      checkBackendHealth();
      // 延迟初始化滚轮（等 DOM 渲染完成）
      setTimeout(() => {
        initWheelPicker();
      }, 100);
    });
    
    onUnmounted(() => {
      document.removeEventListener('keydown', handleKeydown);
      clearInterval(progressTimer);
      clearInterval(countTimer);
      clearInterval(tipTimer);
    });
    
    // ====== 状态监听（调试用） ======
    watch(state, (newVal, oldVal) => {
      console.log(`🔄 状态变化: ${oldVal} → ${newVal}`);
    });
    
    // ====== 强制跳转到结果（调试用） ======
    function forceShowResult() {
      console.log('⚡ 强制跳转到结果页');
      clearInterval(progressTimer);
      clearInterval(countTimer);
      clearInterval(tipTimer);
      loading.value = false;
      progress.value = 100;
      matchedCount.value = 10000;
      state.value = 'result';
    }
    
    // ====== 滚轮选择器逻辑 ======
    
    // 滚轮状态：每个列独立
    const wheelData = {
      year:  { offset: 0, velocity: 0, dragging: false, startY: 0, startOffset: 0, lastY: 0, lastTime: 0 },
      month: { offset: 0, velocity: 0, dragging: false, startY: 0, startOffset: 0, lastY: 0, lastTime: 0 },
      day:   { offset: 0, velocity: 0, dragging: false, startY: 0, startOffset: 0, lastY: 0, lastTime: 0 },
      hour:  { offset: 0, velocity: 0, dragging: false, startY: 0, startOffset: 0, lastY: 0, lastTime: 0 },
    };
    const ITEM_HEIGHT = 56;
    const VISIBLE_ITEMS = 5;
    const CENTER_INDEX = Math.floor(VISIBLE_ITEMS / 2); // 2

    // 滚轮数据缓存
    let wheelYears = [];
    let wheelMonths = [];
    let wheelDays = [];
    let wheelHours = [];
    
    /**
     * 初始化滚轮选择器
     */
    function initWheelPicker() {
      buildYearItems();
      buildMonthItems();
      buildDayItems();
      buildHourItems();
      renderWheel('year', yearScroll.value, wheelYears);
      renderWheel('month', monthScroll.value, wheelMonths);
      renderWheel('day', dayScroll.value, wheelDays);
      renderWheel('hour', hourScroll.value, wheelHours);
      setInitialPositions();
      bindWheelEvents();
    }

    /**
     * 构建时辰列表
     */
    function buildHourItems() {
      wheelHours = [];
      const names = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'];
      const ranges = [
        '23:00-01:00', '01:00-03:00', '03:00-05:00',
        '05:00-07:00', '07:00-09:00', '09:00-11:00',
        '11:00-13:00', '13:00-15:00', '15:00-17:00',
        '17:00-19:00', '19:00-21:00', '21:00-23:00',
      ];
      const values = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22];
      for (let i = 0; i < 12; i++) {
        wheelHours.push({
          value: values[i],
          label: '<span class="hour-name">' + names[i] + '时</span><span class="hour-range">' + ranges[i] + '</span>'
        });
      }
    }
    
    /**
     * 构建年份列表 1900-2025
     */
    function buildYearItems() {
      wheelYears = [];
      for (let y = 1900; y <= 2025; y++) {
        wheelYears.push({ value: y, label: y + '年' });
      }
    }

    /**
     * 构建月份列表
     */
    function buildMonthItems() {
      wheelMonths = [];
      for (let i = 1; i <= 12; i++) {
        wheelMonths.push({ value: i, label: i + '月' });
      }
    }

    /**
     * 构建日期列表（根据当前年月动态计算）
     */
    function buildDayItems() {
      wheelDays = [];
      const selectedYear = getSelectedYear();
      const selectedMonth = getSelectedMonth();
      const maxDay = getMaxDay(selectedYear, selectedMonth);
      for (let i = 1; i <= maxDay; i++) {
        wheelDays.push({ value: i, label: i + '日' });
      }
    }
    
    /**
     * 获取选中的年份
     */
    function getSelectedYear() {
      const dataIdx = Math.round(-wheelData.year.offset / ITEM_HEIGHT);
      const idx = Math.max(0, Math.min(wheelYears.length - 1, dataIdx));
      return wheelYears[idx] ? wheelYears[idx].value : 1995;
    }
    
    /**
     * 获取选中的月份
     */
    function getSelectedMonth() {
      const dataIdx = Math.round(-wheelData.month.offset / ITEM_HEIGHT);
      const idx = Math.max(0, Math.min(wheelMonths.length - 1, dataIdx));
      return wheelMonths[idx] ? wheelMonths[idx].value : 6;
    }
    
    /**
     * 获取某年月的最大天数
     */
    function getMaxDay(year, month) {
      if ([1,3,5,7,8,10,12].includes(month)) return 31;
      if ([4,6,9,11].includes(month)) return 30;
      // 闰年判断
      if (year % 400 === 0) return 29;
      if (year % 100 === 0) return 28;
      if (year % 4 === 0) return 29;
      return 28;
    }
    
    /**
     * 渲染滚轮列
     */
    function renderWheel(type, scrollEl, items) {
      if (!scrollEl) return;
      // 前后各加 VISIBLE_ITEMS-1 个占位元素，让首尾项能滚到中间
      let html = '';
      // 上方占位
      for (let i = 0; i < CENTER_INDEX; i++) {
        html += '<div class="date-wheel-item" style="height:' + ITEM_HEIGHT + 'px;"></div>';
      }
      // 实际数据项
      for (let i = 0; i < items.length; i++) {
        html += '<div class="date-wheel-item" data-idx="' + i + '" style="height:' + ITEM_HEIGHT + 'px;">' + items[i].label + '</div>';
      }
      // 下方占位
      for (let i = 0; i < CENTER_INDEX; i++) {
        html += '<div class="date-wheel-item" style="height:' + ITEM_HEIGHT + 'px;"></div>';
      }
      scrollEl.innerHTML = html;
      updateSelectedHighlight(type);
    }
    
    /**
     * 更新选中项高亮
     * 注意：centerIdx 是 DOM 元素索引（包含占位符），不是 data-idx
     */
    function updateSelectedHighlight(type) {
      let offset = wheelData[type].offset;
      let scrollEl = type === 'year' ? yearScroll.value : (type === 'month' ? monthScroll.value : (type === 'day' ? dayScroll.value : hourScroll.value));
      if (!scrollEl) return;

      // 计算高亮区域中心对应的 DOM 元素索引
      let centerIdx = Math.round(-offset / ITEM_HEIGHT) + CENTER_INDEX;

      const els = scrollEl.querySelectorAll('.date-wheel-item');
      els.forEach((el, i) => {
        if (i === centerIdx) {
          el.classList.add('selected');
        } else {
          el.classList.remove('selected');
        }
      });
    }
    
    /**
     * 设置初始位置（根据 form.birthDate）
     */
    function setInitialPositions() {
      if (!form.birthDate) return;
      const parts = form.birthDate.split('-');
      const targetYear = parseInt(parts[0]);
      const targetMonth = parseInt(parts[1]);
      const targetDay = parseInt(parts[2]);
      
      let yearIdx = wheelYears.findIndex(y => y.value === targetYear);
      if (yearIdx === -1) yearIdx = wheelYears.findIndex(y => y.value === 1995);
      wheelData.year.offset = -(yearIdx) * ITEM_HEIGHT;

      let monthIdx = wheelMonths.findIndex(m => m.value === targetMonth);
      if (monthIdx === -1) monthIdx = 5; // 默认6月
      wheelData.month.offset = -(monthIdx) * ITEM_HEIGHT;
      
      // 重新构建日列表（因为月份可能变了）
      buildDayItems();
      renderWheel('day', dayScroll.value, wheelDays);
      
      let dayIdx = wheelDays.findIndex(d => d.value === targetDay);
      if (dayIdx === -1) dayIdx = Math.min(targetDay - 1, wheelDays.length - 1);
      if (dayIdx === -1) dayIdx = 0;
      wheelData.day.offset = -(dayIdx) * ITEM_HEIGHT;

      // 时辰初始位置
      let hourIdx = wheelHours.findIndex(h => h.value === form.birthHour);
      if (hourIdx === -1) hourIdx = 6; // 默认午时
      wheelData.hour.offset = -(hourIdx) * ITEM_HEIGHT;

      applyWheelTransforms();
    }
    
    /**
     * 应用滚轮变换（直接设置 transform）
     */
    function applyWheelTransforms() {
      if (yearScroll.value) yearScroll.value.style.transform = 'translateY(' + wheelData.year.offset + 'px)';
      if (monthScroll.value) monthScroll.value.style.transform = 'translateY(' + wheelData.month.offset + 'px)';
      if (dayScroll.value) dayScroll.value.style.transform = 'translateY(' + wheelData.day.offset + 'px)';
      if (hourScroll.value) hourScroll.value.style.transform = 'translateY(' + wheelData.hour.offset + 'px)';
      updateSelectedHighlight('year');
      updateSelectedHighlight('month');
      updateSelectedHighlight('day');
      updateSelectedHighlight('hour');
    }
    
    /**
     * 绑定滚轮事件
     */
    function bindWheelEvents() {
      const cols = [
        { type: 'year', col: yearCol.value, scroll: yearScroll.value },
        { type: 'month', col: monthCol.value, scroll: monthScroll.value },
        { type: 'day', col: dayCol.value, scroll: dayScroll.value },
        { type: 'hour', col: hourCol.value, scroll: hourScroll.value },
      ];
      cols.forEach(({ type, col, scroll }) => {
        if (!col || !scroll) return;
        
        // 鼠标事件
        col.addEventListener('mousedown', (e) => onWheelStart(e, type));
        // 触摸事件
        col.addEventListener('touchstart', (e) => onWheelStart(e, type), { passive: false });
        
        // 滚轮事件（鼠标滚轮）
        col.addEventListener('wheel', (e) => {
          e.preventDefault();
          wheelData[type].offset += e.deltaY > 0 ? ITEM_HEIGHT : -ITEM_HEIGHT;
          clampOffset(type);
          applyWheelTransforms();
        }, { passive: false });
      });
      
      // 全局移动/抬起
      document.addEventListener('mousemove', onWheelMove);
      document.addEventListener('mouseup', onWheelEndGlobal);
      document.addEventListener('touchmove', onWheelMove, { passive: false });
      document.addEventListener('touchend', onWheelEndGlobal);
    }
    
    let activeWheelType = null;
    
    function onWheelStart(e, type) {
      e.preventDefault();
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      activeWheelType = type;
      wheelData[type].dragging = true;
      wheelData[type].startY = clientY;
      wheelData[type].startOffset = wheelData[type].offset;
      wheelData[type].lastY = clientY;
      wheelData[type].lastTime = Date.now();
      wheelData[type].velocity = 0;
      
      if (yearScroll.value) yearScroll.value.style.transition = 'none';
      if (monthScroll.value) monthScroll.value.style.transition = 'none';
      if (dayScroll.value) dayScroll.value.style.transition = 'none';
      if (hourScroll.value) hourScroll.value.style.transition = 'none';
    }
    
    function onWheelMove(e) {
      if (!activeWheelType) return;
      e.preventDefault();
      const type = activeWheelType;
      if (!wheelData[type].dragging) return;
      
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      const delta = clientY - wheelData[type].startY;
      wheelData[type].offset = wheelData[type].startOffset + delta;
      
      // 计算速度（用于惯性）
      const now = Date.now();
      const dt = now - wheelData[type].lastTime;
      if (dt > 0) {
        wheelData[type].velocity = (clientY - wheelData[type].lastY) / dt * 16; // 标准化到每帧
      }
      wheelData[type].lastY = clientY;
      wheelData[type].lastTime = now;
      
      applyWheelTransforms();
    }
    
    function onWheelEndGlobal(e) {
      if (!activeWheelType) return;
      const type = activeWheelType;
      wheelData[type].dragging = false;
      activeWheelType = null;
      
      // 启动惯性
      startInertia(type);
    }
    
    /**
     * 惯性滚动
     */
    function startInertia(type) {
      const state = wheelData[type];
      let v = state.velocity * 8; // 惯性力度
      const friction = 0.92;
      const minVelocity = 0.5;
      
      function step() {
        if (wheelData[type].dragging) return; // 拖拽中停止惯性
        
        v *= friction;
        state.offset += v;
        
        // 边界回弹
        const items = type === 'year' ? wheelYears : (type === 'month' ? wheelMonths : (type === 'day' ? wheelDays : wheelHours));
        const maxOffset = 0; // 第一个数据项在高亮区域
        const minOffset = -(items.length - 1) * ITEM_HEIGHT; // 最后一个数据项在高亮区域
        if (state.offset > maxOffset) { state.offset = maxOffset; v = 0; }
        if (state.offset < minOffset) { state.offset = minOffset; v = 0; }
        
        applyWheelTransforms();
        
        if (Math.abs(v) > minVelocity) {
          requestAnimationFrame(step);
        } else {
          // 惯性结束，吸附
          snapToNearest(type);
        }
      }
      
      if (Math.abs(v) > minVelocity) {
        requestAnimationFrame(step);
      } else {
        snapToNearest(type);
      }
    }
    
    /**
     * 吸附到最近项
     */
    function snapToNearest(type) {
      const state = wheelData[type];
      let items = type === 'year' ? wheelYears : (type === 'month' ? wheelMonths : (type === 'day' ? wheelDays : wheelHours));
      let scrollEl = type === 'year' ? yearScroll.value : (type === 'month' ? monthScroll.value : (type === 'day' ? dayScroll.value : hourScroll.value));
      if (!scrollEl) return;

      console.log('[snapToNearest] type=' + type + ' offset=' + state.offset + ' items.length=' + items.length);

      // 计算高亮区域中心对应的 DOM 元素索引
      let domIdx = Math.round(-state.offset / ITEM_HEIGHT) + CENTER_INDEX;

      // 限制在有效数据范围内（排除占位符）
      const firstDataIdx = CENTER_INDEX;
      const lastDataIdx = CENTER_INDEX + items.length - 1;
      domIdx = Math.max(firstDataIdx, Math.min(lastDataIdx, domIdx));

      // 计算目标 offset：让第 domIdx 个 DOM 元素落到高亮区域
      const targetOffset = -(domIdx - CENTER_INDEX) * ITEM_HEIGHT;

      // 动画过渡到目标位置
      const startOffset = state.offset;
      const delta = targetOffset - startOffset;
      const duration = 200;
      const startTime = Date.now();

      function animate() {
        const elapsed = Date.now() - startTime;
        const t = Math.min(1, elapsed / duration);
        const ease = t * (2 - t); // ease-out
        state.offset = startOffset + delta * ease;

        // 更新 DOM
        scrollEl.style.transition = 'none';
        scrollEl.style.transform = 'translateY(' + state.offset + 'px)';
        updateSelectedHighlight(type);

        if (t < 1) {
          requestAnimationFrame(animate);
        } else {
          state.offset = targetOffset;
          scrollEl.style.transform = 'translateY(' + targetOffset + 'px)';
          updateSelectedHighlight(type);
          // 如果改变了年份或月份，需要更新日列表（闰年2月天数不同）
          if (type === 'year' || type === 'month') {
            rebuildDayWheel();
          }
          // 日期滚轮：自动确认
          if (type === 'year' || type === 'month' || type === 'day') {
            autoConfirmDate();
          }
          // 时辰滚轮：自动更新
          if (type === 'hour') {
            autoConfirmHour();
          }
        }
      }
      requestAnimationFrame(animate);
    }
    
    /**
     * 限制 offset 范围（确保不会滚动到占位符区域）
     */
    function clampOffset(type) {
      const state = wheelData[type];
      const items = type === 'year' ? wheelYears : (type === 'month' ? wheelMonths : (type === 'day' ? wheelDays : wheelHours));
      // 最大 offset：第一个数据项（索引0）在高亮区域
      const maxOffset = 0;
      // 最小 offset：最后一个数据项在高亮区域
      const minOffset = -(items.length - 1) * ITEM_HEIGHT;
      state.offset = Math.max(minOffset, Math.min(maxOffset, state.offset));
    }
    
    /**
     * 重新构建日滚轮（月份变化时调用）
     */
    function rebuildDayWheel() {
      // 保存当前选中的日期值（使用数据索引）
      // offset = -dataIdx * ITEM_HEIGHT，所以 dataIdx = -Math.round(offset / ITEM_HEIGHT)
      const currentDataIdx = Math.max(0, Math.min(wheelDays.length - 1, Math.round(-wheelData.day.offset / ITEM_HEIGHT)));
      const currentDayValue = wheelDays[currentDataIdx] ? wheelDays[currentDataIdx].value : 1;

      buildDayItems();
      renderWheel('day', dayScroll.value, wheelDays);

      // 尝试保持选中的日期，如果无效则选最后一天
      let newIdx = wheelDays.findIndex(d => d.value === currentDayValue);
      if (newIdx === -1) newIdx = wheelDays.length - 1;
      wheelData.day.offset = -(newIdx) * ITEM_HEIGHT;

      applyWheelTransforms();
    }
    
    /**
     * 自动确认日期（滚动停止后调用）
     */
    function autoConfirmDate() {
      const year = getSelectedYear();
      const month = getSelectedMonth();
      // 计算数据索引（不是 DOM 元素索引）
      const dataIdx = Math.round(-wheelData.day.offset / ITEM_HEIGHT);
      const idx = Math.max(0, Math.min(wheelDays.length - 1, dataIdx));
      const day = wheelDays[idx] ? wheelDays[idx].value : 1;

      const mm = String(month).padStart(2, '0');
      const dd = String(day).padStart(2, '0');
      form.birthDate = year + '-' + mm + '-' + dd;
    }

    /**
     * 自动确认时辰（滚动停止后调用）
     */
    function autoConfirmHour() {
      const dataIdx = Math.round(-wheelData.hour.offset / ITEM_HEIGHT);
      const idx = Math.max(0, Math.min(wheelHours.length - 1, dataIdx));
      const hour = wheelHours[idx] ? wheelHours[idx].value : 12;
      form.birthHour = hour;
    }
    
    // 监听状态变化，当切回输入页时确保滚轮已初始化
    watch(state, (newVal) => {
      if (newVal === 'input') {
        nextTick(() => {
          initWheelPicker();
          setInitialPositions();
        });
      }
    });
    
    // ====== 返回模板所需数据和方法 ======
    return {
      // 状态
      state,
      progress,
      matchedCount,
      showDetail,
      detailData,
      detailTab,
      errorMessage,
      loading,
      currentTip,
      
      // 表单
      form,
      shichenOptions,
      shichenValues,
      wuxingOrder,
      pillarLabels,
      
      // 数据
      userBazi,
      matches,
      
      // 计算属性
      isFormValid,
      userBaziDisplay,
      comparisonData,
      
      // 滚轮选择器
      wheelContainer,
      yearCol,
      monthCol,
      dayCol,
      yearScroll,
      monthScroll,
      dayScroll,
      hourCol,
      hourScroll,
      startMatch,
      resetMatch,
      openDetail,
      closeDetail,
      switchDetailTab,
      formatPillar,
      wuxingClassOf,
      forceShowResult,
      scoreColor,
      getScoreColor,
      getDimIcon,
      getDimIconBg,
      getDimDesc,
      getScoreBadgeClass,
      getHitTagClass,
      getHitPrefix,
      getWuxingEmoji,
      getDimBarClass,
      dimBarColorClass,
    };
  }
});

// ====== 挂载应用 ======
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue 错误:', err);
  console.error('错误信息:', info);
  alert('页面出现错误，请刷新重试。错误: ' + err.message);
};

app.mount('#app');

console.log('%c🏮 八字合盘匹配系统 %c v2.0', 
  'background: #6366f1; color: white; padding: 4px 8px; border-radius: 4px 0 0 4px; font-weight: bold;',
  'background: #a855f7; color: white; padding: 4px 8px; border-radius: 0 4px 4px 0;'
);
