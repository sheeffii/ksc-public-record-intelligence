import { describe, expect, it } from "vitest";
import { createReaderClient, toOverlay, toSegment } from "./reader";

describe("Phase 20B reader data", () => {
  it("keeps an unresolved citation fail-closed and its precision explicit", () => {
    const overlay = toOverlay({
      anchor_id: "a",
      object_id: "o",
      kind: "citation",
      label: "KSC-BC-2020-06/F01226/A01, para.47",
      state: "UNRESOLVED",
      precision: "page_only",
      failure_reason: "geometry_text_not_found",
      regions: [],
      target_path: null,
      resolution_state: "unresolved",
    });
    expect(overlay.state).toBe("UNRESOLVED");
    expect(overlay.targetPath).toBeUndefined();
    expect(overlay.regions).toEqual([]);
    expect(overlay.precision).toBe("page_only");
  });

  it("serves closed-session segments without text", () => {
    const segment = toSegment({
      id: "s",
      sequence: 4,
      pdf_page_index: 0,
      page_number: 14983,
      line_from: 17,
      line_to: 17,
      speaker: null,
      witness_code: null,
      closed_session: true,
      text: null,
      anchor: null,
    });
    expect(segment.closedSession).toBe(true);
    expect(segment.text).toBeUndefined();
    expect(segment.anchor).toBeUndefined();
  });

  it("labels every local search hit SEARCH_MATCH and requests one version only", async () => {
    const calls: string[] = [];
    const client = createReaderClient("http://api", async (input) => {
      calls.push(input);
      return new Response(
        JSON.stringify({
          query: "solemn",
          total: 1,
          truncated: false,
          items: [
            {
              pdf_page_index: 4,
              page_number: 14987,
              line_from: 6,
              line_to: 7,
              transcript_segment_id: "s",
              speaker: "PRESIDING JUDGE SMITH",
              excerpt: "I solemnly declare",
              occurrences: 1,
              precision: "page_and_line",
            },
          ],
        }),
      );
    });
    const result = await client.search("KSC-BC-2020-06/T/2024-04-29", "solemn");
    expect(result?.items[0]?.matchType).toBe("SEARCH_MATCH");
    expect(calls[0]).toBe(
      "http://api/api/v1/document-versions/KSC-BC-2020-06/T/2024-04-29/source-search?q=solemn",
    );
  });
});
