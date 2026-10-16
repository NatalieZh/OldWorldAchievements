(function () {
  const DEFAULT_LOCALE = "ru";
  const STORAGE_KEY = "ow-guide-language";
  const SUPPORTED_LOCALES = ["ru", "en"];

  function normalizeLocale(locale) {
    const value = String(locale || "").toLowerCase().split("-")[0];
    return SUPPORTED_LOCALES.includes(value) ? value : null;
  }

  function readStoredLocale() {
    try {
      return normalizeLocale(window.localStorage.getItem(STORAGE_KEY));
    } catch (error) {
      return null;
    }
  }

  function initialLocale() {
    const queryLocale = normalizeLocale(new URLSearchParams(window.location.search).get("lang"));
    return queryLocale || readStoredLocale() || DEFAULT_LOCALE;
  }

  let currentLocale = initialLocale();

  function translate(key, variables) {
    const dictionaries = window.APP_LOCALES || {};
    const value = dictionaries[currentLocale]?.[key] ?? dictionaries[DEFAULT_LOCALE]?.[key] ?? key;
    return String(value).replace(/\{(\w+)\}/g, (_, name) => variables?.[name] ?? `{${name}}`);
  }

  function applyTranslations(root) {
    const scope = root || document;
    scope.querySelectorAll("[data-i18n]").forEach(element => {
      element.textContent = translate(element.dataset.i18n);
    });
    scope.querySelectorAll("[data-i18n-html]").forEach(element => {
      element.innerHTML = translate(element.dataset.i18nHtml);
    });
    scope.querySelectorAll("[data-i18n-placeholder]").forEach(element => {
      element.setAttribute("placeholder", translate(element.dataset.i18nPlaceholder));
    });
    scope.querySelectorAll("[data-i18n-aria-label]").forEach(element => {
      element.setAttribute("aria-label", translate(element.dataset.i18nAriaLabel));
    });
    document.title = translate("meta.title");
    document.documentElement.lang = currentLocale;
    document.querySelectorAll("[data-locale]").forEach(button => {
      const active = button.dataset.locale === currentLocale;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    });
  }

  function storeLocale(locale) {
    try {
      window.localStorage.setItem(STORAGE_KEY, locale);
    } catch (error) {}
  }

  function updateUrl(locale) {
    try {
      const url = new URL(window.location.href);
      if (locale === DEFAULT_LOCALE) url.searchParams.delete("lang");
      else url.searchParams.set("lang", locale);
      window.history.replaceState(null, "", url.href);
    } catch (error) {}
  }

  function setLocale(locale, options) {
    const nextLocale = normalizeLocale(locale) || DEFAULT_LOCALE;
    const settings = { persist: true, updateUrl: true, ...options };
    currentLocale = nextLocale;
    if (settings.persist) storeLocale(nextLocale);
    if (settings.updateUrl) updateUrl(nextLocale);
    applyTranslations();
    window.dispatchEvent(new CustomEvent("app:languagechange", { detail: { locale: nextLocale } }));
    return nextLocale;
  }

  window.AppI18n = {
    apply: applyTranslations,
    getLocale: () => currentLocale,
    setLocale,
    t: translate
  };

  storeLocale(currentLocale);
})();
