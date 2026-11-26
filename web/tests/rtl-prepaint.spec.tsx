import { readFileSync } from "node:fs";
import { join } from "node:path";
import { render } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import LanguageScript from "../components/LanguageScript";

function paintLanguage() {
  const { container } = render(<LanguageScript />);
  const script = container.querySelector("script");
  expect(script?.textContent).toContain("deeptutor-language");
  window.eval(script!.textContent!);
}

describe("pre-paint language/direction", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.lang = "en";
    document.documentElement.removeAttribute("dir");
  });

  it("paints Arabic as rtl before hydration", () => {
    localStorage.setItem("deeptutor-language", "ar");
    paintLanguage();
    expect(document.documentElement.lang).toBe("ar");
    expect(document.documentElement.dir).toBe("rtl");
  });

  it("accepts Arabic locale variants", () => {
    for (const value of ["ar-EG", "ar_EG", "العربية", "Arabic"]) {
      localStorage.setItem("deeptutor-language", value);
      paintLanguage();
      expect(document.documentElement.lang).toBe("ar");
      expect(document.documentElement.dir).toBe("rtl");
    }
  });

  it("paints non-RTL locales as ltr, with a safe default", () => {
    for (const [stored, lang] of [
      ["zh", "zh"],
      ["fr-FR", "fr"],
      ["xx", "en"],
    ]) {
      localStorage.setItem("deeptutor-language", stored);
      paintLanguage();
      expect(document.documentElement.lang).toBe(lang);
      expect(document.documentElement.dir).toBe("ltr");
    }
    localStorage.clear();
    paintLanguage();
    expect(document.documentElement.lang).toBe("en");
    expect(document.documentElement.dir).toBe("ltr");
  });
});

describe("coupled RTL layout mirroring (source guards)", () => {
  const globals = readFileSync(join(process.cwd(), "app/globals.css"), "utf8");
  const modern = readFileSync(
    join(process.cwd(), "features/ui-layout/modern/modern.css"),
    "utf8",
  );

  it("squeezes the chat column on the inline-end gutter", () => {
    expect(globals).toContain("padding-inline-end: min(560px, 92vw)");
    expect(globals).toContain("padding-inline-start: 64%");
    expect(globals).toContain(
      "padding-inline-end var(--viewer-dur) var(--viewer-ease)",
    );
  });

  it("flips the viewer and watching panels with the squeeze", () => {
    expect(globals).toContain("--viewer-slide-sign: 1");
    expect(globals).toContain('--viewer-slide-sign: -1');
    expect(globals).toContain(':root[dir="rtl"] .dt-viewer-panel');
    expect(globals).toContain("calc(-100% * var(--viewer-slide-sign))");
    expect(globals).toContain(':root[dir="rtl"] .dt-watching-shell');
    expect(globals).toContain("inset-inline-start: 0;\n  inset-inline-end: auto;");
  });

  it("anchors menus and tray items logically", () => {
    expect(modern).toContain("inset-inline-start: 0");
    expect(modern).toContain("inset-inline: auto 0");
    expect(modern).toContain(
      '[dir="rtl"] .dt-workspace-menu.is-rail .dt-workspace-panel',
    );
    expect(modern).toContain("margin-inline-start: auto");
    expect(modern).toContain("text-align: start");
  });
});
