<template>
  <main>
    <header>
      <small>公安厅项目 · 第二阶段</small>
      <h1>媒体溯源研发验证台</h1>
      <p>验证上传、存储、异步任务与CPU推理的完整链路。</p>
    </header>
    <nav aria-label="主导航">
      <RouterLink to="/">上传验证</RouterLink><RouterLink to="/health">系统健康</RouterLink>
    </nav>
    <RouterView />
  </main>
</template>
<style>
body {
  margin: 0;
  background: #f3f6fa;
  color: #1b293e;
  font-family: system-ui, 'Microsoft YaHei', sans-serif;
}
main {
  max-width: 900px;
  margin: 45px auto;
  padding: 0 24px;
}
header {
  margin-bottom: 28px;
}
small {
  color: #506d9b;
}
h1 {
  font-size: 32px;
}
h2 {
  font-size: 19px;
}
section {
  background: white;
  padding: 26px;
  border: 1px solid #dce4ef;
  border-radius: 12px;
  margin: 18px 0;
}
label {
  display: block;
  margin: 18px 0;
}
input {
  display: block;
  padding: 10px;
  margin-top: 8px;
  width: 95%;
  border: 1px solid #becadd;
  border-radius: 6px;
}
button {
  background: #225aa4;
  color: white;
  padding: 12px 24px;
  border: 0;
  border-radius: 7px;
  cursor: pointer;
}
button:disabled {
  opacity: 0.6;
}
.muted {
  color: #728096;
}
pre {
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 12px;
  background: #f4f7fb;
  padding: 18px;
  border-radius: 8px;
}
nav {
  display: flex;
  gap: 20px;
  margin-bottom: 22px;
}
nav a {
  color: #225aa4;
  padding: 8px 4px;
}
nav a.router-link-exact-active {
  font-weight: 700;
  text-decoration-thickness: 2px;
}
a:focus-visible,
button:focus-visible,
input:focus-visible {
  outline: 3px solid #7d9cc9;
  outline-offset: 3px;
}
</style>
