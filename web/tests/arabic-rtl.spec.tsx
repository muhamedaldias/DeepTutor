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
