<!-- src/App.vue -->

<template>
  <div id="app">
    <RouterView />
  </div>
</template>

<script setup>
import { RouterView } from 'vue-router'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
    Ubuntu, Cantarell, 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  min-height: 100vh;
  background-color: var(--mantine-color-dark-7);
  color: var(--mantine-color-gray-0);
}

:root {
  --mantine-color-grape-9: #862E9C;
  --mantine-color-grape-7: #ae3ec9;
  --mantine-color-green-9: #2f9e44;
  --mantine-color-green-7: #40c057;
  --mantine-color-dark-7: #1A1B1E;
  --mantine-color-dark-6: #25262B;
  --mantine-color-gray-0: #f8f9fa;
  --mantine-color-gray-5: #adb5bd;
}

body {
  background-color: var(--mantine-color-dark-7);
}
</style>