import "@/test/next-mocks";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { NextIntlClientProvider } from "next-intl";
import messages from "@/i18n/messages/en.json";
import { incident } from "@/data/api/fixtures";
import { toIncident } from "@/data/api/mappers";
import { RealIncidentScreen } from "./RealRecordScreens";

describe("RealIncidentScreen", () => {
  it("attributes an SPO allegation and opens its exact operative Reader anchor", () => {
    const reviewed = toIncident({
      ...incident,
      source_category: "spo_allegation",
      verification_state: "human_verified",
      date_as_pleaded: "In May 1999 and in June 1999",
      review_decision: { withdrawal_review: { status: "UNAFFECTED" } },
      sources: [
        {
          sequence: 1,
          role: "operative",
          source_ref: "KSC-DEMO-0000/F-DEMO-001/RED",
          paragraph_number: 12,
          excerpt: "Synthetic public source excerpt.",
          note: null,
          verification_state: "human_verified",
          source_anchor_id: "00000000-0000-0000-0000-000000000001",
          target_path:
            "/documents/F-DEMO-001?version=KSC-DEMO-0000%2FF-DEMO-001%2FRED&pdfPage=1&anchor=00000000-0000-0000-0000-000000000001",
        },
      ],
    });
    render(
      <NextIntlClientProvider locale="en" messages={messages}>
        <RealIncidentScreen incident={reviewed} />
      </NextIntlClientProvider>,
    );
    expect(screen.getByText("SPO allegation · not a Court finding")).toBeInTheDocument();
    expect(screen.getByText("Synthetic public source excerpt.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open exact passage in Reader" })).toHaveAttribute(
      "href",
      expect.stringContaining("anchor=00000000-0000-0000-0000-000000000001"),
    );
  });
});
