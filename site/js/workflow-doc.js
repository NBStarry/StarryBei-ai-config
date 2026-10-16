// 文档只切换显示主题，不读取本机状态。
const themeButton = document.getElementById('doc-theme');
let theme = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
function applyTheme() {
  document.documentElement.dataset.theme = theme;
  themeButton.textContent = theme === 'light' ? '切换深色' : '切换浅色';
}
themeButton.addEventListener('click', () => {
  theme = theme === 'light' ? 'dark' : 'light';
  applyTheme();
});
applyTheme();
