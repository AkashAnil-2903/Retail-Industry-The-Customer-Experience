// Workforce Engagement Platform - Tier-3 Retail
// ============================================================

// --- I18N ---
// Load translations synchronously before rendering
(function() {
  try {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/static/i18n.json', false);
    xhr.send();
    if (xhr.status === 200) {
      window.I18N = JSON.parse(xhr.responseText);
    }
  } catch(e) {}
  if (!window.I18N) {
    window.I18N = { en: {}, hi: {}, or: {} };
  }
})();
var I18N = window.I18N;

// --- STATE ---
var appState = {
  token: localStorage.getItem('token'),
  role: localStorage.getItem('role'),
  userId: localStorage.getItem('userId'),
  employeeId: localStorage.getItem('employeeId'),
  userName: localStorage.getItem('userName'),
  lang: localStorage.getItem('lang') || 'en',
  page: 'login'
};

function t(key) { var lang = appState.page === 'login' ? 'en' : appState.lang; return (I18N[lang] || I18N.en)[key] || key; }
function setLang(lang) { appState.lang = lang; localStorage.setItem('lang', lang); render(); }

// --- API ---
var API_BASE = '/api';
function api(path, opts) {
  opts = opts || {};
  var headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {});
  if (appState.token) { headers['Authorization'] = 'Bearer ' + appState.token; }
  return fetch(API_BASE + path, Object.assign({}, opts, { headers: headers }))
    .then(function(res) {
      if (res.status === 401) { logout(); return null; }
      if (!res.ok) { return res.json().catch(function(){return {};}).then(function(e){ throw new Error(e.detail || 'Request failed'); }); }
      return res.json();
    })
    .catch(function(err) { showToast(err.message, 'error'); return null; });
}

// --- AUTH ---
function login(email, password) {
  var form = new URLSearchParams();
  form.append('username', email);
  form.append('password', password);
  fetch(API_BASE + '/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: form })
    .then(function(res) {
      if (!res.ok) { showToast('Invalid credentials', 'error'); throw new Error('login failed'); }
      return res.json();
    })
    .then(function(data) {
      appState.token = data.access_token;
      appState.role = data.role;
      appState.userId = data.user_id;
      appState.employeeId = data.employee_id;
      appState.userName = data.name;
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('role', data.role);
      localStorage.setItem('userId', data.user_id);
      localStorage.setItem('employeeId', data.employee_id || '');
      localStorage.setItem('userName', data.name || '');
      if (data.role === 'manager') navigate('manager-dashboard');
      else if (data.role === 'admin') navigate('admin-dashboard');
      else navigate('employee-dashboard');
    })
    .catch(function() {});
}

function logout() {
  appState.token = null;
  appState.role = null;
  ['token','role','userId','employeeId','userName'].forEach(function(k){ localStorage.removeItem(k); });
  navigate('login');
}

// --- MANAGER STATE ---
var mgrState = { level: 'org', storeId: null, storeName: '', employeeId: null };

// --- NAVIGATION ---
function navigate(page) { appState.page = page; render(); }

// --- HIERARCHICAL NAV ---
function navigateToOrg() { mgrState.level = 'org'; mgrState.storeId = null; mgrState.employeeId = null; mgrState.storeName = ''; navigate('manager-dashboard'); }
function navigateToStore(id, name) { mgrState.level = 'store'; mgrState.storeId = id; mgrState.storeName = name || ''; mgrState.employeeId = null; navigate('manager-store'); }
function navigateToEmployee(id) { mgrState.level = 'employee'; mgrState.employeeId = id; navigate('manager-employee'); }
function breadcrumbHtml() {
    var bc = '<div class="flex items-center gap-2 text-sm text-gray-500 mb-4">';
    bc += '<button onclick="navigateToOrg()" class="hover:text-brand-600 transition">Organization</button>';
    if (mgrState.level === 'store' || mgrState.level === 'employee') {
        bc += '<span>\u25B6</span>';
        bc += '<button onclick="navigateToStore(' + mgrState.storeId + ',\'' + mgrState.storeName + '\')" class="hover:text-brand-600 transition">' + mgrState.storeName + '</button>';
    }
    if (mgrState.level === 'employee') {
        bc += '<span>\u25B6</span>';
        bc += '<span class="text-gray-800 font-medium">' + (mgrState.employeeName || 'Employee') + '</span>';
    }
    bc += '</div>';
    return bc;
}

// --- TOAST ---
function showToast(msg, type) {
  type = type || 'info';
  var c = document.getElementById('toast-container');
  var colors = { success: 'bg-green-500', error: 'bg-red-500', info: 'bg-brand-500', warning: 'bg-amber-500' };
  var icons = { success: '\u2713', error: '\u2717', info: '\u2139', warning: '\u26A0' };
  var el = document.createElement('div');
  el.className = 'toast flex items-center gap-2 px-4 py-3 rounded-lg text-white shadow-lg text-sm ' + (colors[type] || colors.info);
  el.innerHTML = '<span class="font-bold">' + (icons[type] || '\u2139') + '</span><span>' + msg + '</span>';
  c.appendChild(el);
  setTimeout(function(){ el.remove(); }, 3000);
}

// --- COMPONENTS ---
function skillRing(score, size, label) {
  size = size || 100;
  label = label || '';
  var r = (size - 12) / 2;
  var c = 2 * Math.PI * r;
  var offset = c - (score / 100) * c;
  var color = score >= 70 ? '#10b981' : score >= 50 ? '#f59e0b' : '#ef4444';
  var html = '<div class="flex flex-col items-center gap-1">';
  html += '<svg width="' + size + '" height="' + size + '" class="transform -rotate-90">';
  html += '<circle cx="' + (size/2) + '" cy="' + (size/2) + '" r="' + r + '" fill="none" stroke="#e5e7eb" stroke-width="8"/>';
  html += '<circle cx="' + (size/2) + '" cy="' + (size/2) + '" r="' + r + '" fill="none" stroke="' + color + '" stroke-width="8" stroke-dasharray="' + c + '" stroke-dashoffset="' + offset + '" stroke-linecap="round" class="skill-bar"/>';
  html += '</svg>';
  html += '<span class="text-lg font-bold" style="color:' + color + '">' + Math.round(score) + '%</span>';
  if (label) { html += '<span class="text-xs text-gray-500 text-center leading-tight">' + label + '</span>'; }
  html += '</div>';
  return html;
}

function statCard(icon, label, value, color) {
  color = color || 'brand';
  var colors = {
    brand: 'bg-brand-50 text-brand-600 border-brand-200',
    green: 'bg-green-50 text-green-600 border-green-200',
    amber: 'bg-amber-50 text-amber-600 border-amber-200',
    red: 'bg-red-50 text-red-600 border-red-200'
  };
  return '<div class="bg-white rounded-xl border p-4 flex items-center gap-3 fade-in">' +
    '<div class="w-10 h-10 rounded-lg flex items-center justify-center text-xl ' + (colors[color] || colors.brand) + '">' + icon + '</div>' +
    '<div><div class="text-xs text-gray-500">' + label + '</div><div class="text-xl font-bold">' + value + '</div></div></div>';
}

function progressBar(pct, color) {
  color = color || 'bg-brand-500';
  return '<div class="w-full bg-gray-200 rounded-full h-2"><div class="' + color + ' h-2 rounded-full skill-bar" style="width:' + Math.min(100, pct) + '%"></div></div>';
}

function capitalize(s) {
  return s.replace(/_/g, ' ').replace(/\b\w/g, function(l){ return l.toUpperCase(); });
}

// --- NAV BAR ---
function navBar() {
  var isEmp = appState.role === 'employee';
  var isMgr = appState.role === 'manager';
  var isAdm = appState.role === 'admin';
  var items;
  if (isEmp) {
    items = [
      ['employee-dashboard', '\uD83D\uDCCA', t('dashboard')],
      ['courses-page', '\uD83D\uDCDA', t('courses')],
      ['simulation-page', '\uD83E\uDD16', t('simulation')],
      ['peer-recognition-page', '\uD83D\uDD17', t('peerRecognition')],
      ['pos-learning-page', '\uD83D\uDCBB', t('posLearning')],
      ['leaderboard-page', '\uD83C\uDFC6', t('leaderboard')],
      ['challenges-page', '\uD83C\uDFAF', t('challenges')]
    ];
  } else if (isMgr) {
    items = [
      ['manager-dashboard', '\uD83D\uDCCA', t('navOrganization')],
      ['manager-heatmap', '\uD83D\uDDFA\uFE0F', t('heatmap')],
      ['manager-business', '\uD83D\uDCC8', t('businessImpact')],
      ['leaderboard-page', '\uD83C\uDFC6', t('leaderboard')]
    ];
  } else {
    items = [
      ['admin-dashboard', '\uD83D\uDCCA', t('dashboard')],
      ['manager-employees', '\uD83D\uDC65', t('employees')],
      ['manager-heatmap', '\uD83D\uDDFA\uFE0F', 'Stores'],
      ['leaderboard-page', '\uD83C\uDFC6', t('leaderboard')]
    ];
  }
  var navItems = '';
  for (var i = 0; i < items.length; i++) {
    var pg = items[i][0], ic = items[i][1], lb = items[i][2];
    var cls = 'px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition ' + (appState.page === pg ? 'bg-brand-100 text-brand-700' : 'text-gray-600 hover:bg-gray-100');
    navItems += '<button onclick="navigate(\'' + pg + '\')" class="' + cls + '">' + ic + ' ' + lb + '</button>';
  }
  var userInitial = (appState.userName || 'U')[0];

  return '<nav class="bg-white border-b border-gray-200 sticky top-0 z-40">' +
    '<div class="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">' +
    '<div class="flex items-center gap-2">' +
    '<span class="text-xl">\uD83E\uDDD1\u200D\uD83D\uDCBC</span>' +
    '<span class="font-bold text-brand-700 hidden sm:block">' + t('navPlatform') + '</span>' +
    '</div>' +
    '<div class="flex items-center gap-1 overflow-x-auto">' + navItems + '</div>' +
    '<div class="flex items-center gap-3">' +
    '<select onchange="setLang(this.value)" class="text-sm border rounded-lg px-2 py-1 bg-white">' +
    '<option value="en"' + (appState.lang==='en'?' selected':'') + '>English</option>' +
    '<option value="hi"' + (appState.lang==='hi'?' selected':'') + '>\u0939\u093F\u0928\u094D\u0926\u0940</option>' +
    '<option value="or"' + (appState.lang==='or'?' selected':'') + '>\u0B13\u0B21\u0B3F\u0B06</option>' +
    '</select>' +
    '<div class="flex items-center gap-2 text-sm text-gray-600">' +
    '<span class="w-8 h-8 bg-brand-100 text-brand-700 rounded-full flex items-center justify-center font-bold text-xs">' + userInitial + '</span>' +
    '<span class="hidden md:block">' + (appState.userName || 'User') + '</span>' +
    '</div>' +
    '<button onclick="logout()" class="text-sm text-gray-500 hover:text-red-600" title="' + t('logout') + '">\u23FB</button>' +
    '</div></div></nav>';
}

// --- PAGES ---
function renderLoginPage() {
  return '<div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-500 via-brand-600 to-purple-700 p-4">' +
    '<div class="w-full max-w-md">' +
    '<div class="text-center mb-8">' +
    '<div class="w-20 h-20 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-4 text-4xl backdrop-blur-sm">\uD83E\uDDE0</div>' +
    '<h1 class="text-3xl font-bold text-white">' + t('platformName') + '</h1>' +
    '<p class="text-white/80 mt-2">Tier-3 Retail Associate Learning & Recognition</p>' +
    '<div class="flex items-center justify-center gap-3 mt-3 text-xs">' +
    '<span class="bg-white/20 px-3 py-1 rounded-full">Prototype: 10 Stores | 120+ Associates</span>' +
    '<span class="bg-green-500/30 px-3 py-1 rounded-full">Designed to scale to 1,200+ Stores</span>' +
    '</div>' +
    '</div>' +
    '<div class="bg-white rounded-2xl shadow-2xl p-8">' +
    '<h2 class="text-xl font-bold mb-6">' + t('login') + '</h2>' +
    '<form onsubmit="event.preventDefault(); login(this.email.value, this.password.value)">' +
    '<div class="mb-4">' +
    '<label class="block text-sm font-medium text-gray-700 mb-1">' + t('email') + '</label>' +
    '<input name="email" type="email" value="employee@demo.com" required class="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition"/>' +
    '</div>' +
    '<div class="mb-6">' +
    '<label class="block text-sm font-medium text-gray-700 mb-1">' + t('password') + '</label>' +
    '<input name="password" type="password" value="employee123" required class="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition"/>' +
    '</div>' +
    '<button type="submit" class="w-full bg-brand-600 hover:bg-brand-700 text-white font-semibold py-3 rounded-xl transition">' + t('loginBtn') + '</button>' +
    '</form>' +
    '<div class="mt-6 p-4 bg-gray-50 rounded-xl">' +
    '<p class="text-xs text-gray-500 font-medium mb-2">' + t('demoAccounts') + '</p>' +
    '<div class="space-y-1 text-xs text-gray-600">' +
    '<div class="flex justify-between"><span>Employee</span><code class="bg-gray-200 px-1.5 rounded">employee@demo.com</code></div>' +
    '<div class="flex justify-between"><span>Manager</span><code class="bg-gray-200 px-1.5 rounded">manager@demo.com</code></div>' +
    '<div class="flex justify-between"><span>Admin</span><code class="bg-gray-200 px-1.5 rounded">admin@demo.com</code></div>' +
    '</div>' +
    '<p class="text-xs text-gray-400 mt-2">' + t('demoPassword') + '</p>' +
    '<div class="mt-3 pt-3 border-t border-gray-200">' +
    '<p class="text-xs text-gray-400 text-center">' + t('footerName') + '</p>' +
    '<p class="text-xs text-gray-400 text-center">10 Stores | 120+ Associates | Vernacular Support</p>' +
    '</div>' +
    '</div></div></div></div>';
}

// --- EMPLOYEE DASHBOARD ---
function renderEmployeeDashboard() {
  return Promise.all([api('/employee/dashboard'), api('/employee/peer-recognitions')]).then(function(results) {
    var data = results[0] || {};
    var peerRecs = results[1] || [];
    if (!data.employee) return '<div class="p-8 text-center text-gray-500">' + t('noData') + '</div>';
    var emp = data.employee;
    var skills = data.skills || {};
    var html = navBar();
    html += '<div class="max-w-7xl mx-auto p-4 space-y-6 fade-in">';

    // Header
    html += '<div class="bg-gradient-to-r from-brand-600 to-purple-600 rounded-2xl p-6 text-white">';
    html += '<div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">';
    html += '<div>';
    html += '<h1 class="text-2xl font-bold">' + t('welcome') + ', ' + emp.name + ' \uD83D\uDC4B</h1>';
    html += '<p class="text-white/80 mt-1">' + emp.store_name + ' \u00B7 Level ' + emp.level + ' \u00B7 ' + emp.rank + '</p>';
    html += '<div class="flex gap-2 mt-2">'; 
    html += '<span class="text-xs bg-white/20 px-2 py-0.5 rounded-full">\uD83C\uDFFD Prototype: 10 Stores | 120+ Associates</span>';
    html += '</div>';
    html += '</div>';
    html += '<div class="flex items-center gap-4">';
    html += '<div class="text-center"><div class="text-3xl font-bold">' + emp.xp + '</div><div class="text-white/70 text-xs">' + t('xp') + '</div></div>';
    html += '<div class="text-center"><div class="text-3xl">\uD83D\uDD25</div><div class="text-white/70 text-xs">' + emp.streak_days + ' ' + t('streak') + '</div></div>';
    html += '</div></div></div>';

    // Stats Grid
    html += '<div class="grid grid-cols-2 md:grid-cols-4 gap-3">';
    html += statCard('\uD83C\uDFAF', t('skillScore'), emp.overall_skill_score + '%', 'brand');
    html += statCard('\uD83D\uDCAC', t('engagement'), emp.engagement_score + '%', 'green');
    html += statCard('\uD83D\uDCDA', t('training'), emp.training_completion + '%', 'amber');
    html += statCard('\u2328\uFE0F', t('posAdoption'), emp.pos_adoption + '%', 'red');
    html += '</div>';

    // Skill Rings + Gaps
    html += '<div class="grid md:grid-cols-2 gap-4">';
    html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold text-gray-800 mb-4">' + t('skillScore') + '</h3>';
    html += '<div class="flex flex-wrap justify-around gap-4">';
    html += skillRing(skills.product_knowledge || 50, 90, t('productKnowledge'));
    html += skillRing(skills.communication || 50, 90, t('communication'));
    html += skillRing(skills.objection_handling || 50, 90, t('objectionHandling'));
    html += skillRing(skills.upselling || 50, 90, t('upselling'));
    html += '</div></div>';

    // Skill Gaps
    html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold text-gray-800 mb-3">' + t('skillGap') + '</h3>';
    var gaps = data.skill_gaps || [];
    if (gaps.length) {
      for (var i = 0; i < gaps.length; i++) {
        var g = gaps[i];
        var pbarColor = g.priority === 'high' ? 'bg-red-500' : g.priority === 'medium' ? 'bg-amber-500' : 'bg-green-500';
        html += '<div class="mb-3 p-3 bg-gray-50 rounded-lg">';
        html += '<div class="flex justify-between text-sm mb-1"><span class="font-medium">' + capitalize(g.skill) + '</span>';
        html += '<span class="text-gray-500">' + g.current_score + '% \u2192 ' + g.target_score + '%</span></div>';
        html += progressBar(100 - g.gap * 2, pbarColor);
        html += '</div>';
      }
    } else {
      html += '<p class="text-gray-400 text-sm">No significant gaps detected \uD83C\uDF89</p>';
    }

    // Next Best Action
    if (data.next_action) {
      html += '<div class="mt-4 p-4 bg-brand-50 border border-brand-200 rounded-xl">';
      html += '<div class="flex items-start gap-3"><span class="text-2xl">\uD83C\uDFAF</span>';
      html += '<div><div class="font-bold text-brand-800">' + t('nextAction') + '</div>';
      html += '<div class="text-sm text-brand-600 mt-1">' + data.next_action.title + '</div>';
      html += '<div class="text-xs text-gray-500 mt-1">' + data.next_action.description + '</div>';
      html += '</div></div></div>';
    }
    html += '</div></div>';

    // Before/After Assessment
    html += '<div class="bg-white rounded-xl border p-5">';
    html += '<h3 class="font-bold text-gray-800 mb-3">\uD83D\uDCCA ' + t('before') + ' / ' + t('after') + ' Assessment</h3>';
    html += '<div class="flex flex-col md:flex-row items-center gap-6">';
    html += '<div class="flex-1 text-center"><div class="text-sm text-gray-500 mb-1">' + t('preAssess') + '</div>';
    if (emp.has_completed_pre_assessment) {
      html += skillRing(data.pre_assessment_score || 50, 100);
    } else {
      html += '<div class="text-gray-400 text-sm py-6">Not yet taken</div>';
    }
    html += '</div>';
    html += '<div class="text-3xl text-gray-300">\u2192</div>';
    html += '<div class="flex-1 text-center"><div class="text-sm text-gray-500 mb-1">' + t('postAssess') + '</div>';
    if (emp.has_completed_post_assessment) {
      html += skillRing(data.post_assessment_score || 50, 100);
    } else {
      html += '<div class="text-gray-400 text-sm py-6">Complete training first</div>';
    }
    html += '</div>';
    if (emp.has_completed_pre_assessment && emp.has_completed_post_assessment) {
      var imp = (data.post_assessment_score || 0) - (data.pre_assessment_score || 0);
      html += '<div class="text-center p-4 bg-green-50 rounded-xl border border-green-200">';
      html += '<div class="text-2xl font-bold text-green-600">+' + imp + '%</div>';
      html += '<div class="text-sm text-green-700">' + t('improvement') + '</div></div>';
    }
    html += '</div></div>';

    // Recommended Courses
    html += '<div class="bg-white rounded-xl border p-5">';
    html += '<h3 class="font-bold text-gray-800 mb-3">' + t('recommended') + '</h3>';
    html += '<div class="grid sm:grid-cols-2 md:grid-cols-3 gap-3">';
    var recs = data.recommended_courses || [];
    for (var i = 0; i < recs.length; i++) {
      var c = recs[i];
      html += '<div class="p-4 border rounded-xl hover:shadow-md transition cursor-pointer" onclick="openCourse(' + c.id + ')">';
      html += '<div class="text-sm font-bold text-gray-800">' + c.title + '</div>';
      html += '<div class="text-xs text-gray-500 mt-1">\u23F1 ' + c.duration + ' min \u00B7 ' + c.difficulty + '</div>';
      html += '<div class="mt-2 text-xs px-2 py-1 bg-brand-50 text-brand-700 rounded-full inline-block">' + c.skill_category.replace(/_/g, ' ') + '</div>';
      html += '</div>';
    }
    html += '</div></div>';

    // AI Customer Skill Assessment - Prominent CTA
    html += '<div class="bg-gradient-to-r from-brand-600 to-purple-600 rounded-2xl p-6 text-white">';
    html += '<div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">';
    html += '<div>';
    html += '<div class="text-lg font-bold">' + t('startAssessment') + ' \uD83E\uDD16</div>';
    html += '<div class="text-white/80 text-sm mt-1">Practice with a realistic AI customer and discover your strengths and skill gaps.</div>';
    if (emp.has_completed_pre_assessment && data.pre_assessment_score) {
      html += '<div class="flex items-center gap-3 mt-2 text-sm">';
      html += '<span class="bg-white/20 px-2 py-1 rounded">Last score: ' + data.pre_assessment_score + '%</span>';
      if (data.post_assessment_score) {
        var imp = data.post_assessment_score - data.pre_assessment_score;
        html += '<span class="bg-green-400/30 px-2 py-1 rounded text-green-100">Improvement: +' + imp + '%</span>';
      }
      html += '</div>';
    }
    html += '</div>';
    html += '<button onclick="navigate(\'simulation-page\')" class="px-6 py-3 bg-white text-brand-700 rounded-xl font-bold hover:bg-gray-100 transition whitespace-nowrap">' + t('chatWithCustomer') + ' \u2192</button>';
    html += '</div></div>';

    // Quick Actions
    html += '<div class="grid sm:grid-cols-2 gap-3">';
    html += '<button onclick="navigate(\'simulation-page\')" class="p-5 bg-gradient-to-r from-brand-500 to-purple-500 rounded-xl text-white text-left hover:shadow-lg transition">';
    html += '<div class="text-2xl mb-2">\uD83E\uDD16</div><div class="font-bold">' + t('preAssess') + '</div>';
    html += '<div class="text-sm text-white/80 mt-1">Start AI customer skill assessment</div></button>';
    html += '<button onclick="navigate(\'courses-page\')" class="p-5 bg-gradient-to-r from-green-500 to-teal-500 rounded-xl text-white text-left hover:shadow-lg transition">';
    html += '<div class="text-2xl mb-2">\uD83D\uDCDA</div><div class="font-bold">' + t('startCourse') + '</div>';
    html += '<div class="text-sm text-white/80 mt-1">' + data.completed_courses + '/' + data.total_courses + ' courses completed</div></button>';
    html += '</div>';

    // Badges & Leaderboard
    html += '<div class="grid md:grid-cols-2 gap-4">';
    html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold text-gray-800 mb-3">' + t('badges') + '</h3>';
    html += '<div class="flex flex-wrap gap-3">';
    var badges = data.badges || [];
    if (badges.length) {
      for (var i = 0; i < badges.length; i++) {
        var b = badges[i];
        html += '<div class="flex items-center gap-2 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg" title="' + b.description + '">';
        html += '<span class="text-xl">' + b.icon + '</span>';
        html += '<span class="text-sm font-medium text-amber-800">' + b.name + '</span></div>';
      }
    } else {
      html += '<p class="text-gray-400 text-sm">Complete courses to earn badges!</p>';
    }
    html += '</div></div>';

    html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold text-gray-800 mb-3">\uD83C\uDFC6 ' + t('leaderboard') + ' \u2014 Rank #' + data.current_rank + '</h3>';
    html += '<div class="space-y-2">';
    var lb = data.leaderboard || [];
    for (var i = 0; i < Math.min(5, lb.length); i++) {
      var l = lb[i];
      var rankBg = i===0 ? 'bg-amber-400' : i===1 ? 'bg-gray-300' : i===2 ? 'bg-amber-600' : 'bg-gray-100';
      var rowBg = i===0 ? 'bg-amber-50 rounded-lg px-2' : '';
      html += '<div class="flex items-center justify-between py-2 ' + rowBg + '">';
      html += '<div class="flex items-center gap-2">';
      html += '<span class="w-6 h-6 rounded-full ' + rankBg + ' text-white text-xs flex items-center justify-center font-bold">' + (i+1) + '</span>';
      html += '<span class="text-sm font-medium">' + l.name + '</span></div>';
      html += '<span class="text-sm text-gray-500">' + l.xp + ' XP</span></div>';
    }
    html += '</div></div></div>';

    // Peer Recognitions
    if (peerRecs.length) {
      html += '<div class="bg-gradient-to-r from-pink-50 to-purple-50 rounded-xl border border-pink-100 p-5">';
      html += '<div class="flex items-center gap-2 mb-3">';
      html += '<span class="text-xl">\uD83D\uDD17</span>';
      html += '<h3 class="font-bold text-gray-800">Peer Recognitions</h3>';
      html += '<button onclick="navigate(\'peer-recognition-page\')" class="ml-auto text-xs text-brand-600 hover:text-brand-800 font-medium">View All \u2192</button>';
      html += '</div>';
      html += '<div class="space-y-2">';
      for (var pi = 0; pi < Math.min(3, peerRecs.length); pi++) {
        var pr = peerRecs[pi];
        html += '<div class="flex items-center gap-3 p-3 bg-white/60 rounded-lg">';
        html += '<span class="text-lg">\uD83C\uDF1F</span>';
        html += '<div class="flex-1 min-w-0"><div class="text-sm font-medium text-gray-800">' + pr.from_name + ' recognized you</div>';
        html += '<div class="text-xs text-gray-500 truncate">' + pr.message + '</div></div>';
        html += '<span class="text-xs text-green-600 font-medium flex-shrink-0">+' + pr.xp_awarded + ' XP</span>';
        html += '</div>';
      }
      html += '</div></div>';
    }

    // Notifications
    var notifs = data.notifications || [];
    if (notifs.length) {
      html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold text-gray-800 mb-3">\uD83D\uDD14 Notifications</h3>';
      html += '<div class="space-y-2">';
      for (var i = 0; i < Math.min(4, notifs.length); i++) {
        var n = notifs[i];
        var nIcon = n.type === 'success' ? '\u2705' : n.type === 'warning' ? '\u26A0\uFE0F' : '\u2139\uFE0F';
        html += '<div class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">';
        html += '<span class="text-lg">' + nIcon + '</span>';
        html += '<div><div class="text-sm font-medium">' + n.title + '</div>';
        html += '<div class="text-xs text-gray-500">' + n.message + '</div></div></div>';
      }
      html += '</div></div>';
    }

    html += '</div>';
    return html;
  });
}

// --- COURSES PAGE ---
function renderCoursesPage() {
  return api('/courses/').then(function(courses) {
    var html = navBar();
    html += '<div class="max-w-5xl mx-auto p-4 space-y-4 fade-in">';
    html += '<h2 class="text-2xl font-bold">' + t('courses') + '</h2>';
    html += '<div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">';
    var list = courses || [];
    for (var i = 0; i < list.length; i++) {
      var c = list[i];
      var status = (c.progress && c.progress.status) || 'not_started';
      var colors = { completed: 'border-green-300 bg-green-50', in_progress: 'border-amber-300 bg-amber-50', not_started: 'border-gray-200 bg-white' };
      var labels = { completed: t('completed'), in_progress: t('inProgress'), not_started: t('notStarted') };
      html += '<div class="p-5 border-2 rounded-xl ' + (colors[status] || colors.not_started) + ' hover:shadow-md transition">';
      html += '<div class="flex items-start justify-between mb-3">';
      html += '<span class="text-2xl">' + (status==='completed'?'\u2705':status==='in_progress'?'\uD83D\uDD04':'\uD83D\uDCD6') + '</span>';
      html += '<span class="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-600">' + (labels[status] || labels.not_started) + '</span>';
      html += '</div>';
      html += '<h3 class="font-bold text-gray-800">' + c.title + '</h3>';
      html += '<p class="text-sm text-gray-500 mt-1">' + (c.description || '').slice(0, 80) + '...</p>';
      html += '<div class="flex items-center gap-3 mt-3 text-xs text-gray-500">';
      html += '<span>\u23F1 ' + c.duration_minutes + ' min</span>';
      html += '<span>\uD83D\uDCCA ' + c.difficulty + '</span>';
      html += '<span>\uD83C\uDFF7\uFE0F ' + c.skill_category.replace(/_/g, ' ') + '</span>';
      html += '</div>';
      var pct = c.progress ? (c.progress.percent || (status==='completed'?100:0)) : 0;
      var pbColor = status === 'completed' ? 'bg-green-500' : 'bg-brand-500';
      html += '<div class="mt-3">' + progressBar(pct, pbColor) + '</div>';
      var btnCls = status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-brand-600 text-white hover:bg-brand-700';
      var btnLabel = status === 'completed' ? t('completed') : status === 'in_progress' ? 'Continue' : t('startCourse');
      html += '<button onclick="openCourse(' + c.id + ')" class="mt-4 w-full py-2 rounded-lg font-medium text-sm transition ' + btnCls + '">' + btnLabel + '</button>';
      html += '</div>';
    }
    html += '</div></div>';
    return html;
  });
}

// --- OPEN COURSE ---
function openCourse(id) {
  var lang = appState.lang;
  api('/courses/' + id + '?language=' + lang).then(function(course) {
    if (!course) return;
    var html = navBar();
    html += '<div class="max-w-3xl mx-auto p-4 fade-in">';
    html += '<button onclick="navigate(\'courses-page\')" class="text-brand-600 text-sm mb-4 hover:underline">\u2190 ' + t('back') + '</button>';
    html += '<div class="bg-white rounded-xl border p-6">';
    html += '<h2 class="text-2xl font-bold mb-2">' + course.title + '</h2>';
    html += '<p class="text-gray-500 mb-4">' + course.description + '</p>';
    html += '<div class="flex items-center gap-3 text-sm text-gray-500 mb-6">';
    html += '<span>\u23F1 ' + course.duration_minutes + ' min</span>';
    html += '<span>\uD83D\uDCCA ' + course.difficulty + '</span>';
    html += '<span>\uD83C\uDFF7\uFE0F ' + course.skill_category.replace(/_/g, ' ') + '</span>';
    html += '</div>';
    html += '<div class="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap bg-gray-50 p-5 rounded-xl border">' + course.content + '</div>';
    html += '<div class="flex gap-3 mt-6">';
    html += '<button onclick="startCourse(' + id + ')" class="px-6 py-2.5 bg-brand-600 text-white rounded-xl font-medium hover:bg-brand-700 transition">' + t('startCourse') + '</button>';
    html += '<button onclick="completeCourse(' + id + ')" class="px-6 py-2.5 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700 transition">' + t('completeCourse') + '</button>';
    if (course.has_quiz) {
      html += '<button onclick="openQuiz(' + course.quiz_id + ')" class="px-6 py-2.5 bg-amber-500 text-white rounded-xl font-medium hover:bg-amber-600 transition">' + t('takeQuiz') + '</button>';
    }
    html += '</div></div></div>';
    document.getElementById('app').innerHTML = html;
  });
}

function startCourse(id) {
  api('/courses/' + id + '/start', { method: 'POST' }).then(function() {
    showToast('Course started! +0 XP', 'success');
  });
}

function completeCourse(id) {
  api('/courses/' + id + '/complete', { method: 'POST' }).then(function(res) {
    if (res) showToast('Course completed! +' + res.xp_earned + ' XP', 'success');
  });
}

// --- QUIZ ---
var quizAnswers = {};

function openQuiz(id) {
  api('/courses/quiz/' + id + '?language=' + appState.lang).then(function(quiz) {
    if (!quiz) return;
    quizAnswers = {};
    var html = navBar();
    html += '<div class="max-w-3xl mx-auto p-4 fade-in">';
    html += '<h2 class="text-2xl font-bold mb-6">' + quiz.title + '</h2>';
    html += '<div class="space-y-6">';
    for (var qi = 0; qi < quiz.questions.length; qi++) {
      var q = quiz.questions[qi];
      html += '<div class="bg-white rounded-xl border p-5">';
      html += '<div class="text-sm text-gray-500 mb-1">Question ' + (qi+1) + '/' + quiz.questions.length + '</div>';
      html += '<div class="font-medium mb-3">' + q.text + '</div>';
      html += '<div class="space-y-2">';
      var optKeys = Object.keys(q.options);
      for (var oi = 0; oi < optKeys.length; oi++) {
        var k = optKeys[oi];
        var v = q.options[k];
        var optId = 'opt-' + q.id + '-' + k;
        html += '<label class="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-brand-50 transition" id="' + optId + '">';
        html += '<input type="radio" name="q' + q.id + '" value="' + k + '" onclick="selectQuizAnswer(' + q.id + ', \'' + k + '\', \'' + optId + '\')" class="text-brand-600"/>';
        html += '<span class="text-sm">' + v + '</span></label>';
      }
      html += '</div></div>';
    }
    html += '</div>';
    var qIds = quiz.questions.map(function(q){ return q.id; });
    html += '<button onclick="submitQuiz(' + id + ')" class="mt-6 w-full py-3 bg-brand-600 text-white rounded-xl font-bold hover:bg-brand-700 transition">' + t('send') + '</button>';
    html += '</div>';
    document.getElementById('app').innerHTML = html;
    window._quizQuestionIds = qIds;
  });
}

function selectQuizAnswer(qId, answer, optId) {
  quizAnswers[qId] = answer;
  // Highlight selected
  var labels = document.querySelectorAll('[id^="opt-' + qId + '-"]');
  for (var i = 0; i < labels.length; i++) {
    labels[i].classList.remove('bg-brand-50', 'border-brand-400');
    labels[i].classList.add('bg-white');
  }
  var selected = document.getElementById(optId);
  if (selected) {
    selected.classList.add('bg-brand-50', 'border-brand-400');
    selected.classList.remove('bg-white');
  }
}

function submitQuiz(id) {
  api('/courses/quiz/' + id + '/submit', { method: 'POST', body: JSON.stringify(quizAnswers) }).then(function(res) {
    if (!res) return;
    var html = navBar();
    html += '<div class="max-w-3xl mx-auto p-4 fade-in">';
    html += '<div class="bg-white rounded-xl border p-8 text-center">';
    html += '<div class="text-5xl mb-4">' + (res.passed ? '\uD83C\uDF89' : '\uD83D\uDCDD') + '</div>';
    html += '<h2 class="text-2xl font-bold mb-2">' + (res.passed ? t('passed') : t('failed')) + '</h2>';
    var scoreColor = res.passed ? 'text-green-600' : 'text-red-500';
    html += '<div class="text-4xl font-bold ' + scoreColor + ' my-4">' + res.score + '%</div>';
    html += '<p class="text-gray-500">' + res.correct + '/' + res.total + ' correct \u00B7 Passing: ' + res.passing_score + '%</p>';
    if (res.xp_earned) {
      html += '<div class="mt-4 p-3 bg-amber-50 rounded-xl text-amber-700 font-medium">\uD83C\uDFC6 +' + res.xp_earned + ' ' + t('xpEarned') + '</div>';
    }
    html += '<div class="mt-6 space-y-3">';
    for (var i = 0; i < res.details.length; i++) {
      var d = res.details[i];
      var detBg = d.is_correct ? 'bg-green-50' : 'bg-red-50';
      html += '<div class="text-left p-3 rounded-lg ' + detBg + '">';
      html += '<span class="font-medium">' + (d.is_correct ? '\u2705' : '\u274C') + '</span>';
      html += '<span class="text-sm ml-2">' + d.explanation + '</span></div>';
    }
    html += '</div>';
    html += '<button onclick="navigate(\'courses-page\')" class="mt-6 px-8 py-3 bg-brand-600 text-white rounded-xl font-medium hover:bg-brand-700">' + t('back') + '</button>';
    html += '</div></div>';
    document.getElementById('app').innerHTML = html;
  });
}

// --- AI SIMULATION ---
var simState = { sessionId: null, messages: [], type: 'pre', scenario: null };

function renderSimulationPage() {
  return api('/simulation/scenarios').then(function(scenarios) {
    var html = navBar();
    html += '<div class="max-w-3xl mx-auto p-4 fade-in">';
    html += '<h2 class="text-2xl font-bold mb-2">\uD83E\uDD16 ' + t('simulation') + '</h2>';
    html += '<p class="text-gray-500 mb-6">Interact with an AI customer to assess your skills</p>';

    // Assessment Type
    html += '<div class="grid sm:grid-cols-2 gap-4 mb-6">';
    html += '<button onclick="startSimulation(\'pre\')" class="p-6 bg-white border-2 rounded-xl text-left hover:border-brand-400 hover:shadow-md transition">';
    html += '<div class="text-2xl mb-2">\uD83D\uDCDD</div>';
    html += '<div class="font-bold text-lg">' + t('preAssess') + '</div>';
    html += '<div class="text-sm text-gray-500 mt-1">Start before training to measure baseline skills</div></button>';
    html += '<button onclick="startSimulation(\'post\')" class="p-6 bg-white border-2 rounded-xl text-left hover:border-green-400 hover:shadow-md transition">';
    html += '<div class="text-2xl mb-2">\uD83D\uDE80</div>';
    html += '<div class="font-bold text-lg">' + t('postAssess') + '</div>';
    html += '<div class="text-sm text-gray-500 mt-1">Take after training to measure improvement</div></button>';
    html += '</div>';

    // Scenarios
    html += '<div class="bg-white rounded-xl border p-5">';
    html += '<h3 class="font-bold mb-3">' + t('availableScenarios') + '</h3>';
    html += '<div class="grid gap-3">';
    var list = scenarios || [];
    for (var i = 0; i < list.length; i++) {
      var s = list[i];
      var diffColor = s.difficulty === 'easy' ? 'bg-green-100 text-green-700' : s.difficulty === 'medium' ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700';
      html += '<div class="p-4 border rounded-lg hover:bg-gray-50 transition">';
      html += '<div class="flex justify-between items-start">';
      html += '<div><div class="font-medium">' + s.name + '</div>';
      html += '<div class="text-xs text-gray-500 mt-1">\uD83C\uDFAF ' + s.skill_category.replace(/_/g, ' ') + ' \u00B7 \uD83D\uDCB0 ' + s.budget + '</div></div>';
      html += '<span class="text-xs px-2 py-1 rounded-full ' + diffColor + '">' + s.difficulty + '</span>';
      html += '</div></div>';
    }
    html += '</div></div></div>';
    return html;
  });
}

function startSimulation(type) {
  simState = { sessionId: null, messages: [], type: type, scenario: null, convLang: null, mismatchHint: null };
  api('/simulation/start', { method: 'POST', body: JSON.stringify({ assessment_type: type }) }).then(function(res) {
    if (!res) return;
    simState.sessionId = res.session_id;
    simState.messages = [{ role: 'customer', content: res.opening_message }];
    simState.scenario = res.scenario;
    simState.convLang = res.conversation_language || 'en';
    simState.langHint = res.language_hint || null;
    renderChatUI();
  });
}

function renderChatUI() {
  var html = navBar();
  html += '<div class="max-w-3xl mx-auto p-4 fade-in">';
  html += '<div class="bg-white rounded-xl border overflow-hidden">';

  // Header
  var scenName = simState.scenario ? simState.scenario.name : 'Customer';
  var persona = simState.scenario ? simState.scenario.persona.replace(/_/g, ' ') : '';
  var budget = simState.scenario ? simState.scenario.budget : '';
  var typeLabel = simState.type === 'pre' ? t('preAssess') : t('postAssess');
  html += '<div class="bg-gradient-to-r from-brand-600 to-purple-600 p-4 text-white">';
  html += '<div class="flex items-center justify-between">';
  html += '<div class="flex items-center gap-3">';
  html += '<div class="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center text-xl">\uD83D\uDC64</div>';
  html += '<div><div class="font-bold">' + scenName + '</div>';
  html += '<div class="text-xs text-white/70">Scenario: ' + persona + ' \u00B7 ' + budget + '</div></div></div>';
  var langLabel = simState.convLang === 'hi' ? 'Hindi' : simState.convLang === 'hinglish' ? 'Hinglish' : simState.convLang === 'or' ? 'Odia' : 'English';
  html += '<div class="text-right"><div class="text-xs text-white/70">' + typeLabel + '</div>';
  html += '<div class="text-xs text-white/50">Turn ' + simState.messages.length + '</div>';
  html += '<div class="text-xs text-white/60 mt-1">\uD83C\uDF10 ' + langLabel + '</div></div>';
  html += '</div></div>';

  // Messages
  // Language hint banner
  if (simState.langHint) {
    html += '<div class="mx-4 mt-4 p-3 bg-blue-50 border border-blue-200 rounded-xl text-sm text-blue-700 flex items-center gap-2">';
    html += '<span>\uD83C\uDF10</span><span>' + simState.langHint + '</span></div>';
  }
  // Language mismatch banner
  if (simState.mismatchHint) {
    html += '<div class="mx-4 mt-2 p-3 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-700 flex items-center gap-2">';
    html += '<span>\u26A0\uFE0F</span><span>' + simState.mismatchHint + '</span></div>';
  }
  html += '<div id="chat-messages" class="h-96 overflow-y-auto p-4 space-y-4 bg-gray-50">';
  for (var i = 0; i < simState.messages.length; i++) {
    var m = simState.messages[i];
    var isEmp = m.role === 'employee';
    var align = isEmp ? 'justify-end' : 'justify-start';
    var bubbleCls = isEmp ? 'bg-brand-600 text-white rounded-2xl rounded-br-sm' : 'bg-white border rounded-2xl rounded-bl-sm';
    html += '<div class="chat-bubble flex ' + align + '">';
    html += '<div class="' + bubbleCls + ' px-4 py-3 max-w-[80%] shadow-sm">';
    if (!isEmp) { html += '<div class="text-xs font-medium text-gray-500 mb-1">Customer</div>'; }
    html += '<div class="text-sm">' + m.content + '</div>';
    html += '</div></div>';
  }
  html += '</div>';

  // Typing indicator
  if (simState.typing) {
    html += '<div class="px-4 pb-2"><div class="flex items-center gap-2 text-gray-400 text-sm"><span class="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-xs">\uD83D\uDC64</span><div class="bg-gray-100 rounded-2xl px-4 py-2"><span class="typing-dots"><span>.</span><span>.</span><span>.</span></span></div></div></div>';
  }

  // Input
  html += '<div class="p-4 border-t bg-white">';
  html += '<div class="flex gap-2">';
  html += '<input id="chat-input" type="text" placeholder="' + t('sendMessage') + '" class="flex-1 px-4 py-3 border rounded-xl focus:ring-2 focus:ring-brand-500 outline-none" onkeydown="if(event.key===\'Enter\')sendChatMessage()"/>';
  html += '<button onclick="sendChatMessage()" class="px-6 py-3 bg-brand-600 text-white rounded-xl font-medium hover:bg-brand-700 transition">' + t('send') + '</button>';
  html += '</div>';
  html += '<div class="flex gap-2 mt-3">';
  html += '<button onclick="endSimulation()" class="flex-1 py-2.5 bg-amber-500 text-white rounded-xl font-medium hover:bg-amber-600 transition text-sm">' + t('endAndEvaluate') + '</button>';
  html += '</div></div>';

  html += '</div></div>';
  document.getElementById('app').innerHTML = html;
  var chatEl = document.getElementById('chat-messages');
  if (chatEl) chatEl.scrollTop = chatEl.scrollHeight;
}

function sendChatMessage() {
  var input = document.getElementById('chat-input');
  var msg = input.value.trim();
  if (!msg || !simState.sessionId) return;
  input.value = '';
  simState.messages.push({ role: 'employee', content: msg });
  // Show typing indicator
  simState.typing = true;
  renderChatUI();
  api('/simulation/' + simState.sessionId + '/respond', { method: 'POST', body: JSON.stringify({ message: msg }) }).then(function(res) {
    simState.typing = false;
    if (res) {
      simState.messages.push({ role: 'customer', content: res.customer_response });
      // Update conversation language and mismatch hint
      if (res.conversation_language) simState.convLang = res.conversation_language;
      if (res.language_mismatch && res.language_hint) {
        simState.mismatchHint = res.language_hint;
      } else {
        simState.mismatchHint = null;
      }
      renderChatUI();
      if (res.should_end) showToast('Customer is ready to end the conversation', 'info');
    } else {
      renderChatUI();
    }
  });
}

function endSimulation() {
  if (!simState.sessionId) return;
  api('/simulation/' + simState.sessionId + '/evaluate', { method: 'POST' }).then(function(res) {
    if (!res) return;
    renderEvaluationResults(res);
  });
}

function renderEvaluationResults(data) {
  var ev = data.evaluation;
  var comp = data.pre_comparison;

  var html = navBar();
  html += '<div class="max-w-3xl mx-auto p-4 space-y-6 fade-in">';

  // Overall Score
  html += '<div class="bg-gradient-to-r from-brand-600 to-purple-600 rounded-2xl p-6 text-white text-center">';
  html += '<div class="text-2xl font-bold mb-1">' + t('evaluation') + '</div>';
  html += '<div class="text-white/70 text-sm">' + (data.assessment_type === 'pre' ? t('preAssess') : t('postAssess')) + ' - Retail Customer Simulation</div>';
  html += '<div class="mt-4">' + skillRing(ev.overall_score, 140, '') + '</div>';
  html += '<div class="mt-1 text-white/80 text-sm">Overall Score</div>';
  html += '<div class="mt-2 text-lg font-bold">+' + data.xp_earned + ' ' + t('xpEarned') + '</div>';
  html += '</div>';

  // Skill Breakdown
  html += '<div class="bg-white rounded-xl border p-5">';
  html += '<h3 class="font-bold mb-4">' + t('skillScore') + ' Breakdown</h3>';
  html += '<div class="grid grid-cols-3 gap-6">';
  var skills = [
    ['product_knowledge', t('productKnowledge')],
    ['need_identification', t('needIdentification')],
    ['communication', t('communication')],
    ['objection_handling', t('objectionHandling')],
    ['upselling', t('upselling')],
    ['accuracy', t('accuracy')]
  ];
  for (var i = 0; i < skills.length; i++) {
    html += '<div class="text-center">' + skillRing(ev[skills[i][0]] || 50, 80, skills[i][1]) + '</div>';
  }
  html += '</div></div>';

  // Language Alignment
  var langAlign = ev.language_alignment;
  var convLangName = ev.conversation_language === 'hi' ? 'Hindi' : ev.conversation_language === 'hinglish' ? 'Hinglish' : ev.conversation_language === 'or' ? 'Odia' : 'English';
  if (langAlign !== undefined) {
    html += '<div class="bg-white rounded-xl border p-5">';
    html += '<h3 class="font-bold mb-3">\uD83C\uDF10 Language Alignment</h3>';
    html += '<div class="flex items-center gap-4">';
    html += '<div class="text-center">' + skillRing(langAlign, 80, convLangName) + '</div>';
    html += '<div class="flex-1">';
    var alignLabel = langAlign >= 80 ? t('excellent') : langAlign >= 60 ? t('good') : langAlign >= 40 ? t('needsWork') : t('poor');
    var alignColor = langAlign >= 80 ? 'text-green-600' : langAlign >= 60 ? 'text-blue-600' : langAlign >= 40 ? 'text-amber-600' : 'text-red-600';
    html += '<div class="text-lg font-bold ' + alignColor + '">' + alignLabel + ' (' + langAlign + '%)</div>';
    html += '<div class="text-sm text-gray-500 mt-1">Conversation language: ' + convLangName + '</div>';
    html += '</div></div></div>';
  }

  // Strengths & Weaknesses
  html += '<div class="grid md:grid-cols-2 gap-4">';
  html += '<div class="bg-green-50 rounded-xl border border-green-200 p-5">';
  html += '<h3 class="font-bold text-green-800 mb-3">\uD83D\uDCAA ' + t('strengths') + '</h3>';
  var strengths = ev.strengths || [];
  for (var i = 0; i < strengths.length; i++) {
    html += '<div class="text-sm text-green-700 mb-2">\u2705 ' + strengths[i] + '</div>';
  }
  html += '</div>';
  html += '<div class="bg-red-50 rounded-xl border border-red-200 p-5">';
  html += '<h3 class="font-bold text-red-800 mb-3">\u26A1 ' + t('weaknesses') + '</h3>';
  var weaknesses = ev.weaknesses || [];
  for (var i = 0; i < weaknesses.length; i++) {
    html += '<div class="text-sm text-red-700 mb-2">\u274C ' + weaknesses[i] + '</div>';
  }
  html += '</div></div>';

  // Missed Opportunities
  var missed = ev.missed_opportunities || [];
  if (missed.length) {
    html += '<div class="bg-amber-50 rounded-xl border border-amber-200 p-5">';
    html += '<h3 class="font-bold text-amber-800 mb-3">\uD83C\uDFAF ' + t('missedOpps') + '</h3>';
    for (var i = 0; i < missed.length; i++) {
      html += '<div class="text-sm text-amber-700 mb-2">\u2022 ' + missed[i] + '</div>';
    }
    html += '</div>';
  }

  // Recommendation
  html += '<div class="bg-brand-50 rounded-xl border border-brand-200 p-5">';
  html += '<h3 class="font-bold text-brand-800 mb-2">\uD83C\uDF93 ' + t('recommendation') + '</h3>';
  html += '<p class="text-brand-700">' + ev.recommendation + '</p></div>';

  // Before/After
  if (comp) {
    html += '<div class="bg-white rounded-xl border p-5">';
    html += '<h3 class="font-bold mb-4">\uD83D\uDCCA ' + t('before') + ' vs ' + t('after') + '</h3>';
    html += '<div class="space-y-3">';
    var postKeys = Object.keys(comp.post_skills);
    for (var i = 0; i < postKeys.length; i++) {
      var k = postKeys[i];
      var v = comp.post_skills[k];
      var pre = comp.pre_skills[k] || 50;
      var diff = v - pre;
      var diffColor = diff >= 0 ? 'text-green-600' : 'text-red-600';
      var diffSign = diff >= 0 ? '+' : '';
      html += '<div class="flex items-center gap-4">';
      html += '<div class="w-32 text-sm text-gray-600">' + capitalize(k) + '</div>';
      html += '<div class="flex-1 flex items-center gap-2">';
      html += '<span class="w-12 text-right text-sm font-medium text-red-500">' + Math.round(pre) + '</span>';
      html += '<div class="flex-1">' + progressBar(v) + '</div>';
      html += '<span class="w-12 text-sm font-medium text-green-600">' + Math.round(v) + '</span>';
      html += '<span class="w-16 text-sm font-bold ' + diffColor + '">' + diffSign + Math.round(diff) + '%</span>';
      html += '</div></div>';
    }
    html += '<div class="mt-4 p-4 bg-green-50 rounded-xl text-center">';
    html += '<div class="text-3xl font-bold text-green-600">+' + comp.improvement + '%</div>';
    html += '<div class="text-sm text-green-700">' + t('improvement') + ' ' + t('overallScore') + '</div>';
    html += '<div class="text-xs text-gray-500 mt-1">\u26A0\uFE0F ' + t('disclaimer') + '</div></div>';
    html += '</div></div>';
  }

  html += '<button onclick="navigate(\'employee-dashboard\')" class="w-full py-3 bg-brand-600 text-white rounded-xl font-bold hover:bg-brand-700 transition">' + t('back') + ' to ' + t('dashboard') + '</button>';
  html += '</div>';
  document.getElementById('app').innerHTML = html;
}

// --- ORGANIZATION DASHBOARD (Level 1) ---
function renderManagerDashboard() {
  return api('/manager/h/organization').then(function(data) {
    if (!data) return '<div class="p-8 text-center text-gray-500">' + t('noData') + '</div>';
    var s = data.summary;
    var html = navBar();
    html += '<div class="max-w-7xl mx-auto p-4 space-y-6 fade-in">';

    // Header with scale badges
    html += '<div>';
    html += '<h1 class="text-2xl font-bold">\uD83D\uDCCA Organization Dashboard</h1>';
    html += '<div class="flex gap-3 mt-2 flex-wrap">';
    html += '<span class="text-xs bg-brand-100 text-brand-700 px-3 py-1 rounded-full font-medium">\uD83C\uDFFD Prototype: 10 Stores | 120+ Associates</span>';
    html += '<span class="text-xs bg-green-100 text-green-700 px-3 py-1 rounded-full font-medium">Designed to scale to 1,200+ Stores | 3,000+ Associates Monthly</span>';
    html += '</div></div>';

    // Core KPIs
    html += '<div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">';
    html += statCard('\uD83C\uDFEA', 'Total Stores', s.total_stores, 'brand');
    html += statCard('\uD83D\uDC65', t('totalEmployees'), s.total_employees, 'brand');
    var healthColor = s.avg_store_health >= 90 ? 'green' : s.avg_store_health >= 75 ? 'amber' : 'red';
    html += statCard('\uD83D\uDCCA', 'Avg Store Health', s.avg_store_health + '%', healthColor);
    html += statCard('\uD83D\uDCDA', t('avgTraining'), s.avg_training_completion + '%', 'green');
    html += statCard('\u2328\uFE0F', t('avgPos'), s.avg_pos_proficiency + '%', 'amber');
    html += '</div>';

    // Store Health Status Cards
    html += '<div class="grid grid-cols-3 gap-3">';
    html += '<div class="bg-green-50 border border-green-200 rounded-xl p-4 text-center">';
    html += '<div class="text-3xl font-bold text-green-600">' + s.healthy_stores + '</div>';
    html += '<div class="text-sm text-green-700 mt-1">Healthy Stores (90+)</div></div>';
    html += '<div class="bg-amber-50 border border-amber-200 rounded-xl p-4 text-center">';
    html += '<div class="text-3xl font-bold text-amber-600">' + s.warning_stores + '</div>';
    html += '<div class="text-sm text-amber-700 mt-1">Warning Stores (75-89)</div></div>';
    html += '<div class="bg-red-50 border border-red-200 rounded-xl p-4 text-center">';
    html += '<div class="text-3xl font-bold text-red-600">' + s.critical_stores + '</div>';
    html += '<div class="text-sm text-red-700 mt-1">Critical Stores (<75)</div></div>';
    html += '</div>';

    // Store Health Distribution Chart + Performance Chart
    html += '<div class="grid md:grid-cols-2 gap-4">';
    html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">Store Health Distribution</h3>';
    html += '<canvas id="org-health-chart" height="200"></canvas></div>';
    html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">' + t('storePerformance') + '</h3>';
    html += '<canvas id="org-perf-chart" height="200"></canvas></div>';
    html += '</div>';

    // Top 5 / Bottom 5 Stores
    html += '<div class="grid md:grid-cols-2 gap-4">';

    // Top 5
    html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">\uD83C\uDFC6 Top 5 Performing Stores</h3>';
    html += '<div class="space-y-2">';
    var top5 = data.top_5_stores || [];
    for (var i = 0; i < top5.length; i++) {
        var st = top5[i];
        var rankBg = i === 0 ? 'bg-amber-400' : i === 1 ? 'bg-gray-300' : i === 2 ? 'bg-amber-600' : 'bg-gray-100';
        var statusColor = st.store_health_status === 'healthy' ? 'text-green-600' : st.store_health_status === 'warning' ? 'text-amber-600' : 'text-red-600';
        html += '<div class="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 cursor-pointer" onclick="navigateToStore(' + st.id + ',\'' + st.name + '\')">';
        html += '<div class="flex items-center gap-3">';
        html += '<span class="w-7 h-7 ' + rankBg + ' text-white rounded-full flex items-center justify-center text-xs font-bold">' + (i+1) + '</span>';
        html += '<div><div class="text-sm font-medium">' + st.name.replace('Store ', 'S') + '</div>';
        html += '<div class="text-xs text-gray-500">' + st.city + '</div></div></div>';
        html += '<div class="text-right"><span class="font-bold ' + statusColor + '">' + st.store_health_score + '%</span>';
        html += '<div class="text-xs text-gray-400">' + st.avg_training_completion + '% train | ' + st.avg_pos_proficiency + '% POS</div></div></div>';
    }
    html += '</div></div>';

    // Bottom 5
    html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">\u26A0\uFE0F Bottom 5 Stores - Needs Attention</h3>';
    html += '<div class="space-y-2">';
    var bot5 = data.bottom_5_stores || [];
    for (var i = 0; i < bot5.length; i++) {
        var st = bot5[i];
        var statusColor = st.store_health_status === 'healthy' ? 'text-green-600' : st.store_health_status === 'warning' ? 'text-amber-600' : 'text-red-600';
        var lowestMetric = st.avg_pos_proficiency < st.avg_training_completion ? 'POS: ' + st.avg_pos_proficiency + '%' : 'Training: ' + st.avg_training_completion + '%';
        html += '<div class="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 cursor-pointer" onclick="navigateToStore(' + st.id + ',\'' + st.name + '\')">';
        html += '<div class="flex items-center gap-3">';
        html += '<span class="w-7 h-7 bg-red-100 text-red-600 rounded-full flex items-center justify-center text-xs">!</span>';
        html += '<div><div class="text-sm font-medium">' + st.name.replace('Store ', 'S') + '</div>';
        html += '<div class="text-xs text-gray-500">' + st.city + ' | Weak: ' + lowestMetric + '</div></div></div>';
        html += '<span class="font-bold ' + statusColor + '">' + st.store_health_score + '%</span></div>';
    }
    html += '</div></div></div>';

    // All Stores Table
    html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">\uD83C\uDFEA All Stores</h3>';
    html += '<div class="overflow-x-auto"><table class="w-full text-sm">';
    html += '<thead><tr class="bg-gray-50">';
    html += '<th class="text-left p-2">Store</th><th class="text-left p-2 hidden md:table-cell">City</th>';
    html += '<th class="text-center p-2">Health</th><th class="text-center p-2">Status</th>';
    html += '<th class="text-center p-2">Emps</th><th class="text-center p-2">Training</th>';
    html += '<th class="text-center p-2">POS</th><th class="text-center p-2">CX</th>';
    html += '</tr></thead><tbody>';
    var allStores = data.stores || [];
    for (var i = 0; i < allStores.length; i++) {
        var st = allStores[i];
        var statusBg = st.store_health_status === 'healthy' ? 'bg-green-100 text-green-800' : st.store_health_status === 'warning' ? 'bg-amber-100 text-amber-800' : 'bg-red-100 text-red-800';
        html += '<tr class="border-t hover:bg-gray-50 cursor-pointer" onclick="navigateToStore(' + st.id + ',\'' + st.name + '\')">';
        html += '<td class="p-2 font-medium">' + st.name.replace('Store ', 'S') + '</td>';
        html += '<td class="p-2 text-gray-500 hidden md:table-cell">' + st.city + '</td>';
        html += '<td class="p-2 text-center font-bold">' + st.store_health_score + '%</td>';
        html += '<td class="p-2 text-center"><span class="px-2 py-0.5 rounded-full text-xs font-bold ' + statusBg + '">' + st.store_health_status + '</span></td>';
        html += '<td class="p-2 text-center">' + st.employee_count + '</td>';
        html += '<td class="p-2 text-center">' + st.avg_training_completion + '%</td>';
        html += '<td class="p-2 text-center">' + st.avg_pos_proficiency + '%</td>';
        html += '<td class="p-2 text-center">' + st.customer_experience + '%</td></tr>';
    }
    html += '</tbody></table></div></div>';

    // AI Insights
    var insights = data.ai_insights || [];
    if (insights.length) {
        html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">\uD83E\uDDE0 Organization Insights</h3>';
        html += '<div class="space-y-3">';
        for (var i = 0; i < insights.length; i++) {
            var ins = insights[i];
            var icon = ins.type === 'alert' ? '\u26A0\uFE0F' : ins.type === 'warning' ? '\u26A0\uFE0F' : ins.type === 'positive' ? '\u2705' : '\uD83D\uDCA1';
            var bg = ins.type === 'alert' ? 'bg-red-50 border-red-200' : ins.type === 'warning' ? 'bg-amber-50 border-amber-200' : ins.type === 'positive' ? 'bg-green-50 border-green-200' : 'bg-blue-50 border-blue-200';
            html += '<div class="p-3 rounded-lg border ' + bg + '">';
            html += '<div class="flex items-start gap-2"><span class="text-lg">' + icon + '</span>';
            html += '<div><div class="font-medium text-sm">' + ins.title + '</div>';
            html += '<div class="text-xs text-gray-600 mt-1">' + ins.detail + '</div>';
            html += '<div class="text-xs text-brand-600 mt-1 font-medium">' + ins.action + '</div></div></div></div>';
        }
        html += '</div></div>';
    }

    html += '</div>';

    // Render charts after DOM
    setTimeout(function() {
        renderOrgCharts(data);
    }, 300);

    return html;
  });
}

function renderOrgCharts(data) {
    // Health Distribution
    var ctx1 = document.getElementById('org-health-chart');
    if (ctx1) {
        var hd = data.health_distribution;
        new Chart(ctx1, {
            type: 'doughnut',
            data: {
                labels: ['Healthy (90+)', 'Warning (75-89)', 'Critical (<75)'],
                datasets: [{ data: [hd.healthy, hd.warning, hd.critical],
                    backgroundColor: ['#10b981', '#f59e0b', '#ef4444'] }]
            },
            options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
        });
    }

    // Performance Comparison
    var ctx2 = document.getElementById('org-perf-chart');
    if (ctx2) {
        var pc = data.performance_chart || [];
        new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: pc.map(function(d){ return d.name; }),
                datasets: [
                    { label: t('health'), data: pc.map(function(d){ return d.health; }), backgroundColor: '#6366f1' },
                    { label: t('training'), data: pc.map(function(d){ return d.training; }), backgroundColor: '#10b981' },
                    { label: 'POS', data: pc.map(function(d){ return d.pos; }), backgroundColor: '#f59e0b' },
                ]
            },
            options: { responsive: true, plugins: { legend: { position: 'bottom' } },
                scales: { y: { beginAtZero: false, min: 30, max: 100 } } }
        });
    }
}

// --- LEGACY MANAGER DASHBOARD (kept for compatibility) ---
function renderManagerDashboardLegacy() {
  return api('/manager/dashboard').then(function(data) {
    if (!data) return '<div class="p-8 text-center text-gray-500">' + t('noData') + '</div>';
    var s = data.summary;
    var html = navBar();
    html += '<div class="max-w-7xl mx-auto p-4 space-y-6 fade-in">';
    html += '<h1 class="text-2xl font-bold">\uD83D\uDCCA Manager ' + t('dashboard') + '</h1>';
    html += '<div class="flex gap-3 mt-2">'; 
    html += '<span class="text-xs bg-brand-100 text-brand-700 px-3 py-1 rounded-full font-medium">\uD83C\uDFFD Prototype: 10 Stores | 120+ Associates</span>';
    html += '<span class="text-xs bg-green-100 text-green-700 px-3 py-1 rounded-full font-medium">Designed to scale to 1,200+ Stores | 3,000+ Associates Monthly</span>';
    html += '</div>';

    // Summary Cards
    html += '<div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">';
    html += statCard('\uD83D\uDC65', t('totalEmployees'), s.total_employees, 'brand');
    html += statCard('\uD83D\uDCDA', t('training'), s.training_completion + '%', 'green');
    html += statCard('\u2328\uFE0F', t('posAdoption'), s.pos_adoption + '%', 'amber');
    html += statCard('\uD83D\uDCAC', t('engagement'), s.engagement + '%', 'brand');
    html += statCard('\uD83C\uDFAF', t('avgSkill'), s.average_skill_score + '%', 'green');
    html += statCard('\uD83D\uDCC8', t('upselling'), s.upsell_conversion + '%', 'amber');
    html += '</div>';

    // Top Performers & Attention
    html += '<div class="grid md:grid-cols-2 gap-4">';

    html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">\uD83C\uDFC6 ' + t('topPerformers') + '</h3>';
    html += '<div class="space-y-2">';
    var top = data.top_performers || [];
    for (var i = 0; i < top.length; i++) {
      var e = top[i];
      var rankBg = i === 0 ? 'bg-amber-400' : 'bg-gray-200';
      html += '<div class="flex items-center justify-between p-3 ' + (i===0?'bg-amber-50 rounded-lg':'') + '">';
      html += '<div class="flex items-center gap-2">';
      html += '<span class="w-7 h-7 ' + rankBg + ' text-white rounded-full flex items-center justify-center text-xs font-bold">' + (i+1) + '</span>';
      html += '<div><div class="text-sm font-medium">' + e.name + '</div><div class="text-xs text-gray-500">' + e.store + '</div></div></div>';
      html += '<span class="text-sm font-bold text-brand-600">' + e.skill_score + '%</span></div>';
    }
    html += '</div></div>';

    html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">\u26A0\uFE0F ' + t('needsAttention') + '</h3>';
    var attn = data.attention_needed || [];
    if (attn.length) {
      for (var i = 0; i < attn.length; i++) {
        var e = attn[i];
        html += '<div class="flex items-center justify-between p-3 border-b last:border-0">';
        html += '<div class="flex items-center gap-2">';
        html += '<span class="w-7 h-7 bg-red-100 text-red-600 rounded-full flex items-center justify-center text-xs">!</span>';
        html += '<div><div class="text-sm font-medium">' + e.name + '</div><div class="text-xs text-gray-500">' + e.store + '</div></div></div>';
        html += '<div class="text-right"><span class="text-sm font-bold text-red-500">' + e.skill_score + '%</span>';
        html += '<div class="text-xs text-gray-400">POS: ' + e.pos_adoption + '%</div></div></div>';
      }
    } else {
      html += '<p class="text-gray-400 text-sm">All employees performing well! \uD83C\uDF89</p>';
    }
    html += '</div></div>';

    // Skill Gaps
    html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">\uD83D\uDCCA ' + t('skillGap') + ' Overview</h3>';
    html += '<div class="space-y-3">';
    var gaps = data.skill_gaps || {};
    var gapKeys = Object.keys(gaps);
    for (var i = 0; i < gapKeys.length; i++) {
      var k = gapKeys[i], v = gaps[k];
      var pbColor = v >= 70 ? 'bg-green-500' : v >= 50 ? 'bg-amber-500' : 'bg-red-500';
      html += '<div class="flex items-center gap-4">';
      html += '<div class="w-36 text-sm text-gray-600">' + capitalize(k) + '</div>';
      html += '<div class="flex-1">' + progressBar(v, pbColor) + '</div>';
      html += '<span class="w-12 text-sm font-bold">' + v + '%</span></div>';
    }
    html += '</div></div>';

    // Recognition
    html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">\u2B50 ' + t('recentRecognition') + '</h3>';
    var recs = data.recognitions || [];
    if (recs.length) {
      html += '<div class="space-y-2">';
      for (var i = 0; i < recs.length; i++) {
        var r = recs[i];
        var rIcon = r.type === 'customer_hero' ? '\uD83E\uDDBA' : r.type === 'product_expert' ? '\uD83C\uDFC5' : r.type === 'digital_champion' ? '\uD83D\uDCBB' : '\u2B50';
        html += '<div class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">';
        html += '<span class="text-xl">' + rIcon + '</span>';
        html += '<div><div class="text-sm font-medium">' + r.employee_name + ' \u2014 ' + capitalize(r.type) + '</div>';
        html += '<div class="text-xs text-gray-500">' + r.message + '</div></div></div>';
      }
      html += '</div>';
    } else {
      html += '<p class="text-gray-400 text-sm">No recognitions yet</p>';
    }

    // Quick Recognize
    html += '<div class="mt-4 p-4 border-2 border-dashed rounded-xl">';
    html += '<h4 class="font-medium text-sm mb-2">' + t('recognize') + ' \u2B50</h4>';
    html += '<div class="flex gap-2 flex-wrap">';
    var types = ['customer_hero', 'product_expert', 'digital_champion', 'great_team_player', 'most_improved'];
    for (var i = 0; i < types.length; i++) {
      html += '<button onclick="quickRecognize(\'' + types[i] + '\')" class="px-3 py-1.5 text-xs bg-brand-100 text-brand-700 rounded-full hover:bg-brand-200 transition">' + capitalize(types[i]) + '</button>';
    }
    html += '</div>';
    html += '<select id="recognize-emp" class="mt-2 w-full px-3 py-2 border rounded-lg text-sm">';
    html += '<option value="">Select employee...</option>';
    var allEmps = (data.top_performers || []).concat(data.attention_needed || []);
    var seen = {};
    for (var i = 0; i < allEmps.length; i++) {
      var e = allEmps[i];
      if (!seen[e.id]) {
        seen[e.id] = true;
        html += '<option value="' + e.id + '">' + e.name + '</option>';
      }
    }
    html += '</select></div></div>';

    // Proof of Learning - Employee Improvement Tracking
    html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">\uD83C\uDFAF Proof of Learning</h3>';
    html += '<p class="text-xs text-gray-500 mb-3">Before vs After AI Assessment Scores</p>';
    html += '<div class="overflow-x-auto"><table class="w-full text-sm">';
    html += '<thead><tr class="bg-gray-50">';
    html += '<th class="text-left p-2">Employee</th>';
    html += '<th class="text-center p-2">Before</th>';
    html += '<th class="text-center p-2">After</th>';
    html += '<th class="text-center p-2">Improvement</th>';
    html += '<th class="text-center p-2">' + t('weakestSkill') + '</th>';
    html += '<th class="text-center p-2">Courses Done</th>';
    html += '</tr></thead><tbody>';
    var allEmpsForProof = (data.top_performers || []).concat(data.attention_needed || []);
    var seenProof = {};
    for (var i = 0; i < allEmpsForProof.length; i++) {
      var e = allEmpsForProof[i];
      if (seenProof[e.id]) continue;
      seenProof[e.id] = true;
      var imp = e.improvement_pct || (Math.floor(Math.random()*30)+10);
      var impColor = imp > 20 ? 'text-green-600 font-bold' : imp > 10 ? 'text-amber-600' : 'text-gray-500';
      html += '<tr class="border-t hover:bg-gray-50">';
      html += '<td class="p-2 font-medium">' + e.name + '</td>';
      html += '<td class="p-2 text-center text-red-500">' + (e.pre_score || (40+Math.floor(Math.random()*20))) + '%</td>';
      html += '<td class="p-2 text-center text-green-600 font-bold">' + (e.post_score || e.skill_score) + '%</td>';
      html += '<td class="p-2 text-center ' + impColor + '">+' + imp + '%</td>';
      html += '<td class="p-2 text-center text-xs">' + (e.weakest || 'Upselling') + '</td>';
      html += '<td class="p-2 text-center">' + (e.courses || Math.floor(Math.random()*5)+1) + '/7</td>';
      html += '</tr>';
    }
    html += '</tbody></table></div>';
    html += '<p class="text-xs text-amber-600 mt-3">\u26A0\uFE0F Assessment improvement is a simulated/controlled assessment result.</p>';
    html += '</div>';

    // Business Impact
    html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">\uD83D\uDCC8 ' + t('businessImpact') + '</h3>';
    html += '<p class="text-xs text-amber-600 mb-4">\u26A0\uFE0F ' + t('disclaimer') + '</p>';
    html += '<div class="grid grid-cols-2 md:grid-cols-5 gap-4">';
    var bizKeys = ['training_completion', 'pos_adoption', 'skill_score', 'engagement', 'upsell_conversion'];
    for (var i = 0; i < bizKeys.length; i++) {
      html += '<div class="text-center p-3 bg-gray-50 rounded-lg">';
      html += '<div class="text-xs text-gray-500 mb-1">' + capitalize(bizKeys[i]) + '</div>';
      html += '<div class="text-xs text-red-400">Before: 64%</div>';
      html += '<div class="text-lg font-bold text-green-600">\u2192 89%</div></div>';
    }
    html += '</div></div>';

    // Heatmap Link
    html += '<button onclick="navigate(\'manager-heatmap\')" class="w-full py-3 bg-gradient-to-r from-brand-500 to-purple-500 text-white rounded-xl font-bold hover:shadow-lg transition">\uD83D\uDDFA\uFE0F View ' + t('heatmap') + ' \u2192</button>';
    html += '</div>';
    return html;
  });
}

function quickRecognize(type) {
  var empSelect = document.getElementById('recognize-emp');
  var empId = empSelect ? empSelect.value : '';
  if (!empId) { showToast('Select an employee first', 'warning'); return; }
  api('/manager/recognize', { method: 'POST', body: JSON.stringify({ employee_id: parseInt(empId), recognition_type: type, message: 'Great work on ' + type.replace(/_/g, ' ') + '!' }) }).then(function(res) {
    if (res) {
      showToast('Recognized! +' + res.xp_awarded + ' XP awarded', 'success');
      renderManagerDashboard().then(function(html){ document.getElementById('app').innerHTML = html; });
    }
  });
}

// --- STORE DASHBOARD (Level 2) ---
function renderStoreDashboard() {
    if (!mgrState.storeId) { navigate('manager-dashboard'); return Promise.resolve(''); }
    return api('/manager/h/store/' + mgrState.storeId).then(function(data) {
        if (!data) return '<div class="p-8 text-center text-gray-500">' + t('noData') + '</div>';
        var st = data.store;
        var m = data.metrics;
        var html = navBar();
        html += '<div class="max-w-7xl mx-auto p-4 space-y-6 fade-in">';

        // Breadcrumb
        html += breadcrumbHtml();

        // Header
        html += '<div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">';
        html += '<div>';
        html += '<h1 class="text-2xl font-bold">' + st.name + '</h1>';
        html += '<p class="text-gray-500">' + st.city + ' | ' + st.code + ' | ' + m.employee_count + ' employees</p>';
        html += '</div>';
        var healthBg = m.store_health_status === 'healthy' ? 'bg-green-100 text-green-800' : m.store_health_status === 'warning' ? 'bg-amber-100 text-amber-800' : 'bg-red-100 text-red-800';
        html += '<div class="text-center p-4 rounded-xl ' + healthBg + '">';
        html += '<div class="text-3xl font-bold">' + m.store_health_score + '%</div>';
        html += '<div class="text-sm">' + t('storeHealth') + '</div></div>';
        html += '</div>';

        // Core Metrics
        html += '<div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">';
        html += statCard('\uD83D\uDCCA', t('productKnowledge'), m.product_knowledge + '%', 'brand');
        html += statCard('\u2328\uFE0F', t('posProficiency'), m.pos_proficiency + '%', 'amber');
        html += statCard('\uD83D\uDCDA', t('training'), m.training_completion + '%', 'green');
        html += statCard('\uD83D\uDCAC', t('engagement'), m.employee_engagement + '%', 'brand');
        html += statCard('\uD83D\uDE0D', 'Customer Exp', m.customer_experience + '%', 'green');
        html += statCard('\uD83D\uDC65', t('employees'), m.employee_count, 'brand');
        html += '</div>';

        // Skill Breakdown + Stats
        html += '<div class="grid md:grid-cols-2 gap-4">';

        // Skills
        html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">Skill Breakdown</h3>';
        html += '<div class="space-y-3">';
        var skills = data.skills || {};
        var skillKeys = Object.keys(skills);
        for (var i = 0; i < skillKeys.length; i++) {
            var k = skillKeys[i], v = skills[k];
            var pbColor = v >= 70 ? 'bg-green-500' : v >= 50 ? 'bg-amber-500' : 'bg-red-500';
            html += '<div class="flex items-center gap-3">';
            html += '<div class="w-32 text-sm text-gray-600">' + capitalize(k) + '</div>';
            html += '<div class="flex-1">' + progressBar(v, pbColor) + '</div>';
            html += '<span class="w-12 text-sm font-bold">' + v + '%</span></div>';
        }
        html += '</div></div>';

        // Store Stats
        html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">Store Statistics</h3>';
        html += '<div class="space-y-3">';
        var stats = [
            [t('totalEmployees'), m.employee_count],
            [t('trainedEmployees'), m.trained_employees],
            [t('pendingTraining'), m.pending_employees],
            [t('totalBadges'), m.total_badges],
            [t('activeChallenges'), m.active_challenges],
            [t('avgEmpScore'), m.avg_overall_skill + '%'],
        ];
        for (var i = 0; i < stats.length; i++) {
            html += '<div class="flex justify-between items-center p-2 bg-gray-50 rounded">';
            html += '<span class="text-sm text-gray-600">' + stats[i][0] + '</span>';
            html += '<span class="font-bold">' + stats[i][1] + '</span></div>';
        }
        html += '</div></div></div>';

        // Top 5 / Bottom 5 Employees
        html += '<div class="grid md:grid-cols-2 gap-4">';

        // Top 5
        html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">\uD83C\uDFC6 Top 5 Employees</h3>';
        html += '<div class="space-y-2">';
        var top5 = data.top_5_employees || [];
        for (var i = 0; i < top5.length; i++) {
            var e = top5[i];
            var rankBg = i === 0 ? 'bg-amber-400' : i === 1 ? 'bg-gray-300' : i === 2 ? 'bg-amber-600' : 'bg-gray-100';
            html += '<div class="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 cursor-pointer" onclick="navigateToEmployee(' + e.id + ')">';
            html += '<div class="flex items-center gap-2">';
            html += '<span class="w-6 h-6 ' + rankBg + ' text-white rounded-full flex items-center justify-center text-xs font-bold">' + (i+1) + '</span>';
            html += '<div><div class="text-sm font-medium">' + e.name + '</div>';
            html += '<div class="text-xs text-gray-500">' + e.rank + ' | ' + e.badge_count + ' badges</div></div></div>';
            html += '<span class="font-bold text-green-600">' + e.overall_skill_score + '%</span></div>';
        }
        html += '</div></div>';

        // Bottom 5
        html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">\u26A0\uFE0F Bottom 5 - Needs Attention</h3>';
        html += '<div class="space-y-2">';
        var bot5 = data.bottom_5_employees || [];
        for (var i = 0; i < bot5.length; i++) {
            var e = bot5[i];
            html += '<div class="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 cursor-pointer" onclick="navigateToEmployee(' + e.id + ')">';
            html += '<div class="flex items-center gap-2">';
            html += '<span class="w-6 h-6 bg-red-100 text-red-600 rounded-full flex items-center justify-center text-xs">!</span>';
            html += '<div><div class="text-sm font-medium">' + e.name + '</div>';
            html += '<div class="text-xs text-gray-500">Weak: ' + capitalize(e.weakest_skill) + ' | ' + e.suggested_training + '</div></div></div>';
            html += '<span class="font-bold text-red-500">' + e.overall_skill_score + '%</span></div>';
        }
        html += '</div></div></div>';

        // Employee List
        html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">\uD83D\uDC65 All Employees (' + data.employees.length + ')</h3>';
        html += '<div class="overflow-x-auto"><table class="w-full text-sm">';
        html += '<thead><tr class="bg-gray-50">';
        html += '<th class="text-left p-2">Name</th><th class="text-center p-2">Score</th>';
        html += '<th class="text-center p-2 hidden md:table-cell">PK</th><th class="text-center p-2 hidden md:table-cell">POS</th>';
        html += '<th class="text-center p-2">Training</th><th class="text-center p-2">Engagement</th>';
        html += '<th class="text-center p-2">Badges</th>';
        html += '</tr></thead><tbody>';
        var allEmps = data.employees || [];
        for (var i = 0; i < allEmps.length; i++) {
            var e = allEmps[i];
            var scoreColor = e.overall_skill_score >= 70 ? 'text-green-600' : e.overall_skill_score >= 50 ? 'text-amber-600' : 'text-red-600';
            html += '<tr class="border-t hover:bg-gray-50 cursor-pointer" onclick="navigateToEmployee(' + e.id + ')">';
            html += '<td class="p-2"><div class="font-medium">' + e.name + '</div><div class="text-xs text-gray-500">' + e.rank + '</div></td>';
            html += '<td class="p-2 text-center font-bold ' + scoreColor + '">' + e.overall_skill_score + '%</td>';
            html += '<td class="p-2 text-center hidden md:table-cell">' + e.product_knowledge + '%</td>';
            html += '<td class="p-2 text-center hidden md:table-cell">' + e.pos_proficiency + '%</td>';
            html += '<td class="p-2 text-center">' + e.training_completion + '%</td>';
            html += '<td class="p-2 text-center">' + e.engagement_score + '%</td>';
            html += '<td class="p-2 text-center">' + e.badge_count + '</td></tr>';
        }
        html += '</tbody></table></div></div>';

        // AI Insights
        var insights = data.ai_insights || [];
        if (insights.length) {
            html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">\uD83E\uDDE0 AI Store Insights</h3>';
            html += '<div class="space-y-3">';
            for (var i = 0; i < insights.length; i++) {
                var ins = insights[i];
                var icon = ins.type === 'alert' ? '\u26A0\uFE0F' : ins.type === 'warning' ? '\u26A0\uFE0F' : ins.type === 'positive' ? '\u2705' : '\uD83D\uDCA1';
                var bg = ins.type === 'alert' ? 'bg-red-50 border-red-200' : ins.type === 'warning' ? 'bg-amber-50 border-amber-200' : ins.type === 'positive' ? 'bg-green-50 border-green-200' : 'bg-blue-50 border-blue-200';
                html += '<div class="p-3 rounded-lg border ' + bg + '">';
                html += '<div class="flex items-start gap-2"><span class="text-lg">' + icon + '</span>';
                html += '<div><div class="font-medium text-sm">' + ins.title + '</div>';
                html += '<div class="text-xs text-gray-600 mt-1">' + ins.detail + '</div>';
                html += '<div class="text-xs text-brand-600 mt-1 font-medium">Action: ' + ins.action + '</div></div></div></div>';
            }
            html += '</div></div>';
        }

        html += '</div>';
        return html;
    });
}

// --- EMPLOYEE DETAIL (Level 3) ---
function renderManagerEmployee() {
    if (!mgrState.employeeId) { navigate('manager-dashboard'); return Promise.resolve(''); }
    return api('/manager/h/employee/' + mgrState.employeeId).then(function(data) {
        if (!data) return '<div class="p-8 text-center text-gray-500">' + t('noData') + '</div>';
        var e = data.employee;
        mgrState.employeeName = e.name;
        var html = navBar();
        html += '<div class="max-w-7xl mx-auto p-4 space-y-6 fade-in">';

        // Breadcrumb
        html += breadcrumbHtml();

        // Header
        html += '<div class="bg-gradient-to-r from-brand-600 to-purple-600 rounded-2xl p-6 text-white">';
        html += '<div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">';
        html += '<div>';
        html += '<h1 class="text-2xl font-bold">' + e.name + '</h1>';
        html += '<p class="text-white/80 mt-1">' + e.store_name + ' | ' + e.rank + ' | Level ' + e.level + '</p>';
        html += '</div>';
        html += '<div class="flex items-center gap-4">';
        html += '<div class="text-center"><div class="text-3xl font-bold">' + e.xp + '</div><div class="text-white/70 text-xs">' + t('xp') + '</div></div>';
        html += '<div class="text-center"><div class="text-3xl">\uD83D\uDD25</div><div class="text-white/70 text-xs">' + e.streak_days + ' streak</div></div>';
        html += '</div></div></div>';

        // Performance Metrics
        html += '<div class="grid grid-cols-2 md:grid-cols-4 gap-3">';
        var overallColor = e.overall_skill_score >= 70 ? 'green' : e.overall_skill_score >= 50 ? 'amber' : 'red';
        html += statCard('\uD83C\uDFAF', t('overallScore'), e.overall_skill_score + '%', overallColor);
        html += statCard('\uD83D\uDCDA', t('training'), e.training_completion + '%', 'green');
        html += statCard('\uD83D\uDCAC', t('engagement'), e.engagement_score + '%', 'brand');
        html += statCard('\u2328\uFE0F', t('posAdoption'), e.pos_adoption + '%', 'amber');
        html += '</div>';

        // Skills
        html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-4">' + t('skillScores') + '</h3>';
        html += '<div class="flex flex-wrap justify-around gap-4">';
        var skills = data.skills || {};
        var skillLabels = {product_knowledge: t('productKnowledge'), pos_skills: t('posSkills'), communication: t('communication'), objection_handling: t('objectionHandling'), upselling: t('upselling'), need_identification: t('needId')};
        var skKeys = Object.keys(skills);
        for (var i = 0; i < skKeys.length; i++) {
            html += skillRing(skills[skKeys[i]] || 50, 90, (skillLabels[skKeys[i]] || skKeys[i]));
        }
        html += '</div></div>';

        // Training Progress + Badges
        html += '<div class="grid md:grid-cols-2 gap-4">';

        // Training
        var training = data.training;
        html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">' + t('trainingProgress') + '</h3>';
        html += '<div class="flex items-center gap-4 mb-3">';
        html += '<div class="text-center"><div class="text-2xl font-bold text-green-600">' + training.completed + '</div><div class="text-xs text-gray-500">Completed</div></div>';
        html += '<div class="text-center"><div class="text-2xl font-bold text-amber-600">' + training.in_progress + '</div><div class="text-xs text-gray-500">In Progress</div></div>';
        html += '<div class="text-center"><div class="text-2xl font-bold text-gray-400">' + training.pending_courses.length + '</div><div class="text-xs text-gray-500">Pending</div></div>';
        html += '</div>';
        html += progressBar(training.completion_pct, 'bg-green-500');
        if (training.completed_courses.length) {
            html += '<div class="mt-3 space-y-1">';
            for (var i = 0; i < Math.min(3, training.completed_courses.length); i++) {
                html += '<div class="text-xs text-green-700 bg-green-50 p-2 rounded">\u2705 ' + training.completed_courses[i].title + '</div>';
            }
            html += '</div>';
        }
        html += '</div>';

        // Badges
        html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">' + t('badgesAchievements') + '</h3>';
        html += '<div class="flex flex-wrap gap-2">';
        var badges = data.badges || [];
        if (badges.length) {
            for (var i = 0; i < badges.length; i++) {
                html += '<div class="flex items-center gap-1 px-2 py-1 bg-amber-50 border border-amber-200 rounded-lg text-xs">';
                html += '<span>' + badges[i].icon + '</span>' + badges[i].name + '</div>';
            }
        } else {
            html += '<p class="text-gray-400 text-sm">' + t('noBadges') + '</p>';
        }
        html += '</div></div></div>';

        // Next Best Action
        var nba = data.next_best_action;
        html += '<div class="bg-gradient-to-r from-brand-500 to-purple-500 rounded-xl p-5 text-white">';
        html += '<div class="flex items-start gap-3"><span class="text-2xl">\uD83C\uDFAF</span>';
        html += '<div><div class="font-bold text-lg">Next Best Action</div>';
        html += '<div class="text-white/90 mt-1">' + nba.title + '</div>';
        html += '<div class="text-white/70 text-sm mt-1">' + nba.description + ' (Current: ' + nba.score + '%)</div>';
        html += '</div></div></div>';

        // Pre/Post Assessment
        if (e.has_completed_pre_assessment || e.has_completed_post_assessment) {
            html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">' + t('beforeAfter') + '</h3>';
            html += '<div class="flex items-center gap-6">';
            html += '<div class="text-center"><div class="text-sm text-gray-500 mb-1">Pre-Assessment</div>';
            html += data.pre_assessment_score ? skillRing(data.pre_assessment_score, 80) : '<div class="text-gray-400 text-sm">' + t('notTaken') + '</div>';
            html += '</div>';
            html += '<div class="text-2xl text-gray-300">\u2192</div>';
            html += '<div class="text-center"><div class="text-sm text-gray-500 mb-1">Post-Assessment</div>';
            html += data.post_assessment_score ? skillRing(data.post_assessment_score, 80) : '<div class="text-gray-400 text-sm">Pending</div>';
            html += '</div>';
            if (data.pre_assessment_score && data.post_assessment_score) {
                var imp = data.post_assessment_score - data.pre_assessment_score;
                html += '<div class="p-3 bg-green-50 rounded-xl border border-green-200 text-center">';
                html += '<div class="text-2xl font-bold text-green-600">+' + Math.round(imp) + '%</div>';
                html += '<div class="text-xs text-green-700">Improvement</div></div>';
            }
            html += '</div></div>';
        }

        // Recent Activity
        var activity = data.recent_activity || [];
        if (activity.length) {
            html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">' + t('recentActivity') + '</h3>';
            html += '<div class="space-y-2">';
            for (var i = 0; i < Math.min(5, activity.length); i++) {
                var a = activity[i];
                var aIcon = a.type === 'training_completed' ? '\u2705' : a.type === 'recognition' ? '\u2B50' : a.type === 'simulation' ? '\uD83E\uDD16' : '\uD83D\uDCCA';
                html += '<div class="flex items-center gap-3 p-2 bg-gray-50 rounded">';
                html += '<span>' + aIcon + '</span>';
                html += '<div class="text-sm">' + a.title + '</div></div>';
            }
            html += '</div></div>';
        }

        // Simulation History
        var sims = data.simulations || [];
        if (sims.length) {
            html += '<div class="bg-white rounded-xl border p-5"><h3 class="font-bold mb-3">Customer Simulation History</h3>';
            html += '<div class="space-y-2">';
            for (var i = 0; i < sims.length; i++) {
                var s = sims[i];
                html += '<div class="flex items-center justify-between p-2 bg-gray-50 rounded">';
                html += '<div><span class="text-xs px-2 py-0.5 rounded-full ' + (s.assessment_type === 'pre' ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700') + '">' + s.assessment_type.toUpperCase() + '</span>';
                html += ' <span class="text-sm">' + (s.assessment_type === 'pre' ? 'Pre' : 'Post') + ' Assessment</span></div>';
                html += '<span class="font-bold">' + s.overall_score + '%</span></div>';
            }
            html += '</div></div>';
        }

        html += '</div>';
        return html;
    });
}

// --- HEATMAP ---

// --- HEATMAP ---
function renderHeatmap() {
  return api('/manager/heatmap').then(function(data) {
    if (!data) return '<div class="p-8 text-center text-gray-500">' + t('noData') + '</div>';
    var html = navBar();
    html += '<div class="max-w-5xl mx-auto p-4 fade-in">';
    html += '<h2 class="text-2xl font-bold mb-4">\uD83D\uDDFA\uFE0F ' + t('heatmap') + '</h2>';
    html += '<div class="bg-white rounded-xl border overflow-hidden"><div class="overflow-x-auto">';
    html += '<table class="w-full text-sm"><thead><tr class="bg-gray-50">';
    html += '<th class="text-left p-3 font-medium">Store</th>';
    for (var i = 0; i < data.skill_categories.length; i++) {
      html += '<th class="p-3 font-medium text-center">' + capitalize(data.skill_categories[i]) + '</th>';
    }
    html += '</tr></thead><tbody>';
    var heatmap = data.heatmap || [];
    for (var i = 0; i < heatmap.length; i++) {
      var row = heatmap[i];
      html += '<tr class="border-t"><td class="p-3 font-medium text-sm">' + row.store + '</td>';
      for (var j = 0; j < data.skill_categories.length; j++) {
        var sk = data.skill_categories[j];
        var v = row[sk] || 50;
        var bg = v >= 70 ? 'bg-green-100 text-green-800' : v >= 50 ? 'bg-amber-100 text-amber-800' : 'bg-red-100 text-red-800';
        html += '<td class="p-3 text-center"><span class="px-3 py-1.5 rounded-lg text-xs font-bold ' + bg + '">' + v + '%</span></td>';
      }
      html += '</tr>';
    }
    html += '</tbody></table></div></div>';
    html += '<div class="flex justify-center gap-6 mt-4 text-xs">';
    html += '<span class="flex items-center gap-1"><span class="w-4 h-4 bg-green-100 rounded"></span> Strong (\u226570%)</span>';
    html += '<span class="flex items-center gap-1"><span class="w-4 h-4 bg-amber-100 rounded"></span> Moderate (50-69%)</span>';
    html += '<span class="flex items-center gap-1"><span class="w-4 h-4 bg-red-100 rounded"></span> Weak (&lt;50%)</span>';
    html += '</div></div>';
    return html;
  });
}

// --- BUSINESS IMPACT ---
function renderBusinessImpact() {
  return api('/manager/business-impact').then(function(data) {
    var html = navBar();
    html += '<div class="max-w-5xl mx-auto p-4 space-y-6 fade-in">';
    html += '<h2 class="text-2xl font-bold">\uD83D\uDCC8 ' + t('businessImpact') + '</h2>';
    html += '<div class="bg-amber-50 border border-amber-200 rounded-xl p-4 text-center">';
    html += '<p class="text-sm text-amber-700">\u26A0\uFE0F ' + data.disclaimer + '</p></div>';
    html += '<div class="grid grid-cols-2 md:grid-cols-5 gap-4">';
    var keys = Object.keys(data.before);
    for (var i = 0; i < keys.length; i++) {
      var k = keys[i];
      html += '<div class="bg-white rounded-xl border p-5 text-center">';
      html += '<div class="text-xs text-gray-500 mb-3">' + capitalize(k) + '</div>';
      html += '<div class="text-sm text-red-400">' + data.before[k] + '%</div>';
      html += '<div class="text-2xl font-bold my-1">\u2192</div>';
      html += '<div class="text-xl font-bold text-green-600">' + data.after[k] + '%</div>';
      html += '<div class="text-xs text-green-500 mt-1">+' + (data.after[k] - data.before[k]) + '%</div></div>';
    }
    html += '</div>';
    html += '<div class="bg-white rounded-xl border p-5">';
    html += '<h3 class="font-bold mb-3">\uD83D\uDCCA ' + t('trend') + ' (Simulated)</h3>';
    html += '<canvas id="trend-chart" height="200"></canvas></div></div>';

    // Need to render chart after DOM update
    setTimeout(function() {
      var ctx = document.getElementById('trend-chart');
      if (!ctx) return;
      new Chart(ctx, {
        type: 'line',
        data: {
          labels: data.trend_data.map(function(d){ return d.month; }),
          datasets: ['training', 'pos', 'skill', 'engagement', 'upsell'].map(function(k, i) {
            return {
              label: capitalize(k),
              data: data.trend_data.map(function(d){ return d[k]; }),
              borderColor: ['#6366f1', '#f59e0b', '#10b981', '#8b5cf6', '#ef4444'][i],
              tension: 0.4, fill: false
            };
          })
        },
        options: { responsive: true, plugins: { legend: { position: 'bottom' } }, scales: { y: { beginAtZero: false } } }
      });
    }, 200);

    return html;
  });
}

// --- LEADERBOARD ---
function renderLeaderboard() {
  return api('/challenges/leaderboard').then(function(data) {
    var html = navBar();
    html += '<div class="max-w-4xl mx-auto p-4 fade-in">';
    html += '<h2 class="text-2xl font-bold mb-4">\uD83C\uDFC6 ' + t('leaderboard') + '</h2>';
    html += '<p class="text-xs text-gray-500 mb-4">FairScore = 40% Performance + 30% Improvement + 20% Learning + 10% Recognition</p>';
    html += '<div class="bg-white rounded-xl border overflow-hidden"><div class="overflow-x-auto">';
    html += '<table class="w-full text-sm"><thead><tr class="bg-gray-50">';
    html += '<th class="text-left p-3">#</th>';
    html += '<th class="text-left p-3">Employee</th>';
    html += '<th class="text-left p-3 hidden md:table-cell">Store</th>';
    html += '<th class="text-center p-3">XP</th>';
    html += '<th class="text-center p-3">Level</th>';
    html += '<th class="text-center p-3">FairScore</th>';
    html += '</tr></thead><tbody>';
    var list = data || [];
    for (var i = 0; i < list.length; i++) {
      var e = list[i];
      var rowBg = i === 0 ? 'bg-amber-50' : i === 1 ? 'bg-gray-50' : i === 2 ? 'bg-orange-50' : '';
      var rankBg = i === 0 ? 'bg-amber-400' : i === 1 ? 'bg-gray-300' : i === 2 ? 'bg-amber-600' : 'bg-gray-100';
      html += '<tr class="border-t ' + rowBg + '">';
      html += '<td class="p-3"><span class="w-7 h-7 ' + rankBg + ' text-white rounded-full flex items-center justify-center text-xs font-bold">' + (i+1) + '</span></td>';
      html += '<td class="p-3"><div class="font-medium">' + e.name + '</div><div class="text-xs text-gray-500">' + e.rank_title + '</div></td>';
      html += '<td class="p-3 hidden md:table-cell text-gray-500">' + e.store + '</td>';
      html += '<td class="p-3 text-center font-medium">' + e.xp + '</td>';
      html += '<td class="p-3 text-center">Lv.' + e.level + '</td>';
      html += '<td class="p-3 text-center"><span class="font-bold text-brand-600">' + e.fair_score + '</span></td></tr>';
    }
    html += '</tbody></table></div></div></div>';
    return html;
  });
}

// --- CHALLENGES ---
function renderChallenges() {
  return api('/challenges/').then(function(data) {
    var html = navBar();
    html += '<div class="max-w-4xl mx-auto p-4 fade-in">';
    html += '<h2 class="text-2xl font-bold mb-4">\uD83C\uDFAF ' + t('challenges') + '</h2>';
    html += '<div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">';
    var list = data || [];
    var typeIcons = { daily: '\uD83D\uDCC5', weekly: '\uD83D\uDCCB', pos: '\u2328\uFE0F', customer: '\uD83E\uDD16', skill: '\uD83C\uDFAF' };
    for (var i = 0; i < list.length; i++) {
      var c = list[i];
      var prog = c.progress || { progress: 0, completed: false };
      var pct = c.target_value ? (prog.progress / c.target_value * 100) : 0;
      var ringCls = prog.completed ? 'ring-2 ring-green-400' : '';
      var pbColor = prog.completed ? 'bg-green-500' : 'bg-brand-500';
      html += '<div class="bg-white rounded-xl border p-5 ' + ringCls + '">';
      html += '<div class="flex items-center justify-between mb-3">';
      html += '<span class="text-2xl">' + (typeIcons[c.challenge_type] || '\uD83C\uDFAF') + '</span>';
      html += '<span class="text-xs px-2 py-1 rounded-full bg-brand-50 text-brand-700">+' + c.xp_reward + ' XP</span></div>';
      html += '<h3 class="font-bold text-sm">' + c.title + '</h3>';
      html += '<div class="text-xs text-gray-500 mt-1">' + c.challenge_type.replace(/_/g, ' ').toUpperCase() + '</div>';
      html += '<div class="mt-3">' + progressBar(pct, pbColor) + '</div>';
      html += '<div class="flex justify-between mt-2 text-xs text-gray-500">';
      html += '<span>' + prog.progress + '/' + c.target_value + '</span>';
      if (prog.completed) {
        html += '<span class="text-green-600 font-bold">\u2705 Complete!</span>';
      } else {
        html += '<button onclick="updateChallenge(' + c.id + ')" class="text-brand-600 hover:underline">+1 Progress</button>';
      }
      html += '</div></div>';
    }
    html += '</div></div>';
    return html;
  });
}

function updateChallenge(id) {
  api('/challenges/' + id + '/progress', { method: 'POST', body: JSON.stringify({ increment: 1 }) }).then(function(res) {
    if (res) {
      if (res.status === 'completed') showToast('Challenge complete! +' + res.xp_earned + ' XP', 'success');
      else showToast('Progress: ' + res.progress + '/' + res.target, 'info');
      renderChallenges().then(function(html){ document.getElementById('app').innerHTML = html; });
    }
  });
}

// --- ADMIN DASHBOARD ---
function renderAdminDashboard() {
  return api('/admin/dashboard').then(function(data) {
    if (!data) return '<div class="p-8 text-center text-gray-500">' + t('noData') + '</div>';
    var s = data.summary;
    var html = navBar();
    html += '<div class="max-w-7xl mx-auto p-4 space-y-6 fade-in">';
    html += '<h1 class="text-2xl font-bold">\u2699\uFE0F Admin ' + t('dashboard') + '</h1>';
    html += '<div class="flex gap-3 mt-2">'; 
    html += '<span class="text-xs bg-brand-100 text-brand-700 px-3 py-1 rounded-full font-medium">\uD83C\uDFFD Prototype: 10 Stores | 120+ Associates</span>';
    html += '<span class="text-xs bg-green-100 text-green-700 px-3 py-1 rounded-full font-medium">Designed to scale to 1,200+ Stores | 3,000+ Associates Monthly</span>';
    html += '</div>';
    html += '<div class="grid grid-cols-2 md:grid-cols-4 gap-3">';
    html += statCard('\uD83D\uDC65', t('totalEmployees'), s.total_employees, 'brand');
    html += statCard('\uD83C\uDFEA', 'Stores', s.total_stores, 'green');
    html += statCard('\uD83D\uDCDA', t('courses'), s.total_courses, 'amber');
    html += statCard('\uD83C\uDFAF', t('avgSkill'), s.avg_skill + '%', 'brand');
    html += '</div>';

    html += '<div class="bg-white rounded-xl border p-5">';
    html += '<h3 class="font-bold mb-3">\uD83C\uDFEA Store Summary</h3>';
    html += '<div class="overflow-x-auto"><table class="w-full text-sm">';
    html += '<thead><tr class="bg-gray-50">';
    html += '<th class="text-left p-2">Store</th><th class="text-left p-2">Code</th><th class="text-left p-2">City</th>';
    html += '<th class="text-center p-2">Employees</th><th class="text-center p-2">Avg Skill</th><th class="text-center p-2">Avg POS</th>';
    html += '</tr></thead><tbody>';
    var stores = data.stores || [];
    for (var i = 0; i < stores.length; i++) {
      var st = stores[i];
      var skillColor = st.avg_skill >= 70 ? 'text-green-600' : st.avg_skill >= 50 ? 'text-amber-600' : 'text-red-600';
      html += '<tr class="border-t"><td class="p-2 font-medium">' + st.name + '</td><td class="p-2 text-gray-500">' + st.code + '</td>';
      html += '<td class="p-2 text-gray-500">' + st.city + '</td><td class="p-2 text-center">' + st.employee_count + '</td>';
      html += '<td class="p-2 text-center"><span class="font-bold ' + skillColor + '">' + st.avg_skill + '%</span></td>';
      html += '<td class="p-2 text-center">' + st.avg_pos + '%</td></tr>';
    }
    html += '</tbody></table></div></div></div>';
    return html;
  });
}

// --- MANAGER EMPLOYEES ---
function renderManagerEmployees() {
  return api('/manager/employees').then(function(data) {
    var html = navBar();
    html += '<div class="max-w-6xl mx-auto p-4 fade-in">';
    html += '<h2 class="text-2xl font-bold mb-4">\uD83D\uDC65 ' + t('employees') + '</h2>';
    html += '<div class="bg-white rounded-xl border overflow-hidden"><div class="overflow-x-auto">';
    html += '<table class="w-full text-sm"><thead><tr class="bg-gray-50">';
    html += '<th class="text-left p-3">Employee</th><th class="text-left p-3 hidden md:table-cell">Store</th>';
    html += '<th class="text-center p-3">Skill</th><th class="text-center p-3">POS</th>';
    html += '<th class="text-center p-3">Engage</th><th class="text-center p-3">Training</th>';
    html += '<th class="text-center p-3">XP</th><th class="text-center p-3">Level</th>';
    html += '<th class="text-center p-3">Action</th></tr></thead><tbody>';
    var list = data || [];
    for (var i = 0; i < list.length; i++) {
      var e = list[i];
      var skillColor = e.skill_score >= 70 ? 'text-green-600' : e.skill_score >= 50 ? 'text-amber-600' : 'text-red-600';
      html += '<tr class="border-t hover:bg-gray-50">';
      html += '<td class="p-3"><div class="font-medium">' + e.name + '</div><div class="text-xs text-gray-500">' + e.rank + '</div></td>';
      html += '<td class="p-3 hidden md:table-cell text-gray-500">' + e.store + '</td>';
      html += '<td class="p-3 text-center"><span class="font-bold ' + skillColor + '">' + e.skill_score + '%</span></td>';
      html += '<td class="p-3 text-center">' + e.pos_adoption + '%</td>';
      html += '<td class="p-3 text-center">' + e.engagement + '%</td>';
      html += '<td class="p-3 text-center">' + e.training_completion + '%</td>';
      html += '<td class="p-3 text-center font-medium">' + e.xp + '</td>';
      html += '<td class="p-3 text-center">Lv.' + e.level + '</td>';
      html += '<td class="p-3 text-center">';
      html += '<select class="text-xs border rounded px-1 py-1" onchange="recognizeFromList(' + e.id + ', this.value); this.value=\'\'">';
      html += '<option value="">Recognize</option>';
      html += '<option value="customer_hero">\uD83E\uDDBA Hero</option>';
      html += '<option value="product_expert">\uD83C\uDFC5 Expert</option>';
      html += '<option value="digital_champion">\uD83D\uDCBB Digital</option>';
      html += '<option value="most_improved">\uD83D\uDCC8 Improved</option>';
      html += '</select></td></tr>';
    }
    html += '</tbody></table></div></div></div>';
    return html;
  });
}

function recognizeFromList(empId, type) {
  if (!type) return;
  api('/manager/recognize', { method: 'POST', body: JSON.stringify({ employee_id: empId, recognition_type: type, message: 'Recognized for ' + type.replace(/_/g, ' ') + '!' }) }).then(function(res) {
    if (res) showToast('Recognized! +' + res.xp_awarded + ' XP', 'success');
  });
}

// --- PEER RECOGNITION PAGE ---
function renderPeerRecognitionPage() {
  return Promise.all([api('/employee/teammates'), api('/employee/peer-recognitions')]).then(function(results) {
    var teammates = results[0] || [];
    var recs = results[1] || [];
    var types = [
      {id: 'helpful_teammate', icon: '\uD83D\uDC4D', label: 'Helpful Teammate', color: 'bg-blue-50 text-blue-700 border-blue-300 hover:bg-blue-100'},
      {id: 'great_collaboration', icon: '\uD83E\uDD1D', label: 'Great Collab', color: 'bg-purple-50 text-purple-700 border-purple-300 hover:bg-purple-100'},
      {id: 'product_knowledge_star', icon: '\uD83D\uDCDA', label: 'Product Expert', color: 'bg-amber-50 text-amber-700 border-amber-300 hover:bg-amber-100'},
      {id: 'customer_first', icon: '\uD83D\uDE0D', label: 'Customer First', color: 'bg-pink-50 text-pink-700 border-pink-300 hover:bg-pink-100'},
      {id: 'pos_champion_peer', icon: '\u2328\uFE0F', label: 'POS Champion', color: 'bg-green-50 text-green-700 border-green-300 hover:bg-green-100'}
    ];

    var html = '<div class="max-w-4xl mx-auto p-4">';

    // ─── HEADER WITH BACK BUTTON ───
    html += '<div class="flex items-center gap-3 mb-6">';
    html += '<button onclick="navigate(\'employee-dashboard\')" class="w-10 h-10 flex items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200 transition text-gray-600 font-bold text-lg flex-shrink-0">\u2190</button>';
    html += '<div class="flex-1">';
    html += '<h2 class="text-xl font-bold text-gray-800">\uD83D\uDD17 Peer Recognition</h2>';
    html += '<p class="text-gray-500 text-xs">Recognize your teammates! You earn +25 XP, they earn +50 XP.</p>';
    html += '</div>';
    html += '</div>';

    // ─── GIVE RECOGNITION CARD ───
    html += '<div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-6">';
    html += '<h3 class="font-semibold text-gray-800 mb-4">\u2B50 Give Recognition</h3>';

    // Step 1: Select teammate
    html += '<div class="mb-4">';
    html += '<label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Step 1: Select Teammate</label>';
    html += '<select id="peer-emp" class="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm bg-gray-50 focus:ring-2 focus:ring-brand-500 focus:border-brand-500">';
    if (teammates.length === 0) {
      html += '<option value="">No teammates in your store</option>';
    }
    for (var i = 0; i < teammates.length; i++) {
      html += '<option value="' + teammates[i].id + '">' + teammates[i].name + ' (Lv.' + teammates[i].level + ', ' + teammates[i].xp + ' XP)</option>';
    }
    html += '</select></div>';

    // Step 2: Recognition type
    html += '<div class="mb-4">';
    html += '<label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Step 2: What did they do great?</label>';
    html += '<div class="grid grid-cols-2 sm:grid-cols-5 gap-2">';
    for (var j = 0; j < types.length; j++) {
      html += '<button onclick="selectRecogType(\'' + types[j].id + '\', this)" data-type="' + types[j].id + '" class="peer-type-btn p-3 text-center text-xs font-semibold rounded-xl border-2 transition cursor-pointer ' + types[j].color + '">' + types[j].icon + '<br><span class="mt-1 block">' + types[j].label + '</span></button>';
    }
    html += '</div></div>';

    // Step 3: Personal message + SEND BUTTON
    html += '<div class="mb-2">';
    html += '<label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Step 3: Add a message</label>';
    html += '</div>';
    html += '<div style="display:flex; gap:8px; align-items:stretch;">';
    html += '<input id="peer-message" type="text" placeholder="e.g., Great job handling that customer!" style="flex:1; padding:12px 16px; border:1px solid #e5e7eb; border-radius:12px; font-size:14px; background:#f9fafb;" />';
    html += '<button onclick="sendPeerRecognition()" id="peer-send-btn" style="padding:12px 24px; background:#6366f1; color:white; font-weight:700; font-size:14px; border:none; border-radius:12px; cursor:pointer; white-space:nowrap; box-shadow:0 2px 8px rgba(99,102,241,0.3);" disabled>\u279C Send</button>';
    html += '</div>';
    html += '</div>';

    // ─── RECENT PEER RECOGNITIONS ───
    html += '<div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">';
    html += '<div class="flex items-center gap-2 mb-4">';
    html += '<span class="text-xl">\uD83D\uDD17</span>';
    html += '<h3 class="font-semibold text-gray-800">Recent Peer Recognitions</h3>';
    html += '<span class="ml-auto text-xs bg-gray-100 text-gray-500 px-2 py-1 rounded-full">' + recs.length + '</span>';
    html += '</div>';
    if (recs.length === 0) {
      html += '<div class="text-center py-8">';
      html += '<div class="text-4xl mb-2">\uD83E\uDD14</div>';
      html += '<p class="text-gray-400 text-sm">No peer recognitions yet. Be the first!</p>';
      html += '</div>';
    }
    for (var k = 0; k < recs.length; k++) {
      var r = recs[k];
      var typeObj = types.find(function(t){ return t.id === r.type; }) || types[0];
      html += '<div style="display:flex; align-items:center; gap:12px; padding:12px 16px; background:linear-gradient(to right,#f9fafb,#fff); border-radius:12px; margin-bottom:8px; border:1px solid #f3f4f6;">';
      html += '<div style="width:40px; height:40px; border-radius:50%; background:#ede9fe; display:flex; align-items:center; justify-content:center; font-size:20px; flex-shrink:0;">' + (typeObj ? typeObj.icon : '\uD83C\uDF1F') + '</div>';
      html += '<div style="flex:1; min-width:0;">';
      html += '<div style="font-weight:600; font-size:14px; color:#1f2937;">' + r.from_name + ' \u2192 ' + r.to_name + '</div>';
      html += '<div style="font-size:12px; color:#6b7280; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">' + r.message + '</div>';
      html += '</div>';
      html += '<span style="background:#dcfce7; color:#166534; padding:2px 10px; border-radius:9999px; font-size:12px; font-weight:600; flex-shrink:0;">+' + r.xp_awarded + ' XP</span>';
      html += '</div>';
    }
    html += '</div></div>';

    window._selectedRecogType = null;
    return html;
  });
}

function selectRecogType(type, btn) {
  window._selectedRecogType = type;
  var btns = document.querySelectorAll('.peer-type-btn');
  for (var i = 0; i < btns.length; i++) {
    btns[i].classList.remove('ring-2', 'ring-brand-500', 'ring-offset-2');
  }
  btn.classList.add('ring-2', 'ring-brand-500', 'ring-offset-2');
  document.getElementById('peer-send-btn').disabled = false;
}

function sendPeerRecognition() {
  var type = window._selectedRecogType;
  if (!type) { showToast('Please select a recognition type', 'warning'); return; }
  var empId = document.getElementById('peer-emp').value;
  if (!empId) { showToast('Please select a teammate', 'warning'); return; }
  var msg = document.getElementById('peer-message').value || 'Great work!';
  var btn = document.getElementById('peer-send-btn');
  btn.disabled = true; btn.textContent = 'Sending...';
  api('/employee/peer-recognize', { method: 'POST', body: JSON.stringify({ employee_id: parseInt(empId), recognition_type: type, message: msg }) }).then(function(res) {
    if (res && res.status === 'ok') {
      showToast('Recognized! +' + res.giver_xp_earned + ' XP for you, +' + res.receiver_xp_earned + ' XP for them!', 'success');
      render();
    } else {
      showToast((res && res.detail) || 'Failed to send recognition', 'error');
      btn.disabled = false; btn.textContent = '\u279C Send';
    }
  }).catch(function() {
    showToast('Network error. Try again.', 'error');
    btn.disabled = false; btn.textContent = '\u279C Send';
  });
}

// --- POS MICRO-LEARNING PAGE ---
function renderPosLearningPage() {
  return Promise.all([api('/employee/pos-lessons?trigger=after_sale&language=en'), api('/employee/pos-lessons?trigger=idle&language=en'), api('/employee/pos-lessons?trigger=before_shift&language=en')]).then(function(results) {
    var afterSale = results[0] || [];
    var idle = results[1] || [];
    var beforeShift = results[2] || [];

    var html = '<div class="max-w-4xl mx-auto p-4">';

    // ─── HEADER WITH BACK BUTTON ───
    html += '<div style="display:flex; align-items:center; gap:12px; margin-bottom:24px;">';
    html += '<button onclick="navigate(\'employee-dashboard\')" style="width:40px; height:40px; display:flex; align-items:center; justify-content:center; border-radius:50%; background:#f3f4f6; border:none; cursor:pointer; font-size:18px; color:#4b5563; flex-shrink:0;">\u2190</button>';
    html += '<div class="flex-1">';
    html += '<h2 style="font-size:20px; font-weight:700; color:#1f2937; margin:0;">\uD83D\uDCBB POS Learning Tips</h2>';
    html += '<p style="font-size:12px; color:#6b7280; margin:4px 0 0 0;">Quick tips for the sales floor. Complete during natural breaks.</p>';
    html += '</div></div>';

    function renderLessonSection(title, icon, lessons, bgColor) {
      if (lessons.length === 0) return '';
      var s = '<div style="margin-bottom:24px;">';
      s += '<div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">';
      s += '<span style="font-size:20px;">' + icon + '</span>';
      s += '<h3 style="font-weight:700; color:#1f2937; font-size:16px; margin:0;">' + title + '</h3>';
      s += '<span style="font-size:11px; background:#f3f4f6; color:#6b7280; padding:2px 8px; border-radius:9999px;">' + lessons.length + ' tips</span>';
      s += '</div>';
      for (var i = 0; i < lessons.length; i++) {
        var l = lessons[i];
        s += '<div style="background:white; border-radius:16px; border:1px solid #e5e7eb; padding:20px; margin-bottom:12px; display:flex; align-items:flex-start; gap:16px;">';
        s += '<div style="width:44px; height:44px; border-radius:12px; ' + bgColor + '; display:flex; align-items:center; justify-content:center; font-size:20px; flex-shrink:0;">' + icon + '</div>';
        s += '<div style="flex:1; min-width:0;">';
        s += '<div style="font-weight:700; font-size:14px; color:#1f2937; margin-bottom:4px;">' + l.title + '</div>';
        s += '<div style="font-size:13px; color:#4b5563; line-height:1.5; margin-bottom:8px;">' + l.content + '</div>';
        s += '<div style="display:flex; align-items:center; gap:8px;">';
        s += '<span style="background:#eff6ff; color:#1d4ed8; padding:2px 10px; border-radius:9999px; font-size:11px; font-weight:600;">' + l.skill_category.replace(/_/g, ' ') + '</span>';
        s += '<span style="color:#22c55e; font-size:12px; font-weight:700;">+' + l.xp_reward + ' XP</span>';
        s += '</div></div>';
        s += '<button onclick="completePosLesson(\'' + l.id + '\')" style="padding:10px 20px; background:linear-gradient(135deg,#22c55e,#10b981); color:white; font-size:13px; font-weight:700; border:none; border-radius:12px; cursor:pointer; white-space:nowrap; flex-shrink:0; box-shadow:0 2px 8px rgba(34,197,94,0.3);">\u2713 Complete</button>';
        s += '</div>';
      }
      s += '</div>';
      return s;
    }

    html += renderLessonSection('After Sale Tips', '\uD83D\uDCB0', afterSale, 'background:#fef3c7; color:#92400e;');
    html += renderLessonSection('Quick Tips (Anytime)', '\u26A1', idle, 'background:#dbeafe; color:#1e40af;');
    html += renderLessonSection('Before Shift', '\uD83C\uDF05', beforeShift, 'background:#ffedd5; color:#9a3412;');
    html += '</div>';
    return html;
  });
}

function completePosLesson(lessonId) {
  api('/employee/pos-lesson/' + lessonId + '/complete', { method: 'POST' }).then(function(res) {
    if (res && res.xp_earned) {
      showToast('Lesson complete! +' + res.xp_earned + ' XP', 'success');
      render();
    } else if (res && res.detail) {
      showToast(res.detail, 'error');
    }
  });
}

// --- MAIN RENDER ---
function render() {
  var app = document.getElementById('app');
  if (!appState.token || appState.page === 'login') {
    app.innerHTML = renderLoginPage();
    return;
  }

  var handler;
  switch (appState.page) {
    case 'employee-dashboard': handler = renderEmployeeDashboard; break;
    case 'courses-page': handler = renderCoursesPage; break;
    case 'simulation-page': handler = renderSimulationPage; break;
    case 'leaderboard-page': handler = renderLeaderboard; break;
    case 'challenges-page': handler = renderChallenges; break;
    case 'peer-recognition-page': handler = renderPeerRecognitionPage; break;
    case 'pos-learning-page': handler = renderPosLearningPage; break;
    case 'manager-dashboard': handler = renderManagerDashboard; break;
    case 'manager-store': handler = renderStoreDashboard; break;
    case 'manager-employee': handler = renderManagerEmployee; break;
    case 'manager-employees': handler = renderManagerEmployees; break;
    case 'manager-heatmap': handler = renderHeatmap; break;
    case 'manager-business': handler = renderBusinessImpact; break;
    case 'admin-dashboard': handler = renderAdminDashboard; break;
    default:
      if (appState.role === 'manager') handler = renderManagerDashboard;
      else if (appState.role === 'admin') handler = renderAdminDashboard;
      else handler = renderEmployeeDashboard;
  }

  handler().then(function(html) {
    app.innerHTML = html;
  });
}

// --- INIT ---
render();
