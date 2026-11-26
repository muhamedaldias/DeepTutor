import { render, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  documentDirection,
  I18nProvider,
} from "../i18n/I18nProvider";

describe("Arabic RTL document direction", () => {
  it("maps only Arabic UI languages to rtl", () => {
    expect(documentDirection("ar")).toBe("rtl");
    expect(documentDirection("ar-EG")).toBe("rtl");
    expect(documentDirection("العربية")).toBe("rtl");
    expect(documentDirection("en")).toBe("ltr");
    expect(documentDirection("zh")).toBe("ltr");
  });

  it("applies LTR isolation to inline fragments under RTL", async () => {
    const { container } = render(
      <I18nProvider language="ar">
        <p>
          مرحبا <code>const x = 1</code>{" "}
          <a href="mailto:a@example.com">a@example.com</a>
        </p>
      </I18nProvider>,
    );
    await waitFor(() => {
      expect(document.documentElement.dir).toBe("rtl");
    });
    const code = container.querySelector("code");
    const mailLink = container.querySelector('a[href^="mailto:"]');
    expect(code).not.toBeNull();
    expect(mailLink).not.toBeNull();
    expect(getComputedStyle(code!).direction).toBe("ltr");
    expect(getComputedStyle(mailLink!).direction).toBe("ltr");
  });

  it("mirrors the select affordance under RTL", async () => {
    const { container } = render(
      <I18nProvider language="ar">
        <select className="dt-select" aria-label="test" />
      </I18nProvider>,
    );
    await waitFor(() => {
      expect(document.documentElement.dir).toBe("rtl");
    });
    const style = getComputedStyle(container.querySelector("select")!);
    expect(parseFloat(style.paddingLeft)).toBeGreaterThan(0);
    expect(parseFloat(style.paddingRight)).toBe(0);
  });

  it("sets html lang/dir, isolates LTR fragments, and restores LTR on switch", async () => {
    const root = document.documentElement;
    const { rerender, unmount } = render(
      <I18nProvider language="ar">
        <p>مرحبا</p>
      </I18nProvider>,
    );

    await waitFor(() => {
      expect(root.lang).toBe("ar");
      expect(root.dir).toBe("rtl");
    });
    const style = document.querySelector("style[data-deeptutor-rtl]");
    expect(style).not.toBeNull();
    expect(style?.textContent).toContain("direction: ltr");
    expect(style?.textContent).toContain("unicode-bidi: isolate");

    rerender(
      <I18nProvider language="en">
        <p>hello</p>
      </I18nProvider>,
    );
    await waitFor(() => {
      expect(root.lang).toBe("en");
      expect(root.dir).toBe("ltr");
    });
    expect(document.querySelector("style[data-deeptutor-rtl]")).toBeNull();
    unmount();
  });
});
