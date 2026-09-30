import { describe, expect, it } from "vitest";
import { documentApiPath, documentHref, documentRouteId } from "./document-route";

describe("document routes", () => {
  it("keeps slash-bearing identifiers intact and encodes them as one segment", () => {
    expect(documentRouteId("KSC-BC-2020-06/F00002/A01")).toBe("F00002/A01");
    expect(documentRouteId("IA019/F00001")).toBe("IA019/F00001");
    expect(documentHref("KSC-BC-2020-06/F00002/A01")).toBe("/documents/F00002%2FA01");
    expect(documentHref("IA019/F00001")).toBe("/documents/IA019%2FF00001");
    expect(documentApiPath("F00002/A01")).toBe("/documents/F00002%2FA01");
  });
});
