<template>
  <div class="login-page">
    <!-- Left Section: Visual Branding (Desktop only) -->
    <div class="branding-panel">
      <!-- Subtle architectural pattern -->
      <div class="pattern-overlay"></div>
      <div class="gradient-overlay"></div>

      <!-- Large Architectural Graphic Reference -->
      <div class="branding-content">
        <div class="branding-top">
          <div class="logo-block">
            <img :src="logoUrl" alt="Studio MH02 Logo" class="login-logo-img" />
          </div>
          <h2 class="brand-title">Studio<br />MH 02</h2>
          <div class="brand-divider"></div>
          <p class="brand-tagline">
            Precision-engineered studio suite for high-performance enterprise resource planning.
          </p>
        </div>
            <div class="stat-value">v1.0.0</div>
            <div class="stat-label">Build Release</div>
        <!-- Stats Indicators -->
        <div class="stats-row">
          <div>

          </div>
          <div>

          </div>
        </div>
      </div>
    </div>

    <!-- Right Section: Login Content -->
    <main class="login-panel">
      <!-- Decorative gradient for mobile -->
      <div class="mobile-gradient"></div>

      <div class="login-container">
        <!-- Mobile Logo -->
        <div class="mobile-logo">
          <div class="mobile-logo-block">
            <img :src="logoUrl" alt="Studio MH02 Logo" class="login-logo-img mobile-logo-img" />
          </div>
          <h1 class="mobile-brand-title">Studio MH02</h1>
        </div>

        <!-- Header -->
        <header class="login-header">
          <h2 class="welcome-title">Welcome back</h2>
          <p class="welcome-subtitle">
            Enter your workspace credentials to continue.
          </p>
        </header>

        <!-- Authentication Form -->
        <form @submit.prevent="handleLogin" class="login-form">
          <!-- Studio Email Field -->
          <div class="field-group">
            <label for="studio-email" class="field-label">Studio Email</label>
            <div class="input-wrapper" :class="{ focused: emailFocused }">
              <input
                id="studio-email"
                v-model="form.studio_email"
                type="email"
                placeholder="e.g. user@studiomh02.com"
                required
                class="field-input"
                @focus="emailFocused = true"
                @blur="emailFocused = false"
              />
              <div class="input-icon" :class="{ active: emailFocused }">
                <span class="material-symbols-outlined">mail</span>
              </div>
            </div>
            <p v-if="errors.email" class="field-error">{{ errors.email }}</p>
          </div>

          <!-- Password Field -->
          <div class="field-group">
            <div class="field-label-row">
              <label for="password" class="field-label">Password</label>
            </div>
            <div class="input-wrapper" :class="{ focused: passwordFocused }">
              <input
                id="password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="••••••••••••"
                required
                class="field-input"
                @focus="passwordFocused = true"
                @blur="passwordFocused = false"
              />
              <button
                type="button"
                class="input-icon-btn"
                :class="{ active: passwordFocused }"
                @click="showPassword = !showPassword"
                tabindex="-1"
              >
                <span class="material-symbols-outlined">{{
                  showPassword ? "visibility" : "visibility_off"
                }}</span>
              </button>
            </div>
            <p v-if="errors.password" class="field-error">
              {{ errors.password }}
            </p>
          </div>

          <!-- Keep signed in -->
          <div class="checkbox-row">
            <label class="checkbox-label">
              <input
                v-model="form.keepSigned"
                type="checkbox"
                class="checkbox-input"
              />
              <span class="checkbox-text">Keep me signed in</span>
            </label>
          </div>

          <!-- Error Message -->
          <div v-if="errors.general" class="error-banner">
            <span class="material-symbols-outlined error-banner-icon"
              >error</span
            >
            <p>{{ errors.general }}</p>
          </div>

          <!-- Sign In Button -->
          <div class="submit-group">
            <button type="submit" :disabled="loading" class="sign-in-btn">
              <template v-if="!loading">
                <span>Sign In</span>
                <span class="material-symbols-outlined btn-arrow"
                  >arrow_forward</span
                >
              </template>
              <template v-else>
                <span class="spinner"></span>
                <span>Signing in…</span>
              </template>
            </button>
          </div>
        </form>

        <!-- Footer / Registration -->
        <footer class="login-footer">
          <p>
            Don't have an account yet?
            <a href="#" class="contact-link">Contact administration</a>
          </p>
        </footer>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { authAPI } from "../api/auth";
import { getAppLogoUrl } from "../utils/logo";

const router = useRouter();
const authStore = useAuthStore();

const form = reactive({
  studio_email: "",
  password: "",
  keepSigned: false,
});

const showPassword = ref(false);
const loading = ref(false);
const emailFocused = ref(false);
const passwordFocused = ref(false);
const logoUrl = getAppLogoUrl();

const errors = reactive({
  email: "",
  password: "",
  general: "",
});

/**
 * Redirect the user to the correct dashboard based on their role.
 */
function redirectByRole(role) {
  switch (role) {
    case "admin":
      router.push("/admin/dashboard");
      break;
    case "project_manager":
      router.push("/pm/dashboard");
      break;
    case "employee":
      router.push("/employee/dashboard");
      break;
    default:
      router.push("/");
  }
}

const handleLogin = async () => {
  // Reset errors
  errors.email = "";
  errors.password = "";
  errors.general = "";

  // Client-side validation
  if (!form.studio_email) {
    errors.email = "Studio email is required";
    return;
  }
  if (!form.studio_email.includes("@")) {
    errors.email = "Please enter a valid email address";
    return;
  }
  if (!form.password) {
    errors.password = "Password is required";
    return;
  }

  loading.value = true;

  try {
    const response = await authAPI.login(form.studio_email, form.password);
    const { access_token, role } = response.data;

    authStore.setToken(access_token, role || "employee");
    redirectByRole(role);
  } catch (error) {
    if (error.response?.status === 401) {
      errors.general =
        error.response?.data?.detail || "Invalid email or password";
    } else if (error.response?.status === 422) {
      errors.general = "Please check the format of your credentials";
    } else if (!error.response) {
      errors.general =
        "Unable to connect to the server. Please try again later.";
    } else {
      errors.general =
        error.response?.data?.detail || "Login failed. Please try again.";
    }
    console.error("Login error:", error);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
/* ───────────── Page Layout + Design Tokens ───────────── */
.login-page {
  /* Inherit global tokens, override specific shadows if needed */
  --font-headline: var(--font-display);
  --font-body: var(--font-body);

  --shadow-architectural: 0 1px 2px rgba(40, 116, 117, 0.05),
    0 4px 12px rgba(40, 116, 117, 0.05);

  display: flex;
  min-height: 100vh;
  font-family: var(--font-body);
  color: var(--color-on-surface);
  background: var(--color-background);
  -webkit-font-smoothing: antialiased;
}

/* ───────────── Left Branding Panel ───────────── */
.branding-panel {
  display: none;
  position: relative;
  overflow: hidden;
  width: 50%;
  align-items: center;
  justify-content: center;
  background: linear-gradient(165deg, var(--color-primary-container) 0%, var(--color-background) 100%);
  border-right: 1px solid var(--color-outline-variant);
}

@media (min-width: 1024px) {
  .branding-panel {
    display: flex;
  }
}

.pattern-overlay {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(
    circle at 1px 1px,
    var(--color-primary) 1px,
    transparent 0
  );
  background-size: 32px 32px;
  opacity: 0.08;
}

.gradient-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to top right,
    rgba(40, 116, 117, 0.05),
    transparent,
    transparent
  );
}

.branding-content {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 672px;
  padding: 0 32px;
}

.branding-top {
  margin-bottom: 32px;
}

.logo-block {
  display: inline-flex;
  padding: 16px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(12px);
  border-radius: var(--radius-lg);
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: var(--shadow-architectural);
  margin-bottom: 24px;
  transition: transform 0.5s ease;
}

.logo-block:hover {
  transform: translateY(-2px);
}

.login-logo-img {
  width: 80px;
  max-width: 100px;
  height: auto;
  display: block;
}

.mobile-logo-img {
  width: 72px;
}

.logo-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.logo-cell {
  width: 40px;
  height: 40px;
  border-radius: 2px;
}

.logo-full {
  background-color: var(--color-primary);
}

.logo-light {
  background-color: var(--color-primary);
  opacity: 0.3;
}

.logo-mid {
  background-color: var(--color-primary);
  opacity: 0.6;
}

.brand-title {
  font-family: var(--font-headline);
  font-size: 72px;
  font-weight: 800;
  color: var(--color-primary);
  margin: 0 0 16px;
  letter-spacing: -0.03em;
  line-height: 1.1;
  text-transform: uppercase;
}

.brand-divider {
  width: 96px;
  height: 6px;
  background: rgba(40, 116, 117, 0.2);
  margin-bottom: 24px;
  border-radius: 3px;
}

.brand-tagline {
  font-family: var(--font-body);
  font-size: 20px;
  line-height: 1.6;
  color: var(--color-on-surface-variant);
  max-width: 448px;
  margin: 0;
}

/* Stats */
.stats-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  margin-top: 48px;
  padding-top: 48px;
  border-top: 1px solid rgba(199, 196, 216, 0.4);
}

.stat-value {
  font-family: var(--font-headline);
  font-size: 24px;
  font-weight: 700;
  color: var(--color-primary);
  letter-spacing: -0.01em;
  line-height: 32px;
}

.stat-label {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 700;
  color: rgba(70, 69, 85, 0.6);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-top: 4px;
  line-height: 16px;
}

/* ───────────── Right Login Panel ───────────── */
.login-panel {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: var(--color-surface);
  position: relative;
}

@media (min-width: 640px) {
  .login-panel {
    padding: 32px;
  }
}

@media (min-width: 1024px) {
  .login-panel {
    width: 50%;
  }
}

.mobile-gradient {
  display: block;
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 160px;
  background: linear-gradient(165deg, var(--color-primary-container) 0%, var(--color-background) 100%);
  opacity: 0.6;
  z-index: 0;
}

@media (min-width: 1024px) {
  .mobile-gradient {
    display: none;
  }
}

.login-container {
  width: 100%;
  max-width: 440px;
  position: relative;
  z-index: 1;
}

/* Mobile logo */
.mobile-logo {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 32px;
}

@media (min-width: 1024px) {
  .mobile-logo {
    display: none;
  }
}

.mobile-logo-block {
  padding: 12px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(8px);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  box-shadow: var(--shadow-architectural);
}

.mobile-logo-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}

.logo-cell-sm {
  width: 16px;
  height: 16px;
}

.mobile-brand-title {
  font-family: var(--font-headline);
  font-size: 30px;
  font-weight: 800;
  color: var(--color-on-surface);
  letter-spacing: -0.02em;
  line-height: 38px;
  margin: 0;
}

/* Header */
.login-header {
  margin-bottom: 32px;
}

.welcome-title {
  font-family: var(--font-headline);
  font-size: 30px;
  font-weight: 800;
  color: var(--color-on-surface);
  letter-spacing: -0.02em;
  line-height: 38px;
  margin: 0 0 8px;
}

.welcome-subtitle {
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 20px;
  color: var(--color-on-surface-variant);
  margin: 0;
}

/* ───────────── Form ───────────── */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-label {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  line-height: 18px;
  color: var(--color-on-surface-variant);
  display: block;
  margin-left: 4px;
}

.field-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 4px;
}

.forgot-link {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 700;
  line-height: 16px;
  letter-spacing: 0.05em;
  color: var(--color-primary);
  text-decoration: none;
  transition: color 0.2s ease;
}

.forgot-link:hover {
  color: var(--color-tertiary);
}

.input-wrapper {
  position: relative;
}

.field-input {
  width: 100%;
  height: 56px;
  padding: 0 48px 0 16px;
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 20px;
  color: var(--color-on-surface);
  background: #ffffff;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  outline: none;
  transition: all 0.2s ease;
  box-shadow: var(--shadow-architectural);
  box-sizing: border-box;
}

.field-input::placeholder {
  color: rgba(119, 117, 135, 0.6);
}

.input-wrapper:hover .field-input {
  border-color: var(--color-outline);
}

.field-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 4px rgba(40, 116, 117, 0.05);
}

.input-icon {
  position: absolute;
  inset: 0 0 0 auto;
  display: flex;
  align-items: center;
  padding-right: 16px;
  pointer-events: none;
  color: var(--color-outline);
  transition: color 0.2s ease;
}

.input-icon.active {
  color: var(--color-primary);
}

.input-icon .material-symbols-outlined {
  font-size: 22px;
}

.input-icon-btn {
  position: absolute;
  inset: 0 0 0 auto;
  display: flex;
  align-items: center;
  padding-right: 16px;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-outline);
  transition: color 0.2s ease;
}

.input-icon-btn:hover {
  color: var(--color-primary);
}

.input-icon-btn.active {
  color: var(--color-primary);
}

.input-icon-btn .material-symbols-outlined {
  font-size: 22px;
}

.field-error {
  font-size: 13px;
  color: var(--color-error);
  margin: 0;
  padding-left: 4px;
}

/* Checkbox */
.checkbox-row {
  display: flex;
  align-items: center;
  padding: 0 4px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.checkbox-input {
  width: 20px;
  height: 20px;
  border: 1.5px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  cursor: pointer;
  accent-color: var(--color-primary);
  transition: all 0.2s ease;
}

.checkbox-text {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  line-height: 18px;
  color: var(--color-on-surface-variant);
  transition: color 0.2s ease;
}

.checkbox-label:hover .checkbox-text {
  color: var(--color-on-surface);
}

/* Error banner */
.error-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: rgba(186, 26, 26, 0.06);
  border: 1px solid rgba(186, 26, 26, 0.2);
  border-radius: var(--radius-lg);
  animation: slideIn 0.3s ease;
}

.error-banner-icon {
  color: var(--color-error);
  font-size: 20px;
  flex-shrink: 0;
}

.error-banner p {
  font-size: 14px;
  color: var(--color-error);
  margin: 0;
  line-height: 20px;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Submit button */
.submit-group {
  margin-top: 4px;
}

.sign-in-btn {
  width: 100%;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-family: var(--font-headline);
  font-size: 16px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border: none;
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.25s ease;
}

.sign-in-btn:hover:not(:disabled) {
  background: var(--color-on-surface);
  box-shadow: 0 8px 24px rgba(40, 116, 117, 0.2);
}

.sign-in-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.sign-in-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-arrow {
  font-size: 20px;
}

/* Spinner */
.spinner {
  width: 20px;
  height: 20px;
  border: 2.5px solid rgba(255, 255, 255, 0.3);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Footer */
.login-footer {
  padding-top: 24px;
  text-align: center;
  margin-top: 32px;
}

.login-footer p {
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 20px;
  color: var(--color-on-surface-variant);
  margin: 0;
}

.contact-link {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-primary);
  margin-left: 4px;
  text-decoration: none;
  text-underline-offset: 4px;
}

.contact-link:hover {
  text-decoration: underline;
  text-decoration-color: rgba(53, 37, 205, 0.3);
}

/* ───────────── Material Icons ───────────── */
.material-symbols-outlined {
  font-variation-settings: "FILL" 0, "wght" 400, "GRAD" 0, "opsz" 24;
}
</style>
