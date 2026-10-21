<script setup lang="ts">
import { provide } from 'vue'
import { businessSessionKey, createBusinessSession } from './business/session'
const business = createBusinessSession()
provide(businessSessionKey, business)
</script>
<template>
  <main>
    <header>
      <small>公安厅项目 · 内部研发</small>
      <h1>媒体溯源研发验证台</h1>
      <p>验证上传、存储、异步任务与CPU推理的完整链路。</p>
    </header>
    <nav aria-label="主导航">
      <RouterLink to="/">上传验证</RouterLink><RouterLink to="/health">系统健康</RouterLink>
      <RouterLink to="/business">业务身份</RouterLink
      ><RouterLink to="/approvals">审批管理</RouterLink
      ><RouterLink to="/audit">审计查询</RouterLink>
      <RouterLink to="/tasks">任务与结果</RouterLink>
      <RouterLink to="/reviews/pending">待复核队列</RouterLink>
    </nav>
    <RouterView :key="business.state.generation" />
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
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 22px;
}
.secondary {
  margin-left: 8px;
  background: #e8eff8;
  color: #225aa4;
}
select,
textarea {
  display: block;
  width: 95%;
  padding: 10px;
  margin-top: 8px;
  border: 1px solid #becadd;
  border-radius: 6px;
}
.check {
  display: flex;
  gap: 10px;
  align-items: center;
}
.check input {
  width: auto;
  margin: 0;
}
dd {
  margin: 6px 0 18px;
  overflow-wrap: anywhere;
}
.table-scroll {
  overflow-x: auto;
  margin: 20px 0;
}
table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}
td,
th {
  padding: 10px;
  border-bottom: 1px solid #dce4ef;
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
