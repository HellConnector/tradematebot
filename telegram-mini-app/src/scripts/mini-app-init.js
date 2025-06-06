const app = window.Telegram.WebApp;

app.ready();
app.expand();
window.app = app;

document.body.addEventListener("htmx:configRequest", function (evt) {
  evt.detail.headers["Authorization"] = app.initData;
});

document.addEventListener("DOMContentLoaded", function () {
  document.body.classList.add(`theme-${app.colorScheme}`);

  const root = document.documentElement;
  const themeParams = app.themeParams;

  if (themeParams) {
    root.style.setProperty("--telegram-bg-color", themeParams.bg_color);
    root.style.setProperty("--telegram-text-color", themeParams.text_color);
    root.style.setProperty("--telegram-hint-color", themeParams.hint_color);
    root.style.setProperty("--telegram-link-color", themeParams.link_color);
    root.style.setProperty("--telegram-button-color", themeParams.button_color);
    root.style.setProperty(
      "--telegram-button-text-color",
      themeParams.button_text_color,
    );
    root.style.setProperty(
      "--telegram-secondary-bg-color",
      themeParams.secondary_bg_color,
    );
  }

  app.onEvent("themeChanged", function () {
    document.body.classList.remove("theme-light", "theme-dark");
    document.body.classList.add(`theme-${app.colorScheme}`);

    if (app.themeParams) {
      root.style.setProperty("--telegram-bg-color", app.themeParams.bg_color);
      root.style.setProperty(
        "--telegram-text-color",
        app.themeParams.text_color,
      );
      root.style.setProperty(
        "--telegram-hint-color",
        app.themeParams.hint_color,
      );
      root.style.setProperty(
        "--telegram-link-color",
        app.themeParams.link_color,
      );
      root.style.setProperty(
        "--telegram-button-color",
        app.themeParams.button_color,
      );
      root.style.setProperty(
        "--telegram-button-text-color",
        app.themeParams.button_text_color,
      );
      root.style.setProperty(
        "--telegram-secondary-bg-color",
        app.themeParams.secondary_bg_color,
      );
    }
  });
});

document.addEventListener("click", function (event) {
  if (!event.target.closest("input") && !event.target.closest("textarea")) {
    const activeElement = document.activeElement;
    if (
      activeElement &&
      (activeElement.tagName === "input" ||
        activeElement.tagName === "textarea")
    ) {
      activeElement.blur();
    }
  }
});

window.historyManager = {
  STORAGE_KEY: "history",
  history: [],
  currentIndex: -1,

  loadHistory: function () {
    const data = sessionStorage.getItem(this.STORAGE_KEY);
    if (data) {
      const parsed = JSON.parse(data);
      this.history = parsed.history || [];
      this.currentIndex = parsed.currentIndex || -1;
    }
  },

  saveHistory: function () {
    const data = {
      history: this.history,
      currentIndex: this.currentIndex,
    };
    sessionStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
  },

  push: function (urlPath) {
    this.history = this.history.slice(0, this.currentIndex + 1);
    this.history.push(urlPath);
    this.currentIndex = this.history.length - 1;
    this.saveHistory();
    this.updateBackButton();
  },

  back: function () {
    if (this.canGoBack()) {
      this.currentIndex--;
      this.saveHistory();
      this.updateBackButton();
      return this.getCurrentPage();
    }
    return null;
  },

  canGoBack: function () {
    return this.currentIndex > 0;
  },

  getCurrentPage: function () {
    return this.history[this.currentIndex] || null;
  },

  updateBackButton: function () {
    if (this.canGoBack()) {
      app.BackButton.show();
    } else {
      app.BackButton.hide();
    }
  },

  goToUrl: function (urlPath) {
    this.push(urlPath);
    window.location.href = urlPath;
  },

  init: function () {
    this.loadHistory();
    const currentUrlPath = window.location.pathname + window.location.search;

    if (this.history.length === 0) {
      this.push(currentUrlPath);
    } else {
      if (!(this.getCurrentPage() === currentUrlPath)) {
        this.push(currentUrlPath);
      }
    }

    this.updateBackButton();

    app.onEvent("backButtonClicked", () => {
      const previousPage = this.back();
      if (previousPage) {
        window.location.href = previousPage;
      }
    });
  },
};

window.historyManager.init();

console.log("Mini App initialized successfully with theme:", app.colorScheme);
