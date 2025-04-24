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

console.log("Mini App initialized successfully with theme:", app.colorScheme);
