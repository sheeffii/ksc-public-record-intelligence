import { describe, expect, it } from "vitest";

import { versionFacets } from "./version-label";

describe("versionFacets", () => {
  it("reads language and status from the official reference only", () => {
    expect(versionFacets("KSC-BC-2020-06/F00026/RED", "en")).toEqual({
      language: "en",
      statuses: ["publicRedacted"],
    });
    expect(versionFacets("KSC-BC-2020-06/F00026/RED/sqi/COR", "en")).toEqual({
      language: "sq",
      statuses: ["publicRedacted", "corrected"],
    });
    expect(versionFacets("KSC-BC-2020-06/F03668/RED2", "en").statuses).toEqual([
      "publicRedactedV2",
    ]);
    expect(versionFacets("KSC-BC-2020-06/F00045/A03", "en").statuses).toEqual(["public"]);
    expect(versionFacets("KSC-BC-2020-06/F01234/CONF/RED", "en", "reclassified").statuses).toEqual([
      "reclassified",
      "publicRedacted",
    ]);
  });

  it("never reads a case or filing segment as a language", () => {
    expect(versionFacets("KSC-BC-2020-06/F00001", undefined).language).toBeUndefined();
  });
});
